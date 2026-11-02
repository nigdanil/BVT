from .edge_cases import EMPTY_SLOT_NAMESPACE
from .edge_cases import OCCLUSION_NAMESPACE
from .edge_cases import RETAIL_EDGE_CASES_VERSION
from .edge_cases import WRONG_ANGLE_NAMESPACE
from .edge_cases import WRONG_POSITION_NAMESPACE
from .edge_cases import apply_empty_slot
from .edge_cases import apply_occlusion
from .edge_cases import apply_retail_edge_cases
from .edge_cases import apply_wrong_position
from .edge_cases import capture_retail_edge_case_baseline
from .edge_cases import derive_wrong_angle_delta
from .edge_cases import derive_wrong_position_offset
from .edge_cases import iter_retail_products
from .edge_cases import remove_retail_edge_case_occluders
from .edge_cases import restore_retail_edge_cases
from .edge_cases import select_empty_slot_target
from .edge_cases import select_occlusion_target
from .edge_cases import select_wrong_angle_target
from .edge_cases import select_wrong_position_target


__all__ = (
    "EMPTY_SLOT_NAMESPACE",
    "OCCLUSION_NAMESPACE",
    "RETAIL_EDGE_CASES_VERSION",
    "WRONG_ANGLE_NAMESPACE",
    "WRONG_POSITION_NAMESPACE",
    "apply_empty_slot",
    "apply_occlusion",
    "apply_retail_edge_cases",
    "apply_wrong_position",
    "capture_retail_edge_case_baseline",
    "derive_wrong_angle_delta",
    "derive_wrong_position_offset",
    "iter_retail_products",
    "remove_retail_edge_case_occluders",
    "restore_retail_edge_cases",
    "select_empty_slot_target",
    "select_occlusion_target",
    "select_wrong_angle_target",
    "select_wrong_position_target",
)
