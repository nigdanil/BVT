import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path.cwd()
SOURCE = ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE),
)


import bvt

from bvt.annotation.service import register_object
from bvt.assets import ASSET_CATEGORY_PRODUCT
from bvt.assets import register_asset
from bvt.materials.service import MATERIAL_ROLE_GENERIC
from bvt.materials.service import MATERIAL_ROLE_GLASS
from bvt.materials.service import set_material_role


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

GEOMETRY_MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.json"
)

GEOMETRY_BLEND_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.blend"
)

OUTPUT_BLEND = (
    ROOT
    / "examples"
    / "retail_demo"
    / "scenes"
    / "beverage-fridge-v0.1.blend"
)


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def clear_scene():
    bpy.ops.object.select_all(
        action="SELECT"
    )

    bpy.ops.object.delete(
        use_global=False
    )

    for collection in list(
        bpy.data.collections
    ):
        bpy.data.collections.remove(
            collection
        )


def create_collection(
    name,
):
    collection = bpy.data.collections.new(
        name
    )

    bpy.context.scene.collection.children.link(
        collection
    )

    return collection


def create_material(
    name,
    color,
    roughness,
    role,
):
    material = bpy.data.materials.new(
        name
    )

    material.use_nodes = True

    nodes = material.node_tree.nodes

    principled = next(
        node
        for node
        in nodes
        if node.type == "BSDF_PRINCIPLED"
    )

    base_color = principled.inputs.get(
        "Base Color"
    )

    if base_color is not None:
        base_color.default_value = tuple(
            color
        )

    roughness_input = (
        principled.inputs.get(
            "Roughness"
        )
    )

    if roughness_input is not None:
        roughness_input.default_value = float(
            roughness
        )

    set_material_role(
        material,
        role,
    )

    return material


def create_glass_material():
    material = create_material(
        "BVT_Retail_Fridge_Glass",
        (
            0.92,
            0.97,
            1.0,
            1.0,
        ),
        0.08,
        MATERIAL_ROLE_GLASS,
    )

    principled = next(
        node
        for node
        in material.node_tree.nodes
        if node.type == "BSDF_PRINCIPLED"
    )

    transmission = (
        principled.inputs.get(
            "Transmission Weight"
        )
    )

    if transmission is not None:
        transmission.default_value = 0.92

    ior = principled.inputs.get(
        "IOR"
    )

    if ior is not None:
        ior.default_value = 1.45

    return material


def create_box(
    name,
    dimensions,
    location,
    collection,
    material=None,
):
    bpy.ops.mesh.primitive_cube_add(
        location=location
    )

    obj = bpy.context.object

    obj.name = name

    obj.dimensions = dimensions

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True,
    )

    # primitive_cube_add links into the default active
    # collection. Re-link into the requested collection.
    for current in list(
        obj.users_collection
    ):
        current.objects.unlink(
            obj
        )

    collection.objects.link(
        obj
    )

    if material is not None:
        obj.data.materials.append(
            material
        )

    return obj


