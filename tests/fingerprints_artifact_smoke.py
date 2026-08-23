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
    / "fingerprints-artifact.blend"
)

REFLECTION_ONLY_IMAGE = (
    TMP
    / "fingerprints-reflection-only.png"
)

FIRST_IMAGE = (
    TMP
    / "fingerprints-first.png"
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

    assert (
        first_size
        == second_size
    )

    assert (
        len(first_pixels)
        == len(second_pixels)
    )

    squared_error = 0.0
    max_error = 0.0
    changed_components = 0

    for first, second in zip(
        first_pixels,
        second_pixels,
    ):
        difference = abs(
            first
            - second
        )

        if (
            difference
            > PIXEL_TOLERANCE
        ):
            changed_components += 1

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
        "max_error": (
            max_error
        ),
        "changed_components": (
            changed_components
        ),
    }


def temporary_nodes(
    material,
):
    return [
        node
        for node
        in material.node_tree.nodes
        if node.name.startswith(
            "BVT Fingerprints"
        )
    ]


def temporary_images():
    return [
        image
        for image
        in bpy.data.images
        if image.name.startswith(
            "BVT_Fingerprints_"
        )
    ]


def artifact_by_id(
    frame,
    artifact_id,
):
    return next(
        item
        for item
        in frame[
            "artifacts"
        ][
            "artifacts"
        ]
        if (
            item["artifact"]
            == artifact_id
        )
    )


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
    "Fingerprints Artifact Smoke"
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
cube.bvt_object.class_name = (
    "cube"
)

register_object(
    cube
)


