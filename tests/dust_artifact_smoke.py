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
    / "dust-artifact.blend"
)

BASELINE_IMAGE = (
    TMP
    / "dust-baseline.png"
)

FIRST_IMAGE = (
    TMP
    / "dust-first.png"
)

PIXEL_TOLERANCE = 1e-6


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import (
    register_object,
)
from bvt.artifacts.providers.dust import (
    DUST_ROUGHNESS_DELTA,
)
from bvt.artifacts.providers.dust_mask import (
    DUST_CLUSTER_COUNT,
    DUST_MASK_RESOLUTION,
    DUST_PARTICLE_COUNT,
)
from bvt.core.seeding import (
    derive_subseed,
)
from bvt.materials import (
    MATERIAL_ROLE_GLASS,
    set_material_role,
)
from bvt.project.service import (
    initialize_project,
)
from bvt.render.service import (
    generate_dataset,
)


def load_pixels(
    path,
):
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
            item[
                "artifact"
            ]
            == artifact_id
        )
    )


def read_manifest(
    result,
):
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
        "BVT Dust",
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
        "BVT_Dust_",
    ):
        assert (
            temporary_images(
                prefix
            )
            == []
        )


# =========================================================
# Clean temporary workspace.
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
# Scene / project.
# =========================================================

bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


project = scene.bvt_project

