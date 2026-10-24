#!/usr/bin/env python3
"""Rig for the udeng-slip idle: the udeng tilts down over Wayan's right eye, he pushes it back.

    python3 scripts/udeng_rig.py build
    python3 scripts/udeng_rig.py bare     # redo only the bare hair and skin (after udeng_geom.py)

Builds on the 2.5D head (scripts/head_rig25d.py) in the Rive file "wayan":

- Head25_Udeng: the old udeng shapes (master 1, 2, 8) are replaced by the pieces of
  assets/vector/udeng_slip.svg (scripts/udeng_geom.py), which leave out the hair in front of
  them, wrapped in `UdengSlip` in front of that hair. Head25_Knot and Head25_Fold get
  `KnotSlip` and `FoldSlip`. All three slip groups have their origin at PIVOT, right of
  and below the band's end, so a negative rotation tilts the band down to the left while
  its right end tucks further under the flower. The flower stays where it is.
- Head25_Bare: the Recraft bare-head hair and forehead skin, in Head25 in front of the
  skin, moving with the udeng on head turns. At rest the head parts cover it completely.
- Head25_Flower, Fold, Knot and Udeng move from Head25 to the front of HeadLook, so the
  slipping band covers the brows and the eye.

Ids go to scripts/.udeng.json. Needs the Rive editor open on "wayan".
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402
import svg_tools as tools  # noqa: E402

HEADLOOK = "0-2127"
H25 = json.loads(Path(__file__).with_name(".head25.json").read_text())
G = H25["groups"]
CACHE = Path(__file__).with_name(".udeng.json")
OLD_UDENG = ["0-14062", "0-14100", "0-14127"]  # H25_Udeng_0..2 = master 1, 2, 8 (H25_Udeng_3 is the hair)
KNOT, FOLD = ["0-14178", "0-14157"], ["0-14196"]
PIVOT = (1250.0 - tools.HEAD_POS[0], 620.0 - tools.HEAD_POS[1])  # HeadLook units
HEAD_X, HEAD_Y = "0-2259", "0-2261"                      # FaceVM headX / headY
UDENG_X, UDENG_Y = "0-14415", "0-14475"                  # converters turn4_udeng_x / _y


def commands(d):
    pts = [tuple(map(float, p.split())) for p in re.findall(r"(-?[\d.]+ -?[\d.]+)", d)]
    loc = [(round(x - tools.HEAD_POS[0], 2), round(y - tools.HEAD_POS[1], 2)) for x, y in pts]
    return ([{"commandType": "moveTo", "x": loc[0][0], "y": loc[0][1]}]
            + [{"commandType": "lineTo", "x": x, "y": y} for x, y in loc[1:]] + [{"commandType": "close"}])


def values(call, ids, keys=(13, 14)):
    v = call("query_property_values", {"propertyKeys": {i: list(keys) for i in ids}})
    return v.get("values", v)


def wrap(call, name, members, origin):
    """Group members, then put the group's origin at `origin` (parent units) without moving anything."""
    g = call("group_editor", {"name": name, "objectIds": members})["group"]["id"]
    v = values(call, [g, *members])
    gx, gy = v[g]["13"], v[g]["14"]
    call("set_property_values", {"propertyValues": {
        g: {"13": origin[0], "14": origin[1]},
        **{c: {"13": v[c]["13"] + gx - origin[0], "14": v[c]["14"] + gy - origin[1]} for c in members}}})
    return g


