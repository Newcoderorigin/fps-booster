"""FPS Booster toolkit."""

from .system_optimization import BackgroundTask, SystemOptimizer
from .adaptive_quality_manager import (
    AdaptiveQualityManager,
    GraphicsConfig,
    TelemetrySample,
)

__all__ = [
    "AdaptiveQualityManager",
    "BackgroundTask",
    "GraphicsConfig",
    "SystemOptimizer",
    "TelemetrySample",
]
