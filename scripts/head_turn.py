#!/usr/bin/env python3
"""Head turn for Wayan: a 2.5D head of rigid layers that slide by their depth.

headX/headY (FaceVM, -1..1) follow his gaze on a spring. The head is built by
head_rig25d.py as clean layers (skin, udeng, knot, flower block, ear, sideburn);
the skin never moves, so the silhouette stays round, and every other layer
slides by DEPTH x the turn: the knot on the front of the udeng a lot, the udeng
a little, the flower (with the ear it is tucked behind) a little, Wayan's right
ear against the turn. The rig's eyes, brows, nose and mouth slide the most, the
far eye narrows. Nothing is swapped and nothing bends, so every frame is smooth.

Earlier tries, all rejected and removed (see git history before the 2026-10-24
cleanup): bending the head with bones (dented cheek), swapping in drawn 3/4 heads
(choppy), morphing two drawings (muddled in between).

    python3 scripts/head_turn.py preview assets/preview/head_turn 0,0,0 1,0,0 ...
        sets the parts in the editor for each h,v,t pose, captures, restores
    python3 scripts/head_turn.py install
        writes the formulas as data binds (converter per property)

Needs the Rive editor open on "wayan".
"""

import argparse
import base64
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rive_mcp as m  # noqa: E402

X, Y, R, SX, SY, OPACITY = 13, 14, 15, 16, 17, 18
BX, BY = 90, 91  # RootBone x/y

A, AY = 64.0, 30.0  # travel (SVG units) of a part at depth 1 for headX / headY = 1
# Depth of each layer, across and up/down: 1 = the front of the face, 0 = the
# silhouette, below 0 = behind it (moves against the turn).
DEPTH = {"Skin": (0.0, 0.0), "Udeng": (0.12, 0.15), "Knot": (0.5, 0.4), "Fold": (0.12, 0.15),
         "Flower": (0.12, 0.15), "EarR": (-0.08, -0.1), "Side": (0.0, 0.0)}
# The flower is tucked into the udeng, so it moves with it; any other depth lets the
# udeng's end peek out from behind the petals.
# The long fold rides with the udeng at its edge and stretches to reach the knot.
FOLD_PIVOT_X, FOLD_LEN = 296.0 - 690.0, 719.0 - 296.0


def fold_stretch(h):
    return 1 + A * (DEPTH["Knot"][0] - DEPTH["Fold"][0]) * h / FOLD_LEN
FEATURE = {"face": 0.95, "nose": 1.2, "mouth": 0.85, "brow": 0.9}
NARROW = 0.1  # the far eye's width loss at a full turn
CENTRE = {"eyeL": 823.5, "eyeR": 538.0, "mouth": 678.5, "nose": 676.5}  # SVG x of each feature


def layer_shift(layer, h, v):
    dx, dy = DEPTH[layer]
    return A * dx * h, AY * dy * v


def feature_shift(part, h, v):
    """(dx, dy, scaleX, centre x) of a master feature, as the rig moves it."""
    if part.startswith("eye"):
        sign = -1 if part == "eyeL" else 1
        return (A * FEATURE["face"] * h - sign * 8 * h * h, AY * FEATURE["face"] * v,
                1 + sign * NARROW * h - 0.02 * h * h, CENTRE[part])
    depth = FEATURE["face"] if part == "face" else FEATURE[part]
    sx = 1 - 0.05 * h * h if part == "mouth" else 1.0
    return A * depth * h, AY * (FEATURE["face"] if part != "nose" else 1.15) * v, sx, CENTRE.get(part, 0)


H25 = json.loads(Path(__file__).with_name(".head25.json").read_text()) if Path(__file__).with_name(".head25.json").exists() else {"groups": {}}
F, FN, FM, FB = FEATURE["face"], FEATURE["nose"], FEATURE["mouth"], FEATURE["brow"]

