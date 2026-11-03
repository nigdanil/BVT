import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path.cwd()


SOURCE_BLEND = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.blend"
)


SOURCE_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.json"
)


OUTPUT_BLEND = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "r01-neutral-fridge-v0.1.blend"
)


OUTPUT_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "r01-neutral-fridge-v0.1.json"
)


PREVIEW_PATH = (
    ROOT
    / ".tmp"
    / "r01-neutral-fridge-v0.1-preview.png"
)


SCENE_ID = (
    "r01-neutral-fridge-v0.1"
)


SCENE_COLLECTION = (
    "BVT_R01_Neutral_Fridge_v0_1"
)


SOURCE_PREVIEW_COLLECTION = (
    "BVT_SKU_Proxy_Preview_v0_1"
)


CABINET = {
    "width": 0.92,
    "height": 1.08,
    "depth": 0.36,
}


SHELF_TOPS = {
    "shelf_01": 0.12,
    "shelf_02": 0.46,
    "shelf_03": 0.80,
}


PLACEMENTS = {
    "bev_carton_orange_1000": {
        "shelf_id": "shelf_01",
        "x": -0.30,
        "y": -0.035,
    },

    "bev_carton_white_1000": {
        "shelf_id": "shelf_01",
        "x": -0.10,
        "y": -0.035,
    },

    "bev_box_purple_250": {
        "shelf_id": "shelf_01",
        "x": 0.12,
        "y": -0.035,
    },

    "bev_box_yellow_250": {
        "shelf_id": "shelf_01",
        "x": 0.30,
        "y": -0.035,
    },

    "bev_bottle_green_500": {
        "shelf_id": "shelf_02",
        "x": -0.18,
        "y": -0.035,
    },

    "bev_bottle_amber_500": {
        "shelf_id": "shelf_02",
        "x": 0.18,
        "y": -0.035,
    },

    "bev_can_red_330": {
        "shelf_id": "shelf_03",
        "x": -0.16,
        "y": -0.035,
    },

    "bev_can_blue_330": {
        "shelf_id": "shelf_03",
        "x": 0.16,
        "y": -0.035,
    },
}


def create_material(
    name,
    color,
    roughness=0.45,
):
    material = bpy.data.materials.new(
        name
    )


    material.diffuse_color = color


    material.use_nodes = True


    bsdf = (
        material
        .node_tree
        .nodes
        .get(
            "Principled BSDF"
        )
    )


    if bsdf is not None:
        bsdf.inputs[
            "Base Color"
        ].default_value = color


        bsdf.inputs[
            "Roughness"
        ].default_value = roughness


    return material


def create_box(
    name,
    size,
    location,
    collection,
    material=None,
):
    width, depth, height = size


    x = (
        width
        / 2.0
    )

    y = (
        depth
        / 2.0
    )

    z = (
        height
        / 2.0
    )


    vertices = [
        (
            -x,
            -y,
            -z,
        ),
        (
            x,
            -y,
            -z,
        ),
        (
            x,
            y,
            -z,
        ),
        (
            -x,
            y,
            -z,
        ),
        (
            -x,
            -y,
            z,
        ),
        (
            x,
            -y,
            z,
        ),
        (
            x,
            y,
            z,
        ),
        (
            -x,
            y,
            z,
        ),
    ]


    faces = [
        (
            0,
            3,
            2,
            1,
        ),
        (
            0,
            1,
            5,
            4,
        ),
        (
            1,
            2,
            6,
            5,
        ),
        (
            2,
            3,
            7,
            6,
        ),
        (
            3,
            0,
            4,
            7,
        ),
        (
            4,
            5,
            6,
            7,
        ),
    ]


    mesh = bpy.data.meshes.new(
        name
        + "_Mesh"
    )


    mesh.from_pydata(
        vertices,
        [],
        faces,
    )


    mesh.validate()
    mesh.update()


    obj = bpy.data.objects.new(
        name,
        mesh,
    )


    collection.objects.link(
        obj
    )


    obj.location = location


    if material is not None:
        obj.data.materials.append(
            material
        )


    return obj


