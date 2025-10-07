"""Feature flag management for the Arena helper."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlags:
    """Container for helper feature toggles."""

    hardware_telemetry: bool = False
    cv_model: bool = False
    asr_model: bool = False
    websocket_overlay: bool = False

    def enabled(self, name: str) -> bool:
        """Return True when the named feature is enabled."""

        mapping = {
            "hardware_telemetry": self.hardware_telemetry,
            "cv_model": self.cv_model,
            "asr_model": self.asr_model,
            "websocket_overlay": self.websocket_overlay,
        }
        if name not in mapping:
            raise KeyError(f"Unknown feature flag: {name}")
        return mapping[name]
