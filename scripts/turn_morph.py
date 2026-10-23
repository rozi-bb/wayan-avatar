#!/usr/bin/env python3
"""Morphable head for a smooth turn: the front head reshaped point by point into a 3/4 drawing.

Every head part from the master SVG (skin, udeng pieces, hair, ears, nose) is
rebuilt as a smooth closed path with a fixed number of points; its partner in
the 3/4 drawing is resampled to the same number of points, matched by the
cyclic shift that fits best. Keying both point sets lets Rive slide each point
from one shape to the other, so the head turns without a cut. The flower is
rigid: it slides, narrows and tucks behind the head as one piece.

    python3 scripts/turn_morph.py build right     # create HeadMorph in HeadLook (front pose)
    python3 scripts/turn_morph.py preview right OUT 0,0.25,0.5,0.75,1
                                                  # set in-between poses, capture, restore
Needs the Rive editor open on "wayan".
"""

import base64
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HEADLOOK = "0-2127"
HEAD_POS = (690.0, 990.0)
CACHE = Path(__file__).with_name(".turn_morph.json")
PALETTE = {
    "#ffefab81": (239, 171, 129), "#ffd69067": (214, 144, 103), "#ffededec": (237, 237, 236),
    "#ffd3d2d2": (211, 210, 210), "#fff5bf03": (245, 191, 3), "#ffe9a601": (233, 166, 1),
    "#ffc87915": (200, 121, 21), "#ff3f3e3f": (63, 62, 63),
}

# (name, master path index, 3/4 path index per side, points). None on one side means the
# part is not in that drawing: it shrinks to (or grows from) a point hidden behind the head.
# Listed bottom to top, the master's stacking order.
PARTS = [
    ("skin", 0, {"right": 0}, 72),
    ("udeng", 1, {"right": 1}, 56),
    ("hair_front", 9, {"right": "EDGE_R"}, 40),     # the front's hair slides away behind the crown
    ("hair_turn", "EDGE_L", {"right": 4}, 40),      # the 3/4 hair comes out from the far edge
    ("hair_back", None, {"right": 11}, 16),
    ("knot_front", "DETAIL", None, None),          # knot and folds: rigid, swapped half way
    ("knot_turn", "DETAIL", None, None),
    ("flower_back", "FLOWER_BACK", None, None),
    ("ear_r", 14, {"right": None}, 24),
    ("flower_front", "FLOWER_FRONT", None, None),
    ("ear_l", 16, {"right": 20}, 24),
    ("sideburn", 17, {"right": 8}, 32),
    ("nose", 25, {"right": 19}, 20),
]
# The skin's top is always under the udeng band; flattening it there keeps it hidden in between.
SKIN_TOP = 330
# A hair patch that is in only one drawing hides as a zero-width sliver on this x (SVG units).
EDGE = {"EDGE_R": 1060.0, "EDGE_L": 300.0}
# Knot and folds: master paths and 3/4 paths, each set moved as one piece.
DETAIL = {"knot_front": [10, 11, 12], "knot_turn": {"right": [5, 7, 3]}}
FLOWER_BACK = [3, 4, 5, 6, 7, 13]      # petals that sit behind the right ear
FLOWER_FRONT = [15, 18, 19]
# Where a missing part hides (SVG units): just inside the skin edge on that side.
HIDE = {"ear_r": {"right": (1040, 660)}, "hair_back": {"right": (1030, 520)}}
# The flower in the 3/4 drawing: a sliver past the right edge (bbox of its yellow bits).
FLOWER_TO = {"right": (1047, 415, 1149, 629)}


