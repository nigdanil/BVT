import math
import random

from ...core.seeding import derive_subseed


DUST_MASK_RESOLUTION = 256

DUST_PARTICLE_COUNT = 220
DUST_CLUSTER_COUNT = 12


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


def _sample_clusters(
    seed,
):
    rng = random.Random(
        seed
    )

    clusters = []

    for index in range(
        DUST_CLUSTER_COUNT
    ):
        clusters.append(
            {
                "index": index,
                "center_u": rng.uniform(
                    0.05,
                    0.95,
                ),
                "center_v": rng.uniform(
                    0.05,
                    0.95,
                ),
                "radius": rng.uniform(
                    0.055,
                    0.16,
                ),
                "amplitude": rng.uniform(
                    0.04,
                    0.12,
                ),
            }
        )

    return tuple(
        clusters
    )


def _sample_particles(
    seed,
    clusters,
):
    rng = random.Random(
        seed
    )

    particles = []

    for index in range(
        DUST_PARTICLE_COUNT
    ):
        clustered = (
            rng.random()
            < 0.72
        )

        cluster_index = None

        if clustered:
            cluster = rng.choice(
                clusters
            )

            cluster_index = (
                cluster[
                    "index"
                ]
            )

            angle = rng.uniform(
                0.0,
                math.tau,
            )

            distance = (
                math.sqrt(
                    rng.random()
                )
                * cluster[
                    "radius"
                ]
            )

            center_u = _clamp(
                cluster[
                    "center_u"
                ]
                + math.cos(
                    angle
                )
                * distance,
                0.01,
                0.99,
            )

            center_v = _clamp(
                cluster[
                    "center_v"
                ]
                + math.sin(
                    angle
                )
                * distance,
                0.01,
                0.99,
            )

        else:
            center_u = rng.uniform(
                0.01,
                0.99,
            )

            center_v = rng.uniform(
                0.01,
                0.99,
            )

        particles.append(
            {
                "index": index,
                "cluster_index": (
                    cluster_index
                ),
                "center_u": center_u,
                "center_v": center_v,
                "radius": rng.uniform(
                    0.0035,
                    0.012,
                ),
                "amplitude": rng.uniform(
                    0.30,
                    0.92,
                ),
                "hardness": rng.uniform(
                    1.4,
                    3.2,
                ),
            }
        )

    return tuple(
        particles
    )


def _splat(
    values,
    resolution,
    *,
    center_u,
    center_v,
    radius,
    amplitude,
    hardness,
):
    center_x = (
        center_u
        * resolution
    )

    center_y = (
        center_v
        * resolution
    )

    radius_pixels = max(
        1.0,
        radius
        * resolution,
    )

    extent = int(
        math.ceil(
            radius_pixels
            * 1.25
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

    radius_squared = (
        radius_pixels
        * radius_pixels
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

            distance_squared = (
                dx * dx
                + dy * dy
            )

            if (
                distance_squared
                >= radius_squared
            ):
                continue

            normalized = (
                distance_squared
                / radius_squared
            )

            contribution = (
                amplitude
                * (
                    1.0
                    - normalized
                )
                ** hardness
            )

            index = (
                y
                * resolution
                + x
            )

            current = values[
                index
            ]

            # Soft union keeps overlapping dust
            # particles bounded to [0, 1].
            values[index] = (
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


def build_dust_mask(
    seed,
    resolution=(
        DUST_MASK_RESOLUTION
    ),
):
    cluster_seed = derive_subseed(
        seed,
        "dust-mask",
        "clusters",
    )

    particle_seed = derive_subseed(
        seed,
        "dust-mask",
        "particles",
    )

    clusters = _sample_clusters(
        cluster_seed
    )

    particles = _sample_particles(
        particle_seed,
        clusters,
    )

    pixel_count = (
        resolution
        * resolution
    )

    values = [
        0.0
    ] * pixel_count

    # Low-amplitude irregular deposits.
    # These should remain much weaker than
    # Condensation haze.
    for cluster in clusters:
        _splat(
            values,
            resolution,
            center_u=(
                cluster[
                    "center_u"
                ]
            ),
            center_v=(
                cluster[
                    "center_v"
                ]
            ),
            radius=(
                cluster[
                    "radius"
                ]
            ),
            amplitude=(
                cluster[
                    "amplitude"
                ]
            ),
            hardness=1.8,
        )

    # Small granular particles are the dominant
    # visual signature of Dust.
    for particle in particles:
        _splat(
            values,
            resolution,
            center_u=(
                particle[
                    "center_u"
                ]
            ),
            center_v=(
                particle[
                    "center_v"
                ]
            ),
            radius=(
                particle[
                    "radius"
                ]
            ),
            amplitude=(
                particle[
                    "amplitude"
                ]
            ),
            hardness=(
                particle[
                    "hardness"
                ]
            ),
        )

    pixels = []

    covered_pixels = 0
    total_value = 0.0

    for raw_value in values:
        value = _clamp(
            raw_value
        )

        if value > 0.06:
            covered_pixels += 1

        total_value += value

        # White RGB, mask stored in alpha.
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
        "cluster_seed": (
            cluster_seed
        ),
        "particle_seed": (
            particle_seed
        ),
        "cluster_count": len(
            clusters
        ),
        "particle_count": len(
            particles
        ),
        "clusters": clusters,
        "particles": particles,
    }
