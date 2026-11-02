import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

DATASET_ROOT = (
    ROOT
    / ".tmp"
    / "dataset-productization-120"
)

DATASET = (
    DATASET_ROOT
    / "dataset"
)

ARCHIVE = (
    DATASET_ROOT
    / "dataset.zip"
)


sys.path.insert(
    0,
    str(
        SOURCE
    ),
)


from bvt.export.hashes import verify_dataset_hashes
from bvt.validation.dataset import validate_dataset


assert DATASET.is_dir()
assert ARCHIVE.is_file()


manifest_path = (
    DATASET
    / "manifest.json"
)

statistics_path = (
    DATASET
    / "statistics.json"
)

health_path = (
    DATASET
    / "health.json"
)

validation_path = (
    DATASET
    / "validation.json"
)


for path in (
    manifest_path,
    statistics_path,
    health_path,
    validation_path,
    DATASET / "hashes.json",
    DATASET / "config" / "generation.json",
    DATASET / "splits" / "train.txt",
    DATASET / "splits" / "validation.txt",
    DATASET / "splits" / "test.txt",
):
    assert path.is_file(), path


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

validation = json.loads(
    validation_path.read_text(
        encoding="utf-8"
    )
)


frames = manifest[
    "frames"
]


assert (
    manifest[
        "schema_version"
    ]
    == "bvt-dataset-manifest-2"
)

assert len(
    frames
) == 120

assert (
    manifest[
        "generation"
    ][
        "frame_count"
    ]
    == 120
)

assert (
    manifest[
        "generation"
    ][
        "seed"
    ]
    == 20261102
)


frame_ids = [
    frame[
        "frame_id"
    ]
    for frame
    in frames
]


assert len(
    frame_ids
) == 120

assert len(
    set(
        frame_ids
    )
) == 120


frame_seeds = [
    frame[
        "frame_seed"
    ]
    for frame
    in frames
]


assert len(
    set(
        frame_seeds
    )
) == 120


assert (
    manifest[
        "splits"
    ][
        "counts"
    ]
    == {
        "train": 96,
        "validation": 12,
        "test": 12,
    }
)


for frame in frames:
    assert len(
        frame[
            "objects"
        ]
    ) == 18


images = sorted(
    (
        DATASET
        / "images"
    ).glob(
        "*.png"
    )
)

labels = sorted(
    (
        DATASET
        / "labels"
    ).glob(
        "*.txt"
    )
)


assert len(
    images
) == 120

assert len(
    labels
) == 120


assert (
    statistics[
        "frames"
    ]
    == 120
)

assert (
    statistics[
        "images"
    ]
    == 120
)

assert (
    statistics[
        "labels"
    ]
    == 120
)

assert (
    statistics[
        "objects"
    ]
    == 2160
)

assert (
    statistics[
        "classes"
    ][
        "count"
    ]
    == 8
)

assert (
    statistics[
        "empty_label_frames"
    ]
    == 0
)

assert (
    statistics[
        "splits"
    ]
    == {
        "train": 96,
        "validation": 12,
        "test": 12,
    }
)


assert (
    validation[
        "status"
    ]
    == "PASS"
)

assert (
    health[
        "status"
    ]
    == "PASS"
)


fresh_validation = (
    validate_dataset(
        DATASET
    )
)


assert (
    fresh_validation[
        "status"
    ]
    == "PASS"
)


hash_report = (
    verify_dataset_hashes(
        DATASET
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


dataset_files = {
    path.relative_to(
        DATASET
    ).as_posix()
    for path
    in DATASET.rglob(
        "*"
    )
    if path.is_file()
}


with zipfile.ZipFile(
    ARCHIVE,
    "r",
) as archive:
    archived_files = set(
        archive.namelist()
    )


assert (
    archived_files
    == {
        "dataset/"
        + relative
        for relative
        in dataset_files
    }
)


print(
    "batch_frames=120"
)

print(
    "batch_images=120"
)

print(
    "batch_labels=120"
)

print(
    "batch_objects=2160"
)

print(
    "batch_classes=8"
)

print(
    "batch_split=96/12/12"
)

print(
    "batch_validation=PASS"
)

print(
    "batch_health=PASS"
)

print(
    "batch_hashes=PASS"
)

print(
    "batch_zip_complete=True"
)

print(
    "BVT_DATASET_PRODUCTIZATION_120_ACCEPTANCE=OK"
)

print(
    "RESULT=PASS"
)
