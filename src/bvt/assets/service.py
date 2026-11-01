from .properties import ASSET_CATEGORY_BACKGROUND
from .properties import ASSET_CATEGORY_CAMERA
from .properties import ASSET_CATEGORY_DECORATION
from .properties import ASSET_CATEGORY_FRIDGE
from .properties import ASSET_CATEGORY_LIGHT
from .properties import ASSET_CATEGORY_PRODUCT
from .properties import ASSET_CATEGORY_SHELF


VALID_ASSET_CATEGORIES = frozenset(
    {
        ASSET_CATEGORY_PRODUCT,
        ASSET_CATEGORY_SHELF,
        ASSET_CATEGORY_FRIDGE,
        ASSET_CATEGORY_DECORATION,
        ASSET_CATEGORY_CAMERA,
        ASSET_CATEGORY_LIGHT,
        ASSET_CATEGORY_BACKGROUND,
    }
)


def normalize_asset_category(
    category,
):
    normalized = str(
        category
    ).strip().upper()

    if (
        normalized
        not in VALID_ASSET_CATEGORIES
    ):
        raise ValueError(
            (
                "Unsupported BVT asset "
                f"category: {category!r}"
            )
        )

    return normalized


def normalize_tags(
    tags,
):
    if tags is None:
        return ()

    if isinstance(
        tags,
        str,
    ):
        raw = tags.split(
            ","
        )
    else:
        raw = list(
            tags
        )

    normalized = []

    for value in raw:
        tag = str(
            value
        ).strip().lower()

        if (
            tag
            and tag
            not in normalized
        ):
            normalized.append(
                tag
            )

    return tuple(
        normalized
    )


def register_asset(
    obj,
    *,
    asset_id,
    category,
    manufacturer="",
    tags=(),
    license_name="",
    author="",
    version="0.1.0",
):
    if obj is None:
        raise ValueError(
            "Asset object cannot be None"
        )

    asset_id = str(
        asset_id
    ).strip()

    if not asset_id:
        raise ValueError(
            "Asset ID cannot be empty"
        )

    category = (
        normalize_asset_category(
            category
        )
    )

    tags = normalize_tags(
        tags
    )

    version = str(
        version
    ).strip()

    if not version:
        raise ValueError(
            "Asset version cannot be empty"
        )

    settings = obj.bvt_asset

    settings.asset_id = asset_id
    settings.category = category
    settings.manufacturer = str(
        manufacturer
    ).strip()

    settings.tags = ",".join(
        tags
    )

    settings.license_name = str(
        license_name
    ).strip()

    settings.author = str(
        author
    ).strip()

    settings.version = version
    settings.registered = True

    return settings


def iter_registered_assets(
    scene,
):
    assets = [
        obj
        for obj
        in scene.objects
        if (
            hasattr(
                obj,
                "bvt_asset",
            )
            and obj.bvt_asset.registered
        )
    ]

    assets.sort(
        key=lambda obj: (
            obj.bvt_asset.asset_id,
            obj.name_full,
        )
    )

    return tuple(
        assets
    )


def asset_record(
    obj,
):
    if obj is None:
        raise ValueError(
            "Asset object cannot be None"
        )

    settings = obj.bvt_asset

    if not settings.registered:
        raise ValueError(
            (
                "Object is not registered "
                f"as BVT asset: {obj.name}"
            )
        )

    dimensions = [
        float(
            obj.dimensions.x
        ),
        float(
            obj.dimensions.y
        ),
        float(
            obj.dimensions.z
        ),
    ]

    materials = []

    data = getattr(
        obj,
        "data",
        None,
    )

    slots = getattr(
        data,
        "materials",
        None,
    )

    if slots is not None:
        materials = [
            material.name_full
            for material
            in slots
            if material is not None
        ]

    return {
        "asset_id": (
            settings.asset_id
        ),
        "name": obj.name_full,
        "object_type": obj.type,
        "category": (
            settings.category
        ),
        "manufacturer": (
            settings.manufacturer
        ),
        "tags": list(
            normalize_tags(
                settings.tags
            )
        ),
        "dimensions": dimensions,
        "materials": materials,
        "license": (
            settings.license_name
        ),
        "author": (
            settings.author
        ),
        "version": (
            settings.version
        ),
    }
