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
    / "retail-wrong-angle-baseline"
)

WRONG_ANGLE_OUTPUT = (
    TMP
    / "retail-wrong-angle"
)


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.bbox import calculate_yolo_bbox
from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset
from bvt.retail.edge_cases import WRONG_ANGLE_NAMESPACE
from bvt.retail.edge_cases import iter_retail_products


def close(
    first,
    second,
    tolerance=1e-6,
):
    return abs(
        float(first)
        - float(second)
    ) <= tolerance


def bbox_tuple(
    value,
):
    return tuple(
        float(item)
        for item
        in value
    )


if BASELINE_OUTPUT.exists():
    shutil.rmtree(
        BASELINE_OUTPUT
    )

if WRONG_ANGLE_OUTPUT.exists():
    shutil.rmtree(
        WRONG_ANGLE_OUTPUT
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
    "Retail Wrong Angle Smoke"
)

project.project_id = (
    "retail-wrong-angle-smoke"
)

project.seed = 20261101
project.frame_count = 4

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False
project.artifact_engine_enabled = False

project.retail_edge_cases_enabled = True
project.retail_wrong_angle_enabled = False

project.retail_wrong_angle_min_degrees = 22.0
project.retail_wrong_angle_max_degrees = 22.0


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


original_rotations = {
    obj.bvt_object.instance_id: (
        tuple(
            float(value)
            for value
            in obj.rotation_euler
        )
    )
    for obj
    in products
}


# ---------------------------------------------------------
# Baseline dataset.
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


for frame in baseline_manifest[
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
            "events"
        ]
        == []
    )


# ---------------------------------------------------------
# Wrong Angle dataset.
# ---------------------------------------------------------

project.output_directory = str(
    WRONG_ANGLE_OUTPUT
)

project.retail_wrong_angle_enabled = True


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


# Generation must leave the source scene untouched.
for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    current = tuple(
        float(value)
        for value
        in obj.rotation_euler
    )

    assert (
        current
        == original_rotations[
            instance_id
        ]
    )


assert len(
    first_manifest[
        "frames"
    ]
) == 4


selected_instances = []


for baseline_frame, frame in zip(
    baseline_manifest[
        "frames"
    ],
    first_manifest[
        "frames"
    ],
):
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
    ) == 1

    event = events[0]

    assert (
        event[
            "edge_case"
        ]
        == "wrong_angle"
    )

    assert (
        event[
            "applied"
        ]
        is True
    )

    assert (
        event[
            "axis"
        ]
        == "Z"
    )

    instance_id = event[
        "instance_id"
    ]

    selected_instances.append(
        instance_id
    )

    assert (
        instance_id
        in product_by_instance
    )

    expected_selection = min(
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
        instance_id
        == (
            expected_selection
            .bvt_object
            .instance_id
        )
    )

    expected_selection_seed = (
        derive_subseed(
            frame[
                "frame_seed"
            ],
            (
                WRONG_ANGLE_NAMESPACE
                + "/target"
            ),
            instance_id,
        )
    )

    assert (
        event[
            "selection_seed"
        ]
        == expected_selection_seed
    )

    expected_event_seed = (
        derive_subseed(
            frame[
                "frame_seed"
            ],
            WRONG_ANGLE_NAMESPACE,
            instance_id,
        )
    )

    assert (
        event[
            "seed"
        ]
        == expected_event_seed
    )

    assert close(
        abs(
            event[
                "delta_degrees"
            ]
        ),
        22.0,
    )

    assert close(
        (
            event[
                "after"
            ][
                "rotation_z_degrees"
            ]
            - event[
                "before"
            ][
                "rotation_z_degrees"
            ]
        ),
        event[
            "delta_degrees"
        ],
    )

    # -----------------------------------------------------
    # Annotation must describe the transformed geometry.
    # Reconstruct the final rotation and calculate bbox
    # independently from the manifest.
    # -----------------------------------------------------

    obj = product_by_instance[
        instance_id
    ]

    original_rotation = (
        obj.rotation_euler.copy()
    )

    try:
        obj.rotation_euler.z = (
            math.radians(
                event[
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

        annotation = next(
            item
            for item
            in frame[
                "objects"
            ]
            if (
                item[
                    "instance_id"
                ]
                == instance_id
            )
        )

        actual_bbox = (
            annotation[
                "bbox_yolo"
            ]
        )

        expected_bbox_values = (
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
            expected_bbox_values,
        ):
            assert close(
                actual,
                expected,
                tolerance=1e-7,
            )

    finally:
        obj.rotation_euler = (
            original_rotation
        )

        bpy.context.view_layer.update()

    # Baseline and transformed annotation must differ
    # for the selected object.
    baseline_annotation = next(
        item
        for item
        in baseline_frame[
            "objects"
        ]
        if (
            item[
                "instance_id"
            ]
            == instance_id
        )
    )

    transformed_annotation = next(
        item
        for item
        in frame[
            "objects"
        ]
        if (
            item[
                "instance_id"
            ]
            == instance_id
        )
    )

    assert (
        bbox_tuple(
            baseline_annotation[
                "bbox_yolo"
            ]
        )
        != bbox_tuple(
            transformed_annotation[
                "bbox_yolo"
            ]
        )
    )


# ---------------------------------------------------------
# Determinism: run the same generation again.
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


# Final generation must also restore the scene.
for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    current = tuple(
        float(value)
        for value
        in obj.rotation_euler
    )

    assert (
        current
        == original_rotations[
            instance_id
        ]
    )


print(
    "frames=4"
)

print(
    "products=18"
)

print(
    "events_per_frame=1"
)

print(
    "wrong_angle_degrees=22"
)

print(
    "selected_instances="
    + ",".join(
        selected_instances
    )
)

print(
    "deterministic_selection=True"
)

print(
    "deterministic_events=True"
)

print(
    "deterministic_annotations=True"
)

print(
    "bbox_from_final_transform=True"
)

print(
    "per_frame_reset=True"
)

print(
    "final_scene_restored=True"
)

print(
    "BVT_RETAIL_WRONG_ANGLE_SMOKE=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()

shutil.rmtree(
    BASELINE_OUTPUT
)

shutil.rmtree(
    WRONG_ANGLE_OUTPUT
)
