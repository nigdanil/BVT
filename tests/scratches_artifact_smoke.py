import json
import math
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = TMP / "scratches-artifact.blend"
BASELINE_IMAGE = TMP / "scratches-baseline.png"
FIRST_IMAGE = TMP / "scratches-first.png"

PIXEL_TOLERANCE = 1e-6
BASE_ROUGHNESS = 0.80


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.artifacts.providers.scratches import (
    SCRATCHES_ROUGHNESS_TARGET,
)
from bvt.artifacts.providers.scratches_mask import (
    SCRATCHES_COUNT,
    SCRATCHES_MASK_RESOLUTION,
)
from bvt.core.seeding import derive_subseed
from bvt.materials import (
    MATERIAL_ROLE_GLASS,
    set_material_role,
)
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


def load_pixels(path):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        return (
            tuple(
                image.size
            ),
            list(
                image.pixels[:]
            ),
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

    assert len(
        first_pixels
    ) == len(
        second_pixels
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
            / len(
                first_pixels
            )
        ),
        "max_error": (
            max_error
        ),
        "changed_components": (
            changed_components
        ),
    }


def read_manifest(result):
    return json.loads(
        result[
            "manifest_path"
        ].read_text(
            encoding="utf-8"
        )
    )


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
        if item[
            "artifact"
        ] == artifact_id
    )


def nodes_with_prefix(
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


def images_with_prefix(
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


def assert_clean(
    material,
    roughness,
    normal,
    normal_was_linked,
):
    assert not roughness.is_linked

    assert abs(
        float(
            roughness.default_value
        )
        - BASE_ROUGHNESS
    ) <= 1e-6

    assert (
        normal.is_linked
        == normal_was_linked
    )

    for prefix in (
        "BVT Fingerprints",
        "BVT Condensation",
        "BVT Frost",
        "BVT Dust",
        "BVT Water Drops",
        "BVT Scratches",
    ):
        assert not nodes_with_prefix(
            material,
            prefix,
        )

    for prefix in (
        "BVT_Fingerprints_",
        "BVT_Condensation_",
        "BVT_Frost_",
        "BVT_Dust_",
        "BVT_Water_Drops_",
        "BVT_Scratches_",
    ):
        assert not images_with_prefix(
            prefix
        )


# =========================================================
# Workspace
# =========================================================

if TMP.exists():
    shutil.rmtree(
        TMP
    )

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# Scene
# =========================================================

bvt.register()

scene = bpy.context.scene

bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    ),
)

project = scene.bvt_project

