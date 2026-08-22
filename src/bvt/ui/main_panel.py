import bpy


class BVT_PT_MainPanel(bpy.types.Panel):
    bl_idname = "BVT_PT_main_panel"
    bl_label = "Blender Visual Toolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BVT"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        project = scene.bvt_project
        active_object = context.active_object

        layout.label(
            text="Blender Visual Toolkit",
            icon="TOOL_SETTINGS",
        )

        # ---------------------------------------------------------
        # Project
        # ---------------------------------------------------------

        project_box = layout.box()

        project_box.label(
            text="Project",
            icon="FILE_BLEND",
        )

        project_box.prop(
            project,
            "project_name",
        )

        project_box.prop(
            project,
            "output_directory",
        )

        project_box.prop(
            project,
            "seed",
        )

        project_box.operator(
            "bvt.initialize_project",
            icon="CHECKMARK",
        )

        if project.initialized:
            project_box.separator()

            project_box.label(
                text="Project initialized",
                icon="CHECKMARK",
            )

            project_box.label(
                text=f"ID: {project.project_id[:8]}",
            )

        # ---------------------------------------------------------
        # Object Annotation
        # ---------------------------------------------------------

        annotation_box = layout.box()

        annotation_box.label(
            text="Object Annotation",
            icon="OBJECT_DATA",
        )

        if active_object is None:
            annotation_box.label(
                text="No active object",
                icon="INFO",
            )

        elif active_object.type != "MESH":
            annotation_box.label(
                text=(
                    f"{active_object.name}: "
                    "only mesh objects are supported"
                ),
                icon="ERROR",
            )

        else:
            settings = active_object.bvt_object

            annotation_box.label(
                text=f"Object: {active_object.name}",
            )

            annotation_box.prop(
                settings,
                "class_id",
            )

            annotation_box.prop(
                settings,
                "class_name",
            )

            annotation_box.prop(
                settings,
                "annotation_enabled",
            )

            annotation_box.operator(
                "bvt.register_selected_object",
                icon="ADD",
            )

            if settings.registered:
                annotation_box.separator()

                annotation_box.label(
                    text="Object registered",
                    icon="CHECKMARK",
                )

                annotation_box.label(
                    text=(
                        "Instance: "
                        f"{settings.instance_id[:8]}"
                    ),
                )

        # ---------------------------------------------------------
        # Future modules
        # ---------------------------------------------------------

        layout.separator()

        layout.label(text="Scene")
        layout.label(text="Assets")
        layout.label(text="Placement")
        layout.label(text="Camera")
        layout.label(text="Lighting")
        layout.label(text="Artifacts")
        layout.label(text="Export")

        # ---------------------------------------------------------
        # Generation
        # ---------------------------------------------------------

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
