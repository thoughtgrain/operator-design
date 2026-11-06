#!/usr/bin/env python3
"""Eddy v1, cleaned rest frame (owner pick). Helpers and drawing copied from ../sketch.py; writes clean.svg beside this file.

    python3 screens/eddy/passes/01-subject/v1/clean.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G = {  # stock greys
    "k": "#000000", "g1": "#323232", "g2": "#4B4B4B", "g3": "#646464",
    "g4": "#7D7D7D", "g5": "#969696", "g6": "#AFAFAF", "hi": "#CDCDCD",
}
DEFAULTS = {"spin": 0.25, "flutter": 0.0, "depth": 0.5, "mix": 1.0}
HEADER = [("spin", "0.82"), ("flutter", "0"), ("depth", "50"), ("mix", "100")]
FONT = 'font-family="UniversNextPro-Light"'


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- primitives

def ribbon(pts, w, colour):
    """A polyline as a filled closed ribbon of width w (no out-and-back strokes)."""
    n = len(pts)
    assert 2 <= n <= 32, n
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
            bx, by = pts[i + 1][0] - x, pts[i + 1][1] - y
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            dx, dy = ax / la + bx / lb, ay / la + by / lb
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    ring = left + right[::-1]
    d = "M " + " L ".join(f"{f(a)} {f(b)}" for a, b in ring) + " Z"
    return f'<path d="{d}" fill="{colour}" stroke="none" stroke-width="0"/>'


def poly(pts, fill, stroke="none", sw=0):
    d = "M " + " L ".join(f"{f(a)} {f(b)}" for a, b in pts) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>'


def circle(cx, cy, r, stroke, sw, fill="none"):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>'


def rect(x, y, w, h, fill):
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="none" stroke-width="0"/>'


def text(x, y, s, colour=G["g4"], size=10):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{colour}" stroke="none" '
            f'{FONT} font-size="{size}px">{s}</text>')


def arc(cx, cy, r, a0, a1, n=24, ry=None, wobble=None):
    ry = r if ry is None else ry
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        k = 1 + (wobble(a) if wobble else 0)
        out.append((cx + r * k * math.cos(a), cy + ry * k * math.sin(a)))
    return out


def frame(body: list[str], title: str) -> str:
    hdr = []
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    for i, c in enumerate(steps):
        hdr.append(rect(60 * i, 0, 60, 20, c))
    for i, (t, v) in enumerate(HEADER):
        col = "#CBCBCB" if i < 2 else "#000000"
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" {FONT} font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" {FONT} font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f"  <title>{title}</title>",
        '  <g id="preview_canvas">', "    " + rect(0, 0, W, H, "#000000"), "  </g>",
        '  <g id="preview_header">', *("    " + h for h in hdr), "  </g>",
        '  <g id="art">', *("    " + b for b in body), "  </g>",
        "</svg>", ""])

# ---------------------------------------------------------------- v1  P1 / oscilloscope trace
def v1_clean(p=DEFAULTS):
    """Plan section through the horn chamber, drawn by a scope beam: the twin horn is the bright
    trace, its persistence trail fades behind each mouth, and the cabinet wall is a graticule."""
    b = []
    cx, cy = 240, 118
    # graticule: centre axes with minor ticks, scope style, kept to the chamber
    b.append(ribbon([(124, cy), (356, cy)], 1, G["g1"]))
    b.append(ribbon([(cx, 26), (cx, 210)], 1, G["g1"]))
    for i in range(-14, 15):
        if i == 0:
            continue
        x = cx + i * 8
        if 124 < x < 356:
            b.append(rect(x - 0.5, cy - 2, 1, 4, G["g2"]))
    for i in range(-11, 12):
        if i == 0:
            continue
        y = cy + i * 8
        if 28 < y < 208:
            b.append(rect(cx - 2, y - 0.5, 4, 1, G["g2"]))
    # chamber wall: the rotor's sweep circle, and the drum rotor below it (hidden, lower grey)
    R = 88
    b.append(circle(cx, cy, R, G["g3"], 1.5))
    # horn: length scales with depth (radius sets the doppler)
    L = 36 + 50 * p["depth"]          # 61 px at default
    ang = math.radians(-24)
    # persistence trail: spin sets how much of the turn the beam still shows behind each mouth
    sweep = math.radians(20 + 260 * p["spin"])
    rnd = random.Random(7)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    wob = (lambda a: p["flutter"] * 0.12 * sum(math.sin(3 * (k + 2) * a + ph[k]) for k in range(3)) / 3)
    for side in (0, math.pi):
        a_end = ang + side
        n = 4
        for k in range(n):  # trail split into segments that fade with age
            s0 = a_end - sweep * (k + 1) / n
            s1 = a_end - sweep * k / n - 0.03
            col = [G["g6"], G["g5"], G["g4"], G["g3"]][k]
            b.append(ribbon(arc(cx, cy, L + 9, s0, s1, n=12, wobble=wob), 1.5, col))
    # ghost horns (mix: count of wet ghosts the trace leaves; 2 at mix 100 here)
    for g in range(int(round(2 * p["mix"]))):
        ga = ang - math.radians(32) * (g + 1)
        gx, gy = math.cos(ga), math.sin(ga)
        b.append(ribbon([(cx - gx * L * 0.92, cy - gy * L * 0.92), (cx + gx * L * 0.92, cy + gy * L * 0.92)], 1,
                        [G["g3"], G["g2"]][g]))
    # the horn itself: one closed bright outline, flared mouths both ends
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    prof = [(-L, 9), (-L + 9, 3), (-8, 2.2), (8, 2.2), (L - 9, 3), (L, 9)]
    top = [(cx + ux * s + nx * h, cy + uy * s + ny * h) for s, h in prof]
    bot = [(cx + ux * s - nx * h, cy + uy * s - ny * h) for s, h in prof][::-1]
    b.append(poly(top + bot, G["k"], G["hi"], 2))
    b.append(circle(cx, cy, 5, G["hi"], 2, fill=G["k"]))
    return frame(b, "eddy v1 · clean · oscilloscope trace")




if __name__ == "__main__":
    out = HERE / "clean.svg"
    out.write_text(v1_clean(), encoding="utf-8")
    print(out)
