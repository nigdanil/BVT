import argparse
import json
import re
from pathlib import Path


SKU_ID_RE = re.compile(
    r"^[a-z0-9]+(?:_[a-z0-9]+)*$"
)

SHELF_ID_RE = re.compile(
    r"^shelf_[0-9]{2}$"
)

SLOT_ID_RE = re.compile(
    r"^slot_[0-9]{3}$"
)

SUPPORTED_PACKAGE_TYPES = {
    "can",
    "bottle",
    "carton",
    "box",
}

SUPPORTED_TEMPLATES = {
    "can",
    "bottle",
    "carton",
    "box",
}


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def validate_color(value):
    assert isinstance(
        value,
        list,
    )

    assert len(
        value
    ) == 4

    for channel in value:
        assert isinstance(
            channel,
            (int, float),
        )

        assert (
            0.0
            <= float(channel)
            <= 1.0
        )


def validate_sku_pack(pack):
    assert (
        pack[
            "schema_version"
        ]
        == "bvt-sku-pack-1"
    )

    assert (
        pack[
            "sku_schema_version"
        ]
        == "bvt-sku-1"
    )

    skus = pack[
        "skus"
    ]

    assert isinstance(
        skus,
        list,
    )

    assert len(
        skus
    ) >= 4

    sku_ids = []
    class_ids = []

    for sku in skus:
        assert (
            sku[
                "schema_version"
            ]
            == "bvt-sku-1"
        )

        sku_id = sku[
            "sku_id"
        ]

        assert SKU_ID_RE.fullmatch(
            sku_id
        )

        assert (
            sku[
                "class_name"
            ]
            == sku_id
        )

        class_id = int(
            sku[
                "class_id"
            ]
        )

        assert class_id >= 0

        assert (
            sku[
                "package_type"
            ]
            in SUPPORTED_PACKAGE_TYPES
        )

        assert (
            sku[
                "geometry_template"
            ]
            in SUPPORTED_TEMPLATES
        )

        dimensions = sku[
            "dimensions"
        ]

        for key in (
            "width_m",
            "depth_m",
            "height_m",
        ):
            assert (
                float(
                    dimensions[
                        key
                    ]
                )
                > 0.0
            )

        visual = sku[
            "visual"
        ]

        validate_color(
            visual[
                "base_color"
            ]
        )

        texture = visual[
            "texture"
        ]

        if texture is not None:
            texture_path = Path(
                texture
            )

            assert (
                not texture_path.is_absolute()
            )

            normalized_texture = str(
                texture
            ).replace(
                "\\",
                "/",
            )

            assert normalized_texture.startswith(
                "examples/retail_demo/textures/"
            )

            assert (
                texture_path.suffix.lower()
                == ".png"
            )

            resolved_texture = (
                Path.cwd()
                / texture_path
            )

            assert (
                resolved_texture.is_file()
            ), resolved_texture

        assert (
            sku[
                "annotation"
            ][
                "enabled"
            ]
            is True
        )

        assert (
            sku[
                "provenance"
            ][
                "type"
            ]
            == "synthetic"
        )

        sku_ids.append(
            sku_id
        )

        class_ids.append(
            class_id
        )

    assert (
        len(
            sku_ids
        )
        == len(
            set(
                sku_ids
            )
        )
    )

    assert (
        len(
            class_ids
        )
        == len(
            set(
                class_ids
            )
        )
    )

    assert (
        sorted(
            class_ids
        )
        == list(
            range(
                len(
                    class_ids
                )
            )
        )
    )

    return {
        sku[
            "sku_id"
        ]: sku
        for sku
        in skus
    }


