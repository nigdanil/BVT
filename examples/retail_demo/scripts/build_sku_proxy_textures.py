import hashlib
import json
from pathlib import Path

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[3]
)


ARTWORK_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "artwork"
    / "sku_pack_v0.1"
    / "artwork-manifest-v0.1.json"
)


SKU_MANIFEST = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)


OUTPUT_DIR = (
    ROOT
    / "examples"
    / "retail_demo"
    / "textures"
    / "sku_proxy_v0.1"
)


TEXTURE_MANIFEST = (
    OUTPUT_DIR
    / "texture-manifest-v0.1.json"
)


WIDTH = 1024
HEIGHT = 1536


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


def hex_rgb(
    value,
):
    value = value.lstrip(
        "#"
    )

    return tuple(
        int(
            value[
                index:index + 2
            ],
            16,
        )
        for index
        in (
            0,
            2,
            4,
        )
    )


def font(
    size,
    bold=False,
):
    candidates = (
        (
            "arialbd.ttf",
            "Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
        )
        if bold
        else (
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
        )
    )


    for candidate in candidates:
        try:
            return ImageFont.truetype(
                candidate,
                size,
            )
        except OSError:
            pass


    try:
        return ImageFont.load_default(
            size=size
        )
    except TypeError:
        return ImageFont.load_default()


def centered_text(
    draw,
    text,
    y,
    text_font,
    fill,
):
    box = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=text_font,
    )

    width = (
        box[
            2
        ]
        - box[
            0
        ]
    )

    draw.text(
        (
            (
                WIDTH
                - width
            )
            / 2,
            y,
        ),
        text,
        font=text_font,
        fill=fill,
    )


def build_texture(
    record,
):
    primary = hex_rgb(
        record[
            "primary_color"
        ]
    )

    accent = hex_rgb(
        record[
            "accent_color"
        ]
    )

    class_id = record[
        "class_id"
    ]

    sku_id = record[
        "sku_id"
    ]

    family = record[
        "family"
    ]


    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        primary,
    )


    draw = ImageDraw.Draw(
        image
    )


    # Distinctive deterministic visual pattern.
    step = (
        110
        + class_id * 7
    )


    for x in range(
        -HEIGHT,
        WIDTH + HEIGHT,
        step,
    ):
        draw.polygon(
            [
                (
                    x,
                    0,
                ),
                (
                    x + 42,
                    0,
                ),
                (
                    x + HEIGHT + 42,
                    HEIGHT,
                ),
                (
                    x + HEIGHT,
                    HEIGHT,
                ),
            ],
            fill=accent,
        )


    # Central visual panel.
    draw.rounded_rectangle(
        (
            64,
            64,
            WIDTH - 64,
            HEIGHT - 64,
        ),
        radius=48,
        fill=primary,
        outline=accent,
        width=20,
    )


    draw.rounded_rectangle(
        (
            100,
            100,
            WIDTH - 100,
            310,
        ),
        radius=28,
        fill=accent,
    )


    centered_text(
        draw,
        "BVT",
        145,
        font(
            110,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    centered_text(
        draw,
        family.upper(),
        395,
        font(
            72,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    draw.rounded_rectangle(
        (
            130,
            560,
            WIDTH - 130,
            940,
        ),
        radius=50,
        fill=accent,
    )


    centered_text(
        draw,
        (
            "CLASS "
            + str(
                class_id
            )
        ),
        645,
        font(
            125,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    centered_text(
        draw,
        (
            f"{class_id:02d}"
        ),
        775,
        font(
            150,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    centered_text(
        draw,
        sku_id,
        1060,
        font(
            46,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    centered_text(
        draw,
        "SYNTHETIC ↔ PHYSICAL",
        1235,
        font(
            36,
            bold=True,
        ),
        (
            255,
            255,
            255,
        ),
    )


    centered_text(
        draw,
        "SKU PACK v0.1",
        1325,
        font(
            34,
        ),
        (
            255,
            255,
            255,
        ),
    )


    path = (
        OUTPUT_DIR
        / (
            sku_id
            + ".png"
        )
    )


    image.save(
        path,
        format="PNG",
        optimize=True,
        compress_level=9,
    )


    return path


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    artwork = json.loads(
        ARTWORK_MANIFEST.read_text(
            encoding="utf-8"
        )
    )


    frozen = json.loads(
        SKU_MANIFEST.read_text(
            encoding="utf-8"
        )
    )


    frozen_skus = frozen[
        "skus"
    ]


    artwork_items = artwork[
        "items"
    ]


    assert len(
        frozen_skus
    ) == 8


    assert [
        item[
            "sku_id"
        ]
        for item
        in frozen_skus
    ] == [
        item[
            "sku_id"
        ]
        for item
        in artwork_items
    ]


    records = []


    for record in artwork_items:
        texture_path = build_texture(
            record
        )


        records.append(
            {
                "class_id": (
                    record[
                        "class_id"
                    ]
                ),
                "sku_id": (
                    record[
                        "sku_id"
                    ]
                ),
                "family": (
                    record[
                        "family"
                    ]
                ),
                "width_px": WIDTH,
                "height_px": HEIGHT,
                "texture": (
                    texture_path
                    .relative_to(
                        ROOT
                    )
                    .as_posix()
                ),
                "texture_sha256": (
                    sha256_file(
                        texture_path
                    )
                ),
                "source_artwork": (
                    record[
                        "physical_artwork"
                    ]
                ),
                "source_artwork_sha256": (
                    sha256_file(
                        ROOT
                        / record[
                            "physical_artwork"
                        ]
                    )
                ),
            }
        )


    output = {
        "schema_version": (
            "bvt-sku-proxy-textures-1"
        ),
        "version": "0.1.0",
        "width_px": WIDTH,
        "height_px": HEIGHT,
        "records": records,
    }


    TEXTURE_MANIFEST.write_text(
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
        "texture_count="
        + str(
            len(
                records
            )
        )
    )

    print(
        "texture_size="
        + str(
            WIDTH
        )
        + "x"
        + str(
            HEIGHT
        )
    )

    print(
        "BVT_SKU_PROXY_TEXTURES=OK"
    )


if __name__ == "__main__":
    main()
