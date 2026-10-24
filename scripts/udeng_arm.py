#!/usr/bin/env python3
"""Wayan's right forearm in front of his head, for pushing the slipping udeng back up.

The head draws over the body, so an arm raised beside it would vanish behind the ear.
This builds a second forearm in front of the head that follows the real one:

    BodyFront     node in front of Head, on Body's pivot; Sway and Idle key it exactly like
                  Body (rotation, breathing scale), so it stays on the body while it moves
    ArmFront_R    node at the shoulder (where UpperArm_R starts), keyed with the same
                  rotation and lift as UpperArm_R
      ForeFront_R node at the elbow (UpperArm_R's length along it), keyed like Forearm_R
        Hand_R copy, ArmF_R copy   the round hand and forearm sleeve, duplicated; the copy's
                                   -y edge runs straight from the elbow (-75.5, where ArmF_R
                                   narrows to -48 to clear the sash and would notch a straight
                                   arm) out to the round hand's corner at the cuff (-97.6, which
                                   ArmF_R only reaches in a lip under the hand; the body's
                                   ArmB_R fills in the rest, and it sticks out once raised)
        Hand_R_Udeng               the Recraft hand (assets/vector/udeng_hand_raw.svg), wrist
                                   tucked behind the cuff, origin at the wrist

In Body, UpperRaise_R is a plain sleeve on UpperArm_R, a stadium whose edges line up with the
forearm sleeve's (it is slimmer on the -y side, like ArmF_R), so a straight arm has straight
edges, and whose round end at the elbow rounds a bent elbow; the udeng timeline hides ArmD_R,
the body's elbow disc, meanwhile, as it would bulge past those edges. Raised this high, the
skinned ArmU_R thins out at the shoulder; this keeps the upper arm its own width. It is hidden
too except in the udeng timeline.

ArmFront_R is hidden (opacity 0) except while the udeng timeline plays; at rest it lies
exactly on the real forearm, so showing it changes nothing until the arm reaches the head.

    python3 scripts/udeng_arm.py build
    python3 scripts/udeng_arm.py upper    # (re)make only the plain upper sleeve
    python3 scripts/udeng_arm.py front    # move ArmFront_R under a new BodyFront
    python3 scripts/udeng_arm.py straighten  # straighten the sleeve copy's -y edge

Ids go to scripts/.udeng.json. Needs the Rive editor open on "wayan".
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402
import svg_tools as tools  # noqa: E402

HEADLOOK, HEAD, BODY, WAYAN = "0-2127", "0-729", "0-730", "0-17"
BODY_KEYS = {"Sway": [15], "Idle": [17]}   # Body's own keys (rotation, scale y) that BodyFront copies
CUBIC_KEYS = [63, 64, 65, 66]
UPPER, FORE = "0-734", "0-735"             # UpperArm_R, Forearm_R
ROUND_HAND, SLEEVE = "0-135", "0-9854"     # Hand_R, ArmF_R
CACHE = Path(__file__).with_name(".udeng.json")
HAND_SVG = "assets/vector/udeng_hand_raw.svg"
HAND_PATHS = [1, 2, 3, 4, 5, 6]            # skin, thumb shade, wrist shade, finger lines (7, 8 are nail shine)
HAND_WRIST = (1023.0, 1560.0)              # wrist centre in the drawing; the fingers point up
HAND_CUT = 1800.0                          # the drawing's forearm below this is cut off (under the sleeve)
HAND_SCALE = 0.18                          # drawing units -> bone units
WRIST = (205.0, -6.0)                      # wrist in Forearm_R space, just inside the cuff
# The plain upper sleeve: half its width and how far its centre line sits toward +y, so its
# edges are at -76 and +88 like the forearm sleeve's (ArmF_R runs from about -75 to +88).
UPPER_HALF, UPPER_SHIFT = 82.0, 6.0
SLEEVE_EDGE = -75.5                        # the forearm sleeve's -y edge along its length
SLEEVE_TOP = 88.0                          # its +y edge at the elbow, where the plain upper sleeve ends
SKIN = {(241, 179, 117): "#ffefab81", (196, 142, 105): "#ffd69067"}


def values(call, ids, keys):
    v = call("query_property_values", {"propertyKeys": {i: list(keys) for i in ids}})
    return v.get("values", v)


def hand_commands(d):
    """A drawing path in Hand_R_Udeng space: wrist at 0, fingers along +x, the drawing's right on +y."""
    pts = tools.polyline(d, step=3.0)
    pts = [(x, min(y, HAND_CUT)) for x, y in pts]  # flatten everything below the cut onto it
    loc = [(round(-(y - HAND_WRIST[1]) * HAND_SCALE, 2), round((x - HAND_WRIST[0]) * HAND_SCALE, 2)) for x, y in pts]
    out = [{"commandType": "moveTo", "x": loc[0][0], "y": loc[0][1]}]
    out += [{"commandType": "lineTo", "x": x, "y": y} for x, y in loc[1:]]
    return out + [{"commandType": "close"}]


