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

    artifact_engine_enabled: BoolProperty(
        name="Enable Artifact Engine",
        description=(
            "Enable deterministic artifact generation"
        ),
        default=False,
    )

    artifact_over_exposure_enabled: BoolProperty(
        name="Over Exposure",
        description=(
            "Enable the over exposure artifact"
        ),
        default=False,
    )

    artifact_over_exposure_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying over exposure "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_over_exposure_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Severity of the over exposure artifact"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_reflection_enabled: BoolProperty(
        name="Reflection",
        description=(
            "Enable reflections on BVT glass materials"
        ),
        default=False,
    )

    artifact_reflection_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying reflection "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_reflection_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of the glass reflection artifact"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_reflection_min_roughness: FloatProperty(
        name="Min Roughness",
        description=(
            "Target glass roughness at full "
            "reflection intensity"
        ),
        default=0.02,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_fingerprints_enabled: BoolProperty(
        name="Fingerprints",
        description=(
            "Enable deterministic fingerprints "
            "on BVT glass materials"
        ),
        default=False,
    )

    artifact_fingerprints_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying fingerprints "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_fingerprints_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of fingerprint residue"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_fingerprints_count: IntProperty(
        name="Count",
        description=(
            "Number of fingerprint patterns "
            "per glass material"
        ),
        default=3,
        min=1,
        max=20,
    )

    artifact_fingerprints_transparency: FloatProperty(
        name="Transparency",
        description=(
            "Transparency of fingerprint residue"
        ),
        default=0.35,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_fingerprints_size: FloatProperty(
        name="Size",
        description=(
            "Normalized fingerprint pattern size"
        ),
        default=0.30,
        min=0.05,
        max=0.80,
        subtype="FACTOR",
    )

    artifact_condensation_enabled: BoolProperty(
        name="Condensation",
        description=(
            "Enable deterministic condensation "
            "on BVT glass materials"
        ),
        default=False,
    )

    artifact_condensation_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying condensation "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_condensation_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of condensation haze"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_frost_enabled: BoolProperty(
        name="Frost",
        description=(
            "Enable deterministic crystalline frost "
            "on BVT glass materials"
        ),
        default=False,
    )

    artifact_frost_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying frost "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_frost_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of crystalline frost"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_motion_blur_enabled: BoolProperty(
        name="Motion Blur",
        description=(
            "Enable deterministic camera motion blur"
        ),
        default=False,
    )

    artifact_motion_blur_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying motion blur "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_motion_blur_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of camera motion blur"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_motion_blur_direction_range_degrees: FloatProperty(
        name="Direction Range",
        description=(
            "Maximum seeded motion direction "
            "in degrees"
        ),
        default=180.0,
        min=0.0,
        max=180.0,
    )

    artifact_motion_blur_max_length_pixels: IntProperty(
        name="Max Length",
        description=(
            "Maximum motion blur length "
            "at full intensity in pixels"
        ),
        default=16,
        min=1,
        max=64,
    )

    artifact_noise_enabled: BoolProperty(
        name="Noise",
        description=(
            "Enable deterministic sensor noise"
        ),
        default=False,
    )

    artifact_noise_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying noise "
            "to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_noise_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Strength of sensor noise"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_jpeg_enabled: BoolProperty(
        name="JPEG Compression",
        description=(
            "Enable JPEG compression artifacts"
        ),
        default=False,
    )

    artifact_jpeg_probability: FloatProperty(
        name="Probability",
        description=(
            "Probability of applying JPEG "
            "compression to each generated frame"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_jpeg_intensity: FloatProperty(
        name="Intensity",
        description=(
            "Overall strength of JPEG degradation"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    artifact_jpeg_quality: IntProperty(
        name="Quality",
        description=(
            "Target JPEG quality at full intensity"
        ),
        default=40,
        min=1,
        max=100,
    )

    artifact_jpeg_chroma_loss: FloatProperty(
        name="Chroma Loss",
        description=(
            "Amount of chroma degradation "
            "at full intensity"
        ),
        default=0.50,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
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
