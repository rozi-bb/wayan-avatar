#!/usr/bin/env python3
"""Import a three-quarter head drawing (Gemini, vectorized) into the rig's HeadLook.

The 3/4 SVGs share the master's canvas, so the head lines up with the rig. Only
the head is taken (skin, udeng, hair, ear, flower, nose); the drawing's own eyes,
pupils and mouth are dropped because the rig's eyes, brows and mouth sit on top
(blink, lipsync and expressions keep working). Colours snap to the rig's palette.
The group lands in HeadLook at opacity 0; the turn binds swap it in.

    python3 scripts/head34_to_rive.py left
    python3 scripts/head34_to_rive.py right

Needs the Rive editor open on "wayan".
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HEADLOOK = "0-2127"
HEAD_POS = (690.0, 990.0)  # Head origin (the neck) in master SVG units; HeadLook sits on it at rest
HEAD_BOTTOM = 990          # paths starting below this are the body (shirt, neck, shirt lines)
BODY_TOP = 1150            # ...and so are paths reaching below this (the shirt starts at the shoulders)
# Path indices of the drawing's eye whites, pupils and mouth (plus a stray cream sliver on
# an eye edge), read from the SVG: the rig draws these itself.
DROP = {"left": {19, 20, 21, 22, 23}, "right": {13, 14, 15, 16, 17, 18}}
PALETTE = {
    "#ffefab81": (239, 171, 129), "#ffd69067": (214, 144, 103), "#ffededec": (237, 237, 236),
    "#ffd3d2d2": (211, 210, 210), "#fff5bf03": (245, 191, 3), "#ffe9a601": (233, 166, 1),
    "#ffc87915": (200, 121, 21), "#ff3f3e3f": (63, 62, 63),
}


def paths(svg):
    for attrs in re.findall(r"<path([^>]*)>", svg):
        fill = tuple(map(int, re.search(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"', attrs).groups()))
        yield fill, re.search(r'd="([^"]+)"', attrs).group(1)


def commands(d):
    """SVG path data (M/L/C/Z, absolute) to Rive commands in HeadLook units, and its top and bottom y."""
    tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pt = lambda x, y: (round(float(x) - HEAD_POS[0], 2), round(float(y) - HEAD_POS[1], 2))
    out, i, ys = [], 0, []
    while i < len(tokens):
        t = tokens[i]
        if t in "Zz":
            out.append({"commandType": "close"})
            i += 1
            continue
        n = {"M": 2, "L": 2, "C": 6}[t]
        i += 1
        while i < len(tokens) and tokens[i] not in "MLCZz":
            a = tokens[i:i + n]
            i += n
            ys += [float(v) for v in a[1::2]]
            if t == "C":
                (c1x, c1y), (c2x, c2y), (ex, ey) = pt(*a[0:2]), pt(*a[2:4]), pt(*a[4:6])
                out.append({"commandType": "cubicTo", "control1X": c1x, "control1Y": c1y,
                            "control2X": c2x, "control2Y": c2y, "endX": ex, "endY": ey})
            else:
                x, y = pt(*a)
                out.append({"commandType": "moveTo" if t == "M" else "lineTo", "x": x, "y": y})
                t = "L" if t == "M" else t
    return out, min(ys), max(ys)


def main():
    side = sys.argv[1]
    name = {"left": "Head34_L", "right": "Head34_R"}[side]
    svg = (ROOT / f"assets/vector/head34_{side}.svg").read_text()
    shapes = []
    for n, (fill, d) in enumerate(paths(svg)):
        cmds, top, bottom = commands(d)
        if top >= HEAD_BOTTOM or bottom > BODY_TOP or n in DROP[side]:
            continue
        color = min(PALETTE, key=lambda c: sum((PALETTE[c][k] - fill[k]) ** 2 for k in range(3)))
        shapes.append({"name": f"{name}_{n}", "parentId": HEADLOOK, "x": 0, "y": 0,
                       "paints": [{"paintType": "fill", "color": color}],
                       "paths": [{"name": "Path", "commands": cmds}]})

    call = m.connect("head34")
    r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": shapes}}})
    if not r.get("success", True) or r.get("errors"):
        sys.exit(str(r)[:500])
    found = call("find_objects", {"name": f"{name}_", "parentId": HEADLOOK})["objects"]
    shape_ids = [o["id"] for o in found if o["type"] == "Shape"]
    # New fills default to the clockwise fill rule, which drops counter-clockwise paths: use non-zero.
    fills = [o["id"] for o in call("query_objects", {"objectIds": shape_ids, "depth": 1})["objects"]
             if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})
    group = call("group_editor", {"name": name, "objectIds": shape_ids})["group"]
    call("set_property_values", {"propertyValues": {group["id"]: {"18": 0}}})
    print(name, group["id"], len(shape_ids), "shapes")


if __name__ == "__main__":
    main()