def build(call):
    pieces = tools.svg_paths("assets/vector/udeng_slip.svg")
    names = ["UdengSlip_0", "UdengSlip_1", "UdengSlip_2", "H25_BareHair", "H25_BareSkin"]
    parents = [G["Udeng"]] * 3 + [H25["head"]] * 2
    shapes = [{"name": n, "parentId": p, "x": 0, "y": 0,
               "paints": [{"paintType": "fill", "color": tools.colour(f)}],
               "paths": [{"name": "Path", "commands": commands(d)}]}
              for n, p, (f, d) in zip(names, parents, pieces)]
    # skin first, so the hair lands in front of it; the udeng pieces bottom to top
    order = [4, 3, 0, 1, 2]
    for i in order:
        r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": [shapes[i]]}}})
        if r.get("errors"):
            sys.exit(str(r)[:400])
    found = {}
    for parent in (G["Udeng"], H25["head"]):
        for o in call("find_objects", {"name": "", "parentId": parent})["objects"]:
            if o["type"] == "Shape" and o["name"] in names:
                found[o["name"]] = o["id"]
    missing = set(names) - set(found)
    if missing:
        sys.exit(f"shapes not found: {missing}")
    fills = [o["id"] for o in call("query_objects", {"objectIds": list(found.values()), "depth": 1})["objects"]
             if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})  # nonZero
    call("delete_objects", {"objectIds": OLD_UDENG})

    ids = {"shapes": found}
    ids["UdengSlip"] = wrap(call, "UdengSlip", [found[f"UdengSlip_{k}"] for k in range(3)], PIVOT)
    ids["KnotSlip"] = wrap(call, "KnotSlip", KNOT, PIVOT)
    fold_origin = values(call, [G["Fold"]])[G["Fold"]]
    ids["FoldSlip"] = wrap(call, "FoldSlip", FOLD, (PIVOT[0] - fold_origin["13"], PIVOT[1] - fold_origin["14"]))
    ids["Bare"] = wrap(call, "Head25_Bare", [found["H25_BareHair"], found["H25_BareSkin"]], (0.0, 0.0))

    # the udeng, its knot and folds and the flower go in front of the eyes and brows
    call("reparent_objects", {"operations": [
        {"objectId": G[k], "newParentId": HEADLOOK, "position": "start"} for k in ("Udeng", "Knot", "Fold", "Flower")]})
    # the bare head sits just in front of the skin
    call("reorder_objects", {"operations": [{"objectId": ids["Bare"], "order": "sendToBack"},
                                            {"objectId": ids["Bare"], "order": "bringForward"}]})
    r = call("viewmodel_editor", {"command": "databind", "data": {"databind": {"viewModelId": "0-14", "bindings": [
        {"objectId": ids["Bare"], "propertyKey": 13, "viewModelPropertyId": HEAD_X, "converterId": UDENG_X},
        {"objectId": ids["Bare"], "propertyKey": 14, "viewModelPropertyId": HEAD_Y, "converterId": UDENG_Y}]}}})
    print("binds:", r.get("errors") or "ok")
    CACHE.write_text(json.dumps(ids, indent=1))
    print(json.dumps(ids, indent=1))


def bare(call):
    """Replace the bare hair and skin shapes in Head25_Bare with the current udeng_slip.svg."""
    ids = json.loads(CACHE.read_text())
    pieces = tools.svg_paths("assets/vector/udeng_slip.svg")
    call("delete_objects", {"objectIds": [ids["shapes"]["H25_BareHair"], ids["shapes"]["H25_BareSkin"]]})
    for name, k in (("H25_BareSkin", 4), ("H25_BareHair", 3)):  # the hair lands in front
        f, d = pieces[k]
        r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": [{
            "name": name, "parentId": ids["Bare"], "x": 0, "y": 0,
            "paints": [{"paintType": "fill", "color": tools.colour(f)}],
            "paths": [{"name": "Path", "commands": commands(d)}]}]}}})
        if r.get("errors"):
            sys.exit(str(r)[:400])
    for o in call("find_objects", {"name": "H25_Bare", "parentId": ids["Bare"]})["objects"]:
        if o["type"] == "Shape":
            ids["shapes"][o["name"]] = o["id"]
    fills = [o["id"] for o in call("query_objects", {"objectIds": [ids["shapes"]["H25_BareHair"], ids["shapes"]["H25_BareSkin"]],
                                                     "depth": 1})["objects"] if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})
    CACHE.write_text(json.dumps(ids, indent=1))
    print(json.dumps(ids["shapes"]))


def main():
    call = m.connect("udeng-rig")
    cmd = sys.argv[1:] and sys.argv[1]
    if cmd == "build":
        build(call)
    elif cmd == "bare":
        bare(call)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
