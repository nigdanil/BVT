import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = TMP / "dataset-validation.blend"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.project.service import initialize_project
from bvt.render.service import generate_minimal_dataset
from bvt.validation.dataset import validate_dataset


if TMP.exists():
    shutil.rmtree(TMP)

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)


project = scene.bvt_project

project.project_name = "Dataset Validation Smoke"
project.output_directory = "//bvt_output/"
project.seed = 12345

initialize_project(
    scene,
)


cube = bpy.data.objects["Cube"]

cube_settings = cube.bvt_object

cube_settings.class_id = 0
cube_settings.class_name = "cube"

register_object(
    cube,
)


result = generate_minimal_dataset(
    scene,
)


dataset_directory = result[
    "dataset_directory"
]

validation_path = result[
    "validation_path"
]

report = result[
    "validation_report"
]


assert validation_path.exists()

assert report["status"] == "PASS"
assert report["errors"] == []

assert report["statistics"]["frames"] == 1
assert report["statistics"]["images"] == 1
assert report["statistics"]["labels"] == 1
assert report["statistics"]["objects"] == 1
assert report["statistics"]["classes"] == 1


print("BVT_DATASET_VALIDATION_PASS=OK")
print("validation=", validation_path)


label_path = result["label_path"]

label_path.write_text(
    "0 0.500000 0.500000 1.500000 0.500000\n",
    encoding="utf-8",
)


broken_report = validate_dataset(
    dataset_directory,
)


assert broken_report["status"] == "FAIL"

error_codes = {
    issue["code"]
    for issue in broken_report["errors"]
}

assert "yolo_invalid_size" in error_codes
assert "yolo_bbox_out_of_bounds" in error_codes


print("BVT_DATASET_VALIDATION_FAILURE_DETECTED=OK")
print("errors=", sorted(error_codes))


bvt.unregister()

shutil.rmtree(
    TMP,
)


print("BVT_DATASET_VALIDATION_CLEANUP=OK")
