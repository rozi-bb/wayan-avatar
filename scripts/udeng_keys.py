#!/usr/bin/env python3
"""Key the udeng idle (timeline A_Udeng, 60 fps, FaceVM.action = 3).

The udeng slips: it tilts down over Wayan's right eye (UdengSlip, KnotSlip and FoldSlip
rotate about their shared pivot, see scripts/udeng_rig.py), speeding up like a fall and
landing with a small bounce. Wayan's right arm swings up on its bones; at the fastest frame
the round hand is swapped for the Recraft hand, which lands on the udeng's end, pushes it
back up (the wrist follows the band's corner frame by frame) and lets go, so the udeng
flicks into place with a small overshoot. The arm drops back with the swap reversed.

The forearm is drawn twice: the real one in Body (behind the head) and ArmFront_R /
ForeFront_R in BodyFront (in front of it, see scripts/udeng_arm.py). Both get the same keys,
so they always coincide; the front one is only shown while the arm is up.

Also adds the A_Udeng state (action = 3) to the Aksi layer and puts every property the
gesture touches back in A_Rest. Deletes A_Udeng's keys and writes them again; review with
scripts/rive_frames.py before exporting.

    python3 scripts/udeng_keys.py

Ids come from scripts/.udeng.json; needs the Rive editor open on "wayan".
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

IDS = json.loads(Path(__file__).with_name(".udeng.json").read_text())
UA, FA = "0-734", "0-735"                      # UpperArm_R, Forearm_R
AF, FF = IDS["ArmFront_R"], IDS["ForeFront_R"]
SLIPS = [IDS["UdengSlip"], IDS["KnotSlip"], IDS["FoldSlip"]]
HAND, ROUND, ROUND_FRONT = IDS["Hand_R_Udeng"], "0-135", IDS["HandFront_R"]
UPPER_RAISE, SHIRT_LINE = IDS["UpperRaise_R"], "0-98"
# Body sleeve pieces hidden while the plain upper sleeve and the front forearm stand in: the elbow
# disc ArmD_R, ArmB_R (a skinned forearm copy behind the sash) and ArmU_R (the skinned upper
# sleeve) stick out past their edges once the arm is raised, and ArmF_R's cuff flare would show
# past the straightened copy.
STAND_INS = ["0-9459", "0-9840", "0-9550", "0-9854"]
ACTION, ACTION_PROP = 3, "0-5608"             # FaceVM.action
LENGTH = 168

UA_REST, FA_REST, UA_Y = 110.44, 2.63, -261.7071   # rest rotation and UpperArm_R y (minus = shoulder up)
L1, L2 = 187.0662, 171.8103                          # UpperArm_R, Forearm_R lengths
SHOULDER = (680 - 267.4649, 1290 - 261.7071)          # SVG units
PIVOT = (1250.0, 620.0)                               # the slip pivot, SVG units
CORNER = (266.0, 478.0)                               # the band's lower left corner at rest
GRIP = (-13.0, 114.0)                                 # wrist minus corner while holding it

# Udeng tilt in degrees (negative = down on the left of the picture).
TILT = {0: 0, 4: -0.4, 30: -13.0, 37: -11.2, 43: -12.4, 48: -12.0,
        96: -12.0, 116: -6.5, 125: 1.2, 133: -0.5, 140: 0.0, LENGTH: 0.0}
TILT_CURVE = {4: (0.55, 0.0, 1.0, 1.0), 30: (0.0, 0.0, 0.4, 1.0), 116: (0.0, 0.0, 0.45, 1.0)}
PUSH = (96, 116)                                      # the wrist follows the band's corner here

# Arm: frame -> ("rest") | ("ang", upper, fore, lift) | ("grip", lift) for the wrist on the corner
ARM = {
    0: ("rest",), 52: ("rest",),
    58: ("ang", 114.0, 7.0, 2.0),          # a little swing back first
    70: ("ang", 162.0, 12.0, -4.0),        # the arm swings up nearly straight ...
    84: ("grip", -12.0, 3.0),              # ... and bends at the elbow only to reach the udeng, a touch past its corner ...
    90: ("grip", -10.0, 0.0),              # ... and onto it
    96: ("grip", -10.0, 0.0),
    # 96-116: computed per 2 frames while pushing
    122: ("ang", 196.0, 66.0, -18.0),      # let go: the hand leaves the band
    133: ("ang", 162.0, 12.0, -6.0),       # the elbow straightens as the arm swings down
    148: ("ang", 111.8, 5.0, 1.0),         # land a little past rest
    155: ("ang", 109.9, 1.8, 0.0),
    161: ("rest",), LENGTH: ("rest",),
}
# Into the middle poses the arm speeds up, out of them it slows down, so it never stops there
# and the hand swap at the middle pose falls on the fastest frames.
ARM_CURVE = {52: (0.5, 0.0, 0.7, 1.0), 58: (0.45, 0.0, 1.0, 1.0), 70: (0.0, 0.0, 0.4, 1.0),
             84: (0.3, 0.0, 0.5, 1.0), 122: (0.5, 0.0, 1.0, 1.0), 133: (0.0, 0.0, 0.45, 1.0)}
# Wrist flex of the Recraft hand (degrees; + bends the fingers toward the head)
FLEX = {0: 0, 70: 24, 84: 20, 90: 14, 96: 14, 116: 6, 122: 0, 133: 8, LENGTH: 0}
# The front forearm and plain upper sleeve stand in for the body's sleeve pieces from the first
# frame the arm moves until it is all but down: once the arm leaves the body, the body's pieces
# kink at the elbow (ArmB_R and the elbow disc stick out on its inner side). At rest the stand-ins
# differ only by a sliver of the inner edge against the sash.
SHOW_FRONT, HIDE_FRONT = 53, 150
LINE_OFF, LINE_ON = 52, 161                           # the armpit shirt line would show as a stub while raised
CUT_IN, CUT_OUT = 70, 133                             # round hand <-> Recraft hand, at the middle poses

EASE = (0.42, 0.0, 0.58, 1.0)


def ik(wrist, lift):
    """Upper and fore rotations (degrees) putting the wrist at `wrist` (SVG units), elbow out."""
    sx, sy = SHOULDER[0], SHOULDER[1] + lift
    dx, dy = wrist[0] - sx, wrist[1] - sy
    d = min(math.hypot(dx, dy), L1 + L2 - 0.5)
    phi = math.degrees(math.atan2(dy, dx))
    a = math.degrees(math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
    upper = (phi - a) % 360
    ex, ey = sx + L1 * math.cos(math.radians(upper)), sy + L1 * math.sin(math.radians(upper))
    fore = (math.degrees(math.atan2(wrist[1] - ey, wrist[0] - ex)) - upper + 180) % 360 - 180
    return upper, fore


def corner(tilt):
    a = math.radians(tilt)
    x, y = CORNER[0] - PIVOT[0], CORNER[1] - PIVOT[1]
    return PIVOT[0] + x * math.cos(a) - y * math.sin(a), PIVOT[1] + x * math.sin(a) + y * math.cos(a)


def bezier(c, x):
    lo, hi = 0.0, 1.0
    for _ in range(50):
        t = (lo + hi) / 2
        bx = 3 * (1 - t) ** 2 * t * c[0] + 3 * (1 - t) * t * t * c[2] + t ** 3
        lo, hi = (t, hi) if bx < x else (lo, t)
    t = (lo + hi) / 2
    return 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t * t * c[3] + t ** 3


def tilt_at(f):
    fs = sorted(TILT)
    for a, b in zip(fs, fs[1:]):
        if a <= f <= b:
            return TILT[a] + (TILT[b] - TILT[a]) * bezier(TILT_CURVE.get(a, EASE), (f - a) / (b - a))
    return TILT[fs[-1]]


def arm_pose(spec, f):
    if spec[0] == "rest":
        return UA_REST, FA_REST, 0.0
    if spec[0] == "ang":
        return spec[1], spec[2], spec[3]
    c = corner(tilt_at(f))
    up = spec[2] if len(spec) > 2 else 0.0
    return (*ik((c[0] + GRIP[0], c[1] + GRIP[1] - up), spec[1]), spec[1])


def keys():
    out = []

    def key(obj, prop, frame, value, kind="cubic", curve=EASE):
        k = {"objectId": obj, "propertyKey": prop, "frame": frame, "value": round(value, 3), "interpolationType": kind}
        if kind == "cubic":
            k["cubicParams"] = dict(zip(("x1", "y1", "x2", "y2"), curve))
        out.append(k)

    for f, t in TILT.items():
        for s in SLIPS:
            key(s, 15, f, t, curve=TILT_CURVE.get(f, EASE))

    poses = {f: (arm_pose(spec, f), "cubic", ARM_CURVE.get(f, EASE)) for f, spec in ARM.items()}
    for f in range(PUSH[0], PUSH[1] + 1, 2):  # wrist on the corner, linear between close keys
        poses[f] = (arm_pose(("grip", -10.0 - 14.0 * (f - PUSH[0]) / (PUSH[1] - PUSH[0])), f), "linear", None)
    poses[PUSH[1]] = (poses[PUSH[1]][0], "cubic", ARM_CURVE.get(PUSH[1], EASE))
    for f, ((upper, fore, lift), kind, curve) in sorted(poses.items()):
        for obj in (UA, AF):
            key(obj, 15, f, upper, kind, curve)
        for obj in (FA, FF):
            key(obj, 15, f, fore, kind, curve)
        key(UA, 91, f, UA_Y + lift, kind, curve)
        key(AF, 14, f, UA_Y + lift, kind, curve)

    for f, r in FLEX.items():
        key(HAND, 15, f, r)
    for obj in (AF, UPPER_RAISE):
        key(obj, 18, 0, 0, "hold"); key(obj, 18, SHOW_FRONT, 100, "hold"); key(obj, 18, HIDE_FRONT, 0, "hold")
    for obj in STAND_INS:
        key(obj, 18, 0, 100, "hold"); key(obj, 18, SHOW_FRONT, 0, "hold"); key(obj, 18, HIDE_FRONT, 100, "hold")
    key(SHIRT_LINE, 18, 0, 100, "hold"); key(SHIRT_LINE, 18, LINE_OFF, 0, "hold"); key(SHIRT_LINE, 18, LINE_ON, 100, "hold")
    for obj, on in ((HAND, 100), (ROUND, 0), (ROUND_FRONT, 0)):
        key(obj, 18, 0, 100 - on, "hold"); key(obj, 18, CUT_IN, on, "hold"); key(obj, 18, CUT_OUT, 100 - on, "hold")
    return out


def rest_keys():
    """Values A_Rest must hold so a cancelled udeng leaves nothing behind."""
    out = [{"objectId": s, "propertyKey": 15, "frame": 0, "value": 0, "interpolationType": "hold"} for s in SLIPS]
    out += [{"objectId": o, "propertyKey": 18, "frame": 0, "value": v, "interpolationType": "hold"}
            for o, v in ((AF, 0), (UPPER_RAISE, 0), (HAND, 0), (ROUND_FRONT, 100))]
    out.append({"objectId": HAND, "propertyKey": 15, "frame": 0, "value": 0, "interpolationType": "hold"})
    return out


def write(call, anim, new):
    old = call("animation_editor", {"command": "queryKeyFrames", "data": {"queryKeyFrames": {"animationIds": [anim]}}})
    old = old.get("keyframes", old)[anim]
    if old:  # delete and add in separate calls: one call doing both can drop the new keys
        call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
            "animationId": anim, "delete": [k["keyframeId"] for k in old]}}})
    r = call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {"animationId": anim, "add": new}}})
    return len(old), r.get("success")


def main():
    call = m.connect("udeng-keys")
    anims = {a["name"]: a["id"] for a in call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]}
    if "A_Udeng" not in anims:
        call("animation_editor", {"command": "createLinearAnimations", "data": {"createLinearAnimations": {
            "linearAnimations": [{"name": "A_Udeng", "duration": LENGTH / 60}]}}})  # seconds
        anims = {a["name"]: a["id"] for a in call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]}
    anim = anims["A_Udeng"]
    removed, ok = write(call, anim, keys())
    print(f"A_Udeng: removed {removed} keys, added {len(keys())}, success={ok}")

    # A_Rest: drop older keys on these properties, then add the rest values
    rest = anims["A_Rest"]
    old = call("animation_editor", {"command": "queryKeyFrames", "data": {"queryKeyFrames": {"animationIds": [rest]}}})
    old = old.get("keyframes", old)[rest]
    mine = {(k["objectId"], k["propertyKey"]) for k in rest_keys()}
    stale = [k["keyframeId"] for k in old if (k["objectId"], k["propertyKey"]) in mine]
    if stale:
        call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {"animationId": rest, "delete": stale}}})
    r = call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {"animationId": rest, "add": rest_keys()}}})
    print(f"A_Rest: {len(rest_keys())} keys, success={r.get('success')}")

    # Aksi layer: A_Rest -> A_Udeng on action = 3, back on action = 0, both instant
    def aksi():
        sm = call("animation_editor", {"command": "queryStateMachine"})
        return next(l for l in sm["layers"] if l["layerName"] == "Aksi")
    layer = aksi()
    if any(s.get("animationName") == "A_Udeng" for s in layer["states"]):
        print("A_Udeng state exists")
        return
    call("animation_editor", {"command": "createStates", "data": {"createStates": {
        "layerId": layer["layerId"], "states": [{"name": "A_Udeng", "linearAnimationName": "A_Udeng", "x": 600, "y": 120}]}}})
    layer = aksi()
    rest_state = next(s["id"] for s in layer["states"] if s.get("animationName") == "A_Rest")
    udeng_state = next(s["id"] for s in layer["states"] if s.get("animationName") == "A_Udeng")
    call("animation_editor", {"command": "createTransitions", "data": {"createTransitions": {"states": [
        {"id": rest_state, "transitions": [{"to": udeng_state}]},
        {"id": udeng_state, "transitions": [{"to": rest_state}]}]}}})
    layer = aksi()
    conds = []
    for t in layer["transitions"]:
        if (t["fromStateId"], t["toStateId"]) in ((rest_state, udeng_state), (udeng_state, rest_state)) and not t["conditions"]:
            value = ACTION if t["toStateId"] == udeng_state else 0
            conds.append({"id": t["id"], "conditions": [{"leftComparator": {"viewModelPropertyId": ACTION_PROP},
                          "operation": "equal", "rightComparator": {"valueType": "constantValueType", "value": value}}]})
    r = call("animation_editor", {"command": "createConditions", "data": {"createConditions": {"transitions": conds}}})
    print("state A_Udeng with", len(conds), "transitions", r.get("success"))


if __name__ == "__main__":
    main()
