#!/usr/bin/env python3

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src" / "bvt"
TESTS_DIR = ROOT / "tests"
RELEASES_DIR = ROOT / "releases"

CLI_VERSION = "0.1.0"
CLI_ERROR_SCHEMA = "bvt-cli-error-1"


def _version_key(path):
    match = re.search(
        r"Blender[ _-](\d+(?:\.\d+)*)",
        str(path.parent),
        re.IGNORECASE,
    )

    if not match:
        return ()

    return tuple(
        int(part)
        for part in match.group(1).split(".")
    )


def find_blender(explicit=None):
    candidates = []

    if explicit:
        candidates.append(
            Path(explicit)
        )

    env_path = os.environ.get(
        "BVT_BLENDER"
    )

    if env_path:
        candidates.append(
            Path(env_path)
        )

    which = shutil.which(
        "blender"
    )

    if which:
        candidates.append(
            Path(which)
        )

    program_roots = []

    for env_name in (
        "ProgramFiles",
        "ProgramW6432",
    ):
        value = os.environ.get(
            env_name
        )

        if value:
            program_roots.append(
                Path(value)
            )

    # Standard Windows fallback.
    program_roots.append(
        Path(
            r"C:\Program Files"
        )
    )

    discovered = []

    for root in program_roots:
        blender_root = (
            root
            / "Blender Foundation"
        )

        if not blender_root.exists():
            continue

        discovered.extend(
            blender_root.glob(
                "Blender */blender.exe"
            )
        )

    discovered.sort(
        key=_version_key,
        reverse=True,
    )

    candidates.extend(
        discovered
    )

    seen = set()

    for candidate in candidates:
        try:
            candidate = (
                candidate
                .expanduser()
                .resolve()
            )
        except OSError:
            continue

        key = str(
            candidate
        ).lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        if candidate.is_file():
            return candidate

    raise RuntimeError(
        "Blender executable was not found. "
        "Use --blender PATH or set BVT_BLENDER."
    )