project.project_name = (
    "Dust Artifact Smoke"
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
# Annotated GLASS cube.
# =========================================================

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
        "BVT_Dust_Glass"
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

CONDENSATION_INTENSITY = 1.0

FROST_INTENSITY = 1.0

DUST_INTENSITY = 1.0


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


project.artifact_frost_enabled = True

project.artifact_frost_probability = 1.0

project.artifact_frost_intensity = (
    FROST_INTENSITY
)


project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


# =========================================================
# Baseline:
# Reflection
# -> Fingerprints
# -> Condensation
# -> Frost
#
# Dust disabled.
# =========================================================

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


baseline_dust = artifact_by_id(
    baseline_frame,
    "dust",
)


assert (
    baseline_dust[
        "enabled"
    ]
    is False
)

assert (
    baseline_dust[
        "applied"
    ]
    is False
)

assert (
    baseline_dust[
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
# Full chain:
# Reflection
# -> Fingerprints
# -> Condensation
# -> Frost
# -> Dust
# =========================================================

project.artifact_dust_enabled = True

project.artifact_dust_probability = 1.0

project.artifact_dust_intensity = (
    DUST_INTENSITY
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


EXPECTED_ORDER = [
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


assert (
    artifact_ids
    == EXPECTED_ORDER
)


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

dust = artifact_by_id(
    frame,
    "dust",
)


for artifact in (
    reflection,
    fingerprints,
    condensation,
    frost,
    dust,
):
    assert (
        artifact[
            "applied"
        ]
        is True
    )


assert (
    dust[
        "enabled"
    ]
    is True
)

assert (
    dust[
        "category"
    ]
    == "glass"
)

assert (
    dust[
        "stage"
    ]
    == "pre_render"
)

assert (
    dust[
        "execution_order"
    ]
    == 140
)

assert (
    dust[
        "probability"
    ]
    == 1.0
)

assert (
    dust[
        "intensity"
    ]
    == DUST_INTENSITY
)

assert (
    dust[
        "options"
    ]
    == {}
)


# =========================================================
# Artifact seed.
# =========================================================

expected_seed = derive_subseed(
    frame[
        "frame_seed"
    ],
    "artifact",
    "dust",
)


assert (
    dust[
        "seed"
    ]
    == expected_seed
)


assert (
    dust[
        "affected_materials"
    ]
    == [
        "BVT_Dust_Glass"
    ]
)


# =========================================================
# Dust parameters.
# =========================================================

parameters = dust[
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
    == DUST_MASK_RESOLUTION
)

assert abs(
    parameters[
        "roughness_delta"
    ]
    - DUST_ROUGHNESS_DELTA
) <= 1e-12

assert abs(
    parameters[
        "effective_strength"
    ]
    - DUST_INTENSITY
) <= 1e-12

assert (
    parameters[
        "particle_count"
    ]
    == DUST_PARTICLE_COUNT
)

assert (
    parameters[
        "cluster_count"
    ]
    == DUST_CLUSTER_COUNT
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
    == "BVT_Dust_Glass"
)


# =========================================================
# Material / particle / cluster seeds.
# =========================================================

expected_material_seed = (
    derive_subseed(
        expected_seed,
        "artifact-dust",
        "BVT_Dust_Glass",
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
        "particle_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "dust-mask",
        "particles",
    )
)


assert (
    change[
        "cluster_seed"
    ]
    == derive_subseed(
        expected_material_seed,
        "dust-mask",
        "clusters",
    )
)


assert (
    change[
        "particle_count"
    ]
    == DUST_PARTICLE_COUNT
)

assert (
    change[
        "cluster_count"
    ]
    == DUST_CLUSTER_COUNT
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


# =========================================================
# Dust must wrap Frost.
# =========================================================

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
    == "frost"
)

assert (
    node_change[
        "upstream_node"
    ].startswith(
        "BVT Frost Roughness Mix"
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
    - DUST_ROUGHNESS_DELTA
) <= 1e-12


# =========================================================
# Annotation must not change.
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


# =========================================================
# Dust must create a real RGB difference.
# =========================================================

dust_vs_baseline = compare_images(
    BASELINE_IMAGE,
    FIRST_IMAGE,
)


assert (
    dust_vs_baseline[
        "max_error"
    ]
    > PIXEL_TOLERANCE
)

assert (
    dust_vs_baseline[
        "changed_components"
    ]
    > 0
)


# =========================================================
# Same seed / same config:
# exact same Dust record and pixels.
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


second_manifest = read_manifest(
    second
)

second_frame = (
    second_manifest[
        "frames"
    ][0]
)

second_dust = artifact_by_id(
    second_frame,
    "dust",
)


assert (
    second_dust
    == dust
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
)


# =========================================================
# Final cleanup state.
# =========================================================

temporary_fingerprint_nodes = len(
    temporary_nodes(
        glass_material,
        "BVT Fingerprints",
    )
)

temporary_condensation_nodes = len(
    temporary_nodes(
        glass_material,
        "BVT Condensation",
    )
)

temporary_frost_nodes = len(
    temporary_nodes(
        glass_material,
        "BVT Frost",
    )
)

temporary_dust_nodes = len(
    temporary_nodes(
        glass_material,
        "BVT Dust",
    )
)


temporary_fingerprint_images = len(
    temporary_images(
        "BVT_Fingerprints_"
    )
)

temporary_condensation_images = len(
    temporary_images(
        "BVT_Condensation_"
    )
)

temporary_frost_images = len(
    temporary_images(
        "BVT_Frost_"
    )
)

temporary_dust_images = len(
    temporary_images(
        "BVT_Dust_"
    )
)


assert temporary_fingerprint_nodes == 0
assert temporary_condensation_nodes == 0
assert temporary_frost_nodes == 0
assert temporary_dust_nodes == 0

assert temporary_fingerprint_images == 0
assert temporary_condensation_images == 0
assert temporary_frost_images == 0
assert temporary_dust_images == 0


# =========================================================
# Report.
# =========================================================

print(
    "BVT_DUST_ARTIFACT_SMOKE=OK"
)

print(
    "artifact_order=",
    artifact_ids,
)

print(
    "dust_seed=",
    dust[
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
    "particle_seed=",
    change[
        "particle_seed"
    ],
)

print(
    "cluster_seed=",
    change[
        "cluster_seed"
    ],
)

print(
    "reflection_roughness=",
    expected_reflection_roughness,
)

print(
    "roughness_delta=",
    parameters[
        "roughness_delta"
    ],
)

print(
    "effective_strength=",
    parameters[
        "effective_strength"
    ],
)

print(
    "particle_count=",
    parameters[
        "particle_count"
    ],
)

print(
    "cluster_count=",
    parameters[
        "cluster_count"
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
    "dust_vs_baseline_rmse=",
    dust_vs_baseline[
        "rmse"
    ],
)

print(
    "dust_vs_baseline_max_error=",
    dust_vs_baseline[
        "max_error"
    ],
)

print(
    "changed_components=",
    dust_vs_baseline[
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
    "material_restored=",
    (
        not roughness_socket.is_linked
        and abs(
            float(
                roughness_socket.default_value
            )
            - BASE_ROUGHNESS
        )
        <= 1e-6
    ),
)

print(
    "temporary_fingerprint_nodes_after_reset=",
    temporary_fingerprint_nodes,
)

print(
    "temporary_condensation_nodes_after_reset=",
    temporary_condensation_nodes,
)

print(
    "temporary_frost_nodes_after_reset=",
    temporary_frost_nodes,
)

print(
    "temporary_dust_nodes_after_reset=",
    temporary_dust_nodes,
)

print(
    "temporary_dust_images_after_reset=",
    temporary_dust_images,
)

print(
    "BVT_DUST_ARTIFACT_CLEANUP=OK"
)

print(
    "BVT_DUST_RENDER=OK"
)


bvt.unregister()

shutil.rmtree(
    TMP
)
