import math

from fps_booster.audio import AudioAnalyzer
from fps_booster.cognitive import SessionMetrics
from fps_booster.helper import ArenaHelper, OverlayPayload
from fps_booster.performance import PerformanceSample


def test_arena_helper_pipeline_generates_overlay():
    audio = AudioAnalyzer(sample_rate=8000, window_size=512, event_band=(200, 1000))
    helper = ArenaHelper(audio=audio)

    frame = []
    for _ in range(8):
        row = []
        for col in range(8):
            value = 255 if col < 4 else 0
            row.append([value, value, value])
        frame.append(row)
    helper.process_frame(frame)

    samples = [math.sin(2 * math.pi * 400 * (i / 8000)) for i in range(512)]
    helper.process_audio(samples)

    helper.process_performance(PerformanceSample(fps=70, frame_time_ms=14, cpu_util=60, gpu_util=65))

    helper.record_session(SessionMetrics(reaction_time=0.35, accuracy=0.6, stress_index=0.5))

    payload = helper.overlay_payload()
    assert isinstance(payload, OverlayPayload)
    assert payload.vision is not None
    assert payload.audio is not None
    assert payload.performance is not None
    assert payload.practice is not None
    assert "Awaiting" not in payload.commentary
