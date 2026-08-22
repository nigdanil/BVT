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
        # Material Targeting
        # ---------------------------------------------------------

        material_box = layout.box()

        material_box.label(
            text="Material Targeting",
            icon="MATERIAL",
        )

        if active_object is None:
            material_box.label(
                text="No active object",
                icon="INFO",
            )

        elif active_object.type != "MESH":
            material_box.label(
                text="Select a mesh object",
                icon="INFO",
            )

        elif not active_object.material_slots:
            material_box.label(
                text="Object has no materials",
                icon="INFO",
            )

        else:
            for index, slot in enumerate(
                active_object.material_slots
            ):
                material = slot.material

                if material is None:
                    material_box.label(
                        text=(
                            f"Slot {index}: Empty"
                        ),
                        icon="INFO",
                    )

                    continue

                row = material_box.row(
                    align=True
                )

                row.label(
                    text=material.name,
                )

                row.prop(
                    material.bvt_material,
                    "role",
                    text="",
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

        artifacts_box = layout.box()

        artifacts_box.label(
            text="Artifacts",
            icon="MODIFIER",
        )

        artifacts_box.prop(
            project,
            "artifact_engine_enabled",
        )

        if project.artifact_engine_enabled:
            artifacts_box.separator()

            artifacts_box.label(
                text="Over Exposure",
            )

            artifacts_box.prop(
                project,
                "artifact_over_exposure_enabled",
            )

            if project.artifact_over_exposure_enabled:
                artifacts_box.prop(
                    project,
                    "artifact_over_exposure_probability",
                )

                artifacts_box.prop(
                    project,
                    "artifact_over_exposure_intensity",
                )

            artifacts_box.separator()

            artifacts_box.label(
                text="Reflection",
            )

            artifacts_box.prop(
                project,
                "artifact_reflection_enabled",
            )

            if project.artifact_reflection_enabled:
                artifacts_box.prop(
                    project,
                    "artifact_reflection_probability",
                )

                artifacts_box.prop(
                    project,
                    "artifact_reflection_intensity",
                )

                artifacts_box.prop(
                    project,
                    "artifact_reflection_min_roughness",
                )

            artifacts_box.separator()

            artifacts_box.label(
                text="Motion Blur",
            )

            artifacts_box.prop(
                project,
                "artifact_motion_blur_enabled",
            )

            if project.artifact_motion_blur_enabled:
                artifacts_box.prop(
                    project,
                    "artifact_motion_blur_probability",
                )

                artifacts_box.prop(
                    project,
                    "artifact_motion_blur_intensity",
                )

                artifacts_box.prop(
                    project,
                    "artifact_motion_blur_direction_range_degrees",
                )

                artifacts_box.prop(
                    project,
                    "artifact_motion_blur_max_length_pixels",
                )

            artifacts_box.separator()

            artifacts_box.label(
                text="Noise",
            )

            artifacts_box.prop(
                project,
                "artifact_noise_enabled",
            )

            if project.artifact_noise_enabled:
                artifacts_box.prop(
                    project,
                    "artifact_noise_probability",
                )

                artifacts_box.prop(
                    project,
                    "artifact_noise_intensity",
                )

            artifacts_box.separator()

            artifacts_box.label(
                text="JPEG Compression",
            )

            artifacts_box.prop(
                project,
                "artifact_jpeg_enabled",
            )

            if project.artifact_jpeg_enabled:
                artifacts_box.prop(
                    project,
                    "artifact_jpeg_probability",
                )

                artifacts_box.prop(
                    project,
                    "artifact_jpeg_intensity",
                )

                artifacts_box.prop(
                    project,
                    "artifact_jpeg_quality",
                )

                artifacts_box.prop(
                    project,
                    "artifact_jpeg_chroma_loss",
                )

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
