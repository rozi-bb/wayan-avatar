#!/usr/bin/env python3
"""Split the courtyard background into layers the page can animate.

    python3 scripts/bg_layers.py

Reads web/bg_rumah.svg (one flat stack of vectorized paths, path 0 is the
sky rectangle) and writes three SVGs next to it:

  bg_back.svg   paths drawn before the tree (wall, floor, back of the bale)
  bg_tree.svg   the frangipani tree, cropped to TREE_BOX so it can sway
  bg_front.svg  everything drawn after the tree (gate, bale, pots)
  bg_flower.svg one blossom from the tree, for the blossoms that fall

The sky is left out: the page paints it as a colour and floats clouds over it.
The tree is cut by the left edge of the picture, so a mirrored copy is drawn
outside that edge; when the tree leans right, the mirror fills the sliver
instead of sky showing through.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "bg_rumah.svg"

TREE = [*range(137, 163), *range(198, 212), *range(322, 336), *range(337, 346),
        406, 474, 476, 477, 480, 481, 482, 483, 484]
BACK_END = 137                       # paths 1..136 sit behind the tree
TREE_BOX = (-120, 480, 540, 580)     # x, y, w, h in picture units
FLOWER = [323, 324, 325, 326, 327, 328, 329, 332]  # petals and centre, not the leaf bits between them
FLOWER_BOX = (60, 536, 92, 98)
W, H = 1331, 2048


def svg(view_box, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
            f'preserveAspectRatio="none">\n{body}</svg>\n')


def main():
    paths = re.findall(r"<path\b[^>]*/>", SRC.read_text())
    tree = set(TREE)
    back = [p for i, p in enumerate(paths) if 0 < i < BACK_END]
    front = [p for i, p in enumerate(paths) if i >= BACK_END and i not in tree]
    tree_paths = "\n".join(paths[i] for i in TREE)

    x, y, w, h = TREE_BOX
    tree_body = (f'<g transform="scale(-1,1)">\n{tree_paths}\n</g>\n'
                 f'{tree_paths}\n')
    out = {
        "bg_back.svg": svg(f"0 0 {W} {H}", "\n".join(back) + "\n"),
        "bg_tree.svg": svg(f"{x} {y} {w} {h}", tree_body),
        "bg_front.svg": svg(f"0 0 {W} {H}", "\n".join(front) + "\n"),
        "bg_flower.svg": svg(" ".join(map(str, FLOWER_BOX)),
                             "\n".join(paths[i] for i in FLOWER) + "\n"),
    }
    for name, text in out.items():
        (SRC.parent / name).write_text(text)
        print(f"wrote web/{name} ({len(text) // 1024} KB)")
    print(f"tree box in % of picture: left {x / W:.4%} top {y / H:.4%} "
          f"width {w / W:.4%} height {h / H:.4%}")


if __name__ == "__main__":
    main()