def empty_group(call, name, parent, x, y, rotation):
    g = call("group_editor", {"name": name, "parentId": parent})["group"]["id"]
    # an empty group lands at world (0, 0) with a scale that cancels its parents': reset it
    call("set_property_values", {"propertyValues": {g: {"13": x, "14": y, "15": rotation, "16": 100, "17": 100}}})
    return g


def build(call):
    ids = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    body = values(call, [BODY, HEAD], (13, 14))
    bone = values(call, [UPPER], (15, 89, 90, 91))[UPPER]
    fore = values(call, [FORE], (15,))[FORE]
    # shoulder in HeadLook units (Body and Head are siblings under the scaled Wayan node; HeadLook rests at 0)
    sx = body[BODY]["13"] + bone["90"] - body[HEAD]["13"]
    sy = body[BODY]["14"] + bone["91"] - body[HEAD]["14"]
    arm = empty_group(call, "ArmFront_R", HEADLOOK, sx, sy, bone["15"])
    call("reorder_objects", {"operations": [{"objectId": arm, "order": "sendToFront"}]})
    forearm = empty_group(call, "ForeFront_R", arm, bone["89"], 0.0, fore["15"])

    # copies of the sleeve and the round hand, moved over keeping their place on screen
    before = {o["id"] for o in call("query_objects", {"objectIds": [FORE], "depth": 1})["objects"]}
    call("duplicate_objects", {"objectIds": [ROUND_HAND, SLEEVE]})
    kids = call("query_objects", {"objectIds": [FORE], "depth": 1})["objects"]
    new = {o["name"]: o["id"] for o in kids if o["id"] not in before and o["id"] != FORE}
    copies = [new[n] for n in new if n.startswith("Hand_R")] + [new[n] for n in new if n.startswith("ArmF_R")]
    if len(copies) != 2:
        sys.exit(f"duplicate not found: {new}")
    call("reparent_objects", {"operations": [{"objectId": c, "newParentId": forearm, "position": "end"} for c in copies]})
    call("rename_objects", {"renames": [{"id": copies[0], "name": "HandFront_R"},
                                        {"id": copies[1], "name": "ArmFFront_R"}]})
    straighten(call, copies[1])

    # the Recraft hand, behind the sleeve
    paths = tools.svg_paths(HAND_SVG)
    hand = empty_group(call, "Hand_R_Udeng", forearm, WRIST[0], WRIST[1], 0.0)
    for k in HAND_PATHS:  # bottom to top: each new shape lands on top
        f, d = paths[k]
        r = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": [{
            "name": f"UdengHand_{k}", "parentId": hand, "x": 0, "y": 0,
            "paints": [{"paintType": "fill", "color": SKIN[f]}],
            "paths": [{"name": "Path", "commands": hand_commands(d)}]}]}}})
        if r.get("errors"):
            sys.exit(str(r)[:400])
    shapes = [o["id"] for o in call("query_objects", {"objectIds": [hand], "depth": 1})["objects"] if o["id"] != hand]
    fills = [o["id"] for o in call("query_objects", {"objectIds": shapes, "depth": 1})["objects"] if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {f: {"40": 0} for f in fills}})
    call("reorder_objects", {"operations": [{"objectId": hand, "order": "sendToBack"}]})
    call("set_property_values", {"propertyValues": {arm: {"18": 0}, hand: {"18": 0}}})

    ids.update({"ArmFront_R": arm, "ForeFront_R": forearm, "HandFront_R": copies[0], "ArmFFront_R": copies[1],
                "Hand_R_Udeng": hand})
    CACHE.write_text(json.dumps(ids, indent=1))
    upper(call)
    front(call)
    print(json.dumps({k: ids[k] for k in ("ArmFront_R", "ForeFront_R", "HandFront_R", "ArmFFront_R", "Hand_R_Udeng")}))


def straighten(call, sleeve):
    """Put the sleeve copy's -y vertices on a straight edge from the elbow to the round hand's
    corner, and its +y elbow corner (at 90.5) in line with the plain upper sleeve."""
    verts = [o["id"] for o in call("query_objects", {"objectIds": [sleeve], "depth": 3})["objects"]
             if "Vertex" in o["types"][0]]
    pos = values(call, verts, (24, 25))
    # ArmF_R's own vertices (same order as the copy's) give the corner the round hand is cut to
    orig = [o["id"] for o in call("query_objects", {"objectIds": [SLEEVE], "depth": 3})["objects"]
            if "Vertex" in o["types"][0]]
    opos = values(call, orig, (24, 25))
    corner = min((opos[o]["25"], opos[o]["24"]) for o in orig if opos[o]["24"] < 210)
    cy, cx = corner
    edge = lambda x: SLEEVE_EDGE + (cy - SLEEVE_EDGE) * min(max(x, 0.0), cx) / cx
    near = {v: {"25": round(edge(opos[o]["24"]), 2)} for v, o in zip(verts, orig)
            if opos[o]["25"] < 0 and opos[o]["24"] <= cx}
    near.update({v: {"25": SLEEVE_TOP} for v in verts if pos[v]["24"] < 50 and pos[v]["25"] > SLEEVE_TOP})
    call("set_property_values", {"propertyValues": near})
    print("edge from", SLEEVE_EDGE, "at the elbow to", cy, "at x", cx, "-", near)


