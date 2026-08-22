import json
import math
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    TMP
    / "jpeg-compression-artifact.blend"
)

CLEAN_IMAGE = (
    TMP
    / "jpeg-clean-baseline.png"
)

FIRST_IMAGE = (
    TMP
    / "jpeg-first-run.png"
)

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


PIXEL_EQUAL_TOLERANCE = 1e-6
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def load_pixels(path):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        size = tuple(
            image.size
        )

        pixels = list(
            image.pixels[:]
        )

        return size, pixels

    finally:
        bpy.data.images.remove(
            image
        )


def compare_images(
    first_path,
    second_path,
):
    first_size, first_pixels = (
        load_pixels(
            first_path
        )
    )

    second_size, second_pixels = (
        load_pixels(
            second_path
        )
    )

    assert first_size == second_size

    assert (
        len(first_pixels)
        == len(second_pixels)
    )

    squared_error = 0.0
    max_error = 0.0

    for first, second in zip(
        first_pixels,
        second_pixels,
    ):
        difference = abs(
            first
            - second
        )

        max_error = max(
            max_error,
            difference,
        )

        squared_error += (
            difference
            * difference
        )

    return {
        "rmse": math.sqrt(
            squared_error
            / len(first_pixels)
        ),
        "max_error": max_error,
    }


if TMP.exists():
    shutil.rmtree(
        TMP
    )

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    ),
)


project = scene.bvt_project

project.project_name = (
    "JPEG Compression Artifact Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 1

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False

project.artifact_engine_enabled = False


initialize_project(
    scene
)


cube = bpy.data.objects["Cube"]

cube.bvt_object.class_id = 0
cube.bvt_object.class_name = "cube"

register_object(
    cube
)


clean = generate_dataset(
    scene
)

assert (
    clean["validation_report"]["status"]
    == "PASS"
)

shutil.copy2(
    clean["image_path"],
    CLEAN_IMAGE,
)


clean_manifest = json.loads(
    clean["manifest_path"].read_text(
        encoding="utf-8"
    )
)

clean_bbox = tuple(
    clean_manifest[
        "frames"
    ][0]["objects"][0][
        "bbox_yolo"
    ]
)


project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = False
project.artifact_reflection_enabled = False
project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False

project.artifact_jpeg_enabled = True
project.artifact_jpeg_probability = 1.0
project.artifact_jpeg_intensity = 0.75
project.artifact_jpeg_quality = 25
project.artifact_jpeg_chroma_loss = 0.80


first = generate_dataset(
    scene
)


assert (
    first["validation_report"]["status"]
    == "PASS"
)


with first["image_path"].open(
    "rb"
) as stream:
    assert (
        stream.read(8)
        == PNG_SIGNATURE
    )


manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8"
    )
)


frame = manifest["frames"][0]

artifact_list = (
    frame["artifacts"][
        "artifacts"
    ]
)

artifact_ids = [
    item["artifact"]
    for item in artifact_list
]

assert artifact_ids == [
    "over_exposure",
    "reflection",
    "motion_blur",
    "noise",
    "jpeg_compression",
]


artifacts = {
    item["artifact"]: item
    for item
    in artifact_list
}


assert set(
    artifacts
) == {
    "jpeg_compression",
    "motion_blur",
    "noise",
    "over_exposure",
    "reflection",
}


assert (
    artifacts["reflection"]["enabled"]
    is False
)

assert (
    artifacts["reflection"]["applied"]
    is False
)

assert (
    artifacts["reflection"]["stage"]
    == "pre_render"
)

assert (
    artifacts["motion_blur"]["enabled"]
    is False
)

assert (
    artifacts["motion_blur"][
        "execution_order"
    ]
    == 50
)

assert (
    artifacts["noise"]["enabled"]
    is False
)

assert (
    artifacts[
        "over_exposure"
    ]["enabled"]
    is False
)


jpeg = (
    artifacts[
        "jpeg_compression"
    ]
)


assert jpeg["enabled"] is True
assert jpeg["applied"] is True

assert jpeg["stage"] == "post_render"
assert jpeg["category"] == "compression"

assert (
    artifacts["noise"][
        "execution_order"
    ]
    == 100
)

assert (
    jpeg["execution_order"]
    == 200
)

assert jpeg["probability"] == 1.0
assert jpeg["intensity"] == 0.75


assert (
    jpeg["options"]["quality"]
    == 25
)

assert (
    abs(
        jpeg["options"][
            "chroma_loss"
        ]
        - 0.80
    )
    <= 1e-7
)


expected_seed = derive_subseed(
    frame["frame_seed"],
    "artifact",
    "jpeg_compression",
)

assert jpeg["seed"] == expected_seed


parameters = (
    jpeg["parameters"]
)


assert (
    parameters["codec"]
    == "jpeg"
)

assert (
    parameters["dataset_format"]
    == "png"
)

assert (
    parameters[
        "configured_quality"
    ]
    == 25
)

assert (
    parameters[
        "effective_quality"
    ]
    == 44
)

assert (
    abs(
        parameters[
            "configured_chroma_loss"
        ]
        - 0.80
    )
    <= 1e-7
)

assert (
    abs(
        parameters[
            "effective_chroma_loss"
        ]
        - 0.60
    )
    <= 1e-7
)

assert (
    parameters[
        "changed_components"
    ]
    > 0
)


jpeg_bbox = tuple(
    frame["objects"][0][
        "bbox_yolo"
    ]
)

assert (
    jpeg_bbox
    == clean_bbox
)


jpeg_vs_clean = compare_images(
    CLEAN_IMAGE,
    first["image_path"],
)

assert (
    jpeg_vs_clean["max_error"]
    > PIXEL_EQUAL_TOLERANCE
)


shutil.copy2(
    first["image_path"],
    FIRST_IMAGE,
)


first_artifact_record = (
    frame["artifacts"]
)


second = generate_dataset(
    scene
)


assert (
    second["validation_report"]["status"]
    == "PASS"
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8"
    )
)


second_artifact_record = (
    second_manifest[
        "frames"
    ][0]["artifacts"]
)


assert (
    first_artifact_record
    == second_artifact_record
)


repeat = compare_images(
    FIRST_IMAGE,
    second["image_path"],
)


assert (
    repeat["max_error"]
    <= PIXEL_EQUAL_TOLERANCE
)


temporary_files = list(
    first["image_path"].parent.glob(
        "*.bvt-jpeg-temp.jpg"
    )
)

assert temporary_files == []


print(
    "BVT_JPEG_COMPRESSION_ARTIFACT_SMOKE=OK"
)

print(
    "jpeg_seed=",
    jpeg["seed"],
)

print(
    "configured_quality=",
    parameters[
        "configured_quality"
    ],
)

print(
    "effective_quality=",
    parameters[
        "effective_quality"
    ],
)

print(
    "effective_chroma_loss=",
    parameters[
        "effective_chroma_loss"
    ],
)

print(
    "jpeg_vs_clean_rmse=",
    jpeg_vs_clean["rmse"],
)

print(
    "jpeg_vs_clean_max_error=",
    jpeg_vs_clean["max_error"],
)

print(
    "repeat_max_error=",
    repeat["max_error"],
)

print(
    "bbox_unchanged=",
    jpeg_bbox == clean_bbox,
)

print(
    "output_is_png=True"
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_JPEG_COMPRESSION_ARTIFACT_CLEANUP=OK"
)
