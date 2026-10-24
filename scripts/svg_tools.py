"""Shared SVG helpers for the head and udeng rig scripts.

Reads path outlines from the master SVGs (svg_paths), turns an absolute M/L/C/Z
path into dense points (polyline), evens them out (resample), writes them back as
Rive commands (commands), and snaps a fill to the rig's palette (colour).
Positions are in the master's SVG units; HEAD_POS is where the HeadLook group sits.
"""

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD_POS = (690.0, 990.0)  # HeadLook's origin, SVG units
PALETTE = {
    "#ffefab81": (239, 171, 129), "#ffd69067": (214, 144, 103), "#ffededec": (237, 237, 236),
    "#ffd3d2d2": (211, 210, 210), "#fff5bf03": (245, 191, 3), "#ffe9a601": (233, 166, 1),
    "#ffc87915": (200, 121, 21), "#ff3f3e3f": (63, 62, 63),
}


def svg_paths(file):
    out = []
    for attrs in re.findall(r"<path([^>]*)>", (ROOT / file).read_text()):
        fill = tuple(map(int, re.search(r'fill="rgb\((\d+),\s*(\d+),\s*(\d+)\)"', attrs).groups()))
        out.append((fill, re.search(r'd="([^"]+)"', attrs).group(1)))
    return out


def polyline(d, step=2.0):
    """Dense points along an absolute M/L/C/Z path."""
    tokens = re.findall(r"[MLCZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pts, i, cur = [], 0, None
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t in "Zz":
            continue
        n = {"M": 2, "L": 2, "C": 6}[t]
        while i < len(tokens) and tokens[i] not in "MLCZz":
            a = list(map(float, tokens[i:i + n]))
            i += n
            if t == "M":
                cur = (a[0], a[1])
                pts.append(cur)
                t = "L"
            elif t == "L":
                seg = math.dist(cur, (a[0], a[1]))
                k = max(1, int(seg / step))
                pts += [(cur[0] + (a[0] - cur[0]) * j / k, cur[1] + (a[1] - cur[1]) * j / k) for j in range(1, k + 1)]
                cur = (a[0], a[1])
            else:
                p0, p1, p2, p3 = cur, (a[0], a[1]), (a[2], a[3]), (a[4], a[5])
                approx = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
                k = max(2, int(approx / step))
                for j in range(1, k + 1):
                    s = j / k
                    u = 1 - s
                    pts.append((u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0],
                                u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1]))
                cur = p3
    return pts


def area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


def resample(pts, n):
    """n points evenly spaced along the closed outline, clockwise on screen, from the topmost point."""
    if area(pts) < 0:
        pts = pts[::-1]
    top = min(range(len(pts)), key=lambda i: (pts[i][1], pts[i][0]))
    pts = pts[top:] + pts[:top]
    ring = pts + pts[:1]
    seg = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    total = sum(seg)
    out, acc, j = [], 0.0, 0
    for k in range(n):
        target = total * k / n
        while acc + seg[j] < target:
            acc += seg[j]
            j += 1
        f = (target - acc) / seg[j] if seg[j] else 0
        out.append((ring[j][0] + (ring[j + 1][0] - ring[j][0]) * f, ring[j][1] + (ring[j + 1][1] - ring[j][1]) * f))
    return out


def commands(pts):
    """Closed Catmull-Rom curve through pts as Rive commands, in HeadLook units."""
    n = len(pts)
    loc = [(x - HEAD_POS[0], y - HEAD_POS[1]) for x, y in pts]
    tan = [((loc[(i + 1) % n][0] - loc[i - 1][0]) / 6, (loc[(i + 1) % n][1] - loc[i - 1][1]) / 6) for i in range(n)]
    cmds = [{"commandType": "moveTo", "x": round(loc[0][0], 2), "y": round(loc[0][1], 2)}]
    for i in range(n):
        j = (i + 1) % n
        cmds.append({"commandType": "cubicTo",
                     "control1X": round(loc[i][0] + tan[i][0], 2), "control1Y": round(loc[i][1] + tan[i][1], 2),
                     "control2X": round(loc[j][0] - tan[j][0], 2), "control2Y": round(loc[j][1] - tan[j][1], 2),
                     "endX": round(loc[j][0], 2), "endY": round(loc[j][1], 2)})
    cmds.append({"commandType": "close"})
    return cmds


def colour(fill):
    return min(PALETTE, key=lambda c: sum((PALETTE[c][k] - fill[k]) ** 2 for k in range(3)))
