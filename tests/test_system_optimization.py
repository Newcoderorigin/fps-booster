from fps_booster.system_optimization import BackgroundTask, SystemOptimizer


def test_tasks_to_close_filters_non_critical_hogs() -> None:
    optimizer = SystemOptimizer(cpu_limit=5.0, memory_limit=200.0)
    tasks = [
        BackgroundTask(name="game", cpu_percent=30.0, memory_mb=1500.0, is_critical=True),
        BackgroundTask(name="updater", cpu_percent=12.0, memory_mb=120.0),
        BackgroundTask(name="browser", cpu_percent=3.0, memory_mb=500.0),
        BackgroundTask(name="chat", cpu_percent=0.5, memory_mb=50.0),
    ]

    hogs = optimizer.tasks_to_close(tasks)

    assert [task.name for task in hogs] == ["updater", "browser"]


def test_driver_update_required_detects_outdated_version() -> None:
    assert SystemOptimizer.is_driver_update_required("531.02", "531.12")
    assert not SystemOptimizer.is_driver_update_required("532.01", "531.12")


def test_power_profile_recommendation_prefers_high_performance() -> None:
    optimizer = SystemOptimizer()

    assert optimizer.recommend_power_profile("Balanced") == "High Performance"
    assert optimizer.recommend_power_profile("High Performance") == "High Performance"
