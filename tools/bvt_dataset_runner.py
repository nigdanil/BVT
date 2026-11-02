#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.materials.service import set_material_role
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


SCENARIO_SCHEMA = "bvt-cli-scenario-1"
CLI_ERROR_SCHEMA = "bvt-cli-error-1"

INTERNAL_SETTINGS = {
    "initialized",
    "schema_version",
}


def parse_args():
    argv = sys.argv

    if "--" in argv:
        argv = argv[
            argv.index("--") + 1:
        ]
    else:
        argv = []

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        required=True,
    )

    return parser.parse_args(
        argv
    )


def load_config(
    path,
):
    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    schema = data.get(
        "schema_version"
    )

    if schema != SCENARIO_SCHEMA:
        raise ValueError(
            "Unsupported scenario schema: "
            f"{schema!r}; expected "
            f"{SCENARIO_SCHEMA!r}"
        )

    return data


def resolve_output_directory(
    value,
):
    value = str(
        value
    ).strip()

    if not value:
        raise ValueError(
            "output_directory cannot be empty"
        )

    # Blender-style // paths stay relative
    # to the loaded .blend file.
    if value.startswith("//"):
        return value

    path = Path(
        value
    )

    if not path.is_absolute():
        path = (
            ROOT
            / path
        )

    return str(
        path.resolve()
    )


def apply_project(
    scene,
    config,
):
    settings = scene.bvt_project

    project = config.get(
        "project",
        {},
    )

    allowed = {
        "project_name",
        "output_directory",
        "seed",
        "frame_count",
        "project_id",
    }

    unknown = (
        set(project)
        - allowed
    )

    if unknown:
        raise ValueError(
            "Unsupported project keys: "
            + ", ".join(
                sorted(unknown)
            )
        )

    for key, value in project.items():
        if key == "output_directory":
            value = resolve_output_directory(
                value
            )

        setattr(
            settings,
            key,
            value,
        )

    extra_settings = config.get(
        "settings",
        {},
    )

    if not isinstance(
        extra_settings,
        dict,
    ):
        raise ValueError(
            "settings must be an object"
        )

    for key, value in extra_settings.items():
        if key in INTERNAL_SETTINGS:
            raise ValueError(
                f"Setting is internal: {key}"
            )

        if not hasattr(
            settings,
            key,
        ):
            raise ValueError(
                "Unknown BVT project setting: "
                f"{key}"
            )

        setattr(
            settings,
            key,
            value,
        )

    initialize_project(
        scene
    )

    return settings


def configure_objects(
    scene,
    config,
):
    configured = []

    for item in config.get(
        "objects",
        [],
    ):
        name = item.get(
            "name"
        )

        if not name:
            raise ValueError(
                "Object name is required"
            )

        obj = scene.objects.get(
            name
        )

        if obj is None:
            raise ValueError(
                f"Object not found: {name}"
            )

        settings = obj.bvt_object

        if "class_id" in item:
            settings.class_id = int(
                item["class_id"]
            )

        if "class_name" in item:
            settings.class_name = str(
                item["class_name"]
            )

        if "annotation_enabled" in item:
            settings.annotation_enabled = bool(
                item[
                    "annotation_enabled"
                ]
            )

        if "instance_id" in item:
            settings.instance_id = str(
                item["instance_id"]
            )

        register_object(
            obj
        )

        configured.append(
            obj.name
        )

    return configured


def get_principled_node(
    material,
):
    if not material.use_nodes:
        return None

    if material.node_tree is None:
        return None

    for node in material.node_tree.nodes:
        if (
            node.type
            == "BSDF_PRINCIPLED"
        ):
            return node

    return None


