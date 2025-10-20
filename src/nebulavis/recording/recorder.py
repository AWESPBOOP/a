"""Recording pipeline using ffmpeg."""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RecorderConfig:
    output_path: Path
    width: int = 1920
    height: int = 1080
    framerate: int = 60
    pixel_format: str = "rgba"
    codec: str = "libx264"
    bitrate: str = "20M"


class VideoRecorder:
    def __init__(self, config: RecorderConfig) -> None:
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._start_time: Optional[float] = None
        self._is_recording = False

    def start(self) -> None:
        if self._process:
            LOGGER.warning("Recorder already running")
            return
        args = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            self._config.pixel_format,
            "-s",
            f"{self._config.width}x{self._config.height}",
            "-r",
            str(self._config.framerate),
            "-i",
            "-",
            "-an",
            "-c:v",
            self._config.codec,
            "-b:v",
            self._config.bitrate,
            str(self._config.output_path),
        ]
        LOGGER.info("Starting ffmpeg recorder: %s", " ".join(args))
        self._process = subprocess.Popen(args, stdin=subprocess.PIPE)
        self._start_time = time.time()
        self._is_recording = True

    def stop(self) -> None:
        if not self._process:
            return
        if self._process.stdin:
            self._process.stdin.close()
        self._process.wait(timeout=10)
        LOGGER.info("Recorder stopped after %.1f seconds", time.time() - (self._start_time or time.time()))
        self._process = None
        self._is_recording = False

    def push_frame(self, frame_bytes: bytes) -> None:
        if not self._process or not self._process.stdin:
            return
        self._process.stdin.write(frame_bytes)

    @property
    def is_recording(self) -> bool:
        return self._is_recording
