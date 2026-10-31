#!/usr/bin/env python3
"""Toro round 6: five new bull concepts, one head model (bullhead.py), five ways of drawing it.

  b1 survey     the head as a topographic map: contour lines in the CRT language; fold adds terraces
  b2 signal     the head pushed up through scanlines of toro's own waveform (the round-4 model)
  b3 origami    the head folded from flat facets, lit by the filter; fold adds creases
  b4 cut paper  the head as stacked paper layers in the stepped greys, each casting a hard shadow
  b5 print      the head as an amplitude-modulated halftone; cutoff moves the light

Every concept: spread sweeps the horns out, shape curls the tips, a note lowers the head to charge.

    python3 screens/toro/concepts/bulls.py
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import gen_frames as g  # noqa: E402
import bullhead as bh  # noqa: E402
from character import toro_wave  # noqa: E402

G, f, poly, dot, grey = g.G, g.f, g.poly, g.dot, g.grey
S, OX, OY = 1.12, 240, 142


def kink(a):
    return 0.4 * a + 0.6 * a ** 3


def place(x, y, playing=False, v=None):
    """head units → screen; a note lowers and tips the head forward (the charge)"""
    z = 1.07 if playing else 1.0                                   # the charge: the head comes at you and drops
    return OX + x * S * z, OY + y * S * z + (5 if playing else 0)


def shape(pts, color, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{color}" stroke="none"/>'


def stroke(pts, color, w, close=False):
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + (" Z" if close else "")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>'


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + g.header(v) + ["</svg>"])


def thin(pts, gap=1.6):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) >= gap:
            out.append(p)
    return out


def nose_ring(v, n=24):
    """res: the ring swings bigger; it hangs from the nostrils (head units)"""
    r = 5 + 5 * v["res"]
    return [(math.cos(a) * r, 47 + r + math.sin(a) * r) for a in [k * 2 * math.pi / n for k in range(n)]], r


def relief(v):
    return bh.Relief(spread=v["spread"], curl=v["shape"])


def fit64(pts, cap=62):
    """Douglas–Peucker until the outline fits the SDK's 64-point path limit"""
    from skimage.measure import approximate_polygon
    arr = np.array(pts)
    tol = 0.3
    while True:
        simp = approximate_polygon(arr, tol)
        if len(simp) <= cap:
            out = [tuple(p) for p in simp]
            return out[:-1] if len(out) > 2 and math.dist(out[0], out[-1]) < 0.5 else out
        tol *= 1.3


def contours(r, level):
    from skimage.measure import find_contours
    out = []
    for c in find_contours(r.h, level):
        pts = [(r.X[0, 0] + j * r.step, r.Y[0, 0] + i * r.step) for i, j in c]
        if len(pts) > 6:
            out.append(fit64(pts))
    return out


# b1 · survey ----------------------------------------------------------------------------------------------------------
def survey(v, playing=False):
    r = relief(v)
    o = []
    n = 5 + round(11 * v["fold"])                                  # fold = how many terraces the head is cut into
    top = float(r.h.max())
    lit = v["cutoff"]
    rnd = random.Random(1)
    ring = round((n - 1) * v["res"])
    jit = kink(v["aphx"])
    for k in range(n):
        lev = top * (k + 0.6) / (n + 0.4)
        u = k / max(1, n - 1)
        level = 2 + 5 * min(1.0, max(0.0, (lit + 0.12 - u) * 3))       # cutoff: how far up the head the light climbs
        if playing:
            level = min(7, level + 1)
        if v["res"] > 0.05 and k == ring:
            level = 7
        dx = jit * 6 * (rnd.random() - 0.5)
        for c in contours(r, lev):
            pts = [place(x + dx + v["noise"] * 1.6 * (rnd.random() - 0.5), y, playing) for x, y in c]
            o.append(stroke(pts, grey(min(7, level) / 7), 1.2 + 1.0 * v["drive"] + (0.4 if k == n - 1 else 0), close=True))
    ring, _ = nose_ring(v)
    o.append(stroke([place(*p, playing) for p in ring], G[7], 1.6, close=True))
    return frame(v, o)


# b2 · signal ----------------------------------------------------------------------------------------------------------
def signal(v, playing=False):
    """cross-contour: horizontal lines run across the bull only, lifted by its relief; toro's waveform rides them"""
    r = relief(v)
    o = []
    amp = 10 + 16 * v["fold"]
    o.append(stroke([place(*p, playing) for p in bh.outline()], G[2], 1.2, close=True))      # the silhouette, faint
    for sd in (-1, 1):
        o.append(stroke([place(*p, playing) for p in bh.horn(sd, v["spread"], v["shape"])], G[4], 1.2, close=True))
    for idx, y in enumerate(np.arange(-96, 62, 4.5)):
        w = toro_wave(v, n=96, cycles=4, phase=idx * 0.11, key=idx if v["aphx"] > 0 else 0)
        seg = []
        segs = []
        for k in range(96):
            x = -100 + 200 * k / 95
            hh = r.at(x, y)
            if hh > 0.02:
                ripple = (0.3 + 1.6 * v["cutoff"]) * w[k]                   # toro's wave, louder as the filter opens
                seg.append(place(x, y - amp * hh - ripple * hh, playing))
            elif seg:
                segs.append(seg); seg = []
        if seg:
            segs.append(seg)
        for sg in segs:
            if len(sg) < 2:
                continue
            o.append(shape(sg + [(sg[-1][0], sg[-1][1] + 6), (sg[0][0], sg[0][1] + 6)], G[0]))
            level = 3 + round(4 * min(1.0, 0.25 + 0.75 * v["cutoff"] + (0.15 if playing else 0)) * (0.6 + 0.4 * (idx % 2 == 0)))
            o.append(stroke(sg, grey(min(7, level) / 7), 1.4 + 0.8 * v["drive"]))
    return frame(v, o)


