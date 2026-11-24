#!/usr/bin/env python3
"""Local compatibility entry point for the archived project."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main() -> int:
    if sys.version_info < (3, 9):
        raise RuntimeError("Python 3.9 or newer is required.")
    project = ROOT / "project"
    if project.is_symlink():
        raise RuntimeError("The project directory must not be a symbolic link.")
    if project.exists() and not project.is_dir():
        raise RuntimeError("The project path exists and is not a directory.")
    needs_restore = not project.exists() or not any(project.iterdir())
    if needs_restore:
        restorer = ROOT / "restore_project.py"
        if restorer.is_symlink() or not restorer.is_file():
            raise RuntimeError("A regular restore_project.py file is required next to run.py.")
        print("Restoring the local archive before running the requested project command.", flush=True)
        restoration = subprocess.run([sys.executable, str(restorer)], cwd=ROOT, check=False)
        if restoration.returncode:
            return restoration.returncode
    entry_point = project / "run.py"
    if entry_point.is_symlink() or not entry_point.is_file():
        raise RuntimeError("The existing project has no regular run.py; it was not overwritten.")
    result = subprocess.run([sys.executable, str(entry_point), *sys.argv[1:]],
                            cwd=project, check=False)
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(1)
