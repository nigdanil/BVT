from pathlib import Path

from .bbox import calculate_yolo_bbox
from .service import iter_annotated_objects


def build_class_map(objects):
    classes = {}

    for obj in objects:
        settings = obj.bvt_object

        class_id = settings.class_id
        class_name = settings.class_name

        existing_name = classes.get(class_id)

        if (
            existing_name is not None
            and existing_name != class_name
        ):
            raise ValueError(
                f"Class ID {class_id} is assigned to multiple names: "
                f"{existing_name!r} and {class_name!r}"
            )

        classes[class_id] = class_name

    if classes:
        expected_ids = list(
            range(max(classes) + 1)
        )

        actual_ids = sorted(classes)

        if actual_ids != expected_ids:
            raise ValueError(
                "YOLO class IDs must be contiguous and start from 0"
            )

    return classes


def write_yolo_annotations(
    scene,
    dataset_directory,
    frame_id,
):
    dataset_directory = Path(
        dataset_directory,
    )

    labels_directory = (
        dataset_directory / "labels"
    )

    labels_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    objects = iter_annotated_objects(
        scene,
    )

    classes = build_class_map(
        objects,
    )

    label_path = (
        labels_directory
        / f"{frame_id}.txt"
    )

    classes_path = (
        dataset_directory
        / "classes.txt"
    )

    lines = []
    annotations = []

    for obj in objects:
        bbox = calculate_yolo_bbox(
            scene,
            scene.camera,
            obj,
        )

        if bbox is None:
            continue

        settings = obj.bvt_object

        lines.append(
            (
                f"{settings.class_id} "
                f"{bbox['x_center']:.6f} "
                f"{bbox['y_center']:.6f} "
                f"{bbox['width']:.6f} "
                f"{bbox['height']:.6f}"
            )
        )

        annotations.append(
            {
                "instance_id": settings.instance_id,
                "object_name": obj.name,
                "class_id": settings.class_id,
                "class_name": settings.class_name,
                "bbox_yolo": [
                    bbox["x_center"],
                    bbox["y_center"],
                    bbox["width"],
                    bbox["height"],
                ],
            }
        )

    label_content = ""

    if lines:
        label_content = (
            "\n".join(lines)
            + "\n"
        )

    label_path.write_text(
        label_content,
        encoding="utf-8",
    )

    class_lines = [
        classes[class_id]
        for class_id in sorted(classes)
    ]

    classes_content = ""

    if class_lines:
        classes_content = (
            "\n".join(class_lines)
            + "\n"
        )

    classes_path.write_text(
        classes_content,
        encoding="utf-8",
    )

    return {
        "label_path": label_path,
        "classes_path": classes_path,
        "classes": classes,
        "annotations": annotations,
    }
