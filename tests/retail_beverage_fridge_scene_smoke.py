import hashlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.assets import ASSET_CATEGORY_PRODUCT
from bvt.assets import iter_registered_assets
from bvt.materials.service import MATERIAL_ROLE_GLASS
from bvt.materials.service import get_materials_by_role
from bvt.project.service import initialize_project
from bvt.render.service import generate_dataset


BLEND_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "beverage-fridge-v0.1.blend"
)

SKU_PACK_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)

SCENE_MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "manifests"
    / "beverage-fridge-v0.1.json"
)

TMP = (
    ROOT
    / ".tmp"
    / "retail-beverage-fridge-smoke"
)

TOLERANCE = 1e-6


def close(
    left,
    right,
):
    return abs(
        float(left)
        - float(right)
    ) <= TOLERANCE


assert BLEND_PATH.is_file()


sku_pack = json.loads(
    SKU_PACK_PATH.read_text(
        encoding="utf-8"
    )
)

scene_manifest = json.loads(
    SCENE_MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)


bvt.register()


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


scene = bpy.context.scene


assert (
    scene.name
    == "BVT_Beverage_Fridge_v01"
)

assert (
    scene[
        "bvt_retail_scene_id"
    ]
    == "beverage_fridge_v01"
)

assert scene.camera is not None

assert (
    scene.camera.name
    == "BVT_Retail_Camera"
)


# ---------------------------------------------------------
# GLASS role.
# ---------------------------------------------------------

glass_materials = (
    get_materials_by_role(
        scene,
        MATERIAL_ROLE_GLASS,
    )
)

glass_names = {
    material.name
    for material
    in glass_materials
}

assert (
    "BVT_Retail_Fridge_Glass"
    in glass_names
)


glass = bpy.data.objects.get(
    "BVT_Fridge_Glass_Door"
)

assert glass is not None

assert (
    glass[
        "bvt_component"
    ]
    == "glass_door"
)


# ---------------------------------------------------------
# Shelves.
# ---------------------------------------------------------

shelves = [
    obj
    for obj
    in scene.objects
    if obj.get(
        "bvt_component"
    ) == "shelf"
]

assert len(
    shelves
) == 3


shelf_ids = {
    obj[
        "bvt_shelf_id"
    ]
    for obj
    in shelves
}

assert shelf_ids == {
    "shelf_01",
    "shelf_02",
    "shelf_03",
}


# ---------------------------------------------------------
# Product instances.
# ---------------------------------------------------------

products = [
    obj
    for obj
    in scene.objects
    if obj.get(
        "bvt_sku_id"
    )
]

assert len(
    products
) == 18


products_by_slot = {
    obj[
        "bvt_slot_id"
    ]: obj
    for obj
    in products
}

assert len(
    products_by_slot
) == 18


slots = {
    slot[
        "slot_id"
    ]: slot
    for slot
    in scene_manifest[
        "slots"
    ]
}


skus = {
    sku[
        "sku_id"
    ]: sku
    for sku
    in sku_pack[
        "skus"
    ]
}


expected_instances = {
    item[
        "slot_id"
    ]: item
    for item
    in scene_manifest[
        "product_instances"
    ]
}


seen_classes = set()
seen_skus = set()
seen_instance_ids = set()


for slot_id, expected in (
    expected_instances.items()
):
    obj = products_by_slot[
        slot_id
    ]

    sku_id = expected[
        "sku_id"
    ]

    sku = skus[
        sku_id
    ]

    slot = slots[
        slot_id
    ]

    settings = obj.bvt_object

    assert settings.registered is True
    assert settings.annotation_enabled is True

    assert (
        settings.class_id
        == sku[
            "class_id"
        ]
    )

    assert (
        settings.class_name
        == sku[
            "class_name"
        ]
    )

    assert (
        settings.instance_id
        == expected[
            "instance_id"
        ]
    )

    assert (
        obj[
            "bvt_shelf_id"
        ]
        == expected[
            "shelf_id"
        ]
    )

    assert (
        obj[
            "bvt_sku_id"
        ]
        == sku_id
    )

    assert close(
        obj.location.x,
        slot[
            "position"
        ][0],
    )

    assert close(
        obj.location.y,
        slot[
            "position"
        ][1],
    )

    assert close(
        obj.location.z,
        slot[
            "position"
        ][2],
    )

    dimensions = sku[
        "dimensions"
    ]

    assert close(
        obj.dimensions.x,
        dimensions[
            "width_m"
        ],
    )

    assert close(
        obj.dimensions.y,
        dimensions[
            "depth_m"
        ],
    )

    assert close(
        obj.dimensions.z,
        dimensions[
            "height_m"
        ],
    )

    seen_classes.add(
        settings.class_id
    )

    seen_skus.add(
        sku_id
    )

    assert (
        settings.instance_id
        not in seen_instance_ids
    )

    seen_instance_ids.add(
        settings.instance_id
    )


assert seen_classes == set(
    range(
        8
    )
)

assert seen_skus == set(
    skus
)


# ---------------------------------------------------------
# Asset registration contract.
# ---------------------------------------------------------

registered_assets = (
    iter_registered_assets(
        scene
    )
)

assert len(
    registered_assets
) == 18


