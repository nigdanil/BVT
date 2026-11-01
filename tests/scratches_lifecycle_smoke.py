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
from bvt.artifacts.providers.scratches import (
    SCRATCHES_ROUGHNESS_TARGET,
    ScratchesArtifactProvider,
)
from bvt.artifacts.providers.scratches_mask import (
    SCRATCHES_COUNT,
    SCRATCHES_MASK_RESOLUTION,
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
SCRATCHES_INTENSITY = 1.0


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
    water_drops,
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

    project.artifact_water_drops_enabled = (
        water_drops
    )
    project.artifact_water_drops_probability = 1.0
    project.artifact_water_drops_intensity = 0.80

    # Scratches is exercised manually by this lifecycle
    # smoke. Keep the Engine-owned instance disabled.
    project.artifact_scratches_enabled = False
    project.artifact_scratches_probability = 1.0
    project.artifact_scratches_intensity = 1.0

    project.artifact_motion_blur_enabled = False
    project.artifact_noise_enabled = False
    project.artifact_jpeg_enabled = False


def scratches_context(frame_seed):
    artifact_seed = derive_subseed(
        frame_seed,
        "artifact",
        "scratches",
    )

    config = ArtifactConfig(
        artifact_id="scratches",
        enabled=True,
        probability=1.0,
        intensity=SCRATCHES_INTENSITY,
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


def scratches_change(metadata):
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
    "BVT_Scratches_Glass"
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
# Scratches must preserve it.
# =========================================================

user_material = bpy.data.materials.new(
    "BVT_Scratches_User_Link_Glass"
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
# Capture clean Scratches baseline before any BVT chain.
# =========================================================

provider = ScratchesArtifactProvider()

scratches_baseline = provider.capture(
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
    in scratches_baseline[
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
    in scratches_baseline[
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


PREFIX_BY_MODE = {
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
    "water_drops": (
        "BVT Water Drops Roughness Mix"
    ),
}


def run_case(
    *,
    fingerprints,
    condensation,
    frost,
    dust,
    water_drops,
    expected_mode,
    frame_seed,
):
    configure_engine(
        project,
        fingerprints=fingerprints,
        condensation=condensation,
        frost=frost,
        dust=dust,
        water_drops=water_drops,
    )

    existing_result = apply_artifacts(
        scene=scene,
        project_settings=project,
        frame_seed=frame_seed,
        baseline=engine_baseline,
    )

    artifact_seed, context = (
        scratches_context(
            frame_seed
        )
    )

    metadata = provider.apply(
        scene=scene,
        context=context,
        baseline=scratches_baseline,
    )

    change, node_change = (
        scratches_change(
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
            "BVT Scratches Roughness Mix"
        )
    )

    if expected_mode == "constant":
        assert (
            node_change[
                "upstream_node"
            ]
            is None
        )

    else:
        assert (
            node_change[
                "upstream_node"
            ].startswith(
                PREFIX_BY_MODE[
                    expected_mode
                ]
            )
        )

    images = images_with_prefix(
        "BVT_Scratches_"
    )

    assert len(images) == 1

    image_hash = alpha_hash(
        images[0]
    )

    expected_material_seed = (
        derive_subseed(
            artifact_seed,
            "artifact-scratches",
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
            "scratch_count"
        ]
        == SCRATCHES_COUNT
    )

    parameters = metadata[
        "parameters"
    ]

    assert (
        parameters[
            "mask_resolution"
        ]
        == SCRATCHES_MASK_RESOLUTION
    )

    assert abs(
        parameters[
            "roughness_target"
        ]
        - SCRATCHES_ROUGHNESS_TARGET
    ) < 1e-12

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


def reset_scratches_and_check_upstream(
    expected_mode,
):
    provider.reset(
        scene,
        scratches_baseline,
    )

    assert not images_with_prefix(
        "BVT_Scratches_"
    )

    assert not nodes_with_prefix(
        material,
        "BVT Scratches",
    )

    if expected_mode == "constant":
        assert not roughness.is_linked

    else:
        assert (
            source_node(
                roughness
            ).name.startswith(
                PREFIX_BY_MODE[
                    expected_mode
                ]
            )
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


frame_seed = derive_frame_seed(
    12345,
    1,
)


# =========================================================
# Full Glass chain:
# Reflection -> Fingerprints -> Condensation -> Frost
# -> Dust -> Water Drops -> Scratches
# =========================================================

first = run_case(
    fingerprints=True,
    condensation=True,
    frost=True,
    dust=True,
    water_drops=True,
    expected_mode="water_drops",
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

first_metadata = first[
    "metadata"
]

first_hash = first[
    "image_hash"
]

first_material_seed = first[
    "change"
][
    "material_seed"
]

first_layout_seed = first[
    "change"
][
    "layout_seed"
]

first_shape_seed = first[
    "change"
][
    "shape_seed"
]

first_coverage = first[
    "change"
][
    "coverage"
]


reset_scratches_and_check_upstream(
    "water_drops"
)


# =========================================================
# Same seed -> identical metadata + mask.
# =========================================================

same_artifact_seed, same_context = (
    scratches_context(
        frame_seed
    )
)

same_metadata = provider.apply(
    scene=scene,
    context=same_context,
    baseline=scratches_baseline,
)

same_change, same_node_change = (
    scratches_change(
        same_metadata
    )
)

same_images = images_with_prefix(
    "BVT_Scratches_"
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
    == "water_drops"
)

reset_scratches_and_check_upstream(
    "water_drops"
)


# =========================================================
# Different seed -> different artifact/material/mask seeds.
# =========================================================

different_frame_seed = (
    derive_frame_seed(
        12345,
        2,
    )
)

different_artifact_seed, different_context = (
    scratches_context(
        different_frame_seed
    )
)

different_metadata = provider.apply(
    scene=scene,
    context=different_context,
    baseline=scratches_baseline,
)

different_change, different_node_change = (
    scratches_change(
        different_metadata
    )
)

different_images = images_with_prefix(
    "BVT_Scratches_"
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
    == "water_drops"
)

reset_scratches_and_check_upstream(
    "water_drops"
)

reset_existing_chain()


# =========================================================
# Remaining supported upstream modes.
# =========================================================

CASES = (
    {
        "name": "dust",
        "fingerprints": True,
        "condensation": True,
        "frost": True,
        "dust": True,
        "water_drops": False,
    },
    {
        "name": "frost",
        "fingerprints": True,
        "condensation": True,
        "frost": True,
        "dust": False,
        "water_drops": False,
    },
    {
        "name": "condensation",
        "fingerprints": True,
        "condensation": True,
        "frost": False,
        "dust": False,
        "water_drops": False,
    },
    {
        "name": "fingerprints",
        "fingerprints": True,
        "condensation": False,
        "frost": False,
        "dust": False,
        "water_drops": False,
    },
    {
        "name": "constant",
        "fingerprints": False,
        "condensation": False,
        "frost": False,
        "dust": False,
        "water_drops": False,
    },
)


verified_modes = [
    "water_drops"
]


for case in CASES:
    result = run_case(
        fingerprints=case[
            "fingerprints"
        ],
        condensation=case[
            "condensation"
        ],
        frost=case[
            "frost"
        ],
        dust=case[
            "dust"
        ],
        water_drops=case[
            "water_drops"
        ],
        expected_mode=case[
            "name"
        ],
        frame_seed=frame_seed,
    )

    verified_modes.append(
        result[
            "node_change"
        ][
            "input_mode"
        ]
    )

    reset_scratches_and_check_upstream(
        case[
            "name"
        ]
    )

    reset_existing_chain()


assert verified_modes == [
    "water_drops",
    "dust",
    "frost",
    "condensation",
    "fingerprints",
    "constant",
]


# =========================================================
# Final cleanup contract.
# =========================================================

assert not nodes_with_prefix(
    material,
    "BVT Scratches",
)

assert not images_with_prefix(
    "BVT_Scratches_"
)

for prefix in (
    "BVT Water Drops",
    "BVT Dust",
    "BVT Frost",
    "BVT Condensation",
    "BVT Fingerprints",
):
    assert not nodes_with_prefix(
        material,
        prefix,
    )


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


compatibility = (
    provider.compatibility_rules()
)

assert (
    "compatible_with_water_drops"
    in compatibility
)

assert (
    "normal_socket_untouched"
    in compatibility
)

assert (
    "procedural_mask_no_external_assets"
    in compatibility
)


print(
    "BVT_SCRATCHES_LIFECYCLE_SMOKE=OK"
)

print(
    "BVT_SCRATCHES_LIFECYCLE_CLEANUP=OK"
)

print(
    "verified_modes=",
    verified_modes,
)

print(
    "existing_artifact_order=",
    existing_order,
)

print(
    "scratches_seed=",
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
    "roughness_target=",
    SCRATCHES_ROUGHNESS_TARGET,
)

print(
    "scratch_count=",
    SCRATCHES_COUNT,
)

print(
    "same_seed_equal=",
    same_metadata
    == first_metadata,
)

print(
    "different_seed_changed=",
    different_hash
    != first_hash,
)

print(
    "RESULT=PASS"
)
