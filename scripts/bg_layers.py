#!/usr/bin/env python3
"""Split the courtyard background into layers the page can animate.

    python3 scripts/bg_layers.py

Reads web/bg_rumah.svg (one flat stack of vectorized paths, path 0 is the
sky rectangle) and writes these SVGs next to it:

  bg_back.svg      paths drawn before the tree (wall, floor, back of the bale)
  bg_tree.svg      the frangipani tree, cropped to TREE_BOX so it can sway
  bg_front.svg     everything drawn after the tree (gate, bale, pots)
  bg_plant_?.svg   the plant in each of the three pots (l, m, r), cropped so it can sway
  bg_pots.svg      pot rims drawn again over the plants, so the stems stay in the pot
  bg_flower.svg    one blossom from the tree, for the blossoms that fall

The sky is left out: the page paints it as a colour and floats clouds over it.
The tree is cut by the left edge of the picture, so a mirrored copy is drawn
outside that edge; when the tree leans right, the mirror fills the sliver
instead of sky showing through.

One blossom near the top of the canopy was never drawn: its petals were the
cream sky showing through notches in three leaves (322, 406 over the darker
137), so once the sky turned blue it looked like a hole cut in the leaves.
LEAF_PATCH closes the notch: drawn just above leaf 137, a light patch carries
the canopy edge of 322 on to 406 (tangent at both joins) and a dark patch
carries the dark/light boundary across. The old centre (NOTCH_CENTRE) goes,
and NEW_BLOSSOM puts a blossom the size of its neighbours on top.

Each potted plant sways from where its stems leave the soil (POTS pivot). A
plant is cut out with a mask that replays the picture's paint order (its own
paths white, anything painted later black), so at rest it looks exactly as
drawn, gaps between the stems included. The middle and right plants stand
against the sky, but the gaps between their stems are still the old cream sky
(250,248,243) and its blends with the leaf green, missed when the sky turned
blue; those paths (POTS sky) are cut out of the plant and dropped, so the blue
shows through, and the middle pot's rim point that the cream hid is filled with
soil (POTS patch, drawn with the rims). The left one stands in front of the gate, and the gate was
vectorized with plant-shaped holes over a flat beige, with bits of wall
painted into the gaps between the leaves. POT_PATCH redraws the wall behind
it (brick rows, the pilaster's edge line, the red column and its plinth, the
lit step) at the end of bg_front.svg, masked to the plant's outline grown by
1.5 so it only shows where leaves used to be. The dark bits painted between
its leaves (paths 50-53) read as a block hanging from the plant once it
moves, so they are left behind the patch.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "bg_rumah.svg"

NOTCH_CENTRE = [481, 482, 483, 484]
TREE = [*range(137, 163), *range(198, 212), *range(322, 336), *range(337, 346),
        406, 474, 476, 477, 480]
# A leaf tip cut by the left edge: once the tree leans right it comes into view with its mirror
# as a whole leaf floating above the canopy, so it is left out.
EDGE_TIP = [474]
BACK_END = 137                       # paths 1..136 sit behind the tree
TREE_BOX = (-120, 480, 540, 580)     # x, y, w, h in picture units
FLOWER = [323, 324, 325, 326, 327, 328, 329, 332]  # petals and centre, not the leaf bits between them
FLOWER_BOX = (60, 536, 92, 98)
LEAF_PATCH = [
    ("rgb(32,133,92)", "M 219.9 626.7 C 233.9 632.1 255.7 641.7 267.7 650.7 L 300 645 L 312 625 "
                       "L 306 612.6 C 282.1 605.2 262 589.5 240.4 577 L 230 590 L 215 600 L 205 612 Z"),
    ("rgb(36,108,79)", "M 219.9 626.7 C 233.9 632.1 255.7 641.7 267.7 650.7 L 275 670 L 225 660 L 210 640 Z"),
]
# The FLOWER blossom (centre 107, 586) at the old centre, turned and shrunk to its neighbours' size.
NEW_BLOSSOM = "translate(257 608) rotate(28) scale(0.74) translate(-107 -586)"
POTS = {
    "l": {"plant": [42, 43, 45, 46, 47, 48, 49, 55], "sky": [], "cover": [], "pivot": (122.5, 1686)},
    "m": {"plant": [403, 404, 431, 432, 446, 451, 463], "sky": [405, 433, 434, 435],
          "cover": [422, 440, 441, 442, 443], "pivot": (461, 1527),
          # The rim was cut to a point between the stems under the cream gap: rim colour fills the
          # notch below the soil line, then soil carries 442 across to 443.
          "patch": [("rgb(223,110,70)", "M 449 1530.5 H 466 V 1534.5 H 449 Z"),
                    ("rgb(155,71,57)", "M 448 1527.05 C 455 1526.95 460.5 1526.4 467.5 1526.1 L 467.5 1531.75 "
                                       "C 463 1532.6 455 1532.95 448 1532.3 Z")]},
    "r": {"plant": [410, 411, 412, 447, 448, 453, 459, 460, 461, 462, 464, 465, 466, 468, 469, 470],
          "sky": [*range(413, 421)], "cover": [421, 436, 437, 438, 439], "pivot": (1022, 1528)},
}
BEIGE, RED, LIT = "rgb(208,182,160)", "rgb(170,62,55)", "rgb(218,200,177)"
POT_PATCH = [
    (BEIGE, "M 50 1495 H 200 V 1690 H 50 Z"),                                     # pilaster faces
    (RED, "M 40 1495 L 72.73 1495 L 72.95 1544.08 L 40 1555 Z"),                  # upper wall (37)
    (RED, "M 40 1615.11 L 89.8 1598.2 L 89.8 1690 L 40 1690 Z"),                  # lower wall under the ledge (36)
    ("rgb(23,12,11)", "M 60 1632.5 L 80.9 1625.38 L 87.5 1623.4 L 81.53 1626.6 L 60 1633.9 Z"),  # mortar 7|4
    ("rgb(155,71,57)", "M 96.9 1519 L 99.15 1519 L 101.42 1640.4 C 100.2 1651.91 101.82 1667.08 100.55 1679.66 "
                       "L 99.16 1680.55 C 98.39 1672.21 98.9 1648.65 99.16 1639.44 Z"),           # pilaster edge line (6)
    (RED, "M 163.85 1520 L 188.4 1520 L 189.35 1551.44 L 191.89 1551.96 L 191.97 1576.05 L 163.9 1579.65 Z"),  # column (115)
    ("rgb(102,34,29)", "M 163.9 1579.65 L 191.97 1576.05 L 191.8 1578.59 L 163.9 1581.5 Z"),  # its shadow (166)
    (RED, "M 158.5 1582.1 L 163.9 1581.5 L 191.8 1578.59 L 191.34 1612.01 L 158.5 1611.6 Z"),  # plinth (167)
    (LIT, "M 140 1611.6 L 157.66 1611.6 L 158.2 1646 L 129.5 1660 Z"),          # lit step (56)
    ("rgb(177,115,98)", "M 157.66 1612.02 L 158.53 1611.11 L 160.89 1612.02 L 161.6 1638.4 "
                        "L 158.5 1639 L 158.17 1631.09 Z"),                                 # step side (57)
    (RED, "M 161.6 1638.4 L 179 1639.3 L 179 1640.9 L 161.6 1640 Z"),           # under the step (168|13)
]
POT_PATCH_FLOOR = 1680               # the patch stops at the soil line of the left pot
W, H = 1331, 2048


def svg(view_box, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
            f'preserveAspectRatio="none">\n{body}</svg>\n')


def bbox(path):
    """Bounds of a path from its points and control points (a little generous on curves)."""
    t = re.search(r"translate\(([-\d.]+),([-\d.]+)\)", path)
    tx, ty = map(float, t.groups()) if t else (0.0, 0.0)
    nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", re.search(r'\bd="([^"]*)"', path).group(1))))
    return min(nums[0::2]) + tx, min(nums[1::2]) + ty, max(nums[0::2]) + tx, max(nums[1::2]) + ty


def recolour(path, colour):
    return re.sub(r'fill="[^"]*"', f'fill="{colour}"', path)


def plant_box(paths, pot):
    boxes = [bbox(paths[i]) for i in pot["plant"]]
    return (min(b[0] for b in boxes) - 2, min(b[1] for b in boxes) - 2,
            max(b[2] for b in boxes) + 2, max(b[3] for b in boxes) + 2)


def plant_svg(paths, pot):
    """The plant on its own, masked by everything the picture paints over it."""
    ids = pot["plant"]
    x0, y0, x1, y1 = plant_box(paths, pot)
    def over(b):
        return b[0] < x1 and b[2] > x0 and b[1] < y1 and b[3] > y0
    order = [recolour(p, "#fff" if i in ids else "#000") for i, p in enumerate(paths)
             if i >= min(ids) and (i in ids or over(bbox(p)))]
    w, h = x1 - x0, y1 - y0
    body = (f'<defs><mask id="cut" maskUnits="userSpaceOnUse" x="{x0:g}" y="{y0:g}" width="{w:g}" height="{h:g}">\n'
            + "\n".join(order) + '\n</mask></defs>\n<g mask="url(#cut)">\n'
            + "\n".join(paths[i] for i in ids) + "\n</g>\n")
    return svg(f"{x0:g} {y0:g} {w:g} {h:g}", body)


def pot_patch(paths, pot):
    """POT_PATCH, shown only inside the plant's outline grown by 1.5 and above the soil line."""
    x0, y0, x1, y1 = plant_box(paths, pot)
    outline = "\n".join(recolour(paths[i], "#fff") for i in pot["plant"])
    return (f'<defs><mask id="pot-patch" maskUnits="userSpaceOnUse" x="{x0 - 10:g}" y="{y0 - 10:g}" '
            f'width="{x1 - x0 + 20:g}" height="{y1 - y0 + 20:g}">\n'
            f'<g stroke="#fff" stroke-width="3" stroke-linejoin="round">\n{outline}\n</g>\n'
            f'<rect x="{x0 - 10:g}" y="{POT_PATCH_FLOOR}" width="{x1 - x0 + 20:g}" height="{y1 - POT_PATCH_FLOOR + 10:g}" fill="#000"/>\n'
            '</mask></defs>\n<g mask="url(#pot-patch)">\n'
            + "".join(f'<path fill="{fill}" d="{d}"/>\n' for fill, d in POT_PATCH) + "</g>\n")


