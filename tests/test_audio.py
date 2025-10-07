import math

from fps_booster.audio import AudioAnalyzer


def test_audio_analyzer_identifies_dominant_frequency():
    sr = 8000
    analyzer = AudioAnalyzer(sample_rate=sr, window_size=1024, event_band=(300, 1200))
    samples = [0.5 * math.sin(2 * math.pi * 500 * (i / sr)) for i in range(1024)]
    report = analyzer.analyze(samples)
    assert 450 <= report.dominant_frequency <= 550
    assert report.event_confidence > 0
    assert set(report.band_energy.keys()) == {"low", "mid", "high"}
