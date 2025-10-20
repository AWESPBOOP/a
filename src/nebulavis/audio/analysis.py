"""Audio analysis primitives for NebulaVis."""

from __future__ import annotations

import collections
import logging
import math
import time
from dataclasses import dataclass
from typing import Deque, Iterable, Optional

import numpy as np

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover
    import librosa
except Exception:  # pragma: no cover
    librosa = None


@dataclass(slots=True)
class AudioAnalysisFrame:
    """Container for per-block audio features."""

    timestamp: float
    spectrum: np.ndarray
    band_energies: np.ndarray
    rms: float
    peak: float
    spectral_centroid: float
    spectral_rolloff: float
    tempo: float
    beat: bool
    onset: bool
    beat_phase: float
    envelopes: np.ndarray
    chroma: Optional[np.ndarray] = None


@dataclass(slots=True)
class AudioAnalyzerConfig:
    samplerate: int = 48000
    fft_size: int = 2048
    hop_size: int = 512
    bands: int = 96
    min_frequency: float = 20.0
    max_frequency: float = 18000.0
    onset_sensitivity: float = 1.5
    beat_history_seconds: float = 8.0
    envelope_attack: float = 0.015
    envelope_release: float = 0.12
    smoothing_factor: float = 0.35
    chroma_enabled: bool = False


class AdaptiveTempoEstimator:
    """Simple adaptive tempo tracker with exponential smoothing."""

    def __init__(self, samplerate: int, hop_size: int, history_seconds: float) -> None:
        self._samplerate = samplerate
        self._hop_size = hop_size
        self._history_frames = int(history_seconds * samplerate / hop_size)
        self._onset_history: Deque[float] = collections.deque(maxlen=self._history_frames)
        self._last_beat_time = 0.0
        self._tempo = 120.0
        self._phase = 0.0

    def update(self, onset_strength: float, timestamp: float, threshold: float = 0.3) -> tuple[float, float, bool]:
        """Update with a new onset strength and return (tempo, phase, beat_flag)."""

        beat = False
        if onset_strength >= threshold and timestamp - self._last_beat_time > 0.1:
            beat = True
            if self._last_beat_time > 0.0:
                interval = timestamp - self._last_beat_time
                bpm = 60.0 / max(interval, 1e-6)
                self._onset_history.append(bpm)
                if len(self._onset_history) > 4:
                    self._tempo = 0.8 * self._tempo + 0.2 * float(np.median(self._onset_history))
                else:
                    self._tempo = bpm
            self._last_beat_time = timestamp
            self._phase = 0.0
        else:
            if self._tempo > 0:
                period = 60.0 / self._tempo
                self._phase = (self._phase + self._hop_size / self._samplerate) % period
        phase_norm = (self._phase * self._tempo) / 60.0 if self._tempo > 0 else 0.0
        return self._tempo, phase_norm, beat


