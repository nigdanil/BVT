import bpy

from bpy.props import EnumProperty
from bpy.props import PointerProperty

from .service import MATERIAL_ROLE_GENERIC
from .service import MATERIAL_ROLE_GLASS


class BVT_MaterialSettings(
    bpy.types.PropertyGroup
):
    """
    Persistent BVT metadata attached
    to a Blender material.
    """

    role: EnumProperty(
        name="BVT Role",
        description=(
            "Semantic role used by BVT "
            "material and artifact systems"
        ),
        items=(
            (
                MATERIAL_ROLE_GENERIC,
                "Generic",
                (
                    "Normal material without "
                    "glass-specific targeting"
                ),
            ),
            (
                MATERIAL_ROLE_GLASS,
                "Glass",
                (
                    "Glass material eligible for "
                    "glass and reflection artifacts"
                ),
            ),
        ),
        default=MATERIAL_ROLE_GENERIC,
    )


_CLASSES = (
    BVT_MaterialSettings,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(
            cls
        )

    bpy.types.Material.bvt_material = (
        PointerProperty(
            type=BVT_MaterialSettings,
        )
    )


def unregister():
    if hasattr(
        bpy.types.Material,
        "bvt_material",
    ):
        del bpy.types.Material.bvt_material

    for cls in reversed(
        _CLASSES
    ):
        bpy.utils.unregister_class(
            cls
        )
