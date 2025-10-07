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
            description="Extracts motion cues and neural detections from captured frames.",
            inputs=["frame (H x W x 3)", "previous_frame", "feature_flags.cv_model"],
            outputs=["movement_score", "color_clusters", "annotations", "detections"],
        ),
        ModuleBlueprint(
            name="Audio Intelligence",
            description="Transforms waveform windows and surfaces keyword cues.",
            inputs=["samples", "sample_rate", "feature_flags.asr_model"],
            outputs=["frequency_bands", "event_confidence", "keywords"],
        ),
        ModuleBlueprint(
            name="Hardware Telemetry Bridge",
            description="Aggregates psutil/GPUtil metrics when enabled.",
            inputs=["feature_flags.hardware_telemetry"],
            outputs=["hardware_snapshot"],
        ),
        ModuleBlueprint(
            name="Adaptive Performance",
            description="Learns system response and merges hardware telemetry into advice.",
            inputs=["frame_time", "fps", "cpu_util", "gpu_util", "hardware_snapshot"],
            outputs=["scaling_factor", "quality_shift", "narrative"],
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
            inputs=[
                "vision_report",
                "audio_report",
                "performance_recommendation",
                "practice_recommendation",
            ],
            outputs=["overlay_payload"],
        ),
        ModuleBlueprint(
            name="WebSocket Gateway",
            description="Publishes overlay payloads to UI clients via broadcast.",
            inputs=["overlay_payload", "feature_flags.websocket_overlay"],
            outputs=["websocket_stream"],
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
