import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEMO = (
    ROOT
    / "examples"
    / "retail_demo"
)


release = json.loads(
    (
        DEMO
        / "release-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


sku_pack = json.loads(
    (
        DEMO
        / "sku"
        / "sku-pack-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


required = [
    DEMO / "LICENSES.md",
    DEMO / "ATTRIBUTIONS.md",
    DEMO / "SAMPLE_DATASET_LICENSE.md",
    ROOT / "THIRD_PARTY.md",
]


for path in required:
    assert path.is_file(), path


licenses = (
    DEMO
    / "LICENSES.md"
).read_text(
    encoding="utf-8"
)


sample_license = (
    DEMO
    / "SAMPLE_DATASET_LICENSE.md"
).read_text(
    encoding="utf-8"
)


attributions = (
    DEMO
    / "ATTRIBUTIONS.md"
).read_text(
    encoding="utf-8"
)


third_party = (
    ROOT
    / "THIRD_PARTY.md"
).read_text(
    encoding="utf-8"
)


addon_manifest = (
    ROOT
    / "src"
    / "bvt"
    / "blender_manifest.toml"
).read_text(
    encoding="utf-8"
)


assert (
    "SPDX:GPL-3.0-or-later"
    in addon_manifest
)

assert (
    "CC-BY-4.0"
    in licenses
)

assert (
    "CC-BY-4.0"
    in sample_license
)

assert (
    "third-party demo assets"
    in third_party.lower()
)

assert (
    "0"
    in third_party
)


attribution = release[
    "attribution"
]


assert (
    attribution[
        "path"
    ]
    == (
        "examples/retail_demo/"
        "ATTRIBUTIONS.md"
    )
)

assert (
    attribution[
        "third_party_assets"
    ]
    == 0
)

assert (
    attribution[
        "asset_license_status"
    ]
    == "verified-cc-by-4.0"
)

assert (
    attribution[
        "asset_license_spdx"
    ]
    == "CC-BY-4.0"
)

assert (
    attribution[
        "sample_dataset_license_spdx"
    ]
    == "CC-BY-4.0"
)


skus = sku_pack[
    "skus"
]


assert len(
    skus
) == 8


for sku in skus:
    assert (
        sku[
            "provenance"
        ][
            "type"
        ]
        == "synthetic"
    )

    assert (
        sku[
            "provenance"
        ][
            "attribution_required"
        ]
        is False
    )

    assert (
        sku[
            "display_name"
        ].startswith(
            "Synthetic "
        )
    )


for forbidden in (
    "coca-cola",
    "pepsi",
    "nestlé",
    "nestle",
):
    assert (
        forbidden
        not in attributions.lower()
    )


print(
    "addon_license=GPL-3.0-or-later"
)

print(
    "demo_asset_license=CC-BY-4.0"
)

print(
    "sample_dataset_license=CC-BY-4.0"
)

print(
    "third_party_demo_assets=0"
)

print(
    "synthetic_skus=8"
)

print(
    "BVT_RETAIL_DEMO_LICENSING=OK"
)

print(
    "RESULT=PASS"
)
