import json
from pathlib import Path

import bpy

from ..core.constants import DATASET_LAYOUT_VERSION
from ..core.constants import DATASET_MANIFEST_SCHEMA_VERSION
from ..core.constants import GENERATION_CONFIG_SCHEMA_VERSION
from ..core.constants import TOOLKIT_VERSION
from ..core.seeding import FRAME_SEED_STRATEGY


def build_dataset_manifest(
    scene,
    settings,
    frames,
    resolution_x,
    resolution_y,
    generation_config_file=(
        "config/generation.json"
    ),
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
        "layout": {
            "version": DATASET_LAYOUT_VERSION,
            "images_directory": "images",
            "labels_directory": "labels",
            "classes_file": "classes.txt",
            "generation_config_file": (
                generation_config_file
            ),
            "splits": {
                "train": "splits/train.txt",
                "validation": "splits/validation.txt",
                "test": "splits/test.txt",
            },
            "statistics_file": "statistics.json",
            "health_file": "health.json",
            "validation_file": "validation.json",
            "hashes_file": "hashes.json",
            "hashes_file": "hashes.json",
        },
        "generation": {
            "seed": settings.seed,
            "frame_count": len(frames),
            "frame_seed_strategy": FRAME_SEED_STRATEGY,
            "config_file": (
                generation_config_file
            ),
            "config_schema_version": (
                GENERATION_CONFIG_SCHEMA_VERSION
            ),
        },
        "render": {
            "engine": scene.render.engine,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "resolution_percentage": 100,
            "format": "PNG",
        },
        "frames": frames,
    }


def write_manifest(
    path,
    manifest,
):
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
