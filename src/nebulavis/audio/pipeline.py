"""High-level audio pipeline that couples capture and analysis."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator


from .analysis import AudioAnalysisFrame, AudioAnalyzer, AudioAnalyzerConfig
from .capture import AsyncAudioStream, AudioCapture, AudioCaptureConfig

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AudioPipelineConfig:
    capture: AudioCaptureConfig = field(default_factory=AudioCaptureConfig)
    analyzer: AudioAnalyzerConfig = field(default_factory=AudioAnalyzerConfig)


class AudioPipeline:
    """Combine capture and analysis into a single async iterator."""

    def __init__(self, config: AudioPipelineConfig | None = None) -> None:
        self._config = config or AudioPipelineConfig()
        self.capture = AudioCapture(self._config.capture)
        self.analyzer = AudioAnalyzer(self._config.analyzer)
        self._async_stream = AsyncAudioStream(self.capture)
        self._latency_offset = 0.0

    def start(self) -> None:
        LOGGER.info("Starting audio pipeline with %s", self._config.capture)
        self.capture.start()

    def stop(self) -> None:
        LOGGER.info("Stopping audio pipeline")
        self.capture.stop()

    async def frames(self) -> AsyncIterator[AudioAnalysisFrame]:
        async for block in self._async_stream:
            timestamp = time.perf_counter() - self._latency_offset
            frame = self.analyzer.process_block(block, timestamp)
            yield frame

    def calibrate_latency(self, measured_offset_ms: float) -> None:
        """Apply an additional latency offset derived from calibration."""

        self._latency_offset = measured_offset_ms / 1000.0
        LOGGER.info("Applied latency offset: %.2f ms", measured_offset_ms)

    def latest_latency(self) -> float:
        """Return the latency reported by the capture device, in seconds."""

        return self.capture.latest_latency()

    def latency_budget(self) -> float:
        """Approximate capture→analysis latency in milliseconds."""

        return (self.capture.latest_latency() + self._config.capture.blocksize / self._config.capture.samplerate) * 1000.0
