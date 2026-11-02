import json
import subprocess
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


PROTOCOL_PATH = (
    ROOT
    / "benchmarks"
    / "protocol-v0.1.json"
)


REQUIREMENTS_PATH = (
    ROOT
    / "benchmarks"
    / "requirements-v0.1.txt"
)


CONTRACT_PATH = (
    ROOT
    / "docs"
    / "contracts"
    / "Benchmark-v0.1.md"
)


assert PROTOCOL_PATH.is_file()
assert REQUIREMENTS_PATH.is_file()
assert CONTRACT_PATH.is_file()


protocol = json.loads(
    PROTOCOL_PATH.read_text(
        encoding="utf-8"
    )
)


assert (
    protocol[
        "schema_version"
    ]
    == "bvt-benchmark-protocol-1"
)


assert (
    protocol[
        "protocol_version"
    ]
    == "0.1.0"
)


baseline = protocol[
    "baseline"
]


assert (
    baseline[
        "bvt_release"
    ]
    == "v0.1.0"
)


assert (
    baseline[
        "bvt_release_commit"
    ]
    == "d40fb3c72386c4c87c55bee2e2e4b0f4f0090bd7"
)


assert (
    baseline[
        "blender_version"
    ]
    == "5.2.3 LTS"
)


assert (
    baseline[
        "ultralytics_version"
    ]
    == "8.4.198"
)


assert (
    baseline[
        "model"
    ]
    == "yolo11n.pt"
)


assert (
    baseline[
        "task"
    ]
    == "detect"
)


assert (
    baseline[
        "model_weights_hash_required_before_training"
    ]
    is True
)


model_hash = baseline[
    "model_weights_sha256"
]


assert isinstance(
    model_hash,
    str,
)

assert len(
    model_hash
) == 64

int(
    model_hash,
    16,
)


assert (
    baseline[
        "environment_lock"
    ]
    == "benchmarks/environment-v0.1.json"
)


requirements = (
    REQUIREMENTS_PATH.read_text(
        encoding="utf-8"
    )
)


assert (
    "ultralytics==8.4.198"
    in requirements
)


synthetic = protocol[
    "synthetic_datasets"
]


profiles = synthetic[
    "profiles"
]


assert set(
    profiles
) == {
    "clean",
    "balanced",
    "artifacts",
    "stress",
}


assert (
    synthetic[
        "publication_frames_per_training_profile"
    ]
    == 1000
)


assert (
    profiles[
        "clean"
    ][
        "training_allowed"
    ]
    is True
)


assert (
    profiles[
        "balanced"
    ][
        "training_allowed"
    ]
    is True
)


assert (
    profiles[
        "artifacts"
    ][
        "training_allowed"
    ]
    is True
)


assert (
    profiles[
        "stress"
    ][
        "training_allowed"
    ]
    is False
)


assert (
    profiles[
        "stress"
    ][
        "publication_frames"
    ]
    == 250
)


split = synthetic[
    "split"
]


assert abs(
    (
        split[
            "train"
        ]
        + split[
            "validation"
        ]
        + split[
            "test"
        ]
    )
    - 1.0
) < 1e-9


real_dataset = protocol[
    "real_dataset"
]


assert (
    real_dataset[
        "grouping_unit"
    ]
    == "capture_session"
)


assert (
    real_dataset[
        "test_set"
    ][
        "name"
    ]
    == "real_test"
)


assert (
    real_dataset[
        "test_set"
    ][
        "immutable_after_freeze"
    ]
    is True
)


experiments = protocol[
    "experiment_matrix"
]


assert [
    item[
        "id"
    ]
    for item
    in experiments
] == [
    "E01",
    "E02",
    "E03",
    "E04",
    "E05",
]


for experiment in experiments:
    assert (
        experiment[
            "primary_evaluation"
        ]
        == "real_test"
    )

    assert (
        "real_test"
        not in experiment[
            "training_sources"
        ]
    )

    assert (
        experiment[
            "validation_source"
        ]
        != "real_test"
    )


training = protocol[
    "training"
]


assert (
    training[
        "epochs"
    ]
    == 100
)


assert (
    training[
        "imgsz"
    ]
    == 640
)


assert (
    training[
        "batch"
    ]
    == 8
)


assert (
    training[
        "optimizer"
    ]
    == "AdamW"
)


assert (
    training[
        "deterministic"
    ]
    is True
)


publication_seeds = training[
    "publication_seeds"
]


assert len(
    publication_seeds
) == 3


assert len(
    set(
        publication_seeds
    )
) == 3


evaluation = protocol[
    "evaluation"
]


assert (
    evaluation[
        "primary_dataset"
    ]
    == "real_test"
)


assert (
    evaluation[
        "robustness_dataset"
    ]
    == "synthetic_stress"
)


assert (
    evaluation[
        "primary_metric"
    ]
    == "mAP50-95"
)


assert set(
    evaluation[
        "required_metrics"
    ]
) == {
    "Precision",
    "Recall",
    "mAP50",
    "mAP50-95",
    "Per-class AP",
}


statistics = protocol[
    "statistics"
]


assert (
    statistics[
        "publication_repetitions"
    ]
    == 3
)


assert (
    statistics[
        "no_claim_from_single_seed"
    ]
    is True
)


tag_commit = subprocess.check_output(
    [
        "git",
        "rev-parse",
        "v0.1.0^{}",
    ],
    cwd=ROOT,
    text=True,
).strip()


assert (
    tag_commit
    == baseline[
        "bvt_release_commit"
    ]
)


print(
    "benchmark_protocol=bvt-benchmark-protocol-1"
)

print(
    "baseline_bvt=v0.1.0"
)

print(
    "baseline_blender=5.2.3-LTS"
)

print(
    "baseline_ultralytics=8.4.198"
)

print(
    "baseline_model=yolo11n.pt"
)

print(
    "training_profiles=clean,balanced,artifacts"
)

print(
    "stress_training_allowed=False"
)

print(
    "primary_evaluation=real_test"
)

print(
    "primary_metric=mAP50-95"
)

print(
    "publication_seeds=3"
)

print(
    "BVT_BENCHMARK_PROTOCOL=OK"
)

print(
    "RESULT=PASS"
)
