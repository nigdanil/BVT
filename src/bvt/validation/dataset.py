import hashlib
import json
import math
import struct
from pathlib import Path

from ..core.constants import DATASET_MANIFEST_SCHEMA_VERSION


VALIDATION_SCHEMA_VERSION = "bvt-validation-report-1"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _issue(
    severity,
    code,
    message,
    path=None,
    frame_id=None,
    remediation=None,
):
    issue = {
        "severity": severity,
        "code": code,
        "message": message,
    }

    if path is not None:
        issue["path"] = str(path)

    if frame_id is not None:
        issue["frame_id"] = frame_id

    if remediation is not None:
        issue["remediation"] = remediation

    return issue


def _safe_dataset_path(
    dataset_directory,
    relative_path,
):
    relative = Path(relative_path)

    if relative.is_absolute():
        raise ValueError(
            f"Absolute dataset path is not allowed: {relative_path}"
        )

    if ".." in relative.parts:
        raise ValueError(
            f"Parent traversal is not allowed: {relative_path}"
        )

    return dataset_directory / relative


def _read_png_size(path):
    with path.open("rb") as stream:
        header = stream.read(24)

    if len(header) < 24:
        raise ValueError("PNG file is truncated")

    if header[:8] != PNG_SIGNATURE:
        raise ValueError("Invalid PNG signature")

    if header[12:16] != b"IHDR":
        raise ValueError("PNG IHDR chunk is missing")

    width, height = struct.unpack(
        ">II",
        header[16:24],
    )

    if width <= 0 or height <= 0:
        raise ValueError("Invalid PNG dimensions")

    return width, height


def _sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _parse_yolo_label(
    path,
    known_class_ids,
    frame_id,
    errors,
):
    annotations = []

    text = path.read_text(
        encoding="utf-8",
    )

    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) != 5:
            errors.append(
                _issue(
                    "error",
                    "yolo_invalid_column_count",
                    (
                        f"Expected 5 YOLO columns, "
                        f"got {len(parts)}"
                    ),
                    path=path,
                    frame_id=frame_id,
                )
            )
            continue

        try:
            class_id = int(parts[0])

            values = [
                float(value)
                for value in parts[1:]
            ]

        except ValueError:
            errors.append(
                _issue(
                    "error",
                    "yolo_invalid_number",
                    (
                        "YOLO label contains "
                        "an invalid numeric value"
                    ),
                    path=path,
                    frame_id=frame_id,
                )
            )
            continue

        if class_id not in known_class_ids:
            errors.append(
                _issue(
                    "error",
                    "yolo_unknown_class_id",
                    f"Unknown class ID: {class_id}",
                    path=path,
                    frame_id=frame_id,
                )
            )

        if not all(
            math.isfinite(value)
            for value in values
        ):
            errors.append(
                _issue(
                    "error",
                    "yolo_non_finite_value",
                    "YOLO coordinates contain NaN or infinity",
                    path=path,
                    frame_id=frame_id,
                )
            )
            continue

        x_center, y_center, width, height = values

        if not (
            0.0 <= x_center <= 1.0
            and 0.0 <= y_center <= 1.0
        ):
            errors.append(
                _issue(
                    "error",
                    "yolo_center_out_of_bounds",
                    "YOLO center is outside [0, 1]",
                    path=path,
                    frame_id=frame_id,
                )
            )

        if not (
            0.0 < width <= 1.0
            and 0.0 < height <= 1.0
        ):
            errors.append(
                _issue(
                    "error",
                    "yolo_invalid_size",
                    "YOLO width/height must be in (0, 1]",
                    path=path,
                    frame_id=frame_id,
                )
            )

        left = x_center - width / 2.0
        right = x_center + width / 2.0
        top = y_center - height / 2.0
        bottom = y_center + height / 2.0

        epsilon = 1e-6

        if (
            left < -epsilon
            or right > 1.0 + epsilon
            or top < -epsilon
            or bottom > 1.0 + epsilon
        ):
            errors.append(
                _issue(
                    "error",
                    "yolo_bbox_out_of_bounds",
                    "YOLO bounding box exceeds image bounds",
                    path=path,
                    frame_id=frame_id,
                )
            )

        annotations.append(
            {
                "class_id": class_id,
                "bbox": values,
                "line_number": line_number,
            }
        )

    return annotations


