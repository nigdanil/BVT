import math
import random

import bpy

from ...core.seeding import derive_subseed
from ...materials import get_materials_by_role
from ...materials import MATERIAL_ROLE_GLASS
from ..base import ArtifactProvider


FROST_MASK_RESOLUTION = 256
FROST_ROUGHNESS_DELTA = 0.80

FROST_CRYSTAL_COUNT = 18


_SUPPORTED_NODE_TYPES = frozenset(
    {
        "BSDF_PRINCIPLED",
        "BSDF_GLASS",
    }
)


def _clamp(
    value,
    minimum=0.0,
    maximum=1.0,
):
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _roughness_nodes(
    material,
):
    if (
        not material.use_nodes
        or material.node_tree is None
    ):
        return ()

    result = []

    for node in material.node_tree.nodes:
        if (
            node.type
            not in _SUPPORTED_NODE_TYPES
        ):
            continue

        socket = node.inputs.get(
            "Roughness"
        )

        if socket is None:
            continue

        # Capture only a clean template socket.
        # Existing user shader graphs must not
        # become owned by BVT.
        if socket.is_linked:
            continue

        result.append(
            (
                node,
                socket,
            )
        )

    result.sort(
        key=lambda pair: (
            pair[0].name
        )
    )

    return tuple(
        result
    )


def _sample_crystals(
    seed,
):
    rng = random.Random(
        seed
    )

    crystals = []

    for index in range(
        FROST_CRYSTAL_COUNT
    ):
        crystals.append(
            {
                "index": index,
                "center_u": rng.uniform(
                    0.02,
                    0.98,
                ),
                "center_v": rng.uniform(
                    0.02,
                    0.98,
                ),
                "radius": rng.uniform(
                    0.055,
                    0.18,
                ),
                "rotation": rng.uniform(
                    0.0,
                    math.tau,
                ),
                "arms": rng.randint(
                    5,
                    8,
                ),
                "amplitude": rng.uniform(
                    0.45,
                    0.95,
                ),
                "branch_frequency": rng.uniform(
                    7.0,
                    15.0,
                ),
                "branch_phase": rng.uniform(
                    0.0,
                    math.tau,
                ),
            }
        )

    return tuple(
        crystals
    )


def _crystal_value(
    u,
    v,
    crystal,
):
    du = (
        u
        - crystal[
            "center_u"
        ]
    )

    dv = (
        v
        - crystal[
            "center_v"
        ]
    )

    radius = math.sqrt(
        du * du
        + dv * dv
    )

    configured_radius = (
        crystal[
            "radius"
        ]
    )

    normalized_radius = (
        radius
        / configured_radius
    )

    if normalized_radius >= 1.6:
        return 0.0

    angle = (
        math.atan2(
            dv,
            du,
        )
        - crystal[
            "rotation"
        ]
    )

    arms = crystal[
        "arms"
    ]

    # Primary crystalline spokes.
    primary_distance = abs(
        math.sin(
            arms
            * angle
        )
    )

    primary = math.exp(
        -42.0
        * primary_distance
        * primary_distance
    )

    # Short secondary branching structures.
    branch_wave = abs(
        math.sin(
            crystal[
                "branch_frequency"
            ]
            * normalized_radius
            + crystal[
                "branch_phase"
            ]
            + 2.0
            * angle
        )
    )

    secondary = (
        math.exp(
            -22.0
            * primary_distance
            * primary_distance
        )
        * (
            branch_wave
            ** 5.0
        )
    )

    center = math.exp(
        -8.0
        * normalized_radius
        * normalized_radius
    )

    radial_falloff = _clamp(
        1.0
        - (
            normalized_radius
            / 1.6
        )
    )

    value = (
        0.68
        * primary
        + 0.22
        * secondary
        + 0.10
        * center
    )

    value *= (
        radial_falloff
        * crystal[
            "amplitude"
        ]
    )

    return _clamp(
        value
    )


