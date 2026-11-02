import json
import subprocess
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


PLAN = (
    ROOT
    / "benchmarks"
    / "real"
    / "capture-plan-v0.1.json"
)


CLASSES = (
    ROOT
    / "benchmarks"
    / "real"
    / "classes-v0.1.txt"
)


ANNOTATION = (
    ROOT
    / "benchmarks"
    / "real"
    / "ANNOTATION_POLICY-v0.1.md"
)


CONTRACT = (
    ROOT
    / "docs"
    / "contracts"
    / "Real-Dataset-v0.1.md"
)


VALIDATOR = (
    ROOT
    / "benchmarks"
    / "scripts"
    / "real_dataset_validator.py"
)


INITIALIZER = (
    ROOT
    / "benchmarks"
    / "scripts"
    / "init_real_dataset.py"
)


PROTOCOL = (
    ROOT
    / "benchmarks"
    / "protocol-v0.1.json"
)


REQUIREMENTS = (
    ROOT
    / "benchmarks"
    / "real"
    / "requirements-v0.1.txt"
)


for path in (
    PLAN,
    CLASSES,
    ANNOTATION,
    CONTRACT,
    VALIDATOR,
    INITIALIZER,
    PROTOCOL,
    REQUIREMENTS,
):
    assert path.is_file(), path


requirements = REQUIREMENTS.read_text(
    encoding="utf-8"
)


assert (
    "Pillow==13.0.0"
    in requirements
)


plan = json.loads(
    PLAN.read_text(
        encoding="utf-8"
    )
)


assert (
    plan[
        "schema_version"
    ]
    == "bvt-real-dataset-capture-plan-1"
)


assert (
    plan[
        "dataset_version"
    ]
    == "0.1.0"
)


classes = [
    line.strip()
    for line
    in CLASSES.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]


assert classes == [
    "bev_can_red_330",
    "bev_can_blue_330",
    "bev_bottle_green_500",
    "bev_bottle_amber_500",
    "bev_carton_orange_1000",
    "bev_carton_white_1000",
    "bev_box_purple_250",
    "bev_box_yellow_250",
]


assert (
    plan[
        "capture_target"
    ][
        "session_count"
    ]
    == 10
)


assert (
    plan[
        "capture_target"
    ][
        "total_images"
    ]
    == 500
)


sessions = plan[
    "sessions"
]


assert len(
    sessions
) == 10


assert len(
    {
        item[
            "session_id"
        ]
        for item
        in sessions
    }
) == 10


split_sessions = {
    "train": [],
    "validation": [],
    "test": [],
}


split_images = {
    "train": 0,
    "validation": 0,
    "test": 0,
}


for session in sessions:
    split = session[
        "split"
    ]

    split_sessions[
        split
    ].append(
        session[
            "session_id"
        ]
    )

    split_images[
        split
    ] += session[
        "target_images"
    ]


assert {
    key: len(
        value
    )
    for key, value
    in split_sessions.items()
} == {
    "train": 7,
    "validation": 1,
    "test": 2,
}


assert split_images == {
    "train": 350,
    "validation": 50,
    "test": 100,
}


assert split_sessions[
    "test"
] == [
    "R09",
    "R10",
]


leakage = plan[
    "leakage_policy"
]


assert (
    leakage[
        "exact_duplicate_images_allowed"
    ]
    is False
)


assert (
    leakage[
        "cross_split_near_duplicates_allowed"
    ]
    is False
)


assert (
    leakage[
        "near_duplicate_algorithm"
    ]
    == "dHash-64"
)


assert (
    leakage[
        "near_duplicate_hamming_threshold"
    ]
    == 4
)


assert (
    leakage[
        "real_test_used_for_training"
    ]
    is False
)


assert (
    plan[
        "privacy_policy"
    ][
        "gps_exif_allowed"
    ]
    is False
)


protocol = json.loads(
    PROTOCOL.read_text(
        encoding="utf-8"
    )
)


real = protocol[
    "real_dataset"
]


assert (
    real[
        "foundation_status"
    ]
    == "frozen-data-not-yet-collected"
)


assert (
    real[
        "target_total_images"
    ]
    == 500
)


assert (
    real[
        "planned_split_images"
    ]
    == {
        "train": 350,
        "validation": 50,
        "test": 100,
    }
)


assert (
    real[
        "test_set"
    ][
        "immutable_after_freeze"
    ]
    is True
)


backlog = (
    ROOT
    / "docs"
    / "Backlog.md"
).read_text(
    encoding="utf-8"
)


ep7 = backlog.split(
    "## EP7 — YOLO Benchmark / Sim-to-Real / Research",
    1,
)[1].split(
    "# Milestone 0",
    1,
)[0]


assert (
    "- [ ] Separate real test set."
    in ep7
)


assert (
    "- [ ] Real-only baseline."
    in ep7
)


assert (
    "- [ ] Real + Synthetic training."
    in ep7
)


ignored = subprocess.run(
    [
        "git",
        "check-ignore",
        "-q",
        (
            "benchmarks/real/"
            "data-v0.1/"
            "images/R01/example.jpg"
        ),
    ],
    cwd=ROOT,
    check=False,
)


assert (
    ignored.returncode
    == 0
)


print(
    "real_classes=8"
)

print(
    "real_sessions=10"
)

print(
    "real_train_images_planned=350"
)

print(
    "real_validation_images_planned=50"
)

print(
    "real_test_images_planned=100"
)

print(
    "real_split_unit=capture_session"
)

print(
    "real_near_duplicate_guard=dHash-64"
)

print(
    "real_test_completed=False"
)

print(
    "BVT_REAL_DATASET_FOUNDATION=OK"
)

print(
    "RESULT=PASS"
)
