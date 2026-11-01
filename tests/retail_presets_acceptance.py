import array
import hashlib
import json
from pathlib import Path

import bpy


ROOT = Path.cwd()

CLEAN = (
    ROOT
    / ".tmp"
    / "retail-demo-clean"
    / "dataset"
)

ARTIFACTS = (
    ROOT
    / ".tmp"
    / "retail-demo-artifacts"
    / "dataset"
)


EXPECTED_ARTIFACTS = [
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "frost",
    "dust",
    "water_drops",
    "scratches",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


def sha256_file(path):
    digest = hashlib.sha256(
        path.read_bytes()
    )

    return digest.hexdigest()


def decoded_hash(path):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        pixels = list(
            image.pixels[:]
        )

        values = array.array(
            "f",
            pixels,
        )

        return hashlib.sha256(
            values.tobytes()
        ).hexdigest()

    finally:
        bpy.data.images.remove(
            image
        )


assert CLEAN.is_dir()
assert ARTIFACTS.is_dir()


clean_manifest = json.loads(
    (
        CLEAN
        / "manifest.json"
    ).read_text(
        encoding="utf-8"
    )
)

artifact_manifest = json.loads(
    (
        ARTIFACTS
        / "manifest.json"
    ).read_text(
        encoding="utf-8"
    )
)


assert len(
    clean_manifest[
        "frames"
    ]
) == 5

assert len(
    artifact_manifest[
        "frames"
    ]
) == 5


clean_images = sorted(
    (
        CLEAN
        / "images"
    ).glob(
        "*.png"
    )
)

artifact_images = sorted(
    (
        ARTIFACTS
        / "images"
    ).glob(
        "*.png"
    )
)

clean_labels = sorted(
    (
        CLEAN
        / "labels"
    ).glob(
        "*.txt"
    )
)

artifact_labels = sorted(
    (
        ARTIFACTS
        / "labels"
    ).glob(
        "*.txt"
    )
)


assert len(
    clean_images
) == 5

assert len(
    artifact_images
) == 5

assert len(
    clean_labels
) == 5

assert len(
    artifact_labels
) == 5


# ---------------------------------------------------------
# Annotation contract.
# ---------------------------------------------------------

for path in (
    clean_labels
    + artifact_labels
):
    lines = [
        line
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(
        lines
    ) == 18

    classes = {
        int(
            line.split()[0]
        )
        for line
        in lines
    }

    assert classes == set(
        range(
            8
        )
    )


clean_label_hashes = [
    sha256_file(
        path
    )
    for path
    in clean_labels
]

artifact_label_hashes = [
    sha256_file(
        path
    )
    for path
    in artifact_labels
]


# Geometry/camera/placement are fixed.
assert len(
    set(
        clean_label_hashes
    )
) == 1

assert len(
    set(
        artifact_label_hashes
    )
) == 1


# Artifact Engine must not modify bbox/YOLO labels.
assert (
    clean_label_hashes
    == artifact_label_hashes
)


# ---------------------------------------------------------
# Artifact manifest contract.
# ---------------------------------------------------------

for frame in clean_manifest[
    "frames"
]:
    engine = frame[
        "artifacts"
    ]

    assert (
        engine[
            "enabled"
        ]
        is False
    )

    assert (
        engine[
            "version"
        ]
        == "artifact-engine-v1"
    )

    assert (
        engine[
            "artifacts"
        ]
        == []
    )


for frame in artifact_manifest[
    "frames"
]:
    engine = frame[
        "artifacts"
    ]

    assert (
        engine[
            "enabled"
        ]
        is True
    )

    assert (
        engine[
            "version"
        ]
        == "artifact-engine-v1"
    )

    records = engine[
        "artifacts"
    ]

    assert [
        record[
            "artifact"
        ]
        for record
        in records
    ] == EXPECTED_ARTIFACTS

    assert len(
        records
    ) == 11

    assert all(
        record[
            "enabled"
        ]
        is True
        for record
        in records
    )

    assert all(
        record[
            "applied"
        ]
        is True
        for record
        in records
    )


# ---------------------------------------------------------
# Image contract.
# ---------------------------------------------------------

clean_decoded = [
    decoded_hash(
        path
    )
    for path
    in clean_images
]

artifact_decoded = [
    decoded_hash(
        path
    )
    for path
    in artifact_images
]


# Clean scene has no active per-frame randomization.
assert len(
    set(
        clean_decoded
    )
) == 1


# Artifact seeds vary by frame.
assert len(
    set(
        artifact_decoded
    )
) > 1


# Every corresponding artifact frame must differ
# from the clean baseline.
for clean_hash, artifact_hash in zip(
    clean_decoded,
    artifact_decoded,
):
    assert (
        clean_hash
        != artifact_hash
    )


# ---------------------------------------------------------
# Validation.
# ---------------------------------------------------------

clean_validation = json.loads(
    (
        CLEAN
        / "validation.json"
    ).read_text(
        encoding="utf-8"
    )
)

artifact_validation = json.loads(
    (
        ARTIFACTS
        / "validation.json"
    ).read_text(
        encoding="utf-8"
    )
)


assert (
    clean_validation[
        "status"
    ]
    == "PASS"
)

assert (
    artifact_validation[
        "status"
    ]
    == "PASS"
)


print(
    "frames_per_preset=5"
)

print(
    "products_per_frame=18"
)

print(
    "sku_classes=8"
)

print(
    "clean_artifact_engine=False"
)

print(
    "artifacts_artifact_engine=True"
)

print(
    "artifact_providers=11"
)

print(
    "labels_equal_between_presets=True"
)

print(
    "clean_unique_decoded_images="
    + str(
        len(
            set(
                clean_decoded
            )
        )
    )
)

print(
    "artifact_unique_decoded_images="
    + str(
        len(
            set(
                artifact_decoded
            )
        )
    )
)

print(
    "clean_vs_artifacts_pixels_different=True"
)

print(
    "clean_validation=PASS"
)

print(
    "artifacts_validation=PASS"
)

print(
    "BVT_RETAIL_PRESETS_SMOKE=OK"
)

print(
    "RESULT=PASS"
)
