import hashlib
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


EVIDENCE = (
    ROOT
    / "benchmarks"
    / "pilot-datasets-v0.1.json"
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
    == "bvt-benchmark-pilot-datasets-1"
)


assert (
    data[
        "protocol_version"
    ]
    == "0.1.0"
)


assert (
    data[
        "benchmark_phase"
    ]
    == "pilot"
)


assert (
    data[
        "publication_claim_allowed"
    ]
    is False
)


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
    assert (
        item[
            "frame_count"
        ]
        == 100
    )

    assert (
        item[
            "image_count"
        ]
        == 100
    )

    assert (
        item[
            "label_count"
        ]
        == 100
    )

    assert (
        item[
            "class_count"
        ]
        == 8
    )

    assert (
        item[
            "split_counts"
        ]
        == {
            "train": 80,
            "validation": 10,
            "test": 10,
        }
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


    assert_sha256(
        item[
            "config_sha256"
        ]
    )

    assert_sha256(
        item[
            "hash_manifest_sha256"
        ]
    )

    assert_sha256(
        item[
            "dataset_archive_sha256"
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
    == "training-pilot"
)

assert (
    records[
        1
    ][
        "role"
    ]
    == "training-pilot"
)

assert (
    records[
        2
    ][
        "role"
    ]
    == "training-pilot"
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
    "pilot_clean=PASS"
)

print(
    "pilot_balanced=PASS"
)

print(
    "pilot_artifacts=PASS"
)

print(
    "pilot_stress=PASS"
)

print(
    "pilot_evidence_integrity=True"
)

print(
    "pilot_ephemeral_archives_required=False"
)

print(
    "BVT_BENCHMARK_PILOT_DATASETS=OK"
)

print(
    "RESULT=PASS"
)
