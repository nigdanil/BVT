import math
from pathlib import Path

from ..core.constants import (
    DATASET_SPLIT_SCHEMA_VERSION,
)
from ..core.seeding import derive_subseed


SPLIT_NAMESPACE = "dataset-split"

SPLIT_STRATEGY = "sha256-rank-v1"

SPLIT_NAMES = (
    "train",
    "validation",
    "test",
)


def _validate_ratios(
    train_ratio,
    validation_ratio,
    test_ratio,
):
    ratios = (
        float(train_ratio),
        float(validation_ratio),
        float(test_ratio),
    )

    # Blender FloatProperty values are stored with
    # finite precision, so values configured as
    # 0.8 / 0.1 / 0.1 may not sum to exactly 1.0.
    tolerance = 1e-6

    if any(
        value < -tolerance
        or value > 1.0 + tolerance
        for value in ratios
    ):
        raise ValueError(
            "Dataset split ratios must be "
            "between 0 and 1"
        )

    total = sum(
        ratios
    )

    if abs(
        total - 1.0
    ) > tolerance:
        raise ValueError(
            "Dataset split ratios must sum to 1.0"
        )

    if total <= 0.0:
        raise ValueError(
            "Dataset split ratios must have "
            "a positive total"
        )

    # Normalize accepted Blender float values so
    # downstream allocation operates on an exact
    # unit distribution.
    normalized = tuple(
        max(
            0.0,
            min(
                1.0,
                value / total,
            ),
        )
        for value
        in ratios
    )

    normalized_total = sum(
        normalized
    )

    # Remove the final floating-point residue from
    # the test bucket while preserving deterministic
    # train/validation values.
    normalized = (
        normalized[0],
        normalized[1],
        1.0
        - normalized[0]
        - normalized[1],
    )

    if (
        normalized[2] < -tolerance
        or abs(
            sum(
                normalized
            )
            - 1.0
        ) > tolerance
    ):
        raise ValueError(
            "Dataset split normalization failed"
        )

    return normalized


def _allocate_counts(
    frame_count,
    ratios,
):
    raw_counts = [
        frame_count * ratio
        for ratio
        in ratios
    ]

    counts = [
        math.floor(
            value
        )
        for value
        in raw_counts
    ]

    remaining = (
        frame_count
        - sum(
            counts
        )
    )

    remainder_order = sorted(
        range(
            len(
                ratios
            )
        ),
        key=lambda index: (
            -(
                raw_counts[index]
                - counts[index]
            ),
            index,
        ),
    )

    for index in (
        remainder_order[
            :remaining
        ]
    ):
        counts[
            index
        ] += 1

    return tuple(
        counts
    )


def build_dataset_splits(
    frames,
    base_seed,
    train_ratio,
    validation_ratio,
    test_ratio,
):
    ratios = _validate_ratios(
        train_ratio,
        validation_ratio,
        test_ratio,
    )

    frames = list(
        frames
    )

    counts = _allocate_counts(
        len(
            frames
        ),
        ratios,
    )

    ranked = sorted(
        frames,
        key=lambda frame: (
            derive_subseed(
                base_seed,
                SPLIT_NAMESPACE,
                str(
                    frame[
                        "frame_id"
                    ]
                ),
            ),
            str(
                frame[
                    "frame_id"
                ]
            ),
        ),
    )

    assignment_by_frame = {}

    offset = 0

    for (
        split_name,
        count,
    ) in zip(
        SPLIT_NAMES,
        counts,
    ):
        selected = ranked[
            offset:
            offset + count
        ]

        offset += count

        for frame in selected:
            assignment_by_frame[
                frame[
                    "frame_id"
                ]
            ] = split_name

    assignments = []

    for frame in sorted(
        frames,
        key=lambda item: (
            int(
                item[
                    "frame_index"
                ]
            ),
            str(
                item[
                    "frame_id"
                ]
            ),
        ),
    ):
        frame_id = (
            frame[
                "frame_id"
            ]
        )

        assignments.append(
            {
                "frame_id": (
                    frame_id
                ),
                "image": (
                    frame[
                        "image"
                    ]
                ),
                "label": (
                    frame[
                        "label"
                    ]
                ),
                "split": (
                    assignment_by_frame[
                        frame_id
                    ]
                ),
            }
        )

    return {
        "schema_version": (
            DATASET_SPLIT_SCHEMA_VERSION
        ),
        "strategy": (
            SPLIT_STRATEGY
        ),
        "seed": int(
            base_seed
        ),
        "namespace": (
            SPLIT_NAMESPACE
        ),
        "ratios": {
            "train": ratios[0],
            "validation": ratios[1],
            "test": ratios[2],
        },
        "counts": {
            "train": counts[0],
            "validation": counts[1],
            "test": counts[2],
        },
        "files": {
            "train": (
                "splits/train.txt"
            ),
            "validation": (
                "splits/validation.txt"
            ),
            "test": (
                "splits/test.txt"
            ),
        },
        "assignments": assignments,
    }


def write_dataset_splits(
    dataset_directory,
    split_manifest,
):
    dataset_directory = Path(
        dataset_directory
    )

    splits_directory = (
        dataset_directory
        / "splits"
    )

    splits_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {}

    for split_name in (
        SPLIT_NAMES
    ):
        relative_path = (
            split_manifest[
                "files"
            ][
                split_name
            ]
        )

        path = (
            dataset_directory
            / relative_path
        )

        rows = [
            assignment[
                "image"
            ]
            for assignment
            in split_manifest[
                "assignments"
            ]
            if (
                assignment[
                    "split"
                ]
                == split_name
            )
        ]

        content = ""

        if rows:
            content = (
                "\n".join(
                    rows
                )
                + "\n"
            )

        path.write_text(
            content,
            encoding="utf-8",
        )

        paths[
            split_name
        ] = path

    return paths
