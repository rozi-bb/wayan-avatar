#!/usr/bin/env python3
"""Skin every head shape to three turn bones with a depth field, for a 3D head turn.

The head is treated as a ball: a point's depth z (1 at the front of the face,
0 on the silhouette) decides how far it follows TurnFront, which the page moves
with headX/headY. Points outside the ball (ears, the skin under them, udeng
corners) follow TurnBack the other way a little, like the far side of a ball.
Every shape gets weights from the same field, so udeng, flower, ears, hair and
the face skin under them move together and nothing opens up.

    python3 scripts/turn_skin.py geometry   # print the shapes and vertex counts
    python3 scripts/turn_skin.py bind       # bind each path to the three bones
    python3 scripts/turn_skin.py weights    # write the field as skin weights
    python3 scripts/turn_skin.py pose H V   # move the bones in the editor (preview), 0 0 = rest

Needs the Rive editor open on "wayan".
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

HEADLOOK = "0-2127"
UDENG = "0-5775"
BONES = {"rest": "0-11472", "front": "0-11473", "back": "0-11474"}  # tendon order 1, 2, 3
SHAPES = {
    "Face": "0-641", "Hair_Cap": "0-8141", "Hair_Side_R": "0-366", "Ear_R": "0-376", "Ear_L": "0-393",
    "Flower_Petal_1": "0-344", "Flower_Petal_2": "0-355", "Flower_Petal_3": "0-385", "Flower_Petal_4": "0-404",
    "Flower_Petal_5": "0-518", "Flower_Petal_6": "0-529", "Flower_Petal_7": "0-540", "Flower_Center": "0-550",
    "Flower_Petal_8": "0-561",
    "Udeng_Line_1": "0-421", "Udeng_Line_2": "0-449", "Udeng_Knot": "0-467", "Hair_Top": "0-488",
    "Udeng_Band": "0-506", "Udeng_Side": "0-577", "Udeng_Base": "0-603",
}

# The ball, in HeadLook units (SVG units, y down; the neck is at 0,0).
CX, CY, RX, RY, RY_CHIN = 8.0, -430.0, 400.0, 470.0, 440.0
BACK = 0.15  # TurnBack moves BACK x as far as TurnFront, the other way
FRONT_X, FRONT_Y = 78.0, 36.0  # TurnFront travel at headX/headY = 1


def depth(x, y):
    """+1 front of the face, 0 on the silhouette, down to -BACK outside it."""
    # the lower half is flatter, so the chin (y 14) sits on the silhouette and stays on the neck
    s = math.hypot((x - CX) / RX, (y - CY) / (RY if y < CY else RY_CHIN))
    # 1 - s^3 rather than a true sphere: flat across the face (eyes, nose, mouth move
    # alike) and finite at the silhouette, where a sphere's infinite slope slid
    # neighbouring edges (udeng crown over hair) apart
    d = 1 - s ** 3 if s < 1 else -min(BACK, (s - 1) * 3.0)
    # the jaw sits on the neck: fade to 0 from y -110 down to -30 so the face/neck join never opens
    t = max(0.0, min(1.0, (-30.0 - y) / 80.0))
    return d * t * t * (3 - 2 * t)


# Rigid pieces stuck on the head: the flower is tucked behind Ear_L, so they move as
# one block (otherwise the petal behind the ear slides out); Ear_R on its own.
# Skin and udeng under a block follow it, fading back to the field over FADE units
# once past MARGIN.
BLOCKS = {
    "flower_ear_L": (["Flower_Petal_1", "Flower_Petal_2", "Flower_Petal_3", "Flower_Petal_4", "Flower_Petal_5",
                      "Flower_Petal_6", "Flower_Petal_7", "Flower_Center", "Flower_Petal_8", "Ear_L"], 0.40),
    "ear_R": (["Ear_R"], 0.0),
}
FADE = 150.0
MARGIN = 45.0  # skin this close to a block moves fully with it (the ear's backing)


def hull(points):
    pts = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(reversed(pts))
    return lo[:-1] + hi[:-1]


def outside_distance(poly, x, y):
    """0 inside the convex polygon, else the distance to its edge."""
    inside, best = True, float("inf")
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (bx - ax) * (y - ay) - (by - ay) * (x - ax) < 0:
            inside = False
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return 0.0 if inside else best


def field(g):
    """{vertex_id: d} for every vertex: the depth field, blocks held rigid."""
    hulls = {b: (hull([(x, y) for n in names for _, vs in g[n] for _, _, x, y, *_ in vs]), d)
             for b, (names, d) in BLOCKS.items()}
    owner = {n: b for b, (names, _) in BLOCKS.items() for n in names}
    def at(x, y):
        d = depth(x, y)
        for poly, bd in hulls.values():
            w = max(0.0, 1 - max(0.0, outside_distance(poly, x, y) - MARGIN) / FADE)
            w = w * w * (3 - 2 * w)
            d = d * (1 - w) + bd * w
        return d

    out = {}  # vertex id -> (vertex, in handle, out handle); handles get the field at their own spot
    for name, paths in g.items():
        for _, vs in paths:
            for vid, _, x, y, *hs in vs:
                if name in owner:
                    out[vid] = (hulls[owner[name]][1],) * 3
                    continue
                dv = at(x, y)
                out[vid] = (dv, at(hs[0], hs[1]), at(hs[2], hs[3])) if hs else (dv, dv, dv)
    return out


def pack(d):
    """Packed (values, indices) for bones rest=1, front=2, back=3."""
    if d >= 0:
        f = round(min(d, 1.0) * 255)
        return (255 - f) | (f << 8), 1 | (2 << 8)
    b = round(min(-d / BACK, 1.0) * 255)
    return (255 - b) | (b << 8), 1 | (3 << 8)


def geometry(call):
    """{shape: [(path_id, [(vertex_id, type, x, y)])]} in HeadLook coordinates."""
    out = {}
    tree = call("query_objects", {"objectIds": list(SHAPES.values()), "depth": 2})["objects"]
    by_id = {o["id"]: o for o in tree}
    vals = call("query_property_values", {"propertyKeys": {i: [13, 14] for i in list(SHAPES.values()) + [UDENG]}})
    vals = vals.get("values", vals)
    for name, sid in SHAPES.items():
        ox, oy = vals[sid]["13"], vals[sid]["14"]
        if name.startswith(("Udeng", "Hair_Top")):
            ox += vals[UDENG]["13"]
            oy += vals[UDENG]["14"]
        paths = [c for c in by_id[sid].get("children", []) if "PointsPath" in by_id.get(c, {}).get("types", [])]
        out[name] = []
        for pid in paths:
            pv = call("query_property_values", {"propertyKeys": {pid: [13, 14]}})
            pv = pv.get("values", pv)[pid]
            verts = call("query_objects", {"objectIds": [pid], "depth": 1})["objects"]
            vids = [v for v in verts if v["id"] != pid and "Vertex" in v["types"][0]]
            xy = call("query_property_values", {"propertyKeys": {v["id"]: [24, 25, 84, 85, 86, 87] for v in vids}})
            xy = xy.get("values", xy)
            rows = []
            for v in vids:
                q = xy[v["id"]]
                x, y = ox + pv["13"] + q["24"], oy + pv["14"] + q["25"]
                row = [v["id"], v["types"][0], x, y]
                if "84" in q:  # cubic: in and out handle positions (rotation in degrees)
                    for rk, dk in (("84", "85"), ("86", "87")):
                        a = math.radians(q[rk])
                        row += [x + math.cos(a) * q[dk], y + math.sin(a) * q[dk]]
                rows.append(row)
            out[name].append((pid, rows))
    return out


def main():
    cmd = sys.argv[1]
    call = m.connect("turn-skin")
    cache = Path(__file__).with_name(".turn_geometry.json")
    if cmd == "geometry":
        g = geometry(call)
        cache.write_text(json.dumps(g))
        for name, paths in g.items():
            for pid, vs in paths:
                d = [depth(x, y) for _, _, x, y, *_ in vs]
                print(f"{name:15s} {pid:8s} {len(vs):4d} verts  depth {min(d):+.2f}..{max(d):+.2f}  types {sorted({t for _, t, *_ in vs})}")
        return
    g = json.loads(cache.read_text())
    if cmd == "bind":
        for name, paths in g.items():
            for pid, _ in paths:
                r = call("mesh_rigging_tool", {"command": "bindBones", "data": {"bindBones": {
                    "targetId": pid, "boneIds": [BONES["rest"], BONES["front"], BONES["back"]]}}})
                print(name, pid, r.get("errors") or "bound")
    elif cmd == "weights":
        d = field(g)
        vids = list(d)
        kids = {}
        for i in range(0, len(vids), 150):
            for o in call("query_objects", {"objectIds": vids[i:i + 150], "depth": 1})["objects"]:
                if o["id"] in d and o.get("children"):
                    kids[o["id"]] = o["children"][0]
        missing = [v for v in vids if v not in kids]
        if missing:
            sys.exit(f"{len(missing)} vertices have no weight child (not bound?): {missing[:5]}")
        pv = {}
        for vid, (dv, di, do) in d.items():
            (val, idx), (iv, ii), (ov, oi) = pack(dv), pack(di), pack(do)
            pv[kids[vid]] = {"102": val, "103": idx, "110": iv, "111": ii, "112": ov, "113": oi}
        items = list(pv.items())
        errs = 0
        for i in range(0, len(items), 120):
            r = call("set_property_values", {"propertyValues": dict(items[i:i + 120])})
            errs += len([e for e in r.get("errors", []) if "110" not in str(e) and "111" not in str(e)
                         and "112" not in str(e) and "113" not in str(e)])
        print(f"weights written for {len(pv)} vertices, {errs} real errors")
        for name, paths in g.items():
            ds = [d[vid][0] for _, vs in paths for vid, *_ in vs]
            print(f"  {name:15s} d {min(ds):+.2f}..{max(ds):+.2f}")
    elif cmd == "pose":
        h, v = float(sys.argv[2]), float(sys.argv[3])
        call("set_property_values", {"propertyValues": {
            BONES["front"]: {"90": FRONT_X * h, "91": -430 + FRONT_Y * v},
            BONES["back"]: {"90": -BACK * FRONT_X * h, "91": -430 - BACK * FRONT_Y * v}}})
        print("bones at", h, v)


if __name__ == "__main__":
    main()
