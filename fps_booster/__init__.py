"""Arena helper toolkit for compliant performance and insight augmentation."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict, Tuple

__all__ = [
    "AdaptivePerformanceManager",
    "ArenaHelper",
    "AudioAnalyzer",
    "AudioReport",
    "CognitiveCoach",
    "FeatureFlags",
    "EliteConfiguration",
    "EliteInterface",
    "EliteTheme",
    "HardwareSnapshot",
    "HardwareTelemetryCollector",
    "KeywordSpotter",
    "ModuleBlueprint",
    "OverlayEventBroadcaster",
    "PerformanceRecommendation",
    "PerformanceSample",
    "ReactiveDashboard",
    "ReactiveDashboardState",
    "ReactiveDashboardViewModel",
    "ReactiveTheme",
    "MetricPulse",
    "PracticeRecommendation",
    "SessionMetrics",
    "VisionAnalyzer",
    "VisionReport",
    "YOLOAdapter",
    "build_default_architecture",
]

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "AdaptivePerformanceManager": ("fps_booster.performance", "AdaptivePerformanceManager"),
    "ArenaHelper": ("fps_booster.helper", "ArenaHelper"),
    "AudioAnalyzer": ("fps_booster.audio", "AudioAnalyzer"),
    "AudioReport": ("fps_booster.audio", "AudioReport"),
    "CognitiveCoach": ("fps_booster.cognitive", "CognitiveCoach"),
    "FeatureFlags": ("fps_booster.features", "FeatureFlags"),
    "EliteConfiguration": ("fps_booster.interface", "EliteConfiguration"),
    "EliteInterface": ("fps_booster.interface", "EliteInterface"),
    "EliteTheme": ("fps_booster.interface", "EliteTheme"),
    "HardwareSnapshot": ("fps_booster.integrations", "HardwareSnapshot"),
    "HardwareTelemetryCollector": ("fps_booster.integrations", "HardwareTelemetryCollector"),
    "KeywordSpotter": ("fps_booster.integrations", "KeywordSpotter"),
    "ModuleBlueprint": ("fps_booster.architecture", "ModuleBlueprint"),
    "OverlayEventBroadcaster": ("fps_booster.integrations", "OverlayEventBroadcaster"),
    "PerformanceRecommendation": ("fps_booster.performance", "PerformanceRecommendation"),
    "PerformanceSample": ("fps_booster.performance", "PerformanceSample"),
    "ReactiveDashboard": ("fps_booster.gui", "ReactiveDashboard"),
    "ReactiveDashboardState": ("fps_booster.gui", "ReactiveDashboardState"),
    "ReactiveDashboardViewModel": ("fps_booster.gui", "ReactiveDashboardViewModel"),
    "ReactiveTheme": ("fps_booster.gui", "ReactiveTheme"),
    "MetricPulse": ("fps_booster.gui", "MetricPulse"),
    "PracticeRecommendation": ("fps_booster.cognitive", "PracticeRecommendation"),
    "SessionMetrics": ("fps_booster.cognitive", "SessionMetrics"),
    "VisionAnalyzer": ("fps_booster.vision", "VisionAnalyzer"),
    "VisionReport": ("fps_booster.vision", "VisionReport"),
    "YOLOAdapter": ("fps_booster.integrations", "YOLOAdapter"),
    "build_default_architecture": ("fps_booster.architecture", "build_default_architecture"),
}

if TYPE_CHECKING:  # pragma: no cover - for static analysers only
    from .architecture import ModuleBlueprint, build_default_architecture
    from .audio import AudioAnalyzer, AudioReport
    from .cognitive import CognitiveCoach, PracticeRecommendation, SessionMetrics
    from .features import FeatureFlags
    from .interface import EliteConfiguration, EliteInterface, EliteTheme
    from .gui import MetricPulse, ReactiveDashboard, ReactiveDashboardState, ReactiveDashboardViewModel, ReactiveTheme
    from .helper import ArenaHelper
    from .integrations import (
        HardwareSnapshot,
        HardwareTelemetryCollector,
        KeywordSpotter,
        OverlayEventBroadcaster,
        YOLOAdapter,
    )
    from .performance import (
        AdaptivePerformanceManager,
        PerformanceRecommendation,
        PerformanceSample,
    )
    from .vision import VisionAnalyzer, VisionReport


def __getattr__(name: str) -> Any:
    """Lazily import public objects on first access."""

    if name not in _EXPORTS:
        raise AttributeError(f"module 'fps_booster' has no attribute {name!r}")
    module_name, attr = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return available attributes for auto-completion tools."""

    return sorted(set(list(globals().keys()) + __all__))
"""FPS Booster toolkit."""

from .system_optimization import BackgroundTask, SystemOptimizer
from .adaptive_quality_manager import (
    AdaptiveQualityManager,
    GraphicsConfig,
    TelemetrySample,
)

__all__.extend(
    [
        "AdaptiveQualityManager",
        "BackgroundTask",
        "GraphicsConfig",
        "SystemOptimizer",
        "TelemetrySample",
    ]
)
