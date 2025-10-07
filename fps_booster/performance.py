"""Adaptive performance management for compliant optimization."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

from .features import FeatureFlags
from .integrations import HardwareSnapshot, HardwareTelemetryCollector


@dataclass(frozen=True)
class PerformanceSample:
    """Represents a single telemetry snapshot."""

    fps: float
    frame_time_ms: float
    cpu_util: float
    gpu_util: float


@dataclass(frozen=True)
class PerformanceRecommendation:
    """Encapsulates a performance tuning suggestion."""

    scaling_factor: float
    quality_shift: int
    confidence: float
    narrative: str
    hardware_snapshot: HardwareSnapshot | None


class AdaptivePerformanceManager:
    """Learns smooth setting adjustments from telemetry streams."""

    def __init__(
        self,
        target_fps: float = 60.0,
        history: int = 180,
        feature_flags: FeatureFlags | None = None,
        telemetry_collector: HardwareTelemetryCollector | None = None,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be positive")
        if history <= 0:
            raise ValueError("history must be positive")
        self._target_fps = target_fps
        self._history: Deque[PerformanceSample] = deque(maxlen=history)
        self._feature_flags = feature_flags or FeatureFlags()
        self._telemetry = telemetry_collector if self._feature_flags.hardware_telemetry else None

    def update(self, sample: PerformanceSample) -> PerformanceRecommendation:
        """Ingest telemetry and emit a fresh recommendation."""

        if sample.fps <= 0 or sample.frame_time_ms <= 0:
            raise ValueError("fps and frame_time_ms must be positive")
        if not 0 <= sample.cpu_util <= 100 or not 0 <= sample.gpu_util <= 100:
            raise ValueError("cpu_util and gpu_util must be within [0, 100]")

        telemetry = None
        if self._telemetry:
            telemetry = self._telemetry.snapshot()
            cpu_util = telemetry.cpu_util if telemetry.cpu_util is not None else sample.cpu_util
            gpu_util = telemetry.gpu_util if telemetry.gpu_util is not None else sample.gpu_util
        else:
            cpu_util = sample.cpu_util
            gpu_util = sample.gpu_util

        enriched_sample = PerformanceSample(
            fps=sample.fps,
            frame_time_ms=sample.frame_time_ms,
            cpu_util=cpu_util,
            gpu_util=gpu_util,
        )

        self._history.append(enriched_sample)
        fps_ratio = enriched_sample.fps / self._target_fps
        load = (enriched_sample.cpu_util + enriched_sample.gpu_util) / 200.0
        frame_pressure = enriched_sample.frame_time_ms / (1000.0 / self._target_fps)

        scaling_factor = self._compute_scaling(fps_ratio, load, frame_pressure)
        quality_shift = self._determine_quality_shift(fps_ratio, load)
        confidence = self._confidence()
        narrative = self._compose_narrative(fps_ratio, quality_shift)

        return PerformanceRecommendation(
            scaling_factor=round(scaling_factor, 3),
            quality_shift=quality_shift,
            confidence=round(confidence, 3),
            narrative=narrative,
            hardware_snapshot=telemetry,
        )

    def _compute_scaling(self, fps_ratio: float, load: float, frame_pressure: float) -> float:
        adjustment = 1.0
        adjustment -= max(0.0, 1.0 - fps_ratio) * 0.2
        adjustment -= max(0.0, load - 0.85) * 0.3
        adjustment -= max(0.0, frame_pressure - 1.0) * 0.25
        adjustment += max(0.0, fps_ratio - 1.2) * 0.1
        return min(1.25, max(0.5, adjustment))

    def _determine_quality_shift(self, fps_ratio: float, load: float) -> int:
        if fps_ratio < 0.92 or load > 0.95:
            return -2
        if fps_ratio < 0.98 or load > 0.9:
            return -1
        if fps_ratio > 1.25 and load < 0.7:
            return 1
        return 0

    def _confidence(self) -> float:
        history_len = len(self._history)
        capacity = self._history.maxlen or 1
        return min(1.0, history_len / (0.35 * capacity))

    def _compose_narrative(self, fps_ratio: float, quality_shift: int) -> str:
        if quality_shift < 0:
            tone = "Pare visuals back; stability precedes spectacle."
        elif quality_shift > 0:
            tone = "Performance headroom invites richer detail—paint the battlefield vivid."
        else:
            tone = "Hold the line—balance between clarity and velocity is on point."
        momentum = "Under target" if fps_ratio < 1 else "At pace" if fps_ratio < 1.15 else "Surplus"
        return f"{momentum}: {tone}"

    def reset(self) -> None:
        """Clear accumulated telemetry."""

        self._history.clear()
