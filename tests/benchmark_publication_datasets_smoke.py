import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


evidence = json.loads(
    (
        ROOT
        / "benchmarks"
        / "publication-datasets-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


protocol = json.loads(
    (
        ROOT
        / "benchmarks"
        / "protocol-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


assert (
    evidence[
        "schema_version"
    ]
    == "bvt-benchmark-publication-datasets-1"
)


assert (
    evidence[
        "total_frames"
    ]
    == 3250
)


assert (
    evidence[
        "publication_training_frames"
    ]
    == 3000
)


assert (
    evidence[
        "stress_evaluation_frames"
    ]
    == 250
)


assert (
    evidence[
        "training_execution_completed"
    ]
    is False
)


assert (
    evidence[
        "real_test_completed"
    ]
    is False
)


assert (
    evidence[
        "publication_claim_allowed"
    ]
    is False
)


expected = {
    "clean": 1000,
    "balanced": 1000,
    "artifacts": 1000,
    "stress": 250,
}


for record in evidence[
    "records"
]:
    profile = record[
        "profile"
    ]

    assert (
        record[
            "frame_count"
        ]
        == expected[
            profile
        ]
    )

    assert (
        record[
            "validation_status"
        ]
        == "PASS"
    )

    assert (
        record[
            "health_status"
        ]
        == "PASS"
    )

    assert (
        record[
            "exact_duplicate_images"
        ]
        == 0
    )

    for key in (
        "config_sha256",
        "dataset_statistics_sha256",
        "hash_manifest_sha256",
        "dataset_archive_sha256",
    ):
        value = record[
            key
        ]

        assert len(
            value
        ) == 64

        int(
            value,
            16,
        )


synthetic = protocol[
    "synthetic_datasets"
]


assert (
    synthetic[
        "publication_evidence"
    ]
    == (
        "benchmarks/"
        "publication-datasets-v0.1.json"
    )
)


assert (
    synthetic[
        "publication_dataset_status"
    ]
    == "generated-and-accepted"
)


assert (
    synthetic[
        "publication_total_frames"
    ]
    == 3250
)


assert (
    synthetic[
        "profiles"
    ][
        "stress"
    ][
        "training_allowed"
    ]
    is False
)


print(
    "publication_datasets_frozen=True"
)

print(
    "publication_training_profiles=3"
)

print(
    "publication_training_frames=3000"
)

print(
    "publication_stress_frames=250"
)

print(
    "publication_hashes_frozen=True"
)

print(
    "publication_claim_allowed=False"
)

print(
    "BVT_BENCHMARK_PUBLICATION_FOUNDATION=OK"
)

print(
    "RESULT=PASS"
)
