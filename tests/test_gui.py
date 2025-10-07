"""Tests for the reactive dashboard GUI helpers."""

from __future__ import annotations

from fps_booster.audio import AudioReport
from fps_booster.cognitive import PracticeRecommendation, SessionMetrics
from fps_booster.gui import ReactiveDashboardState, ReactiveDashboardViewModel, ReactiveTheme
from fps_booster.helper import OverlayPayload
from fps_booster.performance import PerformanceRecommendation, PerformanceSample
from fps_booster.vision import VisionReport


def test_theme_palette_reactivity() -> None:
    theme = ReactiveTheme()
    high = theme.palette_for(1.3, 0.2)
    low = theme.palette_for(0.82, 0.78)

    assert high["pulse"] == "surge"
    assert low["pulse"] == "brace"
    assert high["intensity"] > low["intensity"]
    assert high["background"] != low["background"]


def test_view_model_composes_metrics_and_palette() -> None:
    view_model = ReactiveDashboardViewModel(target_fps=120.0)
    sample = PerformanceSample(fps=144.0, frame_time_ms=6.9, cpu_util=65.0, gpu_util=70.0)
    view_model.ingest_performance_sample(sample)

    audio = AudioReport(
        dominant_frequency=440.0,
        band_energy={"mid": 0.42},
        event_confidence=0.72,
        keywords=("contact",),
    )
    vision = VisionReport(
        movement_score=0.62,
        color_clusters=(),
        annotations=("High kinetic",),
        detections=("opponent",),
    )
    recommendation = PerformanceRecommendation(
        scaling_factor=1.1,
        quality_shift=1,
        confidence=0.94,
        narrative="Surplus",
        hardware_snapshot=None,
    )
    practice = PracticeRecommendation(focus_area="precision", drill_duration=6, prompt="Sharpen focus.")
    payload = OverlayPayload(
        vision=vision,
        audio=audio,
        performance=recommendation,
        practice=practice,
        commentary="Test commentary.",
    )
    view_model.apply_payload(payload)

    session = SessionMetrics(reaction_time=0.28, accuracy=0.72, stress_index=0.42)
    view_model.ingest_session_metrics(session)

    state = view_model.render_state()

    assert isinstance(state, ReactiveDashboardState)
    metric_map = {pulse.label: pulse for pulse in state.metrics}
    assert metric_map["Framerate"].status == "optimal"
    assert metric_map["Framerate"].trend == "upshift ↑"
    assert metric_map["Accuracy"].status == "optimal"
    assert metric_map["Audio Pulse"].status == "caution"
    assert state.practice_prompt == "Sharpen focus."
    assert state.theme_palette["pulse"] == "surge"
    assert state.commentary == "Test commentary."
