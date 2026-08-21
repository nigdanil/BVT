import json
from pathlib import Path

import bpy

from ..core.constants import DATASET_MANIFEST_SCHEMA_VERSION
from ..core.constants import TOOLKIT_VERSION


def build_dataset_manifest(
    scene,
    settings,
    image_relative_path,
    resolution_x,
    resolution_y,
):
    return {
        "schema_version": DATASET_MANIFEST_SCHEMA_VERSION,
        "toolkit_version": TOOLKIT_VERSION,
        "blender": {
            "version": bpy.app.version_string,
        },
        "dataset": {
            "dataset_id": f"{settings.project_id}-dataset",
            "project_id": settings.project_id,
            "project_name": settings.project_name,
        },
        "generation": {
            "seed": settings.seed,
            "frame_count": 1,
        },
        "render": {
            "engine": scene.render.engine,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "resolution_percentage": 100,
            "format": "PNG",
        },
        "frames": [
            {
                "frame_id": "000001",
                "scene": scene.name,
                "camera": scene.camera.name,
                "image": image_relative_path,
            }
        ],
    }


def write_manifest(path, manifest):
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
