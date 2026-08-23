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
from bvt.artifacts.providers.dust import (
    DUST_ROUGHNESS_DELTA,
    DustArtifactProvider,
)
from bvt.artifacts.providers.dust_mask import (
    DUST_CLUSTER_COUNT,
    DUST_MASK_RESOLUTION,
    DUST_PARTICLE_COUNT,
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

DUST_INTENSITY = 0.70


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


def source_node(
    socket,
):
    assert socket.is_linked
    assert len(socket.links) == 1

    return socket.links[
        0
    ].from_node


def same_node(
    left,
    right,
):
    return (
        left.as_pointer()
        == right.as_pointer()
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
    frost,
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

    project.artifact_frost_enabled = frost
    project.artifact_frost_probability = 1.0
    project.artifact_frost_intensity = 0.70

    project.artifact_dust_enabled = False

    project.artifact_motion_blur_enabled = False
    project.artifact_noise_enabled = False
    project.artifact_jpeg_enabled = False


def dust_context(
    frame_seed,
):
    artifact_seed = derive_subseed(
        frame_seed,
        "artifact",
        "dust",
    )

    config = ArtifactConfig(
        artifact_id="dust",
        enabled=True,
        probability=1.0,
        intensity=DUST_INTENSITY,
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


def dust_change(
    metadata,
):
    changes = metadata[
        "parameters"
    ][
        "material_changes"
    ]

    assert len(changes) == 1

    change = changes[0]

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
# Primary GLASS material.
# =========================================================

material = bpy.data.materials.new(
    "BVT_Dust_Glass"
)

material.use_nodes = True

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

roughness.default_value = (
    BASE_ROUGHNESS
)

cube.data.materials.clear()
cube.data.materials.append(
    material
)

set_material_role(
    material,
    MATERIAL_ROLE_GLASS,
)


# =========================================================
# Second GLASS material with arbitrary user Roughness link.
# Dust and existing BVT artifacts must preserve it.
# =========================================================

user_material = bpy.data.materials.new(
    "BVT_Dust_User_Link_Glass"
)

user_material.use_nodes = True

user_principled = next(
    node
    for node
    in user_material.node_tree.nodes
    if node.type
    == "BSDF_PRINCIPLED"
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
    "User Roughness Source"
)

user_value.outputs[
    0
].default_value = 0.37

user_material.node_tree.links.new(
    user_value.outputs[0],
    user_roughness,
)

cube.data.materials.append(
    user_material
)

set_material_role(
    user_material,
    MATERIAL_ROLE_GLASS,
)

user_source_pointer = (
    user_value.as_pointer()
)


# =========================================================
# Baselines.
# Dust capture happens while primary Roughness is clean.
# =========================================================

dust_provider = (
    DustArtifactProvider()
)

dust_baseline = (
    dust_provider.capture(
        scene
    )
)

engine_baseline = (
    capture_artifact_baseline(
        scene
    )
)

primary_entry = next(
    entry
    for entry
    in dust_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == material.name
    )
)

user_entry = next(
    entry
    for entry
    in dust_baseline[
        "materials"
    ]
    if (
        entry[
            "material"
        ].name
        == user_material.name
    )
)

assert len(
    primary_entry[
        "nodes"
    ]
) == 1

assert len(
    user_entry[
        "nodes"
    ]
) == 0


# =========================================================
# Helper: create existing chain, then apply Dust directly.
# =========================================================

def run_case(
    *,
    fingerprints,
    condensation,
    frost,
    expected_mode,
    frame_seed,
):
    configure_engine(
        project,
        fingerprints=fingerprints,
        condensation=condensation,
        frost=frost,
    )

    existing_result = apply_artifacts(
        scene=scene,
        project_settings=project,
        frame_seed=frame_seed,
        baseline=engine_baseline,
    )

    (
        artifact_seed,
        _config,
        context,
    ) = dust_context(
        frame_seed
    )

    metadata = dust_provider.apply(
        scene=scene,
        context=context,
        baseline=dust_baseline,
    )

    change, node_change = (
        dust_change(
            metadata
        )
    )

    assert (
        node_change[
            "input_mode"
        ]
        == expected_mode
    )

    assert (
        source_node(
            roughness
        ).name.startswith(
            "BVT Dust Roughness Mix"
        )
    )

    dust_images = images_with_prefix(
        "BVT_Dust_"
    )

    assert len(
        dust_images
    ) == 1

    image_hash = alpha_hash(
        dust_images[0]
    )

    expected_material_seed = (
        derive_subseed(
            artifact_seed,
            "artifact-dust",
            material.name_full,
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
        metadata[
            "parameters"
        ][
            "mask_resolution"
        ]
        == DUST_MASK_RESOLUTION
    )

    assert abs(
        metadata[
            "parameters"
        ][
            "roughness_delta"
        ]
        - DUST_ROUGHNESS_DELTA
    ) < 1e-12

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

    # User graph remains untouched.
    assert user_roughness.is_linked

    assert (
        source_node(
            user_roughness
        ).as_pointer()
        == user_source_pointer
    )

    return {
        "existing_result": (
            existing_result
        ),
        "artifact_seed": (
            artifact_seed
        ),
        "metadata": metadata,
        "change": change,
        "node_change": (
            node_change
        ),
        "image_hash": (
            image_hash
        ),
    }


def reset_dust_and_check_upstream(
    expected_mode,
):
    dust_provider.reset(
        scene,
        dust_baseline,
    )

    assert not images_with_prefix(
        "BVT_Dust_"
    )

    assert not nodes_with_prefix(
        material,
        "BVT Dust",
    )

    if expected_mode == "constant":
        assert not roughness.is_linked

    else:
        upstream = source_node(
            roughness
        )

        prefixes = {
            "fingerprints": (
                "BVT Fingerprints Roughness Mix"
            ),
            "condensation": (
                "BVT Condensation Roughness Mix"
            ),
            "frost": (
                "BVT Frost Roughness Mix"
            ),
        }

        assert upstream.name.startswith(
            prefixes[
                expected_mode
            ]
        )


def reset_existing_chain():
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
    ) < 1e-6

    assert user_roughness.is_linked

    assert (
        source_node(
            user_roughness
        ).as_pointer()
        == user_source_pointer
    )


# =========================================================
# Case 1: full existing GLASS chain -> Frost -> Dust.
# =========================================================

frame_seed = derive_frame_seed(
    12345,
    1,
)

first = run_case(
    fingerprints=True,
    condensation=True,
    frost=True,
    expected_mode="frost",
    frame_seed=frame_seed,
)

existing_order = [
    item[
        "artifact"
    ]
    for item
    in first[
        "existing_result"
    ][
        "artifacts"
    ]
]

EXPECTED_EXISTING_ORDER = [
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
    existing_order
    == EXPECTED_EXISTING_ORDER
)

first_metadata = (
    first[
        "metadata"
    ]
)

first_hash = (
    first[
        "image_hash"
    ]
)

first_material_seed = (
    first[
        "change"
    ][
        "material_seed"
    ]
)

first_particle_seed = (
    first[
        "change"
    ][
        "particle_seed"
    ]
)

first_cluster_seed = (
    first[
        "change"
    ][
        "cluster_seed"
    ]
)

first_coverage = (
    first[
        "change"
    ][
        "coverage"
    ]
)

reset_dust_and_check_upstream(
    "frost"
)


# =========================================================
# Same seed -> exact same Dust metadata + mask.
# Existing Frost chain remains in place.
# =========================================================

(
    same_artifact_seed,
    _same_config,
    same_context,
) = dust_context(
    frame_seed
)

same_metadata = (
    dust_provider.apply(
        scene=scene,
        context=same_context,
        baseline=dust_baseline,
    )
)

same_change, same_node_change = (
    dust_change(
        same_metadata
    )
)

same_images = images_with_prefix(
    "BVT_Dust_"
)

assert len(same_images) == 1

same_hash = alpha_hash(
    same_images[0]
)

assert (
    same_artifact_seed
    == first[
        "artifact_seed"
    ]
)

assert (
    same_metadata
    == first_metadata
)

assert (
    same_hash
    == first_hash
)

assert (
    same_node_change[
        "input_mode"
    ]
    == "frost"
)

reset_dust_and_check_upstream(
    "frost"
)


# =========================================================
# Different frame seed -> different Dust seeds and mask.
# =========================================================

different_frame_seed = (
    derive_frame_seed(
        12345,
        2,
    )
)

(
    different_artifact_seed,
    _different_config,
    different_context,
) = dust_context(
    different_frame_seed
)

different_metadata = (
    dust_provider.apply(
        scene=scene,
        context=different_context,
        baseline=dust_baseline,
    )
)

different_change, different_node_change = (
    dust_change(
        different_metadata
    )
)

different_images = images_with_prefix(
    "BVT_Dust_"
)

assert len(
    different_images
) == 1

different_hash = alpha_hash(
    different_images[0]
)

assert (
    different_artifact_seed
    != first[
        "artifact_seed"
    ]
)

assert (
    different_change[
        "material_seed"
    ]
    != first_material_seed
)

assert (
    different_change[
        "particle_seed"
    ]
    != first_particle_seed
)

assert (
    different_change[
        "cluster_seed"
    ]
    != first_cluster_seed
)

assert (
    different_hash
    != first_hash
)

assert (
    different_node_change[
        "input_mode"
    ]
    == "frost"
)

reset_dust_and_check_upstream(
    "frost"
)

reset_existing_chain()


# =========================================================
# Case 2: Condensation is immediate upstream.
# =========================================================

condensation_case = run_case(
    fingerprints=True,
    condensation=True,
    frost=False,
    expected_mode="condensation",
    frame_seed=frame_seed,
)

assert (
    condensation_case[
        "node_change"
    ][
        "upstream_node"
    ].startswith(
        "BVT Condensation Roughness Mix"
    )
)

reset_dust_and_check_upstream(
    "condensation"
)

reset_existing_chain()


# =========================================================
# Case 3: Fingerprints is immediate upstream.
# =========================================================

fingerprints_case = run_case(
    fingerprints=True,
    condensation=False,
    frost=False,
    expected_mode="fingerprints",
    frame_seed=frame_seed,
)

assert (
    fingerprints_case[
        "node_change"
    ][
        "upstream_node"
    ].startswith(
        "BVT Fingerprints Roughness Mix"
    )
)

reset_dust_and_check_upstream(
    "fingerprints"
)

reset_existing_chain()


# =========================================================
# Case 4: Reflection only -> constant Roughness input.
# =========================================================

constant_case = run_case(
    fingerprints=False,
    condensation=False,
    frost=False,
    expected_mode="constant",
    frame_seed=frame_seed,
)

assert (
    constant_case[
        "node_change"
    ][
        "upstream_node"
    ]
    is None
)

reset_dust_and_check_upstream(
    "constant"
)

reset_existing_chain()


# =========================================================
# Final cleanup contract.
# =========================================================

temporary_dust_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Dust",
    )
)

