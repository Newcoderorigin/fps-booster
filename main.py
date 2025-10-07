"""Command-line entry point for the Arena helper demo runtime."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
from dataclasses import asdict
from typing import Sequence

from fps_booster import (
    ArenaHelper,
    FeatureFlags,
    OverlayEventBroadcaster,
    PerformanceSample,
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


async def _run(args: argparse.Namespace) -> None:
    flags = FeatureFlags(
        hardware_telemetry=args.enable_hw,
        cv_model=args.enable_cv,
        asr_model=args.enable_asr,
        websocket_overlay=args.enable_websocket,
    )
    broadcaster = OverlayEventBroadcaster() if flags.websocket_overlay else None
    helper = ArenaHelper(feature_flags=flags, broadcaster=broadcaster)
    if broadcaster:
        await broadcaster.start()

    try:
        for step in range(args.steps):
            frame = _demo_frame(step)
            helper.process_frame(frame)

            audio = _demo_audio(step, 512)
            helper.process_audio(audio)

            perf_sample = _demo_performance(step)
            helper.process_performance(perf_sample)

            helper.record_session(_demo_session(step))
            payload = helper.overlay_payload()
            print(json.dumps(asdict(payload), indent=2))
            if broadcaster:
                await broadcaster.async_publish(payload)
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
    parser.add_argument("--steps", type=int, default=5, help="Number of demo iterations to run")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds to wait between iterations",
    )
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
