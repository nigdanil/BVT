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
from bvt.artifacts.providers.frost import (
    FROST_CRYSTAL_COUNT,
    FROST_MASK_RESOLUTION,
    FROST_ROUGHNESS_DELTA,
    FrostArtifactProvider,
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

FROST_INTENSITY = 0.70


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


def artifact_by_id(
    result,
    artifact_id,
):
    return next(
        item
        for item
        in result[
            "artifacts"
        ]
        if (
            item[
                "artifact"
            ]
            == artifact_id
        )
    )


def configure_engine(
    project,
    *,
    fingerprints,
    condensation,
):
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

    project.artifact_fingerprints_enabled = (
        fingerprints
    )
    project.artifact_fingerprints_probability = 1.0
    project.artifact_fingerprints_intensity = 0.50
    project.artifact_fingerprints_count = 3
    project.artifact_fingerprints_transparency = 0.35
    project.artifact_fingerprints_size = 0.30

    project.artifact_condensation_enabled = (
        condensation
    )
    project.artifact_condensation_probability = 1.0
    project.artifact_condensation_intensity = 0.65

    project.artifact_frost_enabled = False

    project.artifact_motion_blur_enabled = False
    project.artifact_noise_enabled = False
    project.artifact_jpeg_enabled = False


def frost_context(
    frame_seed,
):
    artifact_seed = derive_subseed(
        frame_seed,
        "artifact",
        "frost",
    )

    config = ArtifactConfig(
        artifact_id="frost",
        enabled=True,
        probability=1.0,
        intensity=FROST_INTENSITY,
    )

    context = ArtifactContext(
        config=config,
        frame_seed=frame_seed,
        artifact_seed=artifact_seed,
        decision_roll=0.0,
    )

    return (
        artifact_seed,
        config,
        context,
    )


def frost_change(
    metadata,
):
    changes = metadata[
        "parameters"
    ][
        "material_changes"
    ]

    assert len(
        changes
    ) == 1

    change = changes[
        0
    ]

    assert len(
        change[
            "nodes"
        ]
    ) == 1

    return (
        change,
        change[
            "nodes"
        ][0],
    )


bvt.register()

scene = bpy.context.scene
project = scene.bvt_project

cube = bpy.data.objects[
    "Cube"
]


# =========================================================
# Main BVT Glass material.
# =========================================================

material = bpy.data.materials.new(
    "BVT_Frost_Glass"
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
# User-linked GLASS material.
#
# None of the BVT material artifacts may replace this link.
# =========================================================

user_material = bpy.data.materials.new(
    "BVT_Frost_User_Link"
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

user_roughness = user_principled.inputs[
    "Roughness"
]

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


user_source_pointer = (
    source_node(
        user_roughness
    ).as_pointer()
)


# =========================================================
# Capture clean baselines BEFORE applying any artifacts.
# =========================================================

provider = FrostArtifactProvider()

frost_baseline = provider.capture(
    scene
)

engine_baseline = (
    capture_artifact_baseline(
        scene
    )
)


assert (
    len(
        frost_baseline[
            "materials"
        ]
    )
    == 2
)


main_baseline = next(
    entry
    for entry
    in frost_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == "BVT_Frost_Glass"
    )
)


user_baseline = next(
    entry
    for entry
    in frost_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == "BVT_Frost_User_Link"
    )
)


assert (
    len(
        main_baseline[
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


expected_reflection_roughness = (
    BASE_ROUGHNESS
    + (
        REFLECTION_MIN_ROUGHNESS
        - BASE_ROUGHNESS
    )
    * REFLECTION_INTENSITY
)


# =========================================================
# MODE 1:
# Reflection -> Fingerprints -> Condensation -> Frost
# =========================================================

configure_engine(
    project,
    fingerprints=True,
    condensation=True,
)


frame_seed_1 = derive_frame_seed(
    12345,
    1,
)


engine_result_1 = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_1,
    baseline=engine_baseline,
)


artifact_order = [
    item[
        "artifact"
    ]
    for item
    in engine_result_1[
        "artifacts"
    ]
]


assert artifact_order == [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "frost",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


condensation = artifact_by_id(
    engine_result_1,
    "condensation",
)

assert (
    condensation[
        "applied"
    ]
    is True
)


condensation_source = source_node(
    roughness
)

condensation_source_name = str(
    condensation_source.name
)

assert (
    condensation_source_name.startswith(
        "BVT Condensation Roughness Mix"
    )
)


frost_seed_1, config_1, context_1 = (
    frost_context(
        frame_seed_1
    )
)


provider.validate_config(
    config_1
)


metadata_1 = provider.apply(
    scene,
    context_1,
    frost_baseline,
)


frost_source = source_node(
    roughness
)

frost_source_name = str(
    frost_source.name
)


assert (
    frost_source_name.startswith(
        "BVT Frost Roughness Mix"
    )
)


assert (
    frost_source.inputs[
        0
    ].is_linked
)


frost_input_source = (
    frost_source.inputs[
        0
    ].links[
        0
    ].from_node
)


assert (
    str(
        frost_input_source.name
    )
    == condensation_source_name
)


assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


assert (
    metadata_1[
        "affected_materials"
    ]
    == [
        "BVT_Frost_Glass"
    ]
)


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
    == FROST_MASK_RESOLUTION
)

assert abs(
    parameters_1[
        "roughness_delta"
    ]
    - FROST_ROUGHNESS_DELTA
) <= 1e-12

assert abs(
    parameters_1[
        "effective_strength"
    ]
    - FROST_INTENSITY
) <= 1e-12

assert (
    parameters_1[
        "crystal_count"
    ]
    == FROST_CRYSTAL_COUNT
)

assert (
    0.0
    < parameters_1[
        "mean_coverage"
    ]
    < 1.0
)

assert (
    0.0
    < parameters_1[
        "mean_mask_value"
    ]
    < 1.0
)


change_1, node_change_1 = (
    frost_change(
        metadata_1
    )
)


assert (
    node_change_1[
        "input_mode"
    ]
    == "condensation"
)

assert (
    node_change_1[
        "upstream_node"
    ]
    == condensation_source_name
)

assert abs(
    node_change_1[
        "base_roughness"
    ]
    - BASE_ROUGHNESS
) <= 1e-6

assert abs(
    node_change_1[
        "input_roughness"
    ]
    - expected_reflection_roughness
) <= 1e-6


expected_material_seed_1 = derive_subseed(
    frost_seed_1,
    "artifact-frost",
    "BVT_Frost_Glass",
)


assert (
    change_1[
        "material_seed"
    ]
    == expected_material_seed_1
)

assert (
    change_1[
        "crystal_seed"
    ]
    == derive_subseed(
        expected_material_seed_1,
        "frost-mask",
        "crystals",
    )
)

assert (
    change_1[
        "texture_seed"
    ]
    == derive_subseed(
        expected_material_seed_1,
        "frost-mask",
        "texture",
    )
)


assert (
    len(
        nodes_with_prefix(
            material,
            "BVT Frost",
        )
    )
    == 5
)


frost_images_1 = (
    images_with_prefix(
        "BVT_Frost_"
    )
)

assert (
    len(
        frost_images_1
    )
    == 1
)


mask_hash_1 = alpha_hash(
    frost_images_1[
        0
    ]
)


# =========================================================
# Frost-only reset:
# Condensation must own Roughness again.
# =========================================================

provider.reset(
    scene,
    frost_baseline,
)


assert (
    nodes_with_prefix(
        material,
        "BVT Frost",
    )
    == []
)

assert (
    images_with_prefix(
        "BVT_Frost_"
    )
    == []
)


restored_condensation = source_node(
    roughness
)


assert (
    str(
        restored_condensation.name
    )
    == condensation_source_name
)


# =========================================================
# Same seed -> same Frost mask + metadata.
# =========================================================

metadata_repeat = provider.apply(
    scene,
    context_1,
    frost_baseline,
)


repeat_images = (
    images_with_prefix(
        "BVT_Frost_"
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
    frost_baseline,
)


# =========================================================
# Different frame -> different Frost seed/mask.
# =========================================================

restore_artifacts(
    scene,
    engine_baseline,
)


frame_seed_2 = derive_frame_seed(
    12345,
    2,
)


engine_result_2 = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_2,
    baseline=engine_baseline,
)


assert (
    artifact_by_id(
        engine_result_2,
        "condensation",
    )[
        "applied"
    ]
    is True
)


frost_seed_2, config_2, context_2 = (
    frost_context(
        frame_seed_2
    )
)


assert (
    frost_seed_2
    != frost_seed_1
)


metadata_2 = provider.apply(
    scene,
    context_2,
    frost_baseline,
)


different_images = (
    images_with_prefix(
        "BVT_Frost_"
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


change_2, node_change_2 = (
    frost_change(
        metadata_2
    )
)


assert (
    node_change_2[
        "input_mode"
    ]
    == "condensation"
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


provider.reset(
    scene,
    frost_baseline,
)

restore_artifacts(
    scene,
    engine_baseline,
)


# =========================================================
# MODE 2:
# Reflection -> Fingerprints -> Frost
#
# Condensation disabled.
# =========================================================

configure_engine(
    project,
    fingerprints=True,
    condensation=False,
)


fingerprint_result = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_1,
    baseline=engine_baseline,
)


fingerprints = artifact_by_id(
    fingerprint_result,
    "fingerprints",
)

condensation_disabled = artifact_by_id(
    fingerprint_result,
    "condensation",
)


assert (
    fingerprints[
        "applied"
    ]
    is True
)

assert (
    condensation_disabled[
        "applied"
    ]
    is False
)


fingerprint_source = source_node(
    roughness
)

fingerprint_source_name = str(
    fingerprint_source.name
)


assert (
    fingerprint_source_name.startswith(
        "BVT Fingerprints Roughness Mix"
    )
)


metadata_fingerprints = provider.apply(
    scene,
    context_1,
    frost_baseline,
)


_, fingerprint_node_change = (
    frost_change(
        metadata_fingerprints
    )
)


assert (
    fingerprint_node_change[
        "input_mode"
    ]
    == "fingerprints"
)

assert (
    fingerprint_node_change[
        "upstream_node"
    ]
    == fingerprint_source_name
)


provider.reset(
    scene,
    frost_baseline,
)


assert (
    str(
        source_node(
            roughness
        ).name
    )
    == fingerprint_source_name
)


restore_artifacts(
    scene,
    engine_baseline,
)


# =========================================================
# MODE 3:
# Reflection -> constant Roughness -> Frost
#
# Fingerprints and Condensation disabled.
# =========================================================

configure_engine(
    project,
    fingerprints=False,
    condensation=False,
)


constant_result = apply_artifacts(
    scene=scene,
    project_settings=project,
    frame_seed=frame_seed_1,
    baseline=engine_baseline,
)


assert (
    artifact_by_id(
        constant_result,
        "reflection",
    )[
        "applied"
    ]
    is True
)


assert (
    roughness.is_linked
    is False
)

assert abs(
    float(
        roughness.default_value
    )
    - expected_reflection_roughness
) <= 1e-6


metadata_constant = provider.apply(
    scene,
    context_1,
    frost_baseline,
)


_, constant_node_change = (
    frost_change(
        metadata_constant
    )
)


assert (
    constant_node_change[
        "input_mode"
    ]
    == "constant"
)

assert (
    constant_node_change[
        "upstream_node"
    ]
    is None
)


provider.reset(
    scene,
    frost_baseline,
)


# Frost reset must preserve Reflection state.
assert (
    roughness.is_linked
    is False
)

assert abs(
    float(
        roughness.default_value
    )
    - expected_reflection_roughness
) <= 1e-6


# =========================================================
# Final full cleanup.
# =========================================================

restore_artifacts(
    scene,
    engine_baseline,
)


assert (
    roughness.is_linked
    is False
)

assert abs(
    float(
        roughness.default_value
    )
    - BASE_ROUGHNESS
) <= 1e-6


assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


assert (
    nodes_with_prefix(
        material,
        "BVT Frost",
    )
    == []
)

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
        "BVT_Frost_"
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


print(
    "BVT_FROST_LIFECYCLE_SMOKE=OK"
)

print(
    "existing_artifact_order=",
    artifact_order,
)

print(
    "frost_seed=",
    frost_seed_1,
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
    "condensation_source=",
    condensation_source_name,
)

print(
    "frost_source=",
    frost_source_name,
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
    "input_mode_condensation=True"
)

print(
    "input_mode_fingerprints=True"
)

print(
    "input_mode_constant=True"
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
    "user_shader_link_preserved=True"
)

print(
    "roughness_restored=",
    float(
        roughness.default_value
    ),
)

print(
    "temporary_frost_nodes_after_reset=",
    len(
        nodes_with_prefix(
            material,
            "BVT Frost",
        )
    ),
)

print(
    "temporary_frost_images_after_reset=",
    len(
        images_with_prefix(
            "BVT_Frost_"
        )
    ),
)


bvt.unregister()


print(
    "BVT_FROST_LIFECYCLE_CLEANUP=OK"
)
