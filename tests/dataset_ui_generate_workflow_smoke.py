import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

TMP = (
    ROOT
    / ".tmp"
    / "dataset-ui-generate-workflow"
)

BLEND_PATH = (
    TMP
    / "ui-generate.blend"
)


sys.path.insert(
    0,
    str(
        SOURCE
    ),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.project.service import initialize_project


if TMP.exists():
    shutil.rmtree(
        TMP
    )


TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()


scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    ),
)


project = (
    scene.bvt_project
)

project.project_name = (
    "Dataset UI Generate Workflow"
)

project.output_directory = (
    "//output/"
)

project.seed = 20261102
project.frame_count = 1

project.dataset_split_train = 1.0
project.dataset_split_validation = 0.0
project.dataset_split_test = 0.0


initialize_project(
    scene
)


cube = bpy.data.objects[
    "Cube"
]

cube_settings = (
    cube.bvt_object
)

cube_settings.class_id = 0
cube_settings.class_name = "cube"

register_object(
    cube
)


result = (
    bpy.ops.bvt.generate_dataset()
)


assert (
    result
    == {"FINISHED"}
)


output_directory = (
    TMP
    / "output"
)

dataset_directory = (
    output_directory
    / "dataset"
)


required_files = [
    "manifest.json",
    "classes.txt",
    "config/generation.json",
    "splits/train.txt",
    "splits/validation.txt",
    "splits/test.txt",
    "statistics.json",
    "health.json",
    "validation.json",
    "hashes.json",
]


for relative in (
    required_files
):
    assert (
        dataset_directory
        / relative
    ).is_file()


assert (
    output_directory
    / "dataset.zip"
).is_file()


assert (
    dataset_directory
    / "images"
    / "000001.png"
).is_file()


assert (
    dataset_directory
    / "labels"
    / "000001.txt"
).is_file()


assert (
    (
        dataset_directory
        / "splits"
        / "train.txt"
    ).read_text(
        encoding="utf-8"
    ).strip()
    == "images/000001.png"
)


assert (
    (
        dataset_directory
        / "splits"
        / "validation.txt"
    ).read_text(
        encoding="utf-8"
    )
    == ""
)


assert (
    (
        dataset_directory
        / "splits"
        / "test.txt"
    ).read_text(
        encoding="utf-8"
    )
    == ""
)


print(
    "ui_operator=bvt.generate_dataset"
)

print(
    "ui_generate_result=FINISHED"
)

print(
    "ui_productized_dataset=True"
)

print(
    "ui_archive_created=True"
)

print(
    "ui_split_controls_contract=True"
)

print(
    "BVT_DATASET_UI_GENERATE_WORKFLOW=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


shutil.rmtree(
    TMP
)
