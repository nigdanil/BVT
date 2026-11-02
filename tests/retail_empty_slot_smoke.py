import hashlib
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
    / "retail-empty-slot-baseline"
)

EMPTY_OUTPUT = (
    TMP
    / "retail-empty-slot"
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

from bvt.core.seeding import derive_subseed
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset
from bvt.retail.edge_cases import EMPTY_SLOT_NAMESPACE
from bvt.retail.edge_cases import iter_retail_products


for directory in (
    BASELINE_OUTPUT,
    EMPTY_OUTPUT,
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
    "Retail Empty Slot Smoke"
)

project.project_id = (
    "retail-empty-slot-smoke"
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
project.retail_empty_slot_enabled = False


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


original_state = {
    obj.bvt_object.instance_id: {
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
# Baseline.
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
) == 4


for frame in baseline_manifest[
    "frames"
]:
    assert len(
        frame[
            "objects"
        ]
    ) == 18

    assert (
        frame[
            "retail_edge_cases"
        ][
            "events"
        ]
        == []
    )


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


assert len(
    baseline_images
) == 4


# ---------------------------------------------------------
# Empty Slot.
# ---------------------------------------------------------

project.output_directory = str(
    EMPTY_OUTPUT
)

project.retail_empty_slot_enabled = True


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
) == 4


# Source scene must be restored after generation.
for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    assert (
        bool(
            obj.hide_render
        )
        == original_state[
            instance_id
        ][
            "hide_render"
        ]
    )

    assert (
        bool(
            obj.bvt_object.annotation_enabled
        )
        == original_state[
            instance_id
        ][
            "annotation_enabled"
        ]
    )


selected_slots = []
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
        == "empty_slot"
    )

    assert (
        event[
            "applied"
        ]
        is True
    )

    slot_id = event[
        "slot_id"
    ]

    instance_id = event[
        "instance_id"
    ]

    selected_slots.append(
        slot_id
    )

    selected_instances.append(
        instance_id
    )

    assert (
        instance_id
        in product_by_instance
    )

    assert (
        event[
            "shelf_id"
        ]
        != ""
    )

    assert (
        event[
            "sku_id"
        ]
        != ""
    )

    expected_target = min(
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
        slot_id
        == str(
            expected_target.get(
                "bvt_slot_id",
                "",
            )
        )
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
                EMPTY_SLOT_NAMESPACE
                + "/target"
            ),
            slot_id,
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
            EMPTY_SLOT_NAMESPACE,
            slot_id,
        )
    )

    assert (
        event[
            "seed"
        ]
        == expected_event_seed
    )

    assert (
        event[
            "before"
        ][
            "hide_render"
        ]
        is False
    )

    assert (
        event[
            "before"
        ][
            "annotation_enabled"
        ]
        is True
    )

    assert (
        event[
            "after"
        ][
            "hide_render"
        ]
        is True
    )

    assert (
        event[
            "after"
        ][
            "annotation_enabled"
        ]
        is False
    )

    # Exactly one product disappears from YOLO.
    assert len(
        baseline_frame[
            "objects"
        ]
    ) == 18

    assert len(
        frame[
            "objects"
        ]
    ) == 17

    frame_instance_ids = {
        item[
            "instance_id"
        ]
        for item
        in frame[
            "objects"
        ]
    }

    assert (
        instance_id
        not in frame_instance_ids
    )

    baseline_instance_ids = {
        item[
            "instance_id"
        ]
        for item
        in baseline_frame[
            "objects"
        ]
    }

    assert (
        instance_id
        in baseline_instance_ids
    )

    # No other object may change annotation geometry.
    baseline_by_instance = {
        item[
            "instance_id"
        ]: item
        for item
        in baseline_frame[
            "objects"
        ]
    }

    current_by_instance = {
        item[
            "instance_id"
        ]: item
        for item
        in frame[
            "objects"
        ]
    }

    for other_instance_id in (
        frame_instance_ids
    ):
        assert (
            current_by_instance[
                other_instance_id
            ][
                "bbox_yolo"
            ]
            == baseline_by_instance[
                other_instance_id
            ][
                "bbox_yolo"
            ]
        )


# Every generated label file must contain 17 rows.
label_paths = sorted(
    first_result[
        "label_paths"
    ]
)


assert len(
    label_paths
) == 4


for path in label_paths:
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


# All 8 classes remain represented because each synthetic
# SKU has at least two physical instances in the fridge.
assert len(
    first_manifest[
        "annotations"
    ][
        "classes"
    ]
) == 8


empty_images = sorted(
    (
        first_result[
            "dataset_directory"
        ]
        / "images"
    ).glob(
        "*.png"
    )
)


assert len(
    empty_images
) == 4


# Empty Slot must have a visible RGB effect.
for baseline_path, empty_path in zip(
    baseline_images,
    empty_images,
):
    assert (
        decoded_png_hash(
            baseline_path
        )
        != decoded_png_hash(
            empty_path
        )
    )


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


for obj in products:
    instance_id = (
        obj.bvt_object.instance_id
    )

    assert (
        bool(
            obj.hide_render
        )
        == original_state[
            instance_id
        ][
            "hide_render"
        ]
    )

    assert (
        bool(
            obj.bvt_object.annotation_enabled
        )
        == original_state[
            instance_id
        ][
            "annotation_enabled"
        ]
    )


print(
    "frames=4"
)

print(
    "baseline_products_per_frame=18"
)

print(
    "empty_slot_products_per_frame=17"
)

print(
    "yolo_rows_per_frame=17"
)

print(
    "classes_preserved=8"
)

print(
    "selected_slots="
    + ",".join(
        selected_slots
    )
)

print(
    "selected_instances="
    + ",".join(
        selected_instances
    )
)

print(
    "deterministic_slot_selection=True"
)

print(
    "deterministic_events=True"
)

print(
    "deterministic_annotations=True"
)

print(
    "hidden_product_not_annotated=True"
)

print(
    "other_bboxes_unchanged=True"
)

print(
    "rgb_changed=True"
)

print(
    "per_frame_reset=True"
)

print(
    "final_scene_restored=True"
)

print(
    "BVT_RETAIL_EMPTY_SLOT_SMOKE=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


for directory in (
    BASELINE_OUTPUT,
    EMPTY_OUTPUT,
):
    if directory.exists():
        shutil.rmtree(
            directory
        )
