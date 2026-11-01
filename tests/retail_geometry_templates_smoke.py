import json
from pathlib import Path

import bpy


ROOT = Path.cwd()

BLEND_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.blend"
)

MANIFEST_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "geometry-templates-v0.1.json"
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
assert MANIFEST_PATH.is_file()


manifest = json.loads(
    MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


assert (
    bpy.context.scene.unit_settings.system
    in {
        "NONE",
        "METRIC",
    }
)


collection = (
    bpy.data.collections.get(
        "BVT_Retail_Geometry_Templates"
    )
)

assert collection is not None


templates = manifest[
    "templates"
]

assert len(
    templates
) == 4


seen = set()


for template in templates:
    template_id = template[
        "template_id"
    ]

    object_name = template[
        "object_name"
    ]

    obj = bpy.data.objects.get(
        object_name
    )

    assert obj is not None
    assert obj.type == "MESH"

    assert (
        obj[
            "bvt_geometry_template"
        ]
        == template_id
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
            "bvt_template_version"
        ]
        == "0.1.0"
    )

    assert close(
        obj.location.x,
        0.0,
    )

    assert close(
        obj.location.y,
        0.0,
    )

    assert close(
        obj.location.z,
        0.0,
    )

    assert close(
        obj.scale.x,
        1.0,
    )

    assert close(
        obj.scale.y,
        1.0,
    )

    assert close(
        obj.scale.z,
        1.0,
    )

    dimensions = template[
        "reference_dimensions"
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


    # Origin contract:
    # mesh starts exactly at Z=0.
    assert close(
        min(
            zs
        ),
        0.0,
    )


    # Bottom-center origin:
    # local XY bounds are centered around 0.
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


    seen.add(
        template_id
    )

    print(
        "template="
        + template_id
        + " dimensions="
        + ",".join(
            f"{value:.6f}"
            for value
            in (
                obj.dimensions.x,
                obj.dimensions.y,
                obj.dimensions.z,
            )
        )
    )


assert seen == {
    "can",
    "bottle",
    "carton",
    "box",
}


print(
    "template_count=4"
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
    "BVT_RETAIL_GEOMETRY_TEMPLATES_SMOKE=OK"
)

print(
    "RESULT=PASS"
)
