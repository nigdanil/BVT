import hashlib
import struct
import zlib


PNG_SIGNATURE = (
    b"\x89PNG\r\n\x1a\n"
)


def _paeth(
    a,
    b,
    c,
):
    p = (
        a
        + b
        - c
    )

    pa = abs(
        p - a
    )

    pb = abs(
        p - b
    )

    pc = abs(
        p - c
    )

    if (
        pa <= pb
        and pa <= pc
    ):
        return a

    if pb <= pc:
        return b

    return c


def decoded_png_bytes(
    path,
):
    data = path.read_bytes()

    if (
        data[:8]
        != PNG_SIGNATURE
    ):
        raise ValueError(
            f"Not a PNG file: {path}"
        )

    offset = 8

    ihdr = None
    idat_parts = []


    while offset < len(
        data
    ):
        length = struct.unpack(
            ">I",
            data[
                offset:
                offset + 4
            ],
        )[0]

        chunk_type = data[
            offset + 4:
            offset + 8
        ]

        chunk_data = data[
            offset + 8:
            offset + 8 + length
        ]

        offset += (
            length
            + 12
        )


        if (
            chunk_type
            == b"IHDR"
        ):
            ihdr = struct.unpack(
                ">IIBBBBB",
                chunk_data,
            )

        elif (
            chunk_type
            == b"IDAT"
        ):
            idat_parts.append(
                chunk_data
            )

        elif (
            chunk_type
            == b"IEND"
        ):
            break


    if ihdr is None:
        raise ValueError(
            f"PNG has no IHDR: {path}"
        )


    (
        width,
        height,
        bit_depth,
        color_type,
        compression,
        filter_method,
        interlace,
    ) = ihdr


    if bit_depth != 8:
        raise ValueError(
            (
                "Only 8-bit PNG is supported: "
                f"{bit_depth}"
            )
        )

    if compression != 0:
        raise ValueError(
            "Unsupported PNG compression"
        )

    if filter_method != 0:
        raise ValueError(
            "Unsupported PNG filter method"
        )

    if interlace != 0:
        raise ValueError(
            "Interlaced PNG is not supported"
        )


    channels_by_type = {
        0: 1,
        2: 3,
        4: 2,
        6: 4,
    }


    if (
        color_type
        not in channels_by_type
    ):
        raise ValueError(
            (
                "Unsupported PNG color type: "
                f"{color_type}"
            )
        )


    channels = (
        channels_by_type[
            color_type
        ]
    )

    bytes_per_pixel = channels

    stride = (
        width
        * channels
    )


    filtered = zlib.decompress(
        b"".join(
            idat_parts
        )
    )


    expected_size = (
        height
        * (
            stride
            + 1
        )
    )


    if (
        len(
            filtered
        )
        != expected_size
    ):
        raise ValueError(
            "Unexpected decoded PNG size"
        )


    output = bytearray()

    previous = bytearray(
        stride
    )

    cursor = 0


    for _ in range(
        height
    ):
        filter_type = (
            filtered[
                cursor
            ]
        )

        cursor += 1

        source = filtered[
            cursor:
            cursor + stride
        ]

        cursor += stride


        row = bytearray(
            stride
        )


        for index, value in enumerate(
            source
        ):
            left = (
                row[
                    index
                    - bytes_per_pixel
                ]
                if (
                    index
                    >= bytes_per_pixel
                )
                else 0
            )

            up = previous[
                index
            ]

            upper_left = (
                previous[
                    index
                    - bytes_per_pixel
                ]
                if (
                    index
                    >= bytes_per_pixel
                )
                else 0
            )


            if filter_type == 0:
                result = value

            elif filter_type == 1:
                result = (
                    value
                    + left
                ) & 0xFF

            elif filter_type == 2:
                result = (
                    value
                    + up
                ) & 0xFF

            elif filter_type == 3:
                result = (
                    value
                    + (
                        (
                            left
                            + up
                        )
                        // 2
                    )
                ) & 0xFF

            elif filter_type == 4:
                result = (
                    value
                    + _paeth(
                        left,
                        up,
                        upper_left,
                    )
                ) & 0xFF

            else:
                raise ValueError(
                    (
                        "Unsupported PNG row "
                        f"filter: {filter_type}"
                    )
                )


            row[
                index
            ] = result


        output.extend(
            row
        )

        previous = row


    return bytes(
        output
    )


def decoded_png_hash(
    path,
):
    return hashlib.sha256(
        decoded_png_bytes(
            path
        )
    ).hexdigest()