def front(call):
    """BodyFront on Body's pivot, in front of Head, keyed like Body; ArmFront_R moves into it."""
    ids = json.loads(CACHE.read_text())
    b = values(call, [BODY], (13, 14, 15, 16, 17))[BODY]
    node = empty_group(call, "BodyFront", WAYAN, b["13"], b["14"], b["15"])
    call("reorder_objects", {"operations": [{"objectId": node, "order": "sendToFront"}]})
    call("reparent_objects", {"operations": [{"objectId": ids["ArmFront_R"], "newParentId": node, "position": "start"}]})
    anims = {a["name"]: a["id"] for a in call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]}
    for name, props in BODY_KEYS.items():
        keys = call("animation_editor", {"command": "queryKeyFrames", "data": {"queryKeyFrames": {"animationIds": [anims[name]]}}})
        keys = [k for k in keys.get("keyframes", keys)[anims[name]] if k["objectId"] == BODY and k["propertyKey"] in props]
        cubic = [k for k in keys if k["interpolationType"] == "cubic"]
        curves = values(call, [k["interpolatorId"] for k in cubic], CUBIC_KEYS) if cubic else {}
        add = []
        for k in keys:
            new = {"objectId": node, "propertyKey": k["propertyKey"], "frame": k["frame"], "value": k["value"],
                   "interpolationType": k["interpolationType"]}
            if k["interpolationType"] == "cubic":
                c = curves[k["interpolatorId"]]
                new["cubicParams"] = dict(zip(("x1", "y1", "x2", "y2"), (c[str(p)] for p in CUBIC_KEYS)))
            add.append(new)
        r = call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
            "animationId": anims[name], "add": add}}})
        print(name, len(add), "keys copied", r.get("success"))
    ids["BodyFront"] = node
    CACHE.write_text(json.dumps(ids, indent=1))
    print("BodyFront", node)


def upper(call):
    """A plain sleeve on UpperArm_R from the shoulder joint to the elbow, round at both ends."""
    ids = json.loads(CACHE.read_text())
    if ids.get("UpperRaise_R"):
        call("delete_objects", {"objectIds": [ids["UpperRaise_R"]]})
    r, k, length = UPPER_HALF, 0.5523 * UPPER_HALF, values(call, [UPPER], (89,))[UPPER]["89"]
    c = lambda x1, y1, x2, y2, x, y: {"commandType": "cubicTo", "control1X": x1, "control1Y": y1,
                                      "control2X": x2, "control2Y": y2, "endX": x, "endY": y}
    o = UPPER_SHIFT
    cmds = [{"commandType": "moveTo", "x": 0, "y": o - r}, {"commandType": "lineTo", "x": length, "y": o - r},
            c(length + k, o - r, length + r, o - k, length + r, o), c(length + r, o + k, length + k, o + r, length, o + r),
            {"commandType": "lineTo", "x": 0, "y": o + r},
            c(-k, o + r, -r, o + k, -r, o), c(-r, o - k, -k, o - r, 0, o - r), {"commandType": "close"}]
    res = call("path_editor", {"command": "createShapes", "data": {"createShapes": {"shapes": [{
        "name": "UpperRaise_R", "parentId": UPPER, "x": 0, "y": 0,
        "paints": [{"paintType": "fill", "color": "#ffededec"}], "paths": [{"name": "Path", "commands": cmds}]}]}}})
    if res.get("errors"):
        sys.exit(str(res)[:400])
    shape = next(o["id"] for o in call("find_objects", {"name": "UpperRaise_R", "parentId": UPPER})["objects"]
                 if o["type"] == "Shape")
    fill = [o["id"] for o in call("query_objects", {"objectIds": [shape], "depth": 1})["objects"] if "Fill" in o["types"]]
    call("set_property_values", {"propertyValues": {**{f: {"40": 0} for f in fill}, shape: {"18": 0}}})
    ids["UpperRaise_R"] = shape
    CACHE.write_text(json.dumps(ids, indent=1))
    print("UpperRaise_R", shape)


def main():
    call = m.connect("udeng-arm")
    cmd = sys.argv[1:] and sys.argv[1]
    if cmd == "build":
        build(call)
    elif cmd == "upper":
        upper(call)
    elif cmd == "front":
        front(call)
    elif cmd == "straighten":
        straighten(call, json.loads(CACHE.read_text())["ArmFFront_R"])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
