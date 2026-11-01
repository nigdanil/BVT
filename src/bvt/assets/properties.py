import bpy

from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import PointerProperty
from bpy.props import StringProperty


ASSET_CATEGORY_PRODUCT = "PRODUCT"
ASSET_CATEGORY_SHELF = "SHELF"
ASSET_CATEGORY_FRIDGE = "FRIDGE"
ASSET_CATEGORY_DECORATION = "DECORATION"
ASSET_CATEGORY_CAMERA = "CAMERA"
ASSET_CATEGORY_LIGHT = "LIGHT"
ASSET_CATEGORY_BACKGROUND = "BACKGROUND"


ASSET_CATEGORY_ITEMS = (
    (
        ASSET_CATEGORY_PRODUCT,
        "Product",
        "Retail or other product asset",
    ),
    (
        ASSET_CATEGORY_SHELF,
        "Shelf",
        "Shelf or placement surface asset",
    ),
    (
        ASSET_CATEGORY_FRIDGE,
        "Fridge",
        "Refrigerator or display cooler asset",
    ),
    (
        ASSET_CATEGORY_DECORATION,
        "Decoration",
        "Decoration or scene support asset",
    ),
    (
        ASSET_CATEGORY_CAMERA,
        "Camera",
        "Camera asset",
    ),
    (
        ASSET_CATEGORY_LIGHT,
        "Light",
        "Light asset",
    ),
    (
        ASSET_CATEGORY_BACKGROUND,
        "Background",
        "Background asset",
    ),
)


class BVT_AssetSettings(
    bpy.types.PropertyGroup
):
    registered: BoolProperty(
        name="Asset Registered",
        default=False,
        options={"HIDDEN"},
    )

    asset_id: StringProperty(
        name="Asset ID",
        description=(
            "Stable logical identifier "
            "of the BVT asset"
        ),
        default="",
    )

    category: EnumProperty(
        name="Category",
        description=(
            "Semantic category of the asset"
        ),
        items=ASSET_CATEGORY_ITEMS,
        default=ASSET_CATEGORY_PRODUCT,
    )

    manufacturer: StringProperty(
        name="Manufacturer",
        default="",
    )

    tags: StringProperty(
        name="Tags",
        description=(
            "Comma-separated normalized asset tags"
        ),
        default="",
    )

    license_name: StringProperty(
        name="License",
        default="",
    )

    author: StringProperty(
        name="Author",
        default="",
    )

    version: StringProperty(
        name="Version",
        default="0.1.0",
    )


_CLASSES = (
    BVT_AssetSettings,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(
            cls
        )

    bpy.types.Object.bvt_asset = (
        PointerProperty(
            type=BVT_AssetSettings,
        )
    )


def unregister():
    if hasattr(
        bpy.types.Object,
        "bvt_asset",
    ):
        del bpy.types.Object.bvt_asset

    for cls in reversed(
        _CLASSES
    ):
        bpy.utils.unregister_class(
            cls
        )