def point_at(
    obj,
    target,
):
    direction = (
        Vector(
            target
        )
        - obj.location
    )


    obj.rotation_euler = (
        direction
        .to_track_quat(
            "-Z",
            "Y",
        )
        .to_euler()
    )


def remove_source_preview():
    collection = (
        bpy.data.collections.get(
            SOURCE_PREVIEW_COLLECTION
        )
    )


    if collection is None:
        return


    for obj in list(
        collection.objects
    ):
        bpy.data.objects.remove(
            obj,
            do_unlink=True,
        )


    bpy.data.collections.remove(
        collection
    )


def create_cabinet(
    collection,
):
    cabinet_material = create_material(
        "MAT_R01_Cabinet",
        (
            0.075,
            0.085,
            0.10,
            1.0,
        ),
        roughness=0.36,
    )


    shelf_material = create_material(
        "MAT_R01_Shelf",
        (
            0.34,
            0.37,
            0.41,
            1.0,
        ),
        roughness=0.38,
    )


    interior_material = create_material(
        "MAT_R01_Interior",
        (
            0.11,
            0.13,
            0.16,
            1.0,
        ),
        roughness=0.58,
    )


    floor_material = create_material(
        "MAT_R01_Floor",
        (
            0.14,
            0.15,
            0.17,
            1.0,
        ),
        roughness=0.65,
    )


    width = CABINET[
        "width"
    ]

    height = CABINET[
        "height"
    ]

    depth = CABINET[
        "depth"
    ]


    wall = 0.032
    back = 0.020
    shelf_thickness = 0.018


    create_box(
        "R01_Cabinet_Left",
        (
            wall,
            depth,
            height,
        ),
        (
            -(
                width
                / 2.0
                - wall
                / 2.0
            ),
            0.0,
            height / 2.0,
        ),
        collection,
        cabinet_material,
    )


    create_box(
        "R01_Cabinet_Right",
        (
            wall,
            depth,
            height,
        ),
        (
            (
                width
                / 2.0
                - wall
                / 2.0
            ),
            0.0,
            height / 2.0,
        ),
        collection,
        cabinet_material,
    )


    create_box(
        "R01_Cabinet_Top",
        (
            width,
            depth,
            wall,
        ),
        (
            0.0,
            0.0,
            (
                height
                - wall
                / 2.0
            ),
        ),
        collection,
        cabinet_material,
    )


    create_box(
        "R01_Cabinet_Back",
        (
            (
                width
                - 2.0
                * wall
            ),
            back,
            (
                height
                - wall
            ),
        ),
        (
            0.0,
            (
                depth
                / 2.0
                - back
                / 2.0
            ),
            (
                height
                / 2.0
                - wall
                / 2.0
            ),
        ),
        collection,
        interior_material,
    )


    # Bottom plinth.
    create_box(
        "R01_Cabinet_Base",
        (
            width,
            depth,
            0.07,
        ),
        (
            0.0,
            0.0,
            0.035,
        ),
        collection,
        cabinet_material,
    )


    shelf_objects = []


    for index, (
        shelf_id,
        top_z,
    ) in enumerate(
        SHELF_TOPS.items(),
        start=1,
    ):
        shelf = create_box(
            (
                "R01_Shelf_"
                + f"{index:02d}"
            ),
            (
                (
                    width
                    - 2.0
                    * wall
                ),
                (
                    depth
                    - 0.055
                ),
                shelf_thickness,
            ),
            (
                0.0,
                -0.010,
                (
                    top_z
                    - shelf_thickness
                    / 2.0
                ),
            ),
            collection,
            shelf_material,
        )


        shelf[
            "bvt_shelf_id"
        ] = shelf_id


        shelf[
            "bvt_top_z"
        ] = top_z


        shelf_objects.append(
            shelf
        )


    # Neutral ground outside the cabinet for shadows.
    create_box(
        "R01_Ground",
        (
            2.40,
            1.60,
            0.020,
        ),
        (
            0.0,
            0.10,
            -0.010,
        ),
        collection,
        floor_material,
    )


    return shelf_objects


