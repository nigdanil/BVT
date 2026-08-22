import hashlib
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
    / "noise-artifact.blend"
)

CLEAN_IMAGE = (
    TMP
    / "noise-clean-baseline.png"
)

FIRST_DIRECTORY = (
    TMP
    / "noise-first"
)

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.artifacts.providers.noise import (
    NOISE_MAX_AMPLITUDE,
)
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


PIXEL_EQUAL_TOLERANCE = 1e-6


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


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

    rmse = math.sqrt(
        squared_error
        / len(first_pixels)
    )

    return {
        "rmse": rmse,
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
    "Noise Artifact Smoke"
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

cube_settings = cube.bvt_object
cube_settings.class_id = 0
cube_settings.class_name = "cube"

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

project.artifact_noise_enabled = True
project.artifact_noise_probability = 1.0
project.artifact_noise_intensity = 0.50


first = generate_dataset(
    scene
)


assert (
    first["validation_report"]["status"]
    == "PASS"
)


manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8"
    )
)


noise_seeds = []
pixel_seeds = []
bboxes = []


for frame in manifest["frames"]:
    engine = frame["artifacts"]

    assert engine["enabled"] is True

    artifacts = {
        item["artifact"]: item
        for item
        in engine["artifacts"]
    }

    assert set(
        artifacts
    ) == {
        "noise",
        "over_exposure",
    }

    exposure = (
        artifacts[
            "over_exposure"
        ]
    )

    assert (
        exposure["enabled"]
        is False
    )

    assert (
        exposure["applied"]
        is False
    )

    noise = artifacts["noise"]

    assert noise["enabled"] is True
    assert noise["applied"] is True

    assert (
        noise["stage"]
        == "post_render"
    )

    assert (
        noise["category"]
        == "sensor"
    )

    assert (
        noise["probability"]
        == 1.0
    )

    assert (
        noise["intensity"]
        == 0.50
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "artifact",
        "noise",
    )

    assert (
        noise["seed"]
        == expected_seed
    )

    expected_roll = random.Random(
        expected_seed
    ).random()

    assert (
        abs(
            noise["decision_roll"]
            - expected_roll
        )
        <= 1e-15
    )

    parameters = (
        noise["parameters"]
    )

    expected_pixel_seed = (
        derive_subseed(
            expected_seed,
            "artifact-noise",
            "pixels",
        )
    )

    assert (
        parameters["pixel_seed"]
        == expected_pixel_seed
    )

    expected_amplitude = (
        NOISE_MAX_AMPLITUDE
        * 0.50
    )

    assert (
        abs(
            parameters["amplitude"]
            - expected_amplitude
        )
        <= 1e-12
    )

    assert (
        parameters["distribution"]
        == "uniform"
    )

    assert (
        parameters["color_mode"]
        == "rgb_independent"
    )

    assert (
        parameters[
            "changed_components"
        ]
        > 0
    )

    noise_seeds.append(
        noise["seed"]
    )

    pixel_seeds.append(
        parameters[
            "pixel_seed"
        ]
    )

    bbox = tuple(
        frame["objects"][0][
            "bbox_yolo"
        ]
    )

    bboxes.append(
        bbox
    )

    assert (
        bbox
        == clean_bbox
    )


assert len(
    set(noise_seeds)
) == 3

assert len(
    set(pixel_seeds)
) == 3

assert len(
    set(bboxes)
) == 1


noise_vs_clean = []

for image_path in first["image_paths"]:
    comparison = compare_images(
        CLEAN_IMAGE,
        image_path,
    )

    assert (
        comparison[
            "max_error"
        ]
        > PIXEL_EQUAL_TOLERANCE
    )

    noise_vs_clean.append(
        comparison
    )


image_hashes = [
    sha256(path)
    for path
    in first["image_paths"]
]

assert len(
    set(image_hashes)
) == 3


FIRST_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

first_copies = []

for path in first["image_paths"]:
    destination = (
        FIRST_DIRECTORY
        / path.name
    )

    shutil.copy2(
        path,
        destination,
    )

    first_copies.append(
        destination
    )


first_artifact_records = [
    frame["artifacts"]
    for frame
    in manifest["frames"]
]


first_labels = [
    path.read_text(
        encoding="utf-8"
    )
    for path
    in first["label_paths"]
]


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


second_artifact_records = [
    frame["artifacts"]
    for frame
    in second_manifest["frames"]
]


assert (
    first_artifact_records
    == second_artifact_records
)


second_labels = [
    path.read_text(
        encoding="utf-8"
    )
    for path
    in second["label_paths"]
]


assert (
    first_labels
    == second_labels
)


repeat_comparisons = []

for first_path, second_path in zip(
    first_copies,
    second["image_paths"],
):
    comparison = compare_images(
        first_path,
        second_path,
    )

    assert (
        comparison[
            "max_error"
        ]
        <= PIXEL_EQUAL_TOLERANCE
    )

    repeat_comparisons.append(
        comparison
    )


print(
    "BVT_NOISE_ARTIFACT_SMOKE=OK"
)

print(
    "noise_seeds=",
    noise_seeds,
)

print(
    "pixel_seeds=",
    pixel_seeds,
)

print(
    "unique_noisy_images=",
    len(
        set(image_hashes)
    ),
)

print(
    "unique_bboxes=",
    len(
        set(bboxes)
    ),
)

print(
    "noise_vs_clean_rmse=",
    [
        item["rmse"]
        for item
        in noise_vs_clean
    ],
)

print(
    "repeat_max_errors=",
    [
        item["max_error"]
        for item
        in repeat_comparisons
    ],
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_NOISE_ARTIFACT_CLEANUP=OK"
)
