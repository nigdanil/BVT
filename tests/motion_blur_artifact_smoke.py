import json
import math
import random
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    TMP
    / "motion-blur-artifact.blend"
)

CLEAN_IMAGE = (
    TMP
    / "motion-blur-clean.png"
)

FIRST_DIR = (
    TMP
    / "motion-blur-first"
)

PIXEL_TOLERANCE = 1e-6
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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


def load_pixels(path):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        return (
            tuple(image.size),
            list(image.pixels[:]),
        )

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
    assert len(first_pixels) == len(second_pixels)

    squared_error = 0.0
    max_error = 0.0

    for first, second in zip(
        first_pixels,
        second_pixels,
    ):
        difference = abs(
            first - second
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

FIRST_DIR.mkdir(
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
    "Motion Blur Artifact Smoke"
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


cube = bpy.data.objects[
    "Cube"
]

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


project.frame_count = 3

project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = False
project.artifact_reflection_enabled = False
project.artifact_fingerprints_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False

project.artifact_motion_blur_enabled = True
project.artifact_motion_blur_probability = 1.0
project.artifact_motion_blur_intensity = 0.75
project.artifact_motion_blur_direction_range_degrees = 90.0
project.artifact_motion_blur_max_length_pixels = 14


first = generate_dataset(
    scene
)

assert (
    first["validation_report"]["status"]
    == "PASS"
)


first_root = (
    first["manifest_path"].parent
)

first_manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8"
    )
)


motion_seeds = []
direction_seeds = []
directions = []
bboxes = []
motion_vs_clean = []

first_artifact_records = []
first_labels = []


for index, frame in enumerate(
    first_manifest["frames"],
    start=1,
):
    engine = frame["artifacts"]

    assert engine["enabled"] is True

    artifact_list = (
        engine["artifacts"]
    )

    artifact_ids = [
        item["artifact"]
        for item in artifact_list
    ]

    assert artifact_ids == [
        "over_exposure",
        "reflection",
        "fingerprints",
        "motion_blur",
        "noise",
        "jpeg_compression",
    ]

    artifacts = {
        item["artifact"]: item
        for item in artifact_list
    }

    assert (
        artifacts[
            "over_exposure"
        ]["enabled"]
        is False
    )

    assert (
        artifacts[
            "reflection"
        ]["enabled"]
        is False
    )

    assert (
        artifacts[
            "reflection"
        ]["applied"]
        is False
    )

    assert (
        artifacts[
            "fingerprints"
        ]["enabled"]
        is False
    )

    assert (
        artifacts[
            "fingerprints"
        ]["applied"]
        is False
    )

    assert (
        artifacts["noise"]["enabled"]
        is False
    )

    assert (
        artifacts[
            "jpeg_compression"
        ]["enabled"]
        is False
    )

    motion = (
        artifacts[
            "motion_blur"
        ]
    )

    assert motion["enabled"] is True
    assert motion["applied"] is True

    assert (
        motion["stage"]
        == "post_render"
    )

    assert (
        motion["category"]
        == "camera"
    )

    assert (
        motion["execution_order"]
        == 50
    )

    assert (
        motion["probability"]
        == 1.0
    )

    assert (
        motion["intensity"]
        == 0.75
    )

    assert abs(
        motion["options"][
            "direction_range_degrees"
        ]
        - 90.0
    ) <= 1e-6

    assert (
        motion["options"][
            "max_length_pixels"
        ]
        == 14
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "artifact",
        "motion_blur",
    )

    assert (
        motion["seed"]
        == expected_seed
    )

    expected_direction_seed = derive_subseed(
        expected_seed,
        "artifact-motion-blur",
        "direction",
    )

    expected_direction = random.Random(
        expected_direction_seed
    ).uniform(
        -90.0,
        90.0,
    )

    parameters = (
        motion["parameters"]
    )

    assert (
        parameters["algorithm"]
        == "directional_box_blur"
    )

    assert (
        parameters["direction_seed"]
        == expected_direction_seed
    )

    assert abs(
        parameters[
            "direction_degrees"
        ]
        - expected_direction
    ) <= 1e-12

    assert (
        parameters[
            "configured_max_length_pixels"
        ]
        == 14
    )

    assert (
        parameters[
            "effective_length_pixels"
        ]
        == 11
    )

    assert (
        parameters[
            "kernel_sample_count"
        ]
        > 1
    )

    assert (
        parameters[
            "changed_components"
        ]
        > 0
    )

    bbox = tuple(
        frame["objects"][0][
            "bbox_yolo"
        ]
    )

    assert bbox == clean_bbox

    image_path = (
        first_root
        / "images"
        / f"{index:06d}.png"
    )

    with image_path.open(
        "rb"
    ) as stream:
        assert (
            stream.read(8)
            == PNG_SIGNATURE
        )

    comparison = compare_images(
        CLEAN_IMAGE,
        image_path,
    )

    assert (
        comparison["max_error"]
        > PIXEL_TOLERANCE
    )

    shutil.copy2(
        image_path,
        FIRST_DIR
        / image_path.name,
    )

    label_path = (
        first_root
        / "labels"
        / f"{index:06d}.txt"
    )

    first_labels.append(
        label_path.read_text(
            encoding="utf-8"
        )
    )

    first_artifact_records.append(
        engine
    )

    motion_seeds.append(
        expected_seed
    )

    direction_seeds.append(
        expected_direction_seed
    )

    directions.append(
        expected_direction
    )

    bboxes.append(
        bbox
    )

    motion_vs_clean.append(
        comparison["rmse"]
    )


assert len(set(motion_seeds)) == 3
assert len(set(direction_seeds)) == 3
assert len(set(directions)) == 3

assert len(set(bboxes)) == 1


second = generate_dataset(
    scene
)

assert (
    second["validation_report"]["status"]
    == "PASS"
)


second_root = (
    second["manifest_path"].parent
)

second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8"
    )
)


repeat_max_errors = []


for index, frame in enumerate(
    second_manifest["frames"],
    start=1,
):
    assert (
        frame["artifacts"]
        == first_artifact_records[
            index - 1
        ]
    )

    label_path = (
        second_root
        / "labels"
        / f"{index:06d}.txt"
    )

    assert (
        label_path.read_text(
            encoding="utf-8"
        )
        == first_labels[
            index - 1
        ]
    )

    comparison = compare_images(
        FIRST_DIR
        / f"{index:06d}.png",
        second_root
        / "images"
        / f"{index:06d}.png",
    )

    assert (
        comparison["max_error"]
        <= PIXEL_TOLERANCE
    )

    repeat_max_errors.append(
        comparison["max_error"]
    )


print(
    "BVT_MOTION_BLUR_ARTIFACT_SMOKE=OK"
)

print(
    "motion_seeds=",
    motion_seeds,
)

print(
    "direction_seeds=",
    direction_seeds,
)

print(
    "directions=",
    directions,
)

print(
    "effective_length_pixels=11"
)

print(
    "unique_bboxes=",
    len(set(bboxes)),
)

print(
    "motion_vs_clean_rmse=",
    motion_vs_clean,
)

print(
    "repeat_max_errors=",
    repeat_max_errors,
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_MOTION_BLUR_ARTIFACT_CLEANUP=OK"
)