def place_products(
    source_manifest,
):
    source_by_sku = {
        item[
            "sku_id"
        ]: item
        for item
        in source_manifest[
            "records"
        ]
    }


    result = []


    assert set(
        source_by_sku
    ) == set(
        PLACEMENTS
    )


    for sku_id, placement in (
        PLACEMENTS.items()
    ):
        source = source_by_sku[
            sku_id
        ]


        obj = bpy.data.objects.get(
            source[
                "object_name"
            ]
        )


        assert obj is not None, sku_id


        shelf_id = placement[
            "shelf_id"
        ]


        top_z = SHELF_TOPS[
            shelf_id
        ]


        obj.location = (
            placement[
                "x"
            ],
            placement[
                "y"
            ],
            top_z,
        )


        obj.rotation_euler = (
            0.0,
            0.0,
            0.0,
        )


        obj[
            "bvt_r01_scene"
        ] = SCENE_ID


        obj[
            "bvt_r01_shelf_id"
        ] = shelf_id


        label = bpy.data.objects.get(
            source[
                "label_object_name"
            ]
        )


        assert label is not None


        assert label.parent is obj


        result.append(
            {
                "class_id": (
                    source[
                        "class_id"
                    ]
                ),
                "sku_id": sku_id,
                "object_name": (
                    obj.name
                ),
                "label_object_name": (
                    label.name
                ),
                "shelf_id": shelf_id,
                "location": [
                    float(
                        obj.location.x
                    ),
                    float(
                        obj.location.y
                    ),
                    float(
                        obj.location.z
                    ),
                ],
                "front_direction": "-Y",
            }
        )


    return result


def create_camera(
    collection,
):
    camera_data = bpy.data.cameras.new(
        "R01_Neutral_Camera"
    )


    camera = bpy.data.objects.new(
        "R01_Neutral_Camera",
        camera_data,
    )


    collection.objects.link(
        camera
    )


    camera.location = (
        0.0,
        -2.05,
        0.58,
    )


    camera_data.lens = 52.0


    camera_data.sensor_width = 36.0


    point_at(
        camera,
        (
            0.0,
            0.01,
            0.56,
        ),
    )


    bpy.context.scene.camera = (
        camera
    )


    return camera


def create_light(
    name,
    location,
    energy,
    size,
    target,
    collection,
):
    data = bpy.data.lights.new(
        name,
        type="AREA",
    )


    data.energy = energy
    data.shape = "DISK"
    data.size = size


    light = bpy.data.objects.new(
        name,
        data,
    )


    collection.objects.link(
        light
    )


    light.location = location


    point_at(
        light,
        target,
    )


    return light


def create_lighting(
    collection,
):
    lights = []


    lights.append(
        create_light(
            "R01_Key_Light",
            (
                -0.55,
                -0.85,
                1.42,
            ),
            360.0,
            1.05,
            (
                0.0,
                0.02,
                0.56,
            ),
            collection,
        )
    )


    lights.append(
        create_light(
            "R01_Fill_Light",
            (
                0.68,
                -0.58,
                1.05,
            ),
            240.0,
            0.90,
            (
                0.0,
                0.02,
                0.50,
            ),
            collection,
        )
    )


    lights.append(
        create_light(
            "R01_Top_Light",
            (
                0.0,
                0.02,
                1.28,
            ),
            170.0,
            0.72,
            (
                0.0,
                0.00,
                0.48,
            ),
            collection,
        )
    )


    return lights


