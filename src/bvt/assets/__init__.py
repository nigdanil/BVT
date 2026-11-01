from .properties import ASSET_CATEGORY_BACKGROUND
from .properties import ASSET_CATEGORY_CAMERA
from .properties import ASSET_CATEGORY_DECORATION
from .properties import ASSET_CATEGORY_FRIDGE
from .properties import ASSET_CATEGORY_LIGHT
from .properties import ASSET_CATEGORY_PRODUCT
from .properties import ASSET_CATEGORY_SHELF
from .properties import register
from .properties import unregister

from .service import asset_record
from .service import iter_registered_assets
from .service import normalize_asset_category
from .service import normalize_tags
from .service import register_asset


__all__ = (
    "register",
    "unregister",
    "register_asset",
    "iter_registered_assets",
    "asset_record",
    "normalize_asset_category",
    "normalize_tags",
    "ASSET_CATEGORY_PRODUCT",
    "ASSET_CATEGORY_SHELF",
    "ASSET_CATEGORY_FRIDGE",
    "ASSET_CATEGORY_DECORATION",
    "ASSET_CATEGORY_CAMERA",
    "ASSET_CATEGORY_LIGHT",
    "ASSET_CATEGORY_BACKGROUND",
)
