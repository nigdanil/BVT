import math
import random

import bpy

from ...core.seeding import derive_subseed
from ...materials import get_materials_by_role
from ...materials import MATERIAL_ROLE_GLASS
from ..base import ArtifactProvider


CONDENSATION_MASK_RESOLUTION = 256

CONDENSATION_ROUGHNESS_DELTA = 0.60

CONDENSATION_PATCH_COUNT = 14
CONDENSATION_DROPLET_COUNT = 28


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
        if node.type not in _SUPPORTED_NODE_TYPES:
            continue

        socket = node.inputs.get(
            "Roughness"
        )

        if socket is None:
            continue

        # Capture only sockets that belong to a clean
        # template material. Existing user shader links
        # must never be replaced by BVT.
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


def _sample_patches(
    seed,
):
    rng = random.Random(
        seed
    )

    patches = []

    for index in range(
        CONDENSATION_PATCH_COUNT
    ):
        patches.append(
            {
                "index": index,
                "center_u": rng.uniform(
                    0.04,
                    0.96,
                ),
                "center_v": rng.uniform(
                    0.04,
                    0.96,
                ),
                "scale_x": rng.uniform(
                    0.11,
                    0.34,
                ),
                "scale_y": rng.uniform(
                    0.10,
                    0.30,
                ),
                "rotation": rng.uniform(
                    0.0,
                    math.tau,
                ),
                "amplitude": rng.uniform(
                    0.34,
                    0.82,
                ),
            }
        )

    return tuple(
        patches
    )


def _sample_droplets(
    seed,
):
    rng = random.Random(
        seed
    )

    droplets = []

    for index in range(
        CONDENSATION_DROPLET_COUNT
    ):
        droplets.append(
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
                    0.006,
                    0.026,
                ),
                "amplitude": rng.uniform(
                    0.20,
                    0.60,
                ),
            }
        )

    return tuple(
        droplets
    )


def _patch_value(
    u,
    v,
    patch,
):
    du = (
        u
        - patch["center_u"]
    )

    dv = (
        v
        - patch["center_v"]
    )

    cosine = math.cos(
        patch["rotation"]
    )

    sine = math.sin(
        patch["rotation"]
    )

    local_x = (
        cosine * du
        + sine * dv
    ) / patch["scale_x"]

    local_y = (
        -sine * du
        + cosine * dv
    ) / patch["scale_y"]

    radius_squared = (
        local_x * local_x
        + local_y * local_y
    )

    if radius_squared >= 4.0:
        return 0.0

    return (
        patch["amplitude"]
        * math.exp(
            -1.65
            * radius_squared
        )
    )


def _droplet_value(
    u,
    v,
    droplet,
):
    du = (
        u
        - droplet["center_u"]
    )

    dv = (
        v
        - droplet["center_v"]
    )

    radius = droplet[
        "radius"
    ]

    distance_squared = (
        du * du
        + dv * dv
    )

    normalized = (
        distance_squared
        / (
            radius
            * radius
        )
    )

    if normalized >= 4.0:
        return 0.0

    return (
        droplet["amplitude"]
        * math.exp(
            -2.4
            * normalized
        )
    )


