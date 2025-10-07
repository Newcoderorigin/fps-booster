"""Command-line entry point for the Arena helper demo runtime."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import threading
from dataclasses import asdict
from typing import Sequence, Tuple

from fps_booster import (
    ArenaHelper,
    FeatureFlags,
    OverlayEventBroadcaster,
    PerformanceSample,
    ReactiveDashboard,
    SessionMetrics,
)


def _demo_frame(step: int) -> Sequence[Sequence[Sequence[int]]]:
    tone = 255 if step % 2 == 0 else 40
    frame = []
    for _ in range(10):
        row = []
        for col in range(10):
            brightness = tone if col < 6 else max(0, tone - 30)
            row.append([brightness, brightness, brightness])
        frame.append(row)
    return frame


def _demo_audio(step: int, window: int) -> Sequence[float]:
    base_freq = 400 + (step % 3) * 75
    return [0.6 * math.sin(2 * math.pi * base_freq * (i / 48000)) for i in range(window)]


def _demo_performance(step: int) -> PerformanceSample:
    fps = 70 - (step % 4) * 5
    frame_time = 1000.0 / max(fps, 1)
    cpu = 40 + (step % 3) * 5
    gpu = 45 + (step % 2) * 10
    return PerformanceSample(fps=fps, frame_time_ms=frame_time, cpu_util=cpu, gpu_util=gpu)


def _demo_session(step: int) -> SessionMetrics:
    reaction = 0.28 + 0.02 * (step % 3)
    accuracy = 0.55 + 0.05 * ((step + 1) % 3)
    stress = 0.4 + 0.1 * (random.random())
    return SessionMetrics(reaction_time=reaction, accuracy=accuracy, stress_index=stress)


def _build_helper(args: argparse.Namespace) -> Tuple[ArenaHelper, OverlayEventBroadcaster | None]:
    """Construct an ``ArenaHelper`` configured by command-line flags."""

    flags = FeatureFlags(
        hardware_telemetry=args.enable_hw,
        cv_model=args.enable_cv,
        asr_model=args.enable_asr,
        websocket_overlay=args.enable_websocket,
    )
    broadcaster = (
        OverlayEventBroadcaster(buffer=args.websocket_buffer)
        if flags.websocket_overlay
        else None
    )
    helper = ArenaHelper(feature_flags=flags, broadcaster=broadcaster)
    return helper, broadcaster


async def _run(
    helper: ArenaHelper,
    broadcaster: OverlayEventBroadcaster | None,
    args: argparse.Namespace,
    stop_event: threading.Event | None = None,
) -> None:
    """Drive the demo helper and optionally publish overlay payloads."""

    if broadcaster:
        await broadcaster.start()

    step = 0
    try:
        while True:
            if stop_event and stop_event.is_set():
                break
            if args.steps > 0 and step >= args.steps:
                break

            frame = _demo_frame(step)
            helper.process_frame(frame)

            audio = _demo_audio(step, 512)
            helper.process_audio(audio)

            perf_sample = _demo_performance(step)
            helper.process_performance(perf_sample)

            helper.record_session(_demo_session(step))
            payload = helper.overlay_payload()
            if args.payload_log_mode != "quiet":
                indent = 2 if args.payload_log_mode == "pretty" else None
                print(json.dumps(asdict(payload), indent=indent))
            if broadcaster:
                await broadcaster.async_publish(payload)

            step += 1
            if stop_event and stop_event.is_set():
                break
            if args.interval > 0:
                await asyncio.sleep(args.interval)
    finally:
        if broadcaster:
            await broadcaster.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Arena helper demo runner")
    parser.add_argument("--enable-hw", action="store_true", help="Enable hardware telemetry integration")
    parser.add_argument("--enable-cv", action="store_true", help="Enable YOLO-style vision detector")
    parser.add_argument("--enable-asr", action="store_true", help="Enable keyword spotting on audio")
    parser.add_argument(
        "--enable-websocket",
        action="store_true",
        help="Broadcast overlay payloads via websocket",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Number of demo iterations to run (0 streams indefinitely)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds to wait between iterations",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without launching the reactive dashboard GUI",
    )
    parser.add_argument(
        "--gui-refresh",
        type=float,
        default=0.5,
        help="Seconds between GUI refresh ticks",
    )
    parser.add_argument(
        "--payload-log-mode",
        choices=("quiet", "compact", "pretty"),
        default="quiet",
        help="Control overlay payload logging verbosity",
    )
    parser.add_argument(
        "--websocket-buffer",
        type=int,
        default=128,
        help="Number of overlay payloads retained for late websocket clients",
    )
    args = parser.parse_args()

    helper, broadcaster = _build_helper(args)

    if args.headless:
        asyncio.run(_run(helper, broadcaster, args))
        return

    dashboard: ReactiveDashboard | None = None
    fallback_message: str | None = None

    try:
        dashboard = ReactiveDashboard(helper, refresh_seconds=args.gui_refresh)
    except ImportError:
        fallback_message = (
            "tkinter is not available in this Python environment. "
            "Install Tk support or pass --headless to run without the GUI."
        )
    except Exception as exc:  # pragma: no cover - GUI backend specific
        if exc.__class__.__name__ == "TclError":
            fallback_message = "tkinter backend error; running in headless mode."
        else:
            raise

    if dashboard is None:
        if fallback_message:
            print(fallback_message)
        asyncio.run(_run(helper, broadcaster, args))
        return

    stop_event = threading.Event()

    def worker() -> None:
        asyncio.run(_run(helper, broadcaster, args, stop_event=stop_event))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    try:
        dashboard.start()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        thread.join()


if __name__ == "__main__":
    main()
