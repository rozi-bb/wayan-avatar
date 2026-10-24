#!/usr/bin/env python3
"""Shapes for the udeng-slip idle (Wayan pushes his slipping udeng back up).

From the master SVG and the Recraft bare-head inpaint (assets/vector/bare_head_raw.svg,
same canvas as the master), writes assets/vector/udeng_slip.svg with, in order:

    0-2  udeng pieces (master 1, 2, 8) minus the hair in front of them (master 9), so the
         udeng can slide in front of that hair and the rest pose still looks the same
    3    bare hair: the inpaint's hair silhouette, one colour (Wayan's hair), no outline
    4    bare skin: the inpaint's forehead skin, Wayan's skin colour

The bare pieces are cut to the head parts that cover them at rest and turn with them (udeng,
knot, folds, flower, hair), shrunk by EDGE and rounded, so at rest and on head turns nothing new
shows; they only appear where the udeng slides away.

Needs shapely (not in the stdlib): python3 -m venv venv && venv/bin/pip install shapely

    venv/bin/python scripts/udeng_geom.py
"""

import sys
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svg_tools as tools  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/vector/udeng_slip.svg"
HAIR, SKIN = (63, 62, 63), (239, 171, 129)
# Head parts over the bare pieces: those that move with them when the head turns (udeng, hair,
# knot, folds, flower and the ear in its block). Not Wayan's right ear or the sideburn: they
# move by other amounts, and the bare hair would peek out beside them.
COVER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19]
EDGE = 2.0          # how far inside the covering parts the bare pieces stop
SMOOTH = 22         # radius that rounds the corners the cut leaves (and fills the tuft's notch)
# Over the crown the hair's top follows a curve that leaves the old hair's flat top (y HAIR_TOP
# at x CROWN_X) level and rises to the left, so the two meet without a step.
HAIR_TOP, CROWN_X, CEIL_RISE = 154.0, 600.0, 0.00066
# Below the band's right end the hair widens out of the old hair's edge (x at the band's top,
# BAND_TOP) to the inpaint's edge over RIGHT_EASE units, instead of stepping out.
BAND_TOP, RIGHT_EASE, RIGHT_WIDEN = 300.0, 80.0, 90.0
FOREHEAD = box(360, 240, 1020, 640)  # the skin is only seen between the fringe's points
TOL = 0.4           # outline simplification (SVG units)


def poly(d):
    p = Polygon(tools.polyline(d, step=1.0))
    return p if p.is_valid else p.buffer(0)


def parts(geom):
    geoms = getattr(geom, "geoms", [geom])
    return [g for g in geoms if g.geom_type == "Polygon" and g.area > 40]


def path_d(geom):
    out = []
    for g in parts(geom.simplify(TOL)):  # outlines only: the skin's two pinholes sit under the flower
        pts = list(g.exterior.coords)[:-1]
        out.append("M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z")
    return " ".join(out)


def ceiling():
    """Region below the hair's highest line: level at HAIR_TOP right of CROWN_X, rising to the left."""
    top = [(x, HAIR_TOP - CEIL_RISE * max(CROWN_X - x, 0) ** 2) for x in range(0, 1348, 8)]
    return Polygon(top + [(1347, 2048), (0, 2048)])


def right_side(hair9):
    """Everything left of the old hair's right edge, widening smoothly below the band's top."""
    x0 = max(x for x, y in hair9.exterior.coords if BAND_TOP - 5 < y < BAND_TOP + 5)
    pts = [(0, 0), (x0, 0)]
    for k in range(41):
        t = k / 40
        pts.append((x0 + RIGHT_WIDEN * t * t * (3 - 2 * t), BAND_TOP + RIGHT_EASE * t))
    return Polygon(pts + [(1347, BAND_TOP + RIGHT_EASE), (1347, 2048), (0, 2048)])


def main():
    master = tools.svg_paths("assets/vector/wayan_master.svg")
    bare = tools.svg_paths("assets/vector/bare_head_raw.svg")
    hair9 = poly(master[9][1])
    pieces = [(master[i][0], poly(master[i][1]).difference(hair9)) for i in (1, 2, 8)]

    cover = unary_union([poly(master[i][1]) for i in COVER]).buffer(-EDGE)
    hidden = cover.union(hair9)  # the old hair shows at rest, so the new hair may fill it too
    hair = poly(bare[2][1]).intersection(cover).union(hair9)
    hair = hair.buffer(SMOOTH).buffer(-SMOOTH).intersection(hidden)  # fill notches, but stay hidden
    hair = hair.intersection(ceiling()).buffer(-SMOOTH).buffer(SMOOTH).intersection(right_side(hair9))
    skin = poly(bare[1][1]).intersection(cover).intersection(FOREHEAD)
    pieces += [(HAIR, hair), (SKIN, skin)]

    body = "\n".join(f'<path fill="rgb({f[0]},{f[1]},{f[2]})" d="{path_d(g)}"/>'
                     for f, g in pieces)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1347 2048" width="1347" height="2048">\n'
                   f'{body}\n</svg>\n')
    for name, (_, g) in zip(["udeng 1", "udeng 2", "udeng 8", "bare hair", "bare skin"], pieces):
        ps = parts(g.simplify(TOL))
        print(f"{name}: {len(ps)} piece(s), holes {sum(len(p.interiors) for p in ps)}, "
              f"points {sum(len(p.exterior.coords) for p in ps)}, area {g.area:.0f}")
    print("->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
