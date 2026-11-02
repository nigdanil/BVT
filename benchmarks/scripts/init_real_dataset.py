import argparse
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[2]


DEFAULT_PLAN = (
    ROOT
    / "benchmarks"
    / "real"
    / "capture-plan-v0.1.json"
)


DEFAULT_ROOT = (
    ROOT
    / "benchmarks"
    / "real"
    / "data-v0.1"
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
    )

    args = parser.parse_args()

    plan = json.loads(
        args.plan.read_text(
            encoding="utf-8"
        )
    )

    root = (
        args.root.resolve()
    )


    for name in (
        "images",
        "labels",
        "sessions",
        "splits",
    ):
        (
            root
            / name
        ).mkdir(
            parents=True,
            exist_ok=True,
        )


    classes_source = (
        ROOT
        / plan[
            "class_contract"
        ][
            "classes_file"
        ]
    )


    (
        root
        / "classes.txt"
    ).write_text(
        classes_source.read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
        newline="\n",
    )


    for session in plan[
        "sessions"
    ]:
        session_id = session[
            "session_id"
        ]

        (
            root
            / "images"
            / session_id
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            root
            / "labels"
            / session_id
        ).mkdir(
            parents=True,
            exist_ok=True,
        )


        manifest_path = (
            root
            / "sessions"
            / (
                session_id
                + ".json"
            )
        )


        if not manifest_path.exists():
            manifest = {
                "schema_version": (
                    "bvt-real-capture-session-1"
                ),
                "dataset_id": (
                    plan[
                        "dataset_id"
                    ]
                ),
                "session_id": (
                    session_id
                ),
                "split": (
                    session[
                        "split"
                    ]
                ),
                "status": "planned",
                "target_images": (
                    session[
                        "target_images"
                    ]
                ),
                "planned_environment": (
                    session[
                        "environment"
                    ]
                ),
                "planned_condition": (
                    session[
                        "condition"
                    ]
                ),
                "planned_camera": (
                    session[
                        "camera"
                    ]
                ),
                "capture": {
                    "started_at": None,
                    "ended_at": None,
                    "image_count": 0,
                    "device": {
                        "manufacturer": None,
                        "model": None
                    }
                },
                "scene_reset_confirmed": False,
                "privacy": {
                    "faces_present": False,
                    "license_plates_present": False,
                    "private_documents_present": False,
                    "gps_exif_removed": False
                },
                "annotation": {
                    "status": "not-started",
                    "review_status": "not-started"
                },
                "notes": None
            }

            manifest_path.write_text(
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )


    print(
        "real_dataset_root="
        + str(
            root
        )
    )

    print(
        "planned_sessions="
        + str(
            len(
                plan[
                    "sessions"
                ]
            )
        )
    )

    print(
        "BVT_REAL_DATASET_INITIALIZED=OK"
    )


if __name__ == "__main__":
    main()
