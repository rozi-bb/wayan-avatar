#!/usr/bin/env python3
"""Render frames of a Rive timeline to PNGs for a frame-by-frame review sheet.

Reads the timeline's keyframes (hold, linear and cubic curves) from the open
editor, sets every keyed property to its value at each requested frame,
captures the artboard, and puts the rest values back afterwards. No timeline
has to be open, and the file is left as it was.

    python3 scripts/rive_frames.py A_Salam assets/preview/salam_k1 0,4,8,20,90,120

Writes d0.png (the rest pose before anything is set) and fNNN.png per frame.
A page such as assets/preview/salam_k1.html lays them out for Rozi.
Needs the Rive editor open on "wayan".
"""

import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

CUBIC_KEYS = [63, 64, 65, 66]  # x1, y1, x2, y2 of a CubicInterpolator


def bezier(c, x):
    """y on a CSS-style cubic-bezier curve at progress x."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        t = (lo + hi) / 2
        bx = 3 * (1 - t) ** 2 * t * c[0] + 3 * (1 - t) * t * t * c[2] + t ** 3
        lo, hi = (t, hi) if bx < x else (lo, t)
    t = (lo + hi) / 2
    return 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t * t * c[3] + t ** 3


def value_at(track, f):
    if f <= track[0]["frame"]:
        return track[0]["value"]
    for a, b in zip(track, track[1:]):
        if a["frame"] <= f < b["frame"]:
            if a["interpolationType"] == "hold":
                return a["value"]
            x = (f - a["frame"]) / (b["frame"] - a["frame"])
            curve = a.get("curve", (0, 0, 1, 1))  # linear when there is no cubic curve
            return a["value"] + (b["value"] - a["value"]) * bezier(curve, x)
    return track[-1]["value"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("animation", help="timeline name, e.g. A_Salam")
    ap.add_argument("out", help="folder for the PNGs")
    ap.add_argument("frames", help="comma-separated frame numbers")
    ap.add_argument("--size", type=int, default=600, help="long edge in px")
    ap.add_argument("--bg", default="#ff242424", help="background #aarrggbb")
    args = ap.parse_args()

    call = m.connect("rive-frames")
    anims = call("animation_editor", {"command": "listLinearAnimations"})["linearAnimations"]
    anim = next((a["id"] for a in anims if a["name"] == args.animation), None)
    if not anim:
        sys.exit(f"no timeline named {args.animation}")
    keys = call("animation_editor", {"command": "queryKeyFrames",
                                     "data": {"queryKeyFrames": {"animationIds": [anim]}}})
    keys = keys.get("keyframes", keys)[anim]

    cubic = [k for k in keys if k["interpolationType"] == "cubic"]
    if cubic:
        curves = call("query_property_values",
                      {"propertyKeys": {k["interpolatorId"]: CUBIC_KEYS for k in cubic}})
        curves = curves.get("values", curves)
        for k in cubic:
            c = curves[k["interpolatorId"]]
            k["curve"] = tuple(c[str(p)] for p in CUBIC_KEYS)
    for k in keys:
        if k["interpolationType"] not in ("hold", "linear", "cubic"):
            print(f"warning: {k['interpolationType']} key on {k['objectId']} drawn as linear")

    tracks = {}
    for k in keys:
        tracks.setdefault((k["objectId"], k["propertyKey"]), []).append(k)
    for t in tracks.values():
        t.sort(key=lambda k: k["frame"])

    def put(values):
        pv = {}
        for (obj, prop), v in values.items():
            pv.setdefault(obj, {})[str(prop)] = v
        call("set_property_values", {"propertyValues": pv})

    def shot(name):
        res = call("capture_artboard", {"longEdge": args.size, "backgroundColor": args.bg}, raw=True)
        img = next(c for c in res["content"] if c.get("type") == "image")
        (out / name).write_bytes(base64.b64decode(img["data"]))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rest = call("query_property_values", {"propertyKeys": {
        obj: [p for (o, p) in tracks if o == obj] for (obj, _) in tracks}})
    rest = {(o, int(p)): v for o, d in rest.get("values", rest).items() for p, v in d.items()}
    try:
        shot("d0.png")
        for f in map(int, args.frames.split(",")):
            put({kp: round(value_at(t, f), 3) for kp, t in tracks.items()})
            shot(f"f{f:03d}.png")
            print(f"f{f:03d}", end=" ", flush=True)
    finally:
        put(rest)
        print("\nrest values restored")


if __name__ == "__main__":
    main()
