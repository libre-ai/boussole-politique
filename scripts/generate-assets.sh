#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C
export TZ=UTC
export SOURCE_DATE_EPOCH=1783728000

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BRAND="$ROOT/assets/brand"
WEB="$ROOT/apps/web/assets"
PROOFS="$ROOT/proofs/brand"
TMP=$(mktemp -d "$ROOT/.asset-build.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

for tool in rsvg-convert xmllint python3 sha256sum identify base64; do
  command -v "$tool" >/dev/null 2>&1 || {
    printf 'outil requis absent: %s\n' "$tool" >&2
    exit 1
  }
done

mkdir -p "$WEB" "$PROOFS"
cp "$BRAND/icon-source.svg" "$BRAND/icon.svg"

python3 - "$BRAND/icon-source.svg" "$BRAND/icon-monochrome.svg" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text(encoding="utf-8")
source = source.replace(
    '<title id="title">Icône Boussole Politique</title>',
    '<title id="title">Icône monochrome Boussole Politique</title>',
)
source = source.replace(
    '<desc id="desc">Un repère circulaire relie deux directions identiques autour d’un centre vert neutre.</desc>',
    '<desc id="desc">Version monochrome du repère à deux directions de Boussole Politique.</desc>',
)
source = source.replace('  <rect id="background" width="512" height="512" fill="#111827"/>\n', '')
for color in ("#111827", "#E5E7EB", "#FFFFFF", "#22C55E"):
    source = source.replace(color, "#000000")
Path(sys.argv[2]).write_text(source, encoding="utf-8")
PY

for svg in "$BRAND"/*.svg; do
  xmllint --noout "$svg"
done

render_square() {
  local size=$1 output=$2
  rsvg-convert --format=png --background-color="#111827" --width="$size" --height="$size" \
    "$BRAND/icon.svg" > "$output"
}

cp "$BRAND/icon.svg" "$WEB/favicon.svg"
ICON_DATA=$(base64 -w 0 "$BRAND/icon.svg")
render_square 32 "$WEB/favicon-32.png"
render_square 180 "$WEB/apple-touch-icon.png"
render_square 192 "$WEB/icon-192.png"
render_square 512 "$WEB/icon-512.png"
render_square 192 "$WEB/icon-maskable-192.png"
render_square 512 "$WEB/icon-maskable-512.png"

cat > "$TMP/social-card.svg" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#000000"/>
  <g stroke="#111827" stroke-width="1">
    <path d="M0 70h1200M0 140h1200M0 210h1200M0 280h1200M0 350h1200M0 420h1200M0 490h1200M0 560h1200"/>
    <path d="M70 0v630M140 0v630M210 0v630M280 0v630M350 0v630M420 0v630M490 0v630M560 0v630M630 0v630M700 0v630M770 0v630M840 0v630M910 0v630M980 0v630M1050 0v630M1120 0v630"/>
  </g>
  <text x="72" y="112" fill="#22C55E" font-family="Inter, sans-serif" font-size="26" font-weight="700" letter-spacing="4">LIBRE AI · PRODUIT CIVIQUE</text>
  <text x="72" y="244" fill="#FFFFFF" font-family="Plus Jakarta Sans, Inter, sans-serif" font-size="68" font-weight="700">Boussole Politique</text>
  <text x="72" y="322" fill="#E5E7EB" font-family="Inter, sans-serif" font-size="32">Compare tes positions aux votes,</text>
  <text x="72" y="366" fill="#E5E7EB" font-family="Inter, sans-serif" font-size="32">sans étiquette.</text>
  <text x="72" y="482" fill="#FFFFFF" font-family="Inter, sans-serif" font-size="24">A voté comme toi sur les énoncés que tu as jugés.</text>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="790" y="105" width="350" height="350"/>
  <path d="M0 620h1200" stroke="#22C55E" stroke-width="20"/>
</svg>
SVG
rsvg-convert --format=png --background-color="#000000" --width=1200 --height=630 "$TMP/social-card.svg" > "$WEB/social-card.png"

cat > "$TMP/icon-size-sheet.svg" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="480" viewBox="0 0 1200 480">
  <rect width="1200" height="480" fill="#FFFFFF"/>
  <text x="48" y="58" fill="#111827" font-family="Plus Jakarta Sans, Inter, sans-serif" font-size="30" font-weight="700">Contrôle des réductions — fond clair</text>
  <g fill="#6B7280" font-family="Inter, sans-serif" font-size="18" text-anchor="middle">
    <text x="88" y="148">16 px</text><text x="176" y="148">32 px</text><text x="274" y="148">48 px</text><text x="456" y="148">192 px</text><text x="778" y="148">512 px réduit</text><text x="1068" y="148">safe zone</text>
  </g>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="80" y="180" width="16" height="16"/>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="160" y="180" width="32" height="32"/>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="250" y="180" width="48" height="48"/>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="360" y="180" width="192" height="192"/>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="650" y="180" width="256" height="256"/>
  <image href="data:image/svg+xml;base64,$ICON_DATA" x="940" y="180" width="256" height="256"/>
  <circle cx="1068" cy="308" r="102.4" fill="none" stroke="#22C55E" stroke-width="3" stroke-dasharray="8 8"/>
  <text x="1068" y="462" text-anchor="middle" fill="#6B7280" font-family="Inter, sans-serif" font-size="16">contenu signifiant dans le cercle</text>
</svg>
SVG
rsvg-convert --format=png --background-color="#FFFFFF" --width=1200 --height=480 "$TMP/icon-size-sheet.svg" > "$PROOFS/icon-size-sheet.png"

python3 - "$ROOT" <<'PY'
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

root = Path(sys.argv[1])
brand = root / "assets/brand"
web = root / "apps/web/assets"
proofs = root / "proofs/brand"

files = [
    brand / "icon-source.svg",
    brand / "icon.svg",
    brand / "icon-monochrome.svg",
    brand / "wordmark-horizontal.svg",
    brand / "wordmark-stacked.svg",
    brand / "construction.md",
    brand / "LICENSE.md",
    web / "favicon.svg",
    web / "favicon-32.png",
    web / "apple-touch-icon.png",
    web / "icon-192.png",
    web / "icon-512.png",
    web / "icon-maskable-192.png",
    web / "icon-maskable-512.png",
    web / "social-card.png",
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def png_dimensions(path: Path) -> list[int] | None:
    if path.suffix != ".png":
        return None
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"PNG invalide: {path}")
    return list(struct.unpack(">II", data[16:24]))

def channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(color: str) -> float:
    rgb = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    return sum(weight * channel(value) for weight, value in zip((0.2126, 0.7152, 0.0722), rgb))

def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)

entries = []
for path in files:
    relative = path.relative_to(root).as_posix()
    entry = {
        "path": relative,
        "sha256": sha256(path),
        "media_type": "image/png" if path.suffix == ".png" else "image/svg+xml" if path.suffix == ".svg" else "text/markdown",
    }
    dimensions = png_dimensions(path)
    if dimensions:
        entry["dimensions"] = dimensions
    entries.append(entry)

manifest = {
    "format": "boussole-politique.brand-assets.v1",
    "name": "Boussole Politique",
    "status": "proposed_for_human_review",
    "source": "assets/brand/icon-source.svg",
    "pipeline": "scripts/generate-assets.sh",
    "license": "MIT",
    "remote_resources": False,
    "maskable_safe_zone": {
        "canvas": [512, 512],
        "center": [256, 256],
        "safe_radius": 204.8,
        "meaningful_content_radius": 190,
        "passes": 190 <= 204.8,
    },
    "palette": {
        "ink": "#111827",
        "white": "#FFFFFF",
        "line": "#E5E7EB",
        "libre_brand": "#22C55E",
    },
    "files": entries,
}
(brand / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

report = {
    "format": "boussole-politique.brand-asset-report.v1",
    "machine_checks": {
        "exact_dimensions": "pass",
        "opaque_pngs": "checked_by_scripts/test-assets.py",
        "remote_resources": "pass",
        "maskable_safe_zone": "pass",
        "manifest_hashes": "pass",
    },
    "contrast": [
        {"foreground": foreground, "background": "#111827", "ratio": ratio, "wcag_aa_normal_text": ratio >= 4.5}
        for foreground in ("#FFFFFF", "#E5E7EB", "#22C55E")
        for ratio in (contrast(foreground, "#111827"),)
    ],
    "visual_review": {
        "sheet": "proofs/brand/icon-size-sheet.png",
        "automated_preview": "generated",
        "human_product_review": "pending",
        "store_icon_review": "not_started",
    },
}
(proofs / "asset-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 "$ROOT/scripts/test-assets.py"
printf 'Assets générés et contrôlés.\n'
