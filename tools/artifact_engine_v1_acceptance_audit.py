import array
import hashlib
import json
import math
import random
from pathlib import Path

import bpy


ROOT = Path.cwd()

FIRST = (
    ROOT
    / ".tmp"
    / "artifact-engine-v1-acceptance-first"
)

SECOND = (
    ROOT
    / ".tmp"
    / "artifact-engine-v1-acceptance"
    / "dataset"
)

BASE_SEED = 24681357


EXPECTED_ORDER = [
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
    "jpeg_compression",
]


EXPECTED_CATEGORY = {
    "over_exposure": "lighting",
    "reflection": "glass",
    "fingerprints": "glass",
    "condensation": "glass",
    "frost": "glass",
    "dust": "glass",
    "water_drops": "glass",
    "scratches": "glass",
    "motion_blur": "camera",
    "noise": "sensor",
    "jpeg_compression": "compression",
}


EXPECTED_STAGE = {
    "over_exposure": "pre_render",
    "reflection": "pre_render",
    "fingerprints": "pre_render",
    "condensation": "pre_render",
    "frost": "pre_render",
    "dust": "pre_render",
    "water_drops": "pre_render",
    "scratches": "pre_render",
    "motion_blur": "post_render",
    "noise": "post_render",
    "jpeg_compression": "post_render",
}


EXPECTED_EXECUTION_ORDER = {
    "over_exposure": 100,
    "reflection": 100,
    "fingerprints": 110,
    "condensation": 120,
    "frost": 130,
    "dust": 140,
    "water_drops": 150,
    "scratches": 160,
    "motion_blur": 50,
    "noise": 100,
    "jpeg_compression": 200,
}


EXPECTED_FIELDS = {
    "artifact",
    "category",
    "description",
    "stage",
    "execution_order",
    "enabled",
    "probability",
    "intensity",
    "options",
    "seed",
    "decision_roll",
    "applied",
    "affected_objects",
    "affected_camera",
    "affected_materials",
    "parameters",
    "compatibility_rules",
}


