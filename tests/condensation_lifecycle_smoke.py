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

from bvt.artifacts.base import (
    ArtifactConfig,
    ArtifactContext,
)
from bvt.artifacts.engine import (
    apply_artifacts,
    capture_artifact_baseline,
    restore_artifacts,
)
from bvt.artifacts.providers.condensation import (
    CONDENSATION_DROPLET_COUNT,
    CONDENSATION_MASK_RESOLUTION,
    CONDENSATION_PATCH_COUNT,
    CONDENSATION_ROUGHNESS_DELTA,
    CondensationArtifactProvider,
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

REFLECTION_MIN_ROUGHNESS = 0.02
REFLECTION_INTENSITY = 0.75

FINGERPRINT_INTENSITY = 0.50
FINGERPRINT_TRANSPARENCY = 0.35

CONDENSATION_INTENSITY = 0.65


def alpha_hash(
    image,
):
    pixels = image.pixels[:]

    alpha = bytearray()

    for index in range(
        3,
        len(pixels),
        4,
    ):
        alpha.append(
            max(
                0,
                min(
                    255,
                    round(
                        float(
                            pixels[index]
                        )
                        * 255.0
                    ),
                ),
            )
        )

    return hashlib.sha256(
        alpha
    ).hexdigest()


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


def source_node(
    socket,
):
    assert socket.is_linked

    assert (
        len(
            socket.links
        )
        == 1
    )

    return socket.links[
        0
    ].from_node


bvt.register()

scene = bpy.context.scene
project = scene.bvt_project

cube = bpy.data.objects[
    "Cube"
]


# =========================================================
# Primary BVT glass material.
# =========================================================

material = bpy.data.materials.new(
    "BVT_Condensation_Glass"
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
    if node.type == "BSDF_PRINCIPLED"
)

roughness = principled.inputs[
    "Roughness"
]

roughness.default_value = (
    BASE_ROUGHNESS
)


# =========================================================
# Second GLASS material with a user-controlled link.
# Condensation must never replace this graph.
# =========================================================

user_material = bpy.data.materials.new(
    "BVT_Condensation_User_Link"
)

user_material.use_nodes = True

set_material_role(
    user_material,
    MATERIAL_ROLE_GLASS,
)

cube.data.materials.append(
    user_material
)


user_principled = next(
    node
    for node
    in user_material.node_tree.nodes
    if node.type == "BSDF_PRINCIPLED"
)

user_roughness = (
    user_principled.inputs[
        "Roughness"
    ]
)

user_value = (
    user_material.node_tree.nodes.new(
        "ShaderNodeValue"
    )
)

user_value.name = (
    "User Roughness Control"
)

user_value.outputs[
    0
].default_value = 0.42

user_material.node_tree.links.new(
    user_value.outputs[
        0
    ],
    user_roughness,
)

assert user_roughness.is_linked

user_source_pointer = (
    source_node(
        user_roughness
    ).as_pointer()
)


# =========================================================
# Capture Condensation BEFORE any other artifacts.
# This mirrors real Artifact Engine baseline capture.
# =========================================================

provider = (
    CondensationArtifactProvider()
)

condensation_baseline = (
    provider.capture(
        scene
    )
)


assert (
    len(
        condensation_baseline[
            "materials"
        ]
    )
    == 2
)

primary_baseline = next(
    entry
    for entry
    in condensation_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == "BVT_Condensation_Glass"
    )
)

user_baseline = next(
    entry
    for entry
    in condensation_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == "BVT_Condensation_User_Link"
    )
)

assert (
    len(
        primary_baseline[
            "nodes"
        ]
    )
    == 1
)

assert (
    user_baseline[
        "nodes"
    ]
    == []
)


# Existing engine baseline currently contains
# Reflection + Fingerprints but not Condensation.
engine_baseline = (
    capture_artifact_baseline(
        scene
    )
)


# =========================================================
# Configure existing artifact chain.
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
project.artifact_fingerprints_count = 3
project.artifact_fingerprints_transparency = (
    FINGERPRINT_TRANSPARENCY
)
project.artifact_fingerprints_size = 0.30

# Condensation is exercised directly in this lifecycle
# test, so keep the Engine-owned instance disabled.
project.artifact_condensation_enabled = False

project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


frame_seed_1 = derive_frame_seed(
    12345,
    1,
)


engine_result = apply_artifacts(
    scene,
    project,
    frame_seed_1,
    engine_baseline,
)


artifact_order = [
    item["artifact"]
    for item
    in engine_result[
        "artifacts"
    ]
]