def _build_mask(
    seed,
    resolution,
):
    patch_seed = derive_subseed(
        seed,
        "condensation-mask",
        "patches",
    )

    droplet_seed = derive_subseed(
        seed,
        "condensation-mask",
        "droplets",
    )

    texture_seed = derive_subseed(
        seed,
        "condensation-mask",
        "texture",
    )

    patches = _sample_patches(
        patch_seed
    )

    droplets = _sample_droplets(
        droplet_seed
    )

    texture_rng = random.Random(
        texture_seed
    )

    frequency_u = texture_rng.uniform(
        7.0,
        13.0,
    )

    frequency_v = texture_rng.uniform(
        8.0,
        15.0,
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

            fog = 0.0

            for patch in patches:
                contribution = (
                    _patch_value(
                        u,
                        v,
                        patch,
                    )
                )

                # Soft union.
                fog = (
                    1.0
                    - (
                        1.0
                        - fog
                    )
                    * (
                        1.0
                        - _clamp(
                            contribution
                        )
                    )
                )

            droplet = 0.0

            for item in droplets:
                droplet = max(
                    droplet,
                    _droplet_value(
                        u,
                        v,
                        item,
                    ),
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

            # Fog is the dominant component.
            # Droplets and micro variation make the
            # result less like a flat transparency map.
            value = (
                fog
                * (
                    0.82
                    + 0.18
                    * micro
                )
            )

            value = max(
                value,
                droplet,
            )

            value = _clamp(
                value
            )

            if value > 0.08:
                covered_pixels += 1

            total_value += value

            # RGB stays white. Alpha carries
            # the procedural condensation mask.
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

    coverage = (
        covered_pixels
        / float(
            pixel_count
        )
    )

    mean_mask_value = (
        total_value
        / float(
            pixel_count
        )
    )

    return {
        "pixels": pixels,
        "patches": patches,
        "droplets": droplets,
        "coverage": coverage,
        "mean_mask_value": (
            mean_mask_value
        ),
        "patch_seed": (
            patch_seed
        ),
        "droplet_seed": (
            droplet_seed
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
        mask["pixels"]
    )

    image.update()

    return image


def _fingerprint_upstream(
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

    if not node.name.startswith(
        "BVT Fingerprints Roughness Mix"
    ):
        return None

    return {
        "link": link,
        "socket": (
            link.from_socket
        ),
        "node": node,
    }


class CondensationArtifactProvider(
    ArtifactProvider
):
    artifact_id = "condensation"
    category = "glass"
    stage = "pre_render"
    execution_order = 120

    description = (
        "Adds deterministic condensation haze "
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

        for material_index, material_entry in enumerate(
            baseline["materials"]
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

                upstream = (
                    _fingerprint_upstream(
                        socket
                    )
                )

                if socket.is_linked:
                    if upstream is None:
                        # Do not replace an arbitrary
                        # user-controlled shader graph.
                        continue

                    input_mode = (
                        "fingerprints"
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
                "artifact-condensation",
                material.name_full,
            )

            mask = _build_mask(
                seed=material_seed,
                resolution=(
                    CONDENSATION_MASK_RESOLUTION
                ),
            )

            image = _create_mask_image(
                name=(
                    "BVT_Condensation_"
                    f"{context.artifact_seed}_"
                    f"{material_index}"
                ),
                mask=mask,
                resolution=(
                    CONDENSATION_MASK_RESOLUTION
                ),
            )

            tree = material.node_tree

            texcoord = tree.nodes.new(
                "ShaderNodeTexCoord"
            )

            texcoord.name = (
                "BVT Condensation Coordinates"
            )

            texture = tree.nodes.new(
                "ShaderNodeTexImage"
            )

            texture.name = (
                "BVT Condensation Mask"
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
                texture.projection_blend = 0.20

            strength = tree.nodes.new(
                "ShaderNodeMath"
            )

            strength.name = (
                "BVT Condensation Strength"
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
                "BVT Condensation Roughness Delta"
            )

            delta.operation = (
                "MULTIPLY"
            )

            delta.inputs[
                1
            ].default_value = (
                CONDENSATION_ROUGHNESS_DELTA
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
                "nodes": created_nodes,
                "image": image,
                "connections": [],
            }

            # Register immediately so reset can
            # clean up a partially-built graph.
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
                    "BVT Condensation Roughness Mix "
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
                            CONDENSATION_ROUGHNESS_DELTA
                        ),
                    }
                )

            affected_materials.append(
                material.name_full
            )

            total_coverage += (
                mask["coverage"]
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
                        mask["coverage"]
                    ),
                    "mean_mask_value": (
                        mask[
                            "mean_mask_value"
                        ]
                    ),
                    "patch_seed": (
                        mask[
                            "patch_seed"
                        ]
                    ),
                    "droplet_seed": (
                        mask[
                            "droplet_seed"
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
                    CONDENSATION_MASK_RESOLUTION
                ),
                "roughness_delta": (
                    CONDENSATION_ROUGHNESS_DELTA
                ),
                "effective_strength": (
                    effective_strength
                ),
                "patch_count": (
                    CONDENSATION_PATCH_COUNT
                ),
                "droplet_count": (
                    CONDENSATION_DROPLET_COUNT
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

            # Remove Condensation nodes first.
            # This disconnects Roughness from the
            # temporary Condensation chain.
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

            # Restore the state that existed immediately
            # before Condensation was applied.
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
                        # The upstream temporary node may
                        # already have disappeared during
                        # cleanup after a partial failure.
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

    def compatibility_rules(self):
        return (
            "targets_material_role_glass",
            "supports_principled_and_glass_bsdf",
            (
                "accepts_clean_or_bvt_fingerprints_"
                "roughness_input"
            ),
            "preserves_user_shader_links",
            "compatible_with_reflection",
            "compatible_with_fingerprints",
            "uses_temporary_shader_nodes",
            "procedural_mask_no_external_assets",
        )
