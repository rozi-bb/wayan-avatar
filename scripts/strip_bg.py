#!/usr/bin/env python3
"""Remove key-coloured background paths from a vectorized SVG.

Stdlib only -- no pip install needed.

Pairs with prep_bg.py: after a raster with a key-coloured background goes
through Recraft's /images/vectorize, every path whose fill is within
--tolerance of the key colour is dropped, leaving the character on a
transparent canvas ready for Rive. The C2PA <metadata> block is dropped too.

Recraft's default `hierarchical` stacking can paint key-coloured patches on
top of other shapes (e.g. the gap between an arm and the torso). Removing
those exposes whatever lies underneath, so always check the result on a
neutral background. If interior patches show up, re-vectorize with
`--shape-stacking cut_out`.

Usage:
    python3 scripts/strip_bg.py in.svg out.svg
    python3 scripts/strip_bg.py in.svg out.svg --key 1,124,251 --tolerance 60
"""

import argparse
import re

PATH_RE = re.compile(r"<path\b[^>]*?/>", re.S)
FILL_RE = re.compile(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"')
AREA_RE = re.compile(r'\bd="([^"]*)"')


def bbox_area(d):
    """Rough bounding-box area of a path, to tell the canvas rect from patches."""
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    if not xs or not ys:
        return 0
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--key", default="1,124,251", help="background colour as r,g,b")
    parser.add_argument("--tolerance", type=float, default=60,
                        help="max RGB distance from the key to count as background")
    args = parser.parse_args()

    key = tuple(int(v) for v in args.key.split(","))
    svg = open(args.src).read()
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)

    removed, kept = [], 0

    def drop_if_key(match):
        nonlocal kept
        tag = match.group(0)
        fill = FILL_RE.search(tag)
        if fill:
            rgb = tuple(int(c) for c in fill.groups())
            dist = sum((a - b) ** 2 for a, b in zip(rgb, key)) ** 0.5
            if dist <= args.tolerance:
                d = AREA_RE.search(tag)
                removed.append((rgb, bbox_area(d.group(1)) if d else 0))
                return ""
        kept += 1
        return tag

    svg = PATH_RE.sub(drop_if_key, svg)
    open(args.dst, "w").write(svg)

    print(f"kept {kept} paths, removed {len(removed)} -> {args.dst}")
    for rgb, area in sorted(removed, key=lambda r: -r[1]):
        print(f"  removed fill rgb{rgb}  bbox area {area:,.0f}")


if __name__ == "__main__":
    main()
