from fps_booster.performance import AdaptivePerformanceManager, PerformanceRecommendation, PerformanceSample


def test_performance_manager_reacts_to_low_fps():
    manager = AdaptivePerformanceManager(target_fps=90, history=10)
    sample = PerformanceSample(fps=60, frame_time_ms=20, cpu_util=95, gpu_util=92)
    recommendation = manager.update(sample)
    assert isinstance(recommendation, PerformanceRecommendation)
    assert recommendation.scaling_factor <= 1.0
    assert recommendation.quality_shift < 0
    assert 0 <= recommendation.confidence <= 1


def test_performance_manager_recovers_with_high_fps():
    manager = AdaptivePerformanceManager(target_fps=60, history=5)
    for _ in range(4):
        manager.update(PerformanceSample(fps=75, frame_time_ms=12, cpu_util=40, gpu_util=55))
    recommendation = manager.update(PerformanceSample(fps=85, frame_time_ms=10, cpu_util=35, gpu_util=45))
    assert recommendation.scaling_factor >= 0.9
    assert recommendation.quality_shift >= 0
    assert recommendation.confidence > 0.5
