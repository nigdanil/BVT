import json
import math
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    TMP
    / "camera-randomization.blend"
)

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


def tuple3(value):
    return (
        float(value[0]),
        float(value[1]),
        float(value[2]),
    )


def close3(
    first,
    second,
    tolerance=1e-6,
):
    return all(
        abs(a - b) <= tolerance
        for a, b in zip(
            first,
            second,
        )
    )


if TMP.exists():
    shutil.rmtree(TMP)

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)


project = scene.bvt_project

project.project_name = (
    "Camera Randomization Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 3

project.placement_randomization_enabled = False

project.camera_randomization_enabled = True

project.camera_position_offset_x = 0.20
project.camera_position_offset_y = 0.20
project.camera_position_offset_z = 0.10

project.camera_rotation_offset_x = math.radians(
    1.5
)

project.camera_rotation_offset_y = math.radians(
    1.5
)

project.camera_rotation_offset_z = math.radians(
    1.5
)


initialize_project(
    scene,
)


cube = bpy.data.objects["Cube"]

cube_settings = cube.bvt_object

cube_settings.class_id = 0
cube_settings.class_name = "cube"

register_object(
    cube,
)


camera = scene.camera

original_location = (
    camera.location.copy()
)

original_rotation = (
    camera.rotation_euler.copy()
)


first = generate_dataset(
    scene,
)


assert close3(
    tuple3(camera.location),
    tuple3(original_location),
)

assert close3(
    tuple3(camera.rotation_euler),
    tuple3(original_rotation),
)


assert (
    first["validation_report"]["status"]
    == "PASS"
)


first_manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8",
    )
)


frames = first_manifest["frames"]

assert len(frames) == 3


camera_transforms = []
camera_seeds = []
bboxes = []


for frame in frames:
    placement = (
        frame["randomization"][
            "placement"
        ]
    )

    assert placement["enabled"] is False

    camera_result = (
        frame["randomization"][
            "camera"
        ]
    )

    assert (
        camera_result["enabled"]
        is True
    )

    assert (
        camera_result["version"]
        == "camera-transform-random-v1"
    )

    assert (
        camera_result["camera_name"]
        == camera.name
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "camera",
        camera.name,
    )

    assert (
        camera_result["seed"]
        == expected_seed
    )

    camera_seeds.append(
        camera_result["seed"]
    )

    position_offset = (
        camera_result["offset"][
            "position"
        ]
    )

    rotation_offset = (
        camera_result["offset"][
            "rotation_euler_rad"
        ]
    )

    assert (
        -0.20
        <= position_offset[0]
        <= 0.20
    )

    assert (
        -0.20
        <= position_offset[1]
        <= 0.20
    )

    assert (
        -0.10
        <= position_offset[2]
        <= 0.10
    )

    rotation_limit = math.radians(
        1.5
    )

    for value in rotation_offset:
        assert (
            -rotation_limit - 1e-6
            <= value
            <= rotation_limit + 1e-6
        )

    base = camera_result["base"]
    transform = camera_result["transform"]

    expected_location = tuple(
        base["location"][index]
        + position_offset[index]
        for index in range(3)
    )

    assert close3(
        expected_location,
        tuple(
            transform["location"]
        ),
    )

    expected_rotation = tuple(
        base[
            "rotation_euler_rad"
        ][index]
        + rotation_offset[index]
        for index in range(3)
    )

    assert close3(
        expected_rotation,
        tuple(
            transform[
                "rotation_euler_rad"
            ]
        ),
    )

    camera_transforms.append(
        (
            *transform["location"],
            *transform[
                "rotation_euler_rad"
            ],
        )
    )

    assert len(
        frame["objects"]
    ) == 1

    bboxes.append(
        tuple(
            frame["objects"][0][
                "bbox_yolo"
            ]
        )
    )


assert len(
    set(camera_seeds)
) == 3

assert len(
    set(camera_transforms)
) == 3

assert len(
    set(bboxes)
) == 3


second = generate_dataset(
    scene,
)


assert close3(
    tuple3(camera.location),
    tuple3(original_location),
)

assert close3(
    tuple3(camera.rotation_euler),
    tuple3(original_rotation),
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8",
    )
)


second_transforms = [
    (
        *frame[
            "randomization"
        ]["camera"][
            "transform"
        ]["location"],
        *frame[
            "randomization"
        ]["camera"][
            "transform"
        ][
            "rotation_euler_rad"
        ],
    )
    for frame
    in second_manifest["frames"]
]


second_bboxes = [
    tuple(
        frame["objects"][0][
            "bbox_yolo"
        ]
    )
    for frame
    in second_manifest["frames"]
]


assert (
    camera_transforms
    == second_transforms
)

assert bboxes == second_bboxes


print(
    "BVT_CAMERA_RANDOMIZATION_SMOKE=OK"
)

print(
    "camera_seeds=",
    camera_seeds,
)

print(
    "camera_transforms=",
    camera_transforms,
)

print(
    "bboxes=",
    bboxes,
)

print(
    "camera_restored_location=",
    tuple3(camera.location),
)

print(
    "camera_restored_rotation=",
    tuple3(camera.rotation_euler),
)


bvt.unregister()

shutil.rmtree(
    TMP,
)


print(
    "BVT_CAMERA_RANDOMIZATION_CLEANUP=OK"
)
