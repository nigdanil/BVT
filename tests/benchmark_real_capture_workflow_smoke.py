import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


SHOT_PLAN = (
    ROOT
    / "benchmarks"
    / "real"
    / "r01-shot-plan-v0.1.json"
)


CAPTURE_CARD = (
    ROOT
    / "benchmarks"
    / "real"
    / "R01_CAPTURE_CARD-v0.1.md"
)


IMPORTER = (
    ROOT
    / "benchmarks"
    / "scripts"
    / "import_real_session.py"
)


SELFTEST = (
    ROOT
    / "benchmarks"
    / "scripts"
    / "selftest_import_real_session.py"
)


for path in (
    SHOT_PLAN,
    CAPTURE_CARD,
    IMPORTER,
    SELFTEST,
):
    assert path.is_file(), path


plan = json.loads(
    SHOT_PLAN.read_text(
        encoding="utf-8"
    )
)


assert (
    plan[
        "schema_version"
    ]
    == "bvt-real-shot-plan-1"
)


assert (
    plan[
        "session_id"
    ]
    == "R01"
)


assert (
    plan[
        "split"
    ]
    == "train"
)


assert (
    plan[
        "target_images"
    ]
    == 50
)


groups = plan[
    "groups"
]


assert len(
    groups
) == 5


assert sum(
    group[
        "count"
    ]
    for group
    in groups
) == 50


assert [
    group[
        "group_id"
    ]
    for group
    in groups
] == [
    "R01-A",
    "R01-B",
    "R01-C",
    "R01-D",
    "R01-E",
]


assert (
    plan[
        "requirements"
    ][
        "gps_exif_allowed"
    ]
    is False
)


assert (
    plan[
        "requirements"
    ][
        "exact_duplicate_frames_allowed"
    ]
    is False
)


assert (
    plan[
        "acceptance"
    ][
        "minimum_visible_instances_per_class_in_session"
    ]
    == 10
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


print(
    "r01_session=R01"
)

print(
    "r01_split=train"
)

print(
    "r01_target_images=50"
)

print(
    "r01_capture_groups=5"
)

print(
    "r01_importer_ready=True"
)

print(
    "real_test_completed=False"
)

print(
    "BVT_REAL_CAPTURE_WORKFLOW=OK"
)

print(
    "RESULT=PASS"
)
