import bpy

from ..project.service import initialize_project
from ..render.service import generate_minimal_dataset


class BVT_OT_InitializeProject(bpy.types.Operator):
    bl_idname = "bvt.initialize_project"
    bl_label = "Initialize Project"
    bl_description = "Initialize the current Blender scene as a BVT project"

    def execute(self, context):
        try:
            settings = initialize_project(context.scene)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"BVT project initialized: {settings.project_name}",
        )

        print(
            "[BVT] Project initialized:",
            settings.project_id,
            settings.project_name,
        )

        return {"FINISHED"}


class BVT_OT_GeneratePreview(bpy.types.Operator):
    bl_idname = "bvt.generate_preview"
    bl_label = "Generate Preview"
    bl_description = "Run a minimal Blender Visual Toolkit preview"

    def execute(self, context):
        settings = context.scene.bvt_project

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

        print(
            "[BVT] Generate Preview",
            "project_id=",
            settings.project_id,
            "seed=",
            settings.seed,
        )

        return {"FINISHED"}


class BVT_OT_GenerateDataset(bpy.types.Operator):
    bl_idname = "bvt.generate_dataset"
    bl_label = "Generate Dataset"
    bl_description = "Generate the first BVT dataset"

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