def _build_mask(
    seed,
    resolution,
):
    crystal_seed = derive_subseed(
        seed,
        "frost-mask",
        "crystals",
    )

    texture_seed = derive_subseed(
        seed,
        "frost-mask",
        "texture",
    )

    crystals = _sample_crystals(
        crystal_seed
    )

    texture_rng = random.Random(
        texture_seed
    )

    frequency_u = texture_rng.uniform(
        15.0,
        27.0,
    )

    frequency_v = texture_rng.uniform(
        17.0,
        31.0,
    )

    phase_u = texture_rng.uniform(
        0.0,
        math.tau,
    )

    phase_v = texture_rng.uniform(
        0.0,
        math.tau,
    )

    pixels = []

    covered_pixels = 0
    total_value = 0.0

    for y in range(
        resolution
    ):
        v = (
            y + 0.5
        ) / resolution

        for x in range(
            resolution
        ):
            u = (
                x + 0.5
            ) / resolution

            frost = 0.0

            for crystal in crystals:
                contribution = (
                    _crystal_value(
                        u,
                        v,
                        crystal,
                    )
                )

                # Soft union of overlapping
                # crystalline structures.
                frost = (
                    1.0
                    - (
                        1.0
                        - frost
                    )
                    * (
                        1.0
                        - contribution
                    )
                )

            micro = (
                0.5
                + 0.5
                * math.sin(
                    math.tau
                    * frequency_u
                    * u
                    + phase_u
                )
                * math.sin(
                    math.tau
                    * frequency_v
                    * v
                    + phase_v
                )
            )

            # Crystalline structure remains dominant.
            # High-frequency variation prevents the mask
            # from looking like a smooth condensation map.
            value = frost * (
                0.78
                + 0.22
                * micro
            )

            value = _clamp(
                value
            )

            if value > 0.08:
                covered_pixels += 1

            total_value += value

            # RGB is white; Alpha stores frost mask.
            pixels.extend(
                (
                    1.0,
                    1.0,
                    1.0,
                    value,
                )
            )

    pixel_count = (
        resolution
        * resolution
    )

    return {
        "pixels": pixels,
        "crystals": crystals,
        "coverage": (
            covered_pixels
            / float(
                pixel_count
            )
        ),
        "mean_mask_value": (
            total_value
            / float(
                pixel_count
            )
        ),
        "crystal_seed": (
            crystal_seed
        ),
        "texture_seed": (
            texture_seed
        ),
        "texture_frequency_u": (
            frequency_u
        ),
        "texture_frequency_v": (
            frequency_v
        ),
        "texture_phase_u": (
            phase_u
        ),
        "texture_phase_v": (
            phase_v
        ),
    }


def _create_mask_image(
    name,
    mask,
    resolution,
):
    image = bpy.data.images.new(
        name=name,
        width=resolution,
        height=resolution,
        alpha=True,
        float_buffer=False,
    )

    image.pixels[:] = (
        mask[
            "pixels"
        ]
    )

    image.update()

    return image


def _bvt_upstream(
    socket,
):
    if not socket.is_linked:
        return None

    if len(
        socket.links
    ) != 1:
        return None

    link = socket.links[
        0
    ]

    node = link.from_node
    name = str(
        node.name
    )

    if name.startswith(
        "BVT Condensation Roughness Mix"
    ):
        input_mode = (
            "condensation"
        )

    elif name.startswith(
        "BVT Fingerprints Roughness Mix"
    ):
        input_mode = (
            "fingerprints"
        )

    else:
        return None

    return {
        "link": link,
        "socket": (
            link.from_socket
        ),
        "node": node,
        "input_mode": (
            input_mode
        ),
    }


