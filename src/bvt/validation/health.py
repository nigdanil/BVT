import json
from pathlib import Path

from ..core.constants import (
    DATASET_HEALTH_SCHEMA_VERSION,
)


CLASS_IMBALANCE_WARNING_RATIO = 3.0


def _finding(
    severity,
    code,
    message,
):
    return {
        "severity": severity,
        "code": code,
        "message": message,
    }


def build_dataset_health_report(
    statistics,
    validation_report,
):
    findings = []

    validation_errors = list(
        validation_report.get(
            "errors",
            [],
        )
    )

    validation_warnings = list(
        validation_report.get(
            "warnings",
            [],
        )
    )

    if validation_errors:
        findings.append(
            _finding(
                "error",
                "validation_failed",
                (
                    "Dataset has hard validation "
                    f"errors: {len(validation_errors)}"
                ),
            )
        )

    per_class = list(
        statistics.get(
            "classes",
            {},
        ).get(
            "per_class",
            [],
        )
    )

    zero_classes = [
        item
        for item
        in per_class
        if int(
            item[
                "objects"
            ]
        ) == 0
    ]

    if zero_classes:
        findings.append(
            _finding(
                "warning",
                "class_without_objects",
                (
                    "Declared classes without "
                    f"objects: {len(zero_classes)}"
                ),
            )
        )

    nonzero_counts = [
        int(
            item[
                "objects"
            ]
        )
        for item
        in per_class
        if int(
            item[
                "objects"
            ]
        ) > 0
    ]

    imbalance_ratio = None

    if len(
        nonzero_counts
    ) >= 2:
        minimum = min(
            nonzero_counts
        )

        maximum = max(
            nonzero_counts
        )

        imbalance_ratio = (
            maximum
            / minimum
        )

        if (
            imbalance_ratio
            > CLASS_IMBALANCE_WARNING_RATIO
        ):
            findings.append(
                _finding(
                    "warning",
                    "class_imbalance",
                    (
                        "Class object-count ratio "
                        f"is {imbalance_ratio:.3f}"
                    ),
                )
            )

    empty_label_frames = int(
        statistics.get(
            "empty_label_frames",
            0,
        )
    )

    if empty_label_frames > 0:
        findings.append(
            _finding(
                "warning",
                "empty_labels",
                (
                    "Frames with empty labels: "
                    f"{empty_label_frames}"
                ),
            )
        )

    split_counts = dict(
        statistics.get(
            "splits",
            {},
        )
    )

    frame_count = int(
        statistics.get(
            "frames",
            0,
        )
    )

    empty_splits = [
        split_name
        for split_name in (
            "train",
            "validation",
            "test",
        )
        if int(
            split_counts.get(
                split_name,
                0,
            )
        ) == 0
    ]

    if (
        frame_count >= 3
        and empty_splits
    ):
        findings.append(
            _finding(
                "warning",
                "empty_split",
                (
                    "Dataset split has no frames: "
                    + ", ".join(
                        empty_splits
                    )
                ),
            )
        )

    if validation_errors:
        status = "FAIL"

    elif findings:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "schema_version": (
            DATASET_HEALTH_SCHEMA_VERSION
        ),
        "status": status,
        "findings": findings,
        "checks": {
            "validation_errors": len(
                validation_errors
            ),
            "validation_warnings": len(
                validation_warnings
            ),
            "empty_label_frames": (
                empty_label_frames
            ),
            "empty_splits": (
                empty_splits
            ),
            "class_imbalance_ratio": (
                imbalance_ratio
            ),
            "class_imbalance_warning_ratio": (
                CLASS_IMBALANCE_WARNING_RATIO
            ),
        },
    }


def write_dataset_health_report(
    path,
    report,
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
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
