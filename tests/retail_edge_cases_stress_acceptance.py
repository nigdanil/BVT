import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TESTS = (
    ROOT
    / "tests"
)

sys.path.insert(
    0,
    str(TESTS),
)


from png_pixel_utils import decoded_png_hash


DATASET = (
    ROOT
    / ".tmp"
    / "retail-edge-case-stress"
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


assert (
    validation[
        "status"
    ]
    == "PASS"
)


frames = manifest[
    "frames"
]


assert len(
    frames
) == 20


assert len(
    manifest[
        "annotations"
    ][
        "classes"
    ]
) == 8


# ---------------------------------------------------------
# Frozen EP4 structural contract.
# ---------------------------------------------------------

expected_edge_case_order = [
    "wrong_angle",
    "wrong_position",
    "empty_slot",
    "occlusion",
]


selected_targets = {
    edge_case: set()
    for edge_case
    in expected_edge_case_order
}


edge_case_seeds = {
    edge_case: set()
    for edge_case
    in expected_edge_case_order
}


# ---------------------------------------------------------
# Frozen Artifact Engine v1 contract.
# ---------------------------------------------------------

expected_artifact_order = [
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


expected_artifact_record_fields = {
    "artifact",
    "category",
    "description",
    "stage",
    "execution_order",
    "enabled",
    "probability",
    "intensity",
    "options",
    "seed",
    "decision_roll",
    "applied",
    "affected_objects",
    "affected_camera",
    "affected_materials",
    "parameters",
    "compatibility_rules",
}


artifact_ids = set()


artifact_seeds = {
    artifact_id: set()
    for artifact_id
    in expected_artifact_order
}


frame_seeds = set()


# ---------------------------------------------------------
# Frame audit.
# ---------------------------------------------------------

for frame in frames:
    frame_seed = (
        frame[
            "frame_seed"
        ]
    )


    assert (
        frame_seed
        not in frame_seeds
    )


    frame_seeds.add(
        frame_seed
    )


    # -----------------------------------------------------
    # Retail structural edge cases.
    # -----------------------------------------------------

    edge_case_block = (
        frame[
            "retail_edge_cases"
        ]
    )


    assert (
        edge_case_block[
            "enabled"
        ]
        is True
    )

    assert (
        edge_case_block[
            "version"
        ]
        == "retail-edge-cases-v0.1"
    )

    assert (
        edge_case_block[
            "seed_strategy"
        ]
        == "sha256-namespace-v1"
    )


    events = (
        edge_case_block[
            "events"
        ]
    )


    assert len(
        events
    ) == 4


    current_edge_case_order = [
        event[
            "edge_case"
        ]
        for event
        in events
    ]


    assert (
        current_edge_case_order
        == expected_edge_case_order
    )


    by_case = {
        event[
            "edge_case"
        ]: event
        for event
        in events
    }


    for edge_case in (
        expected_edge_case_order
    ):
        event = by_case[
            edge_case
        ]


        assert (
            event[
                "applied"
            ]
            is True
        )

        assert (
            "before"
            in event
        )

        assert (
            "after"
            in event
        )


        edge_seed = (
            event[
                "seed"
            ]
        )


        assert (
            edge_seed
            not in edge_case_seeds[
                edge_case
            ]
        )


        edge_case_seeds[
            edge_case
        ].add(
            edge_seed
        )


        selected_targets[
            edge_case
        ].add(
            event[
                "instance_id"
            ]
        )


    empty_instance = (
        by_case[
            "empty_slot"
        ][
            "instance_id"
        ]
    )


    occlusion_instance = (
        by_case[
            "occlusion"
        ][
            "instance_id"
        ]
    )


    # Occlusion target is selected only from
    # products still visible after Empty Slot.
    assert (
        empty_instance
        != occlusion_instance
    )


    # -----------------------------------------------------
    # Final annotations.
    # -----------------------------------------------------

    objects = frame[
        "objects"
    ]


    assert len(
        objects
    ) == 17


    instance_ids = {
        item[
            "instance_id"
        ]
        for item
        in objects
    }


    assert (
        empty_instance
        not in instance_ids
    )

    assert (
        occlusion_instance
        in instance_ids
    )


    for item in objects:
        bbox = item[
            "bbox_yolo"
        ]


        x_center = float(
            bbox[0]
        )

        y_center = float(
            bbox[1]
        )

        width = float(
            bbox[2]
        )

        height = float(
            bbox[3]
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


    # -----------------------------------------------------
    # Frozen Artifact Engine v1 manifest.
    # -----------------------------------------------------

    artifact_block = frame[
        "artifacts"
    ]


    assert (
        artifact_block[
            "enabled"
        ]
        is True
    )

    assert (
        artifact_block[
            "version"
        ]
        == "artifact-engine-v1"
    )


    artifact_records = (
        artifact_block[
            "artifacts"
        ]
    )


    assert len(
        artifact_records
    ) == 11


    current_artifact_order = [
        record[
            "artifact"
        ]
        for record
        in artifact_records
    ]


    assert (
        current_artifact_order
        == expected_artifact_order
    )


    for record in artifact_records:
        assert (
            set(
                record
            )
            == expected_artifact_record_fields
        )


        artifact_id = (
            record[
                "artifact"
            ]
        )


        assert (
            artifact_id
            in artifact_seeds
        )

        assert (
            record[
                "enabled"
            ]
            is True
        )

        # Stress preset has probability 1.0
        # for all eleven providers.
        assert (
            float(
                record[
                    "probability"
                ]
            )
            == 1.0
        )

        assert (
            record[
                "applied"
            ]
            is True
        )


        artifact_seed = (
            record[
                "seed"
            ]
        )


        assert (
            artifact_seed
            not in artifact_seeds[
                artifact_id
            ]
        )


        artifact_seeds[
            artifact_id
        ].add(
            artifact_seed
        )


        artifact_ids.add(
            artifact_id
        )


    # -----------------------------------------------------
    # YOLO file.
    # -----------------------------------------------------

    label_path = (
        DATASET
        / frame[
            "label"
        ]
    )


    assert label_path.is_file()


    label_rows = [
        line
        for line
        in label_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


    assert len(
        label_rows
    ) == 17


# ---------------------------------------------------------
# Cross-frame deterministic coverage.
# ---------------------------------------------------------

assert (
    artifact_ids
    == set(
        expected_artifact_order
    )
)


for artifact_id in (
    expected_artifact_order
):
    assert len(
        artifact_seeds[
            artifact_id
        ]
    ) == 20


for edge_case in (
    expected_edge_case_order
):
    assert len(
        edge_case_seeds[
            edge_case
        ]
    ) == 20


    # Twenty deterministic draws should exercise
    # several physical product instances.
    assert len(
        selected_targets[
            edge_case
        ]
    ) >= 5


assert len(
    frame_seeds
) == 20


# ---------------------------------------------------------
# Real decoded pixel diversity.
# ---------------------------------------------------------

image_paths = sorted(
    (
        DATASET
        / "images"
    ).glob(
        "*.png"
    )
)


assert len(
    image_paths
) == 20


decoded_hashes = [
    decoded_png_hash(
        path
    )
    for path
    in image_paths
]


assert len(
    set(
        decoded_hashes
    )
) == 20


# ---------------------------------------------------------
# Result.
# ---------------------------------------------------------

print(
    "frames=20"
)

print(
    "classes=8"
)

print(
    "objects_per_frame=17"
)

print(
    "yolo_rows_per_frame=17"
)

print(
    "edge_cases_per_frame=4"
)

print(
    "artifact_providers=11"
)

print(
    "artifact_ids="
    + ",".join(
        expected_artifact_order
    )
)

print(
    "artifact_records_per_frame=11"
)

print(
    "artifact_record_fields=17"
)

print(
    "artifact_seeds_unique_per_provider=20"
)

print(
    "artifact_engine_version=artifact-engine-v1"
)


for edge_case in (
    expected_edge_case_order
):
    print(
        edge_case
        + "_unique_targets="
        + str(
            len(
                selected_targets[
                    edge_case
                ]
            )
        )
    )


print(
    "frame_seeds_unique=20"
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
    "validation_status=PASS"
)

print(
    "bbox_normalized=True"
)

print(
    "empty_slot_excluded=True"
)

print(
    "occlusion_target_preserved=True"
)

print(
    "artifact_engine_v1_compatible=True"
)

print(
    "BVT_RETAIL_EDGE_CASE_STRESS=OK"
)

print(
    "RESULT=PASS"
)
