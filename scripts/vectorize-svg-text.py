#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fonttools==4.63.0",
#   "uharfbuzz==0.55.0",
# ]
# ///
"""Replace every <text> in an SVG with an equivalent <path>, once and for all.

WHY THIS EXISTS
---------------
`scripts/generate-assets.sh` rasterises two SVGs to PNG and the CI gates the
resulting bytes with `git diff --exit-code`. As long as those SVGs asked for a
font *by name*, the bytes depended on the set of font families installed on the
runner -- the one input `apt-get install <pkg>=<version>` cannot pin, because
the family set comes from the image. Measured on run 30193088312: 5.5220 % of
social-card samples and 2.3307 % of icon-size-sheet samples moved, while the six
PNGs carrying no text were pixel-identical.

Outlines have no such dependency: a <path> is geometry, and the rasteriser needs
no fontconfig lookup to draw it. This script is therefore run ONCE, by hand, by
someone holding the authentic fonts; its output is committed, and CI only ever
renders the committed outlines. That is why it is not wired into CI: the CI
runner deliberately has no Inter and no Plus Jakarta Sans, and after this
conversion it does not need them.

A SECOND, DIFFERENT REASON (added 2026-07-26)
---------------------------------------------
The wordmarks and `.github/assets/repository-card.svg` are also converted, and
the paragraph above does NOT justify them: nothing rasterises those files, they
are served as SVG, and no CI byte gate covers them. Their dependency was at the
CONSUMER -- a viewer without Plus Jakarta Sans got a substituted family, and for
a wordmark that means the mark is drawn wrong. So the two motives are:

  * build inputs -> outlined so the COMMITTED PNG BYTES stop moving;
  * served SVGs  -> outlined so the MARK IS RIGHT wherever it is displayed.

Converting a served file costs something a build input does not: the glyphs
leave the accessibility tree, so the mark stops being selectable, indexable and
readable by a screen reader. Anything converted and then SERVED must therefore
keep a textual alternative (`role="img"` + `aria-labelledby` -> non-empty
`<title>`), and must keep `fill="currentColor"` if it had it. Both are enforced
by `scripts/test-assets.py`, not left to whoever runs this script -- which is
also why `fill` is in INHERITED below rather than dropped with the other
text-only attributes.

FONTS
-----
Not vendored, on purpose -- the point of the conversion is that the repository
stops needing them. Fetch them from the upstream foundry releases, verify, and
point --fonts at the directory holding the three .ttf files:

  Inter 4.1            https://github.com/rsms/inter/releases/tag/v4.1
    Inter-4.1.zip                    sha256 9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e
    extras/ttf/Inter-Regular.ttf     sha256 40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82
    extras/ttf/Inter-Bold.ttf        sha256 288316099b1e0a47a4716d159098005eef7c0066921f34e3200393dbdb01947f
  Plus Jakarta Sans 2.7.1  https://github.com/tokotype/PlusJakartaSans/releases/tag/2.7.1
    PlusJakartaSans-2.7.1.zip        sha256 4bfc5cdf97d750423bb3d1d40ed8e529bc92288924d9c65e18ff486acefac66c
    ttf/PlusJakartaSans-Bold.ttf     sha256 14972f80fb151f32fb7129c6ad1893f6dd2a9d8bac30c40508c99e7f289b6682

Both are SIL Open Font License 1.1 and neither declares a Reserved Font Name.
Outlines drawn into a document are covered by the OFL's document exemption; see
`assets/brand/FONT-NOTICE.md` for the clause and the reasoning.

SHAPING
-------
Text is shaped with HarfBuzz -- the same engine Pango, and therefore
rsvg-convert, uses -- so kerning and mark positioning match what the <text>
element would have produced had the font been present. Diacritics are not
special-cased: they are shaped, and the script FAILS if shaping yields .notdef
for any cluster, which is what makes a silently accent-less conversion
impossible.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import uharfbuzz as hb
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# The first family of a CSS stack is the intended one; the rest were fallbacks
# for renderers that lacked it, which is exactly the dependency being removed.
FONT_FILES = {
    ("Inter", 400): "Inter-Regular.ttf",
    ("Inter", 700): "Inter-Bold.ttf",
    ("Plus Jakarta Sans", 700): "PlusJakartaSans-Bold.ttf",
}

# Presentation attributes that only mean something to a text layout engine. Once
# the glyphs are outlines they are noise, and leaving them behind would suggest
# a font lookup still happens.
TEXT_ONLY_ATTRS = ("font-family", "font-size", "font-weight", "letter-spacing", "text-anchor")
INHERITED = ("fill", *TEXT_ONLY_ATTRS)


def number(value: float) -> str:
    """Format a coordinate deterministically at 0.01 user-unit resolution."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0", "-") else text


