import random

from ..core.seeding import derive_subseed


LIGHTING_RANDOMIZER_VERSION = (
    "lighting-random-v1"
)


def _clamp(
    value,
    minimum,
    maximum,
):
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _scene_lights(scene):
    lights = [
        obj
        for obj in scene.objects
        if obj.type == "LIGHT"
    ]

    lights.sort(
        key=lambda obj: obj.name
    )

    return lights


def capture_lighting_baseline(scene):
    lights = []

    for obj in _scene_lights(scene):
        data = obj.data

        lights.append(
            {
                "object": obj,
                "data": data,
                "object_name": obj.name,
                "light_type": data.type,
                "location": (
                    obj.location.copy()
                ),
                "energy": float(
                    data.energy
                ),
                "color": tuple(
                    float(value)
                    for value
                    in data.color
                ),
            }
        )

    return {
        "lights": lights,
    }


def apply_random_lighting(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    lights = baseline["lights"]

    if not (
        project_settings
        .lighting_randomization_enabled
    ):
        return {
            "enabled": False,
            "version": (
                LIGHTING_RANDOMIZER_VERSION
            ),
            "lights": [],
        }

    if not lights:
        raise ValueError(
            "Lighting randomization is enabled "
            "but the scene contains no lights"
        )

    results = []

    for base in lights:
        obj = base["object"]
        data = base["data"]

        light_seed = derive_subseed(
            frame_seed,
            "lighting",
            base["object_name"],
        )

        rng = random.Random(
            light_seed
        )

        position_x = rng.uniform(
            -project_settings
            .lighting_position_offset_x,
            project_settings
            .lighting_position_offset_x,
        )

        position_y = rng.uniform(
            -project_settings
            .lighting_position_offset_y,
            project_settings
            .lighting_position_offset_y,
        )

        position_z = rng.uniform(
            -project_settings
            .lighting_position_offset_z,
            project_settings
            .lighting_position_offset_z,
        )

        energy_variation = (
            project_settings
            .lighting_energy_variation
        )

        energy_multiplier = rng.uniform(
            max(
                0.0,
                1.0 - energy_variation,
            ),
            1.0 + energy_variation,
        )

        color_variation = (
            project_settings
            .lighting_color_variation
        )

        sampled_color = [
            _clamp(
                (
                    base["color"][index]
                    + rng.uniform(
                        -color_variation,
                        color_variation,
                    )
                ),
                0.0,
                1.0,
            )
            for index in range(3)
        ]

        base_location = (
            base["location"]
        )

        obj.location.x = (
            base_location.x
            + position_x
        )

        obj.location.y = (
            base_location.y
            + position_y
        )

        obj.location.z = (
            base_location.z
            + position_z
        )

        data.energy = max(
            0.0,
            (
                base["energy"]
                * energy_multiplier
            ),
        )

        data.color = (
            sampled_color
        )

        actual_location = (
            obj.location.copy()
        )

        actual_color = tuple(
            float(value)
            for value
            in data.color
        )

        actual_energy = float(
            data.energy
        )

        results.append(
            {
                "object_name": (
                    base["object_name"]
                ),
                "light_type": (
                    base["light_type"]
                ),
                "seed": light_seed,
                "space": "object_local",
                "base": {
                    "location": [
                        float(base_location.x),
                        float(base_location.y),
                        float(base_location.z),
                    ],
                    "energy": (
                        base["energy"]
                    ),
                    "color": list(
                        base["color"]
                    ),
                },
                "offset": {
                    "position": [
                        float(
                            actual_location.x
                            - base_location.x
                        ),
                        float(
                            actual_location.y
                            - base_location.y
                        ),
                        float(
                            actual_location.z
                            - base_location.z
                        ),
                    ],
                    "color": [
                        (
                            actual_color[index]
                            - base["color"][index]
                        )
                        for index in range(3)
                    ],
                },
                "energy_multiplier": (
                    energy_multiplier
                ),
                "state": {
                    "location": [
                        float(
                            actual_location.x
                        ),
                        float(
                            actual_location.y
                        ),
                        float(
                            actual_location.z
                        ),
                    ],
                    "energy": (
                        actual_energy
                    ),
                    "color": list(
                        actual_color
                    ),
                },
            }
        )

    return {
        "enabled": True,
        "version": (
            LIGHTING_RANDOMIZER_VERSION
        ),
        "ranges": {
            "position": {
                "x": (
                    project_settings
                    .lighting_position_offset_x
                ),
                "y": (
                    project_settings
                    .lighting_position_offset_y
                ),
                "z": (
                    project_settings
                    .lighting_position_offset_z
                ),
            },
            "energy_variation": (
                project_settings
                .lighting_energy_variation
            ),
            "color_variation": (
                project_settings
                .lighting_color_variation
            ),
        },
        "lights": results,
    }


def restore_lighting(
    scene,
    baseline,
):
    for base in baseline["lights"]:
        obj = base["object"]
        data = base["data"]

        obj.location = (
            base["location"]
        )

        data.energy = (
            base["energy"]
        )

        data.color = (
            base["color"]
        )
