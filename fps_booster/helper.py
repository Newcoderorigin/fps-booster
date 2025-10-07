"""High-level orchestrator that fuses subsystem insights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from .audio import AudioAnalyzer, AudioReport
from .cognitive import CognitiveCoach, PracticeRecommendation, SessionMetrics
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
    ) -> None:
        self._vision = vision or VisionAnalyzer()
        if audio is None:
            raise ValueError("AudioAnalyzer must be provided with the appropriate sample rate")
        self._audio = audio
        self._performance = performance or AdaptivePerformanceManager()
        self._coach = coach or CognitiveCoach()
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
        return OverlayPayload(
            vision=self._last_vision,
            audio=self._last_audio,
            performance=self._last_performance,
            practice=self._last_practice,
            commentary=commentary,
        )

    def _compose_commentary(self) -> str:
        pieces = []
        if self._last_vision:
            pieces.append(self._last_vision.annotations[0])
        if self._last_audio:
            pieces.append(
                f"Audio pulse {self._last_audio.dominant_frequency} Hz with confidence {self._last_audio.event_confidence}."
            )
        if self._last_performance:
            pieces.append(self._last_performance.narrative)
        if self._last_practice:
            pieces.append(self._last_practice.prompt)
        return " ".join(pieces) if pieces else "Awaiting telemetry—embrace stillness before the storm."
