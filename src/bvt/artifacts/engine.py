import random

from ..core.seeding import derive_subseed
from .base import ArtifactConfig
from .base import ArtifactContext
from .providers.exposure import (
    OverExposureArtifactProvider,
)
from .providers.noise import (
    NoiseArtifactProvider,
)


ARTIFACT_ENGINE_VERSION = (
    "artifact-engine-v1"
)


_PROVIDERS = (
    OverExposureArtifactProvider(),
    NoiseArtifactProvider(),
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
        ArtifactConfig(
            artifact_id="noise",
            enabled=(
                project_settings
                .artifact_noise_enabled
            ),
            probability=(
                project_settings
                .artifact_noise_probability
            ),
            intensity=(
                project_settings
                .artifact_noise_intensity
            ),
        ),
    )


def capture_artifact_baseline(
    scene,
):
    """Capture reset state for every provider."""

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
    """Reset all providers in reverse registration order."""

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


def _provider_for(
    artifact_id,
):
    provider = (
        _PROVIDER_BY_ID.get(
            artifact_id
        )
    )

    if provider is None:
        raise ValueError(
            (
                "Artifact provider is not "
                "registered: "
                f"{artifact_id}"
            )
        )

    return provider


def _context_from_record(
    record,
    frame_seed,
):
    config = ArtifactConfig(
        artifact_id=(
            record["artifact"]
        ),
        enabled=(
            record["enabled"]
        ),
        probability=(
            record["probability"]
        ),
        intensity=(
            record["intensity"]
        ),
    )

    return ArtifactContext(
        config=config,
        frame_seed=frame_seed,
        artifact_seed=(
            record["seed"]
        ),
        decision_roll=(
            record["decision_roll"]
        ),
    )


def apply_artifacts(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    """
    Resolve decisions for every artifact and apply
    pre-render providers.
    """

    # Every frame starts from the clean captured baseline.
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
        provider = _provider_for(
            config.artifact_id
        )

        provider.validate_config(
            config
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

        if (
            applied
            and provider.stage
            == "pre_render"
        ):
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


def apply_post_render_artifacts(
    scene,
    image_path,
    frame_seed,
    artifact_result,
    baseline,
):
    """Apply post-render providers to the rendered image."""

    if not artifact_result["enabled"]:
        return artifact_result

    records = (
        artifact_result[
            "artifacts"
        ]
    )

    for index, record in enumerate(
        records
    ):
        provider = _provider_for(
            record["artifact"]
        )

        if (
            provider.stage
            != "post_render"
        ):
            continue

        if not record["applied"]:
            continue

        context = _context_from_record(
            record,
            frame_seed,
        )

        metadata = (
            provider.apply_post_render(
                scene=scene,
                image_path=image_path,
                context=context,
                baseline=baseline[
                    provider.artifact_id
                ],
            )
        )

        records[index] = (
            provider.manifest_export(
                context=context,
                applied=True,
                metadata=metadata,
            )
        )

    return artifact_result
