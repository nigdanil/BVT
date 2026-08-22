import hashlib
import json
import math
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = TMP / "batch-generation.blend"
BASELINE = TMP / "batch-baseline"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.core.seeding import derive_frame_seed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
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
        size = tuple(image.size)

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
    first_size, first_pixels = load_pixels(
        first_path,
    )

    second_size, second_pixels = load_pixels(
        second_path,
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
            first - second
        )

        max_error = max(
            max_error,
            difference,
        )

        squared_error += (
            difference * difference
        )

    rmse = math.sqrt(
        squared_error
        / len(first_pixels)
    )

    return {
        "size": first_size,
        "rmse": rmse,
        "max_error": max_error,
    }


if TMP.exists():
    shutil.rmtree(TMP)

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)


project = scene.bvt_project

project.project_name = (
    "Batch Generation Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345
project.frame_count = 3

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


first = generate_dataset(
    scene,
)


assert len(first["image_paths"]) == 3
assert len(first["label_paths"]) == 3


expected_names = [
    "000001",
    "000002",
    "000003",
]


assert [
    path.stem
    for path in first["image_paths"]
] == expected_names


first_manifest = json.loads(
    first["manifest_path"].read_text(
        encoding="utf-8",
    )
)


assert (
    first_manifest["generation"]["frame_count"]
    == 3
)

assert (
    first_manifest["generation"]["seed"]
    == 12345
)


frames = first_manifest["frames"]

assert len(frames) == 3


expected_seeds = [
    derive_frame_seed(
        12345,
        index,
    )
    for index in range(
        1,
        4,
    )
]


actual_seeds = [
    frame["frame_seed"]
    for frame in frames
]


assert actual_seeds == expected_seeds
assert len(set(actual_seeds)) == 3


for index, frame in enumerate(
    frames,
    start=1,
):
    assert frame["frame_index"] == index
    assert frame["blender_frame"] == index

    assert (
        frame["image"]
        == f"images/{index:06d}.png"
    )

    assert (
        frame["label"]
        == f"labels/{index:06d}.txt"
    )


assert (
    first["validation_report"]["status"]
    == "PASS"
)


# Preserve first generation before second run.
shutil.copytree(
    first["dataset_directory"],
    BASELINE,
)


first_hashes = [
    sha256(
        BASELINE
        / "images"
        / f"{index:06d}.png"
    )
    for index in range(
        1,
        4,
    )
]


first_labels = [
    (
        BASELINE
        / "labels"
        / f"{index:06d}.txt"
    ).read_text(
        encoding="utf-8",
    )
    for index in range(
        1,
        4,
    )
]


second = generate_dataset(
    scene,
)


second_manifest = json.loads(
    second["manifest_path"].read_text(
        encoding="utf-8",
    )
)


second_hashes = [
    sha256(path)
    for path in second["image_paths"]
]


second_labels = [
    path.read_text(
        encoding="utf-8",
    )
    for path in second["label_paths"]
]


# Strict deterministic checks.
assert first_manifest == second_manifest
assert first_labels == second_labels


comparisons = []

for index in range(
    1,
    4,
):
    baseline_image = (
        BASELINE
        / "images"
        / f"{index:06d}.png"
    )

    second_image = (
        second["image_paths"][
            index - 1
        ]
    )

    comparisons.append(
        compare_images(
            baseline_image,
            second_image,
        )
    )


# Rendered PNG containers may differ byte-for-byte even when
# the decoded image is identical. Reproducibility is therefore
# verified against decoded pixel values.
PIXEL_RMSE_TOLERANCE = 1e-7
PIXEL_MAX_ERROR_TOLERANCE = 1e-6

for comparison in comparisons:
    assert (
        comparison["rmse"]
        <= PIXEL_RMSE_TOLERANCE
    )

    assert (
        comparison["max_error"]
        <= PIXEL_MAX_ERROR_TOLERANCE
    )


print("BVT_BATCH_STRUCTURE_REPRODUCIBILITY=OK")
print("frames=", len(frames))
print("frame_seeds=", actual_seeds)

print(
    "byte_hashes_equal=",
    first_hashes == second_hashes,
)

for index, comparison in enumerate(
    comparisons,
    start=1,
):
    print(
        f"frame_{index:06d}_rmse=",
        comparison["rmse"],
    )

    print(
        f"frame_{index:06d}_max_error=",
        comparison["max_error"],
    )


print(
    "warnings=",
    len(
        second[
            "validation_report"
        ]["warnings"]
    ),
)


bvt.unregister()

shutil.rmtree(
    TMP,
)


print("BVT_BATCH_GENERATION_SMOKE=OK")
