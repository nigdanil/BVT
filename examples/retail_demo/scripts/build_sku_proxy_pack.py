import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path.cwd()


SKU_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)


ARTWORK_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "artwork"
    / "sku_pack_v0.1"
    / "artwork-manifest-v0.1.json"
)


TEXTURE_MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "textures"
    / "sku_proxy_v0.1"
    / "texture-manifest-v0.1.json"
)


BLEND_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.blend"
)


MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.json"
)


PREVIEW_PATH = (
    ROOT
    / ".tmp"
    / "sku-proxy-pack-v0.1-preview.png"
)


COLLECTION_NAME = (
    "BVT_SKU_Proxy_Pack_v0_1"
)


PREVIEW_COLLECTION_NAME = (
    "BVT_SKU_Proxy_Preview_v0_1"
)


def mesh_object(
    name,
    vertices,
    faces,
    collection,
):
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


    return obj


def cylinder_geometry(
    width,
    depth,
    height,
    segments=64,
):
    radius_x = (
        width
        / 2.0
    )

    radius_y = (
        depth
        / 2.0
    )


    vertices = []


    for z in (
        0.0,
        height,
    ):
        for index in range(
            segments
        ):
            angle = (
                2.0
                * math.pi
                * index
                / segments
            )

            vertices.append(
                (
                    radius_x
                    * math.cos(
                        angle
                    ),
                    radius_y
                    * math.sin(
                        angle
                    ),
                    z,
                )
            )


    bottom_center = len(
        vertices
    )

    vertices.append(
        (
            0.0,
            0.0,
            0.0,
        )
    )


    top_center = len(
        vertices
    )

    vertices.append(
        (
            0.0,
            0.0,
            height,
        )
    )


    faces = []


    for index in range(
        segments
    ):
        next_index = (
            index + 1
        ) % segments


        faces.append(
            (
                index,
                next_index,
                segments
                + next_index,
                segments
                + index,
            )
        )


        faces.append(
            (
                bottom_center,
                next_index,
                index,
            )
        )


        faces.append(
            (
                top_center,
                segments
                + index,
                segments
                + next_index,
            )
        )


    return (
        vertices,
        faces,
    )


def bottle_geometry(
    width,
    depth,
    height,
    segments=64,
):
    radius_x = (
        width
        / 2.0
    )

    radius_y = (
        depth
        / 2.0
    )


    profile = [
        (
            0.00,
            0.92,
        ),
        (
            0.035,
            1.00,
        ),
        (
            0.58,
            1.00,
        ),
        (
            0.67,
            0.96,
        ),
        (
            0.75,
            0.80,
        ),
        (
            0.82,
            0.54,
        ),
        (
            0.88,
            0.38,
        ),
        (
            0.96,
            0.36,
        ),
        (
            1.00,
            0.36,
        ),
    ]


    vertices = []


    for z_factor, radius_factor in profile:
        z = (
            height
            * z_factor
        )


        for index in range(
            segments
        ):
            angle = (
                2.0
                * math.pi
                * index
                / segments
            )


            vertices.append(
                (
                    radius_x
                    * radius_factor
                    * math.cos(
                        angle
                    ),
                    radius_y
                    * radius_factor
                    * math.sin(
                        angle
                    ),
                    z,
                )
            )


    faces = []


    ring_count = len(
        profile
    )


    for ring in range(
        ring_count - 1
    ):
        start = (
            ring
            * segments
        )

        next_start = (
            (
                ring + 1
            )
            * segments
        )


        for index in range(
            segments
        ):
            next_index = (
                index + 1
            ) % segments


            faces.append(
                (
                    start + index,
                    start + next_index,
                    next_start + next_index,
                    next_start + index,
                )
            )


    bottom_center = len(
        vertices
    )

    vertices.append(
        (
            0.0,
            0.0,
            0.0,
        )
    )


    top_center = len(
        vertices
    )

    vertices.append(
        (
            0.0,
            0.0,
            height,
        )
    )


    final_ring = (
        (
            ring_count - 1
        )
        * segments
    )


    for index in range(
        segments
    ):
        next_index = (
            index + 1
        ) % segments


        faces.append(
            (
                bottom_center,
                next_index,
                index,
            )
        )


        faces.append(
            (
                top_center,
                final_ring + index,
                final_ring + next_index,
            )
        )


    return (
        vertices,
        faces,
    )