def validate_dataset(dataset_directory):
    dataset_directory = Path(
        dataset_directory,
    )

    errors = []
    warnings = []

    report = {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "validator": "bvt_dataset_validator",
        "status": "FAIL",
        "errors": errors,
        "warnings": warnings,
        "statistics": {
            "frames": 0,
            "images": 0,
            "labels": 0,
            "objects": 0,
            "classes": 0,
        },
    }

    if not dataset_directory.is_dir():
        errors.append(
            _issue(
                "error",
                "dataset_missing",
                "Dataset directory does not exist",
                path=dataset_directory,
            )
        )
        return report

    manifest_path = (
        dataset_directory / "manifest.json"
    )

    if not manifest_path.is_file():
        errors.append(
            _issue(
                "error",
                "manifest_missing",
                "manifest.json does not exist",
                path=manifest_path,
            )
        )
        return report

    try:
        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        errors.append(
            _issue(
                "error",
                "manifest_invalid_json",
                f"Cannot read manifest.json: {exc}",
                path=manifest_path,
            )
        )
        return report

    if (
        manifest.get("schema_version")
        != DATASET_MANIFEST_SCHEMA_VERSION
    ):
        errors.append(
            _issue(
                "error",
                "manifest_schema_mismatch",
                (
                    "Unsupported manifest schema: "
                    f"{manifest.get('schema_version')!r}"
                ),
                path=manifest_path,
            )
        )

    if not manifest.get("toolkit_version"):
        errors.append(
            _issue(
                "error",
                "manifest_toolkit_version_missing",
                "Toolkit version is missing",
                path=manifest_path,
            )
        )

    dataset_info = manifest.get(
        "dataset",
        {},
    )

    if not dataset_info.get("dataset_id"):
        errors.append(
            _issue(
                "error",
                "dataset_id_missing",
                "Dataset ID is missing",
                path=manifest_path,
            )
        )

    generation = manifest.get(
        "generation",
        {},
    )

    if "seed" not in generation:
        errors.append(
            _issue(
                "error",
                "seed_missing",
                "Generation seed is missing",
                path=manifest_path,
            )
        )

    annotations_info = manifest.get(
        "annotations",
        {},
    )

    if annotations_info.get("format") != "yolo":
        errors.append(
            _issue(
                "error",
                "annotation_format_invalid",
                "Expected YOLO annotation format",
                path=manifest_path,
            )
        )

    declared_classes = annotations_info.get(
        "classes",
        [],
    )

    class_map = {}

    for item in declared_classes:
        class_id = item.get("id")
        class_name = item.get("name")

        if (
            not isinstance(class_id, int)
            or class_id < 0
            or not isinstance(class_name, str)
            or not class_name
        ):
            errors.append(
                _issue(
                    "error",
                    "class_definition_invalid",
                    f"Invalid class definition: {item!r}",
                    path=manifest_path,
                )
            )
            continue

        if class_id in class_map:
            errors.append(
                _issue(
                    "error",
                    "class_id_duplicate",
                    f"Duplicate class ID: {class_id}",
                    path=manifest_path,
                )
            )

        class_map[class_id] = class_name

    report["statistics"]["classes"] = len(
        class_map
    )

    classes_file = annotations_info.get(
        "classes_file",
    )

    if not classes_file:
        errors.append(
            _issue(
                "error",
                "classes_file_missing",
                "classes_file is missing from manifest",
                path=manifest_path,
            )
        )

    else:
        try:
            classes_path = _safe_dataset_path(
                dataset_directory,
                classes_file,
            )

        except ValueError as exc:
            errors.append(
                _issue(
                    "error",
                    "classes_path_invalid",
                    str(exc),
                    path=classes_file,
                )
            )
            classes_path = None

        if (
            classes_path is not None
            and not classes_path.is_file()
        ):
            errors.append(
                _issue(
                    "error",
                    "classes_file_not_found",
                    "classes.txt does not exist",
                    path=classes_path,
                )
            )

        elif classes_path is not None:
            class_lines = [
                line.strip()
                for line in classes_path.read_text(
                    encoding="utf-8",
                ).splitlines()
                if line.strip()
            ]

            expected_lines = [
                class_map[class_id]
                for class_id in sorted(class_map)
            ]

            if class_lines != expected_lines:
                errors.append(
                    _issue(
                        "error",
                        "classes_file_mismatch",
                        (
                            "classes.txt does not match "
                            "manifest classes"
                        ),
                        path=classes_path,
                    )
                )

    if not class_map:
        warnings.append(
            _issue(
                "warning",
                "no_classes",
                "Dataset contains no registered classes",
            )
        )

    frames = manifest.get(
        "frames",
        [],
    )

    if not isinstance(frames, list):
        errors.append(
            _issue(
                "error",
                "frames_invalid",
                "Manifest frames must be an array",
                path=manifest_path,
            )
        )
        frames = []

    report["statistics"]["frames"] = len(
        frames
    )

    expected_frame_count = generation.get(
        "frame_count",
    )

    if expected_frame_count != len(frames):
        errors.append(
            _issue(
                "error",
                "frame_count_mismatch",
                (
                    f"Manifest says {expected_frame_count} frames, "
                    f"but contains {len(frames)}"
                ),
                path=manifest_path,
            )
        )

    render_info = manifest.get(
        "render",
        {},
    )

    expected_width = render_info.get(
        "resolution_x",
    )
    expected_height = render_info.get(
        "resolution_y",
    )

    referenced_images = set()
    referenced_labels = set()
    frame_ids = set()
    image_hashes = {}

    total_objects = 0

    for frame in frames:
        frame_id = frame.get(
            "frame_id",
        )

        if not frame_id:
            errors.append(
                _issue(
                    "error",
                    "frame_id_missing",
                    "Frame ID is missing",
                    path=manifest_path,
                )
            )
            continue

        if frame_id in frame_ids:
            errors.append(
                _issue(
                    "error",
                    "frame_id_duplicate",
                    f"Duplicate frame ID: {frame_id}",
                    path=manifest_path,
                    frame_id=frame_id,
                )
            )

        frame_ids.add(
            frame_id,
        )

        image_relative = frame.get(
            "image",
        )

        label_relative = frame.get(
            "label",
        )

        if not image_relative:
            errors.append(
                _issue(
                    "error",
                    "image_path_missing",
                    "Image path is missing",
                    frame_id=frame_id,
                )
            )
            continue

        if not label_relative:
            errors.append(
                _issue(
                    "error",
                    "label_path_missing",
                    "Label path is missing",
                    frame_id=frame_id,
                )
            )
            continue

        try:
            image_path = _safe_dataset_path(
                dataset_directory,
                image_relative,
            )

            label_path = _safe_dataset_path(
                dataset_directory,
                label_relative,
            )

        except ValueError as exc:
            errors.append(
                _issue(
                    "error",
                    "frame_path_invalid",
                    str(exc),
                    frame_id=frame_id,
                )
            )
            continue

        referenced_images.add(
            image_path.resolve(),
        )

        referenced_labels.add(
            label_path.resolve(),
        )

        if not image_path.is_file():
            errors.append(
                _issue(
                    "error",
                    "image_missing",
                    "Referenced image does not exist",
                    path=image_path,
                    frame_id=frame_id,
                )
            )

        else:
            report["statistics"]["images"] += 1

            try:
                width, height = _read_png_size(
                    image_path,
                )

                if (
                    expected_width is not None
                    and width != expected_width
                ):
                    errors.append(
                        _issue(
                            "error",
                            "image_width_mismatch",
                            (
                                f"Expected width {expected_width}, "
                                f"got {width}"
                            ),
                            path=image_path,
                            frame_id=frame_id,
                        )
                    )

                if (
                    expected_height is not None
                    and height != expected_height
                ):
                    errors.append(
                        _issue(
                            "error",
                            "image_height_mismatch",
                            (
                                f"Expected height {expected_height}, "
                                f"got {height}"
                            ),
                            path=image_path,
                            frame_id=frame_id,
                        )
                    )

            except (
                OSError,
                ValueError,
            ) as exc:
                errors.append(
                    _issue(
                        "error",
                        "image_invalid",
                        f"Invalid PNG image: {exc}",
                        path=image_path,
                        frame_id=frame_id,
                    )
                )

            digest = _sha256(
                image_path,
            )

            previous_frame = image_hashes.get(
                digest,
            )

            if previous_frame is not None:
                errors.append(
                    _issue(
                        "error",
                        "duplicate_image",
                        (
                            "Image is identical to frame "
                            f"{previous_frame}"
                        ),
                        path=image_path,
                        frame_id=frame_id,
                    )
                )

            image_hashes[digest] = frame_id

        if not label_path.is_file():
            errors.append(
                _issue(
                    "error",
                    "label_missing",
                    "Referenced label does not exist",
                    path=label_path,
                    frame_id=frame_id,
                )
            )
            parsed_labels = []

        else:
            report["statistics"]["labels"] += 1

            parsed_labels = _parse_yolo_label(
                label_path,
                set(class_map),
                frame_id,
                errors,
            )

        objects = frame.get(
            "objects",
            [],
        )

        if not isinstance(objects, list):
            errors.append(
                _issue(
                    "error",
                    "frame_objects_invalid",
                    "Frame objects must be an array",
                    path=manifest_path,
                    frame_id=frame_id,
                )
            )
            objects = []

        total_objects += len(objects)

        if len(parsed_labels) != len(objects):
            errors.append(
                _issue(
                    "error",
                    "label_object_count_mismatch",
                    (
                        f"Label count {len(parsed_labels)} "
                        f"does not match object count {len(objects)}"
                    ),
                    path=label_path,
                    frame_id=frame_id,
                )
            )

        instance_ids = set()

        for index, obj in enumerate(objects):
            instance_id = obj.get(
                "instance_id",
            )

            if not instance_id:
                errors.append(
                    _issue(
                        "error",
                        "instance_id_missing",
                        "Object instance_id is missing",
                        path=manifest_path,
                        frame_id=frame_id,
                    )
                )

            elif instance_id in instance_ids:
                errors.append(
                    _issue(
                        "error",
                        "instance_id_duplicate",
                        (
                            "Duplicate instance_id "
                            f"{instance_id}"
                        ),
                        path=manifest_path,
                        frame_id=frame_id,
                    )
                )

            instance_ids.add(
                instance_id,
            )

            class_id = obj.get(
                "class_id",
            )

            class_name = obj.get(
                "class_name",
            )

            if class_id not in class_map:
                errors.append(
                    _issue(
                        "error",
                        "manifest_unknown_class_id",
                        f"Unknown object class ID: {class_id}",
                        path=manifest_path,
                        frame_id=frame_id,
                    )
                )

            elif class_map[class_id] != class_name:
                errors.append(
                    _issue(
                        "error",
                        "manifest_class_name_mismatch",
                        (
                            f"Class ID {class_id} is "
                            f"{class_map[class_id]!r}, "
                            f"not {class_name!r}"
                        ),
                        path=manifest_path,
                        frame_id=frame_id,
                    )
                )

            if index < len(parsed_labels):
                label = parsed_labels[index]

                if label["class_id"] != class_id:
                    errors.append(
                        _issue(
                            "error",
                            "manifest_label_class_mismatch",
                            (
                                "Manifest object class differs "
                                "from YOLO label"
                            ),
                            path=label_path,
                            frame_id=frame_id,
                        )
                    )

                bbox = obj.get(
                    "bbox_yolo",
                )

                if (
                    not isinstance(bbox, list)
                    or len(bbox) != 4
                ):
                    errors.append(
                        _issue(
                            "error",
                            "manifest_bbox_invalid",
                            "Manifest bbox_yolo must contain 4 values",
                            path=manifest_path,
                            frame_id=frame_id,
                        )
                    )

                else:
                    for manifest_value, label_value in zip(
                        bbox,
                        label["bbox"],
                    ):
                        if (
                            abs(
                                manifest_value
                                - label_value
                            )
                            > 1e-5
                        ):
                            errors.append(
                                _issue(
                                    "error",
                                    "manifest_label_bbox_mismatch",
                                    (
                                        "Manifest bbox differs "
                                        "from YOLO label"
                                    ),
                                    path=label_path,
                                    frame_id=frame_id,
                                )
                            )
                            break

    report["statistics"]["objects"] = (
        total_objects
    )

    if total_objects == 0:
        warnings.append(
            _issue(
                "warning",
                "no_annotated_objects",
                "Dataset contains no annotated objects",
            )
        )

    images_directory = (
        dataset_directory / "images"
    )

    labels_directory = (
        dataset_directory / "labels"
    )

    if images_directory.is_dir():
        for path in images_directory.glob(
            "*.png"
        ):
            if (
                path.resolve()
                not in referenced_images
            ):
                errors.append(
                    _issue(
                        "error",
                        "orphan_image",
                        "Image is not referenced by manifest",
                        path=path,
                    )
                )

    if labels_directory.is_dir():
        for path in labels_directory.glob(
            "*.txt"
        ):
            if (
                path.resolve()
                not in referenced_labels
            ):
                errors.append(
                    _issue(
                        "error",
                        "orphan_label",
                        "Label is not referenced by manifest",
                        path=path,
                    )
                )

    report["status"] = (
        "PASS"
        if not errors
        else "FAIL"
    )

    return report


def write_validation_report(
    dataset_directory,
    report,
):
    dataset_directory = Path(
        dataset_directory,
    )

    report_path = (
        dataset_directory
        / "validation.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return report_path
