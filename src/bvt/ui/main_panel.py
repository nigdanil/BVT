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
        placement_box = layout.box()

        placement_box.label(
            text="Placement",
            icon="ORIENTATION_LOCAL",
        )

        placement_box.prop(
            project,
            "placement_randomization_enabled",
        )

        if project.placement_randomization_enabled:
            placement_box.prop(
                project,
                "placement_offset_x",
            )

            placement_box.prop(
                project,
                "placement_offset_y",
            )

            placement_box.prop(
                project,
                "placement_offset_z",
            )
        camera_box = layout.box()

        camera_box.label(
            text="Camera",
            icon="CAMERA_DATA",
        )

        camera_box.prop(
            project,
            "camera_randomization_enabled",
        )

        if project.camera_randomization_enabled:
            camera_box.label(
                text="Position Range",
            )

            camera_box.prop(
                project,
                "camera_position_offset_x",
            )

            camera_box.prop(
                project,
                "camera_position_offset_y",
            )

            camera_box.prop(
                project,
                "camera_position_offset_z",
            )

            camera_box.separator()

            camera_box.label(
                text="Rotation Range",
            )

            camera_box.prop(
                project,
                "camera_rotation_offset_x",
            )

            camera_box.prop(
                project,
                "camera_rotation_offset_y",
            )

            camera_box.prop(
                project,
                "camera_rotation_offset_z",
            )

        lighting_box = layout.box()

        lighting_box.label(
            text="Lighting",
            icon="LIGHT",
        )

        lighting_box.prop(
            project,
            "lighting_randomization_enabled",
        )

        if project.lighting_randomization_enabled:
            lighting_box.prop(
                project,
                "lighting_energy_variation",
            )

            lighting_box.prop(
                project,
                "lighting_color_variation",
            )

            lighting_box.separator()

            lighting_box.label(
                text="Position Range",
            )

            lighting_box.prop(
                project,
                "lighting_position_offset_x",
            )

            lighting_box.prop(
                project,
                "lighting_position_offset_y",
            )

            lighting_box.prop(
                project,
                "lighting_position_offset_z",
            )

        layout.label(text="Artifacts")
        layout.label(text="Export")

        # ---------------------------------------------------------
        # Generation
        # ---------------------------------------------------------

        layout.separator()

        generation_box = layout.box()

        generation_box.label(
            text="Generation",
            icon="RENDER_ANIMATION",
        )

        generation_box.prop(
            project,
            "frame_count",
        )

        generation_box.label(
            text="Resolution: 512 x 512",
        )

        generation_box.operator(
            "bvt.generate_preview",
            text="Generate Preview",
            icon="RENDER_STILL",
        )

        generation_box.operator(
            "bvt.generate_dataset",
            text="Generate Dataset",
            icon="FILE_TICK",
        )
