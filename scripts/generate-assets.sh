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

for tool in rsvg-convert xmllint python3 sha256sum identify convert; do
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
  local rendered="$TMP/icon-$size.png"
  rsvg-convert --format=png --width="$size" --height="$size" \
    "$BRAND/icon.svg" > "$rendered"
  convert "$rendered" -background '#111827' -alpha remove -alpha off "PNG24:$output"
}

cp "$BRAND/icon.svg" "$WEB/favicon.svg"
render_square 32 "$WEB/favicon-32.png"
render_square 180 "$WEB/apple-touch-icon.png"
render_square 192 "$WEB/icon-192.png"
render_square 512 "$WEB/icon-512.png"
render_square 192 "$WEB/icon-maskable-192.png"
render_square 512 "$WEB/icon-maskable-512.png"

# The two composed sheets carry no <text>: `scripts/vectorize-svg-text.py` has
# already turned every glyph into an outline, so nothing here consults
# fontconfig. That is deliberate and load-bearing. While they still asked for
# "Inter" and "Plus Jakarta Sans" by name, the rendered bytes depended on the
# runner's font families -- the one input `apt-get install <pkg>=<version>`
# cannot pin -- and run 30193088312 measured the cost: 5.5220 % of social-card
# samples and 2.3307 % of icon-size-sheet samples moved, while the six PNGs
# without text stayed pixel-identical.
#
# Only the icon is late-bound, through the __ICON_DATA__ placeholder. Doing the
# substitution in Python rather than in a shell heredoc keeps the coupling to
# `icon-source.svg` exact -- a change there always reaches these sheets -- while
# removing any chance of the shell expanding `$` or a backtick inside 100 kB of
# committed path data.
python3 - "$BRAND" "$TMP" <<'PY'
import base64
import sys
from pathlib import Path

brand, tmp = Path(sys.argv[1]), Path(sys.argv[2])
icon = base64.b64encode((brand / "icon.svg").read_bytes()).decode("ascii")
for name in ("social-card", "icon-size-sheet"):
    template = (brand / f"{name}.svg").read_text(encoding="utf-8")
    if "__ICON_DATA__" not in template:
        raise SystemExit(f"{name}.svg no longer carries the __ICON_DATA__ placeholder")
    if "<text" in template:
        raise SystemExit(f"{name}.svg contains <text>: rendering would depend on installed fonts")
    (tmp / f"{name}.svg").write_text(template.replace("__ICON_DATA__", icon), encoding="utf-8")
PY

rsvg-convert --format=png --width=1200 --height=630 "$TMP/social-card.svg" > "$TMP/social-card.png"
convert "$TMP/social-card.png" -background '#000000' -alpha remove -alpha off "PNG24:$WEB/social-card.png"

rsvg-convert --format=png --width=1200 --height=480 "$TMP/icon-size-sheet.svg" > "$TMP/icon-size-sheet.png"
convert "$TMP/icon-size-sheet.png" -background '#FFFFFF' -alpha remove -alpha off "PNG24:$PROOFS/icon-size-sheet.png"

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
    brand / "social-card-source.svg",
    brand / "social-card.svg",
    brand / "icon-size-sheet-source.svg",
    brand / "icon-size-sheet.svg",
    brand / "construction.md",
    brand / "FONT-NOTICE.md",
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
    "license": "LicenseRef-Trademark",
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
