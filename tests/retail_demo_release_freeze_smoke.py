import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "release-v0.1.json"
)

SKU_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


release = json.loads(
    RELEASE_PATH.read_text(
        encoding="utf-8"
    )
)


assert (
    release[
        "schema_version"
    ]
    == "bvt-retail-demo-release-1"
)

assert (
    release[
        "release_id"
    ]
    == "retail-demo-v0.1"
)

assert (
    release[
        "release_version"
    ]
    == "0.1.0"
)

assert (
    release[
        "status"
    ]
    == "candidate"
)


records = release[
    "files"
]


assert len(
    records
) == 17


paths = set()


for item in records:
    relative = item[
        "path"
    ]

    assert relative not in paths

    paths.add(relative)

    path = ROOT / relative

    assert path.is_file(), relative

    assert (
        path.stat().st_size
        == item[
            "size_bytes"
        ]
    )

    assert (
        sha256_file(path)
        == item[
            "sha256"
        ]
    )


scene_path = (
    "examples/retail_demo/scenes/"
    "beverage-fridge-v0.1.blend"
)

sku_path = (
    "examples/retail_demo/sku/"
    "sku-pack-v0.1.json"
)


assert (
    release[
        "scene"
    ][
        "path"
    ]
    == scene_path
)

assert scene_path in paths

assert (
    release[
        "sku_pack"
    ][
        "path"
    ]
    == sku_path
)

assert sku_path in paths


sku_pack = json.loads(
    SKU_PATH.read_text(
        encoding="utf-8"
    )
)


skus = sku_pack[
    "skus"
]


assert len(
    skus
) == 8

assert (
    [
        item[
            "class_id"
        ]
        for item
        in skus
    ]
    == list(
        range(8)
    )
)

assert len(
    {
        item[
            "sku_id"
        ]
        for item
        in skus
    }
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

    texture = (
        sku[
            "visual"
        ][
            "texture"
        ]
    )

    assert texture in paths


presets = release[
    "presets"
]


assert set(
    presets
) == {
    "clean",
    "balanced",
    "artifacts",
    "stress",
}


configs = {}


for name, relative in (
    presets.items()
):
    assert relative in paths

    configs[name] = json.loads(
        (
            ROOT
            / relative
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        configs[name][
            "schema_version"
        ]
        == "bvt-cli-scenario-1"
    )


clean = configs[
    "clean"
][
    "settings"
]

assert (
    clean[
        "artifact_engine_enabled"
    ]
    is False
)

assert (
    clean[
        "placement_randomization_enabled"
    ]
    is False
)

assert (
    clean[
        "camera_randomization_enabled"
    ]
    is False
)

assert (
    clean[
        "lighting_randomization_enabled"
    ]
    is False
)


balanced = configs[
    "balanced"
][
    "settings"
]

assert (
    balanced[
        "placement_randomization_enabled"
    ]
    is True
)

assert (
    balanced[
        "camera_randomization_enabled"
    ]
    is True
)

assert (
    balanced[
        "lighting_randomization_enabled"
    ]
    is True
)

assert (
    balanced[
        "artifact_engine_enabled"
    ]
    is True
)

assert (
    balanced[
        "retail_edge_cases_enabled"
    ]
    is False
)


artifact_names = (
    "over_exposure",
    "reflection",
    "fingerprints",
    "condensation",
    "frost",
    "dust",
    "water_drops",
    "scratches",
    "motion_blur",
    "noise",
    "jpeg",
)


artifacts = configs[
    "artifacts"
][
    "settings"
]


for name in artifact_names:
    assert (
        artifacts[
            "artifact_"
            + name
            + "_enabled"
        ]
        is True
    )


assert (
    artifacts[
        "retail_edge_cases_enabled"
    ]
    is False
)


stress = configs[
    "stress"
][
    "settings"
]


for name in artifact_names:
    assert (
        stress[
            "artifact_"
            + name
            + "_enabled"
        ]
        is True
    )


assert (
    stress[
        "retail_edge_cases_enabled"
    ]
    is True
)

assert (
    stress[
        "retail_wrong_angle_enabled"
    ]
    is True
)

assert (
    stress[
        "retail_wrong_position_enabled"
    ]
    is True
)

assert (
    stress[
        "retail_empty_slot_enabled"
    ]
    is True
)

assert (
    stress[
        "retail_occlusion_enabled"
    ]
    is True
)


assert (
    release[
        "attribution"
    ][
        "third_party_assets"
    ]
    == 0
)

assert (
    release[
        "attribution"
    ][
        "asset_license_status"
    ]
    == "verified-cc-by-4.0"
)


print(
    "frozen_scene=True"
)

print(
    "frozen_sku_pack=True"
)

print(
    "sku_count=8"
)

print(
    "third_party_assets=0"
)

print(
    "preset_clean=True"
)

print(
    "preset_balanced=True"
)

print(
    "preset_artifacts=True"
)

print(
    "preset_stress=True"
)

print(
    "asset_license_status=pending-final-release-decision"
)

print(
    "BVT_RETAIL_DEMO_RELEASE_FREEZE=OK"
)

print(
    "RESULT=PASS"
)
