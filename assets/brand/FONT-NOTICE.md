# Fonts used to draw the composed sheets

`social-card.svg` and `icon-size-sheet.svg` contain no `<text>`. Every glyph in
them is a `<path>`, produced once by `scripts/vectorize-svg-text.py` from the
editable `*-source.svg` files next to them.

This note records which fonts drew those outlines, where they came from, and why
the result may be published here. It is not a licence obligation — see the
verdict below — it is provenance.

## Why outlines at all

`.github/workflows/ci.yml` re-renders these sheets and gates the bytes with
`git diff --exit-code`. While the SVGs asked for a font _by name_, those bytes
depended on the set of font families installed on the runner. That set comes
from the runner image, and it is the one rendering input that
`apt-get install <package>=<version>` cannot pin.

The cost was measured, not assumed. Run `30193088312` compared the committed
bytes to a regeneration on a fully pinned toolchain:

| Asset                              | Samples differing              | Cause                            |
| ---------------------------------- | ------------------------------ | -------------------------------- |
| `apps/web/assets/social-card.png`  | 125 239 / 2 268 000 (5.5220 %) | font substitution                |
| `proofs/brand/icon-size-sheet.png` | 40 274 / 1 728 000 (2.3307 %)  | font substitution                |
| the six PNGs carrying no text      | 0                              | — (container only, since pinned) |

Neither Inter nor Plus Jakarta Sans is installed on `ubuntu-24.04`, so fontconfig
substituted a generic family and the social card's title grew wide enough to
reach the icon. Outlines end that dependency: a `<path>` is geometry, and the
rasteriser resolves no font to draw it.

## Provenance

Downloaded from the upstream foundry releases, not a mirror or a CDN.

### Inter 4.1 — <https://github.com/rsms/inter/releases/tag/v4.1>

| File                           | SHA-256                                                            |
| ------------------------------ | ------------------------------------------------------------------ |
| `Inter-4.1.zip`                | `9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e` |
| `extras/ttf/Inter-Regular.ttf` | `40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82` |
| `extras/ttf/Inter-Bold.ttf`    | `288316099b1e0a47a4716d159098005eef7c0066921f34e3200393dbdb01947f` |
| `LICENSE.txt`                  | `262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a` |

`Copyright (c) 2016 The Inter Project Authors (https://github.com/rsms/inter)`

### Plus Jakarta Sans 2.7.1 — <https://github.com/tokotype/PlusJakartaSans/releases/tag/2.7.1>

| File                           | SHA-256                                                            |
| ------------------------------ | ------------------------------------------------------------------ |
| `PlusJakartaSans-2.7.1.zip`    | `4bfc5cdf97d750423bb3d1d40ed8e529bc92288924d9c65e18ff486acefac66c` |
| `ttf/PlusJakartaSans-Bold.ttf` | `14972f80fb151f32fb7129c6ad1893f6dd2a9d8bac30c40508c99e7f289b6682` |
| `OFL.txt`                      | `995c7199cab65954f545996326755daee7b63cc6b42b06c13da1f9502ab08a99` |

`Copyright 2020 The Plus Jakarta Sans Project Authors (https://github.com/tokotype/PlusJakartaSans)`

**Neither font is vendored in this repository, deliberately.** Shipping the `.ttf`
files would be distribution of Font Software, which _does_ trigger OFL condition
2 (each copy must carry the copyright notice and the licence). Converting to
outlines is precisely what makes the fonts unnecessary here, so the repository
keeps none.

## Licence verdict: permitted, no attribution required

Both fonts are under the **SIL Open Font License 1.1**, and **neither declares a
Reserved Font Name** — in both files the phrase occurs once, inside the licence's
own DEFINITIONS section, and nothing follows the copyright statement. OFL
condition 3 is therefore inapplicable in every reading.

The outlines are a _document_, not Font Software. OFL 1.1 defines Font Software
as "the set of files released by the Copyright Holder(s) under this license and
clearly marked as such"; a generated SVG is neither released nor marked by them.
Condition 5 then closes the question:

> The Font Software, modified or unmodified, in part or in whole, must be
> distributed entirely under this license, and must not be distributed under any
> other license. **The requirement for fonts to remain under this license does not
> apply to any document created using the Font Software.**

SIL's own OFL-FAQ (v1.1-update7) addresses the operation directly. Question 1.1
permits using the fonts "to create logos or other graphics, or even to
manufacture objects **based on their outlines**", listing "3D-printed/laser-cut
shapes" — outline extraction is the named, blessed mechanism. Question 1.13 adds
that "creating any kind of graphic using a font under the OFL does not make the
resulting artwork subject to the OFL", and 1.1.1 that "you remain the author and
copyright holder of that newly derived graphic". On acknowledgement, 1.1.2 is
explicit: "No. … that is not required."

_Honest limit of that reading:_ the OFL-FAQ contains no question phrased as
"convert text to outlines". The verdict rests on the general answers above,
which cover the operation by their own terms, not on an exactly-worded entry.

Where the answer would flip: outline data becomes Font Software again if it is
reassembled into something installable or usable to render arbitrary text — an
SVG font, an `@font-face` asset, or a codepoint-keyed glyph sheet. Two fixed
strings of `<path>` elements are not that.

> OFL 1.1 and OFL-FAQ quotations: copyright (c) 2005-2023 SIL International, used
> by permission — <https://openfontlicense.org/documents/OFL.txt> and
> <https://openfontlicense.org/documents/OFL-FAQ.txt>.

Trademark is a separate regime the OFL does not touch (OFL-FAQ 3.7). The marks
in these sheets stay governed by `assets/brand/LICENSE.md`.

## Regenerating

Only needed when the wording, size or position of the text changes. Edit the
`*-source.svg` file, fetch the fonts above into one directory, and run:

```sh
uv run --script scripts/vectorize-svg-text.py \
  --fonts <directory holding the three .ttf files> \
  assets/brand/social-card-source.svg assets/brand/social-card.svg
```

The script refuses to emit anything if shaping yields `.notdef` for any cluster,
so a conversion that silently lost the French diacritics cannot be committed.
Both files keep the `__ICON_DATA__` placeholder, which `scripts/generate-assets.sh`
replaces with the current `icon.svg` at build time; they are build inputs, never
served.
