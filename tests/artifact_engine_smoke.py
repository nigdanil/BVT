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
    / "artifact-engine.blend"
)

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.artifacts.engine import ARTIFACT_ENGINE_VERSION
from bvt.artifacts.providers.exposure import (
    OVER_EXPOSURE_MAX_STOPS,
)
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


PIXEL_EQUAL_TOLERANCE = 1e-6


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
            image,
        )


def compare_images(
    first_path,
    second_path,
):
    first_size, first_pixels = (
        load_pixels(
            first_path,
        )
    )

    second_size, second_pixels = (
        load_pixels(
            second_path,
        )
    )

    assert (
        first_size
        == second_size
    )

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
    "Artifact Engine Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 3

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False

project.artifact_engine_enabled = True

project.artifact_over_exposure_enabled = True
project.artifact_over_exposure_probability = 0.50
project.artifact_over_exposure_intensity = 0.50

project.artifact_reflection_enabled = False
project.artifact_motion_blur_enabled = False
project.artifact_noise_enabled = False
project.artifact_jpeg_enabled = False


initialize_project(
    scene,
)


cube = bpy.data.objects["Cube"]

cube_settings = cube.bvt_object

cube_settings.class_id = 0
cube_settings.class_name = "cube"

register_object(
    cube,
)


original_exposure = float(
    scene.view_settings.exposure
)


first = generate_dataset(
    scene,
)


assert (
    first["validation_report"]["status"]
    == "PASS"
)


assert (
    abs(
        float(
            scene.view_settings.exposure
        )
        - original_exposure
    )
    <= 1e-9
)


first_manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8",
    )
)


frames = first_manifest["frames"]

assert len(frames) == 3


artifact_records = []
applied_flags = []
bboxes = []


for frame in frames:
    engine_result = (
        frame["artifacts"]
    )

    assert (
        engine_result["enabled"]
        is True
    )

    assert (
        engine_result["version"]
        == ARTIFACT_ENGINE_VERSION
    )

    assert (
        len(
            engine_result["artifacts"]
        )
        == 5
    )

    artifacts_by_id = {
        item["artifact"]: item
        for item
        in engine_result["artifacts"]
    }

    assert set(
        artifacts_by_id
    ) == {
        "jpeg_compression",
        "motion_blur",
        "noise",
        "over_exposure",
        "reflection",
    }

    reflection_artifact = (
        artifacts_by_id[
            "reflection"
        ]
    )

    assert (
        reflection_artifact["enabled"]
        is False
    )

    assert (
        reflection_artifact["applied"]
        is False
    )

    assert (
        reflection_artifact["stage"]
        == "pre_render"
    )

    assert (
        reflection_artifact["parameters"]
        == {}
    )

    motion_blur_artifact = (
        artifacts_by_id[
            "motion_blur"
        ]
    )

    assert (
        motion_blur_artifact["enabled"]
        is False
    )

    assert (
        motion_blur_artifact["applied"]
        is False
    )

    assert (
        motion_blur_artifact["stage"]
        == "post_render"
    )

    assert (
        motion_blur_artifact[
            "execution_order"
        ]
        == 50
    )

    assert (
        motion_blur_artifact["parameters"]
        == {}
    )

    jpeg_artifact = (
        artifacts_by_id[
            "jpeg_compression"
        ]
    )

    assert (
        jpeg_artifact["enabled"]
        is False
    )

    assert (
        jpeg_artifact["applied"]
        is False
    )

    assert (
        jpeg_artifact["stage"]
        == "post_render"
    )

    noise_artifact = (
        artifacts_by_id["noise"]
    )

    assert (
        noise_artifact["enabled"]
        is False
    )

    assert (
        noise_artifact["applied"]
        is False
    )

    assert (
        noise_artifact["stage"]
        == "post_render"
    )

    assert (
        noise_artifact["parameters"]
        == {}
    )

    artifact = (
        artifacts_by_id[
            "over_exposure"
        ]
    )

    assert (
        artifact["stage"]
        == "pre_render"
    )

    assert (
        artifact["artifact"]
        == "over_exposure"
    )

    assert (
        artifact["category"]
        == "lighting"
    )

    assert (
        artifact["enabled"]
        is True
    )

    assert (
        artifact["probability"]
        == 0.50
    )

    assert (
        artifact["intensity"]
        == 0.50
    )

    expected_seed = derive_subseed(
        frame["frame_seed"],
        "artifact",
        "over_exposure",
    )

    assert (
        artifact["seed"]
        == expected_seed
    )

    expected_roll = random.Random(
        expected_seed
    ).random()

    assert (
        abs(
            artifact[
                "decision_roll"
            ]
            - expected_roll
        )
        <= 1e-15
    )

    expected_applied = (
        expected_roll
        < 0.50
    )

    assert (
        artifact["applied"]
        is expected_applied
    )

    if expected_applied:
        parameters = (
            artifact["parameters"]
        )

        expected_stops = (
            OVER_EXPOSURE_MAX_STOPS
            * 0.50
        )

        assert (
            abs(
                parameters[
                    "exposure_stops"
                ]
                - expected_stops
            )
            <= 1e-9
        )

        assert (
            parameters[
                "exposure_after"
            ]
            > parameters[
                "base_exposure"
            ]
        )

    else:
        assert (
            artifact["parameters"]
            == {}
        )

    artifact_records.append(
        engine_result
    )

    applied_flags.append(
        artifact["applied"]
    )

    assert (
        len(
            frame["objects"]
        )
        == 1
    )

    bboxes.append(
        tuple(
            frame["objects"][0][
                "bbox_yolo"
            ]
        )
    )


