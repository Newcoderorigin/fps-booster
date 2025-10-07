"""Reactive GUI helpers for the Arena helper toolkit."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterable, List, Sequence
from urllib.parse import urlparse
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
    """Serve a local web dashboard that streams helper telemetry."""
    """Tkinter-based dashboard rendering telemetry in real time."""

    def __init__(
        self,
        helper: ArenaHelper,
        refresh_seconds: float = 0.5,
        view_model: ReactiveDashboardViewModel | None = None,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        if refresh_seconds <= 0:
            raise ValueError("refresh_seconds must be positive")
        if port < 0:
            raise ValueError("port must be non-negative")
        self._helper = helper
        self._view_model = view_model or ReactiveDashboardViewModel()
        self._refresh_seconds = refresh_seconds
        self._host = host
        self._port = port
        self._httpd: _DashboardHTTPServer | None = None
        self._serve_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._lock = threading.Lock()
        self._base_url: str | None = None

    @property
    def base_url(self) -> str | None:
        """Return the base URL where the dashboard is served."""

        return self._base_url

    @property
    def refresh_seconds(self) -> float:
        """Return the refresh cadence advertised to the frontend."""

        return self._refresh_seconds

    def start(self, block: bool = True) -> None:
        """Start the HTTP server and optionally block until stopped."""

        self._start_server()
        if block:
            self.wait_forever()

    def wait_forever(self) -> None:
        """Block the caller until the dashboard is stopped."""

        try:
            while not self._stop_event.wait(timeout=0.5):
                pass
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Shut down the HTTP server and release resources."""

        self._stop_event.set()
        httpd = self._httpd
        serve_thread = self._serve_thread
        if httpd is None:
            return
        self._httpd = None
        self._serve_thread = None
        httpd.shutdown()
        httpd.server_close()
        if serve_thread:
            serve_thread.join(timeout=1.5)

    def snapshot_state(self) -> ReactiveDashboardState:
        """Collect the latest helper telemetry and render dashboard state."""

        with self._lock:
            payload = self._helper.overlay_payload()
            self._view_model.apply_payload(payload)
            sample = self._helper.last_performance_sample()
            if sample:
                self._view_model.ingest_performance_sample(sample)
            session = self._helper.last_session_metrics()
            if session:
                self._view_model.ingest_session_metrics(session)
            return self._view_model.render_state()

    def render_dashboard_page(self) -> str:
        """Return the HTML shell for the reactive dashboard."""

        palette = self._view_model.theme.palette_for(1.0, 0.35)
        return _DASHBOARD_TEMPLATE.format(
            title=f"{self._view_model.theme.name} Metrics Console",
            refresh_ms=int(self._refresh_seconds * 1000),
            background=palette["background"],
            accent_primary=palette["accent_primary"],
            accent_secondary=palette["accent_secondary"],
            accent_tertiary=palette["accent_tertiary"],
            text_primary=self._view_model.theme.text_primary,
            text_muted=self._view_model.theme.text_muted,
        )

    def state_payload(self) -> Dict[str, object]:
        """Return the serialized dashboard state for HTTP responses."""

        state = self.snapshot_state()
        return {
            "timestamp": state.timestamp.isoformat() + "Z",
            "metrics": [
                {
                    "label": pulse.label,
                    "value": pulse.value,
                    "unit": pulse.unit,
                    "status": pulse.status,
                    "trend": pulse.trend,
                    "emphasis": pulse.emphasis,
                }
                for pulse in state.metrics
            ],
            "theme": state.theme_palette,
            "commentary": state.commentary,
            "practice": state.practice_prompt,
            "hero": state.hero_banner,
        }

    def _start_server(self) -> None:
        if self._httpd is not None:
            raise RuntimeError("dashboard already running")
        self._stop_event.clear()
        self._ready_event.clear()
        try:
            httpd = _DashboardHTTPServer((self._host, self._port), _DashboardRequestHandler, self)
        except OSError:
            self._stop_event.set()
            self._ready_event.set()
            raise
        self._httpd = httpd
        bound_host, bound_port = httpd.server_address
        display_host = self._host
        if display_host in {"0.0.0.0", ""}:
            display_host = "127.0.0.1"
        elif bound_host not in {"0.0.0.0", ""}:
            display_host = bound_host
        self._base_url = f"http://{display_host}:{bound_port}"
        self._serve_thread = threading.Thread(
            target=self._serve_forever,
            name="ReactiveDashboardServer",
            daemon=True,
        )
        self._serve_thread.start()
        self._ready_event.wait(timeout=1.0)
        print(f"Reactive web dashboard available at {self._base_url}", flush=True)

    def _serve_forever(self) -> None:
        if self._httpd is None:
            return
        self._ready_event.set()
        self._httpd.serve_forever(poll_interval=0.25)


class _DashboardHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server that exposes the dashboard instance."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, dashboard: ReactiveDashboard):
        super().__init__(server_address, handler_class)
        self.dashboard = dashboard


