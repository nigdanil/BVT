import base64
import hashlib
import json
import math
from pathlib import Path

from PIL import Image


ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[3]
)


PROXY_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "assets"
    / "sku-proxy-pack-v0.1.json"
)


OUTPUT_ROOT = (
    ROOT
    / "examples"
    / "retail_demo"
    / "print"
    / "r01-v0.1"
)


LABEL_DIR = (
    OUTPUT_ROOT
    / "labels"
)


SHEET_DIR = (
    OUTPUT_ROOT
    / "sheets"
)


OUTPUT_MANIFEST = (
    OUTPUT_ROOT
    / "print-pack-v0.1.json"
)


DPI = 300
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
CALIBRATION_MM = 50.0
FAMILY_GAP_MM = 12.0


FAMILY_ORDER = [
    "can",
    "bottle",
    "carton",
    "box",
]


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


def mm_to_px(
    mm,
):
    return int(
        round(
            mm
            / 25.4
            * DPI
        )
    )


def mm_text(
    value,
):
    return (
        f"{value:.2f}"
    )


def package_dimensions_mm(
    record,
):
    source = record[
        "dimensions"
    ]

    return {
        "width": (
            float(
                source[
                    "width_m"
                ]
            )
            * 1000.0
        ),
        "depth": (
            float(
                source[
                    "depth_m"
                ]
            )
            * 1000.0
        ),
        "height": (
            float(
                source[
                    "height_m"
                ]
            )
            * 1000.0
        ),
    }


def label_dimensions_mm(
    record,
):
    source = record[
        "label_dimensions_m"
    ]

    return {
        "width": (
            float(
                source[
                    "width"
                ]
            )
            * 1000.0
        ),
        "height": (
            float(
                source[
                    "height"
                ]
            )
            * 1000.0
        ),
    }


def png_data_uri(
    path,
):
    encoded = base64.b64encode(
        path.read_bytes()
    ).decode(
        "ascii"
    )

    return (
        "data:image/png;base64,"
        + encoded
    )


def build_print_png(
    source_path,
    output_path,
    width_mm,
    height_mm,
):
    width_px = mm_to_px(
        width_mm
    )

    height_px = mm_to_px(
        height_mm
    )


    with Image.open(
        source_path
    ) as image:
        image = image.convert(
            "RGB"
        )


        resized = image.resize(
            (
                width_px,
                height_px,
            ),
            Image.Resampling.LANCZOS,
        )


        resized.save(
            output_path,
            format="PNG",
            dpi=(
                DPI,
                DPI,
            ),
            optimize=True,
            compress_level=9,
        )


    return (
        width_px,
        height_px,
    )


def build_label_svg(
    sku_id,
    print_png,
    output_path,
    width_mm,
    height_mm,
):
    data_uri = png_data_uri(
        print_png
    )


    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{mm_text(width_mm)}mm"
     height="{mm_text(height_mm)}mm"
     viewBox="0 0 {width_mm:.4f} {height_mm:.4f}">
  <title>{sku_id}</title>
  <image
      x="0"
      y="0"
      width="{width_mm:.4f}"
      height="{height_mm:.4f}"
      preserveAspectRatio="none"
      href="{data_uri}" />
</svg>
'''


    output_path.write_text(
        svg,
        encoding="utf-8",
        newline="\n",
    )


def image_svg(
    x,
    y,
    width,
    height,
    data_uri,
):
    return f'''
  <image
      x="{x:.4f}"
      y="{y:.4f}"
      width="{width:.4f}"
      height="{height:.4f}"
      preserveAspectRatio="none"
      href="{data_uri}" />
'''


def cut_rect_svg(
    x,
    y,
    width,
    height,
):
    return f'''
  <rect
      x="{x:.4f}"
      y="{y:.4f}"
      width="{width:.4f}"
      height="{height:.4f}"
      fill="none"
      stroke="#111111"
      stroke-width="0.25"
      stroke-dasharray="2,1" />
