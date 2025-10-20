"""Latency calibration helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
import numpy as np

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class LatencyCalibrationResult:
    offset_ms: float
    correlation: float
    reference_peak: int
    measured_peak: int


class LatencyCalibrator:
    """Estimate latency by cross-correlating reference and captured signals."""

    def __init__(self, samplerate: int) -> None:
        self._samplerate = samplerate

    def calibrate(self, reference: np.ndarray, captured: np.ndarray) -> LatencyCalibrationResult:
        if reference.ndim > 1:
            reference = reference.mean(axis=1)
        if captured.ndim > 1:
            captured = captured.mean(axis=1)
        reference = reference - np.mean(reference)
        captured = captured - np.mean(captured)

        corr = np.correlate(captured, reference, mode="full")
        peak_index = int(np.argmax(corr))
        correlation = float(corr[peak_index]) / (np.linalg.norm(reference) * np.linalg.norm(captured) + 1e-6)
        lag = peak_index - len(reference) + 1
        offset_seconds = lag / self._samplerate
        LOGGER.info("Latency calibration: lag=%s samples, correlation=%.3f", lag, correlation)
        return LatencyCalibrationResult(
            offset_ms=offset_seconds * 1000.0,
            correlation=correlation,
            reference_peak=int(np.argmax(np.abs(reference))),
            measured_peak=int(np.argmax(np.abs(captured))),
        )
