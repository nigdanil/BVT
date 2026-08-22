import shutil
from pathlib import Path

import bpy

from ..annotation.yolo import write_yolo_annotations
from ..artifacts.engine import apply_artifacts
from ..artifacts.engine import apply_post_render_artifacts
from ..artifacts.engine import capture_artifact_baseline
from ..artifacts.engine import restore_artifacts
from ..camera.randomizer import apply_random_camera
from ..camera.randomizer import capture_camera_baseline
from ..camera.randomizer import restore_camera
from ..core.constants import DEFAULT_RENDER_RESOLUTION
from ..core.seeding import derive_frame_seed
from ..export.manifest import build_dataset_manifest
from ..export.manifest import write_manifest
from ..lighting.randomizer import apply_random_lighting
from ..lighting.randomizer import capture_lighting_baseline
from ..lighting.randomizer import restore_lighting
from ..placement.randomizer import apply_random_placement
from ..placement.randomizer import capture_placement_baseline
from ..placement.randomizer import restore_placement
from ..validation.dataset import validate_dataset
from ..validation.dataset import write_validation_report


def resolve_output_directory(settings):
    raw_path = settings.output_directory.strip()

    if not raw_path:
        raise ValueError(
            "Output Directory cannot be empty"
        )

    if (
        raw_path.startswith("//")
        and not bpy.data.filepath
    ):
        raise ValueError(
            "Save the .blend file before using "
            "a relative Output Directory"
        )

    resolved_path = bpy.path.abspath(
        raw_path,
    )

    return Path(
        resolved_path,
    )


