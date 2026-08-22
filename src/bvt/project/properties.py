import bpy
from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import PointerProperty
from bpy.props import StringProperty

from ..core.constants import DEFAULT_FRAME_COUNT
from ..core.constants import DEFAULT_OUTPUT_DIRECTORY
from ..core.constants import DEFAULT_PROJECT_NAME
from ..core.constants import DEFAULT_SEED
from ..core.constants import PROJECT_SCHEMA_VERSION
from ..core.constants import MAX_FRAME_COUNT


class BVT_ProjectSettings(bpy.types.PropertyGroup):
    project_name: StringProperty(
        name="Project Name",
        description="Name of the Blender Visual Toolkit project",
        default=DEFAULT_PROJECT_NAME,
    )

    output_directory: StringProperty(
        name="Output Directory",
        description="Directory used for generated BVT datasets",
        default=DEFAULT_OUTPUT_DIRECTORY,
    )

    seed: IntProperty(
        name="Seed",
        description="Base seed used for reproducible generation",
        default=DEFAULT_SEED,
        min=0,
        max=2_147_483_647,
    )

    frame_count: IntProperty(
        name="Frame Count",
        description="Number of images to generate",
        default=DEFAULT_FRAME_COUNT,
        min=1,
        max=MAX_FRAME_COUNT,
    )

    initialized: BoolProperty(
        name="Initialized",
        default=False,
        options={"HIDDEN"},
    )

    project_id: StringProperty(
        name="Project ID",
        default="",
        options={"HIDDEN"},
    )

    schema_version: StringProperty(
        name="Schema Version",
        default=PROJECT_SCHEMA_VERSION,
        options={"HIDDEN"},
    )


_CLASSES = (
    BVT_ProjectSettings,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.bvt_project = PointerProperty(
        type=BVT_ProjectSettings,
    )


def unregister():
    del bpy.types.Scene.bvt_project

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