registered_asset_ids = {
    obj.bvt_asset.asset_id
    for obj
    in registered_assets
}


assert (
    registered_asset_ids
    == set(
        skus
    )
)


for obj in products:
    assert (
        obj.bvt_asset.registered
        is True
    )

    assert (
        obj.bvt_asset.category
        == ASSET_CATEGORY_PRODUCT
    )

    assert (
        obj.bvt_asset.asset_id
        == obj[
            "bvt_sku_id"
        ]
    )

    assert (
        obj.bvt_asset.version
        == sku_pack[
            "version"
        ]
    )


# ---------------------------------------------------------
# Synthetic texture + UV contract.
# ---------------------------------------------------------

texture_paths = {
    sku[
        "visual"
    ][
        "texture"
    ]
    for sku
    in skus.values()
}


assert len(
    texture_paths
) == 8


texture_hashes = set()


for relative in texture_paths:
    assert relative is not None

    texture_path = (
        ROOT
        / relative
    )

    assert texture_path.is_file()

    texture_hashes.add(
        hashlib.sha256(
            texture_path.read_bytes()
        ).hexdigest()
    )


assert len(
    texture_hashes
) == 8


for obj in products:
    sku_id = obj[
        "bvt_sku_id"
    ]

    sku = skus[
        sku_id
    ]

    assert (
        obj[
            "bvt_uv_map"
        ]
        == "BVT_UV"
    )

    assert (
        obj[
            "bvt_uv_contract"
        ]
        == "bvt-uv-1"
    )

    uv_layer = (
        obj.data.uv_layers.get(
            "BVT_UV"
        )
    )

    assert uv_layer is not None

    assert len(
        uv_layer.data
    ) == len(
        obj.data.loops
    )

    assert len(
        obj.data.materials
    ) == 1

    material = (
        obj.data.materials[0]
    )

    expected_texture = (
        sku[
            "visual"
        ][
            "texture"
        ]
    )

    assert (
        material[
            "bvt_texture_path"
        ]
        == expected_texture
    )

    image_nodes = [
        node
        for node
        in material.node_tree.nodes
        if node.type
        == "TEX_IMAGE"
    ]

    assert len(
        image_nodes
    ) == 1

    assert (
        image_nodes[0].image
        is not None
    )

    uv_nodes = [
        node
        for node
        in material.node_tree.nodes
        if node.type
        == "UVMAP"
    ]

    assert len(
        uv_nodes
    ) == 1

    assert (
        uv_nodes[0].uv_map
        == "BVT_UV"
    )


# ---------------------------------------------------------
# Infrastructure must not be product annotations.
# ---------------------------------------------------------

for name in (
    "BVT_Fridge_Left",
    "BVT_Fridge_Right",
    "BVT_Fridge_Bottom",
    "BVT_Fridge_Top",
    "BVT_Fridge_Back",
    "BVT_Fridge_Glass_Door",
):
    obj = bpy.data.objects.get(
        name
    )

    assert obj is not None

    assert (
        obj.bvt_object.registered
        is False
    )


# ---------------------------------------------------------
# Existing BVT dataset pipeline smoke.
# ---------------------------------------------------------

if TMP.exists():
    shutil.rmtree(
        TMP
    )

settings = scene.bvt_project

settings.project_name = (
    "BVT Retail Beverage Fridge Smoke"
)

settings.project_id = (
    "bvt-retail-beverage-fridge-smoke"
)

settings.output_directory = str(
    TMP
)

settings.seed = 12345
settings.frame_count = 1

settings.placement_randomization_enabled = False
settings.camera_randomization_enabled = False
settings.lighting_randomization_enabled = False

settings.artifact_engine_enabled = False


initialize_project(
    scene
)


result = generate_dataset(
    scene
)


assert (
    result[
        "validation_report"
    ][
        "status"
    ]
    == "PASS"
)

assert len(
    result[
        "image_paths"
    ]
) == 1

assert len(
    result[
        "label_paths"
    ]
) == 1


label_path = result[
    "label_paths"
][0]

label_lines = [
    line
    for line
    in label_path.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]


assert len(
    label_lines
) == 18


classes_in_label = {
    int(
        line.split()[0]
    )
    for line
    in label_lines
}

assert classes_in_label == set(
    range(
        8
    )
)


manifest = json.loads(
    result[
        "manifest_path"
    ].read_text(
        encoding="utf-8"
    )
)


assert len(
    manifest[
        "frames"
    ]
) == 1


print(
    "scene_id=beverage_fridge_v01"
)

print(
    "shelves=3"
)

print(
    "products=18"
)

print(
    "sku_classes=8"
)

print(
    "deterministic_slots=18"
)

print(
    "deterministic_instance_ids=18"
)

print(
    "registered_assets=18"
)

print(
    "unique_asset_ids=8"
)

print(
    "synthetic_textures=8"
)

print(
    "unique_texture_hashes=8"
)

print(
    "uv_products=18"
)

print(
    "uv_contract=bvt-uv-1"
)

print(
    "glass_role=GLASS"
)

print(
    "dataset_frames=1"
)

print(
    "yolo_labels=18"
)

print(
    "validation_status=PASS"
)

print(
    "BVT_BEVERAGE_FRIDGE_SCENE_SMOKE=OK"
)

print(
    "RESULT=PASS"
)
