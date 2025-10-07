"""High-level orchestrator that fuses subsystem insights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from .audio import AudioAnalyzer, AudioReport
from .cognitive import CognitiveCoach, PracticeRecommendation, SessionMetrics
from .features import FeatureFlags
from .integrations import (
    HardwareTelemetryCollector,
    KeywordSpotter,
    OverlayEventBroadcaster,
    YOLOAdapter,
)
from .performance import AdaptivePerformanceManager, PerformanceRecommendation, PerformanceSample
from .vision import VisionAnalyzer, VisionReport


@dataclass
class OverlayPayload:
    """Represents the combined helper output for UI layers."""

    vision: VisionReport | None
    audio: AudioReport | None
    performance: PerformanceRecommendation | None
    practice: PracticeRecommendation | None
    commentary: str


class ArenaHelper:
    """Composes the compliant helper subsystems into a cohesive assistant."""

    def __init__(
        self,
        vision: Optional[VisionAnalyzer] = None,
        audio: Optional[AudioAnalyzer] = None,
        performance: Optional[AdaptivePerformanceManager] = None,
        coach: Optional[CognitiveCoach] = None,
        feature_flags: FeatureFlags | None = None,
        broadcaster: OverlayEventBroadcaster | None = None,
        telemetry_collector: HardwareTelemetryCollector | None = None,
    ) -> None:
        self._feature_flags = feature_flags or FeatureFlags()
        if vision is None:
            detector = YOLOAdapter.heuristic() if self._feature_flags.cv_model else None
            self._vision = VisionAnalyzer(detector=detector)
        else:
            self._vision = vision
        if audio is None:
            keyword_spotter = KeywordSpotter.heuristic() if self._feature_flags.asr_model else None
            self._audio = AudioAnalyzer(sample_rate=48000, keyword_spotter=keyword_spotter)
        else:
            self._audio = audio
        collector = telemetry_collector
        if self._feature_flags.hardware_telemetry and collector is None:
            collector = HardwareTelemetryCollector()
        if performance is None:
            self._performance = AdaptivePerformanceManager(
                feature_flags=self._feature_flags,
                telemetry_collector=collector,
            )
        else:
            self._performance = performance
        self._coach = coach or CognitiveCoach()
        self._broadcaster = broadcaster
        self._last_vision: VisionReport | None = None
        self._last_audio: AudioReport | None = None
        self._last_performance: PerformanceRecommendation | None = None
        self._last_practice: PracticeRecommendation | None = None

    def process_frame(self, frame: Sequence[Sequence[Sequence[int]]]) -> VisionReport:
        """Analyze a captured frame."""

        self._last_vision = self._vision.analyze_frame(frame)
        return self._last_vision

    def process_audio(self, samples: Sequence[float]) -> AudioReport:
        """Analyze captured audio samples."""

        self._last_audio = self._audio.analyze(samples)
        return self._last_audio

    def process_performance(self, sample: PerformanceSample) -> PerformanceRecommendation:
        """Update performance recommendations."""

        self._last_performance = self._performance.update(sample)
        return self._last_performance

    def record_session(self, metrics: SessionMetrics) -> PracticeRecommendation:
        """Record player metrics and return the latest practice recommendation."""

        self._coach.record_session(metrics)
        self._last_practice = self._coach.recommend_practice()
        return self._last_practice

    def overlay_payload(self) -> OverlayPayload:
        """Return a fused overlay payload with narrative commentary."""

        commentary = self._compose_commentary()
        payload = OverlayPayload(
            vision=self._last_vision,
            audio=self._last_audio,
            performance=self._last_performance,
            practice=self._last_practice,
            commentary=commentary,
        )
        self._publish_overlay(payload)
        return payload

    def _compose_commentary(self) -> str:
        pieces = []
        if self._last_vision:
            if self._last_vision.annotations:
                pieces.append(self._last_vision.annotations[0])
            if self._last_vision.detections:
                pieces.append(f"Sightlines flag {self._last_vision.detections[0]} present.")
        if self._last_audio:
            pieces.append(
                f"Audio pulse {self._last_audio.dominant_frequency} Hz with confidence {self._last_audio.event_confidence}."
            )
            if self._last_audio.keywords:
                pieces.append(f"Audio cues whisper {', '.join(self._last_audio.keywords)}.")
        if self._last_performance:
            pieces.append(self._last_performance.narrative)
            snapshot = self._last_performance.hardware_snapshot
            if snapshot and (snapshot.cpu_temp_c or snapshot.gpu_temp_c):
                thermal = []
                if snapshot.cpu_temp_c is not None:
                    thermal.append(f"CPU {snapshot.cpu_temp_c:.1f}C")
                if snapshot.gpu_temp_c is not None:
                    thermal.append(f"GPU {snapshot.gpu_temp_c:.1f}C")
                if thermal:
                    pieces.append(f"Thermals steady: {' / '.join(thermal)}.")
        if self._last_practice:
            pieces.append(self._last_practice.prompt)
        return " ".join(pieces) if pieces else "Awaiting telemetry—embrace stillness before the storm."

    def _publish_overlay(self, payload: OverlayPayload) -> None:
        if not self._broadcaster:
            return
        serialized = {
            "vision": payload.vision.__dict__ if payload.vision else None,
            "audio": payload.audio.__dict__ if payload.audio else None,
            "performance": payload.performance.__dict__ if payload.performance else None,
            "practice": payload.practice.__dict__ if payload.practice else None,
            "commentary": payload.commentary,
        }
        self._broadcaster.publish(serialized)
