#!/usr/bin/env python3
"""meikyu, round 3: planets.

Every step is a planet drawn as a 3D wireframe sphere (outline, equator, latitudes, meridians). The wireframe is
static art, layered ABOVE the planet's dot; the dot is the sphere's disc, filled. So a step that plays turns its
planet from wireframe to solid, with the wire lines still drawn over it as shading, and a step that doesn't play is
left as wire. Planets in front of their orbit's centre are bigger than those behind it, and order is back to front.

The phrase is a ringed planet: its ring cut into eight segments (dots 16..23). The segments behind the planet come
before its body in the artwork, the ones in front after, so the ring passes behind and in front of it in 3D.

  o1 system   a sun with two tilted orbits, A outside and B inside; the ringed planet stands off to the right
  o2 orrery   a big sun at the left edge with sixteen orbits sweeping right, one planet on each
  o3 binary   two suns, A's planets round the left, B's round the right; the ringed planet between them

Same ABI and player.cpp mapping as rounds 1 and 2.

    python3 orbits.py      → o*/<pose>.svg and board-orbits.png
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

import pages as P
import effects as E

HERE = Path(__file__).resolve().parent
W, H = 480, 220
WIRE, ORBIT, BODY, HOT, INK, SUN = "#7A7A7A", "#3C3C3C", "#BEBEBE", "#F0F0F0", "#000000", "#A4A4A4"


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def path(pts, stroke, w=1.0, fill="none", close=False):
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else "")
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}" stroke-linejoin="round" stroke-linecap="round"/>'


def ell(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=40):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def wire_sphere(cx, cy, r, color=WIRE, w=0.8, tilt=0.32):
    """static art: a sphere as lines, drawn over its disc. Back halves of latitudes are skipped (hidden-line)."""
    o = [path(ell(cx, cy, r, r, n=min(60, max(16, int(r * 2)))), color, w + 0.2, close=True)]
    n = min(40, max(8, int(r)))
    lats, mers = ((-0.55, 0.0, 0.55), (0.38, 0.8)) if r >= 11 else ((0.0,), (0.5,))   # small spheres get fewer lines
    for lat in lats:                                                      # latitudes: front halves only
        rr, yy = r * math.cos(lat * math.pi / 2), cy + r * math.sin(lat * math.pi / 2)
        o.append(path(ell(cx, yy, rr, rr * tilt, 0, math.pi, n), color, w))
    for m in mers:                                                        # meridians
        o.append(path(ell(cx, cy, r * m, r, n=n), color, w, close=True))
    o.append(path([(cx, cy - r), (cx, cy + r)], color, w))
    return o


def disc(cx, cy, r, lit, fill=BODY):
    """the dot: the planet's disc, drawn under its wireframe"""
    return [path(ell(cx, cy, r, r, n=min(60, max(16, int(r * 2)))), fill, 0.5, fill=fill, close=True)] if lit else []


def planet(cx, cy, r, lit, solid_back=True):
    o = [path(ell(cx, cy, r, r, n=min(60, max(16, int(r * 2)))), INK, 0.5, fill=INK, close=True)] if solid_back else []
    return o + disc(cx, cy, r, lit) + wire_sphere(cx, cy, r)


def ringed(cx, cy, r, p, ring=(1.9, 2.6), tilt=0.28):
    """the phrase planet. Segments k=0..7 run left to right across the front (k 0..3 front-left... see below)."""
    o = []
    r0, r1 = r * ring[0], r * ring[1]

    def segment(k):
        a0 = math.pi * k / 4 + 0.05                                       # eight segments round the ring
        a1 = a0 + math.pi / 4 - 0.1
        outer = ell(cx, cy, r1, r1 * tilt, a0, a1, 8)
        inner = ell(cx, cy, r0, r0 * tilt, a1, a0, 8)
        return outer + inner, (a0 + a1) / 2

    segs = [segment(k) for k in range(8)]
    # order the phrase so tone 1 is front-left and it runs round the front to the right, then round the back
    order = [3, 2, 1, 0, 7, 6, 5, 4]
    back = [(order.index(k), pts) for k, (pts, mid) in enumerate(segs) if math.sin(mid) < 0]
    front = [(order.index(k), pts) for k, (pts, mid) in enumerate(segs) if math.sin(mid) >= 0]
    for tone, pts in back:
        o.append(path(pts, ORBIT, 0.8, close=True))
        if p.tone_lit(tone):
            o.append(path(pts, HOT, 0.5, fill=HOT, close=True))
    o += planet(cx, cy, r, False)
    for tone, pts in front:
        o.append(path(pts, ORBIT, 0.8, close=True))
        if p.tone_lit(tone):
            o.append(path(pts, HOT, 0.5, fill=HOT, close=True))
    return o


def place(cx, cy, rx, ry, a, base):
    """a planet on an orbit at angle a: position and a size that grows toward the front (bottom of the ellipse)"""
    return cx + rx * math.cos(a), cy + ry * math.sin(a), base * (0.72 + 0.28 * (math.sin(a) + 1) / 2)


