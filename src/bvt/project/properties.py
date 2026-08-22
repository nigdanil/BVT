import math

import bpy
from bpy.props import BoolProperty
from bpy.props import FloatProperty
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

    placement_randomization_enabled: BoolProperty(
        name="Random Placement",
        description=(
            "Randomize registered object positions "
            "for every generated frame"
        ),
        default=False,
    )

    placement_offset_x: FloatProperty(
        name="X Range",
        description="Maximum random X offset",
        default=0.03,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    placement_offset_y: FloatProperty(
        name="Y Range",
        description="Maximum random Y offset",
        default=0.03,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    placement_offset_z: FloatProperty(
        name="Z Range",
        description="Maximum random Z offset",
        default=0.0,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    camera_randomization_enabled: BoolProperty(
        name="Random Camera",
        description=(
            "Randomize the active camera transform "
            "for every generated frame"
        ),
        default=False,
    )

    camera_position_offset_x: FloatProperty(
        name="Position X Range",
        description="Maximum camera X position offset",
        default=0.10,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    camera_position_offset_y: FloatProperty(
        name="Position Y Range",
        description="Maximum camera Y position offset",
        default=0.10,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    camera_position_offset_z: FloatProperty(
        name="Position Z Range",
        description="Maximum camera Z position offset",
        default=0.05,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    camera_rotation_offset_x: FloatProperty(
        name="Rotation X Range",
        description="Maximum camera X rotation offset",
        default=math.radians(2.0),
        min=0.0,
        max=math.radians(45.0),
        unit="ROTATION",
    )

    camera_rotation_offset_y: FloatProperty(
        name="Rotation Y Range",
        description="Maximum camera Y rotation offset",
        default=math.radians(2.0),
        min=0.0,
        max=math.radians(45.0),
        unit="ROTATION",
    )

    camera_rotation_offset_z: FloatProperty(
        name="Rotation Z Range",
        description="Maximum camera Z rotation offset",
        default=math.radians(2.0),
        min=0.0,
        max=math.radians(45.0),
        unit="ROTATION",
    )

    lighting_randomization_enabled: BoolProperty(
        name="Random Lighting",
        description=(
            "Randomize scene lights "
            "for every generated frame"
        ),
        default=False,
    )

    lighting_energy_variation: FloatProperty(
        name="Energy Variation",
        description=(
            "Maximum relative light energy variation"
        ),
        default=0.25,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    lighting_color_variation: FloatProperty(
        name="Color Variation",
        description=(
            "Maximum per-channel light color variation"
        ),
        default=0.05,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    lighting_position_offset_x: FloatProperty(
        name="Position X Range",
        description="Maximum light X position offset",
        default=0.25,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    lighting_position_offset_y: FloatProperty(
        name="Position Y Range",
        description="Maximum light Y position offset",
        default=0.25,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
    )

    lighting_position_offset_z: FloatProperty(
        name="Position Z Range",
        description="Maximum light Z position offset",
        default=0.25,
        min=0.0,
        max=1000.0,
        unit="LENGTH",
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