assert artifact_order == [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


# Reflection changes the constant roughness first.
expected_reflection_roughness = (
    BASE_ROUGHNESS
    + (
        REFLECTION_MIN_ROUGHNESS
        - BASE_ROUGHNESS
    )
    * REFLECTION_INTENSITY
)

assert abs(
    float(
        roughness.default_value
    )
    - expected_reflection_roughness
) <= 1e-7


# Fingerprints owns Roughness at this point.
fingerprint_source = (
    source_node(
        roughness
    )
)

fingerprint_source_name = str(
    fingerprint_source.name
)

assert (
    fingerprint_source_name.startswith(
        "BVT Fingerprints Roughness Mix"
    )
)


# User graph must remain untouched by existing artifacts.
assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


# =========================================================
# Direct Condensation application.
# =========================================================

condensation_seed_1 = derive_subseed(
    frame_seed_1,
    "artifact",
    "condensation",
)

config_1 = ArtifactConfig(
    artifact_id="condensation",
    enabled=True,
    probability=1.0,
    intensity=CONDENSATION_INTENSITY,
)

context_1 = ArtifactContext(
    config=config_1,
    frame_seed=frame_seed_1,
    artifact_seed=condensation_seed_1,
    decision_roll=0.0,
)


provider.validate_config(
    config_1
)

metadata_1 = provider.apply(
    scene,
    context_1,
    condensation_baseline,
)


# Condensation now owns Roughness.
condensation_source = (
    source_node(
        roughness
    )
)

condensation_source_name = str(
    condensation_source.name
)

assert (
    condensation_source_name.startswith(
        "BVT Condensation Roughness Mix"
    )
)


# Condensation input must come from Fingerprints.
condensation_input = (
    condensation_source.inputs[
        0
    ]
)

assert condensation_input.is_linked

condensation_input_source = (
    condensation_input.links[
        0
    ].from_node
)

assert (
    str(
        condensation_input_source.name
    )
    == fingerprint_source_name
)


# User-controlled GLASS shader remains intact.
assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


assert metadata_1[
    "affected_materials"
] == [
    "BVT_Condensation_Glass"
]


parameters_1 = metadata_1[
    "parameters"
]

assert (
    parameters_1[
        "target_role"
    ]
    == "GLASS"
)

assert (
    parameters_1[
        "mask_resolution"
    ]
    == CONDENSATION_MASK_RESOLUTION
)

assert abs(
    parameters_1[
        "roughness_delta"
    ]
    - CONDENSATION_ROUGHNESS_DELTA
) <= 1e-12

assert abs(
    parameters_1[
        "effective_strength"
    ]
    - CONDENSATION_INTENSITY
) <= 1e-12

assert (
    parameters_1[
        "patch_count"
    ]
    == CONDENSATION_PATCH_COUNT
)

assert (
    parameters_1[
        "droplet_count"
    ]
    == CONDENSATION_DROPLET_COUNT
)

assert (
    parameters_1[
        "mean_coverage"
    ]
    > 0.0
)

assert (
    parameters_1[
        "mean_coverage"
    ]
    < 1.0
)

assert (
    parameters_1[
        "mean_mask_value"
    ]
    > 0.0
)

assert (
    parameters_1[
        "mean_mask_value"
    ]
    < 1.0
)


changes_1 = parameters_1[
    "material_changes"
]

assert len(
    changes_1
) == 1

change_1 = changes_1[
    0
]

assert (
    change_1[
        "material"
    ]
    == "BVT_Condensation_Glass"
)


expected_material_seed_1 = derive_subseed(
    condensation_seed_1,
    "artifact-condensation",
    "BVT_Condensation_Glass",
)

assert (
    change_1[
        "material_seed"
    ]
    == expected_material_seed_1
)

assert (
    change_1[
        "patch_seed"
    ]
    == derive_subseed(
        expected_material_seed_1,
        "condensation-mask",
        "patches",
    )
)

assert (
    change_1[
        "droplet_seed"
    ]
    == derive_subseed(
        expected_material_seed_1,
        "condensation-mask",
        "droplets",
    )
)

assert (
    change_1[
        "texture_seed"
    ]
    == derive_subseed(
        expected_material_seed_1,
        "condensation-mask",
        "texture",
    )
)

assert (
    change_1[
        "coverage"
    ]
    > 0.0
)

assert (
    change_1[
        "mean_mask_value"
    ]
    > 0.0
)


node_changes_1 = change_1[
    "nodes"
]

assert len(
    node_changes_1
) == 1

node_change_1 = (
    node_changes_1[
        0
    ]
)

assert (
    node_change_1[
        "input_mode"
    ]
    == "fingerprints"
)

assert (
    node_change_1[
        "upstream_node"
    ]
    == fingerprint_source_name
)

assert abs(
    node_change_1[
        "base_roughness"
    ]
    - BASE_ROUGHNESS
) <= 1e-7

assert abs(
    node_change_1[
        "input_roughness"
    ]
    - expected_reflection_roughness
) <= 1e-7


condensation_nodes_1 = (
    nodes_with_prefix(
        material,
        "BVT Condensation",
    )
)

assert (
    len(
        condensation_nodes_1
    )
    == 5
)


condensation_images_1 = (
    images_with_prefix(
        "BVT_Condensation_"
    )
)

assert (
    len(
        condensation_images_1
    )
    == 1
)

mask_hash_1 = alpha_hash(
    condensation_images_1[
        0
    ]
)


# =========================================================
# Condensation-only reset.
#
# Fingerprints must become owner of Roughness again.
# =========================================================

provider.reset(
    scene,
    condensation_baseline,
)


assert (
    nodes_with_prefix(
        material,
        "BVT Condensation",
    )
    == []
)

assert (
    images_with_prefix(
        "BVT_Condensation_"
    )
    == []
)


restored_fingerprint_source = (
    source_node(
        roughness
    )
)

assert (
    str(
        restored_fingerprint_source.name
    )
    == fingerprint_source_name
)


# Existing Fingerprints graph must still exist.
assert (
    len(
        nodes_with_prefix(
            material,
            "BVT Fingerprints",
        )
    )
    == 5
)


# User link still untouched.
assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


# =========================================================
# Same Condensation seed -> same metadata and mask.
# =========================================================

metadata_repeat = provider.apply(
    scene,
    context_1,
    condensation_baseline,
)

repeat_images = (
    images_with_prefix(
        "BVT_Condensation_"
    )
)

assert len(
    repeat_images
) == 1

mask_hash_repeat = alpha_hash(
    repeat_images[
        0
    ]
)

assert (
    metadata_repeat
    == metadata_1
)

assert (
    mask_hash_repeat
    == mask_hash_1
)


provider.reset(
    scene,
    condensation_baseline,
)


# =========================================================
# Different frame -> different Condensation seed/mask.
# =========================================================

restore_artifacts(
    scene,
    engine_baseline,
)


frame_seed_2 = derive_frame_seed(
    12345,
    2,
)


apply_artifacts(
    scene,
    project,
    frame_seed_2,
    engine_baseline,
)


fingerprint_source_2 = (
    source_node(
        roughness
    )
)

assert (
    str(
        fingerprint_source_2.name
    ).startswith(
        "BVT Fingerprints Roughness Mix"
    )
)


condensation_seed_2 = derive_subseed(
    frame_seed_2,
    "artifact",
    "condensation",
)

assert (
    condensation_seed_2
    != condensation_seed_1
)


config_2 = ArtifactConfig(
    artifact_id="condensation",
    enabled=True,
    probability=1.0,
    intensity=CONDENSATION_INTENSITY,
)

context_2 = ArtifactContext(
    config=config_2,
    frame_seed=frame_seed_2,
    artifact_seed=condensation_seed_2,
    decision_roll=0.0,
)


metadata_2 = provider.apply(
    scene,
    context_2,
    condensation_baseline,
)


different_images = (
    images_with_prefix(
        "BVT_Condensation_"
    )
)

assert len(
    different_images
) == 1

mask_hash_2 = alpha_hash(
    different_images[
        0
    ]
)


change_2 = (
    metadata_2[
        "parameters"
    ][
        "material_changes"
    ][0]
)


assert (
    change_2[
        "material_seed"
    ]
    != change_1[
        "material_seed"
    ]
)

assert (
    mask_hash_2
    != mask_hash_1
)


# =========================================================
# Final cleanup:
# Condensation first, then existing artifacts.
# =========================================================

provider.reset(
    scene,
    condensation_baseline,
)

restore_artifacts(
    scene,
    engine_baseline,
)


assert not roughness.is_linked

assert abs(
    float(
        roughness.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-6


assert (
    nodes_with_prefix(
        material,
        "BVT Condensation",
    )
    == []
)

assert (
    nodes_with_prefix(
        material,
        "BVT Fingerprints",
    )
    == []
)

assert (
    images_with_prefix(
        "BVT_Condensation_"
    )
    == []
)

assert (
    images_with_prefix(
        "BVT_Fingerprints_"
    )
    == []
)


# User-controlled graph must survive the entire lifecycle.
assert user_roughness.is_linked

assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


print(
    "BVT_CONDENSATION_LIFECYCLE_SMOKE=OK"
)

print(
    "existing_artifact_order=",
    artifact_order,
)

print(
    "condensation_seed=",
    condensation_seed_1,
)

print(
    "material_seed=",
    expected_material_seed_1,
)

print(
    "reflection_roughness=",
    expected_reflection_roughness,
)

print(
    "fingerprint_source=",
    fingerprint_source_name,
)

print(
    "condensation_source=",
    condensation_source_name,
)

print(
    "coverage=",
    change_1[
        "coverage"
    ],
)

print(
    "mean_mask_value=",
    change_1[
        "mean_mask_value"
    ],
)

print(
    "temporary_condensation_nodes=5"
)

print(
    "same_seed_mask_equal=",
    (
        mask_hash_repeat
        == mask_hash_1
    ),
)

print(
    "different_seed_mask_changed=",
    (
        mask_hash_2
        != mask_hash_1
    ),
)

print(
    "fingerprints_restored_after_condensation_reset=True"
)

print(
    "user_shader_link_preserved=True"
)

print(
    "roughness_restored=",
    float(
        roughness.default_value
    ),
)

print(
    "temporary_condensation_images_after_reset=",
    len(
        images_with_prefix(
            "BVT_Condensation_"
        )
    ),
)


bvt.unregister()


print(
    "BVT_CONDENSATION_LIFECYCLE_CLEANUP=OK"
)
