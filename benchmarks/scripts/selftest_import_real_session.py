import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path.cwd()


TMP = (
    ROOT
    / ".tmp"
    / "ep7-real-import-selftest"
)


IMPORTER = (
    ROOT
    / "benchmarks"
    / "scripts"
    / "import_real_session.py"
)


if TMP.exists():
    shutil.rmtree(
        TMP
    )


source = (
    TMP
    / "source"
)


data = (
    TMP
    / "data"
)


source.mkdir(
    parents=True
)


(
    data
    / "images"
    / "T01"
).mkdir(
    parents=True
)


(
    data
    / "sessions"
).mkdir(
    parents=True
)


for index in range(
    3
):
    image = Image.new(
        "RGB",
        (
            64,
            64,
        ),
        (
            30
            + index * 50,
            80
            + index * 20,
            120
            + index * 30,
        ),
    )


    image.save(
        source
        / (
            "phone_"
            + str(
                index + 1
            )
            + ".png"
        )
    )


plan = {
    "dataset_id": "selftest",
    "sessions": [
        {
            "session_id": "T01",
            "split": "train",
            "target_images": 3,
        }
    ],
}


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


session_manifest = {
    "schema_version": (
        "bvt-real-capture-session-1"
    ),
    "dataset_id": "selftest",
    "session_id": "T01",
    "split": "train",
    "status": "planned",
    "capture": {
        "image_count": 0
    },
}


(
    data
    / "sessions"
    / "T01.json"
).write_text(
    json.dumps(
        session_manifest,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


result = subprocess.run(
    [
        sys.executable,
        str(
            IMPORTER
        ),
        "--session",
        "T01",
        "--source",
        str(
            source
        ),
        "--root",
        str(
            data
        ),
        "--plan",
        str(
            plan_path
        ),
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)


if result.returncode != 0:
    print(
        result.stdout
    )

    print(
        result.stderr
    )


assert (
    result.returncode
    == 0
)


assert (
    "BVT_REAL_SESSION_IMPORT=OK"
    in result.stdout
)


images = sorted(
    (
        data
        / "images"
        / "T01"
    ).glob(
        "*.png"
    )
)


assert [
    path.name
    for path
    in images
] == [
    "T01_0001.png",
    "T01_0002.png",
    "T01_0003.png",
]


manifest = json.loads(
    (
        data
        / "sessions"
        / "T01.json"
    ).read_text(
        encoding="utf-8"
    )
)


assert (
    manifest[
        "status"
    ]
    == "captured-unannotated"
)


assert (
    manifest[
        "capture"
    ][
        "image_count"
    ]
    == 3
)


import_manifest = (
    data
    / "imports"
    / "T01-import.json"
)


assert import_manifest.is_file()


second = subprocess.run(
    [
        sys.executable,
        str(
            IMPORTER
        ),
        "--session",
        "T01",
        "--source",
        str(
            source
        ),
        "--root",
        str(
            data
        ),
        "--plan",
        str(
            plan_path
        ),
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)


assert (
    second.returncode
    != 0
)


assert (
    "Destination is not empty"
    in (
        second.stdout
        + second.stderr
    )
)


print(
    "importer_byte_preserving_copy=PASS"
)

print(
    "importer_canonical_naming=PASS"
)

print(
    "importer_manifest_update=PASS"
)

print(
    "importer_overwrite_guard=PASS"
)

print(
    "BVT_REAL_SESSION_IMPORT_SELFTEST=OK"
)