def box_geometry(
    width,
    depth,
    height,
):
    x = (
        width
        / 2.0
    )

    y = (
        depth
        / 2.0
    )


    vertices = [
        (
            -x,
            -y,
            0.0,
        ),
        (
            x,
            -y,
            0.0,
        ),
        (
            x,
            y,
            0.0,
        ),
        (
            -x,
            y,
            0.0,
        ),
        (
            -x,
            -y,
            height,
        ),
        (
            x,
            -y,
            height,
        ),
        (
            x,
            y,
            height,
        ),
        (
            -x,
            y,
            height,
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


    return (
        vertices,
        faces,
    )


def carton_geometry(
    width,
    depth,
    height,
):
    x = (
        width
        / 2.0
    )

    y = (
        depth
        / 2.0
    )

    body_top = (
        height
        * 0.90
    )


    vertices = [
        (
            -x,
            -y,
            0.0,
        ),
        (
            x,
            -y,
            0.0,
        ),
        (
            x,
            y,
            0.0,
        ),
        (
            -x,
            y,
            0.0,
        ),
        (
            -x,
            -y,
            body_top,
        ),
        (
            x,
            -y,
            body_top,
        ),
        (
            x,
            y,
            body_top,
        ),
        (
            -x,
            y,
            body_top,
        ),
        (
            0.0,
            -y,
            height,
        ),
        (
            0.0,
            y,
            height,
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
            8,
        ),
        (
            7,
            9,
            6,
        ),
        (
            4,
            8,
            9,
            7,
        ),
        (
            5,
            6,
            9,
            8,
        ),
    ]


    return (
        vertices,
        faces,
    )


def body_material(
    sku,
):
    material = bpy.data.materials.new(
        (
            "MAT_"
            + sku[
                "sku_id"
            ]
            + "_Body"
        )
    )


    material.use_nodes = True


    bsdf = (
        material
        .node_tree
        .nodes
        .get(
            "Principled BSDF"
        )
    )


    color = sku[
        "visual"
    ][
        "base_color"
    ]


    rgb = [
        float(
            value
        )
        for value
        in color[
            :3
        ]
    ]


    spread = (
        max(
            rgb
        )
        - min(
            rgb
        )
    )


    if (
        min(
            rgb
        )
        > 0.75
        and spread
        < 0.08
    ):
        color_factor = 0.88

    else:
        color_factor = 1.12


    body_color = tuple(
        min(
            1.0,
            max(
                0.0,
                value
                * color_factor,
            ),
        )
        for value
        in rgb
    ) + (
        float(
            color[
                3
            ]
        ),
    )


    bsdf.inputs[
        "Base Color"
    ].default_value = body_color


    material[
        "bvt_body_color_factor"
    ] = color_factor


    bsdf.inputs[
        "Roughness"
    ].default_value = (
        0.30
        if sku[
            "package_type"
        ]
        in {
            "can",
            "bottle",
        }
        else 0.48
    )


    if (
        sku[
            "package_type"
        ]
        == "can"
    ):
        bsdf.inputs[
            "Metallic"
        ].default_value = 0.10


    return material


def label_material(
    sku_id,
    texture_path,
):
    material = bpy.data.materials.new(
        (
            "MAT_"
            + sku_id
            + "_Label"
        )
    )


    material.use_nodes = True


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


    nodes.clear()


    output = nodes.new(
        "ShaderNodeOutputMaterial"
    )


    bsdf = nodes.new(
        "ShaderNodeBsdfPrincipled"
    )


    texture = nodes.new(
        "ShaderNodeTexImage"
    )


    image = bpy.data.images.load(
        str(
            texture_path
        ),
        check_existing=False,
    )


    image.filepath = bpy.path.relpath(
        str(
            texture_path
        ),
        start=str(
            BLEND_PATH.parent
        ),
    )


    texture.image = image


    adjust = nodes.new(
        "ShaderNodeHueSaturation"
    )


    adjust.inputs[
        "Saturation"
    ].default_value = 1.20


    adjust.inputs[
        "Value"
    ].default_value = 0.92


    links.new(
        texture.outputs[
            "Color"
        ],
        adjust.inputs[
            "Color"
        ],
    )


    links.new(
        adjust.outputs[
            "Color"
        ],
        bsdf.inputs[
            "Base Color"
        ],
    )


    links.new(
        bsdf.outputs[
            "BSDF"
        ],
        output.inputs[
            "Surface"
        ],
    )


    bsdf.inputs[
        "Roughness"
    ].default_value = 0.32


    material[
        "bvt_label_saturation"
    ] = 1.20


    material[
        "bvt_label_value"
    ] = 0.92


    return material


def label_mesh_object(
    sku_id,
    width,
    height,
    collection,
):
    vertices = [
        (
            -width / 2.0,
            0.0,
            -height / 2.0,
        ),
        (
            width / 2.0,
            0.0,
            -height / 2.0,
        ),
        (
            width / 2.0,
            0.0,
            height / 2.0,
        ),
        (
            -width / 2.0,
            0.0,
            height / 2.0,
        ),
    ]


    mesh = bpy.data.meshes.new(
        (
            "SKU_Label_"
            + sku_id
            + "_Mesh"
        )
    )


    mesh.from_pydata(
        vertices,
        [],
        [
            (
                0,
                1,
                2,
                3,
            )
        ],
    )


    mesh.update()


    uv_layer = mesh.uv_layers.new(
        name="UVMap"
    )


    uv_values = [
        (
            0.0,
            0.0,
        ),
        (
            1.0,
            0.0,
        ),
        (
            1.0,
            1.0,
        ),
        (
            0.0,
            1.0,
        ),
    ]


    polygon = mesh.polygons[
        0
    ]


    for loop_index, uv in zip(
        polygon.loop_indices,
        uv_values,
    ):
        uv_layer.data[
            loop_index
        ].uv = uv


    obj = bpy.data.objects.new(
        (
            "SKU_Label_"
            + sku_id
        ),
        mesh,
    )


    collection.objects.link(
        obj
    )


    return obj


def curved_label_mesh_object(
    sku_id,
    radius_x,
    radius_y,
    height,
    arc_degrees,
    collection,
    segments=36,
    surface_offset=0.0008,
):
    """
    Curved front label for cylindrical packaging.

    Front direction is -Y. UV runs left-to-right across
    the curved arc and bottom-to-top vertically.
    """

    center_angle = (
        -math.pi
        / 2.0
    )


    half_arc = (
        math.radians(
            arc_degrees
        )
        / 2.0
    )


    vertices = []


    for index in range(
        segments
        + 1
    ):
        fraction = (
            index
            / segments
        )


        angle = (
            center_angle
            - half_arc
            + (
                2.0
                * half_arc
                * fraction
            )
        )


        x = (
            (
                radius_x
                + surface_offset
            )
            * math.cos(
                angle
            )
        )


        y = (
            (
                radius_y
                + surface_offset
            )
            * math.sin(
                angle
            )
        )


        vertices.extend(
            [
                (
                    x,
                    y,
                    -height / 2.0,
                ),
                (
                    x,
                    y,
                    height / 2.0,
                ),
            ]
        )


    faces = []


    for index in range(
        segments
    ):
        left_bottom = (
            index
            * 2
        )

        left_top = (
            left_bottom
            + 1
        )

        right_bottom = (
            left_bottom
            + 2
        )

        right_top = (
            left_bottom
            + 3
        )


        faces.append(
            (
                left_bottom,
                right_bottom,
                right_top,
                left_top,
            )
        )


    mesh = bpy.data.meshes.new(
        (
            "SKU_Label_"
            + sku_id
            + "_Mesh"
        )
    )


    mesh.from_pydata(
        vertices,
        [],
        faces,
    )


    mesh.validate()
    mesh.update()


    uv_layer = mesh.uv_layers.new(
        name="UVMap"
    )


    for index, polygon in enumerate(
        mesh.polygons
    ):
        u0 = (
            index
            / segments
        )

        u1 = (
            (
                index
                + 1
            )
            / segments
        )


        uv_values = [
            (
                u0,
                0.0,
            ),
            (
                u1,
                0.0,
            ),
            (
                u1,
                1.0,
            ),
            (
                u0,
                1.0,
            ),
        ]


        for loop_index, uv in zip(
            polygon.loop_indices,
            uv_values,
        ):
            uv_layer.data[
                loop_index
            ].uv = uv


    obj = bpy.data.objects.new(
        (
            "SKU_Label_"
            + sku_id
        ),
        mesh,
    )


    collection.objects.link(
        obj
    )


    return obj


def add_preview_floor(
    collection,
):
    vertices = [
        (
            -1.2,
            -0.35,
            0.0,
        ),
        (
            1.2,
            -0.35,
            0.0,
        ),
        (
            1.2,
            0.35,
            0.0,
        ),
        (
            -1.2,
            0.35,
            0.0,
        ),
    ]


    floor = mesh_object(
        "BVT_Proxy_Preview_Floor",
        vertices,
        [
            (
                0,
                1,
                2,
                3,
            )
        ],
        collection,
    )


    material = bpy.data.materials.new(
        "MAT_BVT_Proxy_Preview_Floor"
    )


    material.diffuse_color = (
        0.10,
        0.11,
        0.13,
        1.0,
    )


    floor.data.materials.append(
        material
    )


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


def add_preview_camera_and_lights(
    collection,
):
    scene = bpy.context.scene


    camera_data = bpy.data.cameras.new(
        "BVT_SKU_Proxy_Preview_Camera"
    )


    camera = bpy.data.objects.new(
        "BVT_SKU_Proxy_Preview_Camera",
        camera_data,
    )


    collection.objects.link(
        camera
    )


    camera.location = (
        0.0,
        -2.35,
        0.36,
    )


    camera.data.lens = 50.0


    point_at(
        camera,
        (
            0.0,
            0.0,
            0.105,
        ),
    )


    scene.camera = camera


    for (
        name,
        location,
        energy,
        size,
    ) in (
        (
            "Key",
            (
                -0.7,
                -1.0,
                1.55,
            ),
            950.0,
            1.25,
        ),
        (
            "Fill",
            (
                0.9,
                -0.55,
                1.00,
            ),
            650.0,
            1.0,
        ),
    ):
        light_data = bpy.data.lights.new(
            (
                "BVT_SKU_Proxy_"
                + name
            ),
            type="AREA",
        )


        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size


        light = bpy.data.objects.new(
            (
                "BVT_SKU_Proxy_"
                + name
            ),
            light_data,
        )


        collection.objects.link(
            light
        )


        light.location = location


        point_at(
            light,
            (
                0.0,
                0.0,
                0.10,
            ),
        )


def main():
    bpy.ops.wm.read_factory_settings(
        use_empty=True
    )


    scene = bpy.context.scene


    scene.unit_settings.system = (
        "METRIC"
    )


    scene.unit_settings.length_unit = (
        "METERS"
    )


    frozen = json.loads(
        SKU_PATH.read_text(
            encoding="utf-8"
        )
    )


    artwork = json.loads(
        ARTWORK_PATH.read_text(
            encoding="utf-8"
        )
    )


    textures = json.loads(
        TEXTURE_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


    texture_by_sku = {
        item[
            "sku_id"
        ]: item
        for item
        in textures[
            "records"
        ]
    }


    artwork_by_sku = {
        item[
            "sku_id"
        ]: item
        for item
        in artwork[
            "items"
        ]
    }


    collection = bpy.data.collections.new(
        COLLECTION_NAME
    )


    scene.collection.children.link(
        collection
    )


    preview_collection = (
        bpy.data.collections.new(
            PREVIEW_COLLECTION_NAME
        )
    )


    scene.collection.children.link(
        preview_collection
    )


    records = []


    skus = frozen[
        "skus"
    ]


    spacing = 0.18


    start_x = (
        -spacing
        * (
            len(
                skus
            )
            - 1
        )
        / 2.0
    )


    for index, sku in enumerate(
        skus
    ):
        sku_id = sku[
            "sku_id"
        ]


        package_type = sku[
            "package_type"
        ]


        dimensions = sku[
            "dimensions"
        ]


        width = dimensions[
            "width_m"
        ]

        depth = dimensions[
            "depth_m"
        ]

        height = dimensions[
            "height_m"
        ]


        if package_type == "can":
            vertices, faces = (
                cylinder_geometry(
                    width,
                    depth,
                    height,
                )
            )

        elif package_type == "bottle":
            vertices, faces = (
                bottle_geometry(
                    width,
                    depth,
                    height,
                )
            )

        elif package_type == "carton":
            vertices, faces = (
                carton_geometry(
                    width,
                    depth,
                    height,
                )
            )

        elif package_type == "box":
            vertices, faces = (
                box_geometry(
                    width,
                    depth,
                    height,
                )
            )

        else:
            raise RuntimeError(
                "Unsupported package type: "
                + package_type
            )


        object_name = (
            "SKU_"
            + sku_id
        )


        obj = mesh_object(
            object_name,
            vertices,
            faces,
            collection,
        )


        x = (
            start_x
            + index
            * spacing
        )


        obj.location = (
            x,
            0.0,
            0.0,
        )


        obj[
            "bvt_sku_id"
        ] = sku_id


        obj[
            "bvt_class_id"
        ] = sku[
            "class_id"
        ]


        obj[
            "bvt_geometry_template"
        ] = sku[
            "geometry_template"
        ]


        obj[
            "bvt_package_type"
        ] = package_type


        obj[
            "bvt_origin_contract"
        ] = "bottom-center"


        obj[
            "bvt_front_direction"
        ] = "-Y"


        obj[
            "bvt_units"
        ] = "meters"


        obj[
            "bvt_proxy_pack_version"
        ] = "0.1.0"


        obj.data.materials.append(
            body_material(
                sku
            )
        )


        if package_type in {
            "can",
            "bottle",
        }:
            for polygon in obj.data.polygons:
                polygon.use_smooth = True


        label_width = (
            width
            * 0.82
        )


        label_height = (
            label_width
            * 1.5
        )


        center_z = (
            height
            * 0.50
        )


        if package_type in {
            "can",
            "bottle",
        }:
            average_radius = (
                (
                    width
                    + depth
                )
                / 4.0
            )


            label_arc_degrees = (
                math.degrees(
                    label_width
                    / average_radius
                )
            )


            label = curved_label_mesh_object(
                sku_id,
                width / 2.0,
                depth / 2.0,
                label_height,
                label_arc_degrees,
                collection,
            )


            label_surface = (
                "curved_arc"
            )


            label.parent = obj


            label.location = (
                0.0,
                0.0,
                center_z,
            )

        else:
            label_arc_degrees = 0.0


            label = label_mesh_object(
                sku_id,
                label_width,
                label_height,
                collection,
            )


            label_surface = (
                "front_plane"
            )


            label.parent = obj


            label.location = (
                0.0,
                (
                    -depth
                    / 2.0
                    - 0.0008
                ),
                center_z,
            )


        texture_record = texture_by_sku[
            sku_id
        ]


        texture_path = (
            ROOT
            / texture_record[
                "texture"
            ]
        )


        label.data.materials.append(
            label_material(
                sku_id,
                texture_path,
            )
        )


        label[
            "bvt_sku_id"
        ] = sku_id


        label[
            "bvt_label_for"
        ] = object_name


        label[
            "bvt_front_direction"
        ] = "-Y"


        label[
            "bvt_label_surface"
        ] = label_surface


        label[
            "bvt_label_arc_degrees"
        ] = float(
            label_arc_degrees
        )


        label[
            "bvt_label_parented"
        ] = True


        label[
            "bvt_proxy_texture"
        ] = texture_record[
            "texture"
        ]


        artwork_record = artwork_by_sku[
            sku_id
        ]


        obj[
            "bvt_physical_artwork"
        ] = artwork_record[
            "physical_artwork"
        ]


        obj[
            "bvt_proxy_texture"
        ] = texture_record[
            "texture"
        ]


        records.append(
            {
                "class_id": (
                    sku[
                        "class_id"
                    ]
                ),
                "sku_id": sku_id,
                "package_type": (
                    package_type
                ),
                "object_name": (
                    object_name
                ),
                "label_object_name": (
                    label.name
                ),
                "dimensions": (
                    dimensions
                ),
                "location": [
                    x,
                    0.0,
                    0.0,
                ],
                "origin": (
                    "bottom-center"
                ),
                "front_direction": (
                    "-Y"
                ),
                "proxy_texture": (
                    texture_record[
                        "texture"
                    ]
                ),
                "physical_artwork": (
                    artwork_record[
                        "physical_artwork"
                    ]
                ),
                "label_dimensions_m": {
                    "width": (
                        label_width
                    ),
                    "height": (
                        label_height
                    ),
                },
                "label_surface": (
                    label_surface
                ),
                "label_arc_degrees": (
                    label_arc_degrees
                ),
                "carton_gable_fraction": (
                    0.10
                    if package_type
                    == "carton"
                    else None
                ),
            }
        )


    add_preview_floor(
        preview_collection
    )


    add_preview_camera_and_lights(
        preview_collection
    )


    manifest = {
        "schema_version": (
            "bvt-sku-proxy-pack-1"
        ),
        "version": "0.1.0",
        "units": "meters",
        "origin": "bottom-center",
        "front_direction": "-Y",
        "source_sku_pack": (
            "examples/retail_demo/"
            "sku/sku-pack-v0.1.json"
        ),
        "source_artwork_manifest": (
            "examples/retail_demo/"
            "artwork/sku_pack_v0.1/"
            "artwork-manifest-v0.1.json"
        ),
        "texture_manifest": (
            "examples/retail_demo/"
            "textures/sku_proxy_v0.1/"
            "texture-manifest-v0.1.json"
        ),
        "blend": (
            "examples/retail_demo/"
            "assets/sku-proxy-pack-v0.1.blend"
        ),
        "collection": (
            COLLECTION_NAME
        ),
        "records": records,
    }


    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


    PREVIEW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    scene.render.engine = (
        "BLENDER_EEVEE"
    )


    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100


    scene.render.image_settings.file_format = (
        "PNG"
    )


    scene.render.filepath = str(
        PREVIEW_PATH
    )


    if scene.world is None:
        world = bpy.data.worlds.new(
            "BVT_SKU_Proxy_World"
        )

        scene.world = world


    scene.world.color = (
        0.025,
        0.028,
        0.035,
    )


    BLEND_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    # First save establishes the .blend location.
    bpy.ops.wm.save_as_mainfile(
        filepath=str(
            BLEND_PATH
        )
    )


    # Then convert linked texture paths relative to the saved .blend.
    bpy.ops.file.make_paths_relative()


    # Persist the converted paths.
    bpy.ops.wm.save_as_mainfile(
        filepath=str(
            BLEND_PATH
        )
    )


    bpy.ops.render.render(
        write_still=True
    )


    print(
        "proxy_objects="
        + str(
            len(
                records
            )
        )
    )


    print(
        "proxy_textures=8"
    )


    print(
        "collection="
        + COLLECTION_NAME
    )


    print(
        "blend="
        + str(
            BLEND_PATH
        )
    )


    print(
        "preview="
        + str(
            PREVIEW_PATH
        )
    )


    print(
        "BVT_SKU_PROXY_PACK_BUILD=OK"
    )


if __name__ == "__main__":
    main()