def main():
    assert SOURCE_BLEND.is_file()
    assert SOURCE_MANIFEST.is_file()


    source_manifest = json.loads(
        SOURCE_MANIFEST.read_text(
            encoding="utf-8"
        )
    )


    bpy.ops.wm.open_mainfile(
        filepath=str(
            SOURCE_BLEND
        )
    )


    scene = bpy.context.scene


    remove_source_preview()


    collection = bpy.data.collections.new(
        SCENE_COLLECTION
    )


    scene.collection.children.link(
        collection
    )


    shelf_objects = create_cabinet(
        collection
    )


    placements = place_products(
        source_manifest
    )


    camera = create_camera(
        collection
    )


    lights = create_lighting(
        collection
    )


    if scene.world is None:
        scene.world = (
            bpy.data.worlds.new(
                "R01_Neutral_World"
            )
        )


    scene.world.color = (
        0.025,
        0.028,
        0.034,
    )


    scene[
        "bvt_scene_id"
    ] = SCENE_ID


    scene[
        "bvt_scene_role"
    ] = (
        "r01-neutral-sim-to-real-reference"
    )


    scene[
        "bvt_glass_enabled"
    ] = False


    scene[
        "bvt_source_proxy_pack"
    ] = (
        "sku-proxy-pack-v0.1"
    )


    scene.render.engine = (
        "BLENDER_EEVEE"
    )


    scene.view_settings.exposure = -0.7


    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100


    scene.render.image_settings.file_format = (
        "PNG"
    )


    PREVIEW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    scene.render.filepath = str(
        PREVIEW_PATH
    )


    manifest = {
        "schema_version": (
            "bvt-r01-neutral-scene-1"
        ),
        "scene_id": SCENE_ID,
        "version": "0.1.0",
        "role": (
            "r01-neutral-sim-to-real-reference"
        ),
        "source_proxy_pack": (
            "examples/retail_demo/"
            "assets/sku-proxy-pack-v0.1.blend"
        ),
        "source_proxy_manifest": (
            "examples/retail_demo/"
            "assets/sku-proxy-pack-v0.1.json"
        ),
        "front_direction": "-Y",
        "glass_enabled": False,
        "cabinet": CABINET,
        "shelf_top_heights_m": (
            SHELF_TOPS
        ),
        "camera": {
            "name": camera.name,
            "lens_mm": (
                camera.data.lens
            ),
            "location": [
                float(
                    value
                )
                for value
                in camera.location
            ],
        },
        "lights": [
            light.name
            for light
            in lights
        ],
        "render": {
            "engine": "BLENDER_EEVEE",
            "resolution_x": 1200,
            "resolution_y": 1600,
            "exposure": -0.7,
            "lighting": {
                "key_energy": 360.0,
                "fill_energy": 240.0,
                "top_energy": 170.0,
            },
        },
        "shelves": [
            {
                "name": shelf.name,
                "shelf_id": (
                    shelf[
                        "bvt_shelf_id"
                    ]
                ),
                "top_z": (
                    shelf[
                        "bvt_top_z"
                    ]
                ),
            }
            for shelf
            in shelf_objects
        ],
        "placements": placements,
        "preview": (
            ".tmp/"
            "r01-neutral-fridge-v0.1-preview.png"
        ),
    }


    OUTPUT_MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    OUTPUT_MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


    # Save first so Blender has a base location for relative paths.
    bpy.ops.wm.save_as_mainfile(
        filepath=str(
            OUTPUT_BLEND
        )
    )


    bpy.ops.file.make_paths_relative()


    bpy.ops.wm.save_as_mainfile(
        filepath=str(
            OUTPUT_BLEND
        )
    )


    bpy.ops.render.render(
        write_still=True
    )


    print(
        "scene_id="
        + SCENE_ID
    )


    print(
        "sku_objects="
        + str(
            len(
                placements
            )
        )
    )


    print(
        "shelves="
        + str(
            len(
                shelf_objects
            )
        )
    )


    print(
        "lights="
        + str(
            len(
                lights
            )
        )
    )


    print(
        "glass_enabled=False"
    )


    print(
        "preview="
        + str(
            PREVIEW_PATH
        )
    )


    print(
        "BVT_R01_NEUTRAL_SCENE_BUILD=OK"
    )


if __name__ == "__main__":
    main()