def generate_dataset(scene):
    settings = scene.bvt_project

    if not settings.initialized:
        raise ValueError(
            "Initialize the BVT project first"
        )

    if scene.camera is None:
        raise ValueError(
            "The scene does not have an active camera"
        )

    if settings.frame_count < 1:
        raise ValueError(
            "Frame Count must be at least 1"
        )

    output_directory = resolve_output_directory(
        settings,
    )

    dataset_directory = (
        output_directory / "dataset"
    )

    # Clean previous generated dataset so that decreasing
    # Frame Count cannot leave orphan images or labels.
    if dataset_directory.exists():
        shutil.rmtree(
            dataset_directory,
        )

    images_directory = (
        dataset_directory / "images"
    )

    images_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path = (
        dataset_directory
        / "manifest.json"
    )

    original_filepath = (
        scene.render.filepath
    )

    original_resolution_x = (
        scene.render.resolution_x
    )

    original_resolution_y = (
        scene.render.resolution_y
    )

    original_resolution_percentage = (
        scene.render.resolution_percentage
    )

    original_file_format = (
        scene.render.image_settings.file_format
    )

    original_frame = (
        scene.frame_current
    )

    resolution = DEFAULT_RENDER_RESOLUTION

    frames = []
    image_paths = []
    label_paths = []

    dataset_classes = None

    placement_baseline = (
        capture_placement_baseline(
            scene,
        )
    )

    camera_baseline = (
        capture_camera_baseline(
            scene,
        )
    )

    lighting_baseline = (
        capture_lighting_baseline(
            scene,
        )
    )

    artifact_baseline = (
        capture_artifact_baseline(
            scene,
        )
    )

    try:
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100

        scene.render.image_settings.file_format = (
            "PNG"
        )

        for frame_index in range(
            1,
            settings.frame_count + 1,
        ):
            frame_id = (
                f"{frame_index:06d}"
            )

            frame_seed = derive_frame_seed(
                settings.seed,
                frame_index,
            )

            # For now BVT maps generated frame N to Blender frame N.
            # Future randomizers will use frame_seed.
            scene.frame_set(
                frame_index,
            )

            placement_result = (
                apply_random_placement(
                    scene=scene,
                    project_settings=settings,
                    frame_seed=frame_seed,
                    baseline=placement_baseline,
                )
            )

            camera_result = (
                apply_random_camera(
                    scene=scene,
                    project_settings=settings,
                    frame_seed=frame_seed,
                    baseline=camera_baseline,
                )
            )

            lighting_result = (
                apply_random_lighting(
                    scene=scene,
                    project_settings=settings,
                    frame_seed=frame_seed,
                    baseline=lighting_baseline,
                )
            )

            artifact_result = (
                apply_artifacts(
                    scene=scene,
                    project_settings=settings,
                    frame_seed=frame_seed,
                    baseline=artifact_baseline,
                )
            )

            image_path = (
                images_directory
                / f"{frame_id}.png"
            )

            scene.render.filepath = str(
                image_path,
            )

            bpy.ops.render.render(
                write_still=True,
                scene=scene.name,
            )

            artifact_result = (
                apply_post_render_artifacts(
                    scene=scene,
                    image_path=image_path,
                    frame_seed=frame_seed,
                    artifact_result=artifact_result,
                    baseline=artifact_baseline,
                )
            )

            yolo_result = (
                write_yolo_annotations(
                    scene=scene,
                    dataset_directory=dataset_directory,
                    frame_id=frame_id,
                )
            )

            current_classes = dict(
                yolo_result["classes"]
            )

            if dataset_classes is None:
                dataset_classes = current_classes

            elif dataset_classes != current_classes:
                raise ValueError(
                    "Dataset classes changed between frames"
                )

            frames.append(
                {
                    "frame_id": frame_id,
                    "frame_index": frame_index,
                    "blender_frame": scene.frame_current,
                    "frame_seed": frame_seed,
                    "scene": scene.name,
                    "camera": scene.camera.name,
                    "image": (
                        f"images/{frame_id}.png"
                    ),
                    "label": (
                        f"labels/{frame_id}.txt"
                    ),
                    "objects": (
                        yolo_result[
                            "annotations"
                        ]
                    ),
                    "randomization": {
                        "placement": (
                            placement_result
                        ),
                        "camera": (
                            camera_result
                        ),
                        "lighting": (
                            lighting_result
                        ),
                    },
                    "artifacts": (
                        artifact_result
                    ),
                }
            )

            image_paths.append(
                image_path,
            )

            label_paths.append(
                yolo_result[
                    "label_path"
                ],
            )

        if dataset_classes is None:
            dataset_classes = {}

        manifest = build_dataset_manifest(
            scene=scene,
            settings=settings,
            frames=frames,
            resolution_x=resolution,
            resolution_y=resolution,
        )

        manifest["annotations"] = {
            "format": "yolo",
            "classes_file": "classes.txt",
            "classes": [
                {
                    "id": class_id,
                    "name": class_name,
                }
                for class_id, class_name
                in sorted(
                    dataset_classes.items()
                )
            ],
        }

        write_manifest(
            manifest_path,
            manifest,
        )

        validation_report = validate_dataset(
            dataset_directory,
        )

        validation_path = write_validation_report(
            dataset_directory,
            validation_report,
        )

        if (
            validation_report["status"]
            != "PASS"
        ):
            raise ValueError(
                "Dataset validation failed: "
                f"{len(validation_report['errors'])} error(s)"
            )

    finally:
        scene.frame_set(
            original_frame,
        )

        restore_artifacts(
            scene,
            artifact_baseline,
        )

        restore_lighting(
            scene,
            lighting_baseline,
        )

        restore_camera(
            scene,
            camera_baseline,
        )

        restore_placement(
            scene,
            placement_baseline,
        )

        scene.render.filepath = (
            original_filepath
        )

        scene.render.resolution_x = (
            original_resolution_x
        )

        scene.render.resolution_y = (
            original_resolution_y
        )

        scene.render.resolution_percentage = (
            original_resolution_percentage
        )

        scene.render.image_settings.file_format = (
            original_file_format
        )

    result = {
        "dataset_directory": dataset_directory,
        "manifest_path": manifest_path,
        "classes_path": (
            dataset_directory
            / "classes.txt"
        ),
        "validation_path": validation_path,
        "validation_report": validation_report,
        "image_paths": image_paths,
        "label_paths": label_paths,
    }

    # Compatibility for existing single-frame callers.
    if image_paths:
        result["image_path"] = image_paths[0]

    if label_paths:
        result["label_path"] = label_paths[0]

    return result


def generate_minimal_dataset(scene):
    """
    Compatibility wrapper for the pre-batch API.
    """
    return generate_dataset(
        scene,
    )