def svg_paths(file):
    out = []
    for attrs in re.findall(r"<path([^>]*)>", (ROOT / file).read_text()):
        fill = tuple(map(int, re.search(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"', attrs).groups()))
        out.append((fill, re.search(r'd="([^"]+)"', attrs).group(1)))
    return out


def polyline(d, step=2.0):
    """Dense points along an absolute M/L/C/Z path."""
    tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pts, i, cur = [], 0, None
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t in "Zz":
            continue
        n = {"M": 2, "L": 2, "C": 6}[t]
        while i < len(tokens) and tokens[i] not in "MLCZz":
            a = list(map(float, tokens[i:i + n]))
            i += n
            if t == "M":
                cur = (a[0], a[1])
                pts.append(cur)
                t = "L"
            elif t == "L":
                seg = math.dist(cur, (a[0], a[1]))
                k = max(1, int(seg / step))
                pts += [(cur[0] + (a[0] - cur[0]) * j / k, cur[1] + (a[1] - cur[1]) * j / k) for j in range(1, k + 1)]
                cur = (a[0], a[1])
            else:
                p0, p1, p2, p3 = cur, (a[0], a[1]), (a[2], a[3]), (a[4], a[5])
                approx = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
                k = max(2, int(approx / step))
                for j in range(1, k + 1):
                    s = j / k
                    u = 1 - s
                    pts.append((u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0],
                                u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1]))
                cur = p3
    return pts


def area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


def resample(pts, n):
    """n points evenly spaced along the closed outline, clockwise on screen, from the topmost point."""
    if area(pts) < 0:
        pts = pts[::-1]
    top = min(range(len(pts)), key=lambda i: (pts[i][1], pts[i][0]))
    pts = pts[top:] + pts[:top]
    ring = pts + pts[:1]
    seg = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    total = sum(seg)
    out, acc, j = [], 0.0, 0
    for k in range(n):
        target = total * k / n
        while acc + seg[j] < target:
            acc += seg[j]
            j += 1
        f = (target - acc) / seg[j] if seg[j] else 0
        out.append((ring[j][0] + (ring[j + 1][0] - ring[j][0]) * f, ring[j][1] + (ring[j + 1][1] - ring[j][1]) * f))
    return out


def best_shift(a, b):
    """Rotate b's point order to line up with a (after matching centres)."""
    ca = (sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a))
    cb = (sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b))
    n = len(a)
    def cost(s):
        return sum((a[i][0] - ca[0] - b[(i + s) % n][0] + cb[0]) ** 2 + (a[i][1] - ca[1] - b[(i + s) % n][1] + cb[1]) ** 2
                   for i in range(n))
    s = min(range(n), key=cost)
    return b[s:] + b[:s]


def commands(pts):
    """Closed Catmull-Rom curve through pts as Rive commands, in HeadLook units."""
    n = len(pts)
    loc = [(x - HEAD_POS[0], y - HEAD_POS[1]) for x, y in pts]
    tan = [((loc[(i + 1) % n][0] - loc[i - 1][0]) / 6, (loc[(i + 1) % n][1] - loc[i - 1][1]) / 6) for i in range(n)]
    cmds = [{"commandType": "moveTo", "x": round(loc[0][0], 2), "y": round(loc[0][1], 2)}]
    for i in range(n):
        j = (i + 1) % n
        cmds.append({"commandType": "cubicTo",
                     "control1X": round(loc[i][0] + tan[i][0], 2), "control1Y": round(loc[i][1] + tan[i][1], 2),
                     "control2X": round(loc[j][0] - tan[j][0], 2), "control2Y": round(loc[j][1] - tan[j][1], 2),
                     "endX": round(loc[j][0], 2), "endY": round(loc[j][1], 2)})
    cmds.append({"commandType": "close"})
    return cmds


def colour(fill):
    return min(PALETTE, key=lambda c: sum((PALETTE[c][k] - fill[k]) ** 2 for k in range(3)))