def point_object(
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


def load_template_sources(
    geometry_manifest,
):
    templates = geometry_manifest[
        "templates"
    ]

    object_names = [
        item[
            "object_name"
        ]
        for item
        in templates
    ]

    with bpy.data.libraries.load(
        str(
            GEOMETRY_BLEND_PATH
        ),
        link=False,
    ) as (
        data_from,
        data_to,
    ):
        missing = (
            set(
                object_names
            )
            - set(
                data_from.objects
            )
        )

        assert not missing, missing

        data_to.objects = object_names

    loaded = {}

    for obj in data_to.objects:
        if obj is None:
            continue

        template_id = obj.get(
            "bvt_geometry_template"
        )

        assert template_id, (
            "Loaded geometry template has no "
            "bvt_geometry_template property: "
            + obj.name
        )

        assert (
            template_id
            not in loaded
        ), template_id

        loaded[
            template_id
        ] = obj

    expected = {
        item[
            "template_id"
        ]
        for item
        in templates
    }

    assert (
        set(
            loaded
        )
        == expected
    ), {
        "expected": sorted(
            expected
        ),
        "loaded": sorted(
            loaded
        ),
        "object_names": [
            obj.name
            for obj
            in data_to.objects
            if obj is not None
        ],
    }

    print(
        "loaded_templates="
        + ",".join(
            sorted(
                loaded
            )
        )
    )

    return loaded


def remove_template_sources(
    sources,
):
    for obj in sources.values():
        mesh = obj.data

        bpy.data.objects.remove(
            obj,
            do_unlink=True,
        )

        if (
            mesh is not None
            and mesh.users == 0
        ):
            bpy.data.meshes.remove(
                mesh
            )


def ensure_bvt_uv(
    obj,
):
    mesh = obj.data

    if mesh is None:
        raise ValueError(
            "Product mesh is missing"
        )

    uv_layer = mesh.uv_layers.get(
        "BVT_UV"
    )

    if uv_layer is None:
        uv_layer = (
            mesh.uv_layers.new(
                name="BVT_UV"
            )
        )

    vertices = [
        vertex.co
        for vertex
        in mesh.vertices
    ]

    min_x = min(
        vertex.x
        for vertex
        in vertices
    )

    max_x = max(
        vertex.x
        for vertex
        in vertices
    )

    min_y = min(
        vertex.y
        for vertex
        in vertices
    )

    max_y = max(
        vertex.y
        for vertex
        in vertices
    )

    min_z = min(
        vertex.z
        for vertex
        in vertices
    )

    max_z = max(
        vertex.z
        for vertex
        in vertices
    )

    size_x = max(
        max_x - min_x,
        1e-12,
    )

    size_y = max(
        max_y - min_y,
        1e-12,
    )

    size_z = max(
        max_z - min_z,
        1e-12,
    )

    for polygon in mesh.polygons:
        normal = polygon.normal

        abs_x = abs(
            normal.x
        )

        abs_y = abs(
            normal.y
        )

        abs_z = abs(
            normal.z
        )

        for loop_index in (
            polygon.loop_indices
        ):
            vertex_index = (
                mesh.loops[
                    loop_index
                ].vertex_index
            )

            co = mesh.vertices[
                vertex_index
            ].co

            if (
                abs_z
                >= abs_x
                and abs_z
                >= abs_y
            ):
                u = (
                    co.x - min_x
                ) / size_x

                v = (
                    co.y - min_y
                ) / size_y

            elif abs_x >= abs_y:
                u = (
                    co.y - min_y
                ) / size_y

                v = (
                    co.z - min_z
                ) / size_z

            else:
                u = (
                    co.x - min_x
                ) / size_x

                v = (
                    co.z - min_z
                ) / size_z

            uv_layer.data[
                loop_index
            ].uv = (
                u,
                v,
            )

    obj[
        "bvt_uv_map"
    ] = "BVT_UV"

    obj[
        "bvt_uv_contract"
    ] = "bvt-uv-1"

    return uv_layer


def create_product_material(
    sku,
):
    sku_id = sku[
        "sku_id"
    ]

    name = (
        "BVT_SKU_"
        + sku_id
    )

    material = create_material(
        name,
        sku[
            "visual"
        ][
            "base_color"
        ],
        0.34,
        MATERIAL_ROLE_GENERIC,
    )

    texture_relative = (
        sku[
            "visual"
        ][
            "texture"
        ]
    )

    assert texture_relative, sku_id

    texture_path = (
        ROOT
        / texture_relative
    )

    assert (
        texture_path.is_file()
    ), texture_path

    nodes = (
        material
        .node_tree
        .nodes
    )

    links = (
        material
        .node_tree
        .links
    )

    principled = next(
        node
        for node
        in nodes
        if node.type
        == "BSDF_PRINCIPLED"
    )

    image = bpy.data.images.load(
        str(
            texture_path
        ),
        check_existing=True,
    )

    image.name = (
        "BVT_Texture_"
        + sku_id
    )

    uv_node = nodes.new(
        "ShaderNodeUVMap"
    )

    uv_node.name = (
        "BVT SKU UV"
    )

    uv_node.label = (
        "BVT SKU UV"
    )

    uv_node.uv_map = (
        "BVT_UV"
    )

    texture_node = nodes.new(
        "ShaderNodeTexImage"
    )

    texture_node.name = (
        "BVT SKU Base Color"
    )

    texture_node.label = (
        "BVT SKU Base Color"
    )

    texture_node.image = image
    texture_node.interpolation = "Linear"
    texture_node.extension = "REPEAT"

    links.new(
        uv_node.outputs[
            "UV"
        ],
        texture_node.inputs[
            "Vector"
        ],
    )

    links.new(
        texture_node.outputs[
            "Color"
        ],
        principled.inputs[
            "Base Color"
        ],
    )

    material[
        "bvt_sku_id"
    ] = sku_id

    material[
        "bvt_texture_path"
    ] = texture_relative

    material[
        "bvt_texture_sha256"
    ] = hashlib.sha256(
        texture_path.read_bytes()
    ).hexdigest()

    return material


def build_products(
    scene_manifest,
    sku_pack,
    geometry_manifest,
    collection,
):
    skus = {
        sku[
            "sku_id"
        ]: sku
        for sku
        in sku_pack[
            "skus"
        ]
    }

    slots = {
        slot[
            "slot_id"
        ]: slot
        for slot
        in scene_manifest[
            "slots"
        ]
    }

    templates = {
        item[
            "template_id"
        ]: item
        for item
        in geometry_manifest[
            "templates"
        ]
    }

    sources = load_template_sources(
        geometry_manifest
    )

    materials = {
        sku_id: create_product_material(
            sku
        )
        for sku_id, sku
        in skus.items()
    }

    products = []

    for instance in scene_manifest[
        "product_instances"
    ]:
        sku_id = instance[
            "sku_id"
        ]

        sku = skus[
            sku_id
        ]

        slot_id = instance[
            "slot_id"
        ]

        shelf_id = instance[
            "shelf_id"
        ]

        slot = slots[
            slot_id
        ]

        template_id = sku[
            "geometry_template"
        ]

        template = templates[
            template_id
        ]

        source = sources[
            template_id
        ]

        object_name = (
            "BVT_Product_"
            + slot_id
            + "_"
            + sku_id
        )

        obj = bpy.data.objects.new(
            object_name,
            source.data.copy(),
        )

        collection.objects.link(
            obj
        )

        obj.location = tuple(
            float(value)
            for value
            in slot[
                "position"
            ]
        )

        obj.rotation_euler = (
            0.0,
            0.0,
            0.0,
        )

        obj.scale = (
            1.0,
            1.0,
            1.0,
        )

        ensure_bvt_uv(
            obj
        )

        obj.data.materials.clear()

        obj.data.materials.append(
            materials[
                sku_id
            ]
        )

        obj[
            "bvt_sku_id"
        ] = sku_id

        obj[
            "bvt_shelf_id"
        ] = shelf_id

        obj[
            "bvt_slot_id"
        ] = slot_id

        obj[
            "bvt_geometry_template"
        ] = template_id

        obj[
            "bvt_retail_scene"
        ] = scene_manifest[
            "scene_id"
        ]

        settings = obj.bvt_object

        settings.class_id = int(
            sku[
                "class_id"
            ]
        )

        settings.class_name = str(
            sku[
                "class_name"
            ]
        )

        settings.instance_id = str(
            instance[
                "instance_id"
            ]
        )

        settings.annotation_enabled = True

        register_object(
            obj
        )

        register_asset(
            obj,
            asset_id=sku_id,
            category=ASSET_CATEGORY_PRODUCT,
            manufacturer="BVT Synthetic",
            tags=(
                "retail",
                "beverage",
                sku[
                    "package_type"
                ],
                sku_id,
            ),
            license_name="BVT Synthetic Demo",
            author="BVT",
            version=sku_pack[
                "version"
            ],
        )

        products.append(
            obj
        )

    remove_template_sources(
        sources
    )

    return products


def build():
    sku_pack = load_json(
        SKU_PACK_PATH
    )

    scene_manifest = load_json(
        SCENE_MANIFEST_PATH
    )

    geometry_manifest = load_json(
        GEOMETRY_MANIFEST_PATH
    )

    assert (
        scene_manifest[
            "scene_id"
        ]
        == "beverage_fridge_v01"
    )

    assert (
        len(
            scene_manifest[
                "product_instances"
            ]
        )
        == 18
    )

    clear_scene()

    bvt.register()

    scene = bpy.context.scene

    scene.name = (
        "BVT_Beverage_Fridge_v01"
    )

    scene.unit_settings.system = (
        "METRIC"
    )

    scene.unit_settings.length_unit = (
        "METERS"
    )

    scene.render.engine = (
        "BLENDER_EEVEE"
    )

    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100

    scene[
        "bvt_retail_scene_id"
    ] = scene_manifest[
        "scene_id"
    ]

    scene[
        "bvt_retail_schema"
    ] = scene_manifest[
        "schema_version"
    ]

    scene[
        "bvt_sku_pack_id"
    ] = sku_pack[
        "pack_id"
    ]

    infrastructure = create_collection(
        "BVT_Retail_Infrastructure"
    )

    shelves_collection = create_collection(
        "BVT_Retail_Shelves"
    )

    products_collection = create_collection(
        "BVT_Retail_Products"
    )

    camera_collection = create_collection(
        "BVT_Retail_Camera_Lights"
    )

    body_material = create_material(
        "BVT_Retail_Fridge_Body",
        (
            0.10,
            0.11,
            0.13,
            1.0,
        ),
        0.28,
        MATERIAL_ROLE_GENERIC,
    )

    shelf_material = create_material(
        "BVT_Retail_Fridge_Shelf",
        (
            0.42,
            0.45,
            0.48,
            1.0,
        ),
        0.24,
        MATERIAL_ROLE_GENERIC,
    )

    glass_material = (
        create_glass_material()
    )

    # -----------------------------------------------------
    # Fridge carcass.
    # -----------------------------------------------------

    create_box(
        "BVT_Fridge_Left",
        (
            0.055,
            0.50,
            1.30,
        ),
        (
            -0.4275,
            0.0,
            0.65,
        ),
        infrastructure,
        body_material,
    )

    create_box(
        "BVT_Fridge_Right",
        (
            0.055,
            0.50,
            1.30,
        ),
        (
            0.4275,
            0.0,
            0.65,
        ),
        infrastructure,
        body_material,
    )

    create_box(
        "BVT_Fridge_Bottom",
        (
            0.80,
            0.50,
            0.055,
        ),
        (
            0.0,
            0.0,
            0.0275,
        ),
        infrastructure,
        body_material,
    )

    create_box(
        "BVT_Fridge_Top",
        (
            0.80,
            0.50,
            0.055,
        ),
        (
            0.0,
            0.0,
            1.2725,
        ),
        infrastructure,
        body_material,
    )

    create_box(
        "BVT_Fridge_Back",
        (
            0.80,
            0.025,
            1.20,
        ),
        (
            0.0,
            0.2375,
            0.65,
        ),
        infrastructure,
        body_material,
    )

    glass = create_box(
        "BVT_Fridge_Glass_Door",
        (
            0.82,
            0.008,
            1.20,
        ),
        (
            0.0,
            -0.246,
            0.65,
        ),
        infrastructure,
        glass_material,
    )

    glass[
        "bvt_component"
    ] = "glass_door"

    glass[
        "bvt_material_role"
    ] = "GLASS"

    # -----------------------------------------------------
    # Shelves.
    # -----------------------------------------------------

    shelf_thickness = 0.018

    for shelf in scene_manifest[
        "shelves"
    ]:
        shelf_id = shelf[
            "shelf_id"
        ]

        surface_z = float(
            shelf[
                "surface_z_m"
            ]
        )

        shelf_obj = create_box(
            "BVT_"
            + shelf_id,
            (
                float(
                    shelf[
                        "width_m"
                    ]
                ),
                float(
                    shelf[
                        "depth_m"
                    ]
                ),
                shelf_thickness,
            ),
            (
                0.0,
                0.0,
                surface_z
                - shelf_thickness
                / 2.0,
            ),
            shelves_collection,
            shelf_material,
        )

        shelf_obj[
            "bvt_component"
        ] = "shelf"

        shelf_obj[
            "bvt_shelf_id"
        ] = shelf_id

        shelf_obj[
            "bvt_surface_z_m"
        ] = surface_z

    # -----------------------------------------------------
    # Products.
    # -----------------------------------------------------

    products = build_products(
        scene_manifest,
        sku_pack,
        geometry_manifest,
        products_collection,
    )

    assert len(
        products
    ) == 18

    # -----------------------------------------------------
    # Camera.
    # -----------------------------------------------------

    camera_data = bpy.data.cameras.new(
        "BVT_Retail_Camera"
    )

    camera = bpy.data.objects.new(
        "BVT_Retail_Camera",
        camera_data,
    )

    camera_collection.objects.link(
        camera
    )

    camera.location = (
        0.0,
        -3.0,
        0.67,
    )

    camera_data.lens = 52.0

    point_object(
        camera,
        (
            0.0,
            0.0,
            0.67,
        ),
    )

    scene.camera = camera

    # -----------------------------------------------------
    # Lights.
    # -----------------------------------------------------

    key_data = bpy.data.lights.new(
        "BVT_Retail_Key",
        type="AREA",
    )

    key_data.energy = 850.0
    key_data.shape = "RECTANGLE"
    key_data.size = 2.1
    key_data.size_y = 1.7

    key = bpy.data.objects.new(
        "BVT_Retail_Key",
        key_data,
    )

    camera_collection.objects.link(
        key
    )

    key.location = (
        -0.9,
        -1.4,
        1.45,
    )

    point_object(
        key,
        (
            0.0,
            0.0,
            0.65,
        ),
    )

    fill_data = bpy.data.lights.new(
        "BVT_Retail_Fill",
        type="AREA",
    )

    fill_data.energy = 500.0
    fill_data.shape = "RECTANGLE"
    fill_data.size = 1.7
    fill_data.size_y = 1.4

    fill = bpy.data.objects.new(
        "BVT_Retail_Fill",
        fill_data,
    )

    camera_collection.objects.link(
        fill
    )

    fill.location = (
        0.9,
        -1.1,
        1.05,
    )

    point_object(
        fill,
        (
            0.0,
            0.0,
            0.65,
        ),
    )

    # -----------------------------------------------------
    # World.
    # -----------------------------------------------------

    world = bpy.data.worlds.get(
        "World"
    )

    if world is None:
        world = bpy.data.worlds.new(
            "World"
        )

        scene.world = world

    world.use_nodes = True

    background = next(
        node
        for node
        in world.node_tree.nodes
        if node.type == "BACKGROUND"
    )

    background.inputs[
        "Color"
    ].default_value = (
        0.025,
        0.025,
        0.025,
        1.0,
    )

    background.inputs[
        "Strength"
    ].default_value = 0.30

    # -----------------------------------------------------
    # Save.
    # -----------------------------------------------------

    OUTPUT_BLEND.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    bpy.ops.wm.save_as_mainfile(
        filepath=str(
            OUTPUT_BLEND
        )
    )

    print(
        "scene_id="
        + scene_manifest[
            "scene_id"
        ]
    )

    print(
        "shelves="
        + str(
            len(
                scene_manifest[
                    "shelves"
                ]
            )
        )
    )

    print(
        "products="
        + str(
            len(
                products
            )
        )
    )

    print(
        "glass_role="
        + glass_material.bvt_material.role
    )

    print(
        "camera="
        + scene.camera.name
    )

    print(
        "lights=2"
    )

    print(
        "blend="
        + str(
            OUTPUT_BLEND
        )
    )

    print(
        "BVT_BEVERAGE_FRIDGE_BUILD=OK"
    )


build()
