import bpy


class BVT_PT_MainPanel(bpy.types.Panel):
    bl_idname = "BVT_PT_main_panel"
    bl_label = "Blender Visual Toolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BVT"

    def draw(self, context):
        layout = self.layout

        layout.label(
            text="Blender Visual Toolkit",
            icon="TOOL_SETTINGS",
        )

        layout.separator()

        layout.label(text="Project")
        layout.label(text="Scene")
        layout.label(text="Assets")
        layout.label(text="Placement")
        layout.label(text="Camera")
        layout.label(text="Lighting")
        layout.label(text="Artifacts")
        layout.label(text="Export")

        layout.separator()

        layout.operator(
            "bvt.generate_preview",
            text="Generate Preview",
            icon="RENDER_STILL",
        )
