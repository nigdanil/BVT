import array
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "beverage-fridge-v0.1.blend"
)

BASELINE_OUTPUT = (
    TMP
    / "retail-edge-cases-combined-baseline"
)

COMBINED_OUTPUT = (
    TMP
    / "retail-edge-cases-combined"
)


sys.path.insert(
    0,
    str(SOURCE),
)

sys.path.insert(
    0,
    str(
        ROOT
        / "tests"
    ),
)

from png_pixel_utils import decoded_png_hash


import bpy
import bvt

from bvt.annotation.bbox import calculate_yolo_bbox
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset
from bvt.retail.edge_cases import EMPTY_SLOT_NAMESPACE
from bvt.retail.edge_cases import OCCLUSION_NAMESPACE
from bvt.retail.edge_cases import WRONG_ANGLE_NAMESPACE
from bvt.retail.edge_cases import WRONG_POSITION_NAMESPACE
from bvt.retail.edge_cases import iter_retail_products


def close(
    first,
    second,
    tolerance=1e-7,
):
    return abs(
        float(first)
        - float(second)
    ) <= tolerance


def tuple3(
    value,
):
    return tuple(
        float(item)
        for item
        in value
    )


def occluders(
    scene,
):
    return [
        obj
        for obj
        in scene.objects
        if bool(
            obj.get(
                "bvt_retail_edge_case_occluder",
                False,
            )
        )
    ]


for directory in (
    BASELINE_OUTPUT,
    COMBINED_OUTPUT,
):
    if directory.exists():
        shutil.rmtree(
            directory
        )


bvt.register()


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


scene = bpy.context.scene

project = scene.bvt_project

project.project_name = (
    "Retail Edge Cases Combined Smoke"
)

project.project_id = (
    "retail-edge-cases-combined-smoke"
)

project.seed = 20261101
project.frame_count = 5

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False
project.artifact_engine_enabled = False

project.retail_edge_cases_enabled = True

project.retail_wrong_angle_enabled = False
project.retail_wrong_position_enabled = False
project.retail_empty_slot_enabled = False
project.retail_occlusion_enabled = False

project.retail_wrong_angle_min_degrees = 22.0
project.retail_wrong_angle_max_degrees = 22.0

project.retail_wrong_position_offset_x = 0.035
project.retail_wrong_position_offset_y = 0.020

project.retail_occlusion_width_factor = 0.45
project.retail_occlusion_height_factor = 0.70


initialize_project(
    scene
)


products = list(
    iter_retail_products(
        scene
    )
)


assert len(
    products
) == 18


product_by_instance = {
    obj.bvt_object.instance_id: obj
    for obj
    in products
}


baseline_state = {
    obj.bvt_object.instance_id: {
        "location": (
            tuple3(
                obj.location
            )
        ),
        "rotation": (
            tuple3(
                obj.rotation_euler
            )
        ),
        "hide_render": bool(
            obj.hide_render
        ),
        "annotation_enabled": bool(
            obj.bvt_object.annotation_enabled
        ),
    }
    for obj
    in products
}


# ---------------------------------------------------------
# Clean structural baseline.
# ---------------------------------------------------------

project.output_directory = str(
    BASELINE_OUTPUT
)


baseline_result = generate_dataset(
    scene
)


