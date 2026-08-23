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
    / "frost-artifact.blend"
)

BASELINE_IMAGE = (
    TMP
    / "frost-baseline.png"
)

FIRST_IMAGE = (
    TMP
    / "frost-first.png"
)

PIXEL_TOLERANCE = 1e-6


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.artifacts.providers.frost import (
    FROST_CRYSTAL_COUNT,
    FROST_MASK_RESOLUTION,
    FROST_ROUGHNESS_DELTA,
)
from bvt.core.seeding import derive_subseed
from bvt.materials import MATERIAL_ROLE_GLASS
from bvt.materials import set_material_role
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


def load_pixels(path):
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
        load_pixels(first_path)
    )

    second_size, second_pixels = (
        load_pixels(second_path)
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
            first - second
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
        "max_error": max_error,
        "changed_components": (
            changed_components
        ),
    }


def temporary_nodes(
    material,
    prefix,
):
    return [
        node
        for node
        in material.node_tree.nodes
        if node.name.startswith(
            prefix
        )
    ]


def temporary_images(
    prefix,
):
    return [
        image
        for image
        in bpy.data.images
        if image.name.startswith(
            prefix
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


def read_manifest(result):
    return json.loads(
        result[
            "manifest_path"
        ].read_text(
            encoding="utf-8"
        )
    )


def assert_clean(
    material,
    roughness_socket,
    base_roughness,
):
    assert abs(
        float(
            roughness_socket.default_value
        )
        - base_roughness
    ) <= 1e-6

    assert (
        roughness_socket.is_linked
        is False
    )

    for prefix in (
        "BVT Fingerprints",
        "BVT Condensation",
        "BVT Frost",
    ):
        assert (
            temporary_nodes(
                material,
                prefix,
            )
            == []
        )

    for prefix in (
        "BVT_Fingerprints_",
        "BVT_Condensation_",
        "BVT_Frost_",
    ):
        assert (
            temporary_images(
                prefix
            )
            == []
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
    "Frost Artifact Smoke"
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
        "BVT_Frost_Glass"
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
    if node.type
    == "BSDF_PRINCIPLED"
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

CONDENSATION_INTENSITY = 1.0

FROST_INTENSITY = 1.0


roughness_socket.default_value = (
    BASE_ROUGHNESS
)


# =========================================================
# Shared artifact configuration.
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

project.artifact_condensation_enabled = True
project.artifact_condensation_probability = 1.0
project.artifact_condensation_intensity = (
    CONDENSATION_INTENSITY
)

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


# =========================================================
# Baseline:
# Reflection + Fingerprints + Condensation.
# Frost disabled.
# =========================================================

project.artifact_frost_enabled = False
project.artifact_dust_enabled = False


baseline = generate_dataset(
    scene
)


assert (
    baseline[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


shutil.copy2(
    baseline[
        "image_path"
    ],
    BASELINE_IMAGE,
)


baseline_manifest = (
    read_manifest(
        baseline
    )
)

baseline_frame = (
    baseline_manifest[
        "frames"
    ][0]
)


baseline_bbox = tuple(
    baseline_frame[
        "objects"
    ][0][
        "bbox_yolo"
    ]
)


baseline_frost = artifact_by_id(
    baseline_frame,
    "frost",
)


assert (
    baseline_frost[
        "enabled"
    ]
    is False
)

assert (
    baseline_frost[
        "applied"
    ]
    is False
)

assert (
    baseline_frost[
        "parameters"
    ]
    == {}
)


assert_clean(
    glass_material,
    roughness_socket,
    BASE_ROUGHNESS,
)


# =========================================================
# Reflection + Fingerprints + Condensation + Frost.
# =========================================================

project.artifact_frost_enabled = True
project.artifact_frost_probability = 1.0
project.artifact_frost_intensity = (
    FROST_INTENSITY
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


shutil.copy2(
    first[
        "image_path"
    ],
    FIRST_IMAGE,
)


assert_clean(
    glass_material,
    roughness_socket,
    BASE_ROUGHNESS,
)


manifest = read_manifest(
    first
)

frame = manifest[
    "frames"
][0]


artifact_ids = [
    item[
        "artifact"
    ]
    for item
    in frame[
        "artifacts"
    ][
        "artifacts"
    ]
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

condensation = artifact_by_id(
    frame,
    "condensation",
)

frost = artifact_by_id(
    frame,
    "frost",
)


assert (
    reflection["applied"]
    is True
)

assert (
    fingerprints["applied"]
    is True
)

assert (
    condensation["applied"]
    is True
)

assert (
    frost["enabled"]
    is True
)

assert (
    frost["applied"]
    is True
)

assert (
    frost["category"]
    == "glass"
)

assert (
    frost["stage"]
    == "pre_render"
)

assert (
    frost[
        "execution_order"
    ]
    == 130
)

assert (
    frost["probability"]
    == 1.0
)

assert (
    frost["intensity"]
    == FROST_INTENSITY
)

assert (
    frost["options"]
    == {}
)


expected_seed = derive_subseed(
    frame[
        "frame_seed"
    ],
    "artifact",
    "frost",
)


assert (
    frost["seed"]
    == expected_seed
)


assert (
    frost[
        "affected_materials"
    ]
    == [
        "BVT_Frost_Glass"
    ]
)


parameters = frost[
    "parameters"
]


assert (
    parameters[
        "target_role"
    ]
    == "GLASS"
)

assert (
    parameters[
        "mask_resolution"
    ]
    == FROST_MASK_RESOLUTION
)

assert abs(
    parameters[
        "roughness_delta"
    ]
    - FROST_ROUGHNESS_DELTA
) <= 1e-12

assert abs(
    parameters[
        "effective_strength"
    ]
    - FROST_INTENSITY
) <= 1e-12

assert (
    parameters[
        "crystal_count"
    ]
    == FROST_CRYSTAL_COUNT
)

assert (
    0.0
    < parameters[
        "mean_coverage"
    ]
    < 1.0
)

assert (
    0.0
    < parameters[
        "mean_mask_value"
    ]
    < 1.0
)


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


change = material_changes[
    0
]


assert (
    change[
        "material"
    ]
    == "BVT_Frost_Glass"
)


expected_material_seed = derive_subseed(
    expected_seed,
    "artifact-frost",
    "BVT_Frost_Glass",
)


assert (
    change[
        "material_seed"
    ]
    == expected_material_seed
)

assert (
    change[
        "crystal_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "frost-mask",
        "crystals",
    )
)

assert (
    change[
        "texture_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "frost-mask",
        "texture",
    )
)


assert (
    0.0
    < change[
        "coverage"
    ]
    < 1.0
)

assert (
    0.0
    < change[
        "mean_mask_value"
    ]
    < 1.0
)


node_changes = change[
    "nodes"
]

assert (
    len(
        node_changes
    )
    == 1
)


node_change = node_changes[
    0
]


assert (
    node_change[
        "input_mode"
    ]
    == "condensation"
)

assert (
    node_change[
        "upstream_node"
    ].startswith(
        "BVT Condensation Roughness Mix"
    )
)

assert abs(
    node_change[
        "base_roughness"
    ]
    - BASE_ROUGHNESS
) <= 1e-6


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

assert abs(
    node_change[
        "roughness_delta"
    ]
    - FROST_ROUGHNESS_DELTA
) <= 1e-12


first_bbox = tuple(
    frame[
        "objects"
    ][0][
        "bbox_yolo"
    ]
)


assert (
    first_bbox
    == baseline_bbox
)


# =========================================================
# Frost must produce a real RGB difference.
# =========================================================

frost_vs_baseline = compare_images(
    BASELINE_IMAGE,
    FIRST_IMAGE,
)


assert (
    frost_vs_baseline[
        "max_error"
    ]
    > PIXEL_TOLERANCE
)

assert (
    frost_vs_baseline[
        "changed_components"
    ]
    > 0
)


# =========================================================
# Same seed / same configuration:
# same manifest artifact record + same pixels.
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


assert_clean(
    glass_material,
    roughness_socket,
    BASE_ROUGHNESS,
)


second_manifest = (
    read_manifest(
        second
    )
)

second_frame = (
    second_manifest[
        "frames"
    ][0]
)


second_frost = artifact_by_id(
    second_frame,
    "frost",
)


assert (
    second_frost
    == frost
)


repeat_delta = compare_images(
    FIRST_IMAGE,
    second[
        "image_path"
    ],
)


assert (
    repeat_delta[
        "max_error"
    ]
    <= PIXEL_TOLERANCE
)


second_bbox = tuple(
    second_frame[
        "objects"
    ][0][
        "bbox_yolo"
    ]
)


assert (
    second_bbox
    == first_bbox
)


assert (
    baseline[
        "label_path"
    ].read_text(
        encoding="utf-8"
    )
    == second[
        "label_path"
    ].read_text(
        encoding="utf-8"
    )
)


print(
    "BVT_FROST_ARTIFACT_SMOKE=OK"
)

print(
    "artifact_order=",
    artifact_ids,
)

print(
    "frost_seed=",
    expected_seed,
)

print(
    "material_seed=",
    expected_material_seed,
)

print(
    "reflection_roughness=",
    expected_reflection_roughness,
)

print(
    "roughness_delta=",
    FROST_ROUGHNESS_DELTA,
)

print(
    "effective_strength=",
    FROST_INTENSITY,
)

print(
    "coverage=",
    change[
        "coverage"
    ],
)

print(
    "mean_mask_value=",
    change[
        "mean_mask_value"
    ],
)

print(
    "input_mode=",
    node_change[
        "input_mode"
    ],
)

print(
    "frost_vs_baseline_rmse=",
    frost_vs_baseline[
        "rmse"
    ],
)

print(
    "frost_vs_baseline_max_error=",
    frost_vs_baseline[
        "max_error"
    ],
)

print(
    "changed_components=",
    frost_vs_baseline[
        "changed_components"
    ],
)

print(
    "repeat_max_error=",
    repeat_delta[
        "max_error"
    ],
)

print(
    "bbox_unchanged=",
    (
        first_bbox
        == baseline_bbox
        == second_bbox
    ),
)

print(
    "material_restored=True"
)

print(
    "temporary_fingerprint_nodes_after_reset=",
    len(
        temporary_nodes(
            glass_material,
            "BVT Fingerprints",
        )
    ),
)

print(
    "temporary_condensation_nodes_after_reset=",
    len(
        temporary_nodes(
            glass_material,
            "BVT Condensation",
        )
    ),
)

print(
    "temporary_frost_nodes_after_reset=",
    len(
        temporary_nodes(
            glass_material,
            "BVT Frost",
        )
    ),
)

print(
    "temporary_frost_images_after_reset=",
    len(
        temporary_images(
            "BVT_Frost_"
        )
    ),
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_FROST_ARTIFACT_CLEANUP=OK"
)
