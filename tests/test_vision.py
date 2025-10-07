from fps_booster.vision import VisionAnalyzer


def test_vision_motion_detection_increases():
    analyzer = VisionAnalyzer(motion_threshold=0.1, smoothing=0.5)
    frame1 = [[[0, 0, 0] for _ in range(10)] for _ in range(10)]
    report1 = analyzer.analyze_frame(frame1)
    assert report1.movement_score == 0
    frame2 = [[[200, 200, 200] for _ in range(10)] for _ in range(10)]
    report2 = analyzer.analyze_frame(frame2)
    assert report2.movement_score > report1.movement_score
    assert any("High kinetic" in text or "Moderate" in text for text in report2.annotations)


def test_color_clusters_identified():
    analyzer = VisionAnalyzer()
    frame = []
    for _ in range(2):
        frame.append([[255, 0, 0] for _ in range(4)])
    for _ in range(2):
        frame.append([[0, 255, 0] for _ in range(4)])
    report = analyzer.analyze_frame(frame)
    assert report.color_clusters
    assert len(report.color_clusters) <= 3
    assert isinstance(report.color_clusters[0]["mean_color"], tuple)