def run_process(
    command,
    *,
    cwd=ROOT,
    capture=False,
):
    if capture:
        return subprocess.run(
            [
                str(item)
                for item in command
            ],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    return subprocess.run(
        [
            str(item)
            for item in command
        ],
        cwd=str(cwd),
        check=False,
    )


def blender_version(
    blender,
):
    result = run_process(
        [
            blender,
            "--version",
        ],
        capture=True,
    )

    first_line = (
        result.stdout
        .splitlines()[0]
        if result.stdout
        else "unknown"
    )

    return first_line


def git_value(
    *args,
):
    result = run_process(
        [
            "git",
            *args,
        ],
        capture=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def find_test(
    query,
):
    query = query.strip()

    direct_candidates = [
        TESTS_DIR / query,
        TESTS_DIR / f"{query}.py",
        TESTS_DIR / f"{query}_smoke.py",
    ]

    for candidate in direct_candidates:
        if candidate.is_file():
            return candidate

    matches = sorted(
        TESTS_DIR.glob(
            f"*{query}*_smoke.py"
        )
    )

    if not matches:
        raise RuntimeError(
            f"No smoke test matches: {query}"
        )

    if len(matches) > 1:
        names = "\n".join(
            f"  - {path.name}"
            for path in matches
        )

        raise RuntimeError(
            "Test query is ambiguous:\n"
            f"{names}"
        )

    return matches[0]


def emit_cli_error(
    code,
    message,
):
    message = " ".join(
        str(
            message
        ).splitlines()
    ).strip()

    print(
        "ERROR_SCHEMA="
        + CLI_ERROR_SCHEMA
    )

    print(
        "ERROR_CODE="
        + str(
            code
        )
    )

    print(
        "ERROR_MESSAGE="
        + message
    )


def smoke_markers(
    output,
):
    markers = []

    for line in output.splitlines():
        stripped = line.strip()

        if (
            stripped.startswith("BVT_")
            or stripped.startswith(
                "RESULT="
            )
        ):
            markers.append(
                stripped
            )

    return markers


def run_smoke(
    blender,
    test_path,
    *,
    verbose=False,
):
    result = run_process(
        [
            blender,
            "--background",
            "--factory-startup",
            "--python",
            test_path,
        ],
        capture=True,
    )

    output = (
        result.stdout
        or ""
    )

    has_traceback = (
        "Traceback (most recent call last):"
        in output
    )

    success = (
        result.returncode == 0
        and not has_traceback
    )

    print(
        (
            "PASS"
            if success
            else "FAIL"
        ),
        test_path.relative_to(
            ROOT
        ),
    )

    for marker in smoke_markers(
        output
    )[-12:]:
        print(
            f"  {marker}"
        )

    if (
        verbose
        or not success
    ):
        if output:
            print(
                "\n".join(
                    output.splitlines()[
                        -160:
                    ]
                )
            )

    return success


def cmd_doctor(
    args,
):
    blender = find_blender(
        args.blender
    )

    tests = sorted(
        TESTS_DIR.glob(
            "*_smoke.py"
        )
    )

    print(
        f"BVT_CLI_VERSION={CLI_VERSION}"
    )

    print(
        f"ROOT={ROOT}"
    )

    print(
        f"PYTHON={sys.version.split()[0]}"
    )

    print(
        f"BLENDER={blender}"
    )

    print(
        "BLENDER_VERSION="
        + blender_version(
            blender
        )
    )

    print(
        "BRANCH="
        + str(
            git_value(
                "branch",
                "--show-current",
            )
        )
    )

    print(
        "HEAD="
        + str(
            git_value(
                "rev-parse",
                "HEAD",
            )
        )
    )

    print(
        f"SMOKE_COUNT={len(tests)}"
    )

    print(
        "SOURCE_DIR_EXISTS="
        f"{SOURCE_DIR.is_dir()}"
    )

    print(
        "BVT_DOCTOR=OK"
    )

    return 0


def cmd_test(
    args,
):
    blender = find_blender(
        args.blender
    )

    test_path = find_test(
        args.test
    )

    success = run_smoke(
        blender,
        test_path,
        verbose=args.verbose,
    )

    if success:
        print(
            "BVT_TEST=OK"
        )
        return 0

    print(
        "BVT_TEST=FAIL"
    )

    return 1


def cmd_regression(
    args,
):
    blender = find_blender(
        args.blender
    )

    tests = sorted(
        TESTS_DIR.glob(
            "*_smoke.py"
        )
    )

    passed = 0
    failed = []

    print(
        f"TOTAL={len(tests)}"
    )

    for index, test_path in enumerate(
        tests,
        start=1,
    ):
        print()
        print(
            f"[{index}/{len(tests)}] "
            f"{test_path.name}"
        )

        success = run_smoke(
            blender,
            test_path,
            verbose=args.verbose,
        )

        if success:
            passed += 1
        else:
            failed.append(
                test_path
            )

            if args.fail_fast:
                break

    print()
    print(
        "=========================================="
    )
    print(
        "REGRESSION SUMMARY"
    )
    print(
        "=========================================="
    )

    print(
        f"PASS={passed}"
    )

    print(
        f"FAIL={len(failed)}"
    )

    if failed:
        print(
            "FAILED_TESTS="
        )

        for path in failed:
            print(
                f"  {path.name}"
            )

        print(
            "BVT_REGRESSION=FAIL"
        )

        return 1

    print(
        "BVT_REGRESSION=OK"
    )

    return 0


def validate_extension(
    blender,
    target,
):
    result = run_process(
        [
            blender,
            "--command",
            "extension",
            "validate",
            target,
        ]
    )

    return result.returncode


def cmd_validate(
    args,
):
    blender = find_blender(
        args.blender
    )

    target = (
        Path(args.target)
        if args.target
        else SOURCE_DIR
    )

    if not target.is_absolute():
        target = (
            ROOT
            / target
        )

    target = target.resolve()

    print(
        f"VALIDATE_TARGET={target}"
    )

    exit_code = validate_extension(
        blender,
        target,
    )

    print(
        f"VALIDATE_EXIT={exit_code}"
    )

    if exit_code == 0:
        print(
            "BVT_VALIDATE=OK"
        )
    else:
        print(
            "BVT_VALIDATE=FAIL"
        )

    return exit_code


def build_extension(
    blender,
):
    RELEASES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = run_process(
        [
            blender,
            "--command",
            "extension",
            "build",
            "--source-dir",
            SOURCE_DIR,
            "--output-dir",
            RELEASES_DIR,
            "--verbose",
        ]
    )

    return result.returncode


def newest_zip():
    archives = sorted(
        RELEASES_DIR.glob(
            "*.zip"
        ),
        key=lambda path: (
            path.stat().st_mtime
        ),
        reverse=True,
    )

    if not archives:
        return None

    return archives[0]


def cmd_build(
    args,
):
    blender = find_blender(
        args.blender
    )

    exit_code = build_extension(
        blender
    )

    print(
        f"BUILD_EXIT={exit_code}"
    )

    archive = newest_zip()

    if archive:
        print(
            f"PACKAGE={archive}"
        )

    if exit_code == 0:
        print(
            "BVT_BUILD=OK"
        )
    else:
        print(
            "BVT_BUILD=FAIL"
        )

    return exit_code


def sha256(
    path,
):
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


def cmd_package(
    args,
):
    blender = find_blender(
        args.blender
    )

    print(
        "STEP=validate-source"
    )

    exit_code = validate_extension(
        blender,
        SOURCE_DIR,
    )

    if exit_code != 0:
        print(
            "BVT_PACKAGE=FAIL"
        )
        return exit_code

    print(
        "STEP=build"
    )

    exit_code = build_extension(
        blender
    )

    if exit_code != 0:
        print(
            "BVT_PACKAGE=FAIL"
        )
        return exit_code

    archive = newest_zip()

    if archive is None:
        print(
            "ERROR=No extension ZIP produced"
        )
        print(
            "BVT_PACKAGE=FAIL"
        )
        return 1

    print(
        "STEP=validate-zip"
    )

    exit_code = validate_extension(
        blender,
        archive,
    )

    if exit_code != 0:
        print(
            "BVT_PACKAGE=FAIL"
        )
        return exit_code

    digest = sha256(
        archive
    )

    print(
        f"PACKAGE={archive}"
    )

    print(
        f"SIZE_BYTES={archive.stat().st_size}"
    )

    print(
        f"SHA256={digest}"
    )

    print(
        "BVT_PACKAGE=OK"
    )

    return 0



def cmd_dataset(
    args,
):
    blender = find_blender(
        args.blender
    )

    config = Path(
        args.config
    )

    if not config.is_absolute():
        config = (
            ROOT
            / config
        )

    config = config.resolve()

    if not config.is_file():
        emit_cli_error(
            "INPUT_NOT_FOUND",
            (
                "Scenario config not found: "
                f"{config}"
            ),
        )

        print(
            "BVT_DATASET=FAIL"
        )

        return 1

    runner = (
        ROOT
        / "tools"
        / "bvt_dataset_runner.py"
    )

    if not runner.is_file():
        emit_cli_error(
            "INTERNAL_ERROR",
            (
                "Dataset runner not found: "
                f"{runner}"
            ),
        )

        print(
            "BVT_DATASET=FAIL"
        )

        return 1

    command = [
        blender,
        "--background",
        "--factory-startup",
    ]

    if args.blend:
        blend = Path(
            args.blend
        )

        if not blend.is_absolute():
            blend = (
                ROOT
                / blend
            )

        blend = blend.resolve()

        if not blend.is_file():
            raise RuntimeError(
                f"Blend file not found: {blend}"
            )

        command.append(
            blend
        )

    command.extend(
        [
            "--python",
            runner,
            "--",
            "--config",
            config,
        ]
    )

    result = run_process(
        command,
        capture=True,
    )

    output = (
        result.stdout
        or ""
    )

    has_traceback = (
        "Traceback (most recent call last):"
        in output
    )

    marker_ok = (
        "BVT_DATASET_CLI=OK"
        in output
    )

    success = (
        result.returncode == 0
        and not has_traceback
        and marker_ok
    )

    interesting_prefixes = (
        "ERROR_SCHEMA=",
        "ERROR_CODE=",
        "ERROR_MESSAGE=",
        "DATASET_DIRECTORY=",
        "MANIFEST=",
        "CONFIG=",
        "VALIDATION=",
        "STATISTICS=",
        "HEALTH=",
        "HASHES=",
        "ARCHIVE=",
        "FRAMES=",
        "OBJECTS=",
        "MATERIALS=",
        "VALIDATION_STATUS=",
        "BVT_",
        "RESULT=",
    )

    for line in output.splitlines():
        stripped = line.strip()

        if stripped.startswith(
            interesting_prefixes
        ):
            print(
                stripped
            )

    if (
        args.verbose
        or not success
    ):
        print(
            "\n--- Blender output ---"
        )

        print(
            "\n".join(
                output.splitlines()[
                    -180:
                ]
            )
        )

    print(
        "PROCESS_EXIT="
        f"{result.returncode}"
    )

    print(
        "TRACEBACK="
        + (
            "FOUND"
            if has_traceback
            else "NONE"
        )
    )

    if success:
        print(
            "BVT_DATASET=OK"
        )
        return 0

    if (
        "ERROR_CODE="
        not in output
    ):
        if has_traceback:
            code = (
                "BLENDER_TRACEBACK"
            )

            message = (
                "Blender dataset runner "
                "reported a traceback"
            )

        elif result.returncode != 0:
            code = (
                "PROCESS_FAILED"
            )

            message = (
                "Blender dataset process "
                "returned non-zero exit code "
                f"{result.returncode}"
            )

        else:
            code = (
                "SUCCESS_MARKER_MISSING"
            )

            message = (
                "Dataset process completed "
                "without the success marker"
            )

        emit_cli_error(
            code,
            message,
        )

    print(
        "BVT_DATASET=FAIL"
    )

    return 1


def cmd_run_script(
    args,
):
    blender = find_blender(
        args.blender
    )

    script = Path(
        args.script
    )

    if not script.is_absolute():
        script = (
            ROOT
            / script
        )

    script = script.resolve()

    if not script.is_file():
        raise RuntimeError(
            f"Script not found: {script}"
        )

    command = [
        blender,
        "--background",
    ]

    if args.factory_startup:
        command.append(
            "--factory-startup"
        )

    if args.blend:
        blend_path = Path(
            args.blend
        )

        if not blend_path.is_absolute():
            blend_path = (
                ROOT
                / blend_path
            )

        command.append(
            blend_path.resolve()
        )

    command.extend(
        [
            "--python",
            script,
        ]
    )

    if args.script_args:
        command.append(
            "--"
        )

        command.extend(
            args.script_args
        )

    result = run_process(
        command,
        capture=True,
    )

    output = (
        result.stdout
        or ""
    )

    has_traceback = (
        "Traceback (most recent call last):"
        in output
    )

    if output:
        print(
            output,
            end=(
                ""
                if output.endswith("\\n")
                else "\\n"
            ),
        )

    print(
        "PROCESS_EXIT="
        f"{result.returncode}"
    )

    print(
        "TRACEBACK="
        + (
            "FOUND"
            if has_traceback
            else "NONE"
        )
    )

    if (
        result.returncode == 0
        and not has_traceback
    ):
        print(
            "BVT_RUN_SCRIPT=OK"
        )
        return 0

    print(
        "BVT_RUN_SCRIPT=FAIL"
    )

    return 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bvt",
        description=(
            "Blender Visual Toolkit "
            "development CLI"
        ),
    )

    parser.add_argument(
        "--blender",
        help=(
            "Path to blender executable. "
            "Can also be set using BVT_BLENDER."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"BVT CLI {CLI_VERSION}"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    doctor = subparsers.add_parser(
        "doctor",
        help=(
            "Check BVT development environment"
        ),
    )

    doctor.set_defaults(
        handler=cmd_doctor
    )

    test = subparsers.add_parser(
        "test",
        help=(
            "Run one smoke test"
        ),
    )

    test.add_argument(
        "test",
        help=(
            "Test name, partial name, "
            "or smoke test path"
        ),
    )

    test.add_argument(
        "-v",
        "--verbose",
        action="store_true",
    )

    test.set_defaults(
        handler=cmd_test
    )

    regression = subparsers.add_parser(
        "regression",
        help=(
            "Run every *_smoke.py test"
        ),
    )

    regression.add_argument(
        "-v",
        "--verbose",
        action="store_true",
    )

    regression.add_argument(
        "--fail-fast",
        action="store_true",
    )

    regression.set_defaults(
        handler=cmd_regression
    )

    validate = subparsers.add_parser(
        "validate",
        help=(
            "Validate extension source or ZIP"
        ),
    )

    validate.add_argument(
        "target",
        nargs="?",
        help=(
            "Path to extension source or ZIP. "
            "Defaults to src/bvt."
        ),
    )

    validate.set_defaults(
        handler=cmd_validate
    )

    build = subparsers.add_parser(
        "build",
        help=(
            "Build Blender extension ZIP"
        ),
    )

    build.set_defaults(
        handler=cmd_build
    )

    package = subparsers.add_parser(
        "package",
        help=(
            "Validate, build, validate ZIP "
            "and calculate SHA256"
        ),
    )

    package.set_defaults(
        handler=cmd_package
    )

    dataset = subparsers.add_parser(
        "dataset",
        help=(
            "Generate and validate a dataset "
            "from a JSON scenario"
        ),
    )

    dataset.add_argument(
        "--config",
        required=True,
        help=(
            "BVT CLI scenario JSON"
        ),
    )

    dataset.add_argument(
        "--blend",
        help=(
            "Optional source .blend file. "
            "Without it Blender factory startup "
            "scene is used."
        ),
    )

    dataset.add_argument(
        "-v",
        "--verbose",
        action="store_true",
    )

    dataset.set_defaults(
        handler=cmd_dataset
    )

    run_script = subparsers.add_parser(
        "run-script",
        help=(
            "Run arbitrary Python script "
            "inside Blender"
        ),
    )

    run_script.add_argument(
        "script",
    )

    run_script.add_argument(
        "--blend",
        help=(
            "Optional .blend file"
        ),
    )

    run_script.add_argument(
        "--no-factory-startup",
        dest="factory_startup",
        action="store_false",
        default=True,
    )

    run_script.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
    )

    run_script.set_defaults(
        handler=cmd_run_script
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    try:
        return int(
            args.handler(
                args
            )
            or 0
        )

    except KeyboardInterrupt:
        print(
            "Interrupted",
            file=sys.stderr,
        )
        return 130

    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
