import json
from pathlib import Path

from ..core.constants import (
    DATASET_STATISTICS_SCHEMA_VERSION,
)


def build_dataset_statistics(
    manifest,
):
    frames = list(
        manifest.get(
            "frames",
            [],
        )
    )

    classes = list(
        manifest.get(
            "annotations",
            {},
        ).get(
            "classes",
            [],
        )
    )

    class_counts = {
        int(
            item[
                "id"
            ]
        ): 0
        for item
        in classes
    }

    bbox_areas = []

    object_count = 0
    empty_label_frames = 0

    for frame in frames:
        objects = list(
            frame.get(
                "objects",
                [],
            )
        )

        if not objects:
            empty_label_frames += 1

        object_count += len(
            objects
        )

        for item in objects:
            class_id = int(
                item[
                    "class_id"
                ]
            )

            class_counts[
                class_id
            ] = (
                class_counts.get(
                    class_id,
                    0,
                )
                + 1
            )

            bbox = item[
                "bbox_yolo"
            ]

            width = float(
                bbox[2]
            )

            height = float(
                bbox[3]
            )

            bbox_areas.append(
                width
                * height
            )

    per_class = []

    class_names = {
        int(
            item[
                "id"
            ]
        ): item[
            "name"
        ]
        for item
        in classes
    }

    for class_id in sorted(
        class_counts
    ):
        per_class.append(
            {
                "id": class_id,
                "name": (
                    class_names.get(
                        class_id,
                        "",
                    )
                ),
                "objects": (
                    class_counts[
                        class_id
                    ]
                ),
            }
        )

    if bbox_areas:
        bbox_summary = {
            "count": len(
                bbox_areas
            ),
            "area_min": min(
                bbox_areas
            ),
            "area_max": max(
                bbox_areas
            ),
            "area_mean": (
                sum(
                    bbox_areas
                )
                / len(
                    bbox_areas
                )
            ),
        }

    else:
        bbox_summary = {
            "count": 0,
            "area_min": None,
            "area_max": None,
            "area_mean": None,
        }

    split_counts = dict(
        manifest.get(
            "splits",
            {},
        ).get(
            "counts",
            {},
        )
    )

    return {
        "schema_version": (
            DATASET_STATISTICS_SCHEMA_VERSION
        ),
        "dataset_id": (
            manifest.get(
                "dataset",
                {},
            ).get(
                "dataset_id"
            )
        ),
        "frames": len(
            frames
        ),
        "images": len(
            frames
        ),
        "labels": len(
            frames
        ),
        "objects": (
            object_count
        ),
        "classes": {
            "count": len(
                classes
            ),
            "per_class": (
                per_class
            ),
        },
        "empty_label_frames": (
            empty_label_frames
        ),
        "bbox": (
            bbox_summary
        ),
        "splits": (
            split_counts
        ),
    }


def write_dataset_statistics(
    path,
    statistics,
):
    path = Path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            statistics,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
