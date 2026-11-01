import math
import random

from ...core.seeding import derive_subseed


SCRATCHES_MASK_RESOLUTION = 256
SCRATCHES_COUNT = 32

_SHORT_COUNT = 22
_MEDIUM_COUNT = 8
_LONG_COUNT = 2


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


def _length_for_class(
    rng,
    size_class,
):
    if size_class == "short":
        return rng.uniform(
            0.04,
            0.10,
        )

    if size_class == "medium":
        return rng.uniform(
            0.10,
            0.20,
        )

    if size_class == "long":
        return rng.uniform(
            0.20,
            0.35,
        )

    raise ValueError(
        f"Unknown scratch size class: {size_class}"
    )


def _segment_count_for_class(
    size_class,
):
    if size_class == "short":
        return 3

    if size_class == "medium":
        return 4

    if size_class == "long":
        return 5

    raise ValueError(
        f"Unknown scratch size class: {size_class}"
    )


def _build_centerline(
    *,
    center_u,
    center_v,
    angle,
    length,
    curvature,
    segment_count,
):
    direction_u = math.cos(
        angle
    )

    direction_v = math.sin(
        angle
    )

    perpendicular_u = (
        -direction_v
    )

    perpendicular_v = (
        direction_u
    )

    points = []

    for index in range(
        segment_count + 1
    ):
        normalized = (
            index
            / float(
                segment_count
            )
        )

        along = (
            normalized
            - 0.5
        )

        # Zero curvature at both ends and maximum
        # displacement near the scratch midpoint.
        curve_profile = (
            1.0
            - (
                2.0
                * along
            )
            ** 2
        )

        curve_offset = (
            curvature
            * length
            * curve_profile
        )

        u = (
            center_u
            + direction_u
            * along
            * length
            + perpendicular_u
            * curve_offset
        )

        v = (
            center_v
            + direction_v
            * along
            * length
            + perpendicular_v
            * curve_offset
        )

        points.append(
            (
                _clamp(
                    u,
                    0.001,
                    0.999,
                ),
                _clamp(
                    v,
                    0.001,
                    0.999,
                ),
            )
        )

    return tuple(
        points
    )


def _sample_scratches(
    layout_seed,
    shape_seed,
):
    layout_rng = random.Random(
        layout_seed
    )

    shape_rng = random.Random(
        shape_seed
    )

    size_classes = (
        ["short"] * _SHORT_COUNT
        + ["medium"] * _MEDIUM_COUNT
        + ["long"] * _LONG_COUNT
    )

    layout_rng.shuffle(
        size_classes
    )

    scratches = []

    for index, size_class in enumerate(
        size_classes
    ):
        length = _length_for_class(
            layout_rng,
            size_class,
        )

        center_u = layout_rng.uniform(
            0.18,
            0.82,
        )

        center_v = layout_rng.uniform(
            0.18,
            0.82,
        )

        angle = layout_rng.uniform(
            0.0,
            math.tau,
        )

        width = shape_rng.uniform(
            0.0014,
            0.0036,
        )

        amplitude = shape_rng.uniform(
            0.55,
            0.98,
        )

        curvature = shape_rng.uniform(
            -0.12,
            0.12,
        )

        edge_softness = (
            shape_rng.uniform(
                0.32,
                0.58,
            )
        )

        segment_count = (
            _segment_count_for_class(
                size_class
            )
        )

        points = _build_centerline(
            center_u=center_u,
            center_v=center_v,
            angle=angle,
            length=length,
            curvature=curvature,
            segment_count=segment_count,
        )

        scratches.append(
            {
                "index": index,
                "size_class": (
                    size_class
                ),
                "center_u": (
                    center_u
                ),
                "center_v": (
                    center_v
                ),
                "angle": angle,
                "length": length,
                "width": width,
                "amplitude": (
                    amplitude
                ),
                "curvature": (
                    curvature
                ),
                "edge_softness": (
                    edge_softness
                ),
                "segment_count": (
                    segment_count
                ),
                "points": points,
            }
        )

    return tuple(
        scratches
    )


