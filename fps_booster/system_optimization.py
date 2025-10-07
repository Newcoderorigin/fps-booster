"""System optimization utilities for safe FPS boosting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class BackgroundTask:
    """Represents a running background task with resource usage metrics."""

    name: str
    cpu_percent: float
    memory_mb: float
    is_critical: bool = False

    def exceeds_limits(self, cpu_limit: float, memory_limit: float) -> bool:
        """Return True when the task uses more CPU or memory than allowed."""

        return self.cpu_percent > cpu_limit or self.memory_mb > memory_limit


class SystemOptimizer:
    """Analyzes system state and recommends safe optimizations."""

    def __init__(self, cpu_limit: float = 10.0, memory_limit: float = 300.0) -> None:
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit

    def tasks_to_close(self, tasks: Iterable[BackgroundTask]) -> List[BackgroundTask]:
        """Return non-critical tasks exceeding configured resource limits."""

        return [
            task
            for task in tasks
            if not task.is_critical and task.exceeds_limits(self.cpu_limit, self.memory_limit)
        ]

    @staticmethod
    def is_driver_update_required(current_version: str, latest_version: str) -> bool:
        """Return True if the GPU driver should be updated."""

        return _compare_versions(current_version, latest_version) < 0

    @staticmethod
    def recommend_power_profile(current_profile: str) -> str:
        """Recommend the correct power profile for gaming sessions."""

        normalized = current_profile.strip().lower()
        if normalized in {"high performance", "ultimate performance"}:
            return current_profile
        return "High Performance"

    def summarize_actions(
        self,
        tasks: Sequence[BackgroundTask],
        current_driver: str,
        latest_driver: str,
        current_power_profile: str,
    ) -> dict:
        """Return a summary of safe optimization steps to execute."""

        return {
            "terminate": self.tasks_to_close(tasks),
            "update_driver": self.is_driver_update_required(current_driver, latest_driver),
            "power_profile": self.recommend_power_profile(current_power_profile),
        }


def _compare_versions(current: str, latest: str) -> int:
    """Compare two dotted version strings.

    Returns:
        -1 if ``current`` < ``latest``, 0 if equal, and 1 otherwise.
    """

    current_tokens = _parse_version(current)
    latest_tokens = _parse_version(latest)
    for current_part, latest_part in zip(_pad_version(current_tokens, latest_tokens), _pad_version(latest_tokens, current_tokens)):
        if current_part < latest_part:
            return -1
        if current_part > latest_part:
            return 1
    return 0


def _parse_version(version: str) -> List[int]:
    if not version:
        return [0]
    parts: List[int] = []
    for token in version.replace("-", ".").split("."):
        if not token:
            continue
        try:
            parts.append(int(token))
        except ValueError:
            numeric = "".join(ch for ch in token if ch.isdigit())
            parts.append(int(numeric) if numeric else 0)
    return parts or [0]


def _pad_version(source: Sequence[int], target: Sequence[int]) -> List[int]:
    padding = max(len(target) - len(source), 0)
    if padding:
        return list(source) + [0] * padding
    return list(source)


__all__ = ["BackgroundTask", "SystemOptimizer"]
