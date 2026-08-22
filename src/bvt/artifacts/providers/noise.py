import random

import bpy

from ...core.seeding import derive_subseed
from ..base import ArtifactProvider


NOISE_MAX_AMPLITUDE = 0.08


class NoiseArtifactProvider(
    ArtifactProvider
):
    """Apply deterministic RGB sensor noise."""

    artifact_id = "noise"
    category = "sensor"
    stage = "post_render"

    description = (
        "Simulates deterministic RGB sensor noise"
    )

    def capture(
        self,
        scene,
    ):
        """Noise does not modify persistent scene state."""

        return {}

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """Noise must execute after the image is rendered."""

        raise RuntimeError(
            "Noise artifact must run post-render"
        )

    def apply_post_render(
        self,
        scene,
        image_path,
        context,
        baseline,
    ):
        """Add deterministic independent RGB noise."""

        image_path = str(
            image_path
        )

        pixel_seed = derive_subseed(
            context.artifact_seed,
            "artifact-noise",
            "pixels",
        )

        amplitude = (
            NOISE_MAX_AMPLITUDE
            * context.config.intensity
        )

        rng = random.Random(
            pixel_seed
        )

        image = bpy.data.images.load(
            image_path,
            check_existing=False,
        )

        try:
            width = int(
                image.size[0]
            )

            height = int(
                image.size[1]
            )

            channels = int(
                image.channels
            )

            if channels < 3:
                raise ValueError(
                    "Noise artifact requires "
                    "an RGB or RGBA image"
                )

            pixels = list(
                image.pixels[:]
            )

            changed_components = 0

            for offset in range(
                0,
                len(pixels),
                channels,
            ):
                for channel in range(3):
                    index = (
                        offset
                        + channel
                    )

                    original = (
                        pixels[index]
                    )

                    delta = rng.uniform(
                        -amplitude,
                        amplitude,
                    )

                    value = max(
                        0.0,
                        min(
                            1.0,
                            original
                            + delta,
                        ),
                    )

                    if (
                        abs(
                            value
                            - original
                        )
                        > 1e-12
                    ):
                        changed_components += 1

                    pixels[index] = value

            image.pixels[:] = pixels

            image.update()

            image.filepath_raw = (
                image_path
            )

            image.file_format = "PNG"

            image.save()

        finally:
            bpy.data.images.remove(
                image
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
                "distribution": "uniform",
                "color_mode": "rgb_independent",
                "amplitude": amplitude,
                "pixel_seed": pixel_seed,
                "width": width,
                "height": height,
                "channels": channels,
                "changed_components": (
                    changed_components
                ),
            },
        }

    def reset(
        self,
        scene,
        baseline,
    ):
        """Post-render noise has no scene state to reset."""

        return None

    def compatibility_rules(self):
        return (
            "requires_rgb_or_rgba_image",
        )
