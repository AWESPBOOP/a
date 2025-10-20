from __future__ import annotations

import numpy as np

from nebulavis.audio.latency import LatencyCalibrator


def test_latency_calibration_detects_offset():
    samplerate = 48000
    calibrator = LatencyCalibrator(samplerate)
    reference = np.zeros(1024, dtype=np.float32)
    reference[10] = 1.0
    captured = np.zeros(2048, dtype=np.float32)
    captured[260] = 1.0
    result = calibrator.calibrate(reference, captured)
    assert abs(result.offset_ms - (250 / samplerate * 1000.0)) < 1.0
