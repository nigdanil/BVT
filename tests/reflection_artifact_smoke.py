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
    / "reflection-artifact.blend"
)

CLEAN_IMAGE = (
    TMP
    / "reflection-clean.png"
)

FIRST_IMAGE = (
    TMP
    / "reflection-first.png"
)

PIXEL_TOLERANCE = 1e-6


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.seeding import derive_subseed
from bvt.materials import MATERIAL_ROLE_GLASS
from bvt.materials import set_material_role
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


def load_pixels(
    path,
):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        return (
            tuple(image.size),
            list(image.pixels[:]),
        )

    finally:
        bpy.data.images.remove(
            image
        )


def compare_images(
    first_path,
    second_path,
):
    first_size, first_pixels = (
        load_pixels(
            first_path
        )
    )

    second_size, second_pixels = (
        load_pixels(
            second_path
        )
    )

    assert first_size == second_size
    assert len(first_pixels) == len(
        second_pixels
    )

    squared_error = 0.0
    max_error = 0.0

    for first, second in zip(
        first_pixels,
        second_pixels,
    ):
        difference = abs(
            first - second
        )

        squared_error += (
            difference
            * difference
        )

        max_error = max(
            max_error,
            difference,
        )

    return {
        "rmse": math.sqrt(
            squared_error
            / len(first_pixels)
        ),
        "max_error": max_error,
    }


if TMP.exists():
    shutil.rmtree(
        TMP
    )

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


project = scene.bvt_project

project.project_name = (
    "Reflection Artifact Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 1

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False


initialize_project(
    scene
)


cube = bpy.data.objects[
    "Cube"
]

cube.bvt_object.class_id = 0
cube.bvt_object.class_name = "cube"

register_object(
    cube
)


glass_material = (
    bpy.data.materials.new(
        "BVT_Reflection_Glass"
    )
)

glass_material.use_nodes = True

set_material_role(
    glass_material,
    MATERIAL_ROLE_GLASS,
)


cube.data.materials.clear()

cube.data.materials.append(
    glass_material
)


principled = next(
    node
    for node
    in glass_material.node_tree.nodes
    if node.type == "BSDF_PRINCIPLED"
)

roughness_socket = (
    principled.inputs[
        "Roughness"
    ]
)

BASE_ROUGHNESS = 0.80
MIN_ROUGHNESS = 0.02
INTENSITY = 0.75

roughness_socket.default_value = (
    BASE_ROUGHNESS
)


project.artifact_engine_enabled = False


clean = generate_dataset(
    scene
)

assert (
    clean["validation_report"]["status"]
    == "PASS"
)


shutil.copy2(
    clean["image_path"],
    CLEAN_IMAGE,
)


clean_manifest = json.loads(
    clean["manifest_path"].read_text(
        encoding="utf-8"
    )
)

clean_bbox = tuple(
    clean_manifest[
        "frames"
    ][0]["objects"][0][
        "bbox_yolo"
    ]
)


assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7


project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = False

project.artifact_reflection_enabled = True
project.artifact_reflection_probability = 1.0
project.artifact_reflection_intensity = (
    INTENSITY
)
project.artifact_reflection_min_roughness = (
    MIN_ROUGHNESS
)

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


first = generate_dataset(
    scene
)

assert (
    first["validation_report"]["status"]
    == "PASS"
)


# Template material must already be restored.
assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7


shutil.copy2(
    first["image_path"],
    FIRST_IMAGE,
)


manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8"
    )
)

frame = manifest[
    "frames"
][0]

artifact_list = (
    frame["artifacts"][
        "artifacts"
    ]
)

artifact_ids = [
    item["artifact"]
    for item in artifact_list
]

assert artifact_ids == [
    "over_exposure",
    "reflection",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


artifacts = {
    item["artifact"]: item
    for item in artifact_list
}


reflection = artifacts[
    "reflection"
]

assert reflection["enabled"] is True
assert reflection["applied"] is True

assert (
    reflection["stage"]
    == "pre_render"
)

assert (
    reflection["category"]
    == "glass"
)

assert (
    reflection["execution_order"]
    == 100
)

assert (
    reflection["probability"]
    == 1.0
)

assert abs(
    reflection["intensity"]
    - INTENSITY
) <= 1e-7

assert abs(
    reflection["options"][
        "min_roughness"
    ]
    - MIN_ROUGHNESS
) <= 1e-7


expected_seed = derive_subseed(
    frame["frame_seed"],
    "artifact",
    "reflection",
)

assert (
    reflection["seed"]
    == expected_seed
)


assert (
    reflection[
        "affected_materials"
    ]
    == [
        "BVT_Reflection_Glass"
    ]
)


parameters = (
    reflection["parameters"]
)

assert (
    parameters[
        "target_role"
    ]
    == "GLASS"
)

assert (
    parameters[
        "supported_node_count"
    ]
    == 1
)


changes = (
    parameters[
        "material_changes"
    ]
)

assert len(changes) == 1

change = changes[0]

assert (
    change["material"]
    == "BVT_Reflection_Glass"
)

assert abs(
    change["base_roughness"]
    - BASE_ROUGHNESS
) <= 1e-7

assert abs(
    change["target_roughness"]
    - MIN_ROUGHNESS
) <= 1e-7


expected_effective = (
    BASE_ROUGHNESS
    + (
        MIN_ROUGHNESS
        - BASE_ROUGHNESS
    )
    * INTENSITY
)

assert abs(
    change[
        "effective_roughness"
    ]
    - expected_effective
) <= 1e-7


first_bbox = tuple(
    frame["objects"][0][
        "bbox_yolo"
    ]
)

assert first_bbox == clean_bbox


reflection_vs_clean = (
    compare_images(
        CLEAN_IMAGE,
        FIRST_IMAGE,
    )
)

assert (
    reflection_vs_clean[
        "max_error"
    ]
    > PIXEL_TOLERANCE
)


second = generate_dataset(
    scene
)

assert (
    second["validation_report"]["status"]
    == "PASS"
)


assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8"
    )
)


assert (
    second_manifest[
        "frames"
    ][0]["artifacts"]
    == frame["artifacts"]
)


repeat = compare_images(
    FIRST_IMAGE,
    second["image_path"],
)

assert (
    repeat["max_error"]
    <= PIXEL_TOLERANCE
)


second_bbox = tuple(
    second_manifest[
        "frames"
    ][0]["objects"][0][
        "bbox_yolo"
    ]
)

assert second_bbox == clean_bbox


print(
    "BVT_REFLECTION_ARTIFACT_SMOKE=OK"
)

print(
    "reflection_seed=",
    expected_seed,
)

print(
    "base_roughness=",
    BASE_ROUGHNESS,
)

print(
    "effective_roughness=",
    expected_effective,
)

print(
    "affected_materials=",
    reflection[
        "affected_materials"
    ],
)

print(
    "reflection_vs_clean_rmse=",
    reflection_vs_clean[
        "rmse"
    ],
)

print(
    "reflection_vs_clean_max_error=",
    reflection_vs_clean[
        "max_error"
    ],
)

print(
    "repeat_max_error=",
    repeat[
        "max_error"
    ],
)

print(
    "bbox_unchanged=",
    second_bbox == clean_bbox,
)

print(
    "material_restored=True"
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_REFLECTION_ARTIFACT_CLEANUP=OK"
)
