#!/usr/bin/env python3
"""Key the Om Swastiastu gesture (timeline A_Salam, 2 s at 60 fps).

The approved way to animate a hand gesture on Wayan:
  1. the rig's real arms rise on their bones, speeding up, to a pose whose
     outline matches the drawn key pose (Pose_Salam, hands together);
  2. at the fastest frame a one-frame opacity cut hides the rig's shirt torso,
     arm pieces, round hands and shirt lines and shows Pose_Salam;
  3. the body bounces and the head bows, then the cut runs in reverse and the
     bones bring the arms down with a small overshoot.
The A_Salam -> A_Rest transition is 0 ms so a cancel never crossfades layers.

Deletes every key in A_Salam and writes them again, so it can be rerun after
tuning the numbers below. Review with scripts/rive_frames.py before exporting.

    python3 scripts/salam_keys.py

Object ids are from the Rive file "wayan"; needs the editor open on it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

UA_L, FA_L, UA_R, FA_R = "0-732", "0-733", "0-734", "0-735"  # arm bones
HEAD, BODY, POSE = "0-729", "0-730", "0-8132"                  # Head, Body, Pose_Salam
RIG = ["0-8435",                                               # Shirt_Torso
       "0-9550", "0-9526", "0-9459", "0-9429", "0-9840", "0-9813", "0-9826", "0-9854",  # ArmU/D/B/F
       "0-124", "0-135",                                       # Hand_L/R (round)
       "0-107", "0-98"]                                        # ShirtLine_L/R
ALWAYS_OFF = ["0-9058", "0-9072", "0-9960", "0-9966", "0-234"]  # old palms, creases, old Shirt
ALWAYS_ON = ["0-118", "0-2250", "0-2241", "0-787"]              # Neck, Shoulder_L/R, Neck_Back

# Arm poses as (UpperArm_L, Forearm_L, UpperArm_R, Forearm_R) rotations in degrees.
REST = (70.61, -1.35, 110.44, 2.63)
DOWN = (73.0, -7.0, 108.0, 8.0)       # anticipation: arms settle back a little
MATCH = (52.0, 125.0, 128.0, -125.0)  # bone pose whose outline matches Pose_Salam
SETTLE = (69.0, 3.0, 112.0, -2.0)     # small overshoot on the way down
CUT_IN, CUT_OUT = 20, 90              # frames where the drawing swaps in and out

EASE_IN = {"x1": 0.55, "y1": 0.0, "x2": 1.0, "y2": 1.0}   # accelerate into the cut
EASE_OUT = {"x1": 0.0, "y1": 0.0, "x2": 0.35, "y2": 1.0}  # leave the cut fast, then slow
EASE = {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0}


def keys():
    out = []

    def key(obj, prop, frame, value, kind="cubic", curve=EASE):
        k = {"objectId": obj, "propertyKey": prop, "frame": frame, "value": value, "interpolationType": kind}
        if kind == "cubic":
            k["cubicParams"] = curve
        out.append(k)

    def arms(frame, pose, curve=EASE):
        for obj, v in zip((UA_L, FA_L, UA_R, FA_R), pose):
            key(obj, 15, frame, v, curve=curve)

    arms(0, REST); arms(8, DOWN, EASE_IN); arms(CUT_IN, MATCH)
    arms(CUT_OUT, MATCH, EASE_OUT); arms(106, SETTLE); arms(114, REST); arms(120, REST)
    for obj in RIG:  # opacity: rig visible, hidden while the drawing shows
        key(obj, 18, 0, 100, "hold"); key(obj, 18, CUT_IN, 0, "hold"); key(obj, 18, CUT_OUT, 100, "hold")
    key(POSE, 18, 0, 0, "hold"); key(POSE, 18, CUT_IN, 100, "hold"); key(POSE, 18, CUT_OUT, 0, "hold")
    for obj in ALWAYS_OFF:
        key(obj, 18, 0, 0, "hold")
    for obj in ALWAYS_ON:
        key(obj, 18, 0, 100, "hold")
    # Bow: the head dips after the cut and rises before the cut back.
    for f, v in ((0, 990), (CUT_IN, 990), (32, 1006), (44, 1003), (80, 1003), (96, 988), (104, 991), (110, 990), (120, 990)):
        key(HEAD, 14, f, v)
    # Body scaleY: squash in anticipation, bounce on arrival and on the way down.
    for f, v in ((0, 100), (8, 98.5), (CUT_IN, 101.5), (28, 99.3), (36, 100), (84, 100), (94, 101), (104, 99.6), (112, 100), (120, 100)):
        key(BODY, 17, f, v)
    return out


def main():
    call = m.connect("salam-keys")
    anims = call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]
    anim = next(a["id"] for a in anims if a["name"] == "A_Salam")
    old = call("animation_editor", {"command": "queryKeyFrames", "data": {"queryKeyFrames": {"animationIds": [anim]}}})
    old = old.get("keyframes", old)[anim]
    # Delete and add in separate calls: one call doing both can drop the new keys.
    call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
        "animationId": anim, "delete": [k["keyframeId"] for k in old]}}})
    new = keys()
    r = call("animation_editor", {"command": "modifyKeyFrames", "data": {"modifyKeyFrames": {
        "animationId": anim, "add": new}}})
    print(f"A_Salam: removed {len(old)} keys, added {len(new)}, success={r.get('success')}")


if __name__ == "__main__":
    main()
