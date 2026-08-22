from ..base import ArtifactProvider


OVER_EXPOSURE_MAX_STOPS = 3.0


class OverExposureArtifactProvider(
    ArtifactProvider
):
    """Simulate camera over-exposure."""

    artifact_id = "over_exposure"
    category = "lighting"

    description = (
        "Simulates an over-exposed camera image"
    )

    def capture(
        self,
        scene,
    ):
        """Capture the original exposure."""

        return {
            "exposure": float(
                scene.view_settings.exposure
            ),
        }

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """Increase exposure according to artifact intensity."""

        exposure_stops = (
            OVER_EXPOSURE_MAX_STOPS
            * context.config.intensity
        )

        scene.view_settings.exposure = (
            baseline["exposure"]
            + exposure_stops
        )

        return {
            "affected_objects": [],
            "affected_camera": (
                scene.camera.name
                if scene.camera is not None
                else None
            ),
            "affected_materials": [],
            "parameters": {
                "base_exposure": (
                    baseline["exposure"]
                ),
                "exposure_stops": (
                    exposure_stops
                ),
                "exposure_after": float(
                    scene.view_settings.exposure
                ),
            },
        }

    def reset(
        self,
        scene,
        baseline,
    ):
        """Restore the original exposure."""

        scene.view_settings.exposure = (
            baseline["exposure"]
        )

    def compatibility_rules(self):
        """Return current compatibility constraints."""

        return ()
