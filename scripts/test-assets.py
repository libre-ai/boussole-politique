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
    "wordmark-horizontal-source.svg",
    "wordmark-horizontal.svg",
    "wordmark-stacked-source.svg",
    "wordmark-stacked.svg",
    "social-card-source.svg",
    "social-card.svg",
    "icon-size-sheet-source.svg",
    "icon-size-sheet.svg",
    "construction.md",
    "FONT-NOTICE.md",
    "LICENSE.md",
    "manifest.json",
}

# Every file here must carry outlines, never <text>. Their `*-source.svg`
# counterparts are the editable originals and are expected to still hold the
# text. Paths are root-relative because the set no longer lives in one place.
#
# TWO DIFFERENT REASONS, and conflating them would misread this gate:
#
#   * the two sheets are RASTERISED by scripts/generate-assets.sh, so a <text>
#     would put the set of font families installed on the runner back into the
#     committed PNG bytes -- the one rendering input CI cannot pin. Run
#     30193088312 measured that cost. The `Prove the render depends on no
#     installed font` step in ci.yml re-renders with an empty fontconfig and is
#     the live proof for these two.
#
#   * the wordmarks and the repository card are SERVED AS SVG and rasterised
#     nowhere, so no PNG gate can ever cover them and that step says nothing
#     about them. Their dependency was at the CONSUMER: a viewer without Plus
#     Jakarta Sans got a substituted family, which for a wordmark means the mark
#     itself is wrong. This static check is therefore the whole proof for them,
#     not a supplement to a byte comparison -- which is precisely why it is
#     asserted here rather than inferred from the render.
VECTORISED = {
    "assets/brand/social-card.svg",
    "assets/brand/icon-size-sheet.svg",
    "assets/brand/wordmark-horizontal.svg",
    "assets/brand/wordmark-stacked.svg",
    ".github/assets/repository-card.svg",
}

# The subset of VECTORISED that a person actually receives as SVG. Only these
# reach an accessibility tree, so only these owe a textual alternative: the two
# sheets are build inputs rasterised to PNG, and a PNG's alternative is written
# by whatever embeds it, not by the SVG that produced it.
SERVED = {
    "assets/brand/wordmark-horizontal.svg",
    "assets/brand/wordmark-stacked.svg",
    ".github/assets/repository-card.svg",
}

# Outlining must not cost the wordmarks their theme adaptation. `currentColor`
# sat on the <text> element; it survives only because the converter propagates
# `fill` onto the emitted <path>. Counted, not asserted as a boolean: "at least
# one" would still pass if a glyph path silently lost its fill while the mark's
# strokes kept theirs. (total currentColor attributes, glyph-path fills among them)
#
# horizontal: 2 stroke on <g> + 1 glyph path. stacked: 2 stroke + 2 glyph paths.
THEMED = {
    "assets/brand/wordmark-horizontal.svg": (3, 1),
    "assets/brand/wordmark-stacked.svg": (4, 2),
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

    for name in sorted(VECTORISED):
        path = ROOT / name
        if not path.is_file():
            fail(f"fichier vectorisé absent: {name}")
        root = ET.parse(path).getroot()
        texts = [el for el in root.iter() if el.tag.rsplit("}", 1)[-1] == "text"]
        if texts:
            fail(f"{name} contient {len(texts)} <text>: le rendu dépendrait des polices installées")
        fonts = [
            el.tag for el in root.iter() if "font-family" in el.attrib
        ]
        if fonts:
            fail(f"{name} déclare encore font-family sur {len(fonts)} éléments")
        # Vectorising removes the glyphs from the accessibility tree: the mark
        # stops being readable text for a screen reader, an indexer or a
        # translator. An outlined wordmark with no textual alternative is a
        # regression, so the alternative is required here rather than trusted.
        if name not in SERVED:
            continue
        if root.get("role") != "img":
            fail(f'{name} a perdu role="img": les tracés ne sont plus annonçables')
        labelled = root.get("aria-labelledby", "").split()
        titles = [el for el in root.iter() if el.tag.rsplit("}", 1)[-1] == "title"]
        if not labelled or not titles:
            fail(f"{name} n'a plus d'alternative textuelle (aria-labelledby/<title>)")
        ids = {el.get("id") for el in root.iter()}
        missing_ids = [ref for ref in labelled if ref not in ids]
        if missing_ids:
            fail(f"{name}: aria-labelledby pointe vers des id absents: {missing_ids}")
        if not (titles[0].text or "").strip():
            fail(f"{name}: <title> vide, l'alternative textuelle ne dit rien")

    # `currentColor` is what makes a served wordmark adapt to its context. The
    # <text> that carried it is gone; only the converter propagating `fill`
    # keeps the behaviour, so it is verified on the committed bytes.
    for name, (expected_total, expected_glyphs) in sorted(THEMED.items()):
        root = ET.parse(ROOT / name).getroot()
        total = sum(
            1 for el in root.iter() for value in el.attrib.values()
            if value.strip() == "currentColor"
        )
        glyphs = sum(
            1 for el in root.iter()
            if el.tag.rsplit("}", 1)[-1] == "path" and el.get("fill") == "currentColor"
        )
        if (total, expected_glyphs) != (expected_total, glyphs):
            fail(
                f"{name}: currentColor {total} attributs / {glyphs} tracés de glyphe, "
                f"attendu {expected_total} / {expected_glyphs} — le wordmark ne suit plus le thème"
            )

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
        if opaque.strip().lower() != "true":
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
