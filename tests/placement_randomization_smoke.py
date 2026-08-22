import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    TMP
    / "placement-randomization.blend"
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


def tuple3(vector):
    return (
        float(vector[0]),
        float(vector[1]),
        float(vector[2]),
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
    "Placement Randomization Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 3

project.placement_randomization_enabled = True

project.placement_offset_x = 0.10
project.placement_offset_y = 0.10
project.placement_offset_z = 0.00


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


original_location = (
    cube.location.copy()
)


first = generate_dataset(
    scene,
)


# Generation must never leave the Blender scene mutated.
assert tuple3(cube.location) == tuple3(
    original_location
)


assert (
    first["validation_report"]["status"]
    == "PASS"
)


manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8",
    )
)


frames = manifest["frames"]

assert len(frames) == 3


placements = []

bbox_values = []


for frame in frames:
    placement = (
        frame["randomization"][
            "placement"
        ]
    )

    assert placement["enabled"] is True

    assert (
        placement["version"]
        == "placement-random-v1"
    )

    assert placement["space"] == "local"

    assert len(
        placement["objects"]
    ) == 1

    placed_object = (
        placement["objects"][0]
    )

    assert (
        placed_object["instance_id"]
        == cube_settings.instance_id
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "placement",
        cube_settings.instance_id,
    )

    assert (
        placed_object["seed"]
        == expected_seed
    )

    offset = (
        placed_object["offset"]
    )

    assert -0.10 <= offset[0] <= 0.10
    assert -0.10 <= offset[1] <= 0.10
    assert offset[2] == 0.0

    base_location = (
        placed_object[
            "base_location"
        ]
    )

    location = (
        placed_object[
            "location"
        ]
    )

    for index in range(3):
        assert abs(
            (
                base_location[index]
                + offset[index]
            )
            - location[index]
        ) < 1e-9

    placements.append(
        tuple(location)
    )

    assert len(
        frame["objects"]
    ) == 1

    bbox_values.append(
        tuple(
            frame["objects"][0][
                "bbox_yolo"
            ]
        )
    )


# Three deterministic seeds should create different placements.
assert len(set(placements)) == 3

# The moved cube must also produce different annotations.
assert len(set(bbox_values)) == 3


first_placements = list(
    placements
)

first_bboxes = list(
    bbox_values
)


second = generate_dataset(
    scene,
)


assert tuple3(cube.location) == tuple3(
    original_location
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8",
    )
)


second_placements = [
    tuple(
        frame["randomization"][
            "placement"
        ]["objects"][0]["location"]
    )
    for frame in second_manifest["frames"]
]


second_bboxes = [
    tuple(
        frame["objects"][0][
            "bbox_yolo"
        ]
    )
    for frame in second_manifest["frames"]
]


# Same seed must reproduce transforms and annotations.
assert (
    first_placements
    == second_placements
)

assert first_bboxes == second_bboxes


print(
    "BVT_PLACEMENT_RANDOMIZATION_SMOKE=OK"
)

print(
    "placements=",
    first_placements,
)

print(
    "bboxes=",
    first_bboxes,
)

print(
    "scene_restored=",
    tuple3(cube.location),
)


bvt.unregister()

shutil.rmtree(
    TMP,
)


print(
    "BVT_PLACEMENT_RANDOMIZATION_CLEANUP=OK"
)
