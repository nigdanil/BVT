import json
import random
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(
    __file__
).resolve().parent


sys.path.insert(
    0,
    str(
        SCRIPT_DIR
    ),
)


from PIL import Image

from real_dataset_validator import (
    ValidationError,
    validate_dataset,
)


ROOT = Path.cwd()

TMP = (
    ROOT
    / ".tmp"
    / "ep7-real-validator-selftest"
)


if TMP.exists():
    shutil.rmtree(
        TMP
    )


TMP.mkdir(
    parents=True,
)


data_root = (
    TMP
    / "data"
)


for directory in (
    "images",
    "labels",
    "sessions",
    "splits",
):
    (
        data_root
        / directory
    ).mkdir(
        parents=True,
    )


(
    data_root
    / "classes.txt"
).write_text(
    "test_class\n",
    encoding="utf-8",
)


sessions = [
    {
        "session_id": "T01",
        "split": "train",
        "target_images": 2,
    },
    {
        "session_id": "V01",
        "split": "validation",
        "target_images": 2,
    },
    {
        "session_id": "X01",
        "split": "test",
        "target_images": 2,
    },
]


plan = {
    "schema_version": (
        "bvt-real-dataset-capture-plan-1"
    ),
    "dataset_id": "selftest",
    "dataset_version": "0.0",
    "class_contract": {
        "class_count": 1,
        "classes_file": (
            ".tmp/"
            "ep7-real-validator-selftest/"
            "classes-reference.txt"
        ),
    },
    "leakage_policy": {
        "near_duplicate_hamming_threshold": 4
    },
    "minimum_class_instances_by_split": {
        "train": 1,
        "validation": 1,
        "test": 1
    },
    "sessions": sessions,
}


reference_classes = (
    TMP
    / "classes-reference.txt"
)


reference_classes.write_text(
    "test_class\n",
    encoding="utf-8",
)


plan_path = (
    TMP
    / "plan.json"
)


plan_path.write_text(
    json.dumps(
        plan,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


def make_image(
    path,
    seed,
):
    rng = random.Random(
        seed
    )

    image = Image.new(
        "RGB",
        (
            64,
            64,
        ),
    )

    pixels = []


    for _ in range(
        64
        * 64
    ):
        pixels.append(
            (
                rng.randrange(
                    256
                ),
                rng.randrange(
                    256
                ),
                rng.randrange(
                    256
                ),
            )
        )


    image.putdata(
        pixels
    )

    image.save(
        path
    )


seed = 100


for session in sessions:
    session_id = session[
        "session_id"
    ]


    image_dir = (
        data_root
        / "images"
        / session_id
    )

    label_dir = (
        data_root
        / "labels"
        / session_id
    )


    image_dir.mkdir(
        parents=True,
    )

    label_dir.mkdir(
        parents=True,
    )


    for index in range(
        2
    ):
        stem = (
            session_id
            + "_"
            + f"{index + 1:04d}"
        )


        make_image(
            image_dir
            / (
                stem
                + ".png"
            ),
            seed,
        )


        (
            label_dir
            / (
                stem
                + ".txt"
            )
        ).write_text(
            "0 0.5 0.5 0.5 0.5\n",
            encoding="utf-8",
        )


        seed += 1


    manifest = {
        "schema_version": (
            "bvt-real-capture-session-1"
        ),
        "dataset_id": "selftest",
        "session_id": (
            session_id
        ),
        "split": (
            session[
                "split"
            ]
        ),
    }


    (
        data_root
        / "sessions"
        / (
            session_id
            + ".json"
        )
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


evidence_path = (
    TMP
    / "evidence.json"
)


valid = validate_dataset(
    data_root,
    plan_path,
    evidence_path,
)


assert (
    valid[
        "total_images"
    ]
    == 6
)

assert (
    valid[
        "split_image_counts"
    ]
    == {
        "train": 2,
        "validation": 2,
        "test": 2,
    }
)

assert (
    valid[
        "exact_duplicates"
    ]
    == 0
)

assert (
    valid[
        "cross_split_near_duplicates"
    ]
    == 0
)


print(
    "validator_valid_dataset=PASS"
)


train_image = (
    data_root
    / "images"
    / "T01"
    / "T01_0001.png"
)


test_image = (
    data_root
    / "images"
    / "X01"
    / "X01_0001.png"
)


test_image.write_bytes(
    train_image.read_bytes()
)


duplicate_detected = False


try:
    validate_dataset(
        data_root,
        plan_path,
    )

except ValidationError:
    duplicate_detected = True


assert duplicate_detected


print(
    "validator_duplicate_detection=PASS"
)

print(
    "BVT_REAL_DATASET_VALIDATOR_SELFTEST=OK"
)
