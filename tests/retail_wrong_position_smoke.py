import json
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
    / "retail-wrong-position-baseline"
)

WRONG_POSITION_OUTPUT = (
    TMP
    / "retail-wrong-position"
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


def bbox_tuple(
    value,
):
    return tuple(
        float(item)
        for item
        in value
    )


for directory in (
    BASELINE_OUTPUT,
    WRONG_POSITION_OUTPUT,
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
    "Retail Wrong Position Smoke"
)

project.project_id = (
    "retail-wrong-position-smoke"
)

project.seed = 20261101
project.frame_count = 4

project.placement_randomization_enabled = False
project.camera_randomization_enabled = False
project.lighting_randomization_enabled = False
project.artifact_engine_enabled = False

project.retail_edge_cases_enabled = True
project.retail_wrong_angle_enabled = False
project.retail_wrong_position_enabled = False

project.retail_wrong_position_offset_x = 0.035
project.retail_wrong_position_offset_y = 0.020


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


original_locations = {
    obj.bvt_object.instance_id: (
        tuple3(
            obj.location
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
# Wrong Position dataset.
# ---------------------------------------------------------

project.output_directory = str(
    WRONG_POSITION_OUTPUT
)

project.retail_wrong_position_enabled = True


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


# Generation must restore all product locations.
for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    assert (
        tuple3(
            obj.location
        )
        == original_locations[
            instance_id
        ]
    )


assert len(
    first_manifest[
        "frames"
    ]
) == 4


selected_instances = []
offsets = []


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
        == "wrong_position"
    )

    assert (
        event[
            "applied"
        ]
        is True
    )

    instance_id = (
        event[
            "instance_id"
        ]
    )

    selected_instances.append(
        instance_id
    )

    assert (
        instance_id
        in product_by_instance
    )

    expected_target = min(
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
        instance_id
        == (
            expected_target
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
                WRONG_POSITION_NAMESPACE
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
            WRONG_POSITION_NAMESPACE,
            instance_id,
        )
    )

    assert (
        event[
            "seed"
        ]
        == expected_event_seed
    )

    offset = event[
        "offset_m"
    ]

    offsets.append(
        tuple3(
            offset
        )
    )

    assert (
        -0.035
        <= float(
            offset[0]
        )
        <= 0.035
    )

    assert (
        -0.020
        <= float(
            offset[1]
        )
        <= 0.020
    )

    assert close(
        offset[2],
        0.0,
    )

    before = event[
        "before"
    ][
        "location_m"
    ]

    after = event[
        "after"
    ][
        "location_m"
    ]

    assert close(
        (
            after[0]
            - before[0]
        ),
        offset[0],
    )

    assert close(
        (
            after[1]
            - before[1]
        ),
        offset[1],
    )

    assert close(
        after[2],
        before[2],
    )

    assert (
        event[
            "slot_id"
        ]
        != ""
    )

    assert (
        event[
            "shelf_id"
        ]
        != ""
    )

    # -----------------------------------------------------
    # Annotation must match final translated geometry.
    # -----------------------------------------------------

    obj = product_by_instance[
        instance_id
    ]

    original_location = (
        obj.location.copy()
    )

    try:
        obj.location.x = (
            float(
                after[0]
            )
        )

        obj.location.y = (
            float(
                after[1]
            )
        )

        obj.location.z = (
            float(
                after[2]
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
            annotation[
                "bbox_yolo"
            ],
            expected_values,
        ):
            assert close(
                actual,
                expected,
            )

    finally:
        obj.location = (
            original_location
        )

        bpy.context.view_layer.update()

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


assert len(
    set(
        offsets
    )
) == 4


# ---------------------------------------------------------
# Determinism.
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


first_events = [
    frame[
        "retail_edge_cases"
    ]
    for frame
    in first_manifest[
        "frames"
    ]
]

second_events = [
    frame[
        "retail_edge_cases"
    ]
    for frame
    in second_manifest[
        "frames"
    ]
]


assert (
    first_events
    == second_events
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


for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    assert (
        tuple3(
            obj.location
        )
        == original_locations[
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
    "selected_instances="
    + ",".join(
        selected_instances
    )
)

print(
    "unique_offsets="
    + str(
        len(
            set(
                offsets
            )
        )
    )
)

print(
    "z_preserved=True"
)

print(
    "slot_identity_preserved=True"
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
    "BVT_RETAIL_WRONG_POSITION_SMOKE=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


for directory in (
    BASELINE_OUTPUT,
    WRONG_POSITION_OUTPUT,
):
    if directory.exists():
        shutil.rmtree(
            directory
        )
