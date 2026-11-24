#!/usr/bin/env python3
"""Verify the local archive parts and safely restore project/ using only the stdlib."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
UPLOAD_MANIFEST = ROOT / "UPLOAD_MANIFEST.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise RuntimeError("Invalid archive or manifest path.")
    relative = PurePosixPath(name)
    components = name.rstrip("/").split("/")
    if (relative.is_absolute()
            or any(component in ("", ".", "..") for component in components)
            or any(component.casefold() == ".git" for component in components)):
        raise RuntimeError("Unsafe archive or manifest path: " + name)
    return relative


def check_record(path: Path, record: dict, description: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(description + " is missing or is not a regular file.")
    if path.stat().st_size != record["size"]:
        raise RuntimeError(description + " has an unexpected byte length.")
    if file_sha256(path) != record["sha256"]:
        raise RuntimeError(description + " has an unexpected SHA-256.")


def load_upload_manifest() -> dict:
    if UPLOAD_MANIFEST.is_symlink():
        raise RuntimeError("UPLOAD_MANIFEST.json must not be a symbolic link.")
    data = json.loads(UPLOAD_MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported upload manifest version.")
    archive = data["archive"]
    if archive.get("root_directory") != "project":
        raise RuntimeError("Unexpected archive root directory.")
    if archive.get("formal_file_count_including_manifest") != 4427:
        raise RuntimeError("Unexpected project file inventory.")
    expected_names = [f"capital-project-20261124.part{index:02d}" for index in range(1, 8)]
    if [part["name"] for part in data["parts"]] != expected_names:
        raise RuntimeError("The upload manifest must list the seven expected parts in order.")
    for record in [archive, *data["parts"]]:
        if not isinstance(record["size"], int) or record["size"] <= 0:
            raise RuntimeError("Invalid byte length in the upload manifest.")
        if not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
            raise RuntimeError("Invalid SHA-256 in the upload manifest.")
    if sum(part["size"] for part in data["parts"]) != archive["size"]:
        raise RuntimeError("Part sizes do not add up to the complete ZIP size.")
    return data


def assemble_parts(data: dict, destination: Path) -> None:
    with destination.open("xb") as output:
        for part in data["parts"]:
            source = ROOT / part["name"]
            check_record(source, part, part["name"])
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, output, length=1024 * 1024)
    check_record(destination, data["archive"], "The reassembled ZIP")


def ensure_empty_destination(destination: Path) -> None:
    for component in [destination, *destination.parents]:
        if component.is_symlink():
            raise RuntimeError("The output path must not contain symbolic links.")
    if destination.exists():
        if not destination.is_dir():
            raise RuntimeError("The output path already exists and is not a directory.")
        if any(destination.iterdir()):
            raise RuntimeError("Refusing to overwrite an existing nonempty project directory.")


def safely_extract(archive_path: Path, extraction: Path) -> Path:
    seen: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            relative = safe_relative(member.filename)
            if relative.parts[0] != "project":
                raise RuntimeError("Every ZIP member must be inside project/.")
            if len(relative.parts) == 1 and not member.is_dir():
                raise RuntimeError("The project root must be a directory.")
            canonical = relative.as_posix()
            if canonical in seen:
                raise RuntimeError("Duplicate ZIP member: " + canonical)
            seen.add(canonical)
            mode = member.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if stat.S_ISLNK(mode) or kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise RuntimeError("ZIP contains a symbolic link or another unsupported file type.")
            target = extraction.joinpath(*relative.parts)
            if extraction.resolve() not in target.resolve().parents:
                raise RuntimeError("ZIP member escaped the extraction directory.")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                if mode:
                    target.chmod(mode & 0o777)
    project = extraction / "project"
    if not project.is_dir():
        raise RuntimeError("The archive has no project/ directory.")
    return project


def verify_restored_manifest(project: Path, expected_count: int) -> int:
    manifest_name = "MANIFEST.sha256.json"
    manifest = json.loads((project / manifest_name).read_text(encoding="utf-8"))
    if manifest.get("algorithm") != "SHA-256":
        raise RuntimeError("Unexpected project manifest algorithm.")
    records = manifest["files"]
    actual_files = set()
    for path in project.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("The extracted project contains a symbolic link.")
        if path.is_file():
            actual_files.add(path.relative_to(project).as_posix())
    expected_files = set(records) | {manifest_name}
    if actual_files != expected_files or len(actual_files) != expected_count:
        raise RuntimeError("The extracted project file set differs from its manifest.")
    for name, record in records.items():
        relative = safe_relative(name)
        check_record(project.joinpath(*relative.parts), record, name)
    return len(actual_files)


def main() -> int:
    if sys.version_info < (3, 9):
        raise RuntimeError("Python 3.9 or newer is required.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Check all seven parts and the complete ZIP hash without extracting.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "project",
                        help="Destination project directory; it must not exist or must be empty.")
    arguments = parser.parse_args()
    data = load_upload_manifest()
    if arguments.check:
        with tempfile.TemporaryDirectory(prefix="capital-parts-check-") as temporary:
            archive_path = Path(temporary) / "capital-project-20261124.zip"
            assemble_parts(data, archive_path)
        print(json.dumps({
            "status": "PASS", "mode": "check_only", "parts": len(data["parts"]),
            "archive_bytes": data["archive"]["size"],
            "archive_sha256": data["archive"]["sha256"], "extracted": False,
        }, ensure_ascii=False, indent=2))
        return 0

    destination = Path(os.path.abspath(arguments.output_dir))
    ensure_empty_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".capital-restore-", dir=destination.parent) as temporary:
        temporary = Path(temporary)
        archive_path = temporary / "capital-project-20261124.zip"
        assemble_parts(data, archive_path)
        extraction = temporary / "unpacked"
        extraction.mkdir()
        project = safely_extract(archive_path, extraction)
        count = verify_restored_manifest(
            project, data["archive"]["formal_file_count_including_manifest"])
        ensure_empty_destination(destination)
        if destination.exists():
            destination.rmdir()
        project.replace(destination)
    print(json.dumps({
        "status": "PASS", "mode": "restore", "parts": len(data["parts"]),
        "archive_bytes": data["archive"]["size"],
        "archive_sha256": data["archive"]["sha256"],
        "restored_directory": str(destination),
        "formal_files_including_manifest": count,
        "project_scripts_executed": False,
        "next_commands": ["cd " + str(destination), "python3 run.py verify", "python3 run.py build"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(1)
