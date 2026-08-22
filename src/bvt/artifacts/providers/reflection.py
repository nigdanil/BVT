from ...materials import get_materials_by_role
from ...materials import MATERIAL_ROLE_GLASS
from ..base import ArtifactProvider


REFLECTION_DEFAULT_MIN_ROUGHNESS = 0.02

_SUPPORTED_NODE_TYPES = frozenset(
    {
        "BSDF_PRINCIPLED",
        "BSDF_GLASS",
    }
)


def _roughness_nodes(
    material,
):
    """
    Return supported unlinked Roughness sockets
    in deterministic node-name order.
    """

    if (
        not material.use_nodes
        or material.node_tree is None
    ):
        return ()

    result = []

    for node in material.node_tree.nodes:
        if node.type not in _SUPPORTED_NODE_TYPES:
            continue

        socket = node.inputs.get(
            "Roughness"
        )

        if socket is None:
            continue

        # A linked socket is controlled by another
        # shader node. Changing default_value would
        # not affect the material.
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


class ReflectionArtifactProvider(
    ArtifactProvider
):
    """
    Increase visible reflections on BVT glass
    materials by deterministically reducing
    shader roughness.
    """

    artifact_id = "reflection"
    category = "glass"
    stage = "pre_render"
    execution_order = 100

    description = (
        "Enhances reflections on BVT glass materials"
    )

    def validate_config(
        self,
        config,
    ):
        super().validate_config(
            config
        )

        min_roughness = float(
            config.options.get(
                "min_roughness",
                REFLECTION_DEFAULT_MIN_ROUGHNESS,
            )
        )

        if not (
            0.0
            <= min_roughness
            <= 1.0
        ):
            raise ValueError(
                "Reflection minimum roughness must "
                "be between 0 and 1"
            )

    def capture(
        self,
        scene,
    ):
        """
        Capture roughness values for all compatible
        nodes on materials tagged as GLASS.
        """

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
        }

    def apply(
        self,
        scene,
        context,
        baseline,
    ):
        """
        Reduce glass roughness according to artifact
        intensity while preserving the captured
        template values for reset.
        """

        configured_min_roughness = float(
            context.config.options.get(
                "min_roughness",
                REFLECTION_DEFAULT_MIN_ROUGHNESS,
            )
        )

        affected_materials = []
        changes = []

        for material_entry in baseline[
            "materials"
        ]:
            material = material_entry[
                "material"
            ]

            material_changed = False

            for node_entry in material_entry[
                "nodes"
            ]:
                node = node_entry[
                    "node"
                ]

                socket = node_entry[
                    "socket"
                ]

                base_roughness = float(
                    node_entry[
                        "base_roughness"
                    ]
                )

                # Reflection must never make an
                # already-glossy material rougher.
                target_roughness = min(
                    base_roughness,
                    configured_min_roughness,
                )

                effective_roughness = (
                    base_roughness
                    + (
                        target_roughness
                        - base_roughness
                    )
                    * context.config.intensity
                )

                socket.default_value = (
                    effective_roughness
                )

                material_changed = True

                changes.append(
                    {
                        "material": (
                            material.name_full
                        ),
                        "node": node.name,
                        "base_roughness": (
                            base_roughness
                        ),
                        "target_roughness": (
                            target_roughness
                        ),
                        "effective_roughness": (
                            float(
                                socket.default_value
                            )
                        ),
                    }
                )

            if material_changed:
                affected_materials.append(
                    material.name_full
                )

        affected_materials.sort()

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
                "configured_min_roughness": (
                    configured_min_roughness
                ),
                "supported_node_count": (
                    len(changes)
                ),
                "material_changes": (
                    changes
                ),
            },
        }

    def reset(
        self,
        scene,
        baseline,
    ):
        """
        Restore every captured roughness value.
        """

        for material_entry in baseline[
            "materials"
        ]:
            for node_entry in material_entry[
                "nodes"
            ]:
                node_entry[
                    "socket"
                ].default_value = (
                    node_entry[
                        "base_roughness"
                    ]
                )

    def compatibility_rules(self):
        return (
            "targets_material_role_glass",
            "supports_principled_and_glass_bsdf",
            "requires_unlinked_roughness_input",
        )
