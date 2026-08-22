import bpy

from ..annotation.service import register_object
from ..project.service import initialize_project
from ..render.service import generate_minimal_dataset


class BVT_OT_InitializeProject(bpy.types.Operator):
    bl_idname = "bvt.initialize_project"
    bl_label = "Initialize Project"
    bl_description = "Initialize the current Blender scene as a BVT project"

    def execute(self, context):
        try:
            settings = initialize_project(
                context.scene,
            )
        except ValueError as exc:
            self.report(
                {"ERROR"},
                str(exc),
            )
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            (
                "BVT project initialized: "
                f"{settings.project_name}"
            ),
        )

        return {"FINISHED"}


class BVT_OT_RegisterSelectedObject(
    bpy.types.Operator
):
    bl_idname = "bvt.register_selected_object"
    bl_label = "Register Selected Object"
    bl_description = (
        "Register the active mesh object "
        "for BVT annotations"
    )

    def execute(self, context):
        try:
            settings = register_object(
                context.active_object,
            )
        except ValueError as exc:
            self.report(
                {"ERROR"},
                str(exc),
            )
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            (
                "BVT object registered: "
                f"{context.active_object.name}"
            ),
        )

        print(
            "[BVT] Object registered:",
            settings.instance_id,
        )

        return {"FINISHED"}


class BVT_OT_GeneratePreview(bpy.types.Operator):
    bl_idname = "bvt.generate_preview"
    bl_label = "Generate Preview"
    bl_description = (
        "Run a minimal Blender Visual Toolkit preview"
    )

    def execute(self, context):
        settings = (
            context.scene.bvt_project
        )

        if not settings.initialized:
            self.report(
                {"WARNING"},
                "Initialize the BVT project first",
            )
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            "Blender Visual Toolkit is running",
        )

        return {"FINISHED"}


class BVT_OT_GenerateDataset(bpy.types.Operator):
    bl_idname = "bvt.generate_dataset"
    bl_label = "Generate Dataset"
    bl_description = (
        "Generate the first BVT dataset"
    )

    def execute(self, context):
        try:
            result = generate_minimal_dataset(
                context.scene,
            )
        except ValueError as exc:
            self.report(
                {"ERROR"},
                str(exc),
            )
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            "BVT dataset generated successfully",
        )

        print(
            "[BVT] Dataset generated:",
            result["dataset_directory"],
        )

        return {"FINISHED"}
