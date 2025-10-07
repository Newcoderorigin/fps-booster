"""Computer-vision utilities for the Arena helper (numpy-free)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .integrations import YOLOAdapter

Pixel = Sequence[int]
Frame = Sequence[Sequence[Pixel]]


@dataclass(frozen=True)
class VisionReport:
    """Summarizes visual cues from an analyzed frame."""

    movement_score: float
    color_clusters: Sequence[dict]
    annotations: Sequence[str]
    detections: Sequence[str]


class VisionAnalyzer:
    """Derives actionable metadata from frame captures."""

    def __init__(
        self,
        motion_threshold: float = 0.12,
        smoothing: float = 0.8,
        detector: YOLOAdapter | None = None,
    ) -> None:
        if not 0.0 <= motion_threshold <= 1.0:
            raise ValueError("motion_threshold must be within [0, 1]")
        if not 0.0 < smoothing <= 1.0:
            raise ValueError("smoothing must be within (0, 1]")
        self._motion_threshold = motion_threshold
        self._smoothing = smoothing
        self._previous_flat: List[Tuple[int, int, int]] | None = None
        self._smoothed_motion = 0.0
        self._detector = detector

    def analyze_frame(self, frame: Frame) -> VisionReport:
        """Analyze the frame and return movement and color insights."""

        flat = self._flatten(frame)
        movement = self._compute_motion(flat)
        clusters = self._cluster_colors(flat)
        annotations = self._build_annotations(movement, clusters)
        detections = self._detector.detect(frame) if self._detector else []
        if detections:
            annotations = list(annotations) + [f"Detections: {', '.join(detections)}."]
        return VisionReport(
            movement_score=movement,
            color_clusters=clusters,
            annotations=annotations,
            detections=tuple(detections),
        )

    def _flatten(self, frame: Frame) -> List[Tuple[int, int, int]]:
        flat: List[Tuple[int, int, int]] = []
        for row in frame:
            for pixel in row:
                if len(pixel) != 3:
                    raise ValueError("Pixels must contain three channels")
                r, g, b = (int(channel) for channel in pixel)
                if not all(0 <= value <= 255 for value in (r, g, b)):
                    raise ValueError("Pixel values must be within [0, 255]")
                flat.append((r, g, b))
        if not flat:
            raise ValueError("Frame must contain at least one pixel")
        return flat

    def _compute_motion(self, flat: List[Tuple[int, int, int]]) -> float:
        if self._previous_flat is None or len(self._previous_flat) != len(flat):
            movement = 0.0
        else:
            total_diff = 0.0
            for prev, curr in zip(self._previous_flat, flat):
                diff = sum(abs(a - b) for a, b in zip(prev, curr)) / 3.0
                total_diff += diff
            movement = (total_diff / len(flat)) / 255.0
        self._previous_flat = list(flat)
        self._smoothed_motion = self._smoothing * self._smoothed_motion + (1 - self._smoothing) * movement
        return round(self._smoothed_motion, 4)

    def _cluster_colors(self, flat: List[Tuple[int, int, int]]) -> List[dict]:
        buckets: List[List[Tuple[int, int, int]]] = [[] for _ in range(5)]
        for pixel in flat:
            luminance = sum(pixel) / 3.0
            index = min(int(luminance / 51), 4)
            buckets[index].append(pixel)
        clusters: List[dict] = []
        total = float(len(flat))
        for bucket in buckets:
            if not bucket:
                continue
            coverage = len(bucket) / total
            if coverage < 0.05:
                continue
            avg = tuple(round(sum(channel[i] for channel in bucket) / len(bucket) / 255.0, 3) for i in range(3))
            clusters.append({"mean_color": avg, "coverage": round(coverage, 3)})
        clusters.sort(key=lambda c: c["coverage"], reverse=True)
        return clusters[:3]

    def _build_annotations(self, movement: float, clusters: Sequence[dict]) -> List[str]:
        annotations: List[str] = []
        if movement >= self._motion_threshold:
            annotations.append("High kinetic activity detected. Stabilize aim and anticipate contact.")
        elif movement >= self._motion_threshold * 0.5:
            annotations.append("Moderate motion. Prepare for engagements.")
        else:
            annotations.append("Scene calm. Scout lanes and reposition deliberately.")

        if clusters:
            dominant = clusters[0]["mean_color"]
            annotations.append(f"Dominant palette intensity {dominant} — leverage contrast for visibility.")
        else:
            annotations.append("Palette uniform. Use audio cues to compensate for visual ambiguity.")
        return annotations

    def reset(self) -> None:
        """Reset the motion integrator."""

        self._previous_flat = None
        self._smoothed_motion = 0.0
