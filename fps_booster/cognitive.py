"""Cognitive feedback loop for player-oriented coaching."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import List


@dataclass(frozen=True)
class SessionMetrics:
    """Captures outcome metrics from a play session or drill."""

    reaction_time: float
    accuracy: float
    stress_index: float


@dataclass(frozen=True)
class PracticeRecommendation:
    """Represents a suggested focus area and prompt."""

    focus_area: str
    drill_duration: int
    prompt: str


class CognitiveCoach:
    """Learns player tendencies and proposes targeted practice."""

    def __init__(self, history: int = 50) -> None:
        if history <= 0:
            raise ValueError("history must be positive")
        self._history: List[SessionMetrics] = []
        self._capacity = history

    def record_session(self, metrics: SessionMetrics) -> None:
        """Persist a set of observed metrics."""

        if metrics.reaction_time <= 0:
            raise ValueError("reaction_time must be positive")
        if not 0.0 <= metrics.accuracy <= 1.0:
            raise ValueError("accuracy must be within [0, 1]")
        if not 0.0 <= metrics.stress_index <= 1.0:
            raise ValueError("stress_index must be within [0, 1]")
        self._history.append(metrics)
        if len(self._history) > self._capacity:
            self._history.pop(0)

    def recommend_practice(self) -> PracticeRecommendation:
        """Generate a drill recommendation based on stored sessions."""

        if not self._history:
            return PracticeRecommendation(
                focus_area="baseline",
                drill_duration=5,
                prompt="Warm up with precision flicks; collect metrics before tailoring guidance.",
            )

        avg_reaction = mean(m.reaction_time for m in self._history)
        avg_accuracy = mean(m.accuracy for m in self._history)
        avg_stress = mean(m.stress_index for m in self._history)

        focus_area = self._select_focus(avg_reaction, avg_accuracy, avg_stress)
        drill_duration = self._duration_for_focus(focus_area)
        prompt = self._compose_prompt(focus_area, avg_reaction, avg_accuracy, avg_stress)
        return PracticeRecommendation(focus_area=focus_area, drill_duration=drill_duration, prompt=prompt)

    def _select_focus(self, reaction: float, accuracy: float, stress: float) -> str:
        if reaction > 0.32:
            return "reflex"
        if accuracy < 0.55:
            return "precision"
        if stress > 0.65:
            return "calm"
        return "refine"

    @staticmethod
    def _duration_for_focus(focus: str) -> int:
        mapping = {"reflex": 6, "precision": 7, "calm": 4, "refine": 5}
        return mapping.get(focus, 5)

    def _compose_prompt(self, focus: str, reaction: float, accuracy: float, stress: float) -> str:
        if focus == "reflex":
            return "Time-slice drills: track flick targets for 6 minutes; embrace disciplined breathing between bursts."
        if focus == "precision":
            return "Grid micro-corrections: slow deliberate shots for 7 minutes to align muscle memory."
        if focus == "calm":
            return "Breathing cadence plus low-intensity tracking; center yourself, let tension dissolve before live rounds."
        return (
            "Consistency weave: alternate high/low sensitivity scenarios; stay curious, narrate each adjustment like a strategist."
        )

    def reset(self) -> None:
        """Forget stored history."""

        self._history.clear()
