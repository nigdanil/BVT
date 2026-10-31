import math
import random

from ...core.seeding import derive_subseed


WATER_DROPS_MASK_RESOLUTION = 256
WATER_DROPS_COUNT = 48


def _clamp(
    value,
    minimum=0.0,
    maximum=1.0,
):
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _sample_drops(
    layout_seed,
    shape_seed,
):
    layout_rng = random.Random(
        layout_seed
    )

    shape_rng = random.Random(
        shape_seed
    )

    drops = []

    for index in range(
        WATER_DROPS_COUNT
    ):
        size_roll = (
            layout_rng.random()
        )

        # Mostly small droplets, fewer medium
        # droplets and only occasional large ones.
        if size_roll < 0.68:
            size_class = "small"
            major_radius = (
                layout_rng.uniform(
                    0.007,
                    0.016,
                )
            )

        elif size_roll < 0.94:
            size_class = "medium"
            major_radius = (
                layout_rng.uniform(
                    0.016,
                    0.028,
                )
            )

        else:
            size_class = "large"
            major_radius = (
                layout_rng.uniform(
                    0.028,
                    0.042,
                )
            )

        aspect = (
            shape_rng.uniform(
                0.68,
                1.0,
            )
        )

        minor_radius = (
            major_radius
            * aspect
        )

        drops.append(
            {
                "index": index,
                "size_class": (
                    size_class
                ),
                "center_u": (
                    layout_rng.uniform(
                        0.035,
                        0.965,
                    )
                ),
                "center_v": (
                    layout_rng.uniform(
                        0.035,
                        0.965,
                    )
                ),
                "major_radius": (
                    major_radius
                ),
                "minor_radius": (
                    minor_radius
                ),
                "aspect": aspect,
                "angle": (
                    shape_rng.uniform(
                        0.0,
                        math.tau,
                    )
                ),
                "amplitude": (
                    shape_rng.uniform(
                        0.72,
                        1.0,
                    )
                ),
                "edge_softness": (
                    shape_rng.uniform(
                        0.16,
                        0.30,
                    )
                ),
            }
        )

    return tuple(
        drops
    )


def _splat_drop(
    values,
    resolution,
    drop,
):
    center_x = (
        drop["center_u"]
        * resolution
    )

    center_y = (
        drop["center_v"]
        * resolution
    )

    major_pixels = max(
        1.0,
        drop["major_radius"]
        * resolution,
    )

    minor_pixels = max(
        1.0,
        drop["minor_radius"]
        * resolution,
    )

    extent = int(
        math.ceil(
            major_pixels
            * 1.15
        )
    )

    min_x = max(
        0,
        int(center_x) - extent,
    )

    max_x = min(
        resolution - 1,
        int(center_x) + extent,
    )

    min_y = max(
        0,
        int(center_y) - extent,
    )

    max_y = min(
        resolution - 1,
        int(center_y) + extent,
    )

    angle = drop["angle"]

    cos_angle = math.cos(
        angle
    )

    sin_angle = math.sin(
        angle
    )

    edge_softness = (
        drop["edge_softness"]
    )

    edge_start = (
        1.0
        - edge_softness
    )

    for y in range(
        min_y,
        max_y + 1,
    ):
        dy = (
            y + 0.5
            - center_y
        )

        for x in range(
            min_x,
            max_x + 1,
        ):
            dx = (
                x + 0.5
                - center_x
            )

            rotated_x = (
                cos_angle * dx
                + sin_angle * dy
            )

            rotated_y = (
                -sin_angle * dx
                + cos_angle * dy
            )

            normalized_distance = (
                math.sqrt(
                    (
                        rotated_x
                        / major_pixels
                    )
                    ** 2
                    + (
                        rotated_y
                        / minor_pixels
                    )
                    ** 2
                )
            )

            if (
                normalized_distance
                >= 1.0
            ):
                continue

            if (
                normalized_distance
                <= edge_start
            ):
                edge_value = 1.0

            else:
                t = _clamp(
                    (
                        1.0
                        - normalized_distance
                    )
                    / edge_softness
                )

                # Smoothstep creates a soft rounded
                # droplet boundary.
                edge_value = (
                    t
                    * t
                    * (
                        3.0
                        - 2.0 * t
                    )
                )

            contribution = (
                drop["amplitude"]
                * edge_value
            )

            value_index = (
                y
                * resolution
                + x
            )

            current = values[
                value_index
            ]

            # Soft union keeps overlapping droplets
            # deterministic and bounded to [0, 1].
            values[value_index] = (
                1.0
                - (
                    1.0
                    - current
                )
                * (
                    1.0
                    - contribution
                )
            )


def build_water_drops_mask(
    seed,
    resolution=(
        WATER_DROPS_MASK_RESOLUTION
    ),
):
    layout_seed = derive_subseed(
        seed,
        "water-drops-mask",
        "layout",
    )

    shape_seed = derive_subseed(
        seed,
        "water-drops-mask",
        "shape",
    )

    drops = _sample_drops(
        layout_seed,
        shape_seed,
    )

    pixel_count = (
        resolution
        * resolution
    )

    values = [
        0.0
    ] * pixel_count

    for drop in drops:
        _splat_drop(
            values,
            resolution,
            drop,
        )

    pixels = []

    covered_pixels = 0
    total_value = 0.0

    for raw_value in values:
        value = _clamp(
            raw_value
        )

        if value > 0.10:
            covered_pixels += 1

        total_value += value

        # White RGB, droplet mask in alpha.
        pixels.extend(
            (
                1.0,
                1.0,
                1.0,
                value,
            )
        )

    return {
        "pixels": pixels,
        "coverage": (
            covered_pixels
            / float(
                pixel_count
            )
        ),
        "mean_mask_value": (
            total_value
            / float(
                pixel_count
            )
        ),
        "layout_seed": (
            layout_seed
        ),
        "shape_seed": (
            shape_seed
        ),
        "drop_count": len(
            drops
        ),
        "drops": drops,
    }
