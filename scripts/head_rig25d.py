#!/usr/bin/env python3
"""Clean 2.5D head layers for the head turn: rigid pieces that slide by depth.

Rebuilds the head from the master SVG as separate groups in HeadLook, each with
its origin at (0, 0) so the turn binds can slide it by a plain offset:

    Head25_Skin    the face skin, trimmed to the face: its top is flattened under
                   the udeng and the ear bulges are cut off, so nothing the other
                   layers uncover was ever drawn by the skin
    Head25_Udeng   udeng band and crown, plus the dark hair behind it (moves a little)
    Head25_Knot    the knot and short fold on the front of the udeng (moves most)
    Head25_Fold    the long fold from the udeng's edge to the knot: pinned at the
                   edge (its group origin) and stretched by the turn binds
    Head25_Flower  flower plus Wayan's left ear (right of the picture): one block, so
                   the petal tucked behind the ear never slides out
    Head25_EarR    Wayan's right ear (left of the picture), moves against the turn
    Head25_Side    the sideburn

The silhouette stays round because only the skin defines it and the skin never
moves. The rig's eyes, brows, nose and mouth stay on top.

    python3 scripts/head_rig25d.py build

Needs the Rive editor open on "wayan".
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402
import turn_morph as tm  # noqa: E402  (SVG parsing, resampling, palette)

HEADLOOK = "0-2127"
CACHE = Path(__file__).with_name(".head25.json")
# Master SVG path indices per layer, bottom to top as the master stacks them.
LAYERS = [
    ("Skin", [0]),
    ("Udeng", [1, 2, 8, 9]),
    ("Knot", [10, 11]),
    ("Fold", [12]),
    ("Flower", [3, 4, 5, 6, 7, 13, 14, 15, 18, 19]),
    ("EarR", [16]),
    ("Side", [17]),
]
SKIN_TOP = 330           # under the udeng band at every pose
FOLD_EDGE = (296.0, 0.0)  # SVG x where the long fold meets the udeng's left edge
FOLD_LEN = 719.0 - 296.0  # its length across, to the knot
PIVOT = {"Fold": (FOLD_EDGE[0] - tm.HEAD_POS[0], 0.0)}  # group origins (HeadLook units), else 0,0
# Face edges (SVG units, measured on the master outline) and the heights where the skin
# bulges past them under the ears and flower; those bulges are cut back to the edge.
SKIN_LEFT, LEFT_BAND = 300.0, (330.0, 745.0)     # under the udeng end, sideburn and his right ear
SKIN_RIGHT, RIGHT_BAND = 1040.0, (330.0, 750.0)  # under the udeng end, the flower and his left ear


def skin_commands():
    """The skin outline, smoothed through 96 points, top flattened and ear bulges trimmed."""
    pts = tm.resample(tm.polyline(tm.svg_paths("assets/vector/wayan_master.svg")[0][1]), 96)
    out = []
    for x, y in pts:
        y = max(y, SKIN_TOP)
        if LEFT_BAND[0] <= y <= LEFT_BAND[1]:
            x = max(x, SKIN_LEFT)
        if RIGHT_BAND[0] <= y <= RIGHT_BAND[1]:
            x = min(x, SKIN_RIGHT)
        out.append((x, y))
    return tm.commands(out)


def raw_commands(d):
    """Original master path data as Rive commands in HeadLook units (no resampling)."""
    import re
    tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pt = lambda x, y: (round(float(x) - tm.HEAD_POS[0], 2), round(float(y) - tm.HEAD_POS[1], 2))
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t in "Zz":
            out.append({"commandType": "close"})
            continue
        n = {"M": 2, "L": 2, "C": 6}[t]
        while i < len(tokens) and tokens[i] not in "MLCZz":
            a = tokens[i:i + n]
            i += n
            if t == "C":
                (c1x, c1y), (c2x, c2y), (ex, ey) = pt(*a[0:2]), pt(*a[2:4]), pt(*a[4:6])
                out.append({"commandType": "cubicTo", "control1X": c1x, "control1Y": c1y,
                            "control2X": c2x, "control2Y": c2y, "endX": ex, "endY": ey})
            else:
                x, y = pt(*a)
                out.append({"commandType": "moveTo" if t == "M" else "lineTo", "x": x, "y": y})
                t = "L" if t == "M" else t
    return out


def build(call):
    master = tm.svg_paths("assets/vector/wayan_master.svg")
    shapes = []
    for layer, idx in LAYERS:
        for k, i in enumerate(idx):
            fill, d = master[i]
            cmds = skin_commands() if layer == "Skin" else raw_commands(d)
            shapes.append({"name": f"H25_{layer}_{k}", "parentId": HEADLOOK, "x": 0, "y": 0,
                           "paints": [{"paintType": "fill", "color": tm.colour(fill)}],
                           "paths": [{"name": "Path", "commands": cmds}]})
    r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": shapes}}})
    if r.get("errors"):
        sys.exit(str(r)[:400])
    found = {o["name"]: o["id"] for o in call("find_objects", {"name": "H25_", "parentId": HEADLOOK})["objects"]
             if o["type"] == "Shape"}
    fills = [o["id"] for o in call("query_objects", {"objectIds": list(found.values()), "depth": 1})["objects"]
             if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})
    # stack in order (first = bottom): send each shape to the front in turn
    order = [found[f"H25_{layer}_{k}"] for layer, idx in LAYERS for k in range(len(idx))]
    call("reorder_objects", {"operations": [{"objectId": i, "order": "sendToFront"} for i in order]})
    groups = {}
    for layer, idx in LAYERS:
        members = [found[f"H25_{layer}_{k}"] for k in range(len(idx))]
        g = call("group_editor", {"name": f"Head25_{layer}", "objectIds": members})["group"]["id"]
        # origin back to (0, 0), children compensated, so a bound offset is the whole move
        gv = call("query_property_values", {"propertyKeys": {g: [13, 14], **{c: [13, 14] for c in members}}})
        gv = gv.get("values", gv)
        gx, gy = gv[g]["13"], gv[g]["14"]
        ox, oy = PIVOT.get(layer, (0.0, 0.0))
        call("set_property_values", {"propertyValues": {
            g: {"13": ox, "14": oy},
            **{c: {"13": gv[c]["13"] + gx - ox, "14": gv[c]["14"] + gy - oy} for c in members}}})
        groups[layer] = g
    head = call("group_editor", {"name": "Head25", "objectIds": list(groups.values())})["group"]["id"]
    hv = call("query_property_values", {"propertyKeys": {head: [13, 14], **{g: [13, 14] for g in groups.values()}}})
    hv = hv.get("values", hv)
    call("set_property_values", {"propertyValues": {
        head: {"13": 0, "14": 0},
        **{g: {"13": hv[g]["13"] + hv[head]["13"], "14": hv[g]["14"] + hv[head]["14"]} for g in groups.values()}}})
    CACHE.write_text(json.dumps({"head": head, "groups": groups}))
    print(json.dumps({"head": head, "groups": groups}))


def main():
    call = m.connect("head25")
    if sys.argv[1] == "build":
        build(call)


if __name__ == "__main__":
    main()
