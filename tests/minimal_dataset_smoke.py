import json
import shutil
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"

TMP_DIRECTORY = REPOSITORY_ROOT / ".tmp"
BLEND_PATH = TMP_DIRECTORY / "minimal-dataset.blend"
OUTPUT_DIRECTORY = TMP_DIRECTORY / "bvt_output"

sys.path.insert(
    0,
    str(SOURCE_ROOT),
)


import bpy
import bvt

from bvt.project.service import initialize_project
from bvt.render.service import generate_minimal_dataset


if TMP_DIRECTORY.exists():
    shutil.rmtree(TMP_DIRECTORY)

TMP_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene
settings = scene.bvt_project


bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)


settings.project_name = "Minimal Dataset Smoke"
settings.output_directory = "//bvt_output/"
settings.seed = 12345
settings.frame_count = 1

initialize_project(scene)


assert settings.initialized is True
assert scene.camera is not None


result = generate_minimal_dataset(
    scene,
)


image_path = result["image_path"]
manifest_path = result["manifest_path"]


assert image_path.exists()
assert image_path.stat().st_size > 0

assert manifest_path.exists()
assert manifest_path.stat().st_size > 0


manifest = json.loads(
    manifest_path.read_text(
        encoding="utf-8",
    )
)


assert manifest["schema_version"] == "bvt-dataset-manifest-1"
assert manifest["toolkit_version"] == "0.1.0"

assert manifest["dataset"]["project_id"] == settings.project_id
assert manifest["dataset"]["project_name"] == "Minimal Dataset Smoke"

assert manifest["generation"]["seed"] == 12345
assert manifest["generation"]["frame_count"] == 1

assert manifest["render"]["resolution_x"] == 512
assert manifest["render"]["resolution_y"] == 512
assert manifest["render"]["format"] == "PNG"

assert len(manifest["frames"]) == 1

frame = manifest["frames"][0]

assert frame["frame_id"] == "000001"
assert frame["scene"] == scene.name
assert frame["camera"] == scene.camera.name
assert frame["image"] == "images/000001.png"


print("BVT_MINIMAL_DATASET_SMOKE=OK")
print("image=", image_path)
print("manifest=", manifest_path)
print("image_size=", image_path.stat().st_size)
print("project_id=", settings.project_id)


bvt.unregister()

shutil.rmtree(
    TMP_DIRECTORY,
)

print("BVT_MINIMAL_DATASET_CLEANUP=OK")
