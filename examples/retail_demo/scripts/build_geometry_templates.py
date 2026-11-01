import json
import math
from pathlib import Path

import bpy


ROOT = Path.cwd()

MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.json"
)

OUTPUT_BLEND = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.blend"
)


def load_manifest():
    return json.loads(
        MANIFEST_PATH.read_text(
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


def create_collection():
    collection = (
        bpy.data.collections.new(
            "BVT_Retail_Geometry_Templates"
        )
    )

    bpy.context.scene.collection.children.link(
        collection
    )

    return collection


def create_mesh_object(
    name,
    vertices,
    faces,
    collection,
):
    mesh = bpy.data.meshes.new(
        name + "_Mesh"
    )

    mesh.from_pydata(
        vertices,
        [],
        faces,
    )

    mesh.update()

    obj = bpy.data.objects.new(
        name,
        mesh,
    )

    collection.objects.link(
        obj
    )

    return obj


def create_box(
    name,
    width,
    depth,
    height,
    collection,
):
    x = width / 2.0
    y = depth / 2.0

    vertices = [
        (-x, -y, 0.0),
        ( x, -y, 0.0),
        ( x,  y, 0.0),
        (-x,  y, 0.0),

        (-x, -y, height),
        ( x, -y, height),
        ( x,  y, height),
        (-x,  y, height),
    ]

    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]

    return create_mesh_object(
        name,
        vertices,
        faces,
        collection,
    )


def create_radial_profile(
    name,
    profile,
    collection,
    segments=64,
):
    vertices = []
    faces = []

    for z, radius in profile:
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
                    radius
                    * math.cos(
                        angle
                    ),
                    radius
                    * math.sin(
                        angle
                    ),
                    z,
                )
            )

    ring_count = len(
        profile
    )

    for ring in range(
        ring_count - 1
    ):
        current = (
            ring
            * segments
        )

        following = (
            (ring + 1)
            * segments
        )

        for index in range(
            segments
        ):
            next_index = (
                (index + 1)
                % segments
            )

            faces.append(
                (
                    current
                    + index,

                    current
                    + next_index,

                    following
                    + next_index,

                    following
                    + index,
                )
            )

    bottom = tuple(
        reversed(
            range(
                segments
            )
        )
    )

    top_start = (
        (ring_count - 1)
        * segments
    )

    top = tuple(
        top_start
        + index
        for index
        in range(
            segments
        )
    )

    faces.append(
        bottom
    )

    faces.append(
        top
    )

    obj = create_mesh_object(
        name,
        vertices,
        faces,
        collection,
    )

    # Side faces smooth, cap faces flat.
    for polygon in obj.data.polygons:
        polygon.use_smooth = (
            len(
                polygon.vertices
            )
            == 4
        )

    return obj


def configure_template(
    obj,
    template,
):
    template_id = template[
        "template_id"
    ]

    obj.location = (
        0.0,
        0.0,
        0.0,
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

    obj[
        "bvt_geometry_template"
    ] = template_id

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
        "bvt_template_version"
    ] = "0.1.0"


def build():
    manifest = load_manifest()

    assert (
        manifest[
            "schema_version"
        ]
        == "bvt-retail-geometry-templates-1"
    )

    assert (
        manifest[
            "units"
        ]
        == "meters"
    )

    assert (
        manifest[
            "origin"
        ]
        == "bottom-center"
    )

    clear_scene()

    collection = create_collection()

    built = {}

    for template in manifest[
        "templates"
    ]:
        template_id = template[
            "template_id"
        ]

        object_name = template[
            "object_name"
        ]

        dimensions = template[
            "reference_dimensions"
        ]

        width = float(
            dimensions[
                "width_m"
            ]
        )

        depth = float(
            dimensions[
                "depth_m"
            ]
        )

        height = float(
            dimensions[
                "height_m"
            ]
        )

        if template_id == "can":
            obj = create_radial_profile(
                object_name,
                [
                    (
                        0.0,
                        width / 2.0,
                    ),
                    (
                        height,
                        width / 2.0,
                    ),
                ],
                collection,
            )

        elif template_id == "bottle":
            radius = (
                width / 2.0
            )

            obj = create_radial_profile(
                object_name,
                [
                    (
                        0.0,
                        radius,
                    ),
                    (
                        height * 0.68,
                        radius,
                    ),
                    (
                        height * 0.76,
                        radius * 0.94,
                    ),
                    (
                        height * 0.84,
                        radius * 0.66,
                    ),
                    (
                        height * 0.94,
                        radius * 0.44,
                    ),
                    (
                        height,
                        radius * 0.44,
                    ),
                ],
                collection,
            )

        elif template_id in {
            "carton",
            "box",
        }:
            obj = create_box(
                object_name,
                width,
                depth,
                height,
                collection,
            )

        else:
            raise ValueError(
                "Unsupported geometry template: "
                + template_id
            )

        configure_template(
            obj,
            template,
        )

        built[
            template_id
        ] = obj

    assert set(
        built
    ) == {
        "can",
        "bottle",
        "carton",
        "box",
    }

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
        "template_count="
        + str(
            len(
                built
            )
        )
    )

    print(
        "templates="
        + ",".join(
            sorted(
                built
            )
        )
    )

    print(
        "blend="
        + str(
            OUTPUT_BLEND
        )
    )

    print(
        "BVT_RETAIL_GEOMETRY_BUILD=OK"
    )


build()
