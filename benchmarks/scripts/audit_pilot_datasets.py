import hashlib
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[2]


PROFILES = (
    "clean",
    "balanced",
    "artifacts",
    "stress",
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


def read_json(
    path,
):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def non_empty_lines(
    path,
):
    return [
        line
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def verify_hash_manifest(
    dataset,
):
    hashes_path = (
        dataset
        / "hashes.json"
    )

    data = read_json(
        hashes_path
    )

    assert (
        data[
            "schema_version"
        ]
        == "bvt-dataset-hashes-1"
    )

    assert (
        data[
            "algorithm"
        ]
        == "sha256"
    )

    declared = {
        item[
            "path"
        ]: item
        for item
        in data[
            "files"
        ]
    }

    actual = {
        path.relative_to(
            dataset
        ).as_posix()
        for path
        in dataset.rglob(
            "*"
        )
        if (
            path.is_file()
            and path.name
            != "hashes.json"
        )
    }

    assert (
        set(
            declared
        )
        == actual
    )

    for relative in sorted(
        actual
    ):
        path = (
            dataset
            / relative
        )

        item = declared[
            relative
        ]

        assert (
            path.stat().st_size
            == item[
                "size_bytes"
            ]
        )

        assert (
            sha256_file(
                path
            )
            == item[
                "sha256"
            ]
        )

    return {
        "file_count": (
            len(
                declared
            )
        ),
        "manifest_sha256": (
            sha256_file(
                hashes_path
            )
        ),
    }


records = []


for profile in PROFILES:
    config_path = (
        ROOT
        / "benchmarks"
        / "configs"
        / (
            "pilot-"
            + profile
            + ".json"
        )
    )

    config = read_json(
        config_path
    )

    output = (
        ROOT
        / config[
            "project"
        ][
            "output_directory"
        ]
    )

    dataset = (
        output
        / "dataset"
    )

    archive = (
        output
        / "dataset.zip"
    )

    assert dataset.is_dir(), dataset
    assert archive.is_file(), archive

    manifest = read_json(
        dataset
        / "manifest.json"
    )

    validation = read_json(
        dataset
        / "validation.json"
    )

    health = read_json(
        dataset
        / "health.json"
    )

    statistics = read_json(
        dataset
        / "statistics.json"
    )

    assert len(
        manifest[
            "frames"
        ]
    ) == 100

    assert (
        validation[
            "status"
        ]
        == "PASS"
    )

    assert (
        health[
            "status"
        ]
        == "PASS"
    )

    images = sorted(
        (
            dataset
            / "images"
        ).glob(
            "*.png"
        )
    )

    labels = sorted(
        (
            dataset
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

    classes = non_empty_lines(
        dataset
        / "classes.txt"
    )

    assert len(
        classes
    ) == 8

    split_counts = {
        name: len(
            non_empty_lines(
                dataset
                / "splits"
                / (
                    name
                    + ".txt"
                )
            )
        )
        for name in (
            "train",
            "validation",
            "test",
        )
    }

    assert split_counts == {
        "train": 80,
        "validation": 10,
        "test": 10,
    }

    hash_result = (
        verify_hash_manifest(
            dataset
        )
    )

    archive_hash = (
        sha256_file(
            archive
        )
    )

    config_hash = (
        sha256_file(
            config_path
        )
    )

    records.append(
        {
            "profile": profile,
            "role": (
                "evaluation-only"
                if profile
                == "stress"
                else "training-pilot"
            ),
            "config": (
                config_path.relative_to(
                    ROOT
                ).as_posix()
            ),
            "config_sha256": (
                config_hash
            ),
            "output_directory": (
                config[
                    "project"
                ][
                    "output_directory"
                ]
            ),
            "seed": (
                config[
                    "project"
                ][
                    "seed"
                ]
            ),
            "frame_count": 100,
            "image_count": 100,
            "label_count": 100,
            "class_count": 8,
            "split_counts": (
                split_counts
            ),
            "validation_status": (
                validation[
                    "status"
                ]
            ),
            "health_status": (
                health[
                    "status"
                ]
            ),
            "hash_manifest_file_count": (
                hash_result[
                    "file_count"
                ]
            ),
            "hash_manifest_sha256": (
                hash_result[
                    "manifest_sha256"
                ]
            ),
            "dataset_archive_sha256": (
                archive_hash
            ),
            "dataset_archive_bytes": (
                archive.stat().st_size
            ),
        }
    )

    print(
        profile
        + "_frames=100"
    )

    print(
        profile
        + "_validation=PASS"
    )

    print(
        profile
        + "_health=PASS"
    )

    print(
        profile
        + "_archive_sha256="
        + archive_hash
    )


evidence = {
    "schema_version": (
        "bvt-benchmark-pilot-datasets-1"
    ),
    "protocol_version": "0.1.0",
    "benchmark_phase": "pilot",
    "publication_claim_allowed": False,
    "records": records,
}


evidence_path = (
    ROOT
    / "benchmarks"
    / "pilot-datasets-v0.1.json"
)


evidence_path.write_text(
    json.dumps(
        evidence,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)


print(
    "pilot_profiles="
    + str(
        len(
            records
        )
    )
)

print(
    "publication_claim_allowed=False"
)

print(
    "BVT_EP7_PILOT_DATASETS=OK"
)
