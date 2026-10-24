#!/usr/bin/env python3
"""Offline check of head_rig25d.py: the layered head as SVG at given turns.

    python3 scripts/head_rig25d_svg.py assets/preview/rig25 -1,0 -0.5,0 0,0 0.5,0 1,0

Each layer slides by DEPTH x the turn, the same numbers head_turn.py binds; the
master's eyes, mouth and nose slide like the rig's features.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import head_rig25d as hr  # noqa: E402
import svg_tools as tools  # noqa: E402
import head_turn as ht  # noqa: E402


def frame(h, v):
    master = tools.svg_paths("assets/vector/wayan_master.svg")
    body = "".join(f'<path fill="rgb{f}" d="{d}"/>' for i, (f, d) in enumerate(master) if i >= 26)
    layers = []
    for layer, idx in hr.LAYERS:
        dx, dy = ht.layer_shift(layer, h, v)
        parts = []
        for i in idx:
            fill, d = master[i]
            if layer == "Skin":
                pts = [(c["x"], c["y"]) for c in hr.skin_commands() if c["commandType"] == "moveTo"]
                cmds = hr.skin_commands()
                d = "M " + " ".join(
                    (f'{c["x"] + 690} {c["y"] + 990}' if c["commandType"] == "moveTo" else
                     f'C {c["control1X"] + 690} {c["control1Y"] + 990} {c["control2X"] + 690} {c["control2Y"] + 990} {c["endX"] + 690} {c["endY"] + 990}'
                     if c["commandType"] == "cubicTo" else "Z") for c in cmds)
            parts.append(f'<path fill="rgb{fill}" d="{d}"/>')
        if layer == "Fold":  # pinned at the udeng's edge, stretched toward the knot
            px = hr.FOLD_EDGE[0]
            layers.append(f'<g transform="translate({px + dx:.1f} {dy:.1f}) scale({ht.fold_stretch(h):.4f} 1) '
                          f'translate({-px:.1f} 0)">{"".join(parts)}</g>')
            continue
        layers.append(f'<g transform="translate({dx:.1f} {dy:.1f})">{"".join(parts)}</g>')
    feats = []
    for i, part in {20: "eyeL", 21: "eyeL", 22: "eyeR", 23: "eyeR", 24: "mouth", 25: "nose"}.items():
        fill, d = master[i]
        dx, dy, sx, cx = ht.feature_shift(part, h, v)
        feats.append(f'<path fill="rgb{fill}" transform="translate({cx + dx:.1f} {dy:.1f}) scale({sx:.3f} 1) '
                     f'translate({-cx:.1f} 0)" d="{d}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="150 60 1050 1050">'
            f'<rect width="1347" height="2048" fill="#6ba8d2"/>{body}{"".join(layers)}{"".join(feats)}</svg>')


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for spec in sys.argv[2:]:
        h, v = map(float, spec.split(","))
        (out / f"h{h:+.2f}_v{v:+.2f}.svg").write_text(frame(h, v))
    print(len(sys.argv) - 2, "frames ->", out)


if __name__ == "__main__":
    main()
