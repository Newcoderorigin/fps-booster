from __future__ import annotations

import math

from fps_booster.adaptive_quality_manager import (
    AdaptiveQualityManager,
    GraphicsConfig,
    RidgeRegressor,
    RollingWindow,
    TelemetrySample,
)


def make_sample(frame_time: float, fps: float | None = None) -> TelemetrySample:
    fps = fps or 1000.0 / frame_time
    return TelemetrySample(fps=fps, gpu_temp=65.0, cpu_usage=55.0, frame_time_ms=frame_time)


def test_manager_scales_down_when_frame_time_is_high() -> None:
    window = RollingWindow(capacity=10)
    manager = AdaptiveQualityManager(window=window, regressor=RidgeRegressor(alpha=1e-2))
    config = GraphicsConfig(resolution_scale=0.95, ambient_occlusion="high", shadow_distance="long")

    for frame_time in [18.0, 19.0, 17.5, 18.5, 20.0]:
        manager.update(make_sample(frame_time), config)

    recommendation = manager.update(make_sample(21.0), config)

    assert recommendation.resolution_scale <= config.resolution_scale
    if recommendation.resolution_scale == config.resolution_scale:
        assert recommendation.ambient_occlusion in {"medium", "low", "off"}


def test_manager_scales_up_when_margin_is_positive() -> None:
    window = RollingWindow(capacity=10)
    manager = AdaptiveQualityManager(window=window, regressor=RidgeRegressor(alpha=1e-2))
    config = GraphicsConfig(resolution_scale=0.85, ambient_occlusion="medium", shadow_distance="medium")

    for frame_time in [12.0, 13.0, 12.5, 13.5, 12.8]:
        manager.update(make_sample(frame_time), config)

    recommendation = manager.update(make_sample(12.2), config)

    assert recommendation.resolution_scale >= config.resolution_scale


def test_clamp_prevents_invalid_configuration() -> None:
    config = GraphicsConfig(resolution_scale=1.2, ambient_occlusion="ultra", shadow_distance="distant")

    clamped = config.clamp()

    assert math.isclose(clamped.resolution_scale, 1.0)
    assert clamped.ambient_occlusion == "medium"
    assert clamped.shadow_distance == "medium"