assert (
    baseline_result[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


baseline_manifest = json.loads(
    baseline_result[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


assert len(
    baseline_manifest[
        "frames"
    ]
) == 5


for frame in baseline_manifest[
    "frames"
]:
    assert (
        frame[
            "retail_edge_cases"
        ][
            "events"
        ]
        == []
    )

    assert len(
        frame[
            "objects"
        ]
    ) == 18


baseline_images = sorted(
    (
        baseline_result[
            "dataset_directory"
        ]
        / "images"
    ).glob(
        "*.png"
    )
)


baseline_hashes = [
    decoded_png_hash(
        path
    )
    for path
    in baseline_images
]


assert len(
    baseline_hashes
) == 5


# ---------------------------------------------------------
# Enable all four EP4 edge cases.
# ---------------------------------------------------------

project.output_directory = str(
    COMBINED_OUTPUT
)

project.retail_wrong_angle_enabled = True
project.retail_wrong_position_enabled = True
project.retail_empty_slot_enabled = True
project.retail_occlusion_enabled = True


first_result = generate_dataset(
    scene
)


assert (
    first_result[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)


first_manifest = json.loads(
    first_result[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


assert len(
    first_manifest[
        "frames"
    ]
) == 5


# No temporary occluders may survive generation.
assert occluders(
    scene
) == []


# Entire source product state must be restored.
for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    state = baseline_state[
        instance_id
    ]

    assert (
        tuple3(
            obj.location
        )
        == state[
            "location"
        ]
    )

    assert (
        tuple3(
            obj.rotation_euler
        )
        == state[
            "rotation"
        ]
    )

    assert (
        bool(
            obj.hide_render
        )
        == state[
            "hide_render"
        ]
    )

    assert (
        bool(
            obj.bvt_object.annotation_enabled
        )
        == state[
            "annotation_enabled"
        ]
    )


combined_images = sorted(
    (
        first_result[
            "dataset_directory"
        ]
        / "images"
    ).glob(
        "*.png"
    )
)


first_hashes = [
    decoded_png_hash(
        path
    )
    for path
    in combined_images
]


assert len(
    first_hashes
) == 5


# Every frame must have a structural RGB difference.
for baseline_hash, combined_hash in zip(
    baseline_hashes,
    first_hashes,
):
    assert (
        baseline_hash
        != combined_hash
    )


selected_by_case = {
    "wrong_angle": [],
    "wrong_position": [],
    "empty_slot": [],
    "occlusion": [],
}


for frame in first_manifest[
    "frames"
]:
    edge_cases = frame[
        "retail_edge_cases"
    ]

    assert (
        edge_cases[
            "enabled"
        ]
        is True
    )

    assert (
        edge_cases[
            "version"
        ]
        == "retail-edge-cases-v0.1"
    )

    assert (
        edge_cases[
            "seed_strategy"
        ]
        == "sha256-namespace-v1"
    )

    events = edge_cases[
        "events"
    ]

    assert len(
        events
    ) == 4

    assert [
        event[
            "edge_case"
        ]
        for event
        in events
    ] == [
        "wrong_angle",
        "wrong_position",
        "empty_slot",
        "occlusion",
    ]


    by_case = {
        event[
            "edge_case"
        ]: event
        for event
        in events
    }


    wrong_angle = by_case[
        "wrong_angle"
    ]

    wrong_position = by_case[
        "wrong_position"
    ]

    empty_slot = by_case[
        "empty_slot"
    ]

    occlusion = by_case[
        "occlusion"
    ]


    for event in events:
        assert (
            event[
                "applied"
            ]
            is True
        )

        assert (
            "before"
            in event
        )

        assert (
            "after"
            in event
        )


    for edge_case in selected_by_case:
        selected_by_case[
            edge_case
        ].append(
            by_case[
                edge_case
            ][
                "instance_id"
            ]
        )


    # -----------------------------------------------------
    # Deterministic target selection.
    # -----------------------------------------------------

    expected_wrong_angle = min(
        products,
        key=lambda obj: (
            derive_subseed(
                frame[
                    "frame_seed"
                ],
                (
                    WRONG_ANGLE_NAMESPACE
                    + "/target"
                ),
                (
                    obj
                    .bvt_object
                    .instance_id
                ),
            ),
            (
                obj
                .bvt_object
                .instance_id
            ),
        ),
    )

    assert (
        wrong_angle[
            "instance_id"
        ]
        == (
            expected_wrong_angle
            .bvt_object
            .instance_id
        )
    )


    expected_wrong_position = min(
        products,
        key=lambda obj: (
            derive_subseed(
                frame[
                    "frame_seed"
                ],
                (
                    WRONG_POSITION_NAMESPACE
                    + "/target"
                ),
                (
                    obj
                    .bvt_object
                    .instance_id
                ),
            ),
            (
                obj
                .bvt_object
                .instance_id
            ),
        ),
    )

    assert (
        wrong_position[
            "instance_id"
        ]
        == (
            expected_wrong_position
            .bvt_object
            .instance_id
        )
    )


    expected_empty = min(
        products,
        key=lambda obj: (
            derive_subseed(
                frame[
                    "frame_seed"
                ],
                (
                    EMPTY_SLOT_NAMESPACE
                    + "/target"
                ),
                str(
                    obj.get(
                        "bvt_slot_id",
                        "",
                    )
                ),
            ),
            str(
                obj.get(
                    "bvt_slot_id",
                    "",
                )
            ),
        ),
    )

    assert (
        empty_slot[
            "instance_id"
        ]
        == (
            expected_empty
            .bvt_object
            .instance_id
        )
    )


    visible_after_empty = [
        obj
        for obj
        in products
        if (
            obj.bvt_object.instance_id
            != empty_slot[
                "instance_id"
            ]
        )
    ]


    expected_occlusion = min(
        visible_after_empty,
        key=lambda obj: (
            derive_subseed(
                frame[
                    "frame_seed"
                ],
                (
                    OCCLUSION_NAMESPACE
                    + "/target"
                ),
                (
                    obj
                    .bvt_object
                    .instance_id
                ),
            ),
            (
                obj
                .bvt_object
                .instance_id
            ),
        ),
    )

    assert (
        occlusion[
            "instance_id"
        ]
        == (
            expected_occlusion
            .bvt_object
            .instance_id
        )
    )

    assert (
        occlusion[
            "instance_id"
        ]
        != empty_slot[
            "instance_id"
        ]
    )


    # -----------------------------------------------------
    # Final annotation state.
    # -----------------------------------------------------

    annotations = frame[
        "objects"
    ]

    assert len(
        annotations
    ) == 17


    annotation_by_instance = {
        item[
            "instance_id"
        ]: item
        for item
        in annotations
    }


    assert (
        empty_slot[
            "instance_id"
        ]
        not in annotation_by_instance
    )

    assert (
        occlusion[
            "instance_id"
        ]
        in annotation_by_instance
    )


    # Every emitted bbox follows clipping policy.
    for annotation in annotations:
        bbox = annotation[
            "bbox_yolo"
        ]

        x_center = float(
            bbox[0]
        )

        y_center = float(
            bbox[1]
        )

        width = float(
            bbox[2]
        )

        height = float(
            bbox[3]
        )

        assert (
            0.0
            <= x_center
            <= 1.0
        )

        assert (
            0.0
            <= y_center
            <= 1.0
        )

        assert (
            0.0
            < width
            <= 1.0
        )

        assert (
            0.0
            < height
            <= 1.0
        )

        assert (
            x_center
            - width / 2.0
            >= -1e-6
        )

        assert (
            x_center
            + width / 2.0
            <= 1.0 + 1e-6
        )

        assert (
            y_center
            - height / 2.0
            >= -1e-6
        )

        assert (
            y_center
            + height / 2.0
            <= 1.0 + 1e-6
        )


    # -----------------------------------------------------
    # Full-object bbox policy under occlusion.
    #
    # Reconstruct final structural transform of the
    # occluded target without the temporary occluder.
    # -----------------------------------------------------

    occluded_instance = (
        occlusion[
            "instance_id"
        ]
    )

    obj = product_by_instance[
        occluded_instance
    ]

    saved_location = (
        obj.location.copy()
    )

    saved_rotation = (
        obj.rotation_euler.copy()
    )

    try:
        state = baseline_state[
            occluded_instance
        ]

        obj.location = (
            state[
                "location"
            ]
        )

        obj.rotation_euler = (
            state[
                "rotation"
            ]
        )


        if (
            wrong_position[
                "instance_id"
            ]
            == occluded_instance
        ):
            after_location = (
                wrong_position[
                    "after"
                ][
                    "location_m"
                ]
            )

            obj.location = (
                float(
                    after_location[0]
                ),
                float(
                    after_location[1]
                ),
                float(
                    after_location[2]
                ),
            )


        if (
            wrong_angle[
                "instance_id"
            ]
            == occluded_instance
        ):
            obj.rotation_euler.z = (
                math.radians(
                    wrong_angle[
                        "after"
                    ][
                        "rotation_z_degrees"
                    ]
                )
            )


        bpy.context.view_layer.update()


        expected_bbox = (
            calculate_yolo_bbox(
                scene,
                scene.camera,
                obj,
            )
        )

        assert (
            expected_bbox
            is not None
        )


        actual_bbox = (
            annotation_by_instance[
                occluded_instance
            ][
                "bbox_yolo"
            ]
        )


        expected_values = (
            expected_bbox[
                "x_center"
            ],
            expected_bbox[
                "y_center"
            ],
            expected_bbox[
                "width"
            ],
            expected_bbox[
                "height"
            ],
        )


        for actual, expected in zip(
            actual_bbox,
            expected_values,
        ):
            assert close(
                actual,
                expected,
            )

    finally:
        obj.location = (
            saved_location
        )

        obj.rotation_euler = (
            saved_rotation
        )

        bpy.context.view_layer.update()


# Every combined label file contains exactly 17 products.
for path in first_result[
    "label_paths"
]:
    rows = [
        line
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(
        rows
    ) == 17


# All eight classes remain represented.
assert len(
    first_manifest[
        "annotations"
    ][
        "classes"
    ]
) == 8


# ---------------------------------------------------------
# Deterministic rerun.
# ---------------------------------------------------------

second_result = generate_dataset(
    scene
)


second_manifest = json.loads(
    second_result[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


second_images = sorted(
    (
        second_result[
            "dataset_directory"
        ]
        / "images"
    ).glob(
        "*.png"
    )
)


second_hashes = [
    decoded_png_hash(
        path
    )
    for path
    in second_images
]


assert (
    first_hashes
    == second_hashes
)


first_edge_cases = [
    frame[
        "retail_edge_cases"
    ]
    for frame
    in first_manifest[
        "frames"
    ]
]

second_edge_cases = [
    frame[
        "retail_edge_cases"
    ]
    for frame
    in second_manifest[
        "frames"
    ]
]


assert (
    first_edge_cases
    == second_edge_cases
)


first_objects = [
    frame[
        "objects"
    ]
    for frame
    in first_manifest[
        "frames"
    ]
]

second_objects = [
    frame[
        "objects"
    ]
    for frame
    in second_manifest[
        "frames"
    ]
]


assert (
    first_objects
    == second_objects
)


# No mutation leakage after rerun.
assert occluders(
    scene
) == []


for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    state = baseline_state[
        instance_id
    ]

    assert (
        tuple3(
            obj.location
        )
        == state[
            "location"
        ]
    )

    assert (
        tuple3(
            obj.rotation_euler
        )
        == state[
            "rotation"
        ]
    )

    assert (
        bool(
            obj.hide_render
        )
        == state[
            "hide_render"
        ]
    )

    assert (
        bool(
            obj.bvt_object.annotation_enabled
        )
        == state[
            "annotation_enabled"
        ]
    )


print(
    "frames=5"
)

print(
    "edge_cases_per_frame=4"
)

print(
    "event_order=wrong_angle,wrong_position,empty_slot,occlusion"
)

print(
    "products_before_empty_slot=18"
)

print(
    "products_after_empty_slot=17"
)

print(
    "classes_preserved=8"
)

print(
    "deterministic_object_selection=True"
)

print(
    "deterministic_manifest=True"
)

print(
    "deterministic_rgb=True"
)

print(
    "manifest_before_after=True"
)

print(
    "bbox_normalized=True"
)

print(
    "bbox_clipped_to_frame=True"
)

print(
    "occlusion_full_object_bbox=True"
)

print(
    "empty_slot_no_bbox=True"
)

print(
    "per_frame_reset=True"
)

print(
    "no_mutation_leakage=True"
)

print(
    "scene_rgb_changed=True"
)

print(
    "final_scene_restored=True"
)

print(
    "BVT_RETAIL_EDGE_CASES_COMBINED_SMOKE=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


for directory in (
    BASELINE_OUTPUT,
    COMBINED_OUTPUT,
):
    if directory.exists():
        shutil.rmtree(
            directory
        )
