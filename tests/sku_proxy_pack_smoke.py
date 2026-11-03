import json
from pathlib import Path

import bpy


ROOT = Path.cwd()


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


SKU_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)


TOLERANCE = 1e-6


def close(
    left,
    right,
):
    return abs(
        float(
            left
        )
        - float(
            right
        )
    ) <= TOLERANCE


assert BLEND_PATH.is_file()
assert MANIFEST_PATH.is_file()
assert SKU_PATH.is_file()


manifest = json.loads(
    MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)


frozen = json.loads(
    SKU_PATH.read_text(
        encoding="utf-8"
    )
)


assert (
    manifest[
        "schema_version"
    ]
    == "bvt-sku-proxy-pack-1"
)


assert (
    manifest[
        "version"
    ]
    == "0.1.0"
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


assert (
    manifest[
        "front_direction"
    ]
    == "-Y"
)


records = manifest[
    "records"
]


assert len(
    records
) == 8


assert [
    item[
        "sku_id"
    ]
    for item
    in records
] == [
    item[
        "sku_id"
    ]
    for item
    in frozen[
        "skus"
    ]
]


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


collection = bpy.data.collections.get(
    manifest[
        "collection"
    ]
)


assert collection is not None


sku_by_id = {
    item[
        "sku_id"
    ]: item
    for item
    in frozen[
        "skus"
    ]
}


for record in records:
    sku_id = record[
        "sku_id"
    ]


    sku = sku_by_id[
        sku_id
    ]


    obj = bpy.data.objects.get(
        record[
            "object_name"
        ]
    )


    label = bpy.data.objects.get(
        record[
            "label_object_name"
        ]
    )


    assert obj is not None
    assert label is not None


    assert obj.type == "MESH"
    assert label.type == "MESH"


    assert label.parent is obj


    assert (
        label[
            "bvt_label_parented"
        ]
        is True
    )


    package_type = sku[
        "package_type"
    ]


    if package_type in {
        "can",
        "bottle",
    }:
        assert (
            label[
                "bvt_label_surface"
            ]
            == "curved_arc"
        )


        arc = float(
            label[
                "bvt_label_arc_degrees"
            ]
        )


        assert (
            80.0
            < arc
            < 115.0
        )


        assert len(
            label.data.polygons
        ) == 36

    else:
        assert (
            label[
                "bvt_label_surface"
            ]
            == "front_plane"
        )


        assert close(
            label[
                "bvt_label_arc_degrees"
            ],
            0.0,
        )


        assert len(
            label.data.polygons
        ) == 1


    assert (
        obj[
            "bvt_sku_id"
        ]
        == sku_id
    )


    assert (
        obj[
            "bvt_class_id"
        ]
        == sku[
            "class_id"
        ]
    )


    assert (
        obj[
            "bvt_geometry_template"
        ]
        == sku[
            "geometry_template"
        ]
    )


    assert (
        obj[
            "bvt_origin_contract"
        ]
        == "bottom-center"
    )


    assert (
        obj[
            "bvt_front_direction"
        ]
        == "-Y"
    )


    assert (
        obj[
            "bvt_units"
        ]
        == "meters"
    )


    assert (
        obj[
            "bvt_proxy_pack_version"
        ]
        == "0.1.0"
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


    if (
        sku[
            "package_type"
        ]
        == "carton"
    ):
        z_levels = sorted(
            {
                round(
                    float(
                        vertex.co.z
                    ),
                    8,
                )
                for vertex
                in obj.data.vertices
            }
        )


        assert len(
            z_levels
        ) == 3


        assert close(
            z_levels[
                1
            ],
            dimensions[
                "height_m"
            ]
            * 0.90,
        )


    xs = [
        vertex.co.x
        for vertex
        in obj.data.vertices
    ]


    ys = [
        vertex.co.y
        for vertex
        in obj.data.vertices
    ]


    zs = [
        vertex.co.z
        for vertex
        in obj.data.vertices
    ]


    assert close(
        min(
            zs
        ),
        0.0,
    )


    assert close(
        (
            min(
                xs
            )
            + max(
                xs
            )
        )
        / 2.0,
        0.0,
    )


    assert close(
        (
            min(
                ys
            )
            + max(
                ys
            )
        )
        / 2.0,
        0.0,
    )


    assert (
        label[
            "bvt_label_for"
        ]
        == obj.name
    )


    texture_path = (
        ROOT
        / record[
            "proxy_texture"
        ]
    )


    artwork_path = (
        ROOT
        / record[
            "physical_artwork"
        ]
    )


    assert texture_path.is_file()
    assert artwork_path.is_file()


    assert len(
        label.data.materials
    ) == 1


    material = label.data.materials[
        0
    ]


    image_nodes = [
        node
        for node
        in material.node_tree.nodes
        if node.type == "TEX_IMAGE"
    ]


    assert len(
        image_nodes
    ) == 1


    image = image_nodes[
        0
    ].image


    assert image is not None


    assert (
        Path(
            image.filepath
        ).name
        == texture_path.name
    )


    assert (
        int(
            image.size[
                0
            ]
        )
        == 1024
    )


    assert (
        int(
            image.size[
                1
            ]
        )
        == 1536
    )


    print(
        "sku="
        + sku_id
        + " dimensions="
        + ",".join(
            [
                (
                    f"{obj.dimensions.x:.6f}"
                ),
                (
                    f"{obj.dimensions.y:.6f}"
                ),
                (
                    f"{obj.dimensions.z:.6f}"
                ),
            ]
        )
    )


print(
    "proxy_object_count=8"
)


print(
    "proxy_texture_count=8"
)


print(
    "units=meters"
)


print(
    "origin=bottom-center"
)


print(
    "front_direction=-Y"
)


print(
    "BVT_SKU_PROXY_PACK_SMOKE=OK"
)


print(
    "RESULT=PASS"
)
