import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp" / "dataset-productization-foundation"

BLEND_PATH = (
    TMP
    / "foundation.blend"
)


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.constants import DATASET_LAYOUT_VERSION
from bvt.core.constants import DATASET_MANIFEST_SCHEMA_VERSION
from bvt.core.constants import GENERATION_CONFIG_SCHEMA_VERSION
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset
from bvt.validation.dataset import validate_dataset


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


project = scene.bvt_project

project.project_name = (
    "Dataset Productization Foundation"
)

project.output_directory = (
    "//output/"
)

project.seed = 20261102
project.frame_count = 2

project.placement_randomization_enabled = True
project.placement_offset_x = 0.01
project.placement_offset_y = 0.01
project.placement_offset_z = 0.0


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


result = generate_dataset(
    scene
)


dataset_directory = (
    result[
        "dataset_directory"
    ]
)

manifest_path = (
    result[
        "manifest_path"
    ]
)

config_path = (
    result[
        "generation_config_path"
    ]
)


assert (
    dataset_directory.name
    == "dataset"
)

assert (
    dataset_directory
    / "images"
).is_dir()

assert (
    dataset_directory
    / "labels"
).is_dir()

assert (
    dataset_directory
    / "config"
).is_dir()

assert (
    dataset_directory
    / "classes.txt"
).is_file()

assert manifest_path.is_file()
assert config_path.is_file()

assert (
    config_path.relative_to(
        dataset_directory
    ).as_posix()
    == "config/generation.json"
)


manifest = json.loads(
    manifest_path.read_text(
        encoding="utf-8"
    )
)


config = json.loads(
    config_path.read_text(
        encoding="utf-8"
    )
)


assert (
    DATASET_LAYOUT_VERSION
    == "bvt-dataset-layout-1"
)

assert (
    DATASET_MANIFEST_SCHEMA_VERSION
    == "bvt-dataset-manifest-2"
)

assert (
    GENERATION_CONFIG_SCHEMA_VERSION
    == "bvt-generation-config-1"
)


assert (
    manifest[
        "schema_version"
    ]
    == DATASET_MANIFEST_SCHEMA_VERSION
)

assert (
    manifest[
        "layout"
    ][
        "version"
    ]
    == DATASET_LAYOUT_VERSION
)

assert (
    manifest[
        "generation"
    ][
        "config_file"
    ]
    == "config/generation.json"
)

assert (
    manifest[
        "generation"
    ][
        "config_schema_version"
    ]
    == GENERATION_CONFIG_SCHEMA_VERSION
)


assert (
    config[
        "schema_version"
    ]
    == GENERATION_CONFIG_SCHEMA_VERSION
)

assert (
    config[
        "project"
    ][
        "project_id"
    ]
    == project.project_id
)

assert (
    config[
        "project"
    ][
        "project_name"
    ]
    == project.project_name
)

assert (
    config[
        "project"
    ][
        "seed"
    ]
    == 20261102
)

assert (
    config[
        "project"
    ][
        "frame_count"
    ]
    == 2
)

assert (
    config[
        "scene"
    ][
        "name"
    ]
    == scene.name
)

assert (
    config[
        "scene"
    ][
        "camera"
    ]
    == scene.camera.name
)

assert (
    config[
        "render"
    ][
        "resolution_x"
    ]
    == 512
)

assert (
    config[
        "render"
    ][
        "resolution_y"
    ]
    == 512
)

assert (
    config[
        "settings"
    ][
        "placement_randomization_enabled"
    ]
    is True
)

assert abs(
    float(
        config[
            "settings"
        ][
            "placement_offset_x"
        ]
    )
    - 0.01
) < 1e-9


report = validate_dataset(
    dataset_directory
)


assert (
    report[
        "status"
    ]
    == "PASS"
)

assert (
    report[
        "errors"
    ]
    == []
)


# Validator must reject a config/manifest mismatch.
original_config = (
    config_path.read_text(
        encoding="utf-8"
    )
)


broken = dict(
    config
)

broken[
    "schema_version"
] = "invalid-generation-schema"


config_path.write_text(
    json.dumps(
        broken,
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


broken_report = validate_dataset(
    dataset_directory
)


assert (
    broken_report[
        "status"
    ]
    == "FAIL"
)


error_codes = {
    issue[
        "code"
    ]
    for issue
    in broken_report[
        "errors"
    ]
}


assert (
    "generation_config_schema_mismatch"
    in error_codes
)


config_path.write_text(
    original_config,
    encoding="utf-8",
)


restored_report = validate_dataset(
    dataset_directory
)


assert (
    restored_report[
        "status"
    ]
    == "PASS"
)


print(
    "dataset_layout=bvt-dataset-layout-1"
)

print(
    "manifest_schema=bvt-dataset-manifest-2"
)

print(
    "generation_config_schema=bvt-generation-config-1"
)

print(
    "generation_config_saved=True"
)

print(
    "generation_config_validation=True"
)

print(
    "BVT_DATASET_PRODUCTIZATION_FOUNDATION=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


shutil.rmtree(
    TMP
)
