import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE_ROOT),
)


import bpy
import bvt

from bvt.project.service import initialize_project


bvt.register()

scene = bpy.context.scene
settings = scene.bvt_project

assert settings.initialized is False
assert settings.seed == 12345
assert settings.schema_version == "bvt-project-1"

settings.project_name = "Smoke Test"
settings.output_directory = "//smoke_output/"
settings.seed = 42

initialize_project(scene)

assert settings.initialized is True
assert settings.project_name == "Smoke Test"
assert settings.output_directory == "//smoke_output/"
assert settings.seed == 42
assert settings.project_id
assert len(settings.project_id) == 32

print("BVT_PROJECT_SMOKE=OK")
print("project_id=", settings.project_id)
print("seed=", settings.seed)

bvt.unregister()
