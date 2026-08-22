import bpy
from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import PointerProperty
from bpy.props import StringProperty


class BVT_ObjectSettings(bpy.types.PropertyGroup):
    registered: BoolProperty(
        name="Registered",
        default=False,
        options={"HIDDEN"},
    )

    annotation_enabled: BoolProperty(
        name="Annotation Enabled",
        description="Include this object in dataset annotations",
        default=True,
    )

    instance_id: StringProperty(
        name="Instance ID",
        default="",
        options={"HIDDEN"},
    )

    class_id: IntProperty(
        name="Class ID",
        description="YOLO class identifier",
        default=0,
        min=0,
    )

    class_name: StringProperty(
        name="Class Name",
        description="Human readable class name",
        default="object",
    )


_CLASSES = (
    BVT_ObjectSettings,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Object.bvt_object = PointerProperty(
        type=BVT_ObjectSettings,
    )


def unregister():
    if hasattr(bpy.types.Object, "bvt_object"):
        del bpy.types.Object.bvt_object

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
