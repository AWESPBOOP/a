"""Audio capture management for NebulaVis."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

try:  # pragma: no cover - optional dependency may not be available during tests
    import sounddevice as sd
except Exception:  # pragma: no cover
    sd = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AudioCaptureConfig:
    """Configuration for the audio capture stream."""

    samplerate: int = 48000
    channels: int = 2
    blocksize: int = 1024
    device: Optional[int | str] = None
    enable_loopback: bool = True
    fallback_microphone: bool = True
    latency_hint: float | None = None
    max_queue_blocks: int = 8


class AudioStreamError(RuntimeError):
    """Raised when the audio stream encounters an unrecoverable error."""


class AudioCapture:
    """Wraps :mod:`sounddevice` to provide resilient audio capture."""

    def __init__(self, config: AudioCaptureConfig) -> None:
        if sd is None:
            raise AudioStreamError(
                "sounddevice is required for audio capture but is not available."
            )
        self._config = config
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=config.max_queue_blocks)
        self._stream: sd.InputStream | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._latest_latency = 0.0
        self._last_underflow = 0.0
        self._latency_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Device helpers
    # ------------------------------------------------------------------
    @staticmethod
    def list_devices() -> list[dict[str, object]]:
        """Return all available devices in a normalized structure."""

        if sd is None:
            return []
        devices = []
        for idx, info in enumerate(sd.query_devices()):
            devices.append(
                {
                    "id": idx,
                    "name": info["name"],
                    "max_input_channels": info["max_input_channels"],
                    "default_samplerate": info["default_samplerate"],
                    "hostapi": sd.query_hostapis(info["hostapi"])["name"],
                }
            )
        return devices

    @staticmethod
    def suggest_loopback_device() -> Optional[int]:
        """Try to find a device that supports loopback capture."""

        if sd is None:
            return None
        try:
            hostapis = sd.query_hostapis()
        except Exception as exc:  # pragma: no cover - passthrough
            LOGGER.debug("Failed to query hostapis: %s", exc)
            return None
        for host_idx, host in enumerate(hostapis):
            if "loopback" not in str(host).lower():
                continue
            for device_idx in host["devices"]:
                info = sd.query_devices(device_idx)
                if info["max_input_channels"] > 0:
                    return device_idx
        return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the capture stream and consumer thread."""

        if self._stream is not None:
            return

        device = self._config.device
        if device is None and self._config.enable_loopback:
            device = self.suggest_loopback_device()
            if device is None:
                LOGGER.warning("Loopback device unavailable; falling back to default input")
        if device is None and not self._config.fallback_microphone:
            raise AudioStreamError("No input device available and microphone fallback disabled")

        def callback(indata: np.ndarray, frames: int, time_info: dict[str, float], status: sd.CallbackFlags) -> None:  # pragma: no cover - relies on hardware
            if status.input_overflow:
                LOGGER.warning("Input overflow detected")
                with self._latency_lock:
                    self._last_underflow = time.time()
            with self._latency_lock:
                self._latest_latency = time_info.get("input_latency", 0.0)
            block = np.copy(indata)
            try:
                self._queue.put_nowait(block)
            except queue.Full:
                LOGGER.warning("Audio capture queue full; dropping frame")

        self._stream = sd.InputStream(
            samplerate=self._config.samplerate,
            blocksize=self._config.blocksize,
            channels=self._config.channels,
            dtype="float32",
            device=device,
            latency=self._config.latency_hint,
            callback=callback,
        )

        self._stream.start()
        self._stop.clear()
        self._thread = threading.Thread(target=self._drain_queue, name="NebulaVisAudio", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the capture stream."""

        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None

        if self._stream is not None:
            with contextlib.suppress(Exception):
                self._stream.stop()
                self._stream.close()
        self._stream = None
        with self._latency_lock:
            self._latest_latency = 0.0

    # ------------------------------------------------------------------
    def _drain_queue(self) -> None:  # pragma: no cover - real-time thread
        """Continuously drain the audio queue to avoid back-pressure."""

        while not self._stop.is_set():
            try:
                self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

    # ------------------------------------------------------------------
    def poll_block(self, timeout: float = 0.05) -> Optional[np.ndarray]:
        """Retrieve the next audio block if available."""

        try:
            block = self._queue.get(timeout=timeout)
            return block
        except queue.Empty:
            return None

    def latest_latency(self) -> float:
        """Return the most recent input latency reported by PortAudio."""

        with self._latency_lock:
            return self._latest_latency

    def last_underflow(self) -> float:
        """Return timestamp of the last underflow event."""

        with self._latency_lock:
            return self._last_underflow


class AsyncAudioStream:
    """Expose captured audio as an asynchronous iterator."""

    def __init__(self, capture: AudioCapture) -> None:
        self._capture = capture
        self._loop = asyncio.get_event_loop()

    async def __aiter__(self) -> "AsyncAudioStream":
        return self

    async def __anext__(self) -> np.ndarray:
        block = await self._loop.run_in_executor(None, self._capture.poll_block)
        if block is None:
            await asyncio.sleep(0.001)
            return await self.__anext__()
        return block


def wait_for_device(predicate: Callable[[dict[str, object]], bool], timeout: float = 5.0) -> Optional[int]:
    """Wait until a device that satisfies *predicate* becomes available."""

    if sd is None:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for device in AudioCapture.list_devices():
            if predicate(device):
                return int(device["id"])  # type: ignore[arg-type]
        time.sleep(0.2)
    return None
