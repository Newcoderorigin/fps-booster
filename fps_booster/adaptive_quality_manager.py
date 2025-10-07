"""Adaptive graphics configuration tuning using lightweight ML."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Deque, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class TelemetrySample:
    """Single telemetry sample captured from the game and hardware sensors."""

    fps: float
    gpu_temp: float
    cpu_usage: float
    frame_time_ms: float

    @property
    def performance_margin(self) -> float:
        """Positive values mean spare frame time headroom; negative means stutter."""

        target_frame_time = 1000.0 / 60.0
        return target_frame_time - self.frame_time_ms


@dataclass(frozen=True)
class GraphicsConfig:
    """Represents safe-to-edit graphics settings."""

    resolution_scale: float
    ambient_occlusion: str
    shadow_distance: str

    def clamp(self) -> "GraphicsConfig":
        """Return a config constrained to safe bounds."""

        clamped_scale = min(max(self.resolution_scale, 0.5), 1.0)
        allowed_ao = ("off", "low", "medium", "high")
        allowed_shadow = ("short", "medium", "long")
        ao = self.ambient_occlusion if self.ambient_occlusion in allowed_ao else "medium"
        shadow = self.shadow_distance if self.shadow_distance in allowed_shadow else "medium"
        return GraphicsConfig(clamped_scale, ao, shadow)


class RollingWindow:
    """Fixed-size queue for telemetry samples."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._buffer: Deque[Tuple[TelemetrySample, GraphicsConfig]] = deque(maxlen=capacity)

    def append(self, sample: TelemetrySample, config: GraphicsConfig) -> None:
        self._buffer.append((sample, config.clamp()))

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._buffer)

    def items(self) -> Iterable[Tuple[TelemetrySample, GraphicsConfig]]:
        return iter(self._buffer)


class RidgeRegressor:
    """Simple ridge regression fitted with normal equation."""

    def __init__(self, alpha: float = 1e-3) -> None:
        self.alpha = alpha
        self._coef: List[float] | None = None

    def fit(self, features: Sequence[Sequence[float]], targets: Sequence[float]) -> None:
        rows = [list(map(float, row)) for row in features]
        if not rows:
            raise ValueError("features must not be empty")
        if any(len(row) != len(rows[0]) for row in rows):
            raise ValueError("feature rows must be uniform length")
        augmented = [([1.0] + row) for row in rows]
        XtX = _matmul_transpose(augmented)
        for i in range(1, len(XtX)):
            XtX[i][i] += self.alpha
        Xty = _matvec(augmented, list(map(float, targets)))
        self._coef = _solve_linear_system(XtX, Xty)

    def predict(self, features: Sequence[float]) -> float:
        if self._coef is None:
            raise RuntimeError("model must be fitted before prediction")
        vector = [1.0] + [float(value) for value in features]
        if len(vector) != len(self._coef):
            raise ValueError("feature vector has unexpected length")
        return sum(a * b for a, b in zip(vector, self._coef))


