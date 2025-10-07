"""Reactive GUI helpers for the Arena helper toolkit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Sequence

from .cognitive import SessionMetrics
from .helper import ArenaHelper, OverlayPayload
from .performance import PerformanceRecommendation, PerformanceSample


@dataclass(frozen=True)
class MetricPulse:
    """Represents a single metric tile in the dashboard."""

    label: str
    value: str
    unit: str
    status: str
    trend: str
    emphasis: str


@dataclass(frozen=True)
class ReactiveDashboardState:
    """Immutable representation of the dashboard render state."""

    timestamp: datetime
    metrics: Sequence[MetricPulse]
    theme_palette: Dict[str, str | float]
    commentary: str
    practice_prompt: str
    hero_banner: str


@dataclass(frozen=True)
class ReactiveTheme:
    """Encodes a vivid, responsive visual identity for the dashboard."""

    name: str = "Luminal Flux"
    background_base: str = "#070A18"
    accent_core: str = "#48E5C2"
    accent_peak: str = "#56CCF2"
    accent_low: str = "#F5A623"
    accent_floor: str = "#262C4A"
    warning: str = "#FFE066"
    danger: str = "#FF2D55"
    success: str = "#6BF178"
    text_primary: str = "#F8F9FF"
    text_muted: str = "#8A90B8"
    grid_glow: str = "#3A3F5C"

    def hero_banner(self) -> str:
        """Return a banner string summarizing the theme."""

        return (
            f"══ {self.name} ══\n"
            f"Accent Flow: {self.accent_core} → {self.accent_peak} → {self.accent_low}\n"
            "Metrics pulse in sync with telemetry."
        )

    def palette_for(self, fps_ratio: float, stress_index: float) -> Dict[str, str | float]:
        """Return a palette tuned to the supplied performance and stress readings."""

        ratio = max(0.0, min(fps_ratio, 1.6))
        stress = max(0.0, min(stress_index, 1.0))
        calm_blend = 1.0 - min(1.0, ratio)
        stress_blend = stress ** 0.5

        accent_primary = self._blend(self.accent_peak, self.danger, stress_blend * 0.65)
        accent_secondary = self._blend(self.accent_core, self.warning, 0.35 + calm_blend * 0.4)
        accent_tertiary = self._blend(self.accent_low, self.success, ratio * 0.6)
        background = self._blend(self.background_base, "#02030A", calm_blend * 0.5 + stress * 0.15)

        intensity = round(0.45 + ratio * 0.35 + (1.0 - stress) * 0.2, 3)
        pulse = "surge" if ratio >= 1.15 and stress < 0.45 else "steady" if ratio >= 0.92 else "brace"

        return {
            "background": background,
            "accent_primary": accent_primary,
            "accent_secondary": accent_secondary,
            "accent_tertiary": accent_tertiary,
            "grid_glow": self.grid_glow,
            "text_primary": self.text_primary,
            "text_muted": self.text_muted,
            "intensity": intensity,
            "pulse": pulse,
        }

    @staticmethod
    def _blend(color_a: str, color_b: str, factor: float) -> str:
        """Blend two hex colors by the supplied factor (0 → a, 1 → b)."""

        clamp = max(0.0, min(factor, 1.0))
        r1, g1, b1 = ReactiveTheme._hex_to_rgb(color_a)
        r2, g2, b2 = ReactiveTheme._hex_to_rgb(color_b)
        blended = (
            int(round(r1 + (r2 - r1) * clamp)),
            int(round(g1 + (g2 - g1) * clamp)),
            int(round(b1 + (b2 - b1) * clamp)),
        )
        return ReactiveTheme._rgb_to_hex(blended)

    @staticmethod
    def _hex_to_rgb(color: str) -> tuple[int, int, int]:
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb: Iterable[int]) -> str:
        return "#" + "".join(f"{value:02X}" for value in rgb)


class ReactiveDashboardViewModel:
    """Transforms helper payloads into GUI-friendly render states."""

    def __init__(
        self,
        theme: ReactiveTheme | None = None,
        target_fps: float = 165.0,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be positive")
        self._theme = theme or ReactiveTheme()
        self._target_fps = target_fps
        self._payload: OverlayPayload | None = None
        self._performance_sample: PerformanceSample | None = None
        self._session_metrics: SessionMetrics | None = None
        self._last_state: ReactiveDashboardState | None = None

    @property
    def theme(self) -> ReactiveTheme:
        """Return the active theme."""

        return self._theme

    def apply_payload(self, payload: OverlayPayload) -> None:
        """Store the latest overlay payload for rendering."""

        self._payload = payload

    def ingest_performance_sample(self, sample: PerformanceSample) -> None:
        """Persist the latest raw performance sample."""

        self._performance_sample = sample

    def ingest_session_metrics(self, metrics: SessionMetrics) -> None:
        """Persist the latest session metrics."""

        self._session_metrics = metrics

    def render_state(self) -> ReactiveDashboardState:
        """Return a snapshot of the dashboard state derived from stored data."""

        fps_ratio = self._fps_ratio()
        stress = self._session_metrics.stress_index if self._session_metrics else 0.35
        palette = self._theme.palette_for(fps_ratio, stress)
        state = ReactiveDashboardState(
            timestamp=datetime.utcnow(),
            metrics=tuple(self._compose_metrics()),
            theme_palette=palette,
            commentary=self._payload.commentary if self._payload else "Awaiting telemetry pulse.",
            practice_prompt=(
                self._payload.practice.prompt
                if self._payload and self._payload.practice
                else "Prime focus routines will appear once sessions stream in."
            ),
            hero_banner=self._theme.hero_banner(),
        )
        self._last_state = state
        return state

    def last_state(self) -> ReactiveDashboardState | None:
        """Return the most recently rendered state, if any."""

        return self._last_state

    def _compose_metrics(self) -> List[MetricPulse]:
        metrics: List[MetricPulse] = []
        recommendation: PerformanceRecommendation | None = None
        if self._payload and self._payload.performance:
            recommendation = self._payload.performance

        if self._performance_sample:
            metrics.extend(self._performance_metrics(self._performance_sample, recommendation))

        if self._session_metrics:
            metrics.extend(self._session_metric_pulses(self._session_metrics))

        if self._payload and self._payload.audio:
            metrics.append(
                MetricPulse(
                    label="Audio Pulse",
                    value=f"{self._payload.audio.dominant_frequency:.0f}",
                    unit="Hz",
                    status=self._status_from_band(self._payload.audio.event_confidence, (0.5, 0.8)),
                    trend=f"confidence {self._payload.audio.event_confidence:.2f}",
                    emphasis="tertiary",
                )
            )

        if self._payload and self._payload.vision:
            motion = self._payload.vision.movement_score
            metrics.append(
                MetricPulse(
                    label="Visual Motion",
                    value=f"{motion:.2f}",
                    unit="Δ",
                    status=self._status_from_band(motion, (0.35, 0.55), invert=False),
                    trend="annotations" if self._payload.vision.annotations else "steady",
                    emphasis="secondary",
                )
            )

        return metrics

    def _performance_metrics(
        self,
        sample: PerformanceSample,
        recommendation: PerformanceRecommendation | None,
    ) -> List[MetricPulse]:
        ratio = sample.fps / self._target_fps
        trend = "steady"
        if recommendation:
            if recommendation.quality_shift > 0:
                trend = "upshift ↑"
            elif recommendation.quality_shift < 0:
                trend = "stabilize ↓"
            else:
                trend = "hold →"

        return [
            MetricPulse(
                label="Framerate",
                value=f"{sample.fps:.1f}",
                unit="fps",
                status=self._status_from_band(ratio, (0.9, 1.05), invert=False),
                trend=trend,
                emphasis="primary",
            ),
            MetricPulse(
                label="Frame Time",
                value=f"{sample.frame_time_ms:.1f}",
                unit="ms",
                status=self._status_from_band(sample.frame_time_ms, (9.0, 16.0)),
                trend="smooth" if ratio >= 1.0 else "pressure",
                emphasis="primary",
            ),
            MetricPulse(
                label="CPU Load",
                value=f"{sample.cpu_util:.0f}",
                unit="%",
                status=self._status_from_band(sample.cpu_util, (70.0, 90.0)),
                trend="balanced" if sample.cpu_util < 70 else "watch",
                emphasis="secondary",
            ),
            MetricPulse(
                label="GPU Load",
                value=f"{sample.gpu_util:.0f}",
                unit="%",
                status=self._status_from_band(sample.gpu_util, (75.0, 92.0)),
                trend="balanced" if sample.gpu_util < 75 else "watch",
                emphasis="secondary",
            ),
        ]

    def _session_metric_pulses(self, metrics: SessionMetrics) -> List[MetricPulse]:
        reaction_ms = metrics.reaction_time * 1000.0
        accuracy_pct = metrics.accuracy * 100.0
        stress_pct = metrics.stress_index * 100.0
        return [
            MetricPulse(
                label="Reaction",
                value=f"{reaction_ms:.0f}",
                unit="ms",
                status=self._status_from_band(reaction_ms, (320.0, 360.0)),
                trend="faster" if reaction_ms < 310 else "stabilize",
                emphasis="tertiary",
            ),
            MetricPulse(
                label="Accuracy",
                value=f"{accuracy_pct:.1f}",
                unit="%",
                status=self._status_from_band(accuracy_pct, (58.0, 68.0), invert=False),
                trend="climb" if accuracy_pct >= 60 else "train",
                emphasis="tertiary",
            ),
            MetricPulse(
                label="Stress",
                value=f"{stress_pct:.0f}",
                unit="%",
                status=self._status_from_band(stress_pct, (55.0, 70.0)),
                trend="compose" if stress_pct < 55 else "soothe",
                emphasis="secondary",
            ),
        ]

    def _fps_ratio(self) -> float:
        if not self._performance_sample:
            return 1.0
        return max(0.01, self._performance_sample.fps / self._target_fps)

    @staticmethod
    def _status_from_band(value: float, thresholds: tuple[float, float], invert: bool = True) -> str:
        """Return a qualitative status for a value relative to thresholds."""

        lower, upper = thresholds
        if invert:
            if value <= lower:
                return "optimal"
            if value <= upper:
                return "caution"
            return "critical"
        if value >= upper:
            return "optimal"
        if value >= lower:
            return "caution"
        return "critical"


class ReactiveDashboard:
    """Tkinter-based dashboard rendering telemetry in real time."""

    def __init__(
        self,
        helper: ArenaHelper,
        refresh_seconds: float = 0.5,
        view_model: ReactiveDashboardViewModel | None = None,
    ) -> None:
        if refresh_seconds <= 0:
            raise ValueError("refresh_seconds must be positive")
        self._helper = helper
        self._view_model = view_model or ReactiveDashboardViewModel()
        self._refresh_ms = max(int(refresh_seconds * 1000), 100)

        import tkinter as tk

        self._tk = tk
        self._root = tk.Tk()
        self._root.title(f"{self._view_model.theme.name} Metrics Console")
        self._root.configure(bg=self._view_model.theme.background_base)

        self._hero_var = tk.StringVar(value=self._view_model.theme.hero_banner())
        self._commentary_var = tk.StringVar(value="Awaiting telemetry pulse.")
        self._practice_var = tk.StringVar(value="Prime focus routines will appear once sessions stream in.")
        self._metric_vars: Dict[str, tk.StringVar] = {}
        self._metric_status: Dict[str, tk.StringVar] = {}
        self._metric_frames: Dict[str, tk.Frame] = {}

        self._build_layout()

    def _build_layout(self) -> None:
        tk = self._tk
        hero = tk.Label(
            self._root,
            textvariable=self._hero_var,
            fg=self._view_model.theme.text_primary,
            bg=self._view_model.theme.background_base,
            justify=tk.LEFT,
            font=("Helvetica", 14, "bold"),
        )
        hero.pack(padx=20, pady=(20, 10), anchor=tk.W)

        self._metrics_container = tk.Frame(self._root, bg=self._view_model.theme.background_base)
        self._metrics_container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        commentary = tk.Label(
            self._root,
            textvariable=self._commentary_var,
            fg=self._view_model.theme.text_primary,
            bg=self._view_model.theme.background_base,
            justify=tk.LEFT,
            wraplength=720,
            font=("Helvetica", 11),
        )
        commentary.pack(padx=20, pady=(10, 4), anchor=tk.W)

        practice = tk.Label(
            self._root,
            textvariable=self._practice_var,
            fg=self._view_model.theme.text_muted,
            bg=self._view_model.theme.background_base,
            justify=tk.LEFT,
            wraplength=720,
            font=("Helvetica", 10, "italic"),
        )
        practice.pack(padx=20, pady=(0, 20), anchor=tk.W)

    def start(self) -> None:
        """Begin the auto-refresh loop and enter the Tk event loop."""

        self._schedule_refresh()
        self._root.mainloop()

    def _schedule_refresh(self) -> None:
        payload = self._helper.overlay_payload()
        self._view_model.apply_payload(payload)
        sample = self._helper.last_performance_sample()
        if sample:
            self._view_model.ingest_performance_sample(sample)
        session = self._helper.last_session_metrics()
        if session:
            self._view_model.ingest_session_metrics(session)
        state = self._view_model.render_state()
        self._apply_state(state)
        self._root.after(self._refresh_ms, self._schedule_refresh)

    def _apply_state(self, state: ReactiveDashboardState) -> None:
        tk = self._tk
        palette = state.theme_palette
        self._root.configure(bg=palette["background"])
        self._metrics_container.configure(bg=palette["background"])
        self._hero_var.set(state.hero_banner)
        self._commentary_var.set(state.commentary)
        self._practice_var.set(state.practice_prompt)

        for index, pulse in enumerate(state.metrics):
            frame = self._ensure_metric_frame(pulse.label, palette, index)
            value_var = self._metric_vars[pulse.label]
            status_var = self._metric_status[pulse.label]
            value_var.set(f"{pulse.value} {pulse.unit}".strip())
            status_var.set(f"{pulse.trend} · {pulse.status}")
            accent = self._accent_for(palette, pulse.emphasis)
            frame.configure(bg=accent)

        # Hide frames not present in current state
        active_labels = {pulse.label for pulse in state.metrics}
        for label, frame in list(self._metric_frames.items()):
            if label not in active_labels:
                frame.pack_forget()

    def _ensure_metric_frame(self, label: str, palette: Dict[str, str | float], index: int) -> "tk.Frame":
        tk = self._tk
        if label in self._metric_frames:
            frame = self._metric_frames[label]
            frame.pack_configure(pady=6, padx=0)
            return frame

        frame = tk.Frame(self._metrics_container, bg=self._accent_for(palette, "secondary"), padx=12, pady=10)
        title = tk.Label(frame, text=label, fg=palette["text_primary"], bg=frame.cget("bg"), font=("Helvetica", 12, "bold"))
        value_var = tk.StringVar()
        self._metric_vars[label] = value_var
        value = tk.Label(frame, textvariable=value_var, fg=palette["text_primary"], bg=frame.cget("bg"), font=("Helvetica", 18, "bold"))
        status_var = tk.StringVar()
        self._metric_status[label] = status_var
        status = tk.Label(frame, textvariable=status_var, fg=palette["text_muted"], bg=frame.cget("bg"), font=("Helvetica", 10))

        title.pack(anchor=tk.W)
        value.pack(anchor=tk.W)
        status.pack(anchor=tk.W)

        frame.pack(side=tk.LEFT, padx=10, pady=6, ipadx=4, ipady=4)
        self._metric_frames[label] = frame
        return frame

    @staticmethod
    def _accent_for(palette: Dict[str, str | float], emphasis: str) -> str:
        match emphasis:
            case "primary":
                return str(palette["accent_primary"])
            case "secondary":
                return str(palette["accent_secondary"])
            case "tertiary":
                return str(palette["accent_tertiary"])
        return str(palette["accent_secondary"])
