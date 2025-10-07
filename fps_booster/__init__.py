"""Arena helper toolkit for compliant performance and insight augmentation."""

from .architecture import ModuleBlueprint, build_default_architecture
from .audio import AudioAnalyzer, AudioReport
from .cognitive import CognitiveCoach, PracticeRecommendation, SessionMetrics
from .features import FeatureFlags
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

__all__ = [
    "AdaptivePerformanceManager",
    "ArenaHelper",
    "AudioAnalyzer",
    "AudioReport",
    "CognitiveCoach",
    "FeatureFlags",
    "HardwareSnapshot",
    "HardwareTelemetryCollector",
    "KeywordSpotter",
    "ModuleBlueprint",
    "OverlayEventBroadcaster",
    "PerformanceRecommendation",
    "PerformanceSample",
    "PracticeRecommendation",
    "SessionMetrics",
    "VisionAnalyzer",
    "VisionReport",
    "YOLOAdapter",
    "build_default_architecture",
]
