#!/usr/bin/env python3
"""Swap a near-white background for a key colour before vectorizing.

Stdlib only -- no pip install needed.

Recraft's vectorizer merges near-white garments into a near-white background
(Wayan's shirt is rgb(239,239,238), the background rgb(253,253,252), so the
shirt vanished). Flood-filling the background from the image border with a
colour that appears nowhere on the character keeps every garment as its own
shape. Delete the key-coloured path from the SVG afterwards.

Only pixels connected to the border are recoloured, so enclosed white areas
such as the whites of the eyes are left alone.

Usage:
    python3 scripts/prep_bg.py in.png out.png
    python3 scripts/prep_bg.py in.png out.png --threshold 246 --key 0,120,255
"""

import argparse
import struct
import sys
import zlib
from collections import deque

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def read_png(path):
    data = open(path, "rb").read()
    if data[:8] != PNG_SIG:
        sys.exit(f"{path} is not a PNG")
    pos, idat = 8, b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length

    if depth != 8 or ctype not in (2, 6) or interlace:
        sys.exit("only 8-bit, non-interlaced RGB or RGBA PNGs are supported")
    bpp = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)

    # Undo the per-row PNG filters (None, Sub, Up, Average, Paeth).
    for y in range(h):
        ftype = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        rows.append(line)
        prev = line
    return w, h, bpp, rows


def write_png(path, w, h, rows):
    """Write as 8-bit RGB with no filtering."""
    def chunk(kind, body):
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc)

    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(PNG_SIG + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--threshold", type=int, default=246,
                        help="a pixel is background if every channel is >= this")
    parser.add_argument("--key", default="0,120,255",
                        help="replacement colour as r,g,b")
    args = parser.parse_args()

    key = tuple(int(v) for v in args.key.split(","))
    w, h, bpp, rows = read_png(args.src)
    rgb = [[tuple(row[x * bpp:x * bpp + 3]) for x in range(w)] for row in rows]

    def is_bg(x, y):
        return min(rgb[y][x]) >= args.threshold

    seen = [[False] * w for _ in range(h)]
    queue = deque()
    for x in range(w):
        queue.extend([(x, 0), (x, h - 1)])
    for y in range(h):
        queue.extend([(0, y), (w - 1, y)])

    filled = 0
    while queue:
        x, y = queue.popleft()
        if seen[y][x] or not is_bg(x, y):
            continue
        seen[y][x] = True
        rgb[y][x] = key
        filled += 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]:
                queue.append((nx, ny))

    out_rows = [bytearray(b for px in line for b in px) for line in rgb]
    write_png(args.dst, w, h, out_rows)
    print(f"recoloured {filled} of {w * h} px ({100 * filled / (w * h):.1f}%) -> {args.dst}")


if __name__ == "__main__":
    main()
