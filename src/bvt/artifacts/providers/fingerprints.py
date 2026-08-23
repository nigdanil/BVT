import math
import random

import bpy

from ...core.seeding import derive_subseed
from ...materials import get_materials_by_role
from ...materials import MATERIAL_ROLE_GLASS
from ..base import ArtifactProvider


FINGERPRINT_DEFAULT_COUNT = 3
FINGERPRINT_DEFAULT_TRANSPARENCY = 0.35
FINGERPRINT_DEFAULT_SIZE = 0.30

FINGERPRINT_MASK_RESOLUTION = 256
FINGERPRINT_ROUGHNESS_DELTA = 0.45

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

        # Fingerprints must not destroy an existing
        # user-controlled shader connection.
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


def _sample_fingerprints(
    seed,
    print_count,
    size,
):
    rng = random.Random(
        seed
    )

    fingerprints = []

    for index in range(
        print_count
    ):
        sampled_size = (
            size
            * rng.uniform(
                0.82,
                1.18,
            )
        )

        scale_x = _clamp(
            sampled_size
            * rng.uniform(
                0.42,
                0.58,
            ),
            0.015,
            0.48,
        )

        scale_y = _clamp(
            sampled_size
            * rng.uniform(
                0.72,
                1.00,
            ),
            0.02,
            0.48,
        )

        rotation_radians = (
            rng.uniform(
                0.0,
                math.tau,
            )
        )

        fingerprints.append(
            {
                "index": index,
                "center_u": rng.uniform(
                    0.10,
                    0.90,
                ),
                "center_v": rng.uniform(
                    0.10,
                    0.90,
                ),
                "scale_x": scale_x,
                "scale_y": scale_y,
                "rotation_radians": (
                    rotation_radians
                ),
                "rotation_degrees": (
                    math.degrees(
                        rotation_radians
                    )
                ),
                "ridge_density": (
                    rng.uniform(
                        16.0,
                        24.0,
                    )
                ),
                "phase": rng.uniform(
                    0.0,
                    math.tau,
                ),
                "spiral": rng.uniform(
                    -0.18,
                    0.18,
                ),
            }
        )

    return tuple(
        fingerprints
    )


def _fingerprint_value(
    u,
    v,
    fingerprint,
):
    du = (
        u
        - fingerprint["center_u"]
    )

    dv = (
        v
        - fingerprint["center_v"]
    )

    angle = (
        fingerprint[
            "rotation_radians"
        ]
    )

    cosine = math.cos(
        angle
    )

    sine = math.sin(
        angle
    )

    local_x = (
        cosine * du
        + sine * dv
    ) / fingerprint["scale_x"]

    local_y = (
        -sine * du
        + cosine * dv
    ) / fingerprint["scale_y"]

    radius = math.sqrt(
        local_x * local_x
        + local_y * local_y
    )

    if radius >= 1.0:
        return 0.0

    theta = math.atan2(
        local_y,
        local_x,
    )

    phase = fingerprint[
        "phase"
    ]

    warped_radius = (
        radius
        + (
            fingerprint["spiral"]
            * theta
            / math.tau
        )
        + (
            0.035
            * math.sin(
                theta * 3.0
                + phase
            )
        )
    )

    ridge_phase = (
        math.tau
        * fingerprint[
            "ridge_density"
        ]
        * warped_radius
        + phase
    )

    wave = (
        0.5
        + 0.5
        * math.cos(
            ridge_phase
        )
    )

    ridge = _clamp(
        (
            wave
            - 0.52
        )
        / 0.38
    )

    ridge = (
        ridge
        * ridge
    )

    # Fade cleanly near the outside of
    # each elliptical fingerprint.
    edge_fade = _clamp(
        (
            1.0
            - radius
        )
        / 0.12
    )

    return (
        ridge
        * edge_fade
    )


