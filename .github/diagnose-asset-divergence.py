#!/usr/bin/env python3
"""TEMPORARY diagnostic: why do the committed PNGs differ from a regeneration?

Runs after `scripts/generate-assets.sh` in CI. For every path git reports as
changed, it compares the committed blob (`git show HEAD:<path>`) with the file
now on disk at three levels, so that "the toolchain renders differently" can be
told apart from "the encoder writes a different container around identical
pixels":

  1. chunk inventory (which PNG chunks each side carries, and their lengths),
  2. IHDR fields (dimensions, bit depth, colour type, interlacing),
  3. decoded pixels (IDAT inflated and unfiltered, then compared byte for byte).

This file is deleted once the cause is established. Stdlib only: it must run on
the CI runner without installing anything.
"""

from __future__ import annotations

import struct
import subprocess
import sys
import zlib
from pathlib import Path

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def changed_paths() -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "-z", "--", "assets/brand", "apps/web/assets", "proofs/brand"]
    )
    return [raw.decode() for raw in out.split(b"\0") if raw]


def committed_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"])


def chunks(data: bytes) -> list[tuple[str, int, bytes]]:
    if data[:8] != SIGNATURE:
        raise ValueError("not a PNG")
    offset, out = 8, []
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8].decode("latin1")
        out.append((kind, length, data[offset + 8 : offset + 8 + length]))
        offset += 12 + length
    return out


def ihdr(parsed: list[tuple[str, int, bytes]]) -> dict[str, int]:
    body = next(body for kind, _, body in parsed if kind == "IHDR")
    width, height, depth, colour, compression, filt, interlace = struct.unpack(">IIBBBBB", body)
    return {
        "width": width,
        "height": height,
        "bit_depth": depth,
        "colour_type": colour,
        "compression": compression,
        "filter": filt,
        "interlace": interlace,
    }


def unfilter(raw: bytes, width: int, height: int, bpp: int) -> bytes:
    stride = width * bpp
    out = bytearray()
    previous = bytearray(stride)
    cursor = 0
    for _ in range(height):
        kind = raw[cursor]
        cursor += 1
        line = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        if kind == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 0xFF
        elif kind == 2:
            for x in range(stride):
                line[x] = (line[x] + previous[x]) & 0xFF
        elif kind == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + previous[x]) >> 1)) & 0xFF
        elif kind == 4:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                upper_left = previous[x - bpp] if x >= bpp else 0
                up = previous[x]
                estimate = left + up - upper_left
                da, db, dc = (
                    abs(estimate - left),
                    abs(estimate - up),
                    abs(estimate - upper_left),
                )
                if da <= db and da <= dc:
                    line[x] = (line[x] + left) & 0xFF
                elif db <= dc:
                    line[x] = (line[x] + up) & 0xFF
                else:
                    line[x] = (line[x] + upper_left) & 0xFF
        elif kind != 0:
            raise ValueError(f"unknown filter type {kind}")
        out += line
        previous = line
    return bytes(out)


def pixels(data: bytes) -> tuple[bytes, int]:
    """Decoded samples plus bytes-per-pixel, for a non-interlaced 8-bit image."""
    parsed = chunks(data)
    header = ihdr(parsed)
    if header["interlace"] != 0 or header["bit_depth"] != 8:
        raise ValueError("diagnostic only decodes non-interlaced 8-bit images")
    if header["colour_type"] == 3:
        raise ValueError("diagnostic does not decode palette images")
    bpp = CHANNELS[header["colour_type"]]
    raw = zlib.decompress(b"".join(body for kind, _, body in parsed if kind == "IDAT"))
    return unfilter(raw, header["width"], header["height"], bpp), bpp


def describe(label: str, data: bytes) -> None:
    parsed = chunks(data)
    inventory = ", ".join(f"{kind}({length})" for kind, length, _ in parsed)
    print(f"    {label}: {len(data)} bytes | {ihdr(parsed)}")
    print(f"    {label}: chunks {inventory}")


def compare_png(path: str) -> None:
    before, after = committed_bytes(path), Path(path).read_bytes()
    describe("committed", before)
    describe("generated", after)
    try:
        left, bpp = pixels(before)
        right, other_bpp = pixels(after)
    except ValueError as error:
        print(f"    pixels: NOT COMPARED ({error})")
        return
    if bpp != other_bpp:
        print(f"    pixels: channel count differs ({bpp} vs {other_bpp})")
        return
    if left == right:
        print(f"    pixels: IDENTICAL ({len(left)} samples) -> container/encoder difference only")
        return
    differing = sum(1 for a, b in zip(left, right) if a != b)
    worst = max((abs(a - b) for a, b in zip(left, right)), default=0)
    print(
        f"    pixels: DIFFERENT -- {differing}/{len(left)} samples "
        f"({100 * differing / len(left):.4f}%), max channel delta {worst}"
        " -> the rendering itself changed"
    )


def main() -> int:
    paths = changed_paths()
    if not paths:
        print("no divergence: the committed tree already matches this toolchain")
        return 0
    print(f"{len(paths)} diverging paths")
    for path in paths:
        print(f"  {path}")
        if path.endswith(".png"):
            compare_png(path)
        else:
            print("    (not a PNG -- see `git diff` above)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
