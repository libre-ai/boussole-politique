#!/usr/bin/env python3
"""Fail if the dry-run depends on a contributor's absolute workspace path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "dry-run" / "scripts"
FORBIDDEN = (b"/home/", b"/Users/", b"Bureau/dev")


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "dry-run"], cwd=REPO_ROOT
    )
    return [REPO_ROOT / raw.decode() for raw in output.split(b"\0") if raw]


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        data = path.read_bytes()
        if any(marker in data for marker in FORBIDDEN):
            failures.append(f"absolute workspace path: {path.relative_to(REPO_ROOT)}")
        if path.suffix == ".py":
            try:
                compile(data, str(path), "exec")
            except SyntaxError as error:
                failures.append(f"invalid Python: {path.relative_to(REPO_ROOT)}: {error}")

    sys.path.insert(0, str(SCRIPTS_DIR))
    import workspace_paths  # noqa: PLC0415

    expected = {
        "REPO_ROOT": REPO_ROOT,
        "DRY_RUN_DIR": REPO_ROOT / "dry-run",
        "DATA_DIR": REPO_ROOT / "dry-run" / "data",
        "OUT_DIR": REPO_ROOT / "dry-run" / "out",
    }
    for name, value in expected.items():
        if getattr(workspace_paths, name) != value:
            failures.append(f"incorrect {name}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"dry-run portability: PASS ({len(tracked_files())} tracked files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
