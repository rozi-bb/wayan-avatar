#!/usr/bin/env python3
"""Turn assets/vector/hands.svg into Rive createShapes payloads, one per arm.

Each hand pose becomes shapes parented to the forearm bone, already placed in
bone space with fingers pointing along it. The wrist starts inside the old round
hand (Hand_L/R), which stays visible as the cuff: the sleeve runs under it, and
the pose's wrist stub disappears into the same skin colour. The sheet
holds right hands; the left arm gets a mirrored copy. Colours are snapped to
Wayan's own skin and crease colours.

    python3 scripts/hands_to_rive.py out_dir

Writes out_dir/hands_R.json and out_dir/hands_L.json for scripts/rive_mcp.py.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCALE = 0.75

# Pose -> SVG path indices, bottom to top, and where the wrist is on the sheet.
# "up": fingers point up, wrist at the bottom. "right": wrist on the left.
POSES = {
    "Open":  ([0, 1], "up"),
    "Thumb": ([2, 3, 4], "right"),
    "Point": ([11, 12, 13], "up"),
    "Fist":  ([5, 6, 7], "up"),
    "Side":  ([14, 15, 16, 17], "right"),
    "Peace": ([8, 9, 10], "up"),
}
COLORS = {(237, 170, 126): "#ffefab81", (204, 132, 93): "#ffd69067"}

# Forearm bone id, wrist point in bone space (just inside the round hand, which
# spans about 172-362 along the bone), mirror the sheet?
ARMS = {
    "R": ("0-735", (212.0, -8.35), False),
    "L": ("0-733", (217.0, -4.59), True),
}


def parse_paths(svg):
    out = []
    for attrs in re.findall(r"<path([^>]*)>", svg):
        fill = tuple(map(int, re.search(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"', attrs).groups()))
        d = re.search(r'd="([^"]+)"', attrs).group(1)
        tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
        cmds, i = [], 0
        while i < len(tokens):
            t = tokens[i]
            if t in "Zz":
                cmds.append(("Z", []))
                i += 1
                continue
            n = {"M": 2, "L": 2, "C": 6}[t]
            i += 1
            while i < len(tokens) and tokens[i] not in "MLCZz":
                cmds.append((t, list(map(float, tokens[i:i + n]))))
                i += n
                t = "L" if t == "M" else t  # implicit lineto after moveto
        out.append((fill, cmds))
    return out


def bbox(cmds):
    xs = [v for _, a in cmds for v in a[0::2]]
    ys = [v for _, a in cmds for v in a[1::2]]
    return min(xs), min(ys), max(xs), max(ys)


def payload(side):
    bone, (wx, wy), mirror = ARMS[side]
    paths = parse_paths((ROOT / "assets/vector/hands.svg").read_text())
    shapes = []
    for pose, (idx, kind) in POSES.items():
        boxes = [bbox(paths[i][1]) for i in idx]
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        anchor = ((x0 + x1) / 2, y1) if kind == "up" else (x0, (y0 + y1) / 2)

        def place(x, y):
            qx, qy = (x - anchor[0]) * SCALE, (y - anchor[1]) * SCALE
            if mirror:
                qx = -qx if kind == "up" else qx
                qy = qy if kind == "up" else -qy
            if kind == "up":  # fingers along -y on the sheet -> along the bone (+x)
                qx, qy = -qy, qx
            return round(wx + qx, 2), round(wy + qy, 2)

        for n, i in enumerate(idx, 1):
            fill, cmds = paths[i]
            out = []
            for c, a in cmds:
                if c == "M":
                    x, y = place(*a); out.append({"commandType": "moveTo", "x": x, "y": y})
                elif c == "L":
                    x, y = place(*a); out.append({"commandType": "lineTo", "x": x, "y": y})
                elif c == "C":
                    (c1x, c1y), (c2x, c2y), (ex, ey) = place(*a[0:2]), place(*a[2:4]), place(*a[4:6])
                    out.append({"commandType": "cubicTo", "control1X": c1x, "control1Y": c1y,
                                "control2X": c2x, "control2Y": c2y, "endX": ex, "endY": ey})
                else:
                    out.append({"commandType": "close"})
            color = min(COLORS, key=lambda c: sum((c[k] - fill[k]) ** 2 for k in range(3)))
            shapes.append({"name": f"Hand_{side}_{pose}_{n}", "parentId": bone, "x": 0, "y": 0,
                           "paints": [{"paintType": "fill", "color": COLORS[color]}],
                           "paths": [{"name": "Path", "commands": out}]})
    return {"command": "createShapes", "data": {"createShapes": {"shapes": shapes}}}


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    for side in ARMS:
        (out_dir / f"hands_{side}.json").write_text(json.dumps(payload(side)))
        print("wrote", out_dir / f"hands_{side}.json")
