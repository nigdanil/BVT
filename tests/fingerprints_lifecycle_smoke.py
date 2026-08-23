import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.artifacts.engine import (
    apply_artifacts,
    capture_artifact_baseline,
    restore_artifacts,
)
from bvt.core.seeding import (
    derive_frame_seed,
    derive_subseed,
)
from bvt.materials import (
    MATERIAL_ROLE_GLASS,
    set_material_role,
)


BASE_ROUGHNESS = 0.80

REFLECTION_INTENSITY = 0.75
REFLECTION_MIN_ROUGHNESS = 0.02

FINGERPRINT_INTENSITY = 0.50
FINGERPRINT_COUNT = 3
FINGERPRINT_TRANSPARENCY = 0.35
FINGERPRINT_SIZE = 0.30

EXPECTED_ORDER = [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


def close_enough(
    first,
    second,
    tolerance=1e-6,
):
    return (
        abs(
            float(first)
            - float(second)
        )
        <= tolerance
    )


def fingerprint_images():
    return [
        image
        for image in bpy.data.images
        if image.name.startswith(
            "BVT_Fingerprints_"
        )
    ]


def fingerprint_nodes(
    material,
):
    return [
        node
        for node in material.node_tree.nodes
        if node.name.startswith(
            "BVT Fingerprints"
        )
    ]


def mask_hash():
    images = fingerprint_images()

    assert len(images) == 1

    image = images[0]

    pixels = image.pixels[:]

    alpha = bytearray()

    for index in range(
        3,
        len(pixels),
        4,
    ):
        value = max(
            0.0,
            min(
                1.0,
                float(
                    pixels[index]
                ),
            ),
        )

        alpha.append(
            int(
                value * 255.0
                + 0.5
            )
        )

    return hashlib.sha256(
        alpha
    ).hexdigest()


def artifact_by_id(
    result,
    artifact_id,
):
    return next(
        item
        for item
        in result["artifacts"]
        if (
            item["artifact"]
            == artifact_id
        )
    )


def assert_clean(
    material,
    roughness,
    baseline,
):
    assert (
        fingerprint_nodes(
            material
        )
        == []
    )

    assert (
        fingerprint_images()
        == []
    )

    assert (
        roughness.is_linked
        is False
    )

    assert close_enough(
        roughness.default_value,
        BASE_ROUGHNESS,
    )

    assert (
        baseline[
            "fingerprints"
        ][
            "runtime"
        ]
        == []
    )


bvt.register()

scene = bpy.context.scene
project = scene.bvt_project


# ---------------------------------------------------------
# Scene / material
# ---------------------------------------------------------

cube = bpy.data.objects[
    "Cube"
]

material = bpy.data.materials.new(
    "BVT_Fingerprints_Glass"
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
    if (
        node.type
        == "BSDF_PRINCIPLED"
    )
)

roughness = principled.inputs.get(
    "Roughness"
)

assert roughness is not None
assert roughness.is_linked is False

roughness.default_value = (
    BASE_ROUGHNESS
)


# ---------------------------------------------------------
# Artifact configuration
# ---------------------------------------------------------

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

project.artifact_condensation_enabled = False

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


baseline = capture_artifact_baseline(
    scene
)


# ---------------------------------------------------------
# First application
# ---------------------------------------------------------

frame_seed_1 = derive_frame_seed(
    12345,
    1,
)

first = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_1,
    baseline=baseline,
)


artifact_ids = [
    item["artifact"]
    for item
    in first["artifacts"]
]

assert (
    artifact_ids
    == EXPECTED_ORDER
)


reflection = artifact_by_id(
    first,
    "reflection",
)

fingerprints = artifact_by_id(
    first,
    "fingerprints",
)


assert reflection["applied"] is True

assert (
    reflection["stage"]
    == "pre_render"
)

assert (
    reflection[
        "execution_order"
    ]
    == 100
)


assert fingerprints["enabled"] is True
assert fingerprints["applied"] is True

assert (
    fingerprints["category"]
    == "glass"
)

assert (
    fingerprints["stage"]
    == "pre_render"
)

assert (
    fingerprints[
        "execution_order"
    ]
    == 110
)


expected_fingerprint_seed = (
    derive_subseed(
        frame_seed_1,
        "artifact",
        "fingerprints",
    )
)

assert (
    fingerprints["seed"]
    == expected_fingerprint_seed
)


assert (
    fingerprints[
        "affected_materials"
    ]
    == [
        "BVT_Fingerprints_Glass"
    ]
)


parameters = fingerprints[
    "parameters"
]

assert (
    parameters["target_role"]
    == "GLASS"
)

assert (
    parameters["print_count"]
    == FINGERPRINT_COUNT
)

assert close_enough(
    parameters[
        "transparency"
    ],
    FINGERPRINT_TRANSPARENCY,
)

assert close_enough(
    parameters["size"],
    FINGERPRINT_SIZE,
)

