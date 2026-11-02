import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
}


class ValidationError(
    RuntimeError
):
    pass


def require(
    condition,
    message,
):
    if not condition:
        raise ValidationError(
            message
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


def dhash64(
    path,
):
    with Image.open(
        path
    ) as image:
        gray = (
            image
            .convert(
                "L"
            )
            .resize(
                (
                    9,
                    8,
                ),
                Image.Resampling.LANCZOS,
            )
        )

        pixels = list(
            gray.getdata()
        )


    value = 0


    for y in range(
        8
    ):
        row = y * 9

        for x in range(
            8
        ):
            value <<= 1

            value |= int(
                pixels[
                    row + x
                ]
                > pixels[
                    row + x + 1
                ]
            )


    return value


def hamming(
    left,
    right,
):
    return (
        left
        ^ right
    ).bit_count()


def read_classes(
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


def parse_label(
    path,
    class_count,
):
    class_ids = []


    for index, line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):
        line = line.strip()

        if not line:
            continue


        parts = line.split()


        require(
            len(
                parts
            )
            == 5,
            (
                f"{path}:"
                f"{index}: "
                "expected 5 YOLO fields"
            ),
        )


        class_id = int(
            parts[
                0
            ]
        )


        require(
            0
            <= class_id
            < class_count,
            (
                f"{path}:"
                f"{index}: "
                "class id out of range"
            ),
        )


        x, y, width, height = [
            float(
                value
            )
            for value
            in parts[
                1:
            ]
        ]


        require(
            0.0
            <= x
            <= 1.0,
            f"{path}: invalid center_x",
        )

        require(
            0.0
            <= y
            <= 1.0,
            f"{path}: invalid center_y",
        )

        require(
            0.0
            < width
            <= 1.0,
            f"{path}: invalid width",
        )

        require(
            0.0
            < height
            <= 1.0,
            f"{path}: invalid height",
        )


        class_ids.append(
            class_id
        )


    return class_ids


def check_no_gps(
    path,
):
    with Image.open(
        path
    ) as image:
        exif = (
            image.getexif()
        )


        if not exif:
            return


        gps = {}


        try:
            gps = exif.get_ifd(
                0x8825
            )
        except Exception:
            gps = {}


        require(
            not gps,
            (
                "GPS EXIF metadata found: "
                + str(
                    path
                )
            ),
        )


def hash_lines(
    values,
):
    digest = hashlib.sha256()

    for value in sorted(
        values
    ):
        digest.update(
            value.encode(
                "utf-8"
            )
        )

        digest.update(
            b"\n"
        )


    return digest.hexdigest()


def validate_dataset(
    root,
    plan_path,
    evidence_out=None,
):
    root = Path(
        root
    ).resolve()

    plan_path = Path(
        plan_path
    ).resolve()


    plan = json.loads(
        plan_path.read_text(
            encoding="utf-8"
        )
    )


    classes_path = (
        root
        / "classes.txt"
    )


    require(
        classes_path.is_file(),
        "classes.txt missing",
    )


    classes = read_classes(
        classes_path
    )


    expected_classes_path = (
        Path.cwd()
        / plan[
            "class_contract"
        ][
            "classes_file"
        ]
    )


    if expected_classes_path.is_file():
        expected_classes = (
            read_classes(
                expected_classes_path
            )
        )

        require(
            classes
            == expected_classes,
            "class taxonomy mismatch",
        )


    require(
        len(
            classes
        )
        == plan[
            "class_contract"
        ][
            "class_count"
        ],
        "class count mismatch",
    )


    session_specs = {
        item[
            "session_id"
        ]: item
        for item
        in plan[
            "sessions"
        ]
    }


    require(
        len(
            session_specs
        )
        == len(
            plan[
                "sessions"
            ]
        ),
        "duplicate session_id in plan",
    )


    split_sessions = defaultdict(
        set
    )


    for item in plan[
        "sessions"
    ]:
        split_sessions[
            item[
                "split"
            ]
        ].add(
            item[
                "session_id"
            ]
        )


    all_session_ids = []


    for values in split_sessions.values():
        all_session_ids.extend(
            values
        )


    require(
        len(
            all_session_ids
        )
        == len(
            set(
                all_session_ids
            )
        ),
        "session assigned to multiple splits",
    )


    image_records = []

    class_counts = {
        "train": [
            0
            for _ in classes
        ],
        "validation": [
            0
            for _ in classes
        ],
        "test": [
            0
            for _ in classes
        ],
    }


    split_paths = defaultdict(
        list
    )


    exact_hash_owner = {}


    for session_id, spec in (
        session_specs.items()
    ):
        split = spec[
            "split"
        ]


        image_dir = (
            root
            / "images"
            / session_id
        )

        label_dir = (
            root
            / "labels"
            / session_id
        )

        manifest_path = (
            root
            / "sessions"
            / (
                session_id
                + ".json"
            )
        )


        require(
            image_dir.is_dir(),
            (
                "missing image session: "
                + session_id
            ),
        )

        require(
            label_dir.is_dir(),
            (
                "missing label session: "
                + session_id
            ),
        )

        require(
            manifest_path.is_file(),
            (
                "missing session manifest: "
                + session_id
            ),
        )


        session_manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )


        require(
            session_manifest[
                "session_id"
            ]
            == session_id,
            (
                "session manifest id mismatch: "
                + session_id
            ),
        )

        require(
            session_manifest[
                "split"
            ]
            == split,
            (
                "session manifest split mismatch: "
                + session_id
            ),
        )


        images = sorted(
            path
            for path
            in image_dir.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in IMAGE_SUFFIXES
            )
        )


        require(
            len(
                images
            )
            == spec[
                "target_images"
            ],
            (
                session_id
                + ": expected "
                + str(
                    spec[
                        "target_images"
                    ]
                )
                + " images, got "
                + str(
                    len(
                        images
                    )
                )
            ),
        )


        for image_path in images:
            label_path = (
                label_dir
                / (
                    image_path.stem
                    + ".txt"
                )
            )


            require(
                label_path.is_file(),
                (
                    "missing label: "
                    + str(
                        image_path
                    )
                ),
            )


            check_no_gps(
                image_path
            )


            class_ids = parse_label(
                label_path,
                len(
                    classes
                ),
            )


            for class_id in class_ids:
                class_counts[
                    split
                ][
                    class_id
                ] += 1


            image_sha = sha256_file(
                image_path
            )

            label_sha = sha256_file(
                label_path
            )


            require(
                image_sha
                not in exact_hash_owner,
                (
                    "exact duplicate image: "
                    + str(
                        image_path
                    )
                    + " == "
                    + str(
                        exact_hash_owner.get(
                            image_sha
                        )
                    )
                ),
            )


            exact_hash_owner[
                image_sha
            ] = image_path


            relative_image = (
                image_path
                .relative_to(
                    root
                )
                .as_posix()
            )


            split_paths[
                split
            ].append(
                relative_image
            )


            image_records.append(
                {
                    "session_id": (
                        session_id
                    ),
                    "split": split,
                    "image": (
                        relative_image
                    ),
                    "label": (
                        label_path
                        .relative_to(
                            root
                        )
                        .as_posix()
                    ),
                    "image_sha256": (
                        image_sha
                    ),
                    "label_sha256": (
                        label_sha
                    ),
                    "dhash64": (
                        f"{dhash64(image_path):016x}"
                    ),
                }
            )


    threshold = (
        plan[
            "leakage_policy"
        ][
            "near_duplicate_hamming_threshold"
        ]
    )


    cross_split_near_duplicates = []


    for left_index in range(
        len(
            image_records
        )
    ):
        left = image_records[
            left_index
        ]

        left_hash = int(
            left[
                "dhash64"
            ],
            16,
        )


        for right_index in range(
            left_index + 1,
            len(
                image_records
            ),
        ):
            right = image_records[
                right_index
            ]


            if (
                left[
                    "split"
                ]
                == right[
                    "split"
                ]
            ):
                continue


            distance = hamming(
                left_hash,
                int(
                    right[
                        "dhash64"
                    ],
                    16,
                ),
            )


            if distance <= threshold:
                cross_split_near_duplicates.append(
                    {
                        "left": (
                            left[
                                "image"
                            ]
                        ),
                        "right": (
                            right[
                                "image"
                            ]
                        ),
                        "distance": (
                            distance
                        ),
                    }
                )


    require(
        not cross_split_near_duplicates,
        (
            "cross-split near duplicates detected: "
            + json.dumps(
                cross_split_near_duplicates[
                    :10
                ],
                ensure_ascii=False,
            )
        ),
    )


    minimums = (
        plan[
            "minimum_class_instances_by_split"
        ]
    )


    for split in (
        "train",
        "validation",
        "test",
    ):
        minimum = minimums[
            split
        ]


        for class_id, count in enumerate(
            class_counts[
                split
            ]
        ):
            require(
                count >= minimum,
                (
                    split
                    + ": class "
                    + str(
                        class_id
                    )
                    + " has "
                    + str(
                        count
                    )
                    + " instances; minimum="
                    + str(
                        minimum
                    )
                ),
            )


    split_hashes = {}


    for split, values in (
        split_paths.items()
    ):
        split_hashes[
            split
        ] = hash_lines(
            values
        )


    test_records = [
        item
        for item
        in image_records
        if item[
            "split"
        ]
        == "test"
    ]


    real_test_hash = hash_lines(
        (
            item[
                "image_sha256"
            ]
            + ":"
            + item[
                "label_sha256"
            ]
        )
        for item
        in test_records
    )


    evidence = {
        "schema_version": (
            "bvt-real-dataset-evidence-1"
        ),
        "dataset_id": (
            plan[
                "dataset_id"
            ]
        ),
        "dataset_version": (
            plan[
                "dataset_version"
            ]
        ),
        "total_images": (
            len(
                image_records
            )
        ),
        "session_count": (
            len(
                session_specs
            )
        ),
        "split_image_counts": {
            split: len(
                split_paths[
                    split
                ]
            )
            for split
            in (
                "train",
                "validation",
                "test",
            )
        },
        "class_counts": (
            class_counts
        ),
        "exact_duplicates": 0,
        "cross_split_near_duplicates": 0,
        "near_duplicate_algorithm": (
            "dHash-64"
        ),
        "near_duplicate_hamming_threshold": (
            threshold
        ),
        "split_hashes": (
            split_hashes
        ),
        "real_test_hash": (
            real_test_hash
        ),
        "images": (
            image_records
        ),
    }


    if evidence_out is not None:
        evidence_out = Path(
            evidence_out
        )

        evidence_out.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        evidence_out.write_text(
            json.dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


        split_dir = (
            root
            / "splits"
        )

        split_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        for split, values in (
            split_paths.items()
        ):
            (
                split_dir
                / (
                    split
                    + ".txt"
                )
            ).write_text(
                "\n".join(
                    sorted(
                        values
                    )
                )
                + "\n",
                encoding="utf-8",
            )


    return evidence


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--evidence-out",
        type=Path,
    )

    args = parser.parse_args()


    evidence = validate_dataset(
        args.root,
        args.plan,
        args.evidence_out,
    )


    print(
        "real_images="
        + str(
            evidence[
                "total_images"
            ]
        )
    )

    print(
        "real_sessions="
        + str(
            evidence[
                "session_count"
            ]
        )
    )

    print(
        "real_test_images="
        + str(
            evidence[
                "split_image_counts"
            ][
                "test"
            ]
        )
    )

    print(
        "exact_duplicates=0"
    )

    print(
        "cross_split_near_duplicates=0"
    )

    print(
        "real_test_hash="
        + evidence[
            "real_test_hash"
        ]
    )

    print(
        "BVT_REAL_DATASET_VALIDATION=OK"
    )


if __name__ == "__main__":
    main()