def shrink(pts, at, size=3.0):
    """The same outline squeezed to a dot at `at` (for a part missing from one drawing)."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    span = max(max(abs(p[0] - cx), abs(p[1] - cy)) for p in pts) or 1
    return [(at[0] + (p[0] - cx) / span * size, at[1] + (p[1] - cy) / span * size) for p in pts]


def sliver(pts, x):
    """The same outline squeezed to zero width on the line x (kept at its own height)."""
    return [(x, py) for _, py in pts]


def plan(side):
    """{part: (colour, front points, side points)} for every morphing part."""
    master, turned = svg_paths("assets/vector/wayan_master.svg"), svg_paths(f"assets/vector/head34_{side}.svg")
    out = {}
    for name, mi, targets, n in PARTS:
        if mi in ("DETAIL", "FLOWER_BACK", "FLOWER_FRONT"):
            continue
        ti = targets[side]
        if mi in EDGE:                       # only in the 3/4 drawing: comes out of an edge
            b = resample(polyline(turned[ti][1]), n)
            a = sliver(b, EDGE[mi])
            fill = turned[ti][0]
        elif ti in EDGE:                     # only in the front: slides into an edge
            a = resample(polyline(master[mi][1]), n)
            b = sliver(a, EDGE[ti])
            fill = master[mi][0]
        elif mi is None:                     # only in the 3/4 drawing: grows from a hidden dot
            b = resample(polyline(turned[ti][1]), n)
            a = shrink(b, HIDE[name][side])
            fill = turned[ti][0]
        elif ti is None:                     # only in the front: shrinks to a hidden dot
            a = resample(polyline(master[mi][1]), n)
            b = shrink(a, HIDE[name][side])
            fill = master[mi][0]
        else:
            a = resample(polyline(master[mi][1]), n)
            b = best_shift(a, resample(polyline(turned[ti][1]), n))
            fill = master[mi][0]
        if name == "skin":
            a = [(x, max(y, SKIN_TOP)) for x, y in a]
            b = [(x, max(y, SKIN_TOP)) for x, y in b]
        out[name] = (colour(fill), a, b)
    return out


def detail_paths(side):
    """Knot and folds: (front paths, 3/4 paths) and the shift from one set's centre to the other's."""
    master, turned = svg_paths("assets/vector/wayan_master.svg"), svg_paths(f"assets/vector/head34_{side}.svg")
    front = [master[i] for i in DETAIL["knot_front"]]
    back = [turned[i] for i in DETAIL["knot_turn"][side]]
    def centre(paths):
        pts = [p for _, d in paths for p in polyline(d, 8)]
        return ((min(p[0] for p in pts) + max(p[0] for p in pts)) / 2, (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2)
    cf, ct = centre(front), centre(back)
    return front, back, (ct[0] - cf[0], ct[1] - cf[1])


def flower_paths():
    master = svg_paths("assets/vector/wayan_master.svg")
    return {"flower_back": [master[i] for i in FLOWER_BACK], "flower_front": [master[i] for i in FLOWER_FRONT]}


def flower_bbox():
    pts = [p for group in flower_paths().values() for _, d in group for p in polyline(d, 8)]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def flower_pose(side):
    """Group transform (x, y, scaleX, scaleY) taking the front flower onto the 3/4 sliver,
    with the group's origin at the front flower's centre."""
    x0, y0, x1, y1 = flower_bbox()
    tx0, ty0, tx1, ty1 = FLOWER_TO[side]
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    t = ((tx0 + tx1) / 2, (ty0 + ty1) / 2)
    return c, (t[0] - c[0], t[1] - c[1], (tx1 - tx0) / (x1 - x0), (ty1 - ty0) / (y1 - y0))


def build(call, side):
    p = plan(side)
    centre, _ = flower_pose(side)
    shapes = []
    for name, mi, _, _ in PARTS:
        if name not in p:
            continue
        col, a, _ = p[name]
        shapes.append({"name": f"Morph_{name}", "parentId": HEADLOOK, "x": 0, "y": 0,
                       "paints": [{"paintType": "fill", "color": col}],
                       "paths": [{"name": "Path", "commands": commands(a)}]})
    r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": shapes}}})
    if r.get("errors"):
        sys.exit(str(r)[:400])
    # flower pieces keep their own drawing (rigid), in two groups around the right ear
    fl = []
    for gname, group in flower_paths().items():
        for k, (fill, d) in enumerate(group):
            pts = polyline(d, 1.5)
            fl.append({"name": f"Morph_{gname}_{k}", "parentId": HEADLOOK, "x": 0, "y": 0,
                       "paints": [{"paintType": "fill", "color": colour(fill)}],
                       "paths": [{"name": "Path", "commands": commands(resample(pts, 48))}]})
    call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": fl}}})

    found = {o["name"]: o["id"] for o in call("find_objects", {"name": "Morph_", "parentId": HEADLOOK})["objects"]
             if o["type"] == "Shape"}
    kids = call("query_objects", {"objectIds": list(found.values()), "depth": 1})["objects"]
    fills = [o["id"] for o in kids if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})
    ids = {}
    for gname in ("flower_back", "flower_front"):
        members = [i for n, i in found.items() if n.startswith(f"Morph_{gname}_")]
        g = call("group_editor", {"name": f"Morph_{gname}", "objectIds": members})["group"]["id"]
        ids[gname] = g
    # Flower groups: origin on the flower's centre, children compensated, so a scale pivots there.
    vals = call("query_property_values", {"propertyKeys": {g: [13, 14] for g in ids.values()}})
    vals = vals.get("values", vals)
    for gname, g in ids.items():
        gx, gy = vals[g]["13"], vals[g]["14"]
        cx, cy = centre[0] - HEAD_POS[0], centre[1] - HEAD_POS[1]
        members = [i for n, i in found.items() if n.startswith(f"Morph_{gname}_")]
        mv = call("query_property_values", {"propertyKeys": {i: [13, 14] for i in members}})
        mv = mv.get("values", mv)
        call("set_property_values", {"propertyValues": {
            **{g: {"13": cx, "14": cy}},
            **{i: {"13": mv[i]["13"] + gx - cx, "14": mv[i]["14"] + gy - cy} for i in members}}})
    # stack in PARTS order: first = bottom, so send each to the front in turn
    order = []
    for name, mi, _, _ in PARTS:
        order.append(ids[name] if name in ids else found[f"Morph_{name}"])
    call("reorder_objects", {"operations": [{"objectId": i, "order": "sendToFront"} for i in order]})
    group = call("group_editor", {"name": "HeadMorph", "objectIds": order})["group"]["id"]
    CACHE.write_text(json.dumps({"group": group, "shapes": {n: found[f"Morph_{n}"] for n in p},
                                 "flowers": ids}))
    print("HeadMorph", group, len(p), "morph parts +", len(fl), "flower pieces")


def vertex_props(call, shape_id):
    """[(vertex id, {key: value})] for a shape's single path, in path order."""
    path = [o for o in call("query_objects", {"objectIds": [shape_id], "depth": 2})["objects"]
            if "PointsPath" in o["types"]][0]
    vids = path["children"]
    v = call("query_property_values", {"propertyKeys": {i: [24, 25, 84, 85, 86, 87] for i in vids}})
    v = v.get("values", v)
    return [(i, v[i]) for i in vids]


