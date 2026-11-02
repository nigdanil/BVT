import hashlib
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[2]


EXPECTED_CLASSES = [
    "bev_can_red_330",
    "bev_can_blue_330",
    "bev_bottle_green_500",
    "bev_bottle_amber_500",
    "bev_carton_orange_1000",
    "bev_carton_white_1000",
    "bev_box_purple_250",
    "bev_box_yellow_250",
]


EXPECTED = {
    "clean": 1000,
    "balanced": 1000,
    "artifacts": 1000,
    "stress": 250,
}


EXPECTED_SPLITS = {
    "clean": {
        "train": 800,
        "validation": 100,
        "test": 100,
    },
    "balanced": {
        "train": 800,
        "validation": 100,
        "test": 100,
    },
    "artifacts": {
        "train": 800,
        "validation": 100,
        "test": 100,
    },
    "stress": {
        "train": 200,
        "validation": 25,
        "test": 25,
    },
}


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


def lines(
    path,
):
    return [
        line.strip()
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def validate_label(
    path,
):
    for line in lines(
        path
    ):
        parts = (
            line.split()
        )

        assert len(
            parts
        ) == 5, path

        class_id = int(
            parts[
                0
            ]
        )

        assert (
            0
            <= class_id
            < 8
        ), path

        x, y, w, h = [
            float(
                value
            )
            for value
            in parts[
                1:
            ]
        ]

        assert (
            0.0
            <= x
            <= 1.0
        ), path

        assert (
            0.0
            <= y
            <= 1.0
        ), path

        assert (
            0.0
            < w
            <= 1.0
        ), path

        assert (
            0.0
            < h
            <= 1.0
        ), path


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

    for relative, item in (
        declared.items()
    ):
        path = (
            dataset
            / relative
        )

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
        "file_count": len(
            declared
        ),
        "sha256": sha256_file(
            hashes_path
        ),
    }


records = []


for profile, expected in (
    EXPECTED.items()
):
    config_path = (
        ROOT
        / "benchmarks"
        / "configs"
        / (
            "publication-"
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

    assert dataset.is_dir()
    assert archive.is_file()

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
    ) == expected

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
    ) == expected

    assert len(
        labels
    ) == expected

    assert lines(
        dataset
        / "classes.txt"
    ) == EXPECTED_CLASSES


    for label in labels:
        validate_label(
            label
        )


    split_members = {}


    for split_name in (
        "train",
        "validation",
        "test",
    ):
        split_members[
            split_name
        ] = lines(
            dataset
            / "splits"
            / (
                split_name
                + ".txt"
            )
        )


    split_counts = {
        name: len(
            values
        )
        for name, values
        in split_members.items()
    }


    assert (
        split_counts
        == EXPECTED_SPLITS[
            profile
        ]
    )


    train_set = set(
        split_members[
            "train"
        ]
    )

    validation_set = set(
        split_members[
            "validation"
        ]
    )

    test_set = set(
        split_members[
            "test"
        ]
    )


    assert train_set.isdisjoint(
        validation_set
    )

    assert train_set.isdisjoint(
        test_set
    )

    assert validation_set.isdisjoint(
        test_set
    )


    assert len(
        train_set
        | validation_set
        | test_set
    ) == expected


    # Exact rendered duplicates inside one profile are
    # prohibited for the publication benchmark.
    image_hashes = [
        sha256_file(
            image
        )
        for image
        in images
    ]


    assert len(
        set(
            image_hashes
        )
    ) == expected, (
        "Exact duplicate image detected in "
        + profile
    )


    hash_result = (
        verify_hash_manifest(
            dataset
        )
    )


    record = {
        "profile": profile,

        "role": (
            "evaluation-only"
            if profile
            == "stress"
            else "training-publication"
        ),

        "config": (
            config_path.relative_to(
                ROOT
            ).as_posix()
        ),

        "config_sha256": (
            sha256_file(
                config_path
            )
        ),

        "seed": (
            config[
                "project"
            ][
                "seed"
            ]
        ),

        "frame_count": expected,

        "image_count": len(
            images
        ),

        "label_count": len(
            labels
        ),

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

        "dataset_statistics_sha256": (
            sha256_file(
                dataset
                / "statistics.json"
            )
        ),

        "hash_manifest_file_count": (
            hash_result[
                "file_count"
            ]
        ),

        "hash_manifest_sha256": (
            hash_result[
                "sha256"
            ]
        ),

        "dataset_archive_sha256": (
            sha256_file(
                archive
            )
        ),

        "dataset_archive_bytes": (
            archive.stat().st_size
        ),

        "exact_duplicate_images": 0,
    }


    records.append(
        record
    )


    print(
        profile
        + "_frames="
        + str(
            expected
        )
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
        + "_exact_duplicates=0"
    )

    print(
        profile
        + "_archive_sha256="
        + record[
            "dataset_archive_sha256"
        ]
    )


archive_hashes = [
    record[
        "dataset_archive_sha256"
    ]
    for record
    in records
]


assert len(
    set(
        archive_hashes
    )
) == 4


evidence = {
    "schema_version": (
        "bvt-benchmark-publication-datasets-1"
    ),

    "protocol_version": "0.1.0",

    "benchmark_phase": (
        "publication-dataset-generation"
    ),

    "generation_seed": 20261102,

    "total_frames": 3250,

    "publication_training_frames": 3000,

    "stress_evaluation_frames": 250,

    "class_count": 8,

    "records": records,

    "training_profiles": [
        "clean",
        "balanced",
        "artifacts",
    ],

    "evaluation_only_profiles": [
        "stress",
    ],

    "training_execution_completed": False,

    "real_test_completed": False,

    "publication_claim_allowed": False,
}


path = (
    ROOT
    / "benchmarks"
    / "publication-datasets-v0.1.json"
)


path.write_text(
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
    "publication_total_frames=3250"
)

print(
    "publication_training_frames=3000"
)

print(
    "stress_evaluation_frames=250"
)

print(
    "publication_claim_allowed=False"
)

print(
    "BVT_EP7_PUBLICATION_DATASETS=OK"
)
