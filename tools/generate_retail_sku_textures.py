import hashlib
import json
import struct
import zlib
from pathlib import Path


ROOT = Path.cwd()

SKU_PACK_PATH = (
    ROOT
    / "examples"
    / "retail_demo"
    / "sku"
    / "sku-pack-v0.1.json"
)

TEXTURE_DIRECTORY = (
    ROOT
    / "examples"
    / "retail_demo"
    / "textures"
)

WIDTH = 256
HEIGHT = 256


def png_chunk(
    chunk_type,
    payload,
):
    return (
        struct.pack(
            ">I",
            len(
                payload
            ),
        )
        + chunk_type
        + payload
        + struct.pack(
            ">I",
            zlib.crc32(
                chunk_type
                + payload
            )
            & 0xFFFFFFFF,
        )
    )


def write_rgba_png(
    path,
    width,
    height,
    pixels,
):
    assert len(
        pixels
    ) == (
        width
        * height
        * 4
    )

    raw = bytearray()

    stride = (
        width
        * 4
    )

    for y in range(
        height
    ):
        raw.append(
            0
        )

        start = (
            y
            * stride
        )

        raw.extend(
            pixels[
                start:
                start + stride
            ]
        )

    signature = (
        b"\x89PNG\r\n\x1a\n"
    )

    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        6,
        0,
        0,
        0,
    )

    payload = (
        signature
        + png_chunk(
            b"IHDR",
            ihdr,
        )
        + png_chunk(
            b"IDAT",
            zlib.compress(
                bytes(
                    raw
                ),
                level=9,
            ),
        )
        + png_chunk(
            b"IEND",
            b"",
        )
    )

    path.write_bytes(
        payload
    )


def to_rgb(
    rgba,
):
    return tuple(
        max(
            0,
            min(
                255,
                round(
                    float(value)
                    * 255
                ),
            ),
        )
        for value
        in rgba[:3]
    )


def mix(
    first,
    second,
    factor,
):
    return tuple(
        round(
            first[index]
            * (
                1.0
                - factor
            )
            + second[index]
            * factor
        )
        for index
        in range(
            3
        )
    )


def texture_pixels(
    sku,
):
    sku_id = sku[
        "sku_id"
    ]

    class_id = int(
        sku[
            "class_id"
        ]
    )

    base = to_rgb(
        sku[
            "visual"
        ][
            "base_color"
        ]
    )

    white = (
        245,
        245,
        240,
    )

    black = (
        20,
        22,
        26,
    )

    accent = mix(
        base,
        white,
        0.58,
    )

    dark = mix(
        base,
        black,
        0.48,
    )

    digest = hashlib.sha256(
        sku_id.encode(
            "utf-8"
        )
    ).digest()

    pixels = bytearray()

    band_y = (
        54
        + (
            class_id
            * 17
        )
        % 76
    )

    stripe_x = (
        24
        + (
            class_id
            * 23
        )
        % 118
    )

    for y in range(
        HEIGHT
    ):
        for x in range(
            WIDTH
        ):
            color = base

            # Outer synthetic package border.
            if (
                x < 8
                or x >= WIDTH - 8
                or y < 8
                or y >= HEIGHT - 8
            ):
                color = dark

            # Main label band.
            if (
                band_y
                <= y
                < band_y + 38
            ):
                color = accent

            # Vertical design stripe.
            if (
                stripe_x
                <= x
                < stripe_x + 18
            ):
                color = dark

            # Synthetic centered logo block.
            if (
                82
                <= x
                < 174
                and 104
                <= y
                < 164
            ):
                color = accent

            if (
                94
                <= x
                < 162
                and 116
                <= y
                < 152
            ):
                color = dark

            # Deterministic pseudo-barcode.
            if (
                188
                <= y
                < 230
                and 28
                <= x
                < 228
            ):
                index = (
                    (
                        x - 28
                    )
                    // 5
                )

                byte = digest[
                    index
                    % len(
                        digest
                    )
                ]

                bit = (
                    byte
                    >> (
                        index
                        % 8
                    )
                ) & 1

                if bit:
                    color = black
                else:
                    color = white

            pixels.extend(
                (
                    color[0],
                    color[1],
                    color[2],
                    255,
                )
            )

    return pixels


def main():
    pack = json.loads(
        SKU_PACK_PATH.read_text(
            encoding="utf-8"
        )
    )

    TEXTURE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated = []

    for sku in pack[
        "skus"
    ]:
        sku_id = sku[
            "sku_id"
        ]

        filename = (
            sku_id
            + ".png"
        )

        path = (
            TEXTURE_DIRECTORY
            / filename
        )

        write_rgba_png(
            path,
            WIDTH,
            HEIGHT,
            texture_pixels(
                sku
            ),
        )

        relative = (
            "examples/retail_demo/"
            "textures/"
            + filename
        )

        sku[
            "visual"
        ][
            "texture"
        ] = relative

        generated.append(
            path
        )

        print(
            "texture="
            + sku_id
            + " path="
            + relative
        )

    SKU_PACK_PATH.write_text(
        json.dumps(
            pack,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    hashes = {
        hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path
        in generated
    }

    assert len(
        generated
    ) == 8

    assert len(
        hashes
    ) == 8

    print(
        "texture_count=8"
    )

    print(
        "unique_texture_hashes=8"
    )

    print(
        "texture_resolution=256x256"
    )

    print(
        "BVT_RETAIL_SYNTHETIC_TEXTURES=OK"
    )


if __name__ == "__main__":
    main()