def _build_mask(
    seed,
    print_count,
    size,
    resolution,
):
    fingerprints = (
        _sample_fingerprints(
            seed=seed,
            print_count=print_count,
            size=size,
        )
    )

    pixels = []

    covered_pixels = 0

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

            value = 0.0

            for fingerprint in fingerprints:
                value = max(
                    value,
                    _fingerprint_value(
                        u,
                        v,
                        fingerprint,
                    ),
                )

            value = _clamp(
                value
            )

            if value > 0.05:
                covered_pixels += 1

            # RGB stays white. Only Alpha is used
            # by the temporary roughness graph.
            pixels.extend(
                (
                    1.0,
                    1.0,
                    1.0,
                    value,
                )
            )

    coverage = (
        covered_pixels
        / float(
            resolution
            * resolution
        )
    )

    return {
        "pixels": pixels,
        "fingerprints": fingerprints,
        "coverage": coverage,
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


class FingerprintsArtifactProvider(
    ArtifactProvider
):
    artifact_id = "fingerprints"
    category = "glass"
    stage = "pre_render"
    execution_order = 110

    description = (
        "Adds deterministic fingerprint residue "
        "patterns to BVT glass materials"
    )

    def validate_config(
        self,
        config,
    ):
        super().validate_config(
            config
        )

        print_count = int(
            config.options.get(
                "print_count",
                FINGERPRINT_DEFAULT_COUNT,
            )
        )

        transparency = float(
            config.options.get(
                "transparency",
                FINGERPRINT_DEFAULT_TRANSPARENCY,
            )
        )

        size = float(
            config.options.get(
                "size",
                FINGERPRINT_DEFAULT_SIZE,
            )
        )

        if not (
            1
            <= print_count
            <= 20
        ):
            raise ValueError(
                "Fingerprint count must "
                "be between 1 and 20"
            )

        if not (
            0.0
            <= transparency
            <= 1.0
        ):
            raise ValueError(
                "Fingerprint transparency must "
                "be between 0 and 1"
            )

        if not (
            0.05
            <= size
            <= 0.80
        ):
            raise ValueError(
                "Fingerprint size must "
                "be between 0.05 and 0.80"
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
        print_count = int(
            context.config.options.get(
                "print_count",
                FINGERPRINT_DEFAULT_COUNT,
            )
        )

        transparency = float(
            context.config.options.get(
                "transparency",
                FINGERPRINT_DEFAULT_TRANSPARENCY,
            )
        )

        size = float(
            context.config.options.get(
                "size",
                FINGERPRINT_DEFAULT_SIZE,
            )
        )

        effective_strength = (
            context.config.intensity
            * (
                1.0
                - transparency
            )
        )

        affected_materials = []
        material_changes = []

        total_coverage = 0.0

        for material_index, material_entry in enumerate(
            baseline["materials"]
        ):
            material = material_entry[
                "material"
            ]

            active_nodes = [
                node_entry
                for node_entry
                in material_entry["nodes"]
                if not (
                    node_entry[
                        "socket"
                    ].is_linked
                )
            ]

            if not active_nodes:
                continue

            material_seed = (
                derive_subseed(
                    context.artifact_seed,
                    "artifact-fingerprints",
                    material.name_full,
                )
            )

            mask = _build_mask(
                seed=material_seed,
                print_count=print_count,
                size=size,
                resolution=(
                    FINGERPRINT_MASK_RESOLUTION
                ),
            )

            image = _create_mask_image(
                name=(
                    "BVT_Fingerprints_"
                    f"{context.artifact_seed}_"
                    f"{material_index}"
                ),
                mask=mask,
                resolution=(
                    FINGERPRINT_MASK_RESOLUTION
                ),
            )

            tree = material.node_tree

            texcoord = tree.nodes.new(
                "ShaderNodeTexCoord"
            )

            texcoord.name = (
                "BVT Fingerprints Coordinates"
            )

            texture = tree.nodes.new(
                "ShaderNodeTexImage"
            )

            texture.name = (
                "BVT Fingerprints Mask"
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
                texture.projection_blend = 0.15

            strength = tree.nodes.new(
                "ShaderNodeMath"
            )

            strength.name = (
                "BVT Fingerprints Strength"
            )

            strength.operation = (
                "MULTIPLY"
            )

            strength.inputs[1].default_value = (
                effective_strength
            )

            created_nodes = [
                texcoord,
                texture,
                strength,
            ]

            # Register runtime state before wiring the
            # graph so reset can clean partial failures.
            runtime = {
                "material": material,
                "node_tree": tree,
                "nodes": created_nodes,
                "image": image,
            }

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
                strength.inputs[0],
            )

            node_changes = []

            for node_entry in active_nodes:
                node = node_entry[
                    "node"
                ]

                socket = node_entry[
                    "socket"
                ]

                input_roughness = float(
                    socket.default_value
                )

                target_roughness = min(
                    1.0,
                    (
                        input_roughness
                        + FINGERPRINT_ROUGHNESS_DELTA
                    ),
                )

                delta = tree.nodes.new(
                    "ShaderNodeMath"
                )

                delta.name = (
                    "BVT Fingerprints Roughness Delta "
                    f"{node.name}"
                )

                delta.operation = (
                    "MULTIPLY"
                )

                delta.inputs[1].default_value = (
                    target_roughness
                    - input_roughness
                )

                add = tree.nodes.new(
                    "ShaderNodeMath"
                )

                add.name = (
                    "BVT Fingerprints Roughness Mix "
                    f"{node.name}"
                )

                add.operation = "ADD"

                add.inputs[0].default_value = (
                    input_roughness
                )

                created_nodes.extend(
                    (
                        delta,
                        add,
                    )
                )

                tree.links.new(
                    strength.outputs[0],
                    delta.inputs[0],
                )

                tree.links.new(
                    delta.outputs[0],
                    add.inputs[1],
                )

                tree.links.new(
                    add.outputs[0],
                    socket,
                )

                node_changes.append(
                    {
                        "node": node.name,
                        "base_roughness": (
                            node_entry[
                                "base_roughness"
                            ]
                        ),
                        "input_roughness": (
                            input_roughness
                        ),
                        "target_roughness": (
                            target_roughness
                        ),
                    }
                )

            affected_materials.append(
                material.name_full
            )

            total_coverage += (
                mask["coverage"]
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
                    "nodes": node_changes,
                    "fingerprints": [
                        {
                            key: value
                            for key, value
                            in fingerprint.items()
                            if key
                            != "rotation_radians"
                        }
                        for fingerprint
                        in mask[
                            "fingerprints"
                        ]
                    ],
                }
            )

        affected_materials.sort()

        mean_coverage = 0.0

        if material_changes:
            mean_coverage = (
                total_coverage
                / len(
                    material_changes
                )
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
                "print_count": (
                    print_count
                ),
                "transparency": (
                    transparency
                ),
                "size": size,
                "mask_resolution": (
                    FINGERPRINT_MASK_RESOLUTION
                ),
                "roughness_delta": (
                    FINGERPRINT_ROUGHNESS_DELTA
                ),
                "effective_strength": (
                    effective_strength
                ),
                "mean_coverage": (
                    mean_coverage
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

        for material_entry in baseline[
            "materials"
        ]:
            for node_entry in material_entry[
                "nodes"
            ]:
                socket = node_entry[
                    "socket"
                ]

                # Temporary links disappear together
                # with their temporary Math nodes.
                if not socket.is_linked:
                    socket.default_value = (
                        node_entry[
                            "base_roughness"
                        ]
                    )

    def compatibility_rules(self):
        return (
            "targets_material_role_glass",
            "supports_principled_and_glass_bsdf",
            "requires_unlinked_roughness_input",
            "compatible_with_reflection",
            "uses_temporary_shader_nodes",
        )
