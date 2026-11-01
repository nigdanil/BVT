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
from bvt.artifacts.providers.water_drops import (
    WATER_DROPS_WET_ROUGHNESS,
    WaterDropsArtifactProvider,
)
from bvt.artifacts.providers.water_drops_mask import (
    WATER_DROPS_COUNT,
    WATER_DROPS_MASK_RESOLUTION,
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
WATER_INTENSITY = 1.0


def alpha_hash(image):
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
                float(pixels[index]),
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


def source_node(socket):
    assert socket.is_linked
    assert len(socket.links) == 1

    return socket.links[
        0
    ].from_node


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


def images_with_prefix(prefix):
    return [
        image
        for image
        in bpy.data.images
        if image.name.startswith(
            prefix
        )
    ]


def configure_engine(
    project,
    *,
    fingerprints,
    condensation,
    frost,
    dust,
):
    project.artifact_engine_enabled = True

    project.artifact_over_exposure_enabled = False

    project.artifact_reflection_enabled = True
    project.artifact_reflection_probability = 1.0
    project.artifact_reflection_intensity = 0.75
    project.artifact_reflection_min_roughness = 0.02

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

    project.artifact_dust_enabled = dust
    project.artifact_dust_probability = 1.0
    project.artifact_dust_intensity = 0.70

    project.artifact_water_drops_enabled = False
    project.artifact_scratches_enabled = False
    project.artifact_motion_blur_enabled = False
    project.artifact_noise_enabled = False
    project.artifact_jpeg_enabled = False


def water_context(frame_seed):
    artifact_seed = derive_subseed(
        frame_seed,
        "artifact",
        "water_drops",
    )

    config = ArtifactConfig(
        artifact_id="water_drops",
        enabled=True,
        probability=1.0,
        intensity=WATER_INTENSITY,
    )

    context = ArtifactContext(
        config=config,
        frame_seed=frame_seed,
        artifact_seed=artifact_seed,
        decision_roll=0.0,
    )

    return (
        artifact_seed,
        context,
    )


def water_change(metadata):
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
    "BVT_Water_Drops_Glass"
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

normal_socket = principled.inputs[
    "Normal"
]

normal_was_linked = (
    normal_socket.is_linked
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
# Water Drops must never replace it.
# =========================================================

user_material = bpy.data.materials.new(
    "BVT_Water_Drops_User_Link_Glass"
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
# Water baseline is captured while primary Roughness
# is clean and the user material is already linked.
# =========================================================

provider = (
    WaterDropsArtifactProvider()
)

water_baseline = provider.capture(
    scene
)

engine_baseline = (
    capture_artifact_baseline(
        scene
    )
)

primary_entry = next(
    entry
    for entry
    in water_baseline[
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
    in water_baseline[
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


def run_case(
    *,
    fingerprints,
    condensation,
    frost,
    dust,
    expected_mode,
    frame_seed,
):
    configure_engine(
        project,
        fingerprints=fingerprints,
        condensation=condensation,
        frost=frost,
        dust=dust,
    )

    existing_result = apply_artifacts(
        scene=scene,
        project_settings=project,
        frame_seed=frame_seed,
        baseline=engine_baseline,
    )

    artifact_seed, context = (
        water_context(
            frame_seed
        )
    )

    metadata = provider.apply(
        scene=scene,
        context=context,
        baseline=water_baseline,
    )

    change, node_change = (
        water_change(
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
            "BVT Water Drops Roughness Mix"
        )
    )

    images = images_with_prefix(
        "BVT_Water_Drops_"
    )

    assert len(images) == 1

    image_hash = alpha_hash(
        images[0]
    )

    expected_material_seed = (
        derive_subseed(
            artifact_seed,
            "artifact-water-drops",
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
            "drop_count"
        ]
        == WATER_DROPS_COUNT
    )

    assert (
        metadata[
            "parameters"
        ][
            "mask_resolution"
        ]
        == WATER_DROPS_MASK_RESOLUTION
    )

    assert abs(
        metadata[
            "parameters"
        ][
            "wet_roughness"
        ]
        - WATER_DROPS_WET_ROUGHNESS
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

    assert (
        normal_socket.is_linked
        == normal_was_linked
    )

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


def reset_water_and_check_upstream(
    expected_mode,
):
    provider.reset(
        scene,
        water_baseline,
    )

    assert not images_with_prefix(
        "BVT_Water_Drops_"
    )

    assert not nodes_with_prefix(
        material,
        "BVT Water Drops",
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
            "dust": (
                "BVT Dust Roughness Mix"
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
# Case 1:
# Reflection -> Fingerprints -> Condensation -> Frost
# -> Dust -> Water Drops
# =========================================================

frame_seed = derive_frame_seed(
    12345,
    1,
)

first = run_case(
    fingerprints=True,
    condensation=True,
    frost=True,
    dust=True,
    expected_mode="dust",
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
    "water_drops",
    "scratches",
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

first_layout_seed = (
    first[
        "change"
    ][
        "layout_seed"
    ]
)

first_shape_seed = (
    first[
        "change"
    ][
        "shape_seed"
    ]
)

first_coverage = (
    first[
        "change"
    ][
        "coverage"
    ]
)

reset_water_and_check_upstream(
    "dust"
)


# =========================================================
# Same seed -> exact same Water metadata + mask.
# =========================================================

same_artifact_seed, same_context = (
    water_context(
        frame_seed
    )
)

same_metadata = provider.apply(
    scene=scene,
    context=same_context,
    baseline=water_baseline,
)

same_change, same_node_change = (
    water_change(
        same_metadata
    )
)

same_images = images_with_prefix(
    "BVT_Water_Drops_"
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
    == "dust"
)

reset_water_and_check_upstream(
    "dust"
)


# =========================================================
# Different seed -> different Water seeds + mask.
# =========================================================

different_frame_seed = (
    derive_frame_seed(
        12345,
        2,
    )
)

different_artifact_seed, different_context = (
    water_context(
        different_frame_seed
    )
)

different_metadata = provider.apply(
    scene=scene,
    context=different_context,
    baseline=water_baseline,
)

different_change, different_node_change = (
    water_change(
        different_metadata
    )
)

different_images = images_with_prefix(
    "BVT_Water_Drops_"
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
        "layout_seed"
    ]
    != first_layout_seed
)

assert (
    different_change[
        "shape_seed"
    ]
    != first_shape_seed
)

assert (
    different_hash
    != first_hash
)

assert (
    different_node_change[
        "input_mode"
    ]
    == "dust"
)

reset_water_and_check_upstream(
    "dust"
)

reset_existing_chain()


# =========================================================
# Case 2: Frost is immediate upstream.
# =========================================================

frost_case = run_case(
    fingerprints=True,
    condensation=True,
    frost=True,
    dust=False,
    expected_mode="frost",
    frame_seed=frame_seed,
)

assert (
    frost_case[
        "node_change"
    ][
        "upstream_node"
    ].startswith(
        "BVT Frost Roughness Mix"
    )
)

reset_water_and_check_upstream(
    "frost"
)

reset_existing_chain()


# =========================================================
# Case 3: Condensation is immediate upstream.
# =========================================================

condensation_case = run_case(
    fingerprints=True,
    condensation=True,
    frost=False,
    dust=False,
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

reset_water_and_check_upstream(
    "condensation"
)

reset_existing_chain()


# =========================================================
# Case 4: Fingerprints is immediate upstream.
# =========================================================

fingerprints_case = run_case(
    fingerprints=True,
    condensation=False,
    frost=False,
    dust=False,
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

reset_water_and_check_upstream(
    "fingerprints"
)

reset_existing_chain()


# =========================================================
# Case 5: Reflection only -> constant Roughness input.
# =========================================================

constant_case = run_case(
    fingerprints=False,
    condensation=False,
    frost=False,
    dust=False,
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

reset_water_and_check_upstream(
    "constant"
)

reset_existing_chain()


# =========================================================
# Final cleanup contract.
# =========================================================

temporary_water_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Water Drops",
    )
)

temporary_water_images = len(
    images_with_prefix(
        "BVT_Water_Drops_"
    )
)

temporary_dust_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Dust",
    )
)

temporary_frost_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Frost",
    )
)

temporary_condensation_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Condensation",
    )
)

temporary_fingerprint_nodes = len(
    nodes_with_prefix(
        material,
        "BVT Fingerprints",
    )
)


assert temporary_water_nodes == 0
assert temporary_water_images == 0

assert temporary_dust_nodes == 0
assert temporary_frost_nodes == 0
assert temporary_condensation_nodes == 0
assert temporary_fingerprint_nodes == 0

assert not roughness.is_linked

assert abs(
    float(
        roughness.default_value
    )
    - BASE_ROUGHNESS
) < 1e-6

assert (
    normal_socket.is_linked
    == normal_was_linked
)

assert user_roughness.is_linked

assert (
    source_node(
        user_roughness
    ).as_pointer()
    == user_source_pointer
)


print(
    "BVT_WATER_DROPS_LIFECYCLE_SMOKE=OK"
)

print(
    "existing_artifact_order=",
    existing_order,
)

print(
    "water_drops_seed=",
    first[
        "artifact_seed"
    ],
)

print(
    "material_seed=",
    first_material_seed,
)

print(
    "layout_seed=",
    first_layout_seed,
)

print(
    "shape_seed=",
    first_shape_seed,
)

print(
    "coverage=",
    first_coverage,
)

print(
    "wet_roughness=",
    WATER_DROPS_WET_ROUGHNESS,
)

print(
    "input_mode_dust=True"
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
    "normal_socket_untouched=True"
)

print(
    "roughness_restored=",
    roughness.default_value,
)

print(
    "temporary_water_nodes_after_reset=",
    temporary_water_nodes,
)

print(
    "temporary_water_images_after_reset=",
    temporary_water_images,
)

print(
    "BVT_WATER_DROPS_LIFECYCLE_CLEANUP=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()
