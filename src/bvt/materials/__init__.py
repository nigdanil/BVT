from .properties import register
from .properties import unregister

from .service import get_materials_by_role
from .service import iter_scene_materials
from .service import MATERIAL_ROLE_GENERIC
from .service import MATERIAL_ROLE_GLASS
from .service import normalize_material_role
from .service import set_material_role


__all__ = (
    "register",
    "unregister",
    "get_materials_by_role",
    "iter_scene_materials",
    "MATERIAL_ROLE_GENERIC",
    "MATERIAL_ROLE_GLASS",
    "normalize_material_role",
    "set_material_role",
)
