#!/usr/bin/env python3
"""Offline check of turn_morph.py: draw the in-between head as SVG for each t.

    python3 scripts/turn_morph_svg.py right assets/preview/morph 0,0.25,0.5,0.75,1

Eyes, pupils and mouth come from the master and slide to where the 3/4 drawing
has them (the rig does the same), so the face reads as it will in Rive.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import turn_morph as tm  # noqa: E402

# master path index -> (rig part), and per side (dx, scale) as in head_turn.py
FEATURES = {20: "eyeL", 21: "eyeL", 22: "eyeR", 23: "eyeR", 24: "mouth"}
SHIFT = {"right": {"eyeR": (160.8, 0.916), "eyeL": (132.6, 0.854), "mouth": (155.3, 0.906)},
         "left": {"eyeR": (-127.7, 0.795), "eyeL": (-157.4, 0.962), "mouth": (-145.2, 0.92)}}


def curve(pts):
    n = len(pts)
    tan = [((pts[(i + 1) % n][0] - pts[i - 1][0]) / 6, (pts[(i + 1) % n][1] - pts[i - 1][1]) / 6) for i in range(n)]
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(n):
        j = (i + 1) % n
        d += (f"C {pts[i][0] + tan[i][0]:.1f} {pts[i][1] + tan[i][1]:.1f} {pts[j][0] - tan[j][0]:.1f} "
              f"{pts[j][1] - tan[j][1]:.1f} {pts[j][0]:.1f} {pts[j][1]:.1f} ")
    return d + "Z"


def hexcol(c):
    return "#" + c[3:]


def frame(side, t):
    p = tm.plan(side)
    master = tm.svg_paths("assets/vector/wayan_master.svg")
    centre, (fdx, fdy, fsx, fsy) = tm.flower_pose(side)
    sx, sy = 1 + (fsx - 1) * t, 1 + (fsy - 1) * t
    flower_tf = (f'transform="translate({centre[0] + fdx * t:.1f} {centre[1] + fdy * t:.1f}) '
                 f'scale({sx:.3f} {sy:.3f}) translate({-centre[0]:.1f} {-centre[1]:.1f})"')
    body = [f'<path fill="rgb{fill}" d="{d}"/>' for i, (fill, d) in enumerate(master) if i >= 26]
    head = []
    det_front, det_turn, (ddx, ddy) = tm.detail_paths(side)
    for name, mi, _, _ in tm.PARTS:
        if mi in ("FLOWER_BACK", "FLOWER_FRONT"):
            group = tm.flower_paths()[name]
            head.append(f"<g {flower_tf}>" + "".join(f'<path fill="rgb{f}" d="{d}"/>' for f, d in group) + "</g>")
            continue
        if mi == "DETAIL":
            # each set slides toward the other and they swap half way
            front_set = name == "knot_front"
            if front_set != (t < 0.5):
                continue
            k = t if front_set else t - 1
            paths = det_front if front_set else det_turn
            head.append(f'<g transform="translate({ddx * k:.1f} {ddy * k:.1f})">'
                        + "".join(f'<path fill="rgb{f}" d="{d}"/>' for f, d in paths) + "</g>")
            continue
        col, a, b = p[name]
        pts = [(x + (bx - x) * t, y + (by - y) * t) for (x, y), (bx, by) in zip(a, b)]
        head.append(f'<path fill="{hexcol(col)}" d="{curve(pts)}"/>')
    feats = []
    for i, part in FEATURES.items():
        fill, d = master[i]
        xs = [pt[0] for pt in tm.polyline(d, 6)]
        cx = (min(xs) + max(xs)) / 2
        if part.startswith("eye"):  # an eye's centre is its white's centre
            cx = {"eyeL": 823.5, "eyeR": 538.0}[part]
        dx, s = SHIFT[side][part]
        k = 1 + (s - 1) * t
        feats.append(f'<path fill="rgb{fill}" transform="translate({cx + dx * t:.1f} 0) scale({k:.3f} 1) '
                     f'translate({-cx:.1f} 0)" d="{d}"/>')
    # the nose is a morph part; draw features above everything
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="150 60 1050 1050">'
            f'<rect x="0" y="0" width="1347" height="2048" fill="#6ba8d2"/>{"".join(body)}{"".join(head)}{"".join(feats)}</svg>')


def main():
    side, out, ts = sys.argv[1], Path(sys.argv[2]), [float(t) for t in sys.argv[3].split(",")]
    out.mkdir(parents=True, exist_ok=True)
    for t in ts:
        (out / f"{side}_t{t:.2f}.svg").write_text(frame(side, t))
    print(len(ts), "frames ->", out)


if __name__ == "__main__":
    main()