RIG = [
    ("head_r", "0-2127", R, "H*0.0"),
    ("head_x", "0-2127", X, "H*6.0"),
    ("head_y", "0-2127", Y, "V*0.0"),
    # the old heads stay in the file, hidden
    ("front_top_op", "0-13030", OPACITY, "H*0.0"),
    ("front_base_op", "0-13031", OPACITY, "H*0.0"),
    ("head34L_op", "0-12700", OPACITY, "H*0.0"),
    ("head34R_op", "0-13029", OPACITY, "H*0.0"),
    ("nose_op", "0-282", OPACITY, "100.0+H*0.0"),
    # layers
    *[(f"{layer.lower()}_x", gid, X, f"{FOLD_PIVOT_X if layer == 'Fold' else 0.0}+H*({A * DEPTH[layer][0]:.2f})")
      for layer, gid in H25["groups"].items()],
    *[("fold_sx", gid, SX, f"1.0+H*{A * (DEPTH['Knot'][0] - DEPTH['Fold'][0]) / FOLD_LEN:.4f}")
      for layer, gid in H25["groups"].items() if layer == "Fold"],
    *[(f"{layer.lower()}_y", gid, Y, f"V*({AY * DEPTH[layer][1]:.2f})") for layer, gid in H25["groups"].items()],
    # features
    ("face_x", "0-2265", X, f"-10.4093+H*{A * F:.1f}"),
    ("face_y", "0-2265", Y, f"-262.8786+V*{AY * F:.1f}"),
    ("nose_x", "0-282", X, f"-2.7567+H*({A * (FN - F):.1f})"),
    ("nose_y", "0-282", Y, f"0.0677+V*{AY * 0.2:.1f}"),
    ("mouth_x", "0-791", X, f"-0.8656+H*({A * (FM - F):.1f})"),
    ("mouth_y", "0-791", Y, "95.506+V*0.0"),
    ("mouth_sx", "0-791", SX, "1.0-H*H*0.05"),
    ("eyeL_sx", "0-1696", SX, f"1.0-H*{NARROW}-H*H*0.02"),
    ("eyeR_sx", "0-1697", SX, f"1.0+H*{NARROW}-H*H*0.02"),
    ("eyeL_x", "0-1696", X, "0.0-H*H*8.0"),
    ("eyeR_x", "0-1697", X, "H*H*8.0"),
    ("happyL_x", "0-1100", X, "143.4094+H*0.0"),
    ("happyR_x", "0-1092", X, "-143.5907+H*0.0"),
    ("happyL_sx", "0-1100", SX, f"1.0-H*{NARROW}-H*H*0.02"),
    ("happyR_sx", "0-1092", SX, f"1.0+H*{NARROW}-H*H*0.02"),
    ("brow_L_x", "0-1084", X, f"133.0001+H*{A * FB:.1f}"),
    ("brow_R_x", "0-1076", X, f"-154.0+H*{A * FB:.1f}"),
    ("brow_L_sx", "0-1084", SX, f"1.0-H*{NARROW}-H*H*0.02"),
    ("brow_R_sx", "0-1076", SX, f"1.0+H*{NARROW}-H*H*0.02"),
    # brows rise less than the eyes looking up, or they slide under the udeng
    ("brows_y", "0-11269", Y, f"max(V,0.0)*{AY * F:.1f}+min(V,0.0)*{AY * 0.4:.1f}"),
]
PREFIX = "turn4_"  # converters cannot be edited or deleted, so each version gets new names

FACE_VM = "0-14"
SOURCES = {"H": "0-2259", "V": "0-2261", "T": "0-13032"}
NAMES = {"H": "headX", "V": "headY", "T": "turn"}


def evaluate(formula, h, v, t):
    expr = re.sub(r"\b([HVT])\b", lambda mm: f"({ {'H': h, 'V': v, 'T': t}[mm.group(1)] })", formula)
    return eval(expr, {"max": max, "min": min})


def editor_value(prop, value):
    """Editor units: degrees for rotation, percent for scale."""
    return math.degrees(value) if prop == R else value * 100 if prop in (SX, SY) else value


def preview(args):
    call = m.connect("head-turn")
    keys = {}
    for _, oid, prop, _ in RIG:
        keys.setdefault(oid, set()).add(prop)
    rest = call("query_property_values", {"propertyKeys": {i: sorted(k) for i, k in keys.items()}})
    rest = rest.get("values", rest)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    def pose(h, v, t):
        pv = {}
        for _, oid, prop, f in RIG:
            pv.setdefault(oid, {})[str(prop)] = editor_value(prop, evaluate(f, h, v, t))
        call("set_property_values", {"propertyValues": pv})

    try:
        for spec in args.poses:
            h, v, t = map(float, spec.split(","))
            pose(h, v, t)
            res = call("capture_artboard", {"longEdge": 1536, "backgroundColor": "#ff6ba8d2"}, raw=True)
            img = next(c for c in res["content"] if c.get("type") == "image")
            name = out / f"h{h:+.2f}_v{v:+.2f}_t{t:+.0f}.png"
            name.write_bytes(base64.b64decode(img["data"]))
            # head only: artboard px 135..495 x 75..480 at 1536/900 scale
            subprocess.run(["sips", "-c", "690", "640", "--cropOffset", "130", "220", str(name)],
                           check=True, capture_output=True)
            print(name.name, flush=True)
    finally:
        call("set_property_values", {"propertyValues": {
            i: {k: val for k, val in d.items()} for i, d in rest.items()}})
        print("rest values restored")


def install(_args):
    """One formula converter per entry. The source is the first of H, V, T the formula
    uses (H and V change every frame while turning); the others are read as {{FaceVM/...}}."""
    call = m.connect("head-turn")
    have = {c["name"]: c["id"] for c in call("viewmodel_editor", {
        "command": "listConverters", "data": {"listConverters": {}}})["converters"]}
    binds = []
    for name, oid, prop, f in RIG:
        used = [s for s in "HVT" if re.search(rf"\b{s}\b", f)]
        source = used[0]
        formula = re.sub(r"\b([HVT])\b",
                         lambda mm: "{Input}" if mm.group(1) == source else "{{FaceVM/%s}}" % NAMES[mm.group(1)], f)
        cname = f"{PREFIX}{name}"
        if cname in have:
            sys.exit(f"{cname} exists already: converters cannot be edited here, bump PREFIX")
        res = call("viewmodel_editor", {"command": "createConverters", "data": {"createConverters": {
            "converters": [{"converterType": "formula", "formula": formula, "name": cname}]}}})
        cid = res["converters"][0]["id"]
        binds.append({"objectId": oid, "propertyKey": prop, "viewModelPropertyId": SOURCES[source], "converterId": cid})
        print(cname, cid, formula)
    res = call("viewmodel_editor", {"command": "databind", "data": {"databind": {
        "viewModelId": FACE_VM, "bindings": binds}}})
    print(res.get("errors") or "bound", len(binds))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preview")
    p.add_argument("out")
    p.add_argument("poses", nargs="+", help="h,v,t triples")
    sub.add_parser("install")
    args = ap.parse_args()
    {"preview": preview, "install": install}[args.cmd](args)


if __name__ == "__main__":
    main()