class Face:
    """One font file, ready to shape with and to draw from."""

    def __init__(self, path: Path) -> None:
        self.path = path
        data = path.read_bytes()
        self.hb_font = hb.Font(hb.Face(data))
        self.tt = TTFont(path, lazy=True)
        self.upem = self.tt["head"].unitsPerEm
        self.hb_font.scale = (self.upem, self.upem)
        self.glyph_set = self.tt.getGlyphSet()

    def name_of(self, gid: int) -> str:
        return self.tt.getGlyphName(gid)


def shape(face: Face, text: str) -> list[dict[str, object]]:
    buf = hb.Buffer()
    buf.add_str(text)
    # Explicit rather than guessed: this repository is French, left-to-right,
    # Latin. Guessing would make the output depend on the input sample.
    buf.direction = "ltr"
    buf.script = "Latn"
    buf.language = "fr"
    hb.shape(face.hb_font, buf, {"kern": True, "liga": True})
    return [
        {
            "gid": info.codepoint,
            "name": face.name_of(info.codepoint),
            "cluster": info.cluster,
            "x_advance": pos.x_advance,
            "x_offset": pos.x_offset,
            "y_offset": pos.y_offset,
        }
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions)
    ]


def glyph_bounds(face: Face, name: str) -> list[float] | None:
    pen = RecordingPen()
    face.glyph_set[name].draw(pen)
    points: list[tuple[float, float]] = []
    for _, args in pen.value:
        for arg in args:
            if isinstance(arg, tuple):
                points.append(arg)
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def run_to_path(face: Face, run: dict[str, object], glyphs: list[dict[str, object]]) -> tuple[str, float]:
    size = float(run["font-size"])
    spacing = float(run["letter-spacing"])
    scale = size / face.upem

    # Anchoring width excludes trailing letter-spacing, per the SVG text layout
    # model. Moot for these two files -- no run combines a non-zero
    # letter-spacing with a non-start anchor -- but wrong is wrong.
    advance = sum(float(g["x_advance"]) for g in glyphs) * scale
    width = advance + spacing * max(len(glyphs) - 1, 0)

    anchor = run["text-anchor"]
    origin = float(run["x"])
    if anchor == "middle":
        origin -= width / 2
    elif anchor == "end":
        origin -= width

    baseline = float(run["y"])
    svg_pen = SVGPathPen(face.glyph_set, ntos=number)
    cursor = origin
    for glyph in glyphs:
        gx = cursor + float(glyph["x_offset"]) * scale
        gy = baseline - float(glyph["y_offset"]) * scale
        # Font space is y-up and SVG user space is y-down, hence the -scale.
        transform = Transform().translate(gx, gy).scale(scale, -scale)
        face.glyph_set[glyph["name"]].draw(TransformPen(svg_pen, transform))
        cursor += float(glyph["x_advance"]) * scale + spacing
    return svg_pen.getCommands(), width


def resolve(element: ET.Element, inherited: dict[str, str]) -> dict[str, str]:
    style = dict(inherited)
    for attr in INHERITED:
        if attr in element.attrib:
            style[attr] = element.attrib[attr]
    return style


