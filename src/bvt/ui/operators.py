import bpy


class BVT_OT_GeneratePreview(bpy.types.Operator):
    bl_idname = "bvt.generate_preview"
    bl_label = "Generate Preview"
    bl_description = "Run a minimal Blender Visual Toolkit preview"

    def execute(self, context):
        self.report(
            {"INFO"},
            "Blender Visual Toolkit is running",
        )

        print("[BVT] Generate Preview")

        return {"FINISHED"}
