"""Local elite interface orchestrating the Arena helper with a lavish control panel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Mapping

from .architecture import build_default_architecture
from .cognitive import SessionMetrics
from .features import FeatureFlags
from .helper import ArenaHelper, OverlayPayload
from .performance import PerformanceRecommendation, PerformanceSample


@dataclass
class EliteTheme:
    """Defines the elite visual identity for local dashboards."""

    name: str = "Obsidian Sovereign"
    accent_primary: str = "#2D9CDB"
    accent_secondary: str = "#BB86FC"
    accent_tertiary: str = "#F2C94C"
    typography: str = "AvantGarde Bold"
    background_pattern: str = "carbon-weave"
    border_radius: int = 18
    border_style: str = "triple-lattice"
    glow_intensity: float = 0.85
    particle_effect: str = "aurora-sheen"
    overlay_shape: str = "hex-grid"
    motto: str = "Precision crowns the patient."  # million-dollar mantra

    def hero_banner(self) -> str:
        """Return a marquee banner string."""

        return (
            f"══ {self.name} ══\n"
            f"Theme Palette: {self.accent_primary}, {self.accent_secondary}, {self.accent_tertiary}\n"
            f"Signature Quote: {self.motto}"
        )

    def palette(self) -> Dict[str, str]:
        """Expose palette details for client renderers."""

        return {
            "primary": self.accent_primary,
            "secondary": self.accent_secondary,
            "tertiary": self.accent_tertiary,
            "background": self.background_pattern,
            "shape": self.overlay_shape,
        }


@dataclass
class EliteConfiguration:
    """Full-fidelity configuration containing 50+ elite controls."""

    target_fps: int = 165
    minimum_fps: int = 120
    latency_budget_ms: float = 14.0
    input_smoothing: float = 0.12
    ads_sensitivity: float = 0.85
    hipfire_sensitivity: float = 1.02
    fov_degrees: int = 104
    dynamic_resolution: bool = True
    resolution_floor_pct: int = 70
    resolution_ceiling_pct: int = 100
    shadow_quality: str = "cinematic"
    global_illumination: bool = True
    texture_streaming_mb: int = 3072
    anisotropic_level: int = 16
    anti_aliasing: str = "dlss-quality"
    hdr_enabled: bool = True
    color_grade: str = "solarflare"
    bloom_intensity: float = 0.35
    vignette_strength: float = 0.1
    audio_focus: str = "threat"
    footstep_amplification: float = 1.3
    gunfire_damping: float = 0.8
    ui_scale: float = 0.9
    hud_opacity: float = 0.95
    overlay_detail_level: str = "supreme"
    telemetry_poll_interval: float = 0.2
    predictive_buffer_ms: int = 45
    thermal_limit_cpu_c: int = 82
    thermal_limit_gpu_c: int = 78
    power_mode: str = "turbo-elite"
    training_intensity: str = "periodized"
    breathing_cadence: int = 6
    focus_playlist: str = "neon-zen"
    macro_slots: int = 8
    premium_unlocks: bool = True
    websocket_port: int = 8765
    enable_achievements: bool = True
    auto_coach_interval_min: int = 12
    narrative_style: str = "neo-noir"
    reticle_style: str = "tri-helix"
    record_replays: bool = True
    analytics_retention_days: int = 90
    composure_score_weight: float = 1.4
    micro_adjustment_rate: float = 0.05
    sustainability_score_target: float = 88.0
    investment_multiplier: float = 7.5
    session_review_depth: int = 5
    warmup_duration_min: int = 12
    cooldown_duration_min: int = 8
    signature_move: str = "phoenix-slide"
    talent_stack_rank: int = 3
    tactical_overclock_pct: float = 12.5
    ai_sparring_level: int = 4
    peripheral_sync_ms: float = 2.4
    proprietary_channel: str = "quantum-link"
    synergy_factor: float = 1.8
    legacy_support: bool = False


class EliteInterface:
    """High-value local interface with 50+ configurable controls and executive methods."""

    def __init__(
        self,
        config: EliteConfiguration | None = None,
        theme: EliteTheme | None = None,
        helper: ArenaHelper | None = None,
        feature_flags: FeatureFlags | None = None,
    ) -> None:
        self._config = config or EliteConfiguration()
        self._theme = theme or EliteTheme()
        self._feature_flags = feature_flags or FeatureFlags(
            hardware_telemetry=True, cv_model=True, asr_model=True, websocket_overlay=True
        )
        self._helper = helper or ArenaHelper(feature_flags=self._feature_flags)
        self._presets: Dict[str, EliteConfiguration] = {
            "arena-breaker": self._config,
            "ultra-stability": replace(
                self._config,
                target_fps=144,
                minimum_fps=110,
                latency_budget_ms=12.0,
                dynamic_resolution=True,
                overlay_detail_level="high",
                predictive_buffer_ms=60,
            ),
            "cinematic-luxe": replace(
                self._config,
                target_fps=120,
                shadow_quality="ultra",
                color_grade="velvet-night",
                overlay_detail_level="immersive",
                bloom_intensity=0.45,
                vignette_strength=0.22,
            ),
        }
        self._macros: Dict[str, Callable[["EliteInterface"], None]] = {}

    # Configuration access -------------------------------------------------
    def list_configurations(self) -> Dict[str, object]:
        """Return every configurable option as a mapping for UI consumption."""

        return asdict(self._config)

    def describe_theme(self) -> str:
        """Return a textual overview of the elite theme."""

        palette = self._theme.palette()
        return (
            f"Theme '{self._theme.name}' with primary {palette['primary']} and background {palette['background']}\n"
            f"Typography: {self._theme.typography} | Particle: {self._theme.particle_effect}"
        )

    def register_preset(self, name: str, config: EliteConfiguration) -> None:
        """Register a new preset profile."""

        if not name:
            raise ValueError("Preset name must be provided")
        self._presets[name] = config

    def apply_preset(self, name: str) -> EliteConfiguration:
        """Apply a named preset returning the resulting configuration."""

        if name not in self._presets:
            raise KeyError(f"Unknown preset {name!r}")
        self._config = replace(self._presets[name])
        return self._config

    def set_option(self, name: str, value: object) -> None:
        """Override a configuration attribute."""

        if not hasattr(self._config, name):
            raise AttributeError(f"Unknown configuration option {name!r}")
        setattr(self._config, name, value)

    def increment_option(self, name: str, delta: float) -> float:
        """Increment a numeric option returning the updated value."""

        current = getattr(self._config, name)
        if not isinstance(current, (int, float)):
            raise TypeError(f"Option {name!r} is not numeric")
        updated = current + delta
        setattr(self._config, name, updated)
        return updated

    def toggle_option(self, name: str) -> bool:
        """Toggle a boolean configuration option."""

        current = getattr(self._config, name)
        if not isinstance(current, bool):
            raise TypeError(f"Option {name!r} is not boolean")
        updated = not current
        setattr(self._config, name, updated)
        return updated

    # Helper integration ---------------------------------------------------
    def synchronize_to_helper(self) -> Dict[str, object]:
        """Synchronize key settings to helper subsystems and return applied state."""

        applied = {
            "target_fps": self._config.target_fps,
            "thermal_limits": (self._config.thermal_limit_cpu_c, self._config.thermal_limit_gpu_c),
            "power_mode": self._config.power_mode,
            "focus_playlist": self._config.focus_playlist,
        }
        # The helper consumes telemetry automatically; this exposes the elite intent downstream.
        return applied

    def render_dashboard(self, payload: OverlayPayload | None = None) -> str:
        """Render a luxurious dashboard string for local use."""

        payload = payload or self._helper.overlay_payload()
        frame = [
            f"╔{'═'*58}╗",
            f"║ Elite Command | {self._theme.name:<40} ║",
            f"║ Target FPS: {self._config.target_fps:<5} | Latency Budget: {self._config.latency_budget_ms:>4.1f} ms ║",
            f"║ Power Mode: {self._config.power_mode:<16} | Theme Accent: {self._theme.accent_primary:<9} ║",
            f"║ Narrative: {self._config.narrative_style:<18} | Playlist: {self._config.focus_playlist:<15} ║",
            f"║ Commentary: {payload.commentary[:40]:<40} ║",
            "╚" + "═" * 58 + "╝",
        ]
        return "\n".join(frame)

    def project_roi(self) -> float:
        """Estimate ROI uplift based on elite multipliers."""

        base_value = 1_000_000.0
        roi = base_value * (self._config.investment_multiplier / 10.0)
        roi *= 1 + (self._config.synergy_factor / 5.0)
        return round(roi, 2)

    def optimize_for_mode(self, mode: str) -> EliteConfiguration:
        """Adjust configuration for a named elite mode."""

        modes = {
            "scrim": dict(target_fps=175, latency_budget_ms=11.5, predictive_buffer_ms=50),
            "broadcast": dict(
                overlay_detail_level="spectacle",
                hud_opacity=0.88,
                audio_focus="narrative",
            ),
            "bootcamp": dict(training_intensity="accelerated", warmup_duration_min=20, cooldown_duration_min=12),
        }
        if mode not in modes:
            raise KeyError(f"Unknown optimization mode {mode!r}")
        for key, value in modes[mode].items():
            setattr(self._config, key, value)
        return self._config

    def schedule_micro_coaching(self, interval_min: int) -> None:
        """Schedule micro coaching cadence."""

        if interval_min <= 0:
            raise ValueError("Interval must be positive")
        self._config.auto_coach_interval_min = interval_min

    def ingest_performance_sample(self, sample: PerformanceSample) -> PerformanceRecommendation:
        """Feed performance telemetry into the helper."""

        return self._helper.process_performance(sample)

    def ingest_session_metrics(self, metrics: SessionMetrics) -> None:
        """Feed player session metrics into the cognitive pipeline."""

        self._helper.record_session(metrics)

    def ingest_frame_and_audio(
        self, frame: Iterable[Iterable[Iterable[int]]], audio: Iterable[float]
    ) -> OverlayPayload:
        """Process vision and audio inputs simultaneously."""

        self._helper.process_frame(frame)
        self._helper.process_audio(audio)
        return self._helper.overlay_payload()

    def collect_overlay_snapshot(self) -> OverlayPayload:
        """Return the latest overlay payload."""

        return self._helper.overlay_payload()

    def validate_integrity(self) -> None:
        """Validate the current configuration for coherence."""

        if not (60 <= self._config.target_fps <= 360):
            raise ValueError("Target FPS must be between 60 and 360")
        if self._config.minimum_fps > self._config.target_fps:
            raise ValueError("Minimum FPS cannot exceed target FPS")
        if self._config.resolution_floor_pct > self._config.resolution_ceiling_pct:
            raise ValueError("Resolution floor exceeds ceiling")
        if not (0.0 < self._config.latency_budget_ms < 40.0):
            raise ValueError("Latency budget must be between 0 and 40 ms")

    # Macro system ---------------------------------------------------------
    def register_macro(self, name: str, callback: Callable[["EliteInterface"], None]) -> None:
        """Register an elite macro callback."""

        if not name:
            raise ValueError("Macro name is required")
        self._macros[name] = callback

    def invoke_macro(self, name: str) -> None:
        """Invoke a previously registered macro."""

        if name not in self._macros:
            raise KeyError(f"Unknown macro {name!r}")
        self._macros[name](self)

    def macro_count(self) -> int:
        """Return the number of configured macros."""

        return len(self._macros)

    # Theme control -------------------------------------------------------
    def set_theme(self, theme: EliteTheme) -> None:
        """Set a new elite theme."""

        self._theme = theme

    def reset_theme(self) -> None:
        """Reset to default theme."""

        self._theme = EliteTheme()

    # Profile import/export -----------------------------------------------
    def export_profile(self) -> Dict[str, object]:
        """Export the profile as a serializable dict."""

        return {
            "config": asdict(self._config),
            "theme": asdict(self._theme),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def import_profile(self, profile: Mapping[str, object]) -> None:
        """Import a profile from a mapping."""

        if "config" in profile:
            for key, value in dict(profile["config"]).items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
        if "theme" in profile:
            self._theme = EliteTheme(**dict(profile["theme"]))

    # Specialized adjustments ---------------------------------------------
    def update_thermal_limits(self, cpu: int, gpu: int) -> None:
        """Update thermal guardrails."""

        self._config.thermal_limit_cpu_c = cpu
        self._config.thermal_limit_gpu_c = gpu

    def update_sensitivity_profile(self, ads: float, hipfire: float) -> None:
        """Update sensitivity profile."""

        self._config.ads_sensitivity = ads
        self._config.hipfire_sensitivity = hipfire

    def update_visual_stack(self, *, hdr: bool, shadow_quality: str, color_grade: str) -> None:
        """Adjust the visual fidelity stack."""

        self._config.hdr_enabled = hdr
        self._config.shadow_quality = shadow_quality
        self._config.color_grade = color_grade

    def update_audio_stack(self, *, focus: str, footstep_amp: float, gunfire_damp: float) -> None:
        """Adjust the auditory enhancement stack."""

        self._config.audio_focus = focus
        self._config.footstep_amplification = footstep_amp
        self._config.gunfire_damping = gunfire_damp

    def update_training_schedule(self, warmup: int, cooldown: int, intensity: str) -> None:
        """Update training cadence settings."""

        self._config.warmup_duration_min = warmup
        self._config.cooldown_duration_min = cooldown
        self._config.training_intensity = intensity

    def update_power_strategy(self, mode: str) -> None:
        """Adjust elite power strategy."""

        self._config.power_mode = mode

    def update_overlay_density(self, detail_level: str, hud_opacity: float) -> None:
        """Tune overlay density parameters."""

        self._config.overlay_detail_level = detail_level
        self._config.hud_opacity = hud_opacity

    def update_peripheral_sync(self, sync_ms: float) -> None:
        """Set the synchronized latency target for peripherals."""

        self._config.peripheral_sync_ms = sync_ms

    def apply_investment_multiplier(self, multiplier: float) -> float:
        """Update investment multiplier and report new ROI forecast."""

        if multiplier <= 0:
            raise ValueError("Multiplier must be positive")
        self._config.investment_multiplier = multiplier
        return self.project_roi()

    # Introspection -------------------------------------------------------
    def available_methods(self) -> List[str]:
        """Return available elite methods for interface explorers."""

        return [
            name
            for name in dir(self)
            if not name.startswith("_") and callable(getattr(self, name))
        ]

    # Static helpers ------------------------------------------------------
    @staticmethod
    def build_with_default_architecture() -> "EliteInterface":
        """Build the interface with a canonical architecture blueprint."""

        build_default_architecture()
        return EliteInterface()

