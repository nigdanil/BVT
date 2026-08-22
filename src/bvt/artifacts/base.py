from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactConfig:
    """Resolved configuration for one artifact provider."""

    artifact_id: str
    enabled: bool
    probability: float
    intensity: float


@dataclass(frozen=True)
class ArtifactContext:
    """Deterministic per-frame artifact execution context."""

    config: ArtifactConfig
    frame_seed: int
    artifact_seed: int
    decision_roll: float


class ArtifactProvider(ABC):
    """Base contract implemented by every BVT artifact."""

    artifact_id = ""
    category = ""
    description = ""
    stage = "pre_render"

    def validate_config(
        self,
        config,
    ):
        """Validate common artifact configuration."""

        if (
            config.artifact_id
            != self.artifact_id
        ):
            raise ValueError(
                "Artifact configuration ID does not "
                "match provider ID"
            )

        if not (
            0.0
            <= config.probability
            <= 1.0
        ):
            raise ValueError(
                "Artifact probability must be "
                "between 0 and 1"
            )

        if not (
            0.0
            <= config.intensity
            <= 1.0
        ):
            raise ValueError(
                "Artifact intensity must be "
                "between 0 and 1"
            )

        if self.stage not in {
            "pre_render",
            "post_render",
        }:
            raise ValueError(
                "Artifact stage must be "
                "'pre_render' or 'post_render'"
            )

    @abstractmethod
    def capture(
        self,
        scene,
    ):
        """Capture state required to reset the artifact."""

        raise NotImplementedError

    @abstractmethod
    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """Apply a pre-render artifact."""

        raise NotImplementedError

    def apply_post_render(
        self,
        scene,
        image_path,
        context,
        baseline,
    ):
        """Apply a post-render artifact."""

        raise RuntimeError(
            (
                f"Artifact '{self.artifact_id}' "
                "does not implement post-render execution"
            )
        )

    @abstractmethod
    def reset(
        self,
        scene,
        baseline,
    ):
        """Restore state captured before generation."""

        raise NotImplementedError

    def preview(
        self,
        scene,
        context,
        baseline,
    ):
        """Apply a pre-render provider for preview."""

        return self.apply(
            scene,
            context,
            baseline,
        )

    def compatibility_rules(self):
        """Return provider compatibility constraints."""

        return ()

    def manifest_export(
        self,
        context,
        applied,
        metadata=None,
    ):
        """Build canonical per-frame manifest metadata."""

        metadata = metadata or {}

        return {
            "artifact": self.artifact_id,
            "category": self.category,
            "description": self.description,
            "stage": self.stage,
            "enabled": (
                context.config.enabled
            ),
            "probability": (
                context.config.probability
            ),
            "intensity": (
                context.config.intensity
            ),
            "seed": (
                context.artifact_seed
            ),
            "decision_roll": (
                context.decision_roll
            ),
            "applied": bool(
                applied
            ),
            "affected_objects": (
                metadata.get(
                    "affected_objects",
                    [],
                )
            ),
            "affected_camera": (
                metadata.get(
                    "affected_camera"
                )
            ),
            "affected_materials": (
                metadata.get(
                    "affected_materials",
                    [],
                )
            ),
            "parameters": (
                metadata.get(
                    "parameters",
                    {},
                )
            ),
            "compatibility_rules": list(
                self.compatibility_rules()
            ),
        }
