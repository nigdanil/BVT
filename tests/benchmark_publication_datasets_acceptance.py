import hashlib
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


EVIDENCE = (
    ROOT
    / "benchmarks"
    / "publication-datasets-v0.1.json"
)


def sha256_file(
    path,
):
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as stream:
        for chunk in iter(
            lambda: stream.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def assert_sha256(
    value,
):
    assert isinstance(
        value,
        str,
    )

    assert len(
        value
    ) == 64

    int(
        value,
        16,
    )


assert EVIDENCE.is_file()


data = json.loads(
    EVIDENCE.read_text(
        encoding="utf-8"
    )
)


assert (
    data[
        "schema_version"
    ]
    == "bvt-benchmark-publication-datasets-1"
)


assert (
    data[
        "protocol_version"
    ]
    == "0.1.0"
)


assert (
    data[
        "total_frames"
    ]
    == 3250
)


assert (
    data[
        "publication_training_frames"
    ]
    == 3000
)


assert (
    data[
        "stress_evaluation_frames"
    ]
    == 250
)


assert (
    data[
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


records = data[
    "records"
]


assert [
    item[
        "profile"
    ]
    for item
    in records
] == [
    "clean",
    "balanced",
    "artifacts",
    "stress",
]


for item in records:
    profile = item[
        "profile"
    ]

    expected_count = (
        expected[
            profile
        ]
    )


    assert (
        item[
            "frame_count"
        ]
        == expected_count
    )

    assert (
        item[
            "image_count"
        ]
        == expected_count
    )

    assert (
        item[
            "label_count"
        ]
        == expected_count
    )

    assert (
        item[
            "class_count"
        ]
        == 8
    )

    assert (
        item[
            "validation_status"
        ]
        == "PASS"
    )

    assert (
        item[
            "health_status"
        ]
        == "PASS"
    )

    assert (
        item[
            "exact_duplicate_images"
        ]
        == 0
    )


    config_path = (
        ROOT
        / item[
            "config"
        ]
    )

    assert config_path.is_file()

    assert (
        sha256_file(
            config_path
        )
        == item[
            "config_sha256"
        ]
    )


    for key in (
        "config_sha256",
        "dataset_statistics_sha256",
        "hash_manifest_sha256",
        "dataset_archive_sha256",
    ):
        assert_sha256(
            item[
                key
            ]
        )


    assert (
        item[
            "dataset_archive_bytes"
        ]
        > 0
    )


assert (
    records[
        0
    ][
        "role"
    ]
    == "training-publication"
)

assert (
    records[
        1
    ][
        "role"
    ]
    == "training-publication"
)

assert (
    records[
        2
    ][
        "role"
    ]
    == "training-publication"
)

assert (
    records[
        3
    ][
        "role"
    ]
    == "evaluation-only"
)


print(
    "publication_clean=PASS"
)

print(
    "publication_balanced=PASS"
)

print(
    "publication_artifacts=PASS"
)

print(
    "publication_stress=PASS"
)

print(
    "publication_total_frames=3250"
)

print(
    "publication_evidence_integrity=True"
)

print(
    "publication_ephemeral_archives_required=False"
)

print(
    "BVT_BENCHMARK_PUBLICATION_DATASETS=OK"
)

print(
    "RESULT=PASS"
)