def configure_materials(
    scene,
    config,
):
    configured = []

    for item in config.get(
        "materials",
        [],
    ):
        name = item.get(
            "name"
        )

        if not name:
            raise ValueError(
                "Material name is required"
            )

        material = bpy.data.materials.get(
            name
        )

        create = bool(
            item.get(
                "create",
                False,
            )
        )

        if (
            material is None
            and create
        ):
            material = (
                bpy.data.materials.new(
                    name=name
                )
            )

        if material is None:
            raise ValueError(
                f"Material not found: {name}"
            )

        if item.get(
            "use_nodes",
            True,
        ):
            material.use_nodes = True

        role = item.get(
            "role"
        )

        if role is not None:
            set_material_role(
                material,
                role,
            )

        if (
            "roughness"
            in item
        ):
            principled = (
                get_principled_node(
                    material
                )
            )

            if principled is None:
                raise ValueError(
                    "Principled BSDF not found "
                    f"in material: {name}"
                )

            principled.inputs[
                "Roughness"
            ].default_value = float(
                item["roughness"]
            )

        for object_name in item.get(
            "assign_to",
            [],
        ):
            obj = scene.objects.get(
                object_name
            )

            if obj is None:
                raise ValueError(
                    "Material target object "
                    f"not found: {object_name}"
                )

            data = getattr(
                obj,
                "data",
                None,
            )

            slots = getattr(
                data,
                "materials",
                None,
            )

            if slots is None:
                raise ValueError(
                    "Object does not support "
                    f"materials: {object_name}"
                )

            existing = {
                slot.as_pointer()
                for slot in slots
                if slot is not None
            }

            if (
                material.as_pointer()
                not in existing
            ):
                slots.append(
                    material
                )

        configured.append(
            material.name
        )

    return configured


def main():
    args = parse_args()

    config_path = Path(
        args.config
    ).resolve()

    if not config_path.is_file():
        raise FileNotFoundError(
            config_path
        )

    config = load_config(
        config_path
    )

    bvt.register()

    scene = bpy.context.scene

    settings = apply_project(
        scene,
        config,
    )

    configured_materials = (
        configure_materials(
            scene,
            config,
        )
    )

    configured_objects = (
        configure_objects(
            scene,
            config,
        )
    )

    if scene.camera is None:
        raise ValueError(
            "Scene has no active camera"
        )

    result = generate_dataset(
        scene
    )

    manifest = json.loads(
        result[
            "manifest_path"
        ].read_text(
            encoding="utf-8"
        )
    )

    frames = manifest.get(
        "frames",
        [],
    )

    expected_frames = int(
        settings.frame_count
    )

    if (
        len(
            result[
                "image_paths"
            ]
        )
        != expected_frames
    ):
        raise RuntimeError(
            "Unexpected generated image count"
        )

    if (
        len(
            result[
                "label_paths"
            ]
        )
        != expected_frames
    ):
        raise RuntimeError(
            "Unexpected generated label count"
        )

    if (
        len(frames)
        != expected_frames
    ):
        raise RuntimeError(
            "Unexpected manifest frame count"
        )

    validation_status = (
        result[
            "validation_report"
        ][
            "status"
        ]
    )

    if (
        validation_status
        != "PASS"
    ):
        raise RuntimeError(
            "Dataset validation failed"
        )

    print(
        "DATASET_DIRECTORY="
        f"{result['dataset_directory']}"
    )

    print(
        "MANIFEST="
        f"{result['manifest_path']}"
    )

    print(
        "CONFIG="
        f"{result['generation_config_path']}"
    )

    print(
        "VALIDATION="
        f"{result['validation_path']}"
    )

    print(
        "STATISTICS="
        f"{result['statistics_path']}"
    )

    print(
        "HEALTH="
        f"{result['health_path']}"
    )

    print(
        "HASHES="
        f"{result['hashes_path']}"
    )

    print(
        "ARCHIVE="
        f"{result['archive_path']}"
    )

    print(
        f"FRAMES={len(frames)}"
    )

    print(
        "OBJECTS="
        + ",".join(
            configured_objects
        )
    )

    print(
        "MATERIALS="
        + ",".join(
            configured_materials
        )
    )

    print(
        "VALIDATION_STATUS="
        f"{validation_status}"
    )

    print(
        "BVT_DATASET_CLI=OK"
    )


def _emit_cli_error(
    code,
    message,
):
    message = " ".join(
        str(
            message
        ).splitlines()
    ).strip()

    print(
        "ERROR_SCHEMA="
        + CLI_ERROR_SCHEMA
    )

    print(
        "ERROR_CODE="
        + str(
            code
        )
    )

    print(
        "ERROR_MESSAGE="
        + message
    )

    print(
        "BVT_DATASET_CLI=FAIL"
    )


def run_cli():
    try:
        main()
        return 0

    except FileNotFoundError as exc:
        _emit_cli_error(
            "INPUT_NOT_FOUND",
            exc,
        )
        return 1

    except ValueError as exc:
        _emit_cli_error(
            "INVALID_INPUT",
            exc,
        )
        return 1

    except Exception as exc:
        _emit_cli_error(
            "GENERATION_FAILED",
            (
                type(exc).__name__
                + ": "
                + str(exc)
            ),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        run_cli()
    )
