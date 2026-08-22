MATERIAL_ROLE_GENERIC = "GENERIC"
MATERIAL_ROLE_GLASS = "GLASS"


VALID_MATERIAL_ROLES = frozenset(
    {
        MATERIAL_ROLE_GENERIC,
        MATERIAL_ROLE_GLASS,
    }
)


def normalize_material_role(
    role,
):
    """Validate and normalize a BVT material role."""

    normalized = str(
        role
    ).strip().upper()

    if normalized not in VALID_MATERIAL_ROLES:
        raise ValueError(
            (
                "Unsupported BVT material role: "
                f"{role!r}"
            )
        )

    return normalized


def set_material_role(
    material,
    role,
):
    """Assign a validated BVT role to a Blender material."""

    if material is None:
        raise ValueError(
            "Material cannot be None"
        )

    normalized = normalize_material_role(
        role
    )

    material.bvt_material.role = (
        normalized
    )

    return material


def iter_scene_materials(
    scene,
):
    """
    Yield unique materials actually assigned
    to objects in the scene.
    """

    seen = set()

    for obj in scene.objects:
        data = getattr(
            obj,
            "data",
            None,
        )

        if data is None:
            continue

        materials = getattr(
            data,
            "materials",
            None,
        )

        if materials is None:
            continue

        for material in materials:
            if material is None:
                continue

            pointer = material.as_pointer()

            if pointer in seen:
                continue

            seen.add(
                pointer
            )

            yield material


def get_materials_by_role(
    scene,
    role,
):
    """
    Return scene materials matching a BVT role
    in deterministic name order.
    """

    normalized = normalize_material_role(
        role
    )

    materials = [
        material
        for material
        in iter_scene_materials(
            scene
        )
        if (
            material.bvt_material.role
            == normalized
        )
    ]

    materials.sort(
        key=lambda material: (
            material.name_full
        )
    )

    return tuple(
        materials
    )