class FrostArtifactProvider(
    ArtifactProvider
):
    artifact_id = "frost"
    category = "glass"
    stage = "pre_render"
    execution_order = 130

    description = (
        "Adds deterministic crystalline frost "
        "to BVT glass materials"
    )

    def capture(
        self,
        scene,
    ):
        materials = []

        for material in get_materials_by_role(
            scene,
            MATERIAL_ROLE_GLASS,
        ):
            nodes = []

            for node, socket in _roughness_nodes(
                material
            ):
                nodes.append(
                    {
                        "node": node,
                        "socket": socket,
                        "base_roughness": float(
                            socket.default_value
                        ),
                    }
                )

            materials.append(
                {
                    "material": material,
                    "nodes": nodes,
                }
            )

        return {
            "materials": materials,
            "runtime": [],
        }

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        effective_strength = (
            context.config.intensity
        )

        affected_materials = []
        material_changes = []

        total_coverage = 0.0
        total_mean_mask = 0.0

        for (
            material_index,
            material_entry,
        ) in enumerate(
            baseline[
                "materials"
            ]
        ):
            material = material_entry[
                "material"
            ]

            active_nodes = []

            for node_entry in material_entry[
                "nodes"
            ]:
                socket = node_entry[
                    "socket"
                ]

                upstream = _bvt_upstream(
                    socket
                )

                if socket.is_linked:
                    if upstream is None:
                        # Arbitrary user shader graph:
                        # never replace it.
                        continue

                    input_mode = upstream[
                        "input_mode"
                    ]

                else:
                    input_mode = (
                        "constant"
                    )

                active_nodes.append(
                    {
                        "node_entry": (
                            node_entry
                        ),
                        "upstream": (
                            upstream
                        ),
                        "input_mode": (
                            input_mode
                        ),
                    }
                )

            if not active_nodes:
                continue

            material_seed = derive_subseed(
                context.artifact_seed,
                "artifact-frost",
                material.name_full,
            )

            mask = _build_mask(
                seed=material_seed,
                resolution=(
                    FROST_MASK_RESOLUTION
                ),
            )

            image = _create_mask_image(
                name=(
                    "BVT_Frost_"
                    f"{context.artifact_seed}_"
                    f"{material_index}"
                ),
                mask=mask,
                resolution=(
                    FROST_MASK_RESOLUTION
                ),
            )

            tree = material.node_tree

            texcoord = tree.nodes.new(
                "ShaderNodeTexCoord"
            )

            texcoord.name = (
                "BVT Frost Coordinates"
            )

            texture = tree.nodes.new(
                "ShaderNodeTexImage"
            )

            texture.name = (
                "BVT Frost Mask"
            )

            texture.image = image
            texture.interpolation = "Linear"
            texture.extension = "CLIP"

            if hasattr(
                texture,
                "projection",
            ):
                texture.projection = "BOX"

            if hasattr(
                texture,
                "projection_blend",
            ):
                texture.projection_blend = (
                    0.12
                )

            strength = tree.nodes.new(
                "ShaderNodeMath"
            )

            strength.name = (
                "BVT Frost Strength"
            )

            strength.operation = (
                "MULTIPLY"
            )

            strength.inputs[
                1
            ].default_value = (
                effective_strength
            )

            delta = tree.nodes.new(
                "ShaderNodeMath"
            )

            delta.name = (
                "BVT Frost Roughness Delta"
            )

            delta.operation = (
                "MULTIPLY"
            )

            delta.inputs[
                1
            ].default_value = (
                FROST_ROUGHNESS_DELTA
            )

            created_nodes = [
                texcoord,
                texture,
                strength,
                delta,
            ]

            runtime = {
                "material": material,
                "node_tree": tree,
                "nodes": (
                    created_nodes
                ),
                "image": image,
                "connections": [],
            }

            # Register immediately so reset also works
            # after a partial apply failure.
            baseline[
                "runtime"
            ].append(
                runtime
            )

            tree.links.new(
                texcoord.outputs[
                    "Generated"
                ],
                texture.inputs[
                    "Vector"
                ],
            )

            tree.links.new(
                texture.outputs[
                    "Alpha"
                ],
                strength.inputs[
                    0
                ],
            )

            tree.links.new(
                strength.outputs[
                    0
                ],
                delta.inputs[
                    0
                ],
            )

            node_changes = []

            for active in active_nodes:
                node_entry = active[
                    "node_entry"
                ]

                node = node_entry[
                    "node"
                ]

                socket = node_entry[
                    "socket"
                ]

                upstream = active[
                    "upstream"
                ]

                input_mode = active[
                    "input_mode"
                ]

                input_roughness = float(
                    socket.default_value
                )

                upstream_socket = None
                upstream_node_name = None

                if upstream is not None:
                    upstream_socket = (
                        upstream[
                            "socket"
                        ]
                    )

                    upstream_node_name = str(
                        upstream[
                            "node"
                        ].name
                    )

                    tree.links.remove(
                        upstream[
                            "link"
                        ]
                    )

                mix = tree.nodes.new(
                    "ShaderNodeMath"
                )

                mix.name = (
                    "BVT Frost Roughness Mix "
                    f"{node.name}"
                )

                mix.operation = "ADD"

                if hasattr(
                    mix,
                    "use_clamp",
                ):
                    mix.use_clamp = True

                if upstream_socket is None:
                    mix.inputs[
                        0
                    ].default_value = (
                        input_roughness
                    )

                else:
                    tree.links.new(
                        upstream_socket,
                        mix.inputs[
                            0
                        ],
                    )

                tree.links.new(
                    delta.outputs[
                        0
                    ],
                    mix.inputs[
                        1
                    ],
                )

                tree.links.new(
                    mix.outputs[
                        0
                    ],
                    socket,
                )

                created_nodes.append(
                    mix
                )

                runtime[
                    "connections"
                ].append(
                    {
                        "socket": socket,
                        "input_roughness": (
                            input_roughness
                        ),
                        "upstream_socket": (
                            upstream_socket
                        ),
                    }
                )

                node_changes.append(
                    {
                        "node": node.name,
                        "base_roughness": (
                            node_entry[
                                "base_roughness"
                            ]
                        ),
                        "input_mode": (
                            input_mode
                        ),
                        "input_roughness": (
                            input_roughness
                        ),
                        "upstream_node": (
                            upstream_node_name
                        ),
                        "roughness_delta": (
                            FROST_ROUGHNESS_DELTA
                        ),
                    }
                )

            affected_materials.append(
                material.name_full
            )

            total_coverage += (
                mask[
                    "coverage"
                ]
            )

            total_mean_mask += (
                mask[
                    "mean_mask_value"
                ]
            )

            material_changes.append(
                {
                    "material": (
                        material.name_full
                    ),
                    "material_seed": (
                        material_seed
                    ),
                    "coverage": (
                        mask[
                            "coverage"
                        ]
                    ),
                    "mean_mask_value": (
                        mask[
                            "mean_mask_value"
                        ]
                    ),
                    "crystal_seed": (
                        mask[
                            "crystal_seed"
                        ]
                    ),
                    "texture_seed": (
                        mask[
                            "texture_seed"
                        ]
                    ),
                    "nodes": (
                        node_changes
                    ),
                }
            )

        affected_materials.sort()

        mean_coverage = 0.0
        mean_mask_value = 0.0

        if material_changes:
            count = len(
                material_changes
            )

            mean_coverage = (
                total_coverage
                / count
            )

            mean_mask_value = (
                total_mean_mask
                / count
            )

        return {
            "affected_objects": [],
            "affected_camera": None,
            "affected_materials": (
                affected_materials
            ),
            "parameters": {
                "target_role": (
                    MATERIAL_ROLE_GLASS
                ),
                "mask_resolution": (
                    FROST_MASK_RESOLUTION
                ),
                "roughness_delta": (
                    FROST_ROUGHNESS_DELTA
                ),
                "effective_strength": (
                    effective_strength
                ),
                "crystal_count": (
                    FROST_CRYSTAL_COUNT
                ),
                "mean_coverage": (
                    mean_coverage
                ),
                "mean_mask_value": (
                    mean_mask_value
                ),
                "material_changes": (
                    material_changes
                ),
            },
        }

    def reset(
        self,
        scene,
        baseline,
    ):
        for runtime in reversed(
            baseline.get(
                "runtime",
                [],
            )
        ):
            tree = runtime[
                "node_tree"
            ]

            connections = runtime.get(
                "connections",
                [],
            )

            # Removing Frost nodes disconnects the
            # temporary Frost chain from Roughness.
            for node in reversed(
                runtime[
                    "nodes"
                ]
            ):
                try:
                    tree.nodes.remove(
                        node
                    )
                except ReferenceError:
                    pass

            # Restore exactly the state that existed
            # immediately before Frost was applied.
            for connection in connections:
                socket = connection[
                    "socket"
                ]

                if socket.is_linked:
                    continue

                upstream_socket = connection[
                    "upstream_socket"
                ]

                if upstream_socket is None:
                    socket.default_value = (
                        connection[
                            "input_roughness"
                        ]
                    )

                else:
                    try:
                        tree.links.new(
                            upstream_socket,
                            socket,
                        )
                    except ReferenceError:
                        pass

            image = runtime[
                "image"
            ]

            try:
                if (
                    bpy.data.images.get(
                        image.name
                    )
                    is image
                ):
                    bpy.data.images.remove(
                        image
                    )
            except ReferenceError:
                pass

        baseline[
            "runtime"
        ] = []

    def compatibility_rules(
        self,
    ):
        return (
            "targets_material_role_glass",
            "supports_principled_and_glass_bsdf",
            (
                "accepts_clean_or_bvt_fingerprints_"
                "or_condensation_roughness_input"
            ),
            "preserves_user_shader_links",
            "compatible_with_reflection",
            "compatible_with_fingerprints",
            "compatible_with_condensation",
            "uses_temporary_shader_nodes",
            "procedural_mask_no_external_assets",
        )
