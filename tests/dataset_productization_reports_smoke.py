import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

TMP = (
    ROOT
    / ".tmp"
    / "dataset-productization-reports"
)

BLEND_PATH = (
    TMP
    / "reports.blend"
)


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.constants import DATASET_HEALTH_SCHEMA_VERSION
from bvt.core.constants import DATASET_SPLIT_SCHEMA_VERSION
from bvt.core.constants import DATASET_STATISTICS_SCHEMA_VERSION
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


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
    "Dataset Productization Reports"
)

project.output_directory = (
    "//output/"
)

project.seed = 20261102
project.frame_count = 10

project.dataset_split_train = 0.80
project.dataset_split_validation = 0.10
project.dataset_split_test = 0.10

project.placement_randomization_enabled = True
project.placement_offset_x = 0.02
project.placement_offset_y = 0.02
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


first = generate_dataset(
    scene
)


dataset_directory = (
    first[
        "dataset_directory"
    ]
)

manifest_path = (
    first[
        "manifest_path"
    ]
)

statistics_path = (
    first[
        "statistics_path"
    ]
)

health_path = (
    first[
        "health_path"
    ]
)


assert manifest_path.is_file()
assert statistics_path.is_file()
assert health_path.is_file()


manifest = json.loads(
    manifest_path.read_text(
        encoding="utf-8"
    )
)

statistics = json.loads(
    statistics_path.read_text(
        encoding="utf-8"
    )
)

health = json.loads(
    health_path.read_text(
        encoding="utf-8"
    )
)


splits = manifest[
    "splits"
]


assert (
    splits[
        "schema_version"
    ]
    == DATASET_SPLIT_SCHEMA_VERSION
)

assert (
    splits[
        "strategy"
    ]
    == "sha256-rank-v1"
)

assert (
    splits[
        "counts"
    ]
    == {
        "train": 8,
        "validation": 1,
        "test": 1,
    }
)


split_rows = {}

for split_name in (
    "train",
    "validation",
    "test",
):
    path = (
        first[
            "split_paths"
        ][
            split_name
        ]
    )

    assert path.is_file()

    rows = [
        line.strip()
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    split_rows[
        split_name
    ] = rows


assert len(
    split_rows[
        "train"
    ]
) == 8

assert len(
    split_rows[
        "validation"
    ]
) == 1

assert len(
    split_rows[
        "test"
    ]
) == 1


all_rows = (
    split_rows[
        "train"
    ]
    + split_rows[
        "validation"
    ]
    + split_rows[
        "test"
    ]
)


assert len(
    all_rows
) == 10

assert len(
    set(
        all_rows
    )
) == 10


expected_images = {
    f"images/{index:06d}.png"
    for index in range(
        1,
        11,
    )
}


assert (
    set(
        all_rows
    )
    == expected_images
)


assert (
    statistics[
        "schema_version"
    ]
    == DATASET_STATISTICS_SCHEMA_VERSION
)

assert (
    statistics[
        "frames"
    ]
    == 10
)

assert (
    statistics[
        "images"
    ]
    == 10
)

assert (
    statistics[
        "labels"
    ]
    == 10
)

assert (
    statistics[
        "objects"
    ]
    == 10
)

assert (
    statistics[
        "classes"
    ][
        "count"
    ]
    == 1
)

assert (
    statistics[
        "classes"
    ][
        "per_class"
    ]
    == [
        {
            "id": 0,
            "name": "cube",
            "objects": 10,
        }
    ]
)

assert (
    statistics[
        "empty_label_frames"
    ]
    == 0
)

assert (
    statistics[
        "bbox"
    ][
        "count"
    ]
    == 10
)

assert (
    statistics[
        "bbox"
    ][
        "area_min"
    ]
    > 0.0
)

assert (
    statistics[
        "splits"
    ]
    == {
        "train": 8,
        "validation": 1,
        "test": 1,
    }
)


assert (
    health[
        "schema_version"
    ]
    == DATASET_HEALTH_SCHEMA_VERSION
)

assert (
    health[
        "status"
    ]
    == "PASS"
)

assert (
    health[
        "findings"
    ]
    == []
)

assert (
    health[
        "checks"
    ][
        "validation_errors"
    ]
    == 0
)

assert (
    health[
        "checks"
    ][
        "empty_label_frames"
    ]
    == 0
)

assert (
    health[
        "checks"
    ][
        "empty_splits"
    ]
    == []
)


first_split_manifest = json.dumps(
    splits,
    sort_keys=True,
)

first_split_files = {
    split_name: (
        first[
            "split_paths"
        ][
            split_name
        ].read_text(
            encoding="utf-8"
        )
    )
    for split_name
    in (
        "train",
        "validation",
        "test",
    )
}

first_statistics = (
    statistics_path.read_text(
        encoding="utf-8"
    )
)


second = generate_dataset(
    scene
)


second_manifest = json.loads(
    second[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


assert (
    json.dumps(
        second_manifest[
            "splits"
        ],
        sort_keys=True,
    )
    == first_split_manifest
)


for split_name in (
    "train",
    "validation",
    "test",
):
    assert (
        second[
            "split_paths"
        ][
            split_name
        ].read_text(
            encoding="utf-8"
        )
        == first_split_files[
            split_name
        ]
    )


assert (
    second[
        "statistics_path"
    ].read_text(
        encoding="utf-8"
    )
    == first_statistics
)


print(
    "split_schema=bvt-dataset-split-1"
)

print(
    "split_counts=8/1/1"
)

print(
    "split_unique_frames=10"
)

print(
    "split_reproducible=True"
)

print(
    "statistics_schema=bvt-dataset-statistics-1"
)

print(
    "statistics_objects=10"
)

print(
    "health_schema=bvt-dataset-health-1"
)

print(
    "health_status=PASS"
)

print(
    "BVT_DATASET_PRODUCTIZATION_REPORTS=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


shutil.rmtree(
    TMP
)
