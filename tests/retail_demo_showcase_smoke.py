import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SHOWCASE = (
    ROOT
    / "examples"
    / "retail_demo"
    / "showcase"
)

MANIFEST = (
    SHOWCASE
    / "showcase-v0.1.json"
)


def sha256_file(
    path,
):
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as stream:
        for chunk in iter(
            lambda: stream.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def png_size(
    path,
):
    data = path.read_bytes()

    assert (
        data[:8]
        == b"\x89PNG\r\n\x1a\n"
    )

    assert (
        data[12:16]
        == b"IHDR"
    )

    return struct.unpack(
        ">II",
        data[16:24],
    )


data = json.loads(
    MANIFEST.read_text(
        encoding="utf-8"
    )
)


assert (
    data[
        "schema_version"
    ]
    == "bvt-retail-demo-showcase-1"
)

assert (
    data[
        "release_id"
    ]
    == "retail-demo-v0.1"
)

assert (
    data[
        "frame_policy"
    ]
    == "canonical-frame-000001"
)


outputs = data[
    "outputs"
]


assert len(
    outputs
) == 4


assert [
    item[
        "preset"
    ]
    for item
    in outputs
] == [
    "clean",
    "balanced",
    "artifacts",
    "stress",
]


for item in outputs:
    image_path = (
        SHOWCASE
        / item[
            "image"
        ]
    )

    label_path = (
        SHOWCASE
        / item[
            "label"
        ]
    )

    assert image_path.is_file()
    assert label_path.is_file()

    width, height = (
        png_size(
            image_path
        )
    )

    assert width == 512
    assert height == 512

    assert (
        item[
            "width"
        ]
        == 512
    )

    assert (
        item[
            "height"
        ]
        == 512
    )

    assert (
        sha256_file(
            image_path
        )
        == item[
            "image_sha256"
        ]
    )

    assert (
        sha256_file(
            label_path
        )
        == item[
            "label_sha256"
        ]
    )

    lines = [
        line
        for line
        in label_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert (
        len(
            lines
        )
        == item[
            "object_count"
        ]
    )

    assert (
        item[
            "object_count"
        ]
        > 0
    )

    for line in lines:
        parts = (
            line.split()
        )

        assert len(
            parts
        ) == 5

        class_id = int(
            parts[0]
        )

        assert (
            0
            <= class_id
            <= 7
        )

        values = [
            float(
                value
            )
            for value
            in parts[
                1:
            ]
        ]

        for value in values:
            assert (
                0.0
                <= value
                <= 1.0
            )


for path in (
    ROOT
    / "examples"
    / "retail_demo"
    / "SHOWCASE.md",
    ROOT
    / "examples"
    / "retail_demo"
    / "README.md",
):
    assert path.is_file()


print(
    "showcase_outputs=4"
)

print(
    "showcase_resolution=512x512"
)

print(
    "showcase_labels_valid=True"
)

print(
    "showcase_hashes_valid=True"
)

print(
    "showcase_presets=clean,balanced,artifacts,stress"
)

print(
    "BVT_RETAIL_DEMO_SHOWCASE=OK"
)

print(
    "RESULT=PASS"
)
