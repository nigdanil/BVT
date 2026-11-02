import json
import subprocess
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


FROZEN = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)


ARTWORK = (
    ROOT
    / "examples"
    / "retail_demo"
    / "artwork"
    / "sku_pack_v0.1"
    / "artwork-manifest-v0.1.json"
)


CONTRACT = (
    ROOT
    / "docs"
    / "contracts"
    / "SKU-Pack-v0.1.md"
)


assert FROZEN.is_file()
assert ARTWORK.is_file()
assert CONTRACT.is_file()


# The EP7 workflow must never mutate the already released SKU pack.
for ref in (
    "HEAD",
    "v0.1.0",
):
    result = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            ref,
            "--",
            (
                "examples/retail_demo/"
                "sku/sku-pack-v0.1.json"
            ),
        ],
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0


frozen = json.loads(
    FROZEN.read_text(
        encoding="utf-8"
    )
)


skus = frozen[
    "skus"
]


expected = [
    "bev_can_red_330",
    "bev_can_blue_330",
    "bev_bottle_green_500",
    "bev_bottle_amber_500",
    "bev_carton_orange_1000",
    "bev_carton_white_1000",
    "bev_box_purple_250",
    "bev_box_yellow_250",
]


assert [
    item[
        "sku_id"
    ]
    for item
    in skus
] == expected


assert [
    item[
        "class_id"
    ]
    for item
    in skus
] == list(
    range(
        8
    )
)


artwork = json.loads(
    ARTWORK.read_text(
        encoding="utf-8"
    )
)


assert (
    artwork[
        "schema_version"
    ]
    == "bvt-sku-artwork-pack-1"
)


assert (
    artwork[
        "source_sku_pack_mutated"
    ]
    is False
)


items = artwork[
    "items"
]


assert len(
    items
) == 8


assert [
    item[
        "sku_id"
    ]
    for item
    in items
] == expected


assert [
    item[
        "class_id"
    ]
    for item
    in items
] == list(
    range(
        8
    )
)


family_counts = {}


for item in items:
    family = item[
        "family"
    ]

    family_counts[
        family
    ] = (
        family_counts.get(
            family,
            0,
        )
        + 1
    )


    physical = (
        ROOT
        / item[
            "physical_artwork"
        ]
    )


    synthetic = (
        ROOT
        / item[
            "synthetic_texture"
        ]
    )


    assert physical.is_file()
    assert synthetic.is_file()


assert family_counts == {
    "can": 2,
    "bottle": 2,
    "carton": 2,
    "box": 2,
}


print(
    "frozen_sku_pack_unchanged=True"
)

print(
    "sku_count=8"
)

print(
    "artwork_files=8"
)

print(
    "families=can:2,bottle:2,carton:2,box:2"
)

print(
    "BVT_SKU_PACK_CONTRACT=OK"
)

print(
    "RESULT=PASS"
)
