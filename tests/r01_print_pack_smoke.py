import json
import re
import struct
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "print"
    / "r01-v0.1"
    / "print-pack-v0.1.json"
)


PROXY_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.json"
)


CONTRACT = (
    ROOT
    / "docs"
    / "contracts"
    / "R01-Physical-Print-Pack-v0.1.md"
)


CAPTURE_CARD = (
    ROOT
    / "benchmarks"
    / "real"
    / "R01_CAPTURE_CARD-v0.1.md"
)


PNG_SIGNATURE = (
    b"\x89PNG\r\n\x1a\n"
)


def close(
    left,
    right,
    tolerance=0.01,
):
    return abs(
        float(
            left
        )
        - float(
            right
        )
    ) <= tolerance


def png_dimensions(
    path,
):
    data = path.read_bytes()


    assert data.startswith(
        PNG_SIGNATURE
    )


    assert data[
        12:16
    ] == b"IHDR"


    width, height = struct.unpack(
        ">II",
        data[
            16:24
        ],
    )


    return (
        width,
        height,
    )


assert MANIFEST.is_file()
assert PROXY_MANIFEST.is_file()
assert CONTRACT.is_file()
assert CAPTURE_CARD.is_file()


data = json.loads(
    MANIFEST.read_text(
        encoding="utf-8"
    )
)


proxy = json.loads(
    PROXY_MANIFEST.read_text(
        encoding="utf-8"
    )
)


assert (
    data[
        "schema_version"
    ]
    == "bvt-r01-print-pack-1"
)


assert (
    data[
        "dataset_session"
    ]
    == "R01"
)


assert (
    data[
        "print_dpi"
    ]
    == 300
)


assert (
    data[
        "print_scale_percent"
    ]
    == 100
)


assert (
    data[
        "fit_to_page"
    ]
    is False
)


assert (
    data[
        "calibration_square_mm"
    ]
    == 50.0
)


records = data[
    "records"
]


assert len(
    records
) == 8


proxy_by_sku = {
    item[
        "sku_id"
    ]: item
    for item
    in proxy[
        "records"
    ]
}


family_counts = {}


for record in records:
    sku_id = record[
        "sku_id"
    ]


    source = proxy_by_sku[
        sku_id
    ]


    family = record[
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


    expected_width = (
        source[
            "label_dimensions_m"
        ][
            "width"
        ]
        * 1000.0
    )


    expected_height = (
        source[
            "label_dimensions_m"
        ][
            "height"
        ]
        * 1000.0
    )


    assert close(
        record[
            "print_width_mm"
        ],
        expected_width,
    )


    assert close(
        record[
            "print_height_mm"
        ],
        expected_height,
    )


    package = record[
        "target_package_dimensions_mm"
    ]


    assert close(
        package[
            "width"
        ],
        source[
            "dimensions"
        ][
            "width_m"
        ]
        * 1000.0,
    )


    assert close(
        package[
            "depth"
        ],
        source[
            "dimensions"
        ][
            "depth_m"
        ]
        * 1000.0,
    )


    assert close(
        package[
            "height"
        ],
        source[
            "dimensions"
        ][
            "height_m"
        ]
        * 1000.0,
    )


    png_path = (
        ROOT
        / record[
            "print_png"
        ]
    )


    svg_path = (
        ROOT
        / record[
            "print_svg"
        ]
    )


    sheet_path = (
        ROOT
        / record[
            "a4_sheet"
        ]
    )


    assert png_path.is_file()
    assert svg_path.is_file()
    assert sheet_path.is_file()


    assert (
        png_dimensions(
            png_path
        )
        == (
            record[
                "print_width_px"
            ],
            record[
                "print_height_px"
            ],
        )
    )


    svg = svg_path.read_text(
        encoding="utf-8"
    )


    width_pattern = (
        'width="'
        + f'{record["print_width_mm"]:.2f}'
        + 'mm"'
    )


    height_pattern = (
        'height="'
        + f'{record["print_height_mm"]:.2f}'
        + 'mm"'
    )


    assert width_pattern in svg
    assert height_pattern in svg


    assert (
        "data:image/png;base64,"
        in svg
    )


assert family_counts == {
    "can": 2,
    "bottle": 2,
    "carton": 2,
    "box": 2,
}


sheets = data[
    "sheets"
]


assert len(
    sheets
) == 4


assert {
    item[
        "family"
    ]
    for item
    in sheets
} == {
    "can",
    "bottle",
    "carton",
    "box",
}


for sheet in sheets:
    path = (
        ROOT
        / sheet[
            "file"
        ]
    )


    assert path.is_file()


    text = path.read_text(
        encoding="utf-8"
    )


    assert 'width="210mm"' in text
    assert 'height="297mm"' in text
    assert "50 × 50 mm" in text
    assert "DO NOT FIT TO PAGE" in text


capture_card = CAPTURE_CARD.read_text(
    encoding="utf-8"
)


assert (
    "## Physical SKU preparation"
    in capture_card
)


assert (
    "50 × 50 mm"
    in capture_card
)


print(
    "print_labels=8"
)


print(
    "a4_sheets=4"
)


print(
    "families=can:2,bottle:2,carton:2,box:2"
)


print(
    "print_dpi=300"
)


print(
    "print_scale_percent=100"
)


print(
    "calibration_square_mm=50"
)


print(
    "BVT_R01_PRINT_PACK_SMOKE=OK"
)


print(
    "RESULT=PASS"
)