'''


def build_family_sheet(
    family,
    records,
):
    assert len(
        records
    ) == 2


    widths = [
        item[
            "print_width_mm"
        ]
        for item
        in records
    ]


    heights = [
        item[
            "print_height_mm"
        ]
        for item
        in records
    ]


    total_width = (
        sum(
            widths
        )
        + FAMILY_GAP_MM
    )


    start_x = (
        (
            A4_WIDTH_MM
            - total_width
        )
        / 2.0
    )


    top_y = 32.0


    cursor_x = start_x


    elements = []


    for record, width, height in zip(
        records,
        widths,
        heights,
    ):
        png_path = (
            ROOT
            / record[
                "print_png"
            ]
        )


        elements.append(
            image_svg(
                cursor_x,
                top_y,
                width,
                height,
                png_data_uri(
                    png_path
                ),
            )
        )


        elements.append(
            cut_rect_svg(
                cursor_x,
                top_y,
                width,
                height,
            )
        )


        label_y = (
            top_y
            + height
            + 7.0
        )


        elements.append(
            f'''
  <text
      x="{cursor_x + width / 2.0:.4f}"
      y="{label_y:.4f}"
      text-anchor="middle"
      font-family="Arial, Helvetica, sans-serif"
      font-size="3.3">
    {record["sku_id"]}
  </text>
'''
        )


        elements.append(
            f'''
  <text
      x="{cursor_x + width / 2.0:.4f}"
      y="{label_y + 5.0:.4f}"
      text-anchor="middle"
      font-family="Arial, Helvetica, sans-serif"
      font-size="3.0">
    {mm_text(width)} × {mm_text(height)} mm
  </text>
'''
        )


        cursor_x += (
            width
            + FAMILY_GAP_MM
        )


    calibration_x = 15.0
    calibration_y = 226.0


    elements.append(
        f'''
  <rect
      x="{calibration_x:.4f}"
      y="{calibration_y:.4f}"
      width="{CALIBRATION_MM:.4f}"
      height="{CALIBRATION_MM:.4f}"
      fill="none"
      stroke="#111111"
      stroke-width="0.5" />
'''
    )


    elements.append(
        f'''
  <text
      x="{calibration_x + CALIBRATION_MM / 2.0:.4f}"
      y="{calibration_y + CALIBRATION_MM / 2.0:.4f}"
      text-anchor="middle"
      dominant-baseline="middle"
      font-family="Arial, Helvetica, sans-serif"
      font-size="4">
    50 × 50 mm
  </text>
'''
    )


    elements.append(
        '''
  <text
      x="75"
      y="236"
      font-family="Arial, Helvetica, sans-serif"
      font-size="4">
    PRINT AT 100% — DO NOT FIT TO PAGE
  </text>

  <text
      x="75"
      y="244"
      font-family="Arial, Helvetica, sans-serif"
      font-size="3.5">
    Measure the 50 mm calibration square before cutting labels.
  </text>
'''
    )


    sheet_path = (
        SHEET_DIR
        / (
            "A4-"
            + family
            + "-v0.1.svg"
        )
    )


    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="210mm"
     height="297mm"
     viewBox="0 0 210 297">

  <rect
      x="0"
      y="0"
      width="210"
      height="297"
      fill="#ffffff" />

  <text
      x="105"
      y="13"
      text-anchor="middle"
      font-family="Arial, Helvetica, sans-serif"
      font-size="6"
      font-weight="700">
    BVT R01 — {family.upper()} LABELS
  </text>

  <text
      x="105"
      y="21"
      text-anchor="middle"
      font-family="Arial, Helvetica, sans-serif"
      font-size="3.5">
    Physical Print Pack v0.1 — scale 100%
  </text>

{''.join(elements)}

</svg>
'''


    sheet_path.write_text(
        svg,
        encoding="utf-8",
        newline="\n",
    )


    return sheet_path