class _DashboardRequestHandler(BaseHTTPRequestHandler):
    """Serve the dashboard shell and reactive state payloads."""

    server: _DashboardHTTPServer

    def do_GET(self) -> None:  # noqa: N802 - required signature
        parsed = urlparse(self.path)
        route = parsed.path
        if route in {"", "/", "/index.html"}:
            self._serve_html()
        elif route == "/state":
            self._serve_state()
        elif route == "/health":
            self._serve_json({"status": "ok"})
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_HEAD(self) -> None:  # noqa: N802 - required signature
        parsed = urlparse(self.path)
        route = parsed.path
        if route in {"", "/", "/index.html"}:
            self._serve_html(head_only=True)
        elif route == "/state":
            self._serve_state(head_only=True)
        elif route == "/health":
            self._serve_json({"status": "ok"}, head_only=True)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - method name from base class
        return

    def _serve_html(self, head_only: bool = False) -> None:
        dashboard = self.server.dashboard
        html = dashboard.render_dashboard_page().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        if not head_only:
            self.wfile.write(html)

    def _serve_state(self, head_only: bool = False) -> None:
        dashboard = self.server.dashboard
        payload = json.dumps(dashboard.state_payload()).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _serve_json(self, payload: Dict[str, object], head_only: bool = False) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: {background};
        --accent-primary: {accent_primary};
        --accent-secondary: {accent_secondary};
        --accent-tertiary: {accent_tertiary};
        --text-primary: {text_primary};
        --text-muted: {text_muted};
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        background: var(--bg);
        color: var(--text-primary);
        display: flex;
        flex-direction: column;
        padding: 32px 36px 48px;
        gap: 20px;
      }}
      header {{
        display: flex;
        flex-direction: column;
        gap: 12px;
      }}
      .hero {{
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--accent-primary);
      }}
      .hero-sub {{
        font-size: 0.95rem;
        color: var(--text-muted);
        max-width: 720px;
        line-height: 1.6;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }}
      .metric {{
        border-radius: 16px;
        padding: 16px 20px;
        background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(0,0,0,0.35));
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 12px 24px rgba(0,0,0,0.35);
        transition: transform 140ms ease, box-shadow 140ms ease;
      }}
      .metric:hover {{
        transform: translateY(-4px);
        box-shadow: 0 18px 32px rgba(0,0,0,0.45);
      }}
      .metric h3 {{
        margin: 0;
        font-size: 0.95rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.78);
      }}
      .metric .value {{
        font-size: 2.4rem;
        font-weight: 700;
        margin: 12px 0 8px;
        color: var(--text-primary);
      }}
      .metric .status {{
        font-size: 0.9rem;
        color: var(--text-muted);
      }}
      .metric[data-emphasis="primary"] {{
        background: linear-gradient(150deg, rgba(72,229,194,0.65), rgba(33,61,83,0.85));
        color: #010203;
      }}
      .metric[data-emphasis="secondary"] {{
        border-color: rgba(86,204,242,0.55);
      }}
      .metric[data-emphasis="tertiary"] {{
        border-color: rgba(245,166,35,0.55);
      }}
      .commentary {{
        font-size: 1.05rem;
        line-height: 1.7;
        max-width: 820px;
        color: var(--text-primary);
      }}
      .practice {{
        font-size: 0.95rem;
        color: var(--text-muted);
        max-width: 720px;
      }}
      footer {{
        margin-top: auto;
        font-size: 0.8rem;
        color: rgba(255,255,255,0.4);
      }}
    </style>
  </head>
  <body>
    <header>
      <div class="hero" id="hero">{title}</div>
      <div class="hero-sub" id="timestamp">Initializing flux telemetry&hellip;</div>
    </header>
    <section class="grid" id="metrics"></section>
    <section class="commentary" id="commentary">Awaiting telemetry pulse.</section>
    <section class="practice" id="practice">Prime focus routines will appear once sessions stream in.</section>
    <footer>Refresh cadence: {refresh_ms}ms · Powered by the Luminal Flux pipeline.</footer>
    <script>
      const REFRESH_MS = {refresh_ms};
      const metricsContainer = document.getElementById('metrics');
      const commentaryEl = document.getElementById('commentary');
      const practiceEl = document.getElementById('practice');
      const heroEl = document.getElementById('hero');
      const timestampEl = document.getElementById('timestamp');

      function applyPalette(theme) {{
        const root = document.documentElement.style;
        root.setProperty('--bg', theme.background);
        root.setProperty('--accent-primary', theme.accent_primary);
        root.setProperty('--accent-secondary', theme.accent_secondary);
        root.setProperty('--accent-tertiary', theme.accent_tertiary);
      }}

      function renderMetrics(metrics) {{
        metricsContainer.innerHTML = '';
        metrics.forEach(metric => {{
          const card = document.createElement('article');
          card.className = 'metric';
          card.dataset.emphasis = metric.emphasis;
          const title = document.createElement('h3');
          title.textContent = metric.label;
          const value = document.createElement('div');
          value.className = 'value';
          value.textContent = metric.unit ? `${{metric.value}} ${{metric.unit}}` : metric.value;
          const status = document.createElement('div');
          status.className = 'status';
          status.textContent = `${{metric.trend}} · ${{metric.status}}`;
          card.append(title, value, status);
          metricsContainer.appendChild(card);
        }});
      }}

      async function refresh() {{
        try {{
          const response = await fetch('/state', {{ cache: 'no-store' }});
          if (!response.ok) return;
          const payload = await response.json();
          applyPalette(payload.theme);
          renderMetrics(payload.metrics);
          commentaryEl.textContent = payload.commentary;
          practiceEl.textContent = payload.practice;
          heroEl.textContent = payload.hero;
          const timestamp = new Date(payload.timestamp);
          timestampEl.textContent = `Last pulse ${{timestamp.toLocaleString()}}`;
        }} catch (err) {{
          console.error('Refresh failed', err);
        }}
      }}

      refresh();
      setInterval(refresh, REFRESH_MS);
    </script>
  </body>
</html>
"""
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
