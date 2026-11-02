import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


protocol = json.loads(
    (
        ROOT
        / "benchmarks"
        / "protocol-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


environment = json.loads(
    (
        ROOT
        / "benchmarks"
        / "environment-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


evidence = json.loads(
    (
        ROOT
        / "benchmarks"
        / "pilot-datasets-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


baseline = protocol[
    "baseline"
]


assert (
    environment[
        "ultralytics"
    ][
        "version"
    ]
    == "8.4.198"
)


assert (
    environment[
        "model"
    ][
        "name"
    ]
    == "yolo11n.pt"
)


model_hash = (
    environment[
        "model"
    ][
        "sha256"
    ]
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
        "model_weights_sha256"
    ]
    == model_hash
)


assert (
    baseline[
        "environment_lock"
    ]
    == "benchmarks/environment-v0.1.json"
)


def load_config(
    phase,
    profile,
):
    return json.loads(
        (
            ROOT
            / "benchmarks"
            / "configs"
            / (
                phase
                + "-"
                + profile
                + ".json"
            )
        ).read_text(
            encoding="utf-8"
        )
    )


pilot = {
    profile: load_config(
        "pilot",
        profile,
    )
    for profile
    in (
        "clean",
        "balanced",
        "artifacts",
        "stress",
    )
}


publication = {
    profile: load_config(
        "publication",
        profile,
    )
    for profile
    in (
        "clean",
        "balanced",
        "artifacts",
        "stress",
    )
}


for config in (
    pilot.values()
):
    assert (
        config[
            "project"
        ][
            "frame_count"
        ]
        == 100
    )


assert (
    publication[
        "clean"
    ][
        "project"
    ][
        "frame_count"
    ]
    == 1000
)

assert (
    publication[
        "balanced"
    ][
        "project"
    ][
        "frame_count"
    ]
    == 1000
)

assert (
    publication[
        "artifacts"
    ][
        "project"
    ][
        "frame_count"
    ]
    == 1000
)

assert (
    publication[
        "stress"
    ][
        "project"
    ][
        "frame_count"
    ]
    == 250
)


def non_artifact(
    settings,
):
    return {
        key: value
        for key, value
        in settings.items()
        if not key.startswith(
            "artifact_"
        )
    }


clean_settings = (
    pilot[
        "clean"
    ][
        "settings"
    ]
)

balanced_settings = (
    pilot[
        "balanced"
    ][
        "settings"
    ]
)

artifact_settings = (
    pilot[
        "artifacts"
    ][
        "settings"
    ]
)


assert (
    non_artifact(
        clean_settings
    )
    == non_artifact(
        balanced_settings
    )
)

assert (
    non_artifact(
        clean_settings
    )
    == non_artifact(
        artifact_settings
    )
)


assert (
    clean_settings[
        "placement_randomization_enabled"
    ]
    is True
)

assert (
    clean_settings[
        "camera_randomization_enabled"
    ]
    is True
)

assert (
    clean_settings[
        "lighting_randomization_enabled"
    ]
    is True
)

assert (
    clean_settings[
        "artifact_engine_enabled"
    ]
    is False
)

assert (
    balanced_settings[
        "artifact_engine_enabled"
    ]
    is True
)

assert (
    artifact_settings[
        "artifact_engine_enabled"
    ]
    is True
)


profiles = protocol[
    "synthetic_datasets"
][
    "profiles"
]


assert (
    profiles[
        "stress"
    ][
        "training_allowed"
    ]
    is False
)


assert (
    evidence[
        "publication_claim_allowed"
    ]
    is False
)

assert len(
    evidence[
        "records"
    ]
) == 4


for item in evidence[
    "records"
]:
    assert (
        item[
            "frame_count"
        ]
        == 100
    )

    assert len(
        item[
            "dataset_archive_sha256"
        ]
    ) == 64


print(
    "benchmark_environment_frozen=True"
)

print(
    "yolo11n_hash_frozen=True"
)

print(
    "pilot_profiles=4"
)

print(
    "pilot_frames_per_profile=100"
)

print(
    "publication_configs_ready=True"
)

print(
    "clean_artifact_ablation_controlled=True"
)

print(
    "publication_claim_allowed=False"
)

print(
    "BVT_BENCHMARK_PILOT_FOUNDATION=OK"
)

print(
    "RESULT=PASS"
)
