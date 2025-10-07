import math

from fps_booster.cognitive import SessionMetrics
from fps_booster.features import FeatureFlags
from fps_booster.helper import ArenaHelper, OverlayPayload
from fps_booster.integrations import HardwareSnapshot, OverlayEventBroadcaster
from fps_booster.performance import PerformanceSample


def test_arena_helper_pipeline_generates_overlay():
    class StubCollector:
        def snapshot(self) -> HardwareSnapshot:
            return HardwareSnapshot(cpu_util=85.0, gpu_util=75.0, cpu_temp_c=60.0, gpu_temp_c=65.0)

    flags = FeatureFlags(hardware_telemetry=True, cv_model=True, asr_model=True, websocket_overlay=True)
    broadcaster = OverlayEventBroadcaster(buffer=4)
    helper = ArenaHelper(feature_flags=flags, broadcaster=broadcaster, telemetry_collector=StubCollector())

    frame = []
    for _ in range(8):
        row = []
        for col in range(8):
            value = 255 if col < 4 else 0
            row.append([value, value, value])
        frame.append(row)
    helper.process_frame(frame)

    samples = [0.6 * math.sin(2 * math.pi * 400 * (i / 48000)) for i in range(512)]
    helper.process_audio(samples)

    helper.process_performance(PerformanceSample(fps=70, frame_time_ms=14, cpu_util=20, gpu_util=25))

    helper.record_session(SessionMetrics(reaction_time=0.35, accuracy=0.6, stress_index=0.5))

    payload = helper.overlay_payload()
    assert isinstance(payload, OverlayPayload)
    assert payload.vision is not None
    assert payload.audio is not None
    assert payload.performance is not None
    assert payload.practice is not None
    assert payload.vision.detections
    assert payload.audio.keywords
    assert payload.performance.hardware_snapshot is not None
    assert "Sightlines flag" in payload.commentary
    assert "Thermals steady" in payload.commentary
    assert broadcaster.buffered_events()
