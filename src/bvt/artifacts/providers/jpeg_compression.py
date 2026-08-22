from pathlib import Path

import bpy

from ..base import ArtifactProvider


JPEG_MAX_QUALITY = 100


class JPEGCompressionArtifactProvider(
    ArtifactProvider
):
    """Simulate lossy JPEG compression artifacts."""

    artifact_id = "jpeg_compression"
    category = "compression"
    stage = "post_render"
    execution_order = 200

    description = (
        "Simulates JPEG compression and chroma degradation"
    )

    def validate_config(
        self,
        config,
    ):
        super().validate_config(
            config
        )

        quality = int(
            config.options.get(
                "quality",
                40,
            )
        )

        chroma_loss = float(
            config.options.get(
                "chroma_loss",
                0.50,
            )
        )

        if not (
            1
            <= quality
            <= 100
        ):
            raise ValueError(
                "JPEG quality must be "
                "between 1 and 100"
            )

        if not (
            0.0
            <= chroma_loss
            <= 1.0
        ):
            raise ValueError(
                "JPEG chroma loss must be "
                "between 0 and 1"
            )

    def capture(
        self,
        scene,
    ):
        """JPEG compression has no persistent scene state."""

        return {}

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """JPEG compression must execute post-render."""

        raise RuntimeError(
            (
                "JPEG compression artifact "
                "must run post-render"
            )
        )

    def apply_post_render(
        self,
        scene,
        image_path,
        context,
        baseline,
    ):
        """
        Apply chroma degradation and a real JPEG
        encode/decode round trip.
        """

        image_path = Path(
            image_path
        )

        configured_quality = int(
            context.config.options.get(
                "quality",
                40,
            )
        )

        configured_chroma_loss = float(
            context.config.options.get(
                "chroma_loss",
                0.50,
            )
        )

        # Intensity interpolates between a clean image
        # and the user-selected JPEG target quality.
        effective_quality = int(
            round(
                JPEG_MAX_QUALITY
                - (
                    context.config.intensity
                    * (
                        JPEG_MAX_QUALITY
                        - configured_quality
                    )
                )
            )
        )

        effective_quality = max(
            1,
            min(
                JPEG_MAX_QUALITY,
                effective_quality,
            ),
        )

        effective_chroma_loss = (
            configured_chroma_loss
            * context.config.intensity
        )

        chroma_retention = (
            1.0
            - effective_chroma_loss
        )

        temporary_jpeg = (
            image_path.parent
            / (
                f".{image_path.stem}"
                ".bvt-jpeg-temp.jpg"
            )
        )

        if temporary_jpeg.exists():
            temporary_jpeg.unlink()

        source_image = None
        decoded_image = None

        try:
            source_image = (
                bpy.data.images.load(
                    str(image_path),
                    check_existing=False,
                )
            )

            width = int(
                source_image.size[0]
            )

            height = int(
                source_image.size[1]
            )

            channels = int(
                source_image.channels
            )

            if channels < 3:
                raise ValueError(
                    (
                        "JPEG compression artifact "
                        "requires RGB or RGBA image"
                    )
                )

            pixels = list(
                source_image.pixels[:]
            )

            changed_components = 0

            # Approximate chroma degradation by moving
            # RGB components toward luminance before
            # the actual JPEG encoding stage.
            if effective_chroma_loss > 0.0:
                for offset in range(
                    0,
                    len(pixels),
                    channels,
                ):
                    red = pixels[
                        offset
                    ]

                    green = pixels[
                        offset + 1
                    ]

                    blue = pixels[
                        offset + 2
                    ]

                    luminance = (
                        0.2126
                        * red
                        + 0.7152
                        * green
                        + 0.0722
                        * blue
                    )

                    values = (
                        red,
                        green,
                        blue,
                    )

                    for channel, original in enumerate(
                        values
                    ):
                        value = (
                            luminance
                            + (
                                original
                                - luminance
                            )
                            * chroma_retention
                        )

                        value = max(
                            0.0,
                            min(
                                1.0,
                                value,
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

                        pixels[
                            offset
                            + channel
                        ] = value

                source_image.pixels[:] = (
                    pixels
                )

                source_image.update()

            source_image.file_format = (
                "JPEG"
            )

            source_image.save(
                filepath=str(
                    temporary_jpeg
                ),
                quality=effective_quality,
                save_copy=True,
            )

            bpy.data.images.remove(
                source_image
            )

            source_image = None

            decoded_image = (
                bpy.data.images.load(
                    str(
                        temporary_jpeg
                    ),
                    check_existing=False,
                )
            )

            # Save through the scene render settings.
            # BVT generation keeps the dataset format as PNG,
            # so this guarantees a real PNG file rather than
            # re-saving the JPEG buffer with a .png extension.
            decoded_image.save_render(
                filepath=str(
                    image_path
                ),
                scene=scene,
            )

        finally:
            if source_image is not None:
                bpy.data.images.remove(
                    source_image
                )

            if decoded_image is not None:
                bpy.data.images.remove(
                    decoded_image
                )

            if temporary_jpeg.exists():
                temporary_jpeg.unlink()

        return {
            "affected_objects": [],
            "affected_camera": (
                scene.camera.name
                if scene.camera is not None
                else None
            ),
            "affected_materials": [],
            "parameters": {
                "codec": "jpeg",
                "dataset_format": "png",
                "configured_quality": (
                    configured_quality
                ),
                "effective_quality": (
                    effective_quality
                ),
                "configured_chroma_loss": (
                    configured_chroma_loss
                ),
                "effective_chroma_loss": (
                    effective_chroma_loss
                ),
                "chroma_retention": (
                    chroma_retention
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
        """JPEG compression has no scene state to reset."""

        return None

    def compatibility_rules(self):
        return (
            "requires_rgb_or_rgba_image",
            "preserves_png_dataset_contract",
        )