class AdaptiveQualityManager:
    """Learns how to tune graphics settings for smooth frame delivery."""

    def __init__(
        self,
        window: RollingWindow | None = None,
        regressor: RidgeRegressor | None = None,
        target_frame_time_ms: float = 16.0,
        margin_tolerance_ms: float = 1.0,
    ) -> None:
        self.window = window or RollingWindow(capacity=120)
        self.regressor = regressor or RidgeRegressor(alpha=1e-2)
        self.target_frame_time_ms = target_frame_time_ms
        self.margin_tolerance_ms = margin_tolerance_ms

    def update(self, sample: TelemetrySample, config: GraphicsConfig) -> GraphicsConfig:
        """Store telemetry and return the next configuration recommendation."""

        self.window.append(sample, config)
        if len(self.window) < 5:
            return config.clamp()
        self._train_model()
        return self._recommend(sample, config)

    def _train_model(self) -> None:
        samples: List[List[float]] = []
        targets: List[float] = []
        for sample, _ in self.window.items():
            samples.append([sample.fps, sample.gpu_temp, sample.cpu_usage, sample.frame_time_ms])
            targets.append(self.target_frame_time_ms - sample.frame_time_ms)
        self.regressor.fit(samples, targets)

    def _recommend(self, sample: TelemetrySample, config: GraphicsConfig) -> GraphicsConfig:
        prediction = self.regressor.predict([sample.fps, sample.gpu_temp, sample.cpu_usage, sample.frame_time_ms])
        observed_margin = self.target_frame_time_ms - sample.frame_time_ms
        if observed_margin < -self.margin_tolerance_ms or (
            abs(observed_margin) <= self.margin_tolerance_ms and prediction < -self.margin_tolerance_ms
        ):
            return self._scale_down(config)
        if observed_margin > self.margin_tolerance_ms or (
            abs(observed_margin) <= self.margin_tolerance_ms and prediction > self.margin_tolerance_ms
        ):
            return self._scale_up(config)
        return config.clamp()

    def _scale_down(self, config: GraphicsConfig) -> GraphicsConfig:
        ao_levels = ("off", "low", "medium", "high")
        shadow_levels = ("short", "medium", "long")
        current_ao_index = max(ao_levels.index(config.ambient_occlusion), 0)
        current_shadow_index = max(shadow_levels.index(config.shadow_distance), 0)

        if config.resolution_scale > 0.8:
            return replace(config, resolution_scale=round(config.resolution_scale - 0.05, 2)).clamp()
        if current_ao_index > 0:
            return replace(config, ambient_occlusion=ao_levels[current_ao_index - 1]).clamp()
        if current_shadow_index > 0:
            return replace(config, shadow_distance=shadow_levels[current_shadow_index - 1]).clamp()
        return config.clamp()

    def _scale_up(self, config: GraphicsConfig) -> GraphicsConfig:
        ao_levels = ("off", "low", "medium", "high")
        shadow_levels = ("short", "medium", "long")
        current_ao_index = max(ao_levels.index(config.ambient_occlusion), 0)
        current_shadow_index = max(shadow_levels.index(config.shadow_distance), 0)

        if config.resolution_scale < 1.0:
            return replace(config, resolution_scale=round(config.resolution_scale + 0.05, 2)).clamp()
        if current_ao_index < len(ao_levels) - 1:
            return replace(config, ambient_occlusion=ao_levels[current_ao_index + 1]).clamp()
        if current_shadow_index < len(shadow_levels) - 1:
            return replace(config, shadow_distance=shadow_levels[current_shadow_index + 1]).clamp()
        return config.clamp()


def _matmul_transpose(matrix: Sequence[Sequence[float]]) -> List[List[float]]:
    rows = len(matrix)
    cols = len(matrix[0])
    result = [[0.0 for _ in range(cols)] for _ in range(cols)]
    for i in range(rows):
        for j in range(cols):
            value = matrix[i][j]
            for k in range(cols):
                result[j][k] += value * matrix[i][k]
    return result


def _matvec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    return [sum(row[j] * vector[j] for j in range(len(row))) for row in matrix]


def _solve_linear_system(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    size = len(matrix)
    augmented = [list(matrix[row]) + [vector[row]] for row in range(size)]
    for i in range(size):
        pivot_row = max(range(i, size), key=lambda r: abs(augmented[r][i]))
        if abs(augmented[pivot_row][i]) < 1e-12:
            raise ValueError("matrix is singular")
        if pivot_row != i:
            augmented[i], augmented[pivot_row] = augmented[pivot_row], augmented[i]
        pivot = augmented[i][i]
        for j in range(i, size + 1):
            augmented[i][j] /= pivot
        for r in range(size):
            if r == i:
                continue
            factor = augmented[r][i]
            if abs(factor) < 1e-12:
                continue
            for c in range(i, size + 1):
                augmented[r][c] -= factor * augmented[i][c]
    return [augmented[row][size] for row in range(size)]


__all__ = [
    "AdaptiveQualityManager",
    "GraphicsConfig",
    "RidgeRegressor",
    "RollingWindow",
    "TelemetrySample",
]