# b3 · origami ---------------------------------------------------------------------------------------------------------
def origami(v, playing=False):
    from scipy.spatial import Delaunay
    r = relief(v)
    o = []
    rnd = random.Random(7)
    step = 13 - 6 * v["fold"]                                      # fold = more creases
    pts = []
    for y in np.arange(-95, 62, step):
        for x in np.arange(-100, 101, step):
            jx, jy = x + rnd.uniform(-0.3, 0.3) * step, y + rnd.uniform(-0.3, 0.3) * step
            if r.at(jx, jy) > 0.05:
                pts.append((jx, jy))
    ol = bh.outline()
    for a, b in zip(ol, ol[1:] + ol[:1]):                          # keep the silhouette crisp
        for t in np.linspace(0, 1, max(2, int(math.dist(a, b) / step) + 1))[:-1]:
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    for sd in (-1, 1):
        sp = bh.horn_spine(sd, v["spread"], v["shape"], n=10)
        poly_h = bh.tube(sp, bh.horn_widths(10))
        pts += poly_h
    light = (-0.5 - 0.6 * (v["cutoff"] - 0.5), -0.7, 0.35 + 0.8 * v["cutoff"])   # cutoff raises the light
    shade = r.normal_light(light, k=30)
    tri = Delaunay(np.array(pts))
    for s in tri.simplices:
        a, b, c = (pts[i] for i in s)
        cx, cy = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
        i = int(round((cy - r.Y[0, 0]) / r.step)); j = int(round((cx - r.X[0, 0]) / r.step))
        if not (0 <= i < r.h.shape[0] and 0 <= j < r.h.shape[1]) or not r.mask[i, j]:
            continue
        lum = shade[i, j]
        level = 1 + round(6 * lum * (1.1 if playing else 1))
        o.append(shape([place(*a, playing), place(*b, playing), place(*c, playing)], G[max(1, min(7, level))]))
    ring, rr = nose_ring(v, 8)                                     # a faceted ring: octagon, lit top and shaded bottom
    for k in range(8):
        a, b = ring[k], ring[(k + 1) % 8]
        cx, cy = 0, 47 + rr
        ia = [(cx + (p[0] - cx) * 0.62, cy + (p[1] - cy) * 0.62) for p in (b, a)]
        o.append(shape([place(*p, playing) for p in (a, b, *ia)], G[7 if k >= 4 else 4]))
    return frame(v, o)


# b4 · cut paper -------------------------------------------------------------------------------------------------------
def cutpaper(v, playing=False):
    r = relief(v)
    o = []
    n = 4 + round(4 * v["fold"])
    top = float(r.h.max())
    off = 2.0 + 1.5 * v["drive"]                                    # drive: thicker card, deeper shadows
    for k in range(n):
        lev = top * (k + 0.15) / (n + 0.2)
        level = 1 + round((1.5 + 4.5 * v["cutoff"]) * (k + 1) / n)    # cutoff: how much light reaches the top layers
        for c in contours(r, lev):
            pts = [place(x, y, playing) for x, y in c]
            o.append(shape([(x + off, y + off) for x, y in pts], G[0]))     # hard shadow
            o.append(shape(pts, G[min(7, level)]))
    ring, rr = nose_ring(v)
    inner = [(p[0] * 0.7, 47 + rr + (p[1] - 47 - rr) * 0.7) for p in ring]
    for dx, col in ((2.0 + 1.5 * v["drive"], G[0]), (0, G[7])):
        o.append(shape([(x + dx, y + dx) for x, y in [place(*p, playing) for p in ring + [ring[0]] + [inner[0]] + inner[::-1]]], col))
    return frame(v, o)


# b5 · print -----------------------------------------------------------------------------------------------------------
def halftone(v, playing=False):
    r = relief(v)
    o = []
    light = (-0.9 + 1.8 * v["cutoff"], -0.6, 0.5)                   # cutoff swings the light across the face
    shade = r.normal_light(light, k=28)
    step = 4.2
    for jy, y in enumerate(np.arange(-96, 62, step * 0.87)):
        for x in np.arange(-104, 104, step):
            xx = x + (step / 2 if jy % 2 else 0)
            i = int(round((y - r.Y[0, 0]) / r.step)); j = int(round((xx - r.X[0, 0]) / r.step))
            if not (0 <= i < r.h.shape[0] and 0 <= j < r.h.shape[1]) or not r.mask[i, j]:
                continue
            tone = (0.3 + 0.7 * shade[i, j]) * (1.1 if playing else 1)
            rad = 0.4 + 2.2 * min(1.0, tone)
            if rad < 0.8:
                continue
            o.append(shape(dot(rad, 10), G[7] if tone > 0.8 else G[6] if tone > 0.5 else G[5], *place(xx, y, playing)))
    ring, _ = nose_ring(v, 14)
    for p in ring:
        o.append(shape(dot(1.6, 8), G[7], *place(*p, playing)))
    return frame(v, o)


STYLES = {"b1-survey": survey, "b2-signal": signal, "b3-origami": origami, "b4-cutpaper": cutpaper, "b5-print": halftone}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "spread-100": (dict(D, spread=1, shape=0.6), False), "cutoff-000": (dict(D, cutoff=0), False),
             "cutoff-100": (dict(D, cutoff=1), False), "fold-100": (dict(D, fold=1), False), "playing": (D, True)}
    only = sys.argv[1:] or list(STYLES)
    for name in only:
        fn = STYLES[name]
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(only) * len(poses), "frames")


if __name__ == "__main__":
    main()
