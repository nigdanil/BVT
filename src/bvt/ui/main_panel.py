import bpy


class BVT_PT_MainPanel(bpy.types.Panel):
    bl_idname = "BVT_PT_main_panel"
    bl_label = "Blender Visual Toolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BVT"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bvt_project

        layout.label(
            text="Blender Visual Toolkit",
            icon="TOOL_SETTINGS",
        )

        project_box = layout.box()

        project_box.label(
            text="Project",
            icon="FILE_BLEND",
        )

        project_box.prop(
            settings,
            "project_name",
        )

        project_box.prop(
            settings,
            "output_directory",
        )

        project_box.prop(
            settings,
            "seed",
        )

        project_box.operator(
            "bvt.initialize_project",
            icon="CHECKMARK",
        )

        if settings.initialized:
            project_box.separator()

            project_box.label(
                text="Project initialized",
                icon="CHECKMARK",
            )

            project_box.label(
                text=f"ID: {settings.project_id[:8]}",
            )

        layout.separator()

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

        layout.operator(
            "bvt.generate_dataset",
            text="Generate Dataset",
            icon="FILE_TICK",
        )