def system_art(p, planets, orbits, suns, extra):
    """draw orbits' back halves, then everything by depth (y), then orbits' front halves under the planets in front"""
    o = []
    for cx, cy, rx, ry in orbits:
        o.append(path(ell(cx, cy, rx, ry, math.pi, 2 * math.pi), ORBIT, 1.0))
    items = [(y, "sun", (x, y, r)) for x, y, r in suns] + [(y, "planet", (x, y, r, i)) for x, y, r, i in planets]
    front_done = False
    for y, kind, data in sorted(items, key=lambda t: t[0]):
        if not front_done and y > max(cy for _, cy, _, _ in orbits):
            for cx, cy, rx, ry in orbits:
                o.append(path(ell(cx, cy, rx, ry, 0, math.pi), ORBIT, 1.0))
            front_done = True
        if kind == "sun":
            x, yy, r = data
            o.append(path(ell(x, yy, r, r, n=48), SUN, 1.4, fill=INK, close=True))
            o += wire_sphere(x, yy, r, SUN, 0.9)
        else:
            x, yy, r, i = data
            o += planet(x, yy, r, p.step_lit(i))
    if not front_done:
        for cx, cy, rx, ry in orbits:
            o.append(path(ell(cx, cy, rx, ry, 0, math.pi), ORBIT, 1.0))
    return o + extra


# ---- o1 · system -------------------------------------------------------------------------------------------------------
def system(p):
    cx, cy = 168, 88
    orbits = [(cx, cy, 128, 40), (cx, cy, 74, 22)]
    planets = []
    for i in range(16):
        rx, ry = (128, 40) if i < 8 else (74, 22)
        k = i % 8
        a = math.pi / 2 + 2 * math.pi * (k + (0.5 if i >= 8 else 0)) / 8 + 0.2
        if abs(math.cos(a)) < 0.3 and math.sin(a) < 0:               # nothing directly behind the sun
            a += 0.5
        x, y, r = place(cx, cy, rx, ry, a, 12.0 if i < 8 else 8.5)
        planets.append((x, y, r, i))
    return system_art(p, planets, orbits, [(cx, cy, 20)], ringed(400, 86, 18, p, ring=(1.5, 2.3)))


# ---- o2 · orrery -------------------------------------------------------------------------------------------------------
def orrery(p):
    sx, sy = 34, 90
    orbits, planets = [], []
    for i in range(16):                                               # one orbit per step, A on the odd ones outward
        k = i // 2 if i < 8 else (i - 8) // 2
        n = (i % 8) * 2 + (0 if i < 8 else 1)
        rx = 58 + n * 21
        ry = rx * 0.2
        orbits.append((sx, sy, rx, ry))
        a = 0.35 + 0.42 * math.sin(n * 1.9)                           # near the front, scattered above and below
        a = a if n % 2 else -a
        x, y, r = place(sx, sy, rx, ry, a, 7.0 + 5.0 * math.sin(n * 0.7 + 0.4) ** 2)
        planets.append((x, y, r, i))
    art = []
    for cx, cy, rx, ry in orbits:
        art.append(path(ell(cx, cy, rx, ry, -0.75, 0.75, 20), ORBIT, 0.8))
    art.append(path(ell(sx, sy, 30, 30, n=48), SUN, 1.4, fill=INK, close=True))
    art += wire_sphere(sx, sy, 30, SUN, 0.9)
    for x, y, r, i in sorted(planets, key=lambda t: t[1]):
        art += planet(x, y, r, p.step_lit(i))
    return art + ringed(426, 124, 12, p, ring=(1.5, 2.3), tilt=0.3)


# ---- o3 · binary -------------------------------------------------------------------------------------------------------
def binary(p):
    l, r_ = (118, 86), (362, 86)
    orbits = [(l[0], l[1], 82, 28), (r_[0], r_[1], 82, 28)]
    planets = []
    for i in range(16):
        cx, cy = l if i < 8 else r_
        k = i % 8
        a = 2 * math.pi * (k + 0.5) / 8 + (0.25 if i < 8 else -0.25)
        if abs(math.cos(a)) < 0.3 and math.sin(a) < 0:
            a += 0.45
        x, y, r = place(cx, cy, 82, 28, a, 11.0)
        planets.append((x, y, r, i))
    return system_art(p, planets, orbits, [(l[0], l[1], 16), (r_[0], r_[1], 16)], ringed(240, 60, 13, p, ring=(1.5, 2.4)))


STYLES = {"o1-system": system, "o2-orrery": orrery, "o3-binary": binary}


def main():
    ps = E.poses()
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, p in ps.items():
            (d / f"{pose}.svg").write_text(P.frame(p, fn(p)), encoding="utf-8")
    pad = 8
    sheet = Image.new("RGB", (pad + len(ps) * (W + pad), pad + 18 + len(STYLES) * (H + pad)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for j, pose in enumerate(ps):
            dr.text((pad + j * (W + pad), pad), pose, fill=(200, 200, 200))
        for i, name in enumerate(STYLES):
            for j, pose in enumerate(ps):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (pad + j * (W + pad), pad + 18 + i * (H + pad)))
    sheet.save(HERE / "board-orbits.png")
    print("wrote", len(STYLES) * len(ps), "frames")


if __name__ == "__main__":
    main()