def convert(tree: ET.ElementTree, fonts: Path, report: list[dict[str, object]]) -> None:
    faces: dict[str, Face] = {}

    def face_for(family_stack: str, weight: str) -> tuple[Face, str, int]:
        family = family_stack.split(",")[0].strip().strip("'\"")
        numeric = {"normal": 400, "bold": 700}.get(weight, weight)
        numeric = int(numeric)
        key = (family, numeric)
        if key not in FONT_FILES:
            raise SystemExit(f"no font mapped for {family!r} weight {numeric}")
        filename = FONT_FILES[key]
        if filename not in faces:
            path = fonts / filename
            if not path.is_file():
                raise SystemExit(f"missing font file: {path}")
            faces[filename] = Face(path)
        return faces[filename], family, numeric

    def walk(parent: ET.Element, inherited: dict[str, str]) -> None:
        for index, child in enumerate(list(parent)):
            style = resolve(child, inherited)
            if child.tag == f"{{{SVG_NS}}}text":
                text = "".join(child.itertext())
                run = {
                    "x": child.get("x", style.get("x", "0")),
                    "y": child.get("y", style.get("y", "0")),
                    "font-size": style["font-size"],
                    "letter-spacing": style.get("letter-spacing", "0"),
                    "text-anchor": style.get("text-anchor", "start"),
                }
                face, family, weight = face_for(style["font-family"], style.get("font-weight", "400"))
                glyphs = shape(face, text)

                notdef = [g for g in glyphs if g["gid"] == 0]
                if notdef:
                    raise SystemExit(
                        f"shaping produced .notdef for {text!r} in {face.path.name}: "
                        f"clusters {[g['cluster'] for g in notdef]}"
                    )

                commands, width = run_to_path(face, run, glyphs)
                if not commands.strip():
                    raise SystemExit(f"empty outline for {text!r}")

                path_el = ET.Element(f"{{{SVG_NS}}}path")
                path_el.set("fill", style["fill"])
                path_el.set("d", commands)
                path_el.tail = child.tail
                parent[index] = path_el

                report.append(
                    {
                        "text": text,
                        "font_file": face.path.name,
                        "family": family,
                        "weight": weight,
                        "font_size": float(run["font-size"]),
                        "letter_spacing": float(run["letter-spacing"]),
                        "text_anchor": run["text-anchor"],
                        "x": float(run["x"]),
                        "y": float(run["y"]),
                        "advance_width": round(width, 3),
                        "glyph_count": len(glyphs),
                        "non_ascii": [
                            {
                                "char": ch,
                                "codepoint": f"U+{ord(ch):04X}",
                                "unicode_name": unicodedata.name(ch, "?"),
                                "glyph": next(
                                    (g["name"] for g in glyphs if g["cluster"] == i),
                                    None,
                                ),
                            }
                            for i, ch in enumerate(text)
                            if ord(ch) > 127
                        ],
                        "glyphs": [g["name"] for g in glyphs],
                        "path_bytes": len(commands),
                    }
                )
            else:
                walk(child, style)

        for attr in TEXT_ONLY_ATTRS:
            parent.attrib.pop(attr, None)

    root = tree.getroot()
    walk(root, resolve(root, {}))
    for attr in TEXT_ONLY_ATTRS:
        root.attrib.pop(attr, None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", required=True, type=Path, help="directory holding the .ttf files")
    parser.add_argument("--report", type=Path, help="write the per-run measurement report as JSON")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    tree = ET.parse(args.source)
    report: list[dict[str, object]] = []
    convert(tree, args.fonts, report)

    ET.indent(tree, space="  ")
    header = (
        f"<!-- Generated from {args.source.name} by scripts/vectorize-svg-text.py. Do not edit by hand.\n"
        f"     Every glyph is an outline, so rendering depends on no installed font. -->\n"
    )
    args.output.write_text(
        header + ET.tostring(tree.getroot(), encoding="unicode", xml_declaration=False) + "\n",
        encoding="utf-8",
    )

    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for entry in report:
        accents = ", ".join(f"{a['char']} {a['codepoint']}->{a['glyph']}" for a in entry["non_ascii"])
        print(
            f"{entry['font_file']:28} {entry['font_size']:>5.0f}px  "
            f"{entry['glyph_count']:>3} glyphs  w={entry['advance_width']:>8.2f}  "
            f"{entry['text'][:44]!r}" + (f"  [{accents}]" if accents else "")
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