def side_props(call, side):
    """Per part: front vertex props (read from the shape) and the 3/4 props (from a temporary
    shape built the same way, then deleted), angles unwrapped to the nearest turn."""
    cache = json.loads(CACHE.read_text())
    p = plan(side)
    tmp = [{"name": f"Tmp_{n}", "parentId": HEADLOOK, "x": 0, "y": 0,
            "paints": [{"paintType": "fill", "color": "#ff000000"}],
            "paths": [{"name": "Path", "commands": commands(p[n][2])}]} for n in p]
    call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": tmp}}})
    found = {o["name"]: o["id"] for o in call("find_objects", {"name": "Tmp_", "parentId": HEADLOOK})["objects"]
             if o["type"] == "Shape"}
    out = {}
    try:
        for n in p:
            front = vertex_props(call, cache["shapes"][n])
            turned = vertex_props(call, found[f"Tmp_{n}"])
            assert len(front) == len(turned), (n, len(front), len(turned))
            pairs = []
            for (vid, a), (_, b) in zip(front, turned):
                b = dict(b)
                for k in ("84", "86"):
                    if k in a and k in b:
                        while b[k] - a[k] > 180:
                            b[k] -= 360
                        while b[k] - a[k] < -180:
                            b[k] += 360
                pairs.append((vid, a, b))
            out[n] = pairs
    finally:
        call("delete_objects", {"objectIds": list(found.values())})
    return out


def preview(call, side, outdir, ts):
    cache = json.loads(CACHE.read_text())
    props = side_props(call, side)
    _, (fdx, fdy, fsx, fsy) = flower_pose(side)
    fl = cache["flowers"]
    fl_rest = call("query_property_values", {"propertyKeys": {g: [13, 14, 16, 17] for g in fl.values()}})
    fl_rest = fl_rest.get("values", fl_rest)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    def pose(t):
        pv = {}
        for pairs in props.values():
            for vid, a, b in pairs:
                pv[vid] = {k: a[k] + (b[k] - a[k]) * t for k in a if k in b}
        for g in fl.values():
            r = fl_rest[g]
            pv[g] = {"13": r["13"] + fdx * t, "14": r["14"] + fdy * t,
                     "16": 100 + (fsx * 100 - 100) * t, "17": 100 + (fsy * 100 - 100) * t}
        items = list(pv.items())
        for i in range(0, len(items), 150):
            call("set_property_values", {"propertyValues": dict(items[i:i + 150])})

    try:
        for t in ts:
            pose(t)
            res = call("capture_artboard", {"longEdge": 1536, "backgroundColor": "#ff6ba8d2"}, raw=True)
            img = next(c for c in res["content"] if c.get("type") == "image")
            name = out / f"t{t:.2f}.png"
            name.write_bytes(base64.b64decode(img["data"]))
            subprocess.run(["sips", "-c", "690", "640", "--cropOffset", "130", "220", str(name)],
                           check=True, capture_output=True)
            print(name.name, flush=True)
    finally:
        pose(0.0)
        print("front pose restored")


def main():
    call = m.connect("turn-morph")
    cmd, side = sys.argv[1], sys.argv[2]
    if cmd == "build":
        build(call, side)
    elif cmd == "preview":
        preview(call, side, sys.argv[3], [float(t) for t in sys.argv[4].split(",")])


if __name__ == "__main__":
    main()