class AudioAnalyzer:
    """Compute spectral features, envelopes, and beat estimations."""

    def __init__(self, config: AudioAnalyzerConfig) -> None:
        self._config = config
        self._window = np.hanning(config.fft_size).astype(np.float32)
        self._freqs = np.fft.rfftfreq(config.fft_size, 1.0 / config.samplerate)
        self._band_edges = self._compute_band_edges()
        self._tempo_estimator = AdaptiveTempoEstimator(
            config.samplerate, config.hop_size, config.beat_history_seconds
        )
        self._energy_history: Deque[float] = collections.deque(maxlen=int(config.beat_history_seconds * config.samplerate / config.hop_size))
        self._envelopes = np.zeros(config.bands, dtype=np.float32)
        self._spectral_smoothing = np.zeros_like(self._freqs, dtype=np.float32)

    # ------------------------------------------------------------------
    def process_block(self, samples: np.ndarray, timestamp: Optional[float] = None) -> AudioAnalysisFrame:
        if samples.ndim > 1:
            mono = samples.mean(axis=1)
        else:
            mono = samples
        if len(mono) < self._config.fft_size:
            pad = self._config.fft_size - len(mono)
            mono = np.pad(mono, (0, pad), mode="constant")
        else:
            mono = mono[: self._config.fft_size]

        windowed = mono * self._window
        spectrum = np.abs(np.fft.rfft(windowed)).astype(np.float32)

        smoothing = self._config.smoothing_factor
        self._spectral_smoothing = smoothing * self._spectral_smoothing + (1 - smoothing) * spectrum
        spectrum = self._spectral_smoothing

        band_energies = self._compute_bands(spectrum)
        rms = float(np.sqrt(np.mean(mono**2)))
        peak = float(np.max(np.abs(mono)))
        centroid = float(np.sum(self._freqs * spectrum) / (np.sum(spectrum) + 1e-6))
        cumulative = np.cumsum(spectrum)
        target = cumulative[-1] * 0.85 if cumulative.size else 0.0
        index = int(np.searchsorted(cumulative, target)) if cumulative.size else 0
        index = min(index, len(self._freqs) - 1)
        rolloff = float(self._freqs[index])

        onset_value = self._compute_onset(band_energies)
        tempo, beat_phase, beat_flag = self._tempo_estimator.update(onset_value, timestamp or time.perf_counter())
        onset_flag = onset_value > self._config.onset_sensitivity

        envelopes = self._update_envelopes(band_energies)
        chroma = self._compute_chroma(mono) if self._config.chroma_enabled else None

        frame = AudioAnalysisFrame(
            timestamp=timestamp or time.perf_counter(),
            spectrum=spectrum.copy(),
            band_energies=band_energies,
            rms=rms,
            peak=peak,
            spectral_centroid=centroid,
            spectral_rolloff=rolloff,
            tempo=tempo,
            beat=beat_flag,
            onset=onset_flag,
            beat_phase=beat_phase,
            envelopes=envelopes,
            chroma=chroma,
        )
        return frame

    # ------------------------------------------------------------------
    def _compute_band_edges(self) -> np.ndarray:
        freqs = np.geomspace(self._config.min_frequency, self._config.max_frequency, self._config.bands + 1)
        return freqs

    def _compute_bands(self, spectrum: np.ndarray) -> np.ndarray:
        bands = np.zeros(self._config.bands, dtype=np.float32)
        for idx in range(self._config.bands):
            low = self._band_edges[idx]
            high = self._band_edges[idx + 1]
            mask = (self._freqs >= low) & (self._freqs < high)
            if not np.any(mask):
                continue
            bands[idx] = float(np.mean(spectrum[mask]))
        max_energy = float(np.max(bands))
        if max_energy > 0:
            bands /= max_energy
        return bands

    def _compute_onset(self, band_energies: np.ndarray) -> float:
        energy = float(np.sum(band_energies))
        self._energy_history.append(energy)
        if len(self._energy_history) < 4:
            return 0.0
        local_avg = float(np.mean(list(self._energy_history)[-8:]))
        return (energy - local_avg) / (local_avg + 1e-6)

    def _update_envelopes(self, band_energies: np.ndarray) -> np.ndarray:
        attack_coeff = math.exp(-1.0 / (self._config.envelope_attack * self._config.samplerate))
        release_coeff = math.exp(-1.0 / (self._config.envelope_release * self._config.samplerate))
        for idx, value in enumerate(band_energies):
            if value > self._envelopes[idx]:
                coeff = attack_coeff
            else:
                coeff = release_coeff
            self._envelopes[idx] = coeff * self._envelopes[idx] + (1 - coeff) * value
        return self._envelopes.copy()

    def _compute_chroma(self, mono: np.ndarray) -> Optional[np.ndarray]:
        if librosa is None:
            return None
        try:  # pragma: no cover - heavy dependency
            chroma = librosa.feature.chroma_cqt(y=mono, sr=self._config.samplerate, hop_length=self._config.hop_size)
        except Exception as exc:  # pragma: no cover
            LOGGER.debug("Failed to compute chroma: %s", exc)
            return None
        return chroma[:, -1].astype(np.float32)


def chunk_audio(samples: np.ndarray, hop_size: int) -> Iterable[np.ndarray]:
    """Yield evenly sized chunks from the input buffer."""

    total = len(samples)
    for start in range(0, total, hop_size):
        end = start + hop_size
        chunk = samples[start:end]
        if len(chunk) < hop_size:
            chunk = np.pad(chunk, (0, hop_size - len(chunk)))
        yield chunk
