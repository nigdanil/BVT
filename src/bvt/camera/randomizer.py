import random


from ..core.seeding import derive_subseed


CAMERA_RANDOMIZER_VERSION = (
    "camera-transform-random-v1"
)


def capture_camera_baseline(scene):
    camera = scene.camera

    if camera is None:
        raise ValueError(
            "The scene does not have an active camera"
        )

    return {
        "camera": camera,
        "camera_name": camera.name,
        "rotation_mode": camera.rotation_mode,
        "location": camera.location.copy(),
        "rotation_euler": (
            camera.rotation_euler.copy()
        ),
        "lens_mm": float(
            camera.data.lens
        ),
    }


def _camera_state(
    camera,
):
    return {
        "location": [
            float(camera.location.x),
            float(camera.location.y),
            float(camera.location.z),
        ],
        "rotation_euler_rad": [
            float(camera.rotation_euler.x),
            float(camera.rotation_euler.y),
            float(camera.rotation_euler.z),
        ],
        "lens_mm": float(
            camera.data.lens
        ),
    }


def apply_random_camera(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    camera = scene.camera

    if camera is None:
        raise ValueError(
            "The scene does not have an active camera"
        )

    if camera is not baseline["camera"]:
        raise ValueError(
            "Active camera changed during generation"
        )

    if not project_settings.camera_randomization_enabled:
        return {
            "enabled": False,
            "version": CAMERA_RANDOMIZER_VERSION,
            "camera_name": camera.name,
            "space": "object_local",
            "transform": _camera_state(
                camera,
            ),
        }

    if baseline["rotation_mode"] in {
        "QUATERNION",
        "AXIS_ANGLE",
    }:
        raise ValueError(
            "Camera randomization currently "
            "requires an Euler rotation mode"
        )

    camera_seed = derive_subseed(
        frame_seed,
        "camera",
        camera.name,
    )

    rng = random.Random(
        camera_seed
    )

    sampled_position_x = rng.uniform(
        -project_settings.camera_position_offset_x,
        project_settings.camera_position_offset_x,
    )

    sampled_position_y = rng.uniform(
        -project_settings.camera_position_offset_y,
        project_settings.camera_position_offset_y,
    )

    sampled_position_z = rng.uniform(
        -project_settings.camera_position_offset_z,
        project_settings.camera_position_offset_z,
    )

    sampled_rotation_x = rng.uniform(
        -project_settings.camera_rotation_offset_x,
        project_settings.camera_rotation_offset_x,
    )

    sampled_rotation_y = rng.uniform(
        -project_settings.camera_rotation_offset_y,
        project_settings.camera_rotation_offset_y,
    )

    sampled_rotation_z = rng.uniform(
        -project_settings.camera_rotation_offset_z,
        project_settings.camera_rotation_offset_z,
    )

    base_location = baseline["location"]
    base_rotation = baseline["rotation_euler"]

    camera.location.x = (
        base_location.x
        + sampled_position_x
    )

    camera.location.y = (
        base_location.y
        + sampled_position_y
    )

    camera.location.z = (
        base_location.z
        + sampled_position_z
    )

    camera.rotation_euler.x = (
        base_rotation.x
        + sampled_rotation_x
    )

    camera.rotation_euler.y = (
        base_rotation.y
        + sampled_rotation_y
    )

    camera.rotation_euler.z = (
        base_rotation.z
        + sampled_rotation_z
    )

    actual_location = (
        camera.location.copy()
    )

    actual_rotation = (
        camera.rotation_euler.copy()
    )

    actual_position_offset = [
        (
            actual_location.x
            - base_location.x
        ),
        (
            actual_location.y
            - base_location.y
        ),
        (
            actual_location.z
            - base_location.z
        ),
    ]

    actual_rotation_offset = [
        (
            actual_rotation.x
            - base_rotation.x
        ),
        (
            actual_rotation.y
            - base_rotation.y
        ),
        (
            actual_rotation.z
            - base_rotation.z
        ),
    ]

    return {
        "enabled": True,
        "version": CAMERA_RANDOMIZER_VERSION,
        "camera_name": camera.name,
        "seed": camera_seed,
        "space": "object_local",
        "ranges": {
            "position": {
                "x": (
                    project_settings
                    .camera_position_offset_x
                ),
                "y": (
                    project_settings
                    .camera_position_offset_y
                ),
                "z": (
                    project_settings
                    .camera_position_offset_z
                ),
            },
            "rotation_rad": {
                "x": (
                    project_settings
                    .camera_rotation_offset_x
                ),
                "y": (
                    project_settings
                    .camera_rotation_offset_y
                ),
                "z": (
                    project_settings
                    .camera_rotation_offset_z
                ),
            },
        },
        "base": {
            "location": [
                float(base_location.x),
                float(base_location.y),
                float(base_location.z),
            ],
            "rotation_euler_rad": [
                float(base_rotation.x),
                float(base_rotation.y),
                float(base_rotation.z),
            ],
            "lens_mm": baseline[
                "lens_mm"
            ],
        },
        "offset": {
            "position": [
                float(value)
                for value
                in actual_position_offset
            ],
            "rotation_euler_rad": [
                float(value)
                for value
                in actual_rotation_offset
            ],
        },
        "transform": _camera_state(
            camera,
        ),
    }


def restore_camera(
    scene,
    baseline,
):
    camera = baseline["camera"]

    camera.location = (
        baseline["location"]
    )

    camera.rotation_mode = (
        baseline["rotation_mode"]
    )

    camera.rotation_euler = (
        baseline["rotation_euler"]
    )

    camera.data.lens = (
        baseline["lens_mm"]
    )