temporary_dust_images = len(
    images_with_prefix(
        "BVT_Dust_"
    )
)

temporary_fingerprint_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Fingerprints",
    )
)

temporary_condensation_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Condensation",
    )
)

temporary_frost_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Frost",
    )
)

temporary_fingerprint_images = len(
    images_with_prefix(
        "BVT_Fingerprint_"
    )
)

temporary_condensation_images = len(
    images_with_prefix(
        "BVT_Condensation_"
    )
)

temporary_frost_images = len(
    images_with_prefix(
        "BVT_Frost_"
    )
)

assert temporary_dust_nodes == 0
assert temporary_dust_images == 0

assert temporary_fingerprint_nodes == 0
assert temporary_condensation_nodes == 0
assert temporary_frost_nodes == 0

assert temporary_fingerprint_images == 0
assert temporary_condensation_images == 0
assert temporary_frost_images == 0

assert not roughness.is_linked

assert abs(
    float(
        roughness.default_value
    )
    - BASE_ROUGHNESS
) < 1e-6

assert user_roughness.is_linked

assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


print(
    "BVT_DUST_LIFECYCLE_SMOKE=OK"
)

print(
    "existing_artifact_order=",
    existing_order,
)

print(
    "dust_seed=",
    first[
        "artifact_seed"
    ],
)

print(
    "material_seed=",
    first_material_seed,
)

print(
    "particle_seed=",
    first_particle_seed,
)

print(
    "cluster_seed=",
    first_cluster_seed,
)

print(
    "coverage=",
    first_coverage,
)

print(
    "input_mode_frost=True"
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
    same_hash == first_hash,
)

print(
    "different_seed_mask_changed=",
    different_hash != first_hash,
)

print(
    "user_shader_link_preserved=True"
)

print(
    "roughness_restored=",
    roughness.default_value,
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
    "temporary_frost_nodes_after_reset=",
    temporary_frost_nodes,
)

print(
    "temporary_condensation_nodes_after_reset=",
    temporary_condensation_nodes,
)

print(
    "temporary_fingerprint_nodes_after_reset=",
    temporary_fingerprint_nodes,
)

print(
    "BVT_DUST_LIFECYCLE_CLEANUP=OK"
)

bvt.unregister()
