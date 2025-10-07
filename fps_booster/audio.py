"""Audio intelligence layer for spectral situational awareness."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Dict, Sequence, Tuple


@dataclass(frozen=True)
class AudioReport:
    """Encapsulates audio-derived cues for the helper."""

    dominant_frequency: float
    band_energy: Dict[str, float]
    event_confidence: float


class AudioAnalyzer:
    """Transforms waveform samples into actionable metrics without external deps."""

    def __init__(
        self,
        sample_rate: int,
        window_size: int = 512,
        event_band: Tuple[int, int] = (200, 2000),
        intensity_threshold: float = 0.15,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if event_band[0] >= event_band[1]:
            raise ValueError("event_band must be (low, high) with low < high")
        self._sample_rate = sample_rate
        self._window_size = window_size
        self._event_band = event_band
        self._intensity_threshold = intensity_threshold
        self._window = self._build_hann_window(window_size)

    def analyze(self, samples: Sequence[float]) -> AudioReport:
        """Return the spectral decomposition of the provided samples."""

        if len(samples) < self._window_size:
            raise ValueError("samples must contain at least window_size elements")
        windowed = [samples[i] * self._window[i] for i in range(self._window_size)]
        spectrum = self._dft(windowed)
        magnitudes = [abs(value) for value in spectrum]
        freq_step = self._sample_rate / self._window_size
        freqs = [i * freq_step for i in range(len(magnitudes))]

        dominant_idx = max(range(len(magnitudes)), key=magnitudes.__getitem__)
        dominant_frequency = freqs[dominant_idx]

        total_energy = sum(magnitudes) or 1.0
        band_energy = self._aggregate_bands(freqs, magnitudes)
        event_energy = self._band_energy(freqs, magnitudes, self._event_band)
        event_confidence = min(1.0, (event_energy / total_energy) / self._intensity_threshold)

        return AudioReport(
            dominant_frequency=round(dominant_frequency, 2),
            band_energy={k: round(v, 4) for k, v in band_energy.items()},
            event_confidence=round(event_confidence, 3),
        )

    def _aggregate_bands(self, freqs: Sequence[float], magnitudes: Sequence[float]) -> Dict[str, float]:
        bands = {
            "low": (0, 250),
            "mid": (250, 2000),
            "high": (2000, self._sample_rate / 2),
        }
        return {name: self._band_energy(freqs, magnitudes, rng) for name, rng in bands.items()}

    @staticmethod
    def _band_energy(freqs: Sequence[float], magnitudes: Sequence[float], band: Tuple[float, float]) -> float:
        total = 0.0
        for freq, magnitude in zip(freqs, magnitudes):
            if band[0] <= freq < band[1]:
                total += magnitude
        return total

    @staticmethod
    def _build_hann_window(size: int) -> Sequence[float]:
        if size == 1:
            return [1.0]
        return [0.5 - 0.5 * math.cos((2 * math.pi * n) / (size - 1)) for n in range(size)]

    def _dft(self, samples: Sequence[float]) -> Sequence[complex]:
        n = self._window_size
        half_n = n // 2
        result = []
        for k in range(half_n + 1):
            acc = 0j
            for t, sample in enumerate(samples):
                angle = -2j * math.pi * k * t / n
                acc += sample * cmath.exp(angle)
            result.append(acc)
        return result
