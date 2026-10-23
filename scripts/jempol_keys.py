#!/usr/bin/env python3
"""Key the thumbs-up (timeline A_Jempol, 1.8 s at 60 fps, FaceVM.action = 2).

Wayan's right arm (screen left) rises on its bones; at the fastest frame the
round hand is swapped for the Recraft thumbs-up hand (Hand_R_ThumbUp, under the
cuff, pivoting at the wrist) together with a round elbow and the forearm fold
line. The thumb then springs: the arm overshoots and settles while the hand
pops in scale and wiggles, the body bounces and the head nods. On the way down
the swap runs in reverse before the arm lands with a small overshoot. The page
adds the smile (FaceVM.expression), as it does for Om Swastiastu.

Deletes every key in A_Jempol and writes them again; review with
scripts/rive_frames.py before exporting.

    python3 scripts/jempol_keys.py

Object ids are from the Rive file "wayan"; needs the editor open on it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

UA, FA = "0-734", "0-735"            # UpperArm_R, Forearm_R
HEAD, BODY = "0-729", "0-730"
ROUND_HAND, THUMB = "0-135", "0-10835"  # Hand_R, Hand_R_ThumbUp (origin at the wrist)
ELBOW, CREASE, SHIRT_LINE = "0-10836", "0-9966", "0-98"
UA_Y = -261.71                        # UpperArm_R rest y (bone key 91); minus = shoulder up

# frame: (UpperArm_R r, Forearm_R r, shoulder lift)
ARM = {
    0: (110.44, 2.63, 0),
    6: (113.0, 6.0, 2),         # anticipation: arm swings back a little
    16: (99.0, -91.0, -22),     # overshoot past the pose
    22: (102.2, -80.5, -16),    # spring back
    27: (100.5, -85.6, -19),
    33: (101.0, -84.0, -18),    # thumbs-up pose
    70: (101.0, -84.0, -18),
    75: (100.0, -88.0, -20),    # small lift before dropping
    90: (111.5, 5.0, 1),        # land, a little past rest
    97: (109.9, 1.8, 0),
    104: (110.44, 2.63, 0),
    108: (110.44, 2.63, 0),
}
# thumb hand pop and wiggle around the wrist: frame: (scale %, rotation)
THUMB_SPRING = {15: (104, 6), 19: (122, -6), 24: (104, 5), 29: (114, -2), 35: (110, 0),
                70: (110, 0), 75: (112, 3), 80: (106, 6)}
HEAD_Y = {0: 990, 6: 993, 16: 990, 22: 1006, 30: 984, 36: 997, 42: 989, 48: 990,
          70: 990, 80: 994, 92: 987, 100: 990, 108: 990}
BODY_SY = {0: 100, 6: 98.6, 16: 101.8, 24: 99.3, 32: 100.4, 38: 100, 70: 100,
           82: 99.2, 92: 100.8, 100: 100, 108: 100}
CUT_IN, CUT_OUT = 15, 80               # swap frames, in the fastest part of each move
SHIRT_LINE_OFF, SHIRT_LINE_ON = 6, 86  # the armpit line would show as a stub while bent

EASE = {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0}
EASE_IN = {"x1": 0.55, "y1": 0.0, "x2": 1.0, "y2": 1.0}
EASE_OUT = {"x1": 0.0, "y1": 0.0, "x2": 0.35, "y2": 1.0}
CURVE = {6: EASE_IN, 75: EASE_IN, 16: EASE_OUT}  # speed up into the cuts, spring out of the overshoot


def keys():
    out = []

    def key(obj, prop, frame, value, kind="cubic"):
        k = {"objectId": obj, "propertyKey": prop, "frame": frame, "value": value, "interpolationType": kind}
        if kind == "cubic":
            k["cubicParams"] = CURVE.get(frame, EASE)
        out.append(k)

    for f, (ua, fa, lift) in ARM.items():
        key(UA, 15, f, ua); key(FA, 15, f, fa); key(UA, 91, f, round(UA_Y + lift, 2))
    for f, (s, r) in THUMB_SPRING.items():
        key(THUMB, 16, f, s); key(THUMB, 17, f, s); key(THUMB, 15, f, r)
    for f, v in HEAD_Y.items():
        key(HEAD, 14, f, v)
    for f, v in BODY_SY.items():
        key(BODY, 17, f, v)
    for obj in (THUMB, ELBOW, CREASE):  # swapped in and out together with the hand
        key(obj, 18, 0, 0, "hold"); key(obj, 18, CUT_IN, 100, "hold"); key(obj, 18, CUT_OUT, 0, "hold")
    key(ROUND_HAND, 18, 0, 100, "hold"); key(ROUND_HAND, 18, CUT_IN, 0, "hold"); key(ROUND_HAND, 18, CUT_OUT, 100, "hold")
    key(SHIRT_LINE, 18, 0, 100, "hold"); key(SHIRT_LINE, 18, SHIRT_LINE_OFF, 0, "hold"); key(SHIRT_LINE, 18, SHIRT_LINE_ON, 100, "hold")
    return out


def main():
    call = m.connect("jempol-keys")
    anims = call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]
    anim = next(a["id"] for a in anims if a["name"] == "A_Jempol")
    old = call("animation_editor", {"command": "queryKeyFrames", "data": {"queryKeyFrames": {"animationIds": [anim]}}})
    old = old.get("keyframes", old)[anim]
    if old:  # delete and add in separate calls: one call doing both can drop the new keys
        call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
            "animationId": anim, "delete": [k["keyframeId"] for k in old]}}})
    new = keys()
    r = call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
        "animationId": anim, "add": new}}})
    print(f"A_Jempol: removed {len(old)} keys, added {len(new)}, success={r.get('success')}")


if __name__ == "__main__":
    main()
