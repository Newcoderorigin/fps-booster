"""Tests for the command-line demo runtime."""

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace

from main import _build_helper, _run


def _demo_args(**overrides):
    base = dict(
        enable_hw=False,
        enable_cv=False,
        enable_asr=False,
        enable_websocket=False,
        websocket_buffer=128,
        steps=1,
        interval=0.0,
        payload_log_mode="quiet",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_run_generates_samples():
    args = _demo_args(steps=2)
    helper, broadcaster = _build_helper(args)
    asyncio.run(_run(helper, broadcaster, args))
    assert helper.last_performance_sample() is not None
    assert helper.last_session_metrics() is not None


def test_run_honors_stop_event():
    args = _demo_args(steps=0)
    helper, broadcaster = _build_helper(args)
    stop_event = threading.Event()
    stop_event.set()
    asyncio.run(_run(helper, broadcaster, args, stop_event=stop_event))
    assert helper.last_performance_sample() is None


def test_run_logs_payloads_when_requested(capsys):
    args = _demo_args(steps=1, payload_log_mode="compact")
    helper, broadcaster = _build_helper(args)
    asyncio.run(_run(helper, broadcaster, args))
    captured = capsys.readouterr()
    assert "\n" not in captured.out.strip()  # compact JSON


def test_run_suppresses_payload_logs_by_default(capsys):
    args = _demo_args(steps=1)
    helper, broadcaster = _build_helper(args)
    asyncio.run(_run(helper, broadcaster, args))
    captured = capsys.readouterr()
    assert captured.out.strip() == ""