# Fixed seed 12345 with probability 0.5 must
# produce both clean and artifact frames.
assert set(
    applied_flags
) == {
    False,
    True,
}


# Exposure changes appearance only.
assert len(
    set(bboxes)
) == 1


applied_index = (
    applied_flags.index(
        True
    )
)

clean_indices = [
    index
    for index, applied
    in enumerate(
        applied_flags
    )
    if not applied
]


artifact_vs_clean = compare_images(
    first["image_paths"][
        applied_index
    ],
    first["image_paths"][
        clean_indices[0]
    ],
)


assert (
    artifact_vs_clean[
        "max_error"
    ]
    > PIXEL_EQUAL_TOLERANCE
)


if len(clean_indices) >= 2:
    clean_vs_clean = compare_images(
        first["image_paths"][
            clean_indices[0]
        ],
        first["image_paths"][
            clean_indices[1]
        ],
    )

    assert (
        clean_vs_clean[
            "max_error"
        ]
        <= PIXEL_EQUAL_TOLERANCE
    )


first_labels = [
    path.read_text(
        encoding="utf-8"
    )
    for path
    in first["label_paths"]
]


second = generate_dataset(
    scene,
)


assert (
    abs(
        float(
            scene.view_settings.exposure
        )
        - original_exposure
    )
    <= 1e-9
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8",
    )
)


second_artifact_records = [
    frame["artifacts"]
    for frame
    in second_manifest["frames"]
]


assert (
    artifact_records
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


print(
    "BVT_ARTIFACT_ENGINE_SMOKE=OK"
)

print(
    "applied_flags=",
    applied_flags,
)

print(
    "artifact_seeds=",
    [
        next(
            artifact
            for artifact
            in item["artifacts"]
            if (
                artifact["artifact"]
                == "over_exposure"
            )
        )["seed"]
        for item
        in artifact_records
    ],
)

print(
    "artifact_vs_clean_rmse=",
    artifact_vs_clean[
        "rmse"
    ],
)

print(
    "artifact_vs_clean_max_error=",
    artifact_vs_clean[
        "max_error"
    ],
)

print(
    "unique_bboxes=",
    len(
        set(bboxes)
    ),
)

print(
    "exposure_restored=",
    float(
        scene.view_settings.exposure
    ),
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_ARTIFACT_ENGINE_CLEANUP=OK"
)
