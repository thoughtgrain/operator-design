#!/usr/bin/env python3
"""Subject pass 01 for eddy: five rest-frame sketches, one per direction.

v1  P1  Section drawing   / oscilloscope trace
v2  P2  Diagram + trace   / typeset diagram
v3  P3  Trace as subject  / orthographic elevation
v4  P4  Stack in depth    / survey plan
v5  P12 Orrery (stretch)  / patent section

All controls at their defaults (spin 0.25 -> 0.82 Hz, flutter 0, depth 50 %, mix 100 %), no audio.
Sketches only: nothing is bound yet, so lines are filled closed ribbons and circles.

    python3 screens/eddy/passes/01-subject/sketch.py
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
def v1(p=DEFAULTS):
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
    b.append(text(366, 206, "rotor 0.82 hz", G["g4"]))
    return frame(b, "eddy v1 · P1 section · oscilloscope trace")


# ---------------------------------------------------------------- v2  P2 / typeset diagram
def v2(p=DEFAULTS):
    """Left: the signal path typeset as a diagram (in, rotor, eddies feeding its speed, a dry/wet
    vane). Right: what a steady tone sounds like after it, the doppler squeezing its cycles."""
    b = []
    # --- left: diagram (spin, flutter)
    y0 = 100
    b.append(text(12, y0 - 6, "in", G["g5"]))
    b.append(ribbon([(12, y0), (78, y0)], 1, G["g4"]))
    rc = (116, y0)
    b.append(circle(*rc, 34, G["g5"], 1.5))
    # spin: speed ticks round the rotor, count rises with spin (5 at default)
    nt = int(round(3 + 21 * p["spin"]))
    for i in range(nt):
        a = -math.pi / 2 + 2 * math.pi * i / nt
        b.append(ribbon([(rc[0] + 38 * math.cos(a), rc[1] + 38 * math.sin(a)),
                         (rc[0] + 44 * math.cos(a), rc[1] + 44 * math.sin(a))], 1, G["g4"]))
    ha = math.radians(-30)
    b.append(ribbon([(rc[0] - 24 * math.cos(ha), rc[1] - 24 * math.sin(ha)),
                     (rc[0] + 24 * math.cos(ha), rc[1] + 24 * math.sin(ha))], 1.5, G["g5"]))
    b.append(text(98, y0 - 50, "rotor", G["g4"]))
    # flutter: eddy line feeding the rotor's speed from below; flat at 0
    pts = []
    for i in range(24):
        x = 40 + i * 76 / 23 * 1.0
        amp = 2 + 14 * p["flutter"]
        pts.append((x, 182 + amp * math.sin(i * 1.3) * math.sin(i * 0.37 + 1)))
    pts.append((118, 182))
    b.append(ribbon(pts, 1, G["g4"]))
    b.append(ribbon([(116, 180), (116, 138)], 1, G["g4"]))
    b.append(text(40, 200, "eddies", G["g4"]))
    # out to the sum node, dry branch around the rotor
    b.append(ribbon([(150, y0), (196, y0)], 1, G["g4"]))
    b.append(ribbon([(40, y0), (40, 50), (196, 50), (196, 92)], 1, G["g3"]))
    b.append(text(150, 46, "dry", G["g4"]))
    b.append(text(158, 116, "wet", G["g4"]))
    # mix: a vane at the sum node rotates from the dry contact (up) to the wet (left)
    sx, sy = 204, y0
    va = math.radians(-90 + 90 * p["mix"]) + math.pi
    b.append(ribbon([(sx, sy), (sx + 14 * math.cos(va), sy + 14 * math.sin(va))], 1.5, G["g5"]))
    b.append(circle(sx, sy, 2.5, G["g5"], 1.5, fill=G["k"]))
    b.append(ribbon([(208, y0), (232, y0)], 1, G["g4"]))
    # --- right: trace (depth, and mix shown in its dry ghost)
    x0, x1, ym = 250, 470, 112
    b.append(ribbon([(x0, ym), (x1, ym)], 1, G["g1"]))
    b.append(rect(x0, 40, 1, 144, G["g2"]))
    b.append(text(x0 + 4, 200, "out", G["g4"]))

    def tone(dev):
        out, ph = [], 0.0
        for i in range(32):
            x = x0 + (x1 - x0) * i / 31
            t = i / 31
            freq = 3.2 * (1 + dev * math.sin(2 * math.pi * 1.5 * t))
            ph += 2 * math.pi * freq / 31
            amp = 42 * (1 + 0.25 * dev * math.cos(2 * math.pi * 1.5 * t))
            out.append((x, ym - amp * math.sin(ph)))
        return out
    b.append(ribbon(tone(0.0), 1, G["g3"]))
    b.append(ribbon(tone(0.9 * p["depth"]), 2, G["hi"]))
    return frame(b, "eddy v2 · P2 diagram + trace · typeset diagram")


# ---------------------------------------------------------------- v3  P3 / orthographic elevation
def v3(p=DEFAULTS):
    """The horn mouth's path through time is a helix; draw it in elevation (front runs bright,
    back runs as hidden lines) beside its end view, with projection lines between them."""
    b = []
    ex, ey, er = 44, 118, 18 + 40 * p["depth"]       # end view (rotor seen down the time axis)
    x0, x1 = 96, 470
    # projection lines from the end view's extremes into the elevation
    for yy in (ey - er, ey + er):
        b.append(ribbon([(ex, yy), (x1, yy)], 1, G["g1"]))
    b.append(ribbon([(x0 - 8, ey), (x1, ey)], 1, G["g2"]))                 # axis
    b.append(circle(ex, ey, er, G["g4"], 1.5))
    b.append(circle(ex, ey, 3, G["g4"], 1.5))
    a = math.radians(-60)
    b.append(ribbon([(ex, ey), (ex + er * math.cos(a), ey + er * math.sin(a))], 1.5, G["g5"]))
    b.append(text(ex - 22, ey + er + 18, "end", G["g4"]))
    b.append(text(x0, 206, "elevation", G["g4"]))
    # helix: cycles across the width set by spin; flutter jitters the pitch; mix crossfades from
    # the axis (dry, left) into the full helix
    cycles = 1 + 11 * p["spin"]                 # 3.75 at default
    rnd = random.Random(3)
    jit = [rnd.uniform(-1, 1) for _ in range(40)]
    fade_x = x1 - (x1 - x0) * p["mix"]
    def theta(x):
        t = (x - x0) / (x1 - x0)
        base = 2 * math.pi * cycles * t
        k = int(t * 39)
        return base + p["flutter"] * 1.2 * jit[k]
    # split into half-turn runs; front (cos > 0) bright, back as hidden line
    N = 400
    xs = [x0 + (x1 - x0) * i / N for i in range(N + 1)]
    runs, cur, front = [], [], None
    for x in xs:
        th = theta(x) + math.pi / 2
        fr = math.cos(th) > 0
        amp = er * min(1, max(0, (x - fade_x) / 40 + 0.0)) if p["mix"] < 1 else er
        pt = (x, ey - amp * math.sin(th))
        if front is None or fr == front:
            cur.append(pt)
        else:
            runs.append((front, cur)); cur = [cur[-1], pt]
        front = fr
    runs.append((front, cur))
    for fr, pts in runs:
        step = max(1, math.ceil(len(pts) / 30))
        sel = pts[::step]
        if sel[-1] != pts[-1]:
            sel.append(pts[-1])
        sel = sel[:32]
        if len(sel) < 2:
            continue
        b.append(ribbon(sel, 2 if fr else 1, G["hi"] if fr else G["g3"]))
    # dimension: helix radius (depth) at the right end
    dx = 474
    b.append(rect(dx - 0.5, ey - er, 1, 2 * er, G["g3"]))
    b.append(text(434, ey - er - 6, "r 50", G["g4"]))
    return frame(b, "eddy v3 · P3 trace as subject · orthographic elevation")


# ---------------------------------------------------------------- v4  P4 / survey plan
def v4(p=DEFAULTS):
    """Plan sheets of the rotor, one per past revolution, stacked back in time: on each the horn's
    bearing has moved on; the front sheet carries the throw lobe surveyed as contours."""
    b = []
    n = int(round(2 + 3 * p["mix"]))        # sheets shown: 5 at mix 100
    R = 46
    fx, fy = 150, 140                       # front sheet centre
    off = (40, -18)
    step = math.radians(25 + 140 * p["spin"])   # bearing advance per sheet (60 deg at default)
    rnd = random.Random(11)
    jit = [rnd.uniform(-1, 1) for _ in range(8)]
    bear0 = math.radians(-35)
    sheets = []
    for k in range(n):
        c = (fx + off[0] * k + p["flutter"] * 10 * jit[k], fy + off[1] * k + p["flutter"] * 6 * jit[k + 1])
        sheets.append((k, c, bear0 + step * k + p["flutter"] * 0.5 * jit[k]))
    for k, c, br in reversed(sheets):       # back to front, black fills hide what's behind
        front = k == 0
        col = G["g5"] if front else [G["g4"], G["g3"], G["g3"], G["g2"], G["g2"]][k]
        b.append(circle(*c, R, col, 1.5 if front else 1, fill=G["k"]))
        hx, hy = c[0] + (R - 6) * math.cos(br), c[1] + (R - 6) * math.sin(br)
        if not front:
            b.append(ribbon([c, (hx, hy)], 1, col))
            b.append(circle(hx, hy, 2.5, col, 1, fill=G["k"]))
    # front sheet: bearing ticks every 30 deg, the horn bearing, the throw lobe as two contours
    k, c, br = sheets[0]
    for i in range(12):
        a = 2 * math.pi * i / 12
        b.append(ribbon([(c[0] + (R - 5) * math.cos(a), c[1] + (R - 5) * math.sin(a)),
                         (c[0] + R * math.cos(a), c[1] + R * math.sin(a))], 1, G["g4"]))
    L = 30 + 60 * p["depth"]                # throw reach: depth (60 px at default)
    def lobe(scale):
        pts = []
        for i in range(30):
            t = -math.pi / 2 + math.pi * i / 29
            r = scale * L * math.cos(t) ** 1.6 if abs(t) < math.pi / 2 else 0
            w = 0.42 * math.sin(2 * t)
            pts.append((r, w * scale * L * 0.9))
        return pts
    ux, uy = math.cos(br), math.sin(br)
    def place(pts):
        return [(c[0] + ux * (R * 0.25 + x) - uy * y, c[1] + uy * (R * 0.25 + x) + ux * y) for x, y in pts]
    b.append(poly(place(lobe(1.0)), G["k"], G["g4"], 1))
    b.append(poly(place(lobe(0.6)), G["k"], G["hi"], 2))
    b.append(ribbon([c, (c[0] + ux * (R * 0.25), c[1] + uy * (R * 0.25))], 2, G["hi"]))
    b.append(circle(*c, 3, G["hi"], 2, fill=G["k"]))
    # survey furniture: sheet label, bearing, scale bar
    b.append(text(fx - 44, fy + R + 18, "rev 0", G["g4"]))
    b.append(text(fx + off[0] * (n - 1) + R + 6, fy + off[1] * (n - 1) + 4, f"rev -{n - 1}", G["g4"]))
    b.append(text(380, 160, "brg 325", G["g4"]))
    b.append(rect(380, 196, 60, 1, G["g4"]))
    for x in (380, 410, 440):
        b.append(rect(x - 0.5, 192, 1, 5, G["g4"]))
    b.append(text(380, 210, "0     1 m", G["g4"]))
    return frame(b, "eddy v4 · P4 stack in depth · survey plan")


# ---------------------------------------------------------------- v5  P12 / patent section
def v5(p=DEFAULTS):
    """The cabinet cut open like a patent drawing: one shaft, the horn rotor and drum rotor on two
    orbits round it, louvres in the walls, reference numerals on leaders."""
    b = []
    cx = 240
    # 3D model: orbits are circles in horizontal planes about the shaft; camera above, looking down 14 deg
    tilt = math.sin(math.radians(14))
    def proj(r, a, yplane):
        return (cx + r * math.cos(a), yplane + r * tilt * math.sin(a))
    up_y, lo_y = 74, 160
    Rh = 60 + 60 * p["depth"]               # horn orbit radius: depth (90 at default)
    Rd = 104
    # cabinet section: walls, top, base slab with section hatching
    b.append(ribbon([(70, 34), (410, 34)], 1.5, G["g3"]))
    b.append(ribbon([(70, 34), (70, 196)], 1.5, G["g3"]))
    b.append(ribbon([(410, 34), (410, 196)], 1.5, G["g3"]))
    b.append(ribbon([(70, 196), (410, 196)], 1.5, G["g3"]))
    b.append(ribbon([(70, 206), (410, 206)], 1.5, G["g3"]))
    b.append(ribbon([(70, 196), (70, 206)], 1, G["g3"]))
    b.append(ribbon([(410, 196), (410, 206)], 1, G["g3"]))
    for x in range(76, 404, 8):
        b.append(ribbon([(x, 205), (x + 6, 197)], 1, G["g2"]))
    # louvres in both walls: mix opens them (rotation, 70 deg open at mix 100)
    la = math.radians(10 + 60 * p["mix"])
    for wx, sgn in ((70, 1), (410, -1)):
        for i in range(5):
            y = 96 + i * 10
            hx, hy = 6 * math.cos(la), 6 * math.sin(la)
            b.append(ribbon([(wx - sgn * hx * 0.2, y - hy), (wx + sgn * hx, y + hy)], 1.5, G["g4"]))
    # shaft
    b.append(ribbon([(cx, 52), (cx, 196)], 2, G["g4"]))
    # orbits split at the shaft's depth: far half dim, near half brighter, drawn front over the shaft
    def orbit(r, yp, col_far, col_near, wob=None):
        far = [proj(r * (1 + (wob(a) if wob else 0)), a, yp) for a in [math.pi + math.pi * i / 31 for i in range(32)]]
        near = [proj(r * (1 + (wob(a) if wob else 0)), a, yp) for a in [math.pi * i / 31 for i in range(32)]]
        return ribbon(far, 1, col_far), ribbon(near, 1.5, col_near)
    rnd = random.Random(5)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    wob = lambda a: p["flutter"] * 0.14 * (math.sin(5 * a + ph[0]) + math.sin(9 * a + ph[1])) / 2
    lf, ln = orbit(Rd, lo_y, G["g2"], G["g3"], wob)
    uf, un = orbit(Rh, up_y, G["g2"], G["g3"])
    b += [lf, uf]
    # hubs
    b.append(circle(cx, up_y, 4, G["g5"], 1.5, fill=G["k"]))
    b.append(circle(cx, lo_y, 5, G["g5"], 1.5, fill=G["k"]))
    b += [ln, un]
    # spin: phantom positions of the horn along its orbit (count, 4 at default), drum lags behind
    ah = math.radians(60)
    nph = int(round(1 + 12 * p["spin"]))
    for i in range(nph, 0, -1):
        a = ah - math.radians(14) * i
        x, y = proj(Rh, a, up_y)
        b.append(circle(x, y, 4, G["g3"], 1, fill=G["k"]))
    # horn arm from the hub to the mouth, mouth bright
    hx, hy = proj(Rh, ah, up_y)
    b.append(ribbon([(cx, up_y), (hx, hy)], 1.5, G["g5"]))
    b.append(circle(hx, hy, 7, G["hi"], 2, fill=G["k"]))
    ad = math.radians(150)
    dx, dy = proj(Rd, ad, lo_y)
    b.append(ribbon([(cx, lo_y), (dx, dy)], 1.5, G["g4"]))
    b.append(circle(dx, dy, 9, G["g5"], 1.5, fill=G["k"]))
    # reference numerals on leaders
    def num(n, tx, ty, lx, ly, px, py):
        b.append(ribbon([(lx, ly), (px, py)], 1, G["g3"]))
        b.append(text(tx, ty, n, G["g4"]))
    num("10", 436, 58, 434, 54, hx + 6, hy - 4)
    num("12", 38, 190, 52, 184, dx - 6, dy + 6)
    num("14", 256, 46, 254, 44, cx + 3, 60)
    num("16", 436, 122, 434, 118, 412, 120)
    return frame(b, "eddy v5 · P12 orrery (stretch) · patent section")


if __name__ == "__main__":
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn(), encoding="utf-8")
        print(out)
