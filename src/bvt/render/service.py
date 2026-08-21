from pathlib import Path

import bpy

from ..core.constants import DEFAULT_RENDER_RESOLUTION
from ..export.manifest import build_dataset_manifest
from ..export.manifest import write_manifest


def resolve_output_directory(settings):
    raw_path = settings.output_directory.strip()

    if not raw_path:
        raise ValueError("Output Directory cannot be empty")

    if raw_path.startswith("//") and not bpy.data.filepath:
        raise ValueError(
            "Save the .blend file before using a relative Output Directory"
        )

    resolved_path = bpy.path.abspath(raw_path)

    return Path(resolved_path)


def generate_minimal_dataset(scene):
    settings = scene.bvt_project

    if not settings.initialized:
        raise ValueError("Initialize the BVT project first")

    if scene.camera is None:
        raise ValueError("The scene does not have an active camera")

    output_directory = resolve_output_directory(settings)

    dataset_directory = output_directory / "dataset"
    images_directory = dataset_directory / "images"

    images_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame_id = "000001"

    image_path = images_directory / f"{frame_id}.png"
    manifest_path = dataset_directory / "manifest.json"

    original_filepath = scene.render.filepath
    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    original_resolution_percentage = scene.render.resolution_percentage
    original_file_format = scene.render.image_settings.file_format

    resolution = DEFAULT_RENDER_RESOLUTION

    try:
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(image_path)

        bpy.ops.render.render(
            write_still=True,
            scene=scene.name,
        )

        manifest = build_dataset_manifest(
            scene=scene,
            settings=settings,
            image_relative_path=f"images/{frame_id}.png",
            resolution_x=resolution,
            resolution_y=resolution,
        )

        write_manifest(
            manifest_path,
            manifest,
        )

    finally:
        scene.render.filepath = original_filepath
        scene.render.resolution_x = original_resolution_x
        scene.render.resolution_y = original_resolution_y
        scene.render.resolution_percentage = original_resolution_percentage
        scene.render.image_settings.file_format = original_file_format

    return {
        "dataset_directory": dataset_directory,
        "image_path": image_path,
        "manifest_path": manifest_path,
    }
