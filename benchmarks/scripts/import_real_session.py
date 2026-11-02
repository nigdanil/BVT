import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from real_dataset_validator import (
    check_no_gps,
    sha256_file,
)


SCRIPT_DIR = Path(
    __file__
).resolve().parent


ROOT = (
    SCRIPT_DIR
    .parents[1]
)


DEFAULT_PLAN = (
    ROOT
    / "benchmarks"
    / "real"
    / "capture-plan-v0.1.json"
)


DEFAULT_DATASET_ROOT = (
    ROOT
    / "benchmarks"
    / "real"
    / "data-v0.1"
)


IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
}


def load_json(
    path,
):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_json(
    path,
    data,
):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--session",
        required=True,
    )

    parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
    )

    args = parser.parse_args()


    source = (
        args.source
        .resolve()
    )

    data_root = (
        args.root
        .resolve()
    )

    plan_path = (
        args.plan
        .resolve()
    )


    if not source.is_dir():
        raise RuntimeError(
            "Source directory does not exist: "
            + str(
                source
            )
        )


    plan = load_json(
        plan_path
    )


    session_specs = {
        item[
            "session_id"
        ]: item
        for item
        in plan[
            "sessions"
        ]
    }


    if (
        args.session
        not in session_specs
    ):
        raise RuntimeError(
            "Unknown session: "
            + args.session
        )


    spec = session_specs[
        args.session
    ]


    expected_count = spec[
        "target_images"
    ]


    source_images = sorted(
        path
        for path
        in source.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_SUFFIXES
        )
    )


    if (
        len(
            source_images
        )
        != expected_count
    ):
        raise RuntimeError(
            "Session "
            + args.session
            + " requires exactly "
            + str(
                expected_count
            )
            + " images; found "
            + str(
                len(
                    source_images
                )
            )
        )


    destination = (
        data_root
        / "images"
        / args.session
    )


    destination.mkdir(
        parents=True,
        exist_ok=True,
    )


    existing = [
        path
        for path
        in destination.iterdir()
        if path.is_file()
    ]


    if existing:
        raise RuntimeError(
            "Destination is not empty: "
            + str(
                destination
            )
        )


    session_manifest_path = (
        data_root
        / "sessions"
        / (
            args.session
            + ".json"
        )
    )


    if not session_manifest_path.is_file():
        raise RuntimeError(
            "Session manifest missing: "
            + str(
                session_manifest_path
            )
        )


    import_dir = (
        data_root
        / "imports"
    )


    import_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


    staging_root = (
        data_root
        / ".import-staging"
        / args.session
    )


    if staging_root.exists():
        shutil.rmtree(
            staging_root
        )


    staging_root.mkdir(
        parents=True,
        exist_ok=True,
    )


    records = []


    try:
        for index, source_path in enumerate(
            source_images,
            start=1,
        ):
            try:
                with Image.open(
                    source_path
                ) as image:
                    image.verify()

            except Exception as exc:
                raise RuntimeError(
                    "Unreadable image: "
                    + str(
                        source_path
                    )
                ) from exc


            check_no_gps(
                source_path
            )


            suffix = (
                source_path
                .suffix
                .lower()
            )


            destination_name = (
                args.session
                + "_"
                + f"{index:04d}"
                + suffix
            )


            staged_path = (
                staging_root
                / destination_name
            )


            shutil.copy2(
                source_path,
                staged_path,
            )


            source_sha = (
                sha256_file(
                    source_path
                )
            )


            copied_sha = (
                sha256_file(
                    staged_path
                )
            )


            if (
                source_sha
                != copied_sha
            ):
                raise RuntimeError(
                    "Copy SHA mismatch: "
                    + str(
                        source_path
                    )
                )


            records.append(
                {
                    "source_name": (
                        source_path.name
                    ),
                    "source_sha256": (
                        source_sha
                    ),
                    "destination": (
                        (
                            Path(
                                "images"
                            )
                            / args.session
                            / destination_name
                        ).as_posix()
                    ),
                    "destination_sha256": (
                        copied_sha
                    ),
                    "size_bytes": (
                        staged_path
                        .stat()
                        .st_size
                    ),
                }
            )


        for staged_path in sorted(
            staging_root.iterdir()
        ):
            shutil.move(
                str(
                    staged_path
                ),
                str(
                    destination
                    / staged_path.name
                ),
            )


    finally:
        if staging_root.exists():
            shutil.rmtree(
                staging_root
            )


    import_manifest = {
        "schema_version": (
            "bvt-real-session-import-1"
        ),
        "dataset_id": (
            plan[
                "dataset_id"
            ]
        ),
        "session_id": (
            args.session
        ),
        "split": (
            spec[
                "split"
            ]
        ),
        "source_directory": (
            str(
                source
            )
        ),
        "image_count": (
            len(
                records
            )
        ),
        "byte_preserving_copy": True,
        "gps_exif_images": 0,
        "records": records,
    }


    import_manifest_path = (
        import_dir
        / (
            args.session
            + "-import.json"
        )
    )


    write_json(
        import_manifest_path,
        import_manifest,
    )


    session_manifest = load_json(
        session_manifest_path
    )


    session_manifest[
        "status"
    ] = "captured-unannotated"


    session_manifest[
        "capture"
    ][
        "image_count"
    ] = len(
        records
    )


    session_manifest[
        "capture"
    ][
        "imported_at"
    ] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    session_manifest[
        "capture"
    ][
        "import_manifest"
    ] = (
        (
            Path(
                "imports"
            )
            / import_manifest_path.name
        ).as_posix()
    )


    write_json(
        session_manifest_path,
        session_manifest,
    )


    print(
        "session="
        + args.session
    )

    print(
        "imported_images="
        + str(
            len(
                records
            )
        )
    )

    print(
        "byte_preserving_copy=True"
    )

    print(
        "gps_exif_images=0"
    )

    print(
        "session_status=captured-unannotated"
    )

    print(
        "BVT_REAL_SESSION_IMPORT=OK"
    )


if __name__ == "__main__":
    main()
