import array
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import bpy


ROOT = Path.cwd()

DATASET = (
    ROOT
    / ".tmp"
    / "retail-foundation-100"
    / "dataset"
)

MANIFEST_PATH = (
    DATASET
    / "manifest.json"
)

VALIDATION_PATH = (
    DATASET
    / "validation.json"
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


def sha256_file(
    path,
):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def decoded_hash(
    path,
):
    image = bpy.data.images.load(
        str(
            path
        ),
        check_existing=False,
    )

    try:
        assert (
            tuple(
                image.size
            )
            == (
                512,
                512,
            )
        )

        values = array.array(
            "f",
            image.pixels[:],
        )

        return hashlib.sha256(
            values.tobytes()
        ).hexdigest()

    finally:
        bpy.data.images.remove(
            image
        )


assert DATASET.is_dir()
assert MANIFEST_PATH.is_file()
assert VALIDATION_PATH.is_file()


manifest = json.loads(
    MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)

validation = json.loads(
    VALIDATION_PATH.read_text(
        encoding="utf-8"
    )
)


# ---------------------------------------------------------
# Dataset contract.
# ---------------------------------------------------------

assert (
    manifest[
        "schema_version"
    ]
    == "bvt-dataset-manifest-1"
)

assert (
    manifest[
        "generation"
    ][
        "seed"
    ]
    == 20261101
)

assert (
    manifest[
        "generation"
    ][
        "frame_count"
    ]
    == 100
)

assert (
    manifest[
        "generation"
    ][
        "frame_seed_strategy"
    ]
    == "sha256-v1"
)


frames = manifest[
    "frames"
]

assert len(
    frames
) == 100


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
) == 100

assert len(
    labels
) == 100


expected_names = [
    f"{index:06d}"
    for index
    in range(
        1,
        101,
    )
]


assert [
    path.stem
    for path
    in images
] == expected_names

assert [
    path.stem
    for path
    in labels
] == expected_names


# ---------------------------------------------------------
# Manifest frame / Artifact Engine contract.
# ---------------------------------------------------------

frame_ids = []
frame_seeds = []
artifact_seeds = defaultdict(
    list
)


for index, frame in enumerate(
    frames,
    start=1,
):
    expected_id = (
        f"{index:06d}"
    )

    assert (
        frame[
            "frame_id"
        ]
        == expected_id
    )

    assert (
        frame[
            "image"
        ]
        == (
            "images/"
            + expected_id
            + ".png"
        )
    )

    frame_ids.append(
        frame[
            "frame_id"
        ]
    )

    frame_seeds.append(
        frame[
            "frame_seed"
        ]
    )

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

    assert len(
        records
    ) == 11

    assert [
        record[
            "artifact"
        ]
        for record
        in records
    ] == EXPECTED_ARTIFACTS

    for record in records:
        assert (
            record[
                "enabled"
            ]
            is True
        )

        assert (
            record[
                "probability"
            ]
            == 1.0
        )

        assert (
            record[
                "applied"
            ]
            is True
        )

        artifact_seeds[
            record[
                "artifact"
            ]
        ].append(
            record[
                "seed"
            ]
        )


assert len(
    set(
        frame_ids
    )
) == 100

assert len(
    set(
        frame_seeds
    )
) == 100


for artifact_id in EXPECTED_ARTIFACTS:
    seeds = artifact_seeds[
        artifact_id
    ]

    assert len(
        seeds
    ) == 100

    assert len(
        set(
            seeds
        )
    ) == 100


# ---------------------------------------------------------
# YOLO / bbox contract.
# ---------------------------------------------------------

label_hashes = []

total_boxes = 0

class_box_counts = {
    class_id: 0
    for class_id
    in range(
        8
    )
}


for path in labels:
    lines = [
        line.strip()
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(
        lines
    ) == 18

    frame_classes = set()

    for line in lines:
        parts = line.split()

        assert len(
            parts
        ) == 5

        class_id = int(
            parts[0]
        )

        assert (
            0
            <= class_id
            <= 7
        )

        x_center = float(
            parts[1]
        )

        y_center = float(
            parts[2]
        )

        width = float(
            parts[3]
        )

        height = float(
            parts[4]
        )

        assert (
            0.0
            <= x_center
            <= 1.0
        )

        assert (
            0.0
            <= y_center
            <= 1.0
        )

        assert (
            0.0
            < width
            <= 1.0
        )

        assert (
            0.0
            < height
            <= 1.0
        )

        assert (
            x_center
            - width / 2.0
            >= -1e-6
        )

        assert (
            x_center
            + width / 2.0
            <= 1.0 + 1e-6
        )

        assert (
            y_center
            - height / 2.0
            >= -1e-6
        )

        assert (
            y_center
            + height / 2.0
            <= 1.0 + 1e-6
        )

        frame_classes.add(
            class_id
        )

        class_box_counts[
            class_id
        ] += 1

        total_boxes += 1

    assert (
        frame_classes
        == set(
            range(
                8
            )
        )
    )

    label_hashes.append(
        sha256_file(
            path
        )
    )


assert (
    total_boxes
    == 1800
)


# No geometry/camera/placement randomization in EP3
# acceptance. All annotation files must therefore match.
assert len(
    set(
        label_hashes
    )
) == 1


# Every class must appear in the full dataset.
assert set(
    class_box_counts
) == set(
    range(
        8
    )
)

assert all(
    count > 0
    for count
    in class_box_counts.values()
)


# ---------------------------------------------------------
# RGB diversity contract.
# ---------------------------------------------------------

decoded_hashes = [
    decoded_hash(
        path
    )
    for path
    in images
]


# Artifact subseeds vary on every frame, therefore
# acceptance output must contain real visual diversity.
assert len(
    set(
        decoded_hashes
    )
) > 1


# ---------------------------------------------------------
# Dataset validation.
# ---------------------------------------------------------

assert (
    validation[
        "status"
    ]
    == "PASS"
)


print(
    "frames=100"
)

print(
    "images=100"
)

print(
    "labels=100"
)

print(
    "products_per_frame=18"
)

print(
    "total_yolo_boxes="
    + str(
        total_boxes
    )
)

print(
    "sku_classes=8"
)

print(
    "frame_ids_unique=100"
)

print(
    "frame_seeds_unique=100"
)

print(
    "artifact_providers=11"
)

print(
    "artifact_seeds_unique_per_provider=100"
)

print(
    "label_hashes_unique="
    + str(
        len(
            set(
                label_hashes
            )
        )
    )
)

print(
    "decoded_images_unique="
    + str(
        len(
            set(
                decoded_hashes
            )
        )
    )
)

print(
    "bbox_normalized=True"
)

print(
    "bbox_inside_frame=True"
)

print(
    "all_classes_present=True"
)

print(
    "manifest_status=PASS"
)

print(
    "validation_status="
    + validation[
        "status"
    ]
)

print(
    "BVT_RETAIL_ACCEPTANCE_100=OK"
)

print(
    "RESULT=PASS"
)
