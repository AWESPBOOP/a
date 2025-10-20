from __future__ import annotations

import numpy as np

from nebulavis.audio.analysis import AudioAnalyzer, AudioAnalyzerConfig


def test_audio_analyzer_detects_energy():
    config = AudioAnalyzerConfig(samplerate=48000, fft_size=1024, hop_size=512, bands=32)
    analyzer = AudioAnalyzer(config)
    t = np.linspace(0, 1, config.fft_size, endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    frame = analyzer.process_block(signal.astype(np.float32))
    assert frame.rms > 0.1
    assert frame.band_energies.max() > 0.0
    assert 0 <= frame.beat_phase <= 1


def test_audio_analyzer_envelopes_track_energy():
    config = AudioAnalyzerConfig(samplerate=48000, fft_size=1024, hop_size=512, bands=16)
    analyzer = AudioAnalyzer(config)
    noise = np.random.randn(config.fft_size).astype(np.float32) * 0.01
    frame_low = analyzer.process_block(noise)
    noise += np.hanning(config.fft_size).astype(np.float32) * 0.5
    frame_high = analyzer.process_block(noise)
    assert frame_high.envelopes.mean() > frame_low.envelopes.mean()