assert (
    parameters[
        "mask_resolution"
    ]
    == 256
)

expected_strength = (
    FINGERPRINT_INTENSITY
    * (
        1.0
        - FINGERPRINT_TRANSPARENCY
    )
)

assert close_enough(
    parameters[
        "effective_strength"
    ],
    expected_strength,
)

assert (
    parameters[
        "mean_coverage"
    ]
    > 0.0
)


changes = parameters[
    "material_changes"
]

assert len(changes) == 1

change = changes[0]

assert (
    change["material"]
    == "BVT_Fingerprints_Glass"
)

expected_material_seed = (
    derive_subseed(
        expected_fingerprint_seed,
        "artifact-fingerprints",
        "BVT_Fingerprints_Glass",
    )
)

assert (
    change["material_seed"]
    == expected_material_seed
)

assert (
    change["coverage"]
    > 0.0
)

assert (
    len(
        change["fingerprints"]
    )
    == FINGERPRINT_COUNT
)

assert len(
    change["nodes"]
) == 1


node_change = change[
    "nodes"
][0]

expected_reflection_roughness = (
    BASE_ROUGHNESS
    + (
        REFLECTION_MIN_ROUGHNESS
        - BASE_ROUGHNESS
    )
    * REFLECTION_INTENSITY
)

assert close_enough(
    node_change[
        "base_roughness"
    ],
    BASE_ROUGHNESS,
)

# This is the important Reflection -> Fingerprints
# composition check.
assert close_enough(
    node_change[
        "input_roughness"
    ],
    expected_reflection_roughness,
)

expected_target_roughness = min(
    1.0,
    (
        expected_reflection_roughness
        + 0.45
    ),
)

assert close_enough(
    node_change[
        "target_roughness"
    ],
    expected_target_roughness,
)


assert (
    roughness.is_linked
    is True
)

temporary_nodes = (
    fingerprint_nodes(
        material
    )
)

assert (
    len(
        temporary_nodes
    )
    == 5
)

assert (
    len(
        fingerprint_images()
    )
    == 1
)

first_mask_hash = mask_hash()

first_fingerprint_record = (
    fingerprints
)


# ---------------------------------------------------------
# Reset
# ---------------------------------------------------------

restore_artifacts(
    scene,
    baseline,
)

assert_clean(
    material,
    roughness,
    baseline,
)


# ---------------------------------------------------------
# Same seed -> exact same artifact
# ---------------------------------------------------------

second = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_1,
    baseline=baseline,
)

second_fingerprints = (
    artifact_by_id(
        second,
        "fingerprints",
    )
)

second_mask_hash = (
    mask_hash()
)

assert (
    first_fingerprint_record
    == second_fingerprints
)

assert (
    first_mask_hash
    == second_mask_hash
)


restore_artifacts(
    scene,
    baseline,
)

assert_clean(
    material,
    roughness,
    baseline,
)


# ---------------------------------------------------------
# Different frame seed -> different pattern
# ---------------------------------------------------------

frame_seed_2 = derive_frame_seed(
    12345,
    2,
)

third = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_2,
    baseline=baseline,
)

third_fingerprints = (
    artifact_by_id(
        third,
        "fingerprints",
    )
)

third_mask_hash = (
    mask_hash()
)

assert (
    third_fingerprints["seed"]
    != first_fingerprint_record[
        "seed"
    ]
)

assert (
    third_fingerprints[
        "parameters"
    ][
        "material_changes"
    ][0][
        "fingerprints"
    ]
    != first_fingerprint_record[
        "parameters"
    ][
        "material_changes"
    ][0][
        "fingerprints"
    ]
)

assert (
    third_mask_hash
    != first_mask_hash
)


restore_artifacts(
    scene,
    baseline,
)

assert_clean(
    material,
    roughness,
    baseline,
)


# ---------------------------------------------------------
# Cleanup
# ---------------------------------------------------------

cube.data.materials.clear()

bpy.data.materials.remove(
    material
)

bvt.unregister()


print(
    "BVT_FINGERPRINTS_LIFECYCLE_SMOKE=OK"
)

print(
    "artifact_order=",
    artifact_ids,
)

print(
    "fingerprint_seed=",
    expected_fingerprint_seed,
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
    "effective_strength=",
    expected_strength,
)

print(
    "coverage=",
    change["coverage"],
)

print(
    "temporary_nodes=5"
)

print(
    "same_seed_mask_equal=",
    (
        first_mask_hash
        == second_mask_hash
    ),
)

print(
    "different_seed_mask_changed=",
    (
        first_mask_hash
        != third_mask_hash
    ),
)

print(
    "roughness_restored=",
    BASE_ROUGHNESS,
)

print(
    "temporary_images_after_reset=",
    len(
        fingerprint_images()
    ),
)

print(
    "BVT_FINGERPRINTS_LIFECYCLE_CLEANUP=OK"
)
