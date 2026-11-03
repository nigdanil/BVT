import json
from pathlib import Path

import bpy


ROOT = Path(
    __file__
).resolve().parents[1]


BLEND = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "r01-neutral-fridge-v0.1.blend"
)


MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "r01-neutral-fridge-v0.1.json"
)


CONTRACT = (
    ROOT
    / "docs"
    / "contracts"
    / "R01-Neutral-Scene-v0.1.md"
)


assert BLEND.is_file()
assert MANIFEST.is_file()
assert CONTRACT.is_file()


data = json.loads(
    MANIFEST.read_text(
        encoding="utf-8"
    )
)


assert (
    data[
        "schema_version"
    ]
    == "bvt-r01-neutral-scene-1"
)


assert (
    data[
        "scene_id"
    ]
    == "r01-neutral-fridge-v0.1"
)


assert (
    data[
        "glass_enabled"
    ]
    is False
)


assert (
    data[
        "front_direction"
    ]
    == "-Y"
)


assert len(
    data[
        "placements"
    ]
) == 8


assert len(
    data[
        "shelves"
    ]
) == 3


assert len(
    data[
        "lights"
    ]
) == 3


assert (
    data[
        "render"
    ][
        "engine"
    ]
    == "BLENDER_EEVEE"
)


assert (
    data[
        "render"
    ][
        "resolution_x"
    ]
    == 1200
)


assert (
    data[
        "render"
    ][
        "resolution_y"
    ]
    == 1600
)


assert abs(
    data[
        "render"
    ][
        "exposure"
    ]
    - (
        -0.7
    )
) < 1e-9


assert (
    data[
        "render"
    ][
        "lighting"
    ]
    == {
        "key_energy": 360.0,
        "fill_energy": 240.0,
        "top_energy": 170.0,
    }
)


expected_skus = {
    "bev_can_red_330",
    "bev_can_blue_330",
    "bev_bottle_green_500",
    "bev_bottle_amber_500",
    "bev_carton_orange_1000",
    "bev_carton_white_1000",
    "bev_box_purple_250",
    "bev_box_yellow_250",
}


assert {
    item[
        "sku_id"
    ]
    for item
    in data[
        "placements"
    ]
} == expected_skus


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND
    )
)


scene = bpy.context.scene


assert (
    scene[
        "bvt_scene_id"
    ]
    == "r01-neutral-fridge-v0.1"
)


assert (
    scene[
        "bvt_glass_enabled"
    ]
    is False
)


assert scene.camera is not None


assert (
    scene.camera.name
    == "R01_Neutral_Camera"
)


assert abs(
    scene.view_settings.exposure
    - (
        -0.7
    )
) < 1e-6


assert (
    bpy.data.lights[
        "R01_Key_Light"
    ].energy
    == 360.0
)


assert (
    bpy.data.lights[
        "R01_Fill_Light"
    ].energy
    == 240.0
)


assert (
    bpy.data.lights[
        "R01_Top_Light"
    ].energy
    == 170.0
)


shelves = [
    obj
    for obj
    in bpy.data.objects
    if obj.name.startswith(
        "R01_Shelf_"
    )
]


assert len(
    shelves
) == 3


sku_objects = [
    obj
    for obj
    in bpy.data.objects
    if obj.name.startswith(
        "SKU_bev_"
    )
]


labels = [
    obj
    for obj
    in bpy.data.objects
    if obj.name.startswith(
        "SKU_Label_"
    )
]


assert len(
    sku_objects
) == 8


assert len(
    labels
) == 8


assert all(
    label.parent is not None
    for label
    in labels
)


placement_by_sku = {
    item[
        "sku_id"
    ]: item
    for item
    in data[
        "placements"
    ]
}


for obj in sku_objects:
    sku_id = obj[
        "bvt_sku_id"
    ]


    expected = placement_by_sku[
        sku_id
    ]


    actual = [
        float(
            obj.location.x
        ),
        float(
            obj.location.y
        ),
        float(
            obj.location.z
        ),
    ]


    for actual_value, expected_value in zip(
        actual,
        expected[
            "location"
        ],
    ):
        assert abs(
            actual_value
            - expected_value
        ) < 1e-6


    assert (
        obj[
            "bvt_r01_shelf_id"
        ]
        == expected[
            "shelf_id"
        ]
    )


images = [
    image
    for image
    in bpy.data.images
    if image.name
    != "Render Result"
]


assert len(
    images
) == 8


for image in images:
    assert image.filepath.startswith(
        "//"
    ), (
        image.name,
        image.filepath,
    )


assert (
    bpy.data.objects.get(
        "R01_Cabinet_Left"
    )
    is not None
)


assert (
    bpy.data.objects.get(
        "R01_Cabinet_Right"
    )
    is not None
)


assert (
    bpy.data.objects.get(
        "R01_Cabinet_Back"
    )
    is not None
)


assert (
    bpy.data.objects.get(
        "R01_Cabinet_Top"
    )
    is not None
)


print(
    "scene_id=r01-neutral-fridge-v0.1"
)


print(
    "sku_objects=8"
)


print(
    "parented_labels=8"
)


print(
    "shelves=3"
)


print(
    "lights=3"
)


print(
    "glass_enabled=False"
)


print(
    "texture_paths_relative=True"
)


print(
    "BVT_R01_NEUTRAL_SCENE_SMOKE=OK"
)


print(
    "RESULT=PASS"
)