def _distance_to_segment(
    point_x,
    point_y,
    start_x,
    start_y,
    end_x,
    end_y,
):
    segment_x = (
        end_x
        - start_x
    )

    segment_y = (
        end_y
        - start_y
    )

    length_squared = (
        segment_x
        * segment_x
        + segment_y
        * segment_y
    )

    if length_squared <= 1e-12:
        dx = (
            point_x
            - start_x
        )

        dy = (
            point_y
            - start_y
        )

        return math.sqrt(
            dx * dx
            + dy * dy
        )

    projection = (
        (
            point_x
            - start_x
        )
        * segment_x
        + (
            point_y
            - start_y
        )
        * segment_y
    ) / length_squared

    projection = _clamp(
        projection
    )

    closest_x = (
        start_x
        + projection
        * segment_x
    )

    closest_y = (
        start_y
        + projection
        * segment_y
    )

    dx = (
        point_x
        - closest_x
    )

    dy = (
        point_y
        - closest_y
    )

    return math.sqrt(
        dx * dx
        + dy * dy
    )


def _splat_segment(
    values,
    resolution,
    *,
    start,
    end,
    width,
    amplitude,
    edge_softness,
):
    start_x = (
        start[0]
        * resolution
    )

    start_y = (
        start[1]
        * resolution
    )

    end_x = (
        end[0]
        * resolution
    )

    end_y = (
        end[1]
        * resolution
    )

    radius_pixels = max(
        0.65,
        width
        * resolution,
    )

    extent = (
        radius_pixels
        + 1.5
    )

    min_x = max(
        0,
        int(
            math.floor(
                min(
                    start_x,
                    end_x,
                )
                - extent
            )
        ),
    )

    max_x = min(
        resolution - 1,
        int(
            math.ceil(
                max(
                    start_x,
                    end_x,
                )
                + extent
            )
        ),
    )

    min_y = max(
        0,
        int(
            math.floor(
                min(
                    start_y,
                    end_y,
                )
                - extent
            )
        ),
    )

    max_y = min(
        resolution - 1,
        int(
            math.ceil(
                max(
                    start_y,
                    end_y,
                )
                + extent
            )
        ),
    )

    edge_start = (
        1.0
        - edge_softness
    )

    for y in range(
        min_y,
        max_y + 1,
    ):
        point_y = (
            y + 0.5
        )

        for x in range(
            min_x,
            max_x + 1,
        ):
            point_x = (
                x + 0.5
            )

            distance = (
                _distance_to_segment(
                    point_x,
                    point_y,
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                )
            )

            normalized = (
                distance
                / radius_pixels
            )

            if normalized >= 1.0:
                continue

            if normalized <= edge_start:
                edge_value = 1.0

            else:
                t = _clamp(
                    (
                        1.0
                        - normalized
                    )
                    / edge_softness
                )

                edge_value = (
                    t
                    * t
                    * (
                        3.0
                        - 2.0 * t
                    )
                )

            contribution = (
                amplitude
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

            # Soft union keeps crossings bounded
            # and deterministic.
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


def _splat_scratch(
    values,
    resolution,
    scratch,
):
    points = scratch[
        "points"
    ]

    for index in range(
        len(points) - 1
    ):
        _splat_segment(
            values,
            resolution,
            start=points[index],
            end=points[
                index + 1
            ],
            width=scratch[
                "width"
            ],
            amplitude=scratch[
                "amplitude"
            ],
            edge_softness=scratch[
                "edge_softness"
            ],
        )


def build_scratches_mask(
    seed,
    resolution=(
        SCRATCHES_MASK_RESOLUTION
    ),
):
    layout_seed = derive_subseed(
        seed,
        "scratches-mask",
        "layout",
    )

    shape_seed = derive_subseed(
        seed,
        "scratches-mask",
        "shape",
    )

    scratches = _sample_scratches(
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

    for scratch in scratches:
        _splat_scratch(
            values,
            resolution,
            scratch,
        )

    pixels = []

    covered_pixels = 0
    total_value = 0.0

    for raw_value in values:
        value = _clamp(
            raw_value
        )

        if value > 0.08:
            covered_pixels += 1

        total_value += value

        # White RGB, scratch mask in alpha.
        pixels.extend(
            (
                1.0,
                1.0,
                1.0,
                value,
            )
        )

    class_counts = {
        "short": sum(
            1
            for scratch in scratches
            if scratch[
                "size_class"
            ] == "short"
        ),
        "medium": sum(
            1
            for scratch in scratches
            if scratch[
                "size_class"
            ] == "medium"
        ),
        "long": sum(
            1
            for scratch in scratches
            if scratch[
                "size_class"
            ] == "long"
        ),
    }

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
        "scratch_count": len(
            scratches
        ),
        "class_counts": (
            class_counts
        ),
        "scratches": scratches,
    }