EXPECTED_GLASS_INPUTS = {
    "condensation": "fingerprints",
    "frost": "condensation",
    "dust": "frost",
    "water_drops": "dust",
    "scratches": "water_drops",
}


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def stable_seed(payload):
    digest = hashlib.sha256(
        payload.encode(
            "utf-8"
        )
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
    return stable_seed(
        f"bvt:{base_seed}:{frame_index}"
    )


def derive_subseed(
    parent_seed,
    namespace,
    identity="",
):
    return stable_seed(
        (
            f"bvt:{parent_seed}:"
            f"{namespace}:{identity}"
        )
    )


def sha256_file(path):
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


def load_pixels(path):
    image = bpy.data.images.load(
        str(path),
        check_existing=False,
    )

    try:
        pixels = list(
            image.pixels[:]
        )

        return (
            tuple(
                image.size
            ),
            pixels,
        )

    finally:
        bpy.data.images.remove(
            image
        )


def decoded_hash(
    pixels,
):
    values = array.array(
        "f",
        pixels,
    )

    return hashlib.sha256(
        values.tobytes()
    ).hexdigest()


def compare_decoded(
    first_path,
    second_path,
):
    first_size, first_pixels = (
        load_pixels(
            first_path
        )
    )

    second_size, second_pixels = (
        load_pixels(
            second_path
        )
    )

    assert (
        first_size
        == second_size
    )

    assert len(
        first_pixels
    ) == len(
        second_pixels
    )

    squared_error = 0.0
    max_error = 0.0
    changed_components = 0

    for left, right in zip(
        first_pixels,
        second_pixels,
    ):
        difference = abs(
            left - right
        )

        if difference != 0.0:
            changed_components += 1

        squared_error += (
            difference
            * difference
        )

        max_error = max(
            max_error,
            difference,
        )

    return {
        "rmse": math.sqrt(
            squared_error
            / len(
                first_pixels
            )
        ),
        "max_error": max_error,
        "changed_components": (
            changed_components
        ),
        "decoded_hash": (
            decoded_hash(
                second_pixels
            )
        ),
    }


def artifact_by_id(
    frame,
    artifact_id,
):
    return next(
        item
        for item
        in frame[
            "artifacts"
        ][
            "artifacts"
        ]
        if item[
            "artifact"
        ] == artifact_id
    )


def node_change(
    artifact,
):
    changes = (
        artifact[
            "parameters"
        ].get(
            "material_changes",
            [],
        )
    )

    assert len(
        changes
    ) == 1

    nodes = changes[
        0
    ].get(
        "nodes",
        [],
    )

    assert len(
        nodes
    ) == 1

    return nodes[
        0
    ]


# =========================================================
# Dataset existence
# =========================================================

assert FIRST.is_dir(), FIRST
assert SECOND.is_dir(), SECOND


# =========================================================
# Manifest reproducibility
# =========================================================

first_manifest_bytes = (
    FIRST
    / "manifest.json"
).read_bytes()

second_manifest_bytes = (
    SECOND
    / "manifest.json"
).read_bytes()


assert (
    first_manifest_bytes
    == second_manifest_bytes
)


manifest = json.loads(
    second_manifest_bytes.decode(
        "utf-8"
    )
)


frames = manifest[
    "frames"
]


assert len(
    frames
) == 3


assert (
    manifest[
        "generation"
    ][
        "seed"
    ]
    == BASE_SEED
)

assert (
    manifest[
        "generation"
    ][
        "frame_seed_strategy"
    ]
    == "sha256-v1"
)


# =========================================================
# Engine + provider contract
# =========================================================

provider_seeds = {
    artifact_id: []
    for artifact_id
    in EXPECTED_ORDER
}


for frame_index, frame in enumerate(
    frames,
    start=1,
):
    expected_frame_seed = (
        derive_frame_seed(
            BASE_SEED,
            frame_index,
        )
    )

    assert (
        frame[
            "frame_seed"
        ]
        == expected_frame_seed
    )

    engine = frame[
        "artifacts"
    ]

    assert (
        engine[
            "enabled"
        ]
        is True
    )

    assert (
        engine[
            "version"
        ]
        == "artifact-engine-v1"
    )

    records = engine[
        "artifacts"
    ]

    assert len(
        records
    ) == 11

    assert [
        record[
            "artifact"
        ]
        for record
        in records
    ] == EXPECTED_ORDER

    for record in records:
        artifact_id = record[
            "artifact"
        ]

        assert (
            set(
                record
            )
            == EXPECTED_FIELDS
        )

        assert (
            record[
                "category"
            ]
            == EXPECTED_CATEGORY[
                artifact_id
            ]
        )

        assert (
            record[
                "stage"
            ]
            == EXPECTED_STAGE[
                artifact_id
            ]
        )

        assert (
            record[
                "execution_order"
            ]
            == EXPECTED_EXECUTION_ORDER[
                artifact_id
            ]
        )

        assert (
            record[
                "enabled"
            ]
            is True
        )

        assert (
            record[
                "probability"
            ]
            == 1.0
        )

        assert (
            record[
                "applied"
            ]
            is True
        )

        expected_seed = (
            derive_subseed(
                expected_frame_seed,
                "artifact",
                artifact_id,
            )
        )

        assert (
            record[
                "seed"
            ]
            == expected_seed
        )

        expected_roll = random.Random(
            expected_seed
        ).random()

        assert abs(
            record[
                "decision_roll"
            ]
            - expected_roll
        ) <= 1e-15

        provider_seeds[
            artifact_id
        ].append(
            expected_seed
        )

    for (
        artifact_id,
        expected_input,
    ) in (
        EXPECTED_GLASS_INPUTS.items()
    ):
        node = node_change(
            artifact_by_id(
                frame,
                artifact_id,
            )
        )

        assert (
            node[
                "input_mode"
            ]
            == expected_input
        )


for artifact_id, seeds in (
    provider_seeds.items()
):
    assert len(
        set(
            seeds
        )
    ) == 3, artifact_id


# =========================================================
# Label reproducibility
# =========================================================

first_labels = sorted(
    (
        FIRST
        / "labels"
    ).glob(
        "*.txt"
    )
)

second_labels = sorted(
    (
        SECOND
        / "labels"
    ).glob(
        "*.txt"
    )
)


assert len(
    first_labels
) == 3

assert len(
    second_labels
) == 3


first_label_hashes = [
    sha256_file(
        path
    )
    for path
    in first_labels
]

second_label_hashes = [
    sha256_file(
        path
    )
    for path
    in second_labels
]


assert (
    first_label_hashes
    == second_label_hashes
)


# Fixed camera / geometry / placement.
assert (
    len(
        set(
            second_label_hashes
        )
    )
    == 1
)


# =========================================================
# Decoded image reproducibility
# =========================================================

first_images = sorted(
    (
        FIRST
        / "images"
    ).glob(
        "*.png"
    )
)

second_images = sorted(
    (
        SECOND
        / "images"
    ).glob(
        "*.png"
    )
)


assert len(
    first_images
) == 3

assert len(
    second_images
) == 3


png_byte_equal = []
decoded_results = []


for first, second in zip(
    first_images,
    second_images,
):
    with second.open(
        "rb"
    ) as stream:
        assert (
            stream.read(
                8
            )
            == PNG_SIGNATURE
        )

    png_byte_equal.append(
        sha256_file(
            first
        )
        == sha256_file(
            second
        )
    )

    comparison = compare_decoded(
        first,
        second,
    )

    assert (
        comparison[
            "rmse"
        ]
        == 0.0
    )

    assert (
        comparison[
            "max_error"
        ]
        == 0.0
    )

    assert (
        comparison[
            "changed_components"
        ]
        == 0
    )

    decoded_results.append(
        comparison
    )


decoded_hashes = [
    item[
        "decoded_hash"
    ]
    for item
    in decoded_results
]


# Different frame seeds must produce actual
# image variation across the acceptance dataset.
assert (
    len(
        set(
            decoded_hashes
        )
    )
    > 1
)


# =========================================================
# Validation
# =========================================================

validation = json.loads(
    (
        SECOND
        / "validation.json"
    ).read_text(
        encoding="utf-8"
    )
)

assert (
    validation[
        "status"
    ]
    == "PASS"
)


# =========================================================
# Result
# =========================================================

print(
    "BVT_ARTIFACT_ENGINE_V1_ACCEPTANCE=OK"
)

print(
    "frames=",
    len(
        frames
    ),
)

print(
    "providers_per_frame=11"
)

print(
    "all_providers_applied=True"
)

print(
    "engine_version=artifact-engine-v1"
)

print(
    "manifest_fields=",
    len(
        EXPECTED_FIELDS
    ),
)

print(
    "manifest_bytes_equal=True"
)

print(
    "label_hashes_equal=True"
)

print(
    "unique_label_hashes=",
    len(
        set(
            second_label_hashes
        )
    ),
)

print(
    "decoded_pixels_exact=True"
)

print(
    "decoded_rmse=",
    [
        item[
            "rmse"
        ]
        for item
        in decoded_results
    ],
)

print(
    "decoded_max_error=",
    [
        item[
            "max_error"
        ]
        for item
        in decoded_results
    ],
)

print(
    "unique_decoded_images=",
    len(
        set(
            decoded_hashes
        )
    ),
)

print(
    "png_bytes_equal=",
    png_byte_equal,
)

print(
    "glass_chain="
    "fingerprints>"
    "condensation>"
    "frost>"
    "dust>"
    "water_drops>"
    "scratches"
)

print(
    "post_render_chain="
    "motion_blur>noise>jpeg_compression"
)

print(
    "validation_status=",
    validation[
        "status"
    ],
)

print(
    "output_format=PNG"
)

print(
    "RESULT=PASS"
)
