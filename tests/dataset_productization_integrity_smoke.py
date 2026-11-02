import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

TMP = (
    ROOT
    / ".tmp"
    / "dataset-productization-integrity"
)

BLEND_PATH = (
    TMP
    / "integrity.blend"
)


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.constants import DATASET_HASHES_SCHEMA_VERSION
from bvt.export.archive import export_dataset_zip
from bvt.export.hashes import sha256_file
from bvt.export.hashes import verify_dataset_hashes
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
    "Dataset Productization Integrity"
)

project.output_directory = (
    "//output/"
)

project.seed = 20261102
project.frame_count = 10

project.dataset_split_train = 0.80
project.dataset_split_validation = 0.10
project.dataset_split_test = 0.10


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

hashes_path = (
    result[
        "hashes_path"
    ]
)

archive_path = (
    result[
        "archive_path"
    ]
)


assert hashes_path.is_file()
assert archive_path.is_file()


assert (
    result[
        "hashes"
    ][
        "schema_version"
    ]
    == DATASET_HASHES_SCHEMA_VERSION
)


hash_report = (
    verify_dataset_hashes(
        dataset_directory
    )
)


assert (
    hash_report[
        "status"
    ]
    == "PASS"
)

assert (
    hash_report[
        "errors"
    ]
    == []
)


hashed_paths = {
    item[
        "path"
    ]
    for item
    in result[
        "hashes"
    ][
        "files"
    ]
}


required_hashed_files = {
    "manifest.json",
    "classes.txt",
    "config/generation.json",
    "splits/train.txt",
    "splits/validation.txt",
    "splits/test.txt",
    "statistics.json",
    "health.json",
    "validation.json",
}


assert (
    required_hashed_files
    <= hashed_paths
)

assert (
    "hashes.json"
    not in hashed_paths
)


for index in range(
    1,
    11,
):
    frame_id = (
        f"{index:06d}"
    )

    assert (
        f"images/{frame_id}.png"
        in hashed_paths
    )

    assert (
        f"labels/{frame_id}.txt"
        in hashed_paths
    )


# ---------------------------------------------------------
# ZIP must contain the complete canonical dataset root.
# ---------------------------------------------------------

dataset_files = {
    path.relative_to(
        dataset_directory
    ).as_posix()
    for path
    in dataset_directory.rglob(
        "*"
    )
    if path.is_file()
}


with zipfile.ZipFile(
    archive_path,
    "r",
) as archive:
    archive_files = set(
        archive.namelist()
    )

    expected_archive_files = {
        "dataset/"
        + relative
        for relative
        in dataset_files
    }

    assert (
        archive_files
        == expected_archive_files
    )

    for relative in sorted(
        dataset_files
    ):
        assert (
            archive.read(
                "dataset/"
                + relative
            )
            == (
                dataset_directory
                / relative
            ).read_bytes()
        )


# Exporting the same frozen dataset twice must
# produce byte-identical ZIP files.
second_archive = (
    TMP
    / "dataset-second.zip"
)


export_dataset_zip(
    dataset_directory,
    second_archive,
)


assert (
    sha256_file(
        archive_path
    )
    == sha256_file(
        second_archive
    )
)


# ---------------------------------------------------------
# Class validation.
# ---------------------------------------------------------

label_path = (
    dataset_directory
    / "labels"
    / "000001.txt"
)

original_label = (
    label_path.read_text(
        encoding="utf-8"
    )
)


label_path.write_text(
    "999 0.500000 0.500000 0.250000 0.250000\n",
    encoding="utf-8",
)


report = validate_dataset(
    dataset_directory
)


codes = {
    item[
        "code"
    ]
    for item
    in report[
        "errors"
    ]
}


assert (
    report[
        "status"
    ]
    == "FAIL"
)

assert (
    "yolo_unknown_class_id"
    in codes
)


# ---------------------------------------------------------
# Bbox validation.
# ---------------------------------------------------------

label_path.write_text(
    "0 0.500000 0.500000 1.500000 0.500000\n",
    encoding="utf-8",
)


report = validate_dataset(
    dataset_directory
)


codes = {
    item[
        "code"
    ]
    for item
    in report[
        "errors"
    ]
}


assert (
    "yolo_invalid_size"
    in codes
)

assert (
    "yolo_bbox_out_of_bounds"
    in codes
)


label_path.write_text(
    original_label,
    encoding="utf-8",
)


# ---------------------------------------------------------
# File validation.
# ---------------------------------------------------------

image_path = (
    dataset_directory
    / "images"
    / "000001.png"
)

original_image = (
    image_path.read_bytes()
)


image_path.unlink()


report = validate_dataset(
    dataset_directory
)


codes = {
    item[
        "code"
    ]
    for item
    in report[
        "errors"
    ]
}


assert (
    report[
        "status"
    ]
    == "FAIL"
)

assert (
    "image_missing"
    in codes
)


image_path.write_bytes(
    original_image
)


restored_validation = (
    validate_dataset(
        dataset_directory
    )
)


assert (
    restored_validation[
        "status"
    ]
    == "PASS"
)


# ---------------------------------------------------------
# Hash integrity detection.
# ---------------------------------------------------------

label_path.write_text(
    original_label
    + "\n",
    encoding="utf-8",
)


broken_hash_report = (
    verify_dataset_hashes(
        dataset_directory
    )
)


broken_codes = {
    item[
        "code"
    ]
    for item
    in broken_hash_report[
        "errors"
    ]
}


assert (
    broken_hash_report[
        "status"
    ]
    == "FAIL"
)

assert (
    (
        "file_hash_mismatch"
        in broken_codes
    )
    or (
        "file_size_mismatch"
        in broken_codes
    )
)


label_path.write_text(
    original_label,
    encoding="utf-8",
)


restored_hash_report = (
    verify_dataset_hashes(
        dataset_directory
    )
)


assert (
    restored_hash_report[
        "status"
    ]
    == "PASS"
)


print(
    "class_validation=True"
)

print(
    "bbox_validation=True"
)

print(
    "file_validation=True"
)

print(
    "hash_schema=bvt-dataset-hashes-1"
)

print(
    "hash_verification=True"
)

print(
    "hash_tamper_detection=True"
)

print(
    "zip_root=dataset/"
)

print(
    "zip_complete=True"
)

print(
    "zip_deterministic=True"
)

print(
    "BVT_DATASET_PRODUCTIZATION_INTEGRITY=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


shutil.rmtree(
    TMP
)