def main():
    LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    SHEET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    source_manifest = json.loads(
        PROXY_MANIFEST.read_text(
            encoding="utf-8"
        )
    )


    source_records = source_manifest[
        "records"
    ]


    assert len(
        source_records
    ) == 8


    records = []


    for source in source_records:
        sku_id = source[
            "sku_id"
        ]


        family = source[
            "package_type"
        ]


        source_texture = (
            ROOT
            / source[
                "proxy_texture"
            ]
        )


        assert source_texture.is_file()


        label_mm = label_dimensions_mm(
            source
        )


        package_mm = (
            package_dimensions_mm(
                source
            )
        )


        print_png = (
            LABEL_DIR
            / (
                sku_id
                + "-300dpi.png"
            )
        )


        print_svg = (
            LABEL_DIR
            / (
                sku_id
                + "-1to1.svg"
            )
        )


        width_px, height_px = (
            build_print_png(
                source_texture,
                print_png,
                label_mm[
                    "width"
                ],
                label_mm[
                    "height"
                ],
            )
        )


        build_label_svg(
            sku_id,
            print_png,
            print_svg,
            label_mm[
                "width"
            ],
            label_mm[
                "height"
            ],
        )


        record = {
            "class_id": (
                source[
                    "class_id"
                ]
            ),
            "sku_id": sku_id,
            "family": family,
            "label_surface": (
                source[
                    "label_surface"
                ]
            ),
            "source_proxy_texture": (
                source[
                    "proxy_texture"
                ]
            ),
            "source_proxy_texture_sha256": (
                sha256_file(
                    source_texture
                )
            ),
            "target_package_dimensions_mm": (
                package_mm
            ),
            "print_width_mm": (
                label_mm[
                    "width"
                ]
            ),
            "print_height_mm": (
                label_mm[
                    "height"
                ]
            ),
            "print_dpi": DPI,
            "print_width_px": (
                width_px
            ),
            "print_height_px": (
                height_px
            ),
            "print_png": (
                print_png
                .relative_to(
                    ROOT
                )
                .as_posix()
            ),
            "print_png_sha256": (
                sha256_file(
                    print_png
                )
            ),
            "print_svg": (
                print_svg
                .relative_to(
                    ROOT
                )
                .as_posix()
            ),
            "print_svg_sha256": (
                sha256_file(
                    print_svg
                )
            ),
            "scale_percent": 100,
        }


        records.append(
            record
        )


    sheets = []


    for family in FAMILY_ORDER:
        family_records = [
            item
            for item
            in records
            if item[
                "family"
            ]
            == family
        ]


        assert len(
            family_records
        ) == 2


        sheet_path = build_family_sheet(
            family,
            family_records,
        )


        relative_sheet = (
            sheet_path
            .relative_to(
                ROOT
            )
            .as_posix()
        )


        for item in family_records:
            item[
                "a4_sheet"
            ] = relative_sheet


        sheets.append(
            {
                "family": family,
                "file": (
                    relative_sheet
                ),
                "sha256": (
                    sha256_file(
                        sheet_path
                    )
                ),
                "page_width_mm": (
                    A4_WIDTH_MM
                ),
                "page_height_mm": (
                    A4_HEIGHT_MM
                ),
                "calibration_square_mm": (
                    CALIBRATION_MM
                ),
                "scale_percent": 100,
            }
        )


    output = {
        "schema_version": (
            "bvt-r01-print-pack-1"
        ),
        "version": "0.1.0",
        "dataset_session": "R01",
        "source_proxy_manifest": (
            "examples/retail_demo/"
            "assets/sku-proxy-pack-v0.1.json"
        ),
        "print_dpi": DPI,
        "print_scale_percent": 100,
        "fit_to_page": False,
        "calibration_square_mm": (
            CALIBRATION_MM
        ),
        "container_tolerance_mm": {
            "width_depth": 5.0,
            "height": 10.0,
        },
        "records": records,
        "sheets": sheets,
    }


    OUTPUT_MANIFEST.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


    print(
        "print_labels="
        + str(
            len(
                records
            )
        )
    )


    print(
        "a4_sheets="
        + str(
            len(
                sheets
            )
        )
    )


    print(
        "print_dpi="
        + str(
            DPI
        )
    )


    print(
        "print_scale_percent=100"
    )


    print(
        "calibration_square_mm=50"
    )


    print(
        "BVT_R01_PRINT_PACK_BUILD=OK"
    )


if __name__ == "__main__":
    main()
