import bpy

from .main_panel import BVT_PT_MainPanel
from .operators import BVT_OT_GeneratePreview
from .operators import BVT_OT_InitializeProject


_CLASSES = (
    BVT_OT_InitializeProject,
    BVT_OT_GeneratePreview,
    BVT_PT_MainPanel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
