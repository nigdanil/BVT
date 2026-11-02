import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TESTS = ROOT / "tests"

BASELINE = (
    ROOT
    / ".tmp"
    / "dataset-productization-repro-baseline"
    / "dataset"
)

CURRENT = (
    ROOT
    / ".tmp"
    / "dataset-productization-repro"
    / "dataset"
)


sys.path.insert(
    0,
    str(
        SOURCE
    ),
)

sys.path.insert(
    0,
    str(
        TESTS
    ),
)


from bvt.export.hashes import verify_dataset_hashes
from png_pixel_utils import decoded_png_hash


assert BASELINE.is_dir()
assert CURRENT.is_dir()


baseline_hash_report = (
    verify_dataset_hashes(
        BASELINE
    )
)

current_hash_report = (
    verify_dataset_hashes(
        CURRENT
    )
)


assert (
    baseline_hash_report[
        "status"
    ]
    == "PASS"
)

assert (
    current_hash_report[
        "status"
    ]
    == "PASS"
)


# These files describe deterministic structural state.
exact_files = [
    "manifest.json",
    "classes.txt",
    "config/generation.json",
    "splits/train.txt",
    "splits/validation.txt",
    "splits/test.txt",
    "statistics.json",
    "health.json",
    "validation.json",
]


for relative in exact_files:
    baseline_path = (
        BASELINE
        / relative
    )

    current_path = (
        CURRENT
        / relative
    )

    assert baseline_path.is_file()
    assert current_path.is_file()

    assert (
        baseline_path.read_bytes()
        == current_path.read_bytes()
    ), relative


baseline_manifest = json.loads(
    (
        BASELINE
        / "manifest.json"
    ).read_text(
        encoding="utf-8"
    )
)

current_manifest = json.loads(
    (
        CURRENT
        / "manifest.json"
    ).read_text(
        encoding="utf-8"
    )
)


assert (
    baseline_manifest
    == current_manifest
)

assert len(
    baseline_manifest[
        "frames"
    ]
) == 12


baseline_frame_seeds = [
    frame[
        "frame_seed"
    ]
    for frame
    in baseline_manifest[
        "frames"
    ]
]

current_frame_seeds = [
    frame[
        "frame_seed"
    ]
    for frame
    in current_manifest[
        "frames"
    ]
]


assert (
    baseline_frame_seeds
    == current_frame_seeds
)

assert len(
    set(
        baseline_frame_seeds
    )
) == 12


baseline_labels = sorted(
    (
        BASELINE
        / "labels"
    ).glob(
        "*.txt"
    )
)

current_labels = sorted(
    (
        CURRENT
        / "labels"
    ).glob(
        "*.txt"
    )
)


assert len(
    baseline_labels
) == 12

assert len(
    current_labels
) == 12


for baseline_path, current_path in zip(
    baseline_labels,
    current_labels,
):
    assert (
        baseline_path.name
        == current_path.name
    )

    assert (
        baseline_path.read_bytes()
        == current_path.read_bytes()
    )


baseline_images = sorted(
    (
        BASELINE
        / "images"
    ).glob(
        "*.png"
    )
)

current_images = sorted(
    (
        CURRENT
        / "images"
    ).glob(
        "*.png"
    )
)


assert len(
    baseline_images
) == 12

assert len(
    current_images
) == 12


decoded_hashes_equal = []


for baseline_path, current_path in zip(
    baseline_images,
    current_images,
):
    assert (
        baseline_path.name
        == current_path.name
    )

    equal = (
        decoded_png_hash(
            baseline_path
        )
        == decoded_png_hash(
            current_path
        )
    )

    decoded_hashes_equal.append(
        equal
    )


assert all(
    decoded_hashes_equal
)


# PNG container bytes are deliberately NOT the
# reproducibility contract. hashes.json protects
# integrity within each generated dataset; decoded
# image pixels define cross-run RGB reproducibility.
baseline_png_byte_hashes = {
    item[
        "path"
    ]: item[
        "sha256"
    ]
    for item
    in json.loads(
        (
            BASELINE
            / "hashes.json"
        ).read_text(
            encoding="utf-8"
        )
    )[
        "files"
    ]
    if item[
        "path"
    ].startswith(
        "images/"
    )
}


current_png_byte_hashes = {
    item[
        "path"
    ]: item[
        "sha256"
    ]
    for item
    in json.loads(
        (
            CURRENT
            / "hashes.json"
        ).read_text(
            encoding="utf-8"
        )
    )[
        "files"
    ]
    if item[
        "path"
    ].startswith(
        "images/"
    )
}


print(
    "repro_frames=12"
)

print(
    "repro_manifest_equal=True"
)

print(
    "repro_config_equal=True"
)

print(
    "repro_splits_equal=True"
)

print(
    "repro_statistics_equal=True"
)

print(
    "repro_health_equal=True"
)

print(
    "repro_validation_equal=True"
)

print(
    "repro_labels_equal=True"
)

print(
    "repro_frame_seeds_equal=True"
)

print(
    "repro_decoded_rgb_equal=True"
)

print(
    "png_container_hashes_equal="
    + str(
        baseline_png_byte_hashes
        == current_png_byte_hashes
    )
)

print(
    "BVT_DATASET_PRODUCTIZATION_REPRODUCIBILITY=OK"
)

print(
    "RESULT=PASS"
)
