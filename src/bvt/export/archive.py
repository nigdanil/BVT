from pathlib import Path
import zipfile


ARCHIVE_ROOT = "dataset"

FIXED_ZIP_TIMESTAMP = (
    1980,
    1,
    1,
    0,
    0,
    0,
)


def export_dataset_zip(
    dataset_directory,
    archive_path,
):
    dataset_directory = Path(
        dataset_directory
    )

    archive_path = Path(
        archive_path
    )

    if not dataset_directory.is_dir():
        raise ValueError(
            "Dataset directory does not exist"
        )

    archive_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        (
            path
            for path
            in dataset_directory.rglob(
                "*"
            )
            if path.is_file()
        ),
        key=lambda path: (
            path.relative_to(
                dataset_directory
            ).as_posix()
        ),
    )

    if not files:
        raise ValueError(
            "Dataset directory is empty"
        )

    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=(
            zipfile.ZIP_DEFLATED
        ),
        compresslevel=9,
    ) as archive:
        for path in files:
            relative = (
                path.relative_to(
                    dataset_directory
                ).as_posix()
            )

            archive_name = (
                f"{ARCHIVE_ROOT}/"
                f"{relative}"
            )

            info = zipfile.ZipInfo(
                archive_name,
                date_time=(
                    FIXED_ZIP_TIMESTAMP
                ),
            )

            info.compress_type = (
                zipfile.ZIP_DEFLATED
            )

            info.create_system = 3

            info.external_attr = (
                0o100644
                << 16
            )

            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=(
                    zipfile.ZIP_DEFLATED
                ),
                compresslevel=9,
            )

    return archive_path
