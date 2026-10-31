import bpy

from ...core.seeding import derive_subseed
from ...materials import get_materials_by_role
from ...materials import MATERIAL_ROLE_GLASS
from ..base import ArtifactProvider
from .water_drops_mask import build_water_drops_mask
from .water_drops_mask import WATER_DROPS_COUNT
from .water_drops_mask import WATER_DROPS_MASK_RESOLUTION


WATER_DROPS_WET_ROUGHNESS = 0.04


_SUPPORTED_NODE_TYPES = frozenset(
    {
        "BSDF_PRINCIPLED",
        "BSDF_GLASS",
    }
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

        # Capture only clean template sockets.
        # Arbitrary user shader graphs remain
        # outside BVT ownership.
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


def _bvt_upstream(
    socket,
):
    if not socket.is_linked:
        return None

    if len(
        socket.links
    ) != 1:
        return None

    link = socket.links[0]
    node = link.from_node

    name = str(
        node.name
    )

    if name.startswith(
        "BVT Dust Roughness Mix"
    ):
        input_mode = "dust"

    elif name.startswith(
        "BVT Frost Roughness Mix"
    ):
        input_mode = "frost"

    elif name.startswith(
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


def _create_mask_image(
    name,
    mask,
):
    image = bpy.data.images.new(
        name=name,
        width=(
            WATER_DROPS_MASK_RESOLUTION
        ),
        height=(
            WATER_DROPS_MASK_RESOLUTION
        ),
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


class WaterDropsArtifactProvider(
    ArtifactProvider
):
    artifact_id = "water_drops"
    category = "glass"
    stage = "pre_render"
    execution_order = 150

    description = (
        "Adds deterministic discrete water droplets "
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
                        # Preserve arbitrary user links.
                        continue

                    input_mode = (
                        upstream[
                            "input_mode"
                        ]
                    )

                else:
                    input_mode = (
                        "constant"
                    )

                active_nodes.append(
                    {
                        "node_entry": (
                            node_entry
                        ),
                        "upstream": upstream,
                        "input_mode": (
                            input_mode
                        ),
                    }
                )

            if not active_nodes:
                continue

            material_seed = derive_subseed(
                context.artifact_seed,
                "artifact-water-drops",
                material.name_full,
            )

            mask = build_water_drops_mask(
                material_seed,
                WATER_DROPS_MASK_RESOLUTION,
            )

            image = _create_mask_image(
                name=(
                    "BVT_Water_Drops_"
                    f"{context.artifact_seed}_"
                    f"{material_index}"
                ),
                mask=mask,
            )

            tree = material.node_tree

            texcoord = tree.nodes.new(
                "ShaderNodeTexCoord"
            )

            texcoord.name = (
                "BVT Water Drops Coordinates"
            )

            texture = tree.nodes.new(
                "ShaderNodeTexImage"
            )

            texture.name = (
                "BVT Water Drops Mask"
            )

            texture.image = image
            texture.interpolation = (
                "Linear"
            )
            texture.extension = "CLIP"

            if hasattr(
                texture,
                "projection",
            ):
                texture.projection = (
                    "BOX"
                )

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
                "BVT Water Drops Strength"
            )

            strength.operation = (
                "MULTIPLY"
            )

            strength.inputs[
                1
            ].default_value = (
                effective_strength
            )

            one_minus = tree.nodes.new(
                "ShaderNodeMath"
            )

            one_minus.name = (
                "BVT Water Drops One Minus"
            )

            one_minus.operation = (
                "SUBTRACT"
            )

            one_minus.inputs[
                0
            ].default_value = 1.0

            wet = tree.nodes.new(
                "ShaderNodeMath"
            )

            wet.name = (
                "BVT Water Drops Wet Roughness"
            )

            wet.operation = (
                "MULTIPLY"
            )

            wet.inputs[
                1
            ].default_value = (
                WATER_DROPS_WET_ROUGHNESS
            )

            created_nodes = [
                texcoord,
                texture,
                strength,
                one_minus,
                wet,
            ]

            runtime = {
                "material": material,
                "node_tree": tree,
                "nodes": created_nodes,
                "image": image,
                "connections": [],
            }

            # Register immediately so reset remains
            # possible after a partial apply failure.
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
                one_minus.inputs[
                    1
                ],
            )

            tree.links.new(
                strength.outputs[
                    0
                ],
                wet.inputs[
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

                base = tree.nodes.new(
                    "ShaderNodeMath"
                )

                base.name = (
                    "BVT Water Drops Base Roughness "
                    f"{node.name}"
                )

                base.operation = (
                    "MULTIPLY"
                )

                if upstream_socket is None:
                    base.inputs[
                        0
                    ].default_value = (
                        input_roughness
                    )

                else:
                    tree.links.new(
                        upstream_socket,
                        base.inputs[
                            0
                        ],
                    )

                tree.links.new(
                    one_minus.outputs[
                        0
                    ],
                    base.inputs[
                        1
                    ],
                )

                mix = tree.nodes.new(
                    "ShaderNodeMath"
                )

                mix.name = (
                    "BVT Water Drops Roughness Mix "
                    f"{node.name}"
                )

                mix.operation = "ADD"

                if hasattr(
                    mix,
                    "use_clamp",
                ):
                    mix.use_clamp = True

                tree.links.new(
                    base.outputs[
                        0
                    ],
                    mix.inputs[
                        0
                    ],
                )

                tree.links.new(
                    wet.outputs[
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

                created_nodes.extend(
                    [
                        base,
                        mix,
                    ]
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
                        "wet_roughness": (
                            WATER_DROPS_WET_ROUGHNESS
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
                    "layout_seed": (
                        mask[
                            "layout_seed"
                        ]
                    ),
                    "shape_seed": (
                        mask[
                            "shape_seed"
                        ]
                    ),
                    "drop_count": (
                        mask[
                            "drop_count"
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
                    WATER_DROPS_MASK_RESOLUTION
                ),
                "wet_roughness": (
                    WATER_DROPS_WET_ROUGHNESS
                ),
                "effective_strength": (
                    effective_strength
                ),
                "drop_count": (
                    WATER_DROPS_COUNT
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

            # Removing Water Drops nodes disconnects
            # the temporary wrapper chain.
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

            # Restore exactly the Roughness source
            # that existed before Water Drops.
            for connection in connections:
                socket = connection[
                    "socket"
                ]

                if socket.is_linked:
                    continue

                upstream_socket = (
                    connection[
                        "upstream_socket"
                    ]
                )

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
                "or_condensation_or_frost_or_dust_"
                "roughness_input"
            ),
            "preserves_user_shader_links",
            "compatible_with_reflection",
            "compatible_with_fingerprints",
            "compatible_with_condensation",
            "compatible_with_frost",
            "compatible_with_dust",
            "normal_socket_untouched",
            "uses_temporary_shader_nodes",
            "procedural_mask_no_external_assets",
        )
