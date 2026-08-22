import random

from ..core.seeding import derive_subseed
from .base import ArtifactConfig
from .base import ArtifactContext
from .providers.exposure import (
    OverExposureArtifactProvider,
)


ARTIFACT_ENGINE_VERSION = (
    "artifact-engine-v1"
)


_PROVIDERS = (
    OverExposureArtifactProvider(),
)


_PROVIDER_BY_ID = {
    provider.artifact_id: provider
    for provider in _PROVIDERS
}


def build_artifact_configs(
    project_settings,
):
    """Resolve project settings into artifact configurations."""

    return (
        ArtifactConfig(
            artifact_id="over_exposure",
            enabled=(
                project_settings
                .artifact_over_exposure_enabled
            ),
            probability=(
                project_settings
                .artifact_over_exposure_probability
            ),
            intensity=(
                project_settings
                .artifact_over_exposure_intensity
            ),
        ),
    )


def capture_artifact_baseline(
    scene,
):
    """Capture reset state for every registered provider."""

    return {
        provider.artifact_id: (
            provider.capture(
                scene,
            )
        )
        for provider in _PROVIDERS
    }


def restore_artifacts(
    scene,
    baseline,
):
    """Reset all registered artifact providers."""

    for provider in reversed(
        _PROVIDERS
    ):
        provider_baseline = baseline.get(
            provider.artifact_id
        )

        if provider_baseline is None:
            continue

        provider.reset(
            scene,
            provider_baseline,
        )


def apply_artifacts(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    """Apply deterministic artifacts for one generated frame."""

    # A previous frame may have left an artifact active.
    # Every frame starts from the captured clean baseline.
    restore_artifacts(
        scene,
        baseline,
    )

    if not (
        project_settings
        .artifact_engine_enabled
    ):
        return {
            "enabled": False,
            "version": (
                ARTIFACT_ENGINE_VERSION
            ),
            "artifacts": [],
        }

    records = []

    configs = sorted(
        build_artifact_configs(
            project_settings,
        ),
        key=lambda item: (
            item.artifact_id
        ),
    )

    for config in configs:
        provider = (
            _PROVIDER_BY_ID.get(
                config.artifact_id
            )
        )

        if provider is None:
            raise ValueError(
                (
                    "Artifact provider is not "
                    "registered: "
                    f"{config.artifact_id}"
                )
            )

        provider.validate_config(
            config,
        )

        artifact_seed = derive_subseed(
            frame_seed,
            "artifact",
            config.artifact_id,
        )

        decision_roll = random.Random(
            artifact_seed
        ).random()

        applied = bool(
            config.enabled
            and (
                decision_roll
                < config.probability
            )
        )

        context = ArtifactContext(
            config=config,
            frame_seed=frame_seed,
            artifact_seed=artifact_seed,
            decision_roll=decision_roll,
        )

        metadata = {}

        if applied:
            metadata = provider.apply(
                scene,
                context,
                baseline[
                    config.artifact_id
                ],
            )

        records.append(
            provider.manifest_export(
                context=context,
                applied=applied,
                metadata=metadata,
            )
        )

    return {
        "enabled": True,
        "version": (
            ARTIFACT_ENGINE_VERSION
        ),
        "artifacts": records,
    }
