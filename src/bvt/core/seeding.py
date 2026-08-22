import hashlib


FRAME_SEED_STRATEGY = "sha256-v1"


def derive_frame_seed(
    base_seed,
    frame_index,
):
    if frame_index < 1:
        raise ValueError(
            "Frame index must start from 1"
        )

    payload = (
        f"bvt:{base_seed}:{frame_index}"
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).digest()

    return (
        int.from_bytes(
            digest[:8],
            byteorder="big",
            signed=False,
        )
        & 0x7FFFFFFF
    )
