import hashlib


FRAME_SEED_STRATEGY = "sha256-v1"
SUBSEED_STRATEGY = "sha256-namespace-v1"


def _stable_seed(payload):
    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).digest()

    return (
        int.from_bytes(
            digest[:8],
            byteorder="big",
            signed=False,
        )
        & 0x7FFFFFFF
    )


def derive_frame_seed(
    base_seed,
    frame_index,
):
    if frame_index < 1:
        raise ValueError(
            "Frame index must start from 1"
        )

    return _stable_seed(
        f"bvt:{base_seed}:{frame_index}"
    )


def derive_subseed(
    parent_seed,
    namespace,
    identity="",
):
    namespace = str(namespace).strip()

    if not namespace:
        raise ValueError(
            "Seed namespace cannot be empty"
        )

    return _stable_seed(
        (
            f"bvt:{parent_seed}:"
            f"{namespace}:{identity}"
        )
    )