project.project_name = (
    "Scratches Artifact Smoke"
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


# =========================================================
# Annotated GLASS cube
# =========================================================

cube = bpy.data.objects[
    "Cube"
]

cube.bvt_object.class_id = 0
cube.bvt_object.class_name = "cube"

register_object(
    cube
)

material = bpy.data.materials.new(
    "BVT_Scratches_Glass"
)

material.use_nodes = True

set_material_role(
    material,
    MATERIAL_ROLE_GLASS,
)

cube.data.materials.clear()

cube.data.materials.append(
    material
)

principled = next(
    node
    for node
    in material.node_tree.nodes
    if node.type
    == "BSDF_PRINCIPLED"
)

roughness = principled.inputs[
    "Roughness"
]

normal = principled.inputs[
    "Normal"
]

roughness.default_value = (
    BASE_ROUGHNESS
)

normal_was_linked = (
    normal.is_linked
)


# =========================================================
# Existing full GLASS chain before Scratches:
#
# Reflection
# -> Fingerprints
# -> Condensation
# -> Frost
# -> Dust
# -> Water Drops
# -> Scratches
# =========================================================

project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = False

project.artifact_reflection_enabled = True
project.artifact_reflection_probability = 1.0
project.artifact_reflection_intensity = 0.75
project.artifact_reflection_min_roughness = 0.02

project.artifact_fingerprints_enabled = True
project.artifact_fingerprints_probability = 1.0
project.artifact_fingerprints_intensity = 1.0
project.artifact_fingerprints_count = 4
project.artifact_fingerprints_transparency = 0.0
project.artifact_fingerprints_size = 0.45

project.artifact_condensation_enabled = True
project.artifact_condensation_probability = 1.0
project.artifact_condensation_intensity = 1.0

project.artifact_frost_enabled = True
project.artifact_frost_probability = 1.0
project.artifact_frost_intensity = 1.0

project.artifact_dust_enabled = True
project.artifact_dust_probability = 1.0
project.artifact_dust_intensity = 1.0

project.artifact_water_drops_enabled = True
project.artifact_water_drops_probability = 1.0
project.artifact_water_drops_intensity = 1.0

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


# =========================================================
# Baseline:
# full chain through Water Drops, Scratches OFF.
# =========================================================

project.artifact_scratches_enabled = False

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

baseline_label = (
    baseline[
        "label_path"
    ].read_text(
        encoding="utf-8"
    )
)

baseline_manifest = read_manifest(
    baseline
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

baseline_scratches = artifact_by_id(
    baseline_frame,
    "scratches",
)

assert (
    baseline_scratches[
        "enabled"
    ]
    is False
)

assert (
    baseline_scratches[
        "applied"
    ]
    is False
)

assert (
    baseline_scratches[
        "parameters"
    ]
    == {}
)

baseline_water = artifact_by_id(
    baseline_frame,
    "water_drops",
)

assert (
    baseline_water[
        "applied"
    ]
    is True
)

assert_clean(
    material,
    roughness,
    normal,
    normal_was_linked,
)


# =========================================================
# Scratches ON
# =========================================================

project.artifact_scratches_enabled = True
project.artifact_scratches_probability = 1.0
project.artifact_scratches_intensity = 1.0

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

first_label = (
    first[
        "label_path"
    ].read_text(
        encoding="utf-8"
    )
)

assert_clean(
    material,
    roughness,
    normal,
    normal_was_linked,
)


manifest = read_manifest(
    first
)

frame = manifest[
    "frames"
][0]


artifact_order = [
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


EXPECTED_ORDER = [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "frost",
    "dust",
    "water_drops",
    "scratches",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


assert (
    artifact_order
    == EXPECTED_ORDER
)


scratches = artifact_by_id(
    frame,
    "scratches",
)


assert (
    scratches[
        "enabled"
    ]
    is True
)

assert (
    scratches[
        "applied"
    ]
    is True
)

assert (
    scratches[
        "category"
    ]
    == "glass"
)

assert (
    scratches[
        "stage"
    ]
    == "pre_render"
)

assert (
    scratches[
        "execution_order"
    ]
    == 160
)

assert (
    scratches[
        "probability"
    ]
    == 1.0
)

assert (
    scratches[
        "intensity"
    ]
    == 1.0
)

assert (
    scratches[
        "options"
    ]
    == {}
)


# =========================================================
# Upstream artifact must be unaffected by enabling
# Scratches because seeds are artifact-independent.
# =========================================================

first_water = artifact_by_id(
    frame,
    "water_drops",
)

assert (
    first_water
    == baseline_water
)


# =========================================================
# Seeds + metadata
# =========================================================

expected_seed = derive_subseed(
    frame[
        "frame_seed"
    ],
    "artifact",
    "scratches",
)

assert (
    scratches[
        "seed"
    ]
    == expected_seed
)


assert (
    scratches[
        "affected_materials"
    ]
    == [
        "BVT_Scratches_Glass"
    ]
)


parameters = scratches[
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
    == SCRATCHES_MASK_RESOLUTION
)

assert (
    parameters[
        "scratch_count"
    ]
    == SCRATCHES_COUNT
)

assert abs(
    parameters[
        "roughness_target"
    ]
    - SCRATCHES_ROUGHNESS_TARGET
) <= 1e-12

assert abs(
    parameters[
        "effective_strength"
    ]
    - 1.0
) <= 1e-12


changes = parameters[
    "material_changes"
]

assert len(
    changes
) == 1

change = changes[0]


expected_material_seed = (
    derive_subseed(
        expected_seed,
        "artifact-scratches",
        "BVT_Scratches_Glass",
    )
)

assert (
    change[
        "material_seed"
    ]
    == expected_material_seed
)


assert (
    change[
        "layout_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "scratches-mask",
        "layout",
    )
)

assert (
    change[
        "shape_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "scratches-mask",
        "shape",
    )
)


assert (
    change[
        "scratch_count"
    ]
    == SCRATCHES_COUNT
)


assert (
    0.0
    < change[
        "coverage"
    ]
    < 0.10
)

assert (
    0.0
    < change[
        "mean_mask_value"
    ]
    < 0.10
)


assert abs(
    parameters[
        "mean_coverage"
    ]
    - change[
        "coverage"
    ]
) <= 1e-12

assert abs(
    parameters[
        "mean_mask_value"
    ]
    - change[
        "mean_mask_value"
    ]
) <= 1e-12


node_changes = change[
    "nodes"
]

assert len(
    node_changes
) == 1

node_change = node_changes[
    0
]


assert (
    node_change[
        "input_mode"
    ]
    == "water_drops"
)

assert (
    node_change[
        "upstream_node"
    ].startswith(
        "BVT Water Drops Roughness Mix"
    )
)

assert abs(
    node_change[
        "roughness_target"
    ]
    - SCRATCHES_ROUGHNESS_TARGET
) <= 1e-12


# =========================================================
# Geometry / annotation / Normal unchanged
# =========================================================

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


assert (
    first_label
    == baseline_label
)


assert (
    normal.is_linked
    == normal_was_linked
)


# =========================================================
# Real RGB effect
# =========================================================

scratches_vs_baseline = (
    compare_images(
        BASELINE_IMAGE,
        FIRST_IMAGE,
    )
)


assert (
    scratches_vs_baseline[
        "max_error"
    ]
    > PIXEL_TOLERANCE
)

assert (
    scratches_vs_baseline[
        "changed_components"
    ]
    > 0
)


# =========================================================
# Same seed/config -> same manifest record + RGB + label
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
    material,
    roughness,
    normal,
    normal_was_linked,
)


second_manifest = read_manifest(
    second
)

second_frame = (
    second_manifest[
        "frames"
    ][0]
)

second_scratches = artifact_by_id(
    second_frame,
    "scratches",
)


assert (
    second_scratches
    == scratches
)


second_label = (
    second[
        "label_path"
    ].read_text(
        encoding="utf-8"
    )
)

assert (
    second_label
    == first_label
    == baseline_label
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

assert (
    repeat[
        "changed_components"
    ]
    == 0
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
    == baseline_bbox
)


# =========================================================
# Final cleanup
# =========================================================

temporary_scratches_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Scratches",
    )
)

temporary_scratches_images = len(
    images_with_prefix(
        "BVT_Scratches_"
    )
)


assert (
    temporary_scratches_nodes
    == 0
)

assert (
    temporary_scratches_images
    == 0
)


print(
    "BVT_SCRATCHES_ARTIFACT_SMOKE=OK"
)

print(
    "artifact_order=",
    artifact_order,
)

print(
    "scratches_seed=",
    scratches[
        "seed"
    ],
)

print(
    "material_seed=",
    change[
        "material_seed"
    ],
)

print(
    "layout_seed=",
    change[
        "layout_seed"
    ],
)

print(
    "shape_seed=",
    change[
        "shape_seed"
    ],
)

print(
    "roughness_target=",
    parameters[
        "roughness_target"
    ],
)

print(
    "scratch_count=",
    parameters[
        "scratch_count"
    ],
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
    "scratches_vs_baseline_rmse=",
    scratches_vs_baseline[
        "rmse"
    ],
)

print(
    "scratches_vs_baseline_max_error=",
    scratches_vs_baseline[
        "max_error"
    ],
)

print(
    "changed_components=",
    scratches_vs_baseline[
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
    first_bbox
    == baseline_bbox,
)

print(
    "label_unchanged=",
    first_label
    == baseline_label,
)

print(
    "normal_socket_untouched=",
    normal.is_linked
    == normal_was_linked,
)

print(
    "upstream_water_record_unchanged=",
    first_water
    == baseline_water,
)

print(
    "material_restored=True"
)

print(
    "temporary_scratches_nodes_after_reset=",
    temporary_scratches_nodes,
)

print(
    "temporary_scratches_images_after_reset=",
    temporary_scratches_images,
)

print(
    "BVT_SCRATCHES_ARTIFACT_CLEANUP=OK"
)

print(
    "BVT_SCRATCHES_RENDER=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()

shutil.rmtree(
    TMP
)
