import hashlib
import json
from pathlib import Path

from ..core.constants import (
    DATASET_HASHES_SCHEMA_VERSION,
)


HASH_ALGORITHM = "sha256"

HASHES_FILENAME = "hashes.json"


def sha256_file(
    path,
):
    path = Path(
        path
    )

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


def _dataset_files(
    dataset_directory,
):
    dataset_directory = Path(
        dataset_directory
    )

    files = []

    for path in (
        dataset_directory.rglob(
            "*"
        )
    ):
        if not path.is_file():
            continue

        relative = (
            path.relative_to(
                dataset_directory
            ).as_posix()
        )

        if (
            relative
            == HASHES_FILENAME
        ):
            continue

        files.append(
            (
                relative,
                path,
            )
        )

    return sorted(
        files,
        key=lambda item: (
            item[0]
        ),
    )


def build_dataset_hashes(
    dataset_directory,
):
    dataset_directory = Path(
        dataset_directory
    )

    records = []

    for relative, path in (
        _dataset_files(
            dataset_directory
        )
    ):
        records.append(
            {
                "path": relative,
                "size_bytes": (
                    path.stat().st_size
                ),
                "sha256": (
                    sha256_file(
                        path
                    )
                ),
            }
        )

    return {
        "schema_version": (
            DATASET_HASHES_SCHEMA_VERSION
        ),
        "algorithm": (
            HASH_ALGORITHM
        ),
        "files": records,
    }


def write_dataset_hashes(
    path,
    hashes,
):
    path = Path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            hashes,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path


def verify_dataset_hashes(
    dataset_directory,
    hashes_path=None,
):
    dataset_directory = Path(
        dataset_directory
    )

    if hashes_path is None:
        hashes_path = (
            dataset_directory
            / HASHES_FILENAME
        )

    hashes_path = Path(
        hashes_path
    )

    errors = []

    if not hashes_path.is_file():
        return {
            "status": "FAIL",
            "errors": [
                {
                    "code": (
                        "hashes_file_missing"
                    ),
                    "path": str(
                        hashes_path
                    ),
                }
            ],
        }

    try:
        data = json.loads(
            hashes_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "status": "FAIL",
            "errors": [
                {
                    "code": (
                        "hashes_invalid_json"
                    ),
                    "message": str(
                        exc
                    ),
                }
            ],
        }

    if (
        data.get(
            "schema_version"
        )
        != DATASET_HASHES_SCHEMA_VERSION
    ):
        errors.append(
            {
                "code": (
                    "hashes_schema_mismatch"
                ),
            }
        )

    if (
        data.get(
            "algorithm"
        )
        != HASH_ALGORITHM
    ):
        errors.append(
            {
                "code": (
                    "hashes_algorithm_mismatch"
                ),
            }
        )

    records = list(
        data.get(
            "files",
            [],
        )
    )

    declared_paths = {
        str(
            item.get(
                "path",
                ""
            )
        )
        for item
        in records
    }

    actual_paths = {
        relative
        for relative, _
        in _dataset_files(
            dataset_directory
        )
    }

    missing_from_hashes = (
        actual_paths
        - declared_paths
    )

    stale_hash_entries = (
        declared_paths
        - actual_paths
    )

    for relative in sorted(
        missing_from_hashes
    ):
        errors.append(
            {
                "code": (
                    "file_not_hashed"
                ),
                "path": relative,
            }
        )

    for relative in sorted(
        stale_hash_entries
    ):
        errors.append(
            {
                "code": (
                    "hashed_file_missing"
                ),
                "path": relative,
            }
        )

    for item in records:
        relative = str(
            item.get(
                "path",
                ""
            )
        )

        if (
            not relative
            or relative
            in stale_hash_entries
        ):
            continue

        path = (
            dataset_directory
            / Path(
                relative
            )
        )

        actual_size = (
            path.stat().st_size
        )

        if (
            actual_size
            != item.get(
                "size_bytes"
            )
        ):
            errors.append(
                {
                    "code": (
                        "file_size_mismatch"
                    ),
                    "path": relative,
                }
            )

        actual_hash = (
            sha256_file(
                path
            )
        )

        if (
            actual_hash
            != item.get(
                "sha256"
            )
        ):
            errors.append(
                {
                    "code": (
                        "file_hash_mismatch"
                    ),
                    "path": relative,
                }
            )

    return {
        "status": (
            "PASS"
            if not errors
            else "FAIL"
        ),
        "errors": errors,
        "files": len(
            records
        ),
    }
