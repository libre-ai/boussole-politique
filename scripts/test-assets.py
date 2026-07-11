#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets/brand"
WEB = ROOT / "apps/web/assets"
MANIFEST = BRAND / "manifest.json"

EXPECTED_PNG = {
    "favicon-32.png": (32, 32),
    "apple-touch-icon.png": (180, 180),
    "icon-192.png": (192, 192),
    "icon-512.png": (512, 512),
    "icon-maskable-192.png": (192, 192),
    "icon-maskable-512.png": (512, 512),
    "social-card.png": (1200, 630),
}
EXPECTED_BRAND = {
    "icon-source.svg",
    "icon.svg",
    "icon-monochrome.svg",
    "wordmark-horizontal.svg",
    "wordmark-stacked.svg",
    "construction.md",
    "LICENSE.md",
    "manifest.json",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"signature PNG invalide: {path}")
    return struct.unpack(">II", data[16:24])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_svg(path: Path) -> None:
    root = ET.parse(path).getroot()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "script":
            fail(f"script interdit dans {path}")
        for name, value in element.attrib.items():
            lowered = value.strip().lower()
            local_name = name.rsplit("}", 1)[-1]
            if local_name in {"href", "src"} and ("://" in lowered or lowered.startswith("//")):
                fail(f"ressource distante dans {path}: {value}")
            if "url(http://" in lowered or "url(https://" in lowered:
                fail(f"ressource distante CSS dans {path}: {value}")


def main() -> int:
    missing_brand = EXPECTED_BRAND - {path.name for path in BRAND.iterdir() if path.is_file()}
    if missing_brand:
        fail(f"assets de marque absents: {sorted(missing_brand)}")

    for path in sorted(BRAND.glob("*.svg")) + [WEB / "favicon.svg"]:
        check_svg(path)

    for name, expected in EXPECTED_PNG.items():
        path = WEB / name
        if not path.is_file():
            fail(f"dérivé absent: {path}")
        actual = png_dimensions(path)
        if actual != expected:
            fail(f"dimensions de {name}: {actual}, attendu {expected}")
        opaque = subprocess.run(
            ["identify", "-quiet", "-format", "%[opaque]", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if opaque != "True":
            fail(f"fond non opaque: {name}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["format"] != "boussole-politique.brand-assets.v1":
        fail("format de manifest inconnu")
    safe = manifest["maskable_safe_zone"]
    if not safe["passes"] or safe["meaningful_content_radius"] > safe["safe_radius"]:
        fail("zone sûre maskable non respectée")
    if manifest["remote_resources"] is not False:
        fail("le manifest déclare des ressources distantes")

    listed = set()
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        listed.add(entry["path"])
        if not path.is_file():
            fail(f"fichier du manifest absent: {path}")
        if sha256(path) != entry["sha256"]:
            fail(f"hash divergent: {path}")
        if path.suffix == ".png" and list(png_dimensions(path)) != entry["dimensions"]:
            fail(f"dimensions du manifest divergentes: {path}")

    expected_listed = {
        f"assets/brand/{name}" for name in EXPECTED_BRAND - {"manifest.json"}
    } | {f"apps/web/assets/{name}" for name in EXPECTED_PNG} | {"apps/web/assets/favicon.svg"}
    if listed != expected_listed:
        fail(f"inventaire manifest divergent: manquant={sorted(expected_listed - listed)}, extra={sorted(listed - expected_listed)}")

    icon_text = (BRAND / "icon-source.svg").read_text(encoding="utf-8")
    allowed_colors = {"#111827", "#E5E7EB", "#FFFFFF", "#22C55E"}
    found_colors = {part[:7] for part in icon_text.split('"') if part.startswith("#")}
    if found_colors != allowed_colors:
        fail(f"palette canonique inattendue: {found_colors}")

    proof = ROOT / "proofs/brand/icon-size-sheet.png"
    if png_dimensions(proof) != (1200, 480):
        fail("planche de miniatures absente ou invalide")
    report = json.loads((ROOT / "proofs/brand/asset-report.json").read_text(encoding="utf-8"))
    if not all(
        check["ratio"] >= 4.5 and check["wcag_aa_normal_text"]
        for check in report["contrast"]
    ):
        fail("contraste inférieur au seuil WCAG AA renforcé retenu pour les assets")

    print("asset tests: pass")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ET.ParseError, KeyError, json.JSONDecodeError) as error:
        print(f"asset tests: fail: {error}", file=sys.stderr)
        raise SystemExit(1)