def main():
    paths = re.findall(r"<path\b[^>]*/>", SRC.read_text())
    tree = set(TREE)
    plants = {i for pot in POTS.values() for i in pot["plant"] + pot["sky"]}
    back = [p for i, p in enumerate(paths) if 0 < i < BACK_END and i not in plants]
    front = [p for i, p in enumerate(paths) if i >= BACK_END and i not in tree | plants | set(NOTCH_CENTRE)]
    patch = "".join(f'<path fill="{fill}" d="{d}"/>\n' for fill, d in LEAF_PATCH)
    blossom = f'<g transform="{NEW_BLOSSOM}">\n' + "\n".join(paths[i] for i in FLOWER) + "\n</g>"
    tree = [paths[i] for i in TREE if i not in EDGE_TIP]
    tree_paths = "\n".join([tree[0], patch + tree[1], *tree[2:], blossom])

    x, y, w, h = TREE_BOX
    tree_body = (f'<g transform="scale(-1,1)">\n{tree_paths}\n</g>\n'
                 f'{tree_paths}\n')
    out = {
        "bg_back.svg": svg(f"0 0 {W} {H}", "\n".join(back) + "\n"),
        "bg_tree.svg": svg(f"{x} {y} {w} {h}", tree_body),
        "bg_front.svg": svg(f"0 0 {W} {H}", "\n".join(front) + "\n" + pot_patch(paths, POTS["l"])),
        "bg_pots.svg": svg(f"0 0 {W} {H}", "".join(
            "".join(paths[i] + "\n" for i in pot["cover"])
            + "".join(f'<path fill="{fill}" d="{d}"/>\n' for fill, d in pot.get("patch", []))
            for pot in POTS.values())),
        "bg_flower.svg": svg(" ".join(map(str, FLOWER_BOX)),
                             "\n".join(paths[i] for i in FLOWER) + "\n"),
    }
    out.update({f"bg_plant_{k}.svg": plant_svg(paths, pot) for k, pot in POTS.items()})
    for name, text in out.items():
        (SRC.parent / name).write_text(text)
        print(f"wrote web/{name} ({len(text) // 1024} KB)")
    print(f"tree box in % of picture: left {x / W:.4%} top {y / H:.4%} "
          f"width {w / W:.4%} height {h / H:.4%}")
    for k, pot in POTS.items():
        x0, y0, x1, y1 = plant_box(paths, pot)
        (px, py), pw, ph = pot["pivot"], x1 - x0, y1 - y0
        print(f".plant.{k} {{ left: {x0 / W:.4%}; top: {y0 / H:.4%}; width: {pw / W:.4%}; height: {ph / H:.4%}; "
              f"transform-origin: {(px - x0) / pw:.2%} {(py - y0) / ph:.2%}; }}")


if __name__ == "__main__":
    main()
