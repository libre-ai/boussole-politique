#!/usr/bin/env python3
"""Reproduce and verify the bounded M1 sensitivity evidence.

This is an evidence gate for the existing Python dry-run, not the target ETL.
It extracts only the five committed snapshots, runs Q8 twice, and refuses any
non-deterministic output or drift from the registered parameter grid.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DRY_RUN = ROOT / "dry-run"
DATA = DRY_RUN / "data"
OUT = DRY_RUN / "out"
REGISTRATION = ROOT / "docs" / "methodology" / "m1-gate-registration.v1.json"
EVIDENCE = ROOT / "proofs" / "methodology" / "m1-sensitivity.json"
SNAPSHOTS = ("scrutins-16", "scrutins-17", "dossiers-16", "dossiers-17", "amo10-17")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts or item.is_dir() and path == PurePosixPath("."):
                raise RuntimeError(f"unsafe archive member in {archive.name}")
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError(f"symlink archive member in {archive.name}")
        bundle.extractall(destination)


def run_q8() -> tuple[bytes, bytes]:
    subprocess.run(
        [sys.executable, str(DRY_RUN / "scripts" / "q8-vivier-elargi.py")],
        cwd=DRY_RUN,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return (
        (OUT / "q8-vivier-elargi.json").read_bytes(),
        (OUT / "q8-vivier-elargi.md").read_bytes(),
    )


def main() -> int:
    created: list[Path] = []
    try:
        for name in SNAPSHOTS:
            archive = DATA / f"{name}.json.zip"
            destination = DATA / name
            if destination.exists():
                continue
            destination.mkdir()
            created.append(destination)
            safe_extract(archive, destination)

        first = run_q8()
        second = run_q8()
        if first != second:
            raise RuntimeError("Q8 output is not byte-for-byte deterministic")

        registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        report = json.loads(first[0])
        expected_grid = {
            (float(discriminance), float(participation))
            for discriminance in registration["parameter_grid"]["discriminance_min"]
            for participation in registration["parameter_grid"]["participation_min"]
        }
        actual_grid = {
            (float(row["discriminance_min"]), float(row["participation_min"]))
            for row in report["sensibilite"]
        }
        if actual_grid != expected_grid:
            raise RuntimeError("Q8 parameter grid drifted from the M1 registration")
        if report["gates"]["verdict_global"] != "conditionnel":
            raise RuntimeError("M1 verdict changed and requires an explicit methodology review")

        evidence = {
            "format": "boussole-politique.m1-sensitivity-evidence.v1",
            "registration_status": registration["status"],
            "inputs": {
                f"{name}.json.zip": sha256(DATA / f"{name}.json.zip") for name in SNAPSHOTS
            },
            "outputs": {
                "q8-vivier-elargi.json": hashlib.sha256(first[0]).hexdigest(),
                "q8-vivier-elargi.md": hashlib.sha256(first[1]).hexdigest(),
            },
            "observations": {
                "core_candidates": report["vivier_core_filtre_defaut"]["n"],
                "strong_link_core_candidates": report["vivier_core_filtre_lien_fort"]["n"],
                "strong_link_adopted": report["vivier_core_filtre_lien_fort"]["par_sort"].get("adopté", 0),
                "strong_link_rejected": report["vivier_core_filtre_lien_fort"]["par_sort"].get("rejeté", 0),
                "parameter_combinations": len(actual_grid),
                "two_runs_byte_identical": True,
            },
            "verdict": "conditional",
            "blocking_gates": [
                "political_symmetry_unproven",
                "thematic_coverage_unproven",
                "source_links_partially_reviewed",
            ],
            "canonical_selection_authorized": False,
            "pwa_product_claim_authorized": False,
        }
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("M1 sensitivity: PASS (deterministic evidence, verdict remains conditional)")
        return 0
    finally:
        for destination in reversed(created):
            shutil.rmtree(destination)


if __name__ == "__main__":
    raise SystemExit(main())
