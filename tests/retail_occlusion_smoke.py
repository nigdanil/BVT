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
    / "retail-occlusion-baseline"
)

OCCLUSION_OUTPUT = (
    TMP
    / "retail-occlusion"
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
from bvt.retail.edge_cases import OCCLUSION_NAMESPACE
from bvt.retail.edge_cases import iter_retail_products


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
    OCCLUSION_OUTPUT,
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
    "Retail Occlusion Smoke"
)

project.project_id = (
    "retail-occlusion-smoke"
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
project.retail_occlusion_enabled = False

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


assert occluders(
    scene
) == []


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
# Occlusion.
# ---------------------------------------------------------

project.output_directory = str(
    OCCLUSION_OUTPUT
)

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
) == 4


# Final lifecycle cleanup must remove the occluder.
assert occluders(
    scene
) == []


selected_instances = []
occluder_names = []


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
        == "occlusion"
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

    expected_target = min(
        products,
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
                OCCLUSION_NAMESPACE
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
            OCCLUSION_NAMESPACE,
            instance_id,
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
            "occluder_present"
        ]
        is False
    )

    assert (
        event[
            "after"
        ][
            "occluder_present"
        ]
        is True
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
            "annotation_enabled"
        ]
        is True
    )

    occluder = event[
        "occluder"
    ]

    occluder_names.append(
        occluder[
            "object_name"
        ]
    )

    assert (
        occluder[
            "annotation_target"
        ]
        is False
    )

    assert (
        occluder[
            "asset_registered"
        ]
        is False
    )

    dimensions = (
        occluder[
            "dimensions_m"
        ]
    )

    assert (
        float(
            dimensions[0]
        )
        > 0.0
    )

    assert (
        float(
            dimensions[1]
        )
        > 0.0
    )

    assert (
        float(
            dimensions[2]
        )
        > 0.0
    )

    # Occlusion keeps all 18 SKU annotations.
    assert len(
        baseline_frame[
            "objects"
        ]
    ) == 18

    assert len(
        frame[
            "objects"
        ]
    ) == 18

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

    assert (
        set(
            baseline_by_instance
        )
        == set(
            current_by_instance
        )
    )

    # v0.1 annotation policy is full-object bbox.
    # Synthetic occlusion changes pixels but not
    # product geometry.
    assert (
        current_by_instance[
            instance_id
        ][
            "bbox_yolo"
        ]
        == baseline_by_instance[
            instance_id
        ][
            "bbox_yolo"
        ]
    )

    # Occluder must never enter YOLO annotations.
    annotation_names = {
        item[
            "object_name"
        ]
        for item
        in frame[
            "objects"
        ]
    }

    assert (
        occluder[
            "object_name"
        ]
        not in annotation_names
    )


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
    ) == 18


assert len(
    first_manifest[
        "annotations"
    ][
        "classes"
    ]
) == 8


occluded_images = sorted(
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
    occluded_images
) == 4


# Occluder must produce a real RGB difference.
for baseline_path, occluded_path in zip(
    baseline_images,
    occluded_images,
):
    assert (
        decoded_png_hash(
            baseline_path
        )
        != decoded_png_hash(
            occluded_path
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


# Second generation must also leave no objects behind.
assert occluders(
    scene
) == []


print(
    "frames=4"
)

print(
    "products_per_frame=18"
)

print(
    "yolo_rows_per_frame=18"
)

print(
    "classes_preserved=8"
)

print(
    "selected_instances="
    + ",".join(
        selected_instances
    )
)

print(
    "occluders="
    + ",".join(
        occluder_names
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
    "occluder_not_annotated=True"
)

print(
    "full_object_bbox_preserved=True"
)

print(
    "rgb_changed=True"
)

print(
    "per_frame_occluder_cleanup=True"
)

print(
    "final_scene_restored=True"
)

print(
    "BVT_RETAIL_OCCLUSION_SMOKE=OK"
)

print(
    "RESULT=PASS"
)


bvt.unregister()


for directory in (
    BASELINE_OUTPUT,
    OCCLUSION_OUTPUT,
):
    if directory.exists():
        shutil.rmtree(
            directory
        )