glass_material = (
    bpy.data.materials.new(
        "BVT_Fingerprints_Glass"
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
    if (
        node.type
        == "BSDF_PRINCIPLED"
    )
)

roughness_socket = (
    principled.inputs[
        "Roughness"
    ]
)


BASE_ROUGHNESS = 0.80

REFLECTION_MIN_ROUGHNESS = 0.02
REFLECTION_INTENSITY = 0.75

FINGERPRINT_INTENSITY = 1.0
FINGERPRINT_COUNT = 4
FINGERPRINT_TRANSPARENCY = 0.0
FINGERPRINT_SIZE = 0.45


roughness_socket.default_value = (
    BASE_ROUGHNESS
)


# =========================================================
# Baseline:
# Reflection enabled, Fingerprints disabled.
# This isolates the visual delta caused only by fingerprints.
# =========================================================

project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = False

project.artifact_reflection_enabled = True
project.artifact_reflection_probability = 1.0
project.artifact_reflection_intensity = (
    REFLECTION_INTENSITY
)
project.artifact_reflection_min_roughness = (
    REFLECTION_MIN_ROUGHNESS
)

project.artifact_fingerprints_enabled = False
project.artifact_condensation_enabled = False
project.artifact_frost_enabled = False
project.artifact_dust_enabled = False

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


reflection_only = generate_dataset(
    scene
)

assert (
    reflection_only[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


shutil.copy2(
    reflection_only[
        "image_path"
    ],
    REFLECTION_ONLY_IMAGE,
)


reflection_only_manifest = (
    json.loads(
        reflection_only[
            "manifest_path"
        ].read_text(
            encoding="utf-8"
        )
    )
)

reflection_only_frame = (
    reflection_only_manifest[
        "frames"
    ][0]
)

reflection_only_bbox = tuple(
    reflection_only_frame[
        "objects"
    ][0][
        "bbox_yolo"
    ]
)


# Material template must already be clean.
assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7

assert (
    temporary_nodes(
        glass_material
    )
    == []
)

assert (
    temporary_images()
    == []
)


# =========================================================
# Reflection + Fingerprints
# =========================================================

project.artifact_fingerprints_enabled = True
project.artifact_fingerprints_probability = 1.0
project.artifact_fingerprints_intensity = (
    FINGERPRINT_INTENSITY
)
project.artifact_fingerprints_count = (
    FINGERPRINT_COUNT
)
project.artifact_fingerprints_transparency = (
    FINGERPRINT_TRANSPARENCY
)
project.artifact_fingerprints_size = (
    FINGERPRINT_SIZE
)


first = generate_dataset(
    scene
)

assert (
    first[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


# Reset must already have happened.
assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7

assert (
    temporary_nodes(
        glass_material
    )
    == []
)

assert (
    temporary_images()
    == []
)


shutil.copy2(
    first[
        "image_path"
    ],
    FIRST_IMAGE,
)


manifest = json.loads(
    first[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)

frame = manifest[
    "frames"
][0]


artifact_list = (
    frame[
        "artifacts"
    ][
        "artifacts"
    ]
)

artifact_ids = [
    item["artifact"]
    for item
    in artifact_list
]

assert artifact_ids == [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "frost",
    "dust",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


reflection = artifact_by_id(
    frame,
    "reflection",
)

fingerprints = artifact_by_id(
    frame,
    "fingerprints",
)


assert (
    reflection["applied"]
    is True
)

assert (
    fingerprints["enabled"]
    is True
)

assert (
    fingerprints["applied"]
    is True
)

assert (
    fingerprints["stage"]
    == "pre_render"
)

assert (
    fingerprints["category"]
    == "glass"
)

assert (
    fingerprints[
        "execution_order"
    ]
    == 110
)


expected_seed = derive_subseed(
    frame["frame_seed"],
    "artifact",
    "fingerprints",
)

assert (
    fingerprints["seed"]
    == expected_seed
)


assert (
    fingerprints[
        "affected_materials"
    ]
    == [
        "BVT_Fingerprints_Glass"
    ]
)


assert (
    fingerprints[
        "options"
    ][
        "print_count"
    ]
    == FINGERPRINT_COUNT
)

assert abs(
    fingerprints[
        "options"
    ][
        "transparency"
    ]
    - FINGERPRINT_TRANSPARENCY
) <= 1e-7

assert abs(
    fingerprints[
        "options"
    ][
        "size"
    ]
    - FINGERPRINT_SIZE
) <= 1e-7


parameters = (
    fingerprints[
        "parameters"
    ]
)

assert (
    parameters[
        "target_role"
    ]
    == "GLASS"
)

assert (
    parameters[
        "print_count"
    ]
    == FINGERPRINT_COUNT
)

assert (
    parameters[
        "mask_resolution"
    ]
    == 256
)

assert (
    parameters[
        "mean_coverage"
    ]
    > 0.0
)

assert (
    parameters[
        "mean_coverage"
    ]
    < 1.0
)


expected_strength = (
    FINGERPRINT_INTENSITY
    * (
        1.0
        - FINGERPRINT_TRANSPARENCY
    )
)

assert abs(
    parameters[
        "effective_strength"
    ]
    - expected_strength
) <= 1e-7


material_changes = (
    parameters[
        "material_changes"
    ]
)

assert (
    len(
        material_changes
    )
    == 1
)

change = (
    material_changes[0]
)

assert (
    change["material"]
    == "BVT_Fingerprints_Glass"
)

assert (
    change["coverage"]
    > 0.0
)

assert (
    len(
        change[
            "fingerprints"
        ]
    )
    == FINGERPRINT_COUNT
)

assert (
    len(
        change[
            "nodes"
        ]
    )
    == 1
)


node_change = (
    change[
        "nodes"
    ][0]
)


expected_reflection_roughness = (
    BASE_ROUGHNESS
    + (
        REFLECTION_MIN_ROUGHNESS
        - BASE_ROUGHNESS
    )
    * REFLECTION_INTENSITY
)

assert abs(
    node_change[
        "input_roughness"
    ]
    - expected_reflection_roughness
) <= 1e-6


expected_target_roughness = min(
    1.0,
    (
        expected_reflection_roughness
        + 0.45
    ),
)

assert abs(
    node_change[
        "target_roughness"
    ]
    - expected_target_roughness
) <= 1e-6


first_bbox = tuple(
    frame[
        "objects"
    ][0][
        "bbox_yolo"
    ]
)

assert (
    first_bbox
    == reflection_only_bbox
)


fingerprints_vs_reflection = (
    compare_images(
        REFLECTION_ONLY_IMAGE,
        FIRST_IMAGE,
    )
)


assert (
    fingerprints_vs_reflection[
        "max_error"
    ]
    > PIXEL_TOLERANCE
)

assert (
    fingerprints_vs_reflection[
        "changed_components"
    ]
    > 0
)


# =========================================================
# Same seed/config -> same manifest + same rendered pixels
# =========================================================

second = generate_dataset(
    scene
)

assert (
    second[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


assert abs(
    float(
        roughness_socket.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-7

assert (
    temporary_nodes(
        glass_material
    )
    == []
)

assert (
    temporary_images()
    == []
)


second_manifest = json.loads(
    second[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


assert (
    second_manifest[
        "frames"
    ][0][
        "artifacts"
    ]
    == frame[
        "artifacts"
    ]
)


repeat = compare_images(
    FIRST_IMAGE,
    second[
        "image_path"
    ],
)


assert (
    repeat[
        "max_error"
    ]
    <= PIXEL_TOLERANCE
)


second_bbox = tuple(
    second_manifest[
        "frames"
    ][0][
        "objects"
    ][0][
        "bbox_yolo"
    ]
)

assert (
    second_bbox
    == reflection_only_bbox
)


print(
    "BVT_FINGERPRINTS_ARTIFACT_SMOKE=OK"
)

print(
    "artifact_order=",
    artifact_ids,
)

print(
    "fingerprint_seed=",
    expected_seed,
)

print(
    "reflection_input_roughness=",
    expected_reflection_roughness,
)

print(
    "fingerprint_target_roughness=",
    expected_target_roughness,
)

print(
    "effective_strength=",
    expected_strength,
)

print(
    "coverage=",
    change["coverage"],
)

print(
    "fingerprints_vs_reflection_rmse=",
    fingerprints_vs_reflection[
        "rmse"
    ],
)

print(
    "fingerprints_vs_reflection_max_error=",
    fingerprints_vs_reflection[
        "max_error"
    ],
)

print(
    "changed_components=",
    fingerprints_vs_reflection[
        "changed_components"
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
    (
        second_bbox
        == reflection_only_bbox
    ),
)

print(
    "material_restored=True"
)

print(
    "temporary_nodes_after_reset=",
    len(
        temporary_nodes(
            glass_material
        )
    ),
)

print(
    "temporary_images_after_reset=",
    len(
        temporary_images()
    ),
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_FINGERPRINTS_ARTIFACT_CLEANUP=OK"
)
