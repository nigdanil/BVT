import hashlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    TMP
    / "lighting-randomization.blend"
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


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


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
    "Lighting Randomization Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 3

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False

project.lighting_randomization_enabled = True

project.lighting_energy_variation = 0.40
project.lighting_color_variation = 0.10

project.lighting_position_offset_x = 0.50
project.lighting_position_offset_y = 0.50
project.lighting_position_offset_z = 0.50


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


light = bpy.data.objects["Light"]

light.data.energy = 1000.0

light.data.color = (
    0.8,
    0.7,
    0.6,
)


original_location = (
    light.location.copy()
)

original_energy = float(
    light.data.energy
)

original_color = tuple(
    float(value)
    for value
    in light.data.color
)


first = generate_dataset(
    scene,
)


assert close3(
    tuple3(light.location),
    tuple3(original_location),
)

assert (
    abs(
        float(light.data.energy)
        - original_energy
    )
    <= 1e-6
)

assert close3(
    tuple(light.data.color),
    original_color,
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


lighting_seeds = []
lighting_states = []
bboxes = []


for frame in frames:
    randomization = (
        frame["randomization"]
    )

    assert (
        randomization[
            "placement"
        ]["enabled"]
        is False
    )

    assert (
        randomization[
            "camera"
        ]["enabled"]
        is False
    )

    lighting = (
        randomization["lighting"]
    )

    assert lighting["enabled"] is True

    assert (
        lighting["version"]
        == "lighting-random-v1"
    )

    light_result = next(
        item
        for item
        in lighting["lights"]
        if (
            item["object_name"]
            == light.name
        )
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "lighting",
        light.name,
    )

    assert (
        light_result["seed"]
        == expected_seed
    )

    lighting_seeds.append(
        light_result["seed"]
    )

    offset = (
        light_result[
            "offset"
        ]["position"]
    )

    assert -0.50 <= offset[0] <= 0.50
    assert -0.50 <= offset[1] <= 0.50
    assert -0.50 <= offset[2] <= 0.50

    multiplier = (
        light_result[
            "energy_multiplier"
        ]
    )

    assert 0.60 <= multiplier <= 1.40

    state = (
        light_result["state"]
    )

    assert state["energy"] >= 0.0

    for value in state["color"]:
        assert 0.0 <= value <= 1.0

    for index in range(3):
        color_delta = (
            light_result[
                "offset"
            ]["color"][index]
        )

        assert (
            abs(color_delta)
            <= 0.10 + 1e-6
        )

    lighting_states.append(
        (
            *state["location"],
            state["energy"],
            *state["color"],
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
    set(lighting_seeds)
) == 3

assert len(
    set(lighting_states)
) == 3


# Lighting changes appearance, not geometry.
assert len(
    set(bboxes)
) == 1


first_labels = [
    path.read_text(
        encoding="utf-8"
    )
    for path
    in first["label_paths"]
]


image_hashes = [
    sha256(path)
    for path
    in first["image_paths"]
]


# At least two rendered frames must look different.
assert len(
    set(image_hashes)
) > 1


second = generate_dataset(
    scene,
)


assert close3(
    tuple3(light.location),
    tuple3(original_location),
)

assert (
    abs(
        float(light.data.energy)
        - original_energy
    )
    <= 1e-6
)

assert close3(
    tuple(light.data.color),
    original_color,
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8",
    )
)


second_states = []

for frame in second_manifest["frames"]:
    lighting = (
        frame["randomization"][
            "lighting"
        ]
    )

    light_result = next(
        item
        for item
        in lighting["lights"]
        if (
            item["object_name"]
            == light.name
        )
    )

    state = (
        light_result["state"]
    )

    second_states.append(
        (
            *state["location"],
            state["energy"],
            *state["color"],
        )
    )


second_labels = [
    path.read_text(
        encoding="utf-8"
    )
    for path
    in second["label_paths"]
]


assert (
    lighting_states
    == second_states
)

assert (
    first_labels
    == second_labels
)


print(
    "BVT_LIGHTING_RANDOMIZATION_SMOKE=OK"
)

print(
    "lighting_seeds=",
    lighting_seeds,
)

print(
    "lighting_states=",
    lighting_states,
)

print(
    "unique_image_hashes=",
    len(set(image_hashes)),
)

print(
    "unique_bboxes=",
    len(set(bboxes)),
)

print(
    "light_restored_location=",
    tuple3(light.location),
)

print(
    "light_restored_energy=",
    float(light.data.energy),
)

print(
    "light_restored_color=",
    tuple(light.data.color),
)


bvt.unregister()

shutil.rmtree(
    TMP,
)


print(
    "BVT_LIGHTING_RANDOMIZATION_CLEANUP=OK"
)
