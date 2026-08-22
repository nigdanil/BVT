import math
import random

import bpy

from ...core.seeding import derive_subseed
from ..base import ArtifactProvider


MOTION_BLUR_MAX_LENGTH_PIXELS = 64


class MotionBlurArtifactProvider(
    ArtifactProvider
):
    """
    Apply deterministic directional camera-motion blur.
    """

    artifact_id = "motion_blur"
    category = "camera"
    stage = "post_render"
    execution_order = 50

    description = (
        "Simulates deterministic directional "
        "camera motion blur"
    )

    def validate_config(
        self,
        config,
    ):
        super().validate_config(
            config
        )

        direction_range = float(
            config.options.get(
                "direction_range_degrees",
                180.0,
            )
        )

        max_length = int(
            config.options.get(
                "max_length_pixels",
                16,
            )
        )

        if not (
            0.0
            <= direction_range
            <= 180.0
        ):
            raise ValueError(
                "Motion blur direction range must "
                "be between 0 and 180 degrees"
            )

        if not (
            1
            <= max_length
            <= MOTION_BLUR_MAX_LENGTH_PIXELS
        ):
            raise ValueError(
                "Motion blur maximum length must "
                "be between 1 and "
                f"{MOTION_BLUR_MAX_LENGTH_PIXELS} pixels"
            )

    def capture(
        self,
        scene,
    ):
        """Motion blur does not modify persistent scene state."""

        return {}

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """Motion blur must execute after rendering."""

        raise RuntimeError(
            "Motion blur artifact must run post-render"
        )

    @staticmethod
    def _build_offsets(
        length_pixels,
        direction_radians,
    ):
        if length_pixels <= 1:
            return (
                (0, 0),
            )

        cosine = math.cos(
            direction_radians
        )

        sine = math.sin(
            direction_radians
        )

        center = (
            length_pixels - 1
        ) / 2.0

        offsets = []
        seen = set()

        for index in range(
            length_pixels
        ):
            distance = (
                index - center
            )

            offset = (
                int(
                    round(
                        cosine
                        * distance
                    )
                ),
                int(
                    round(
                        sine
                        * distance
                    )
                ),
            )

            if offset in seen:
                continue

            seen.add(
                offset
            )

            offsets.append(
                offset
            )

        if (0, 0) not in seen:
            offsets.append(
                (0, 0)
            )

        return tuple(
            offsets
        )

    def apply_post_render(
        self,
        scene,
        image_path,
        context,
        baseline,
    ):
        """
        Apply a deterministic directional box blur
        to the rendered RGB image.
        """

        image_path = str(
            image_path
        )

        configured_direction_range = float(
            context.config.options.get(
                "direction_range_degrees",
                180.0,
            )
        )

        configured_max_length = int(
            context.config.options.get(
                "max_length_pixels",
                16,
            )
        )

        direction_seed = derive_subseed(
            context.artifact_seed,
            "artifact-motion-blur",
            "direction",
        )

        direction_rng = random.Random(
            direction_seed
        )

        if configured_direction_range > 0.0:
            direction_degrees = (
                direction_rng.uniform(
                    -configured_direction_range,
                    configured_direction_range,
                )
            )
        else:
            direction_degrees = 0.0

        effective_length = int(
            round(
                1.0
                + (
                    configured_max_length
                    - 1
                )
                * context.config.intensity
            )
        )

        effective_length = max(
            1,
            min(
                configured_max_length,
                effective_length,
            ),
        )

        direction_radians = (
            math.radians(
                direction_degrees
            )
        )

        offsets = self._build_offsets(
            effective_length,
            direction_radians,
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
                    "Motion blur requires "
                    "an RGB or RGBA image"
                )

            source = list(
                image.pixels[:]
            )

            result = list(
                source
            )

            changed_components = 0

            for y in range(
                height
            ):
                for x in range(
                    width
                ):
                    red_sum = 0.0
                    green_sum = 0.0
                    blue_sum = 0.0
                    sample_count = 0

                    for dx, dy in offsets:
                        sample_x = (
                            x + dx
                        )

                        sample_y = (
                            y + dy
                        )

                        if not (
                            0
                            <= sample_x
                            < width
                            and 0
                            <= sample_y
                            < height
                        ):
                            continue

                        source_index = (
                            (
                                sample_y
                                * width
                                + sample_x
                            )
                            * channels
                        )

                        red_sum += (
                            source[
                                source_index
                            ]
                        )

                        green_sum += (
                            source[
                                source_index
                                + 1
                            ]
                        )

                        blue_sum += (
                            source[
                                source_index
                                + 2
                            ]
                        )

                        sample_count += 1

                    if sample_count == 0:
                        continue

                    target_index = (
                        (
                            y
                            * width
                            + x
                        )
                        * channels
                    )

                    values = (
                        red_sum
                        / sample_count,
                        green_sum
                        / sample_count,
                        blue_sum
                        / sample_count,
                    )

                    for channel, value in enumerate(
                        values
                    ):
                        original = (
                            source[
                                target_index
                                + channel
                            ]
                        )

                        if (
                            abs(
                                value
                                - original
                            )
                            > 1e-12
                        ):
                            changed_components += 1

                        result[
                            target_index
                            + channel
                        ] = value

            image.pixels[:] = result

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
                "algorithm": (
                    "directional_box_blur"
                ),
                "direction_seed": (
                    direction_seed
                ),
                "direction_range_degrees": (
                    configured_direction_range
                ),
                "direction_degrees": (
                    direction_degrees
                ),
                "configured_max_length_pixels": (
                    configured_max_length
                ),
                "effective_length_pixels": (
                    effective_length
                ),
                "kernel_sample_count": (
                    len(offsets)
                ),
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
        """Post-render motion blur has no scene state to reset."""

        return None

    def compatibility_rules(self):
        return (
            "requires_rgb_or_rgba_image",
        )
