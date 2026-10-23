#!/usr/bin/env python3
"""Import the torso of a whole-body pose SVG into the Rive rig as one group.

Pose SVGs (arms_crossed.svg, hands_together.svg) share the master's canvas, so
their torso lines up with the rig. Only paths that start below the chin and
above the feet are taken (shirt, arms, hands, neck, sash, sarong); the rig keeps
its own head and feet. Colours snap to the rig's palette. The group lands in
Body (so it sways and breathes with it) at opacity 0, ready for an action to
swap it in.

    python3 scripts/pose_to_rive.py assets/vector/hands_together.svg Salam --upper

--upper keeps only the shirt, arms and hands, cut off just below the top of
the sash, so the rig's own sash and sarong (which fit the body exactly) stay
in use. Without it the pose's sash and sarong come along too.

Needs the Rive editor open on "wayan".
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

BODY = "0-730"
BODY_POS = (680.0, 1290.0)   # Body origin in master SVG units
TOP, FEET = 900, 1700        # torso = paths whose top edge is in [TOP, FEET)
SASH_TOP = 1258              # master SVG y just below the top of the rig's sash
SASH_X = (360, 1000)         # the sash's width plus a margin; the cut only applies here,
                             # so the sleeves keep their round ends
LOWER = {"#fff5bf03", "#ffe9a601", "#ff45933a", "#ff30792b"}  # sash and sarong colours
PALETTE = {
    "#ffefab81": (239, 171, 129), "#ffd69067": (214, 144, 103), "#ffededec": (237, 237, 236),
    "#ffd3d2d2": (211, 210, 210), "#fff5bf03": (245, 191, 3), "#ffe9a601": (233, 166, 1),
    "#ff45933a": (69, 147, 58), "#ff30792b": (48, 121, 43),
}


def paths(svg):
    for attrs in re.findall(r"<path([^>]*)>", svg):
        fill = tuple(map(int, re.search(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"', attrs).groups()))
        d = re.search(r'd="([^"]+)"', attrs).group(1)
        yield fill, d


def commands(d, max_y=None):
    tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, i, ys = [], 0, []
    def clamp(x, y):
        inside = max_y and SASH_X[0] <= float(x) <= SASH_X[1]
        return min(float(y), max_y) if inside else float(y)
    pt = lambda x, y: (round(float(x) - BODY_POS[0], 2), round(clamp(x, y) - BODY_POS[1], 2))
    while i < len(tokens):
        t = tokens[i]
        if t in "Zz":
            out.append({"commandType": "close"}); i += 1; continue
        n = {"M": 2, "L": 2, "C": 6}[t]
        i += 1
        while i < len(tokens) and tokens[i] not in "MLCZz":
            a = tokens[i:i + n]; i += n
            ys += [float(v) for v in a[1::2]]
            if t == "C":
                (c1x, c1y), (c2x, c2y), (ex, ey) = pt(*a[0:2]), pt(*a[2:4]), pt(*a[4:6])
                out.append({"commandType": "cubicTo", "control1X": c1x, "control1Y": c1y,
                            "control2X": c2x, "control2Y": c2y, "endX": ex, "endY": ey})
            else:
                x, y = pt(*a)
                out.append({"commandType": "moveTo" if t == "M" else "lineTo", "x": x, "y": y})
                t = "L" if t == "M" else t
    return out, min(ys)


def main():
    svg_path, name = sys.argv[1], sys.argv[2]
    upper = "--upper" in sys.argv
    shapes = []
    for n, (fill, d) in enumerate(paths(Path(svg_path).read_text())):
        cmds, top = commands(d, SASH_TOP if upper else None)
        if not TOP <= top < FEET:
            continue
        color = min(PALETTE, key=lambda c: sum((PALETTE[c][k] - fill[k]) ** 2 for k in range(3)))
        if upper and (color in LOWER or top >= SASH_TOP):
            continue
        shapes.append({"name": f"Pose_{name}_{n}", "parentId": BODY, "x": 0, "y": 0,
                       "paints": [{"paintType": "fill", "color": color}],
                       "paths": [{"name": "Path", "commands": cmds}]})

    session, _ = m.post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "pose", "version": "1"}}})
    ids = [1]

    def call(tool, args):
        ids[0] += 1
        _, raw = m.post({"jsonrpc": "2.0", "id": ids[0], "method": "tools/call",
                         "params": {"name": tool, "arguments": args}}, session)
        return json.loads(m.parse(raw)["result"]["content"][0]["text"])

    r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": shapes}}})
    if not r.get("success"):
        sys.exit(json.dumps(r)[:500])
    found = call("find_objects", {"name": f"Pose_{name}_", "parentId": BODY})["objects"]
    group = call("group_editor", {"name": f"Pose_{name}", "objectIds": [o["id"] for o in found]})["group"]
    call("set_property_values", {"propertyValues": {group["id"]: {"18": 0}}})
    print(json.dumps({"group": group["id"], "shapes": len(shapes)}))


if __name__ == "__main__":
    main()
