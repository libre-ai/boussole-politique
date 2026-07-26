#!/usr/bin/env python3
"""Fail when tracked files share a content fingerprint outside the declared set.

Two files with the same SHA-256 are the same bytes, whatever their names; two
files with the same name may be nothing alike. This gate therefore joins on
content, never on path, and pins the groups that are legitimately identical --
brand-generator outputs plus one documented bit-for-bit copy.

It fails in both directions:

  * an undeclared group of identical files appeared, or
  * a declared group stopped matching.

The second direction is the one that protects scoring. `vecteurs-test.json` is
written at the repository root by `dry-run/scripts/formule_v2.py`, while
`crates/scoring/tests/golden_vectors.rs` reads the copy under `fixtures/scoring/`.
`docs/implementation/contrats-rust-m2.md` calls that copy bit-for-bit, but no
generator and no test keeps the two in step. Without this check a divergence is
silent, and the executable specification and the golden test would then prove
two different scales for the same questionnaire.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Sorted path tuple -> why these bytes are legitimately identical.
DECLARED_GROUPS: dict[tuple[str, ...], str] = {
    (
        "fixtures/scoring/vecteurs-test.json",
        "vecteurs-test.json",
    ): (
        "documented bit-for-bit copy (docs/implementation/contrats-rust-m2.md): "
        "dry-run/scripts/formule_v2.py writes the root file, "
        "crates/scoring/tests/golden_vectors.rs reads the fixture"
    ),
    (
        "apps/web/assets/favicon.svg",
        "assets/brand/icon-source.svg",
        "assets/brand/icon.svg",
    ): (
        "generated: scripts/generate-assets.sh copies "
        "icon-source.svg -> icon.svg -> favicon.svg"
    ),
    (
        "apps/web/assets/icon-192.png",
        "apps/web/assets/icon-maskable-192.png",
    ): "generated: scripts/generate-assets.sh renders both at 192 from the same source",
    (
        "apps/web/assets/icon-512.png",
        "apps/web/assets/icon-maskable-512.png",
    ): "generated: scripts/generate-assets.sh renders both at 512 from the same source",
}


def tracked_files() -> list[str]:
    """Tracked paths only: untracked scratch files would pollute the join."""
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO_ROOT)
    return [raw.decode() for raw in output.split(b"\0") if raw]


def fingerprint(relative: str) -> str:
    digest = hashlib.sha256()
    with (REPO_ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    paths = tracked_files()
    by_digest: dict[str, list[str]] = defaultdict(list)
    examined = 0
    for relative in paths:
        absolute = REPO_ROOT / relative
        # Symlinks and gitlinks carry no content of their own to compare.
        if absolute.is_symlink() or not absolute.is_file():
            continue
        by_digest[fingerprint(relative)].append(relative)
        examined += 1

    # An empty join satisfies every assertion below, so refuse it explicitly
    # rather than report a green that only means "nothing was looked at".
    if examined == 0:
        print(
            "duplicate fingerprints: FAIL (0 files examined -- "
            "the join found nothing to compare)",
            file=sys.stderr,
        )
        return 1

    observed = {
        tuple(sorted(group)): digest
        for digest, group in by_digest.items()
        if len(group) > 1
    }

    failures: list[str] = []
    for group, digest in sorted(observed.items()):
        if group not in DECLARED_GROUPS:
            failures.append(
                f"undeclared identical contents [{digest[:16]}]: " + ", ".join(group)
            )
    for group, reason in sorted(DECLARED_GROUPS.items()):
        if group not in observed:
            failures.append(
                "declared identical contents no longer match: "
                + ", ".join(group)
                + f" -- {reason}"
            )

    if failures:
        print(
            f"duplicate fingerprints: FAIL ({examined} files examined)",
            file=sys.stderr,
        )
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"duplicate fingerprints: PASS ({examined} files examined, "
        f"{len(observed)} declared identical groups)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
