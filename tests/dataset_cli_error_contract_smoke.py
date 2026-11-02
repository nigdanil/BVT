import contextlib
import importlib.util
import io
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]

CLI_PATH = (
    ROOT
    / "tools"
    / "bvt.py"
)


spec = (
    importlib.util.spec_from_file_location(
        "bvt_dev_cli",
        CLI_PATH,
    )
)

module = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    module
)


missing_config = (
    ROOT
    / ".tmp"
    / "definitely-missing-ep5-config.json"
)


if missing_config.exists():
    missing_config.unlink()


stdout = io.StringIO()
stderr = io.StringIO()


original_argv = list(
    sys.argv
)


try:
    sys.argv = [
        "bvt",
        "--blender",
        bpy.app.binary_path,
        "dataset",
        "--config",
        str(
            missing_config
        ),
    ]

    with (
        contextlib.redirect_stdout(
            stdout
        ),
        contextlib.redirect_stderr(
            stderr
        ),
    ):
        exit_code = (
            module.main()
        )

finally:
    sys.argv = (
        original_argv
    )


output = (
    stdout.getvalue()
    + stderr.getvalue()
)


assert exit_code == 1

assert (
    "ERROR_SCHEMA=bvt-cli-error-1"
    in output
)

assert (
    "ERROR_CODE=INPUT_NOT_FOUND"
    in output
)

assert (
    "ERROR_MESSAGE="
    in output
)

assert (
    "BVT_DATASET=FAIL"
    in output
)

assert (
    "Traceback (most recent call last):"
    not in output
)


print(
    "error_schema=bvt-cli-error-1"
)

print(
    "missing_input_code=INPUT_NOT_FOUND"
)

print(
    "error_message_present=True"
)

print(
    "traceback_exposed=False"
)

print(
    "BVT_DATASET_CLI_ERROR_CONTRACT=OK"
)

print(
    "RESULT=PASS"
)
