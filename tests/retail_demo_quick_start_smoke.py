import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

TMP = (
    ROOT
    / ".tmp"
    / "retail-demo-quick-start"
)

SCENE_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "beverage-fridge-v0.1.blend"
)


sys.path.insert(
    0,
    str(
        SOURCE
    ),
)


import bpy
import bvt


if TMP.exists():
    shutil.rmtree(
        TMP
    )


TMP.mkdir(
    parents=True,
    exist_ok=True,
)


assert SCENE_PATH.is_file()


bvt.register()


bpy.ops.wm.open_mainfile(
    filepath=str(
        SCENE_PATH
    )
)


scene = bpy.context.scene
project = scene.bvt_project


# These assignments represent the same settings a user
# changes through the Blender UI.
project.output_directory = (
    str(
        TMP
        / "output"
    )
)

project.frame_count = 5

project.dataset_split_train = 0.8
project.dataset_split_validation = 0.1
project.dataset_split_test = 0.1


# Same public UI step documented in QUICK_START.md.
initialize_result = (
    bpy.ops.bvt.initialize_project()
)


assert (
    initialize_result
    == {"FINISHED"}
)

assert (
    project.initialized
    is True
)


result = (
    bpy.ops.bvt.generate_dataset()
)


assert (
    result
    == {"FINISHED"}
)


output = (
    TMP
    / "output"
)

dataset = (
    output
    / "dataset"
)


required = [
    dataset / "manifest.json",
    dataset / "classes.txt",
    dataset / "config" / "generation.json",
    dataset / "splits" / "train.txt",
    dataset / "splits" / "validation.txt",
    dataset / "splits" / "test.txt",
    dataset / "statistics.json",
    dataset / "health.json",
    dataset / "validation.json",
    dataset / "hashes.json",
    output / "dataset.zip",
]


for path in required:
    assert path.is_file(), path


assert len(
    list(
        (
            dataset
            / "images"
        ).glob(
            "*.png"
        )
    )
) == 5


assert len(
    list(
        (
            dataset
            / "labels"
        ).glob(
            "*.txt"
        )
    )
) == 5


for relative in (
    "examples/retail_demo/QUICK_START.md",
    "examples/retail_demo/SAMPLE_DATASET.md",
    "examples/retail_demo/KNOWN_LIMITATIONS.md",
):
    assert (
        ROOT
        / relative
    ).is_file()


print(
    "quick_start_scene=True"
)

print(
    "quick_start_initialize_project=True"
)

print(
    "quick_start_ui_operator=True"
)

print(
    "quick_start_frames=5"
)

print(
    "quick_start_productized_dataset=True"
)

print(
    "quick_start_python_required=False"
)

print(
    "BVT_RETAIL_DEMO_QUICK_START=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


shutil.rmtree(
    TMP
)