def validate_scene_manifest(
    manifest,
    pack,
    skus,
):
    assert (
        manifest[
            "schema_version"
        ]
        == "bvt-retail-scene-1"
    )

    scene_id = manifest[
        "scene_id"
    ]

    assert (
        scene_id
        == "beverage_fridge_v01"
    )

    pack_ref = manifest[
        "sku_pack"
    ]

    assert (
        pack_ref[
            "pack_id"
        ]
        == pack[
            "pack_id"
        ]
    )

    assert (
        pack_ref[
            "version"
        ]
        == pack[
            "version"
        ]
    )

    coordinate_system = manifest[
        "coordinate_system"
    ]

    assert (
        coordinate_system[
            "units"
        ]
        == "meters"
    )

    assert (
        coordinate_system[
            "width_axis"
        ]
        == "X"
    )

    assert (
        coordinate_system[
            "depth_axis"
        ]
        == "Y"
    )

    assert (
        coordinate_system[
            "vertical_axis"
        ]
        == "Z"
    )

    assert (
        coordinate_system[
            "front_direction"
        ]
        == "-Y"
    )

    templates = manifest[
        "geometry_templates"
    ]

    template_ids = {
        item[
            "template_id"
        ]
        for item
        in templates
    }

    assert (
        template_ids
        == SUPPORTED_TEMPLATES
    )

    for template in templates:
        assert (
            template[
                "origin"
            ]
            == "bottom-center"
        )

        assert (
            template[
                "front_direction"
            ]
            == "-Y"
        )

    materials = {
        item[
            "material_id"
        ]: item
        for item
        in manifest[
            "materials"
        ]
    }

    assert (
        materials[
            "fridge_glass"
        ][
            "role"
        ]
        == "GLASS"
    )

    shelves = manifest[
        "shelves"
    ]

    assert len(
        shelves
    ) >= 3

    shelf_ids = []

    for shelf in shelves:
        shelf_id = shelf[
            "shelf_id"
        ]

        assert SHELF_ID_RE.fullmatch(
            shelf_id
        )

        assert (
            float(
                shelf[
                    "width_m"
                ]
            )
            > 0.0
        )

        assert (
            float(
                shelf[
                    "depth_m"
                ]
            )
            > 0.0
        )

        shelf_ids.append(
            shelf_id
        )

    assert (
        len(
            shelf_ids
        )
        == len(
            set(
                shelf_ids
            )
        )
    )

    shelf_id_set = set(
        shelf_ids
    )

    slots = manifest[
        "slots"
    ]

    slot_ids = []
    slots_by_id = {}

    for slot in slots:
        slot_id = slot[
            "slot_id"
        ]

        assert SLOT_ID_RE.fullmatch(
            slot_id
        )

        assert (
            slot[
                "shelf_id"
            ]
            in shelf_id_set
        )

        position = slot[
            "position"
        ]

        assert isinstance(
            position,
            list,
        )

        assert len(
            position
        ) == 3

        for coordinate in position:
            assert isinstance(
                coordinate,
                (int, float),
            )

        slot_ids.append(
            slot_id
        )

        slots_by_id[
            slot_id
        ] = slot

    assert (
        len(
            slot_ids
        )
        == len(
            set(
                slot_ids
            )
        )
    )

    instances = manifest[
        "product_instances"
    ]

    instance_ids = []
    occupied_slots = []
    referenced_skus = set()

    for instance in instances:
        sku_id = instance[
            "sku_id"
        ]

        shelf_id = instance[
            "shelf_id"
        ]

        slot_id = instance[
            "slot_id"
        ]

        assert (
            sku_id
            in skus
        )

        assert (
            shelf_id
            in shelf_id_set
        )

        assert (
            slot_id
            in slots_by_id
        )

        assert (
            slots_by_id[
                slot_id
            ][
                "shelf_id"
            ]
            == shelf_id
        )

        expected_instance_id = (
            "retail:"
            f"{scene_id}:"
            f"{shelf_id}:"
            f"{slot_id}:"
            f"{sku_id}"
        )

        assert (
            instance[
                "instance_id"
            ]
            == expected_instance_id
        )

        instance_ids.append(
            instance[
                "instance_id"
            ]
        )

        occupied_slots.append(
            slot_id
        )

        referenced_skus.add(
            sku_id
        )

    assert (
        len(
            instance_ids
        )
        == len(
            set(
                instance_ids
            )
        )
    )

    assert (
        len(
            occupied_slots
        )
        == len(
            set(
                occupied_slots
            )
        )
    )

    assert (
        referenced_skus
        == set(
            skus
        )
    )

    return {
        "scene_id": scene_id,
        "shelf_count": len(
            shelves
        ),
        "slot_count": len(
            slots
        ),
        "instance_count": len(
            instances
        ),
        "sku_count": len(
            skus
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sku-pack",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--scene-manifest",
        required=True,
        type=Path,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    pack = load_json(
        args.sku_pack
    )

    manifest = load_json(
        args.scene_manifest
    )

    skus = validate_sku_pack(
        pack
    )

    result = validate_scene_manifest(
        manifest,
        pack,
        skus,
    )

    print(
        "sku_pack_schema=bvt-sku-pack-1"
    )

    print(
        "sku_schema=bvt-sku-1"
    )

    print(
        "scene_schema=bvt-retail-scene-1"
    )

    print(
        "scene_id="
        + result[
            "scene_id"
        ]
    )

    print(
        "sku_count="
        + str(
            result[
                "sku_count"
            ]
        )
    )

    print(
        "shelf_count="
        + str(
            result[
                "shelf_count"
            ]
        )
    )

    print(
        "slot_count="
        + str(
            result[
                "slot_count"
            ]
        )
    )

    print(
        "instance_count="
        + str(
            result[
                "instance_count"
            ]
        )
    )

    print(
        "glass_role=GLASS"
    )

    print(
        "deterministic_instance_ids=True"
    )

    print(
        "all_skus_referenced=True"
    )

    print(
        "BVT_RETAIL_FOUNDATION_VALIDATION=OK"
    )


if __name__ == "__main__":
    main()
