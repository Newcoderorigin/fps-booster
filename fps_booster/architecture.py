"""Architecture blueprint for the Arena helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ModuleBlueprint:
    """Describes a helper subsystem and its interfaces."""

    name: str
    description: str
    inputs: List[str]
    outputs: List[str]

    def summary(self) -> str:
        """Return a concise description string."""

        return f"{self.name}: {self.description}"


def build_default_architecture() -> List[ModuleBlueprint]:
    """Return the canonical Arena helper architecture."""

    return [
        ModuleBlueprint(
            name="Vision Analyzer",
            description="Extracts motion cues and context from captured frames.",
            inputs=["frame (H x W x 3)", "previous_frame"],
            outputs=["movement_score", "color_clusters", "annotations"],
        ),
        ModuleBlueprint(
            name="Audio Intelligence",
            description="Transforms waveform windows into spatial intensity estimates.",
            inputs=["samples", "sample_rate"],
            outputs=["frequency_bands", "event_confidence"],
        ),
        ModuleBlueprint(
            name="Adaptive Performance",
            description="Learns system response and recommends setting adjustments.",
            inputs=["frame_time", "fps", "cpu_util", "gpu_util"],
            outputs=["scaling_factor", "quality_shift"],
        ),
        ModuleBlueprint(
            name="Cognitive Coach",
            description="Models player response to deliver practice routines.",
            inputs=["reaction_time", "accuracy", "stress_index"],
            outputs=["practice_focus", "coaching_prompt"],
        ),
        ModuleBlueprint(
            name="Narrative Overlay",
            description="Fuses subsystem insights into a stylized commentary stream.",
            inputs=["vision_report", "audio_report", "performance_recommendation", "practice_recommendation"],
            outputs=["overlay_payload"],
        ),
    ]


def describe_architecture(blueprints: Iterable[ModuleBlueprint]) -> str:
    """Return a human-readable overview of the architecture."""

    lines = ["Arena Helper Architecture:"]
    for idx, blueprint in enumerate(blueprints, start=1):
        lines.append(f"{idx}. {blueprint.summary()}")
        lines.append(f"   Inputs: {', '.join(blueprint.inputs)}")
        lines.append(f"   Outputs: {', '.join(blueprint.outputs)}")
    return "\n".join(lines)
