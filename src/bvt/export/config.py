import json
from pathlib import Path

from ..core.constants import (
    GENERATION_CONFIG_SCHEMA_VERSION,
)
from ..core.constants import TOOLKIT_VERSION


_PROJECT_FIELDS = {
    "project_name",
    "project_id",
    "output_directory",
    "seed",
    "frame_count",
}


_INTERNAL_FIELDS = {
    "rna_type",
    "initialized",
    "schema_version",
}


def _json_value(
    value,
):
    if (
        value is None
        or isinstance(
            value,
            (
                bool,
                int,
                float,
                str,
            ),
        )
    ):
        return value

    if isinstance(
        value,
        (
            tuple,
            list,
        ),
    ):
        return [
            _json_value(
                item
            )
            for item
            in value
        ]

    try:
        return [
            _json_value(
                item
            )
            for item
            in value
        ]

    except TypeError:
        return str(
            value
        )


def _public_generation_settings(
    settings,
):
    result = {}


    for prop in (
        settings.bl_rna.properties
    ):
        name = prop.identifier

        if (
            name
            in _PROJECT_FIELDS
            or name
            in _INTERNAL_FIELDS
        ):
            continue

        result[
            name
        ] = _json_value(
            getattr(
                settings,
                name,
            )
        )


    return {
        key: result[key]
        for key
        in sorted(
            result
        )
    }


def build_generation_config(
    scene,
    settings,
    resolution_x,
    resolution_y,
):
    return {
        "schema_version": (
            GENERATION_CONFIG_SCHEMA_VERSION
        ),
        "toolkit_version": (
            TOOLKIT_VERSION
        ),
        "project": {
            "schema_version": (
                settings.schema_version
            ),
            "project_id": (
                settings.project_id
            ),
            "project_name": (
                settings.project_name
            ),
            "output_directory": (
                settings.output_directory
            ),
            "seed": int(
                settings.seed
            ),
            "frame_count": int(
                settings.frame_count
            ),
        },
        "scene": {
            "name": scene.name,
            "camera": (
                scene.camera.name
                if scene.camera
                is not None
                else None
            ),
        },
        "render": {
            "engine": (
                scene.render.engine
            ),
            "resolution_x": int(
                resolution_x
            ),
            "resolution_y": int(
                resolution_y
            ),
            "resolution_percentage": 100,
            "format": "PNG",
        },
        "settings": (
            _public_generation_settings(
                settings
            )
        ),
    }


def write_generation_config(
    path,
    config,
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
            config,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
