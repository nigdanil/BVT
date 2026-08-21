import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
TMP_DIRECTORY = REPOSITORY_ROOT / ".tmp"
BLEND_PATH = TMP_DIRECTORY / "bvt-project-persistence.blend"

sys.path.insert(0, str(SOURCE_ROOT))


import bpy
import bvt

from bvt.project.service import initialize_project


TMP_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

if BLEND_PATH.exists():
    BLEND_PATH.unlink()


bvt.register()

scene = bpy.context.scene
settings = scene.bvt_project

settings.project_name = "Persistence Test"
settings.output_directory = "//bvt_output/"
settings.seed = 987654

initialize_project(scene)

expected_project_id = settings.project_id

assert expected_project_id
assert settings.initialized is True

bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)

print("BVT_PROJECT_SAVE=OK")
print("saved=", BLEND_PATH)


bpy.ops.wm.open_mainfile(
    filepath=str(BLEND_PATH),
)

scene = bpy.context.scene
settings = scene.bvt_project

assert settings.initialized is True
assert settings.project_name == "Persistence Test"
assert settings.output_directory == "//bvt_output/"
assert settings.seed == 987654
assert settings.project_id == expected_project_id
assert settings.schema_version == "bvt-project-1"

print("BVT_PROJECT_RELOAD=OK")
print("project_id=", settings.project_id)
print("project_name=", settings.project_name)
print("seed=", settings.seed)

bvt.unregister()

if BLEND_PATH.exists():
    BLEND_PATH.unlink()

try:
    TMP_DIRECTORY.rmdir()
except OSError:
    pass

print("BVT_PROJECT_PERSISTENCE_SMOKE=OK")
