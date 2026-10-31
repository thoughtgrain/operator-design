#!/usr/bin/env python3
"""Concept sketches for toro's reset (screens/toro/concepts.md): 1 spectrum bull, 2 patent mechanical bull,
4 rock-art aurochs. Each draws rest, cutoff 0, cutoff 100, fold 100 and playing at 1:1.

Sketches follow opxy/craft.md (one drawing language, three line weights, one bright subject) but haven't
been through the gates yet; the chosen one gets the full protocol.

    python3 screens/toro/concepts/sketch.py
"""
from __future__ import annotations

import cmath
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_frames as g  # noqa: E402  (shared helpers and the header preview)

G, f, poly, dot, ribbon, annulus, rot, fold_signal = g.G, g.f, g.poly, g.dot, g.ribbon, g.annulus, g.rot, g.fold_signal
FONT = g.FONT
HAIR, LINE, SUBJECT = 1.1, 1.5, 2.0

# ---- the aurochs: one side-view silhouette (facing left), shared by concepts 1 and 4 --------------------------------
AUROCHS = [  # Lascaux-style aurochs, facing left: heavy forequarters, lyre horns, slender legs
    (8, 92), (12, 100), (22, 104), (34, 106), (46, 112), (56, 122), (66, 134), (74, 142), (80, 148), (84, 152),
    (86, 166), (88, 184), (88, 200), (86, 212), (84, 218), (92, 220), (98, 218), (98, 206), (100, 190), (104, 176),
    (108, 166), (124, 170), (150, 172), (176, 170), (196, 166), (204, 174), (206, 190), (204, 206), (202, 214),
    (200, 218), (208, 220), (214, 218), (214, 206), (220, 194), (224, 182), (228, 172), (234, 160), (238, 146),
    (240, 134), (242, 128), (250, 140), (254, 160), (256, 178), (258, 192), (262, 198), (256, 200), (252, 194),
    (248, 176), (246, 156), (242, 140), (240, 122), (236, 112), (224, 104), (206, 98), (184, 94), (160, 90),
    (138, 82), (120, 72), (106, 66), (92, 66), (80, 70), (70, 72), (66, 70), (62, 58), (64, 46), (72, 36), (82, 30),
    (90, 28), (84, 34), (76, 40), (70, 50), (70, 60), (60, 74), (48, 78), (36, 82), (24, 86), (14, 88)]


def resample(pts, n):
    """closed polyline → n points evenly spaced by arc length"""
    ring = pts + [pts[0]]
    segs = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    total = sum(segs)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        target = total * k / n
        while acc + segs[i] < target:
            acc += segs[i]
            i += 1
        t = (target - acc) / segs[i]
        a, b = ring[i], ring[i + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def fourier(pts, n=256):
    z = [complex(x, y) for x, y in resample(pts, n)]
    return {k: sum(z[j] * cmath.exp(-2j * math.pi * k * j / n) for j in range(n)) / n for k in range(-n // 2 + 1, n // 2)}


COEF = fourier(AUROCHS)


def spectrum_outline(harmonics: float, ring: float = 0.0, rolloff: float = 0.0, m: int = 64):
    """the silhouette rebuilt from |k| ≤ harmonics, with ringing at the cutoff and an extra rolloff (shape)"""
    hk = max(1.0, harmonics)
    out = []
    for j in range(m):
        t = j / m
        z = 0j
        for k, c in COEF.items():
            ak = abs(k)
            if ak > hk + 1:
                continue
            w = 1.0 if ak <= hk else (hk + 1 - ak)                  # soft edge between whole harmonics
            if ak > 2 and abs(ak - round(hk)) < 0.5:
                w *= 1 + 1.6 * ring                                  # resonance: boost the cutoff harmonic only
            if ak > 1:
                w *= 1 / (ak ** (0.6 * rolloff))
            z += w * c * cmath.exp(2j * math.pi * k * t)
        out.append((z.real, z.imag))
    return out


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def place(pts, cx, cy, width):
    x0, y0, x1, y1 = bbox(AUROCHS)
    s = width / (x1 - x0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    return [(cx + (x - mx) * s, cy + (y - my) * s) for x, y in pts]


def path(pts, stroke, width, close=True):
    return f'<path d="{poly(pts) if close else "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{stroke}" stroke-width="{width}"/>'


def fill(pts, color):
    return f'<path d="{poly(pts)}" fill="{color}" stroke="none"/>'


def seg(a, b, color, w=HAIR):
    return fill(ribbon([a, b], w), color)


def text(s, x, y, size=10, color=G[4], anchor=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{color}" {FONT} font-size="{size}px"{a}>{s}</text>'


def frame_open(values):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + g.header(values)


def hrand(i, salt):
    return g.hrand(i, salt)


# ======================================================================================================================
# 1 · the bull drawn by its own spectrum
# ======================================================================================================================
def concept1(v, playing=False):
    o = frame_open(v)
    for x in range(20, 480, 20):                                   # graph paper, quiet
        o.append(seg((x, 44), (x, 216), G[1], 0.8 if x % 100 else HAIR))
    for y in range(60, 220, 20):
        o.append(seg((8, y), (348, y), G[1], 0.8))
    harmonics = 3 + 25 * v["cutoff"] ** 1.3 + (3 if playing else 0)
    raw = spectrum_outline(harmonics, ring=v["res"], rolloff=v["shape"])
    pts = place(raw, 182, 134, 196)
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    gain = 1 + 7 * v["fold"]
    folded = []
    rmax = max(math.hypot(x - cx, y - cy) for x, y in pts)
    for x, y in pts:                                                # wavefold only the outer edge, like a folder's peaks
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy) or 1
        lim = 0.72 * rmax
        r2 = lim + lim * fold_signal(gain * (r - lim) / lim) if r > lim else r
        folded.append((cx + dx / r * r2, cy + dy / r * r2))
    frame_x0, frame_x1, frame_y0, frame_y1 = 70 + 40 * v["drive"], 296 - 40 * v["drive"], 58 + 22 * v["drive"], 210 - 22 * v["drive"]
    clipped = folded if v["drive"] <= 0.02 else [(max(frame_x0, min(frame_x1, x)), max(frame_y0, min(frame_y1, y))) for x, y in folded]
    if v["drive"] > 0.02:                                           # the frame the drive presses the bull into
        for a, b in (((frame_x0, frame_y0), (frame_x1, frame_y0)), ((frame_x1, frame_y0), (frame_x1, frame_y1)),
                     ((frame_x1, frame_y1), (frame_x0, frame_y1)), ((frame_x0, frame_y1), (frame_x0, frame_y0))):
            o.append(seg(a, b, G[3], HAIR))
    if v["spread"] > 0.01:                                          # osc 2's outline, at its ratio
        ratio = 1 + 0.5 * v["spread"]
        ghost = [(cx + (x - cx) * ratio ** 0.5 + 30 * (ratio - 1), cy + (y - cy) * ratio ** 0.5) for x, y in clipped]
        o.append(path(ghost, G[3], HAIR))
    rnd = random.Random(5)                                          # noise: stipple inside the body
    for k in range(int(60 * v["noise"])):
        x, y = rnd.uniform(cx - 90, cx + 90), rnd.uniform(cy - 30, cy + 40)
        o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(1.6, 6))}" fill="{G[3]}" stroke="none"/>')
    jitter = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    final = [(x + jitter * 5 * (hrand(i, 1) - 0.5), y + jitter * 5 * (hrand(i, 2) - 0.5)) for i, (x, y) in enumerate(clipped)]
    o.append(path(final, G[7] if playing else G[6], SUBJECT))
    # the spectrum, right: one bar per harmonic, the cutoff as a line
    bx0, base = 366, 196
    o.append(seg((bx0 - 6, base), (472, base), G[3], HAIR))
    mags = [abs(COEF.get(k, 0)) + abs(COEF.get(-k, 0)) for k in range(1, 31)]
    mmax = max(mags)
    for k, mval in enumerate(mags, start=1):
        x = bx0 + (k - 1) * 3.5
        h = 6 + 120 * (mval / mmax) ** 0.5
        if abs(k - harmonics) < 1.5 and k > 1:
            h *= 1 + 1.4 * v["res"]
        on = k <= harmonics
        o.append(seg((x, base), (x, base - h), G[5] if on else G[2], 1.6))
    cxl = bx0 + (harmonics - 1) * 3.5 + 1.75
    o.append(seg((cxl, base + 4), (cxl, 56), G[4], HAIR))
    o.append(text("fig. 1", 12, 210))
    o.append(text("harmonics", 366, 211))
    o.append("</svg>")
    return "\n".join(o)


# ======================================================================================================================
# 2 · patent drawing of the mechanical bull
# ======================================================================================================================
def cam_profile(r0, lobes, fold_v, shape_v, cx, cy, phase=0.0, n=64):
    gain = 1 + 7 * fold_v
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        s = math.sin(lobes * th + phase)
        tri = 2 / math.pi * math.asin(s)
        saw = ((lobes * th + phase) / math.pi) % 2 - 1
        wave = saw * (1 - shape_v) + tri * shape_v
        r = r0 * (1 + 0.26 * fold_signal(gain * wave * 0.7))
        pts.append((cx + math.cos(th) * r, cy + math.sin(th) * r))
    return pts


def concept2(v, playing=False):
    o = frame_open(v)
    buck = 9 if playing else 0                                      # degrees the saddle tilts on a note
    stroke = 4 + 26 * v["cutoff"]                                   # damper open → longer piston stroke
    # base plate with sparse section hatching
    o.append(fill(ribbon([(40, 200), (440, 200)], LINE), G[5]))
    for x in range(48, 440, 14):
        o.append(seg((x, 202), (x - 6, 210), G[2], HAIR))
    # cams on a shaft (left): two oscillators
    shaft = (110, 168)
    o.append(seg((70, shaft[1]), (180, shaft[1]), G[3], HAIR))
    ratio = 1 + 0.5 * v["spread"]
    o.append(path(cam_profile(20, 2, v["fold"], v["shape"], 96, shaft[1]), G[6], LINE))
    o.append(path(cam_profile(15, max(2, round(2 * ratio * 2) / 2), v["fold"], v["shape"], 146, shaft[1], phase=0.9), G[5], LINE))
    for c in ((96, shaft[1]), (146, shaft[1])):
        o.append(fill(annulus(2.5, 1.2, 16), G[5]) .replace('d="', f'transform="matrix(1 0 0 1 {c[0]} {c[1]})" d="'))
    # follower rocker from the cams to the cylinder
    o.append(fill(ribbon([(96, 146), (226, 140)], 2.2), G[4]))
    o.append(fill(annulus(3, 1.2, 16), G[4]).replace('d="', 'transform="matrix(1 0 0 1 96 146)" d="'))
    # hydraulic cylinder and piston
    cyl = (232, 132, 268, 198)
    for a, b in (((cyl[0], cyl[1]), (cyl[0], cyl[3])), ((cyl[2], cyl[1]), (cyl[2], cyl[3])), ((cyl[0], cyl[1]), (cyl[2], cyl[1]))):
        o.append(seg(a, b, G[5], LINE))
    rod_top = cyl[1] - stroke
    o.append(fill(ribbon([(250, cyl[1] + 10), (250, rod_top)], 5), G[3]))
    o.append(path([(246, cyl[1] + 6), (254, cyl[1] + 6), (254, cyl[1] + 14), (246, cyl[1] + 14)], G[5], HAIR))
    # spring (right): coil count and tension from res
    coils = 4 + round(6 * v["res"])
    top, bot = 104, 198
    spring = []
    for k in range(coils * 2 + 1):
        y = bot - (bot - top) * k / (coils * 2)
        spring.append((350 + (8 if k % 2 else -8), y))
    o.append(path(spring, G[5], HAIR, close=False))
    # the saddle: the bull, mounted on the rod, tilting on a note
    body = place(AUROCHS, 0, 0, 150)
    pivot = (250, rod_top)
    body = [(x, y - 30) for x, y in body]
    body = [(pivot[0] + px, pivot[1] + py) for px, py in rot(body, -buck)]
    o.append(path(body, G[7] if playing else G[6], SUBJECT))
    o.append(fill(annulus(3.2, 1.4, 16), G[6]).replace('d="', f'transform="matrix(1 0 0 1 {f(pivot[0])} {f(pivot[1])})" d="'))
    # pressure gauge (top right): drive
    gx, gy, gr = 418, 82, 26
    o.append(fill(annulus(gr, LINE, 31), G[5]).replace('d="', f'transform="matrix(1 0 0 1 {gx} {gy})" d="'))
    for k in range(9):
        a = math.radians(150 + 240 * k / 8)
        o.append(seg((gx + math.cos(a) * (gr - 6), gy + math.sin(a) * (gr - 6)), (gx + math.cos(a) * (gr - 2), gy + math.sin(a) * (gr - 2)), G[4]))
    na = math.radians(150 + 240 * v["drive"])
    o.append(fill(ribbon([(gx, gy), (gx + math.cos(na) * (gr - 6), gy + math.sin(na) * (gr - 6))], 1.6), G[7]))
    o.append(seg((gx, gy + gr), (gx, 126), G[3]))
    o.append(seg((gx, 126), (360, 126), G[3]))
    # grit on the base (noise)
    rnd = random.Random(3)
    for k in range(int(30 * v["noise"])):
        x = rnd.uniform(46, 436)
        o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(196 - rnd.uniform(0, 3))})" d="{poly(dot(1.5, 6))}" fill="{G[3]}" stroke="none"/>')
    # patent numerals and leaders
    for label, (lx, ly), (tx, ty) in (("10", (122, 212), (96, 186)), ("12", (200, 120), (232, 150)), ("14", (316, 112), (350, 140)),
                                      ("16", (460, 112), (436, 98)), ("18", (300, 52), (268, 70))):
        o.append(seg((lx, ly - 3), (tx, ty), G[3], HAIR))
        o.append(text(label, lx, ly, 10, G[4], "middle"))
    o.append(text("FIG. 1", 470, 214, 10, G[4], "end"))
    o.append("</svg>")
    return "\n".join(o)


# ======================================================================================================================
# 4 · rock-art survey of an aurochs
# ======================================================================================================================
def concept4(v, playing=False):
    o = frame_open(v)
    gain = 1 + 7 * v["fold"]
    amp = 3 + 12 * v["fold"]
    for c in range(6):                                              # rock relief contours across the wall
        y0 = 56 + c * 28
        pts = []
        for k in range(49):
            x = k * 10
            u = x / 480
            base = 5 * math.sin(2.1 * math.pi * u + c * 0.9) + 3 * math.sin(4.7 * math.pi * u + c)
            pts.append((x, y0 + base + amp * fold_signal(gain * math.sin(3.3 * math.pi * u + 0.7 * c)) * 0.5))
        o.append(fill(ribbon(pts, HAIR), G[1] if c % 2 else G[2]))
    for x in range(60, 480, 90):                                    # survey grid crosses
        for y in range(70, 220, 60):
            o.append(seg((x - 3, y), (x + 3, y), G[3])); o.append(seg((x, y - 3), (x, y + 3), G[3]))
    lamp = (206, 130)
    lr = 26 + 150 * v["cutoff"] + (14 if playing else 0)
    # palimpsest: a second, smaller animal under the first, offset by osc 2's ratio
    ratio = 1 + 0.5 * v["spread"]
    second = place(AUROCHS, 384 + 70 * (ratio - 1), 176 - 10 * (ratio - 1), 84)
    for i, (x, y) in enumerate(resample(second, 40)):
        d = math.hypot(x - lamp[0], y - lamp[1])
        o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(1.5, 6))}" fill="{G[3] if d < lr else G[1]}" stroke="none"/>')
    # the aurochs: dotted where incised, joined where painted (shape)
    bull = place(AUROCHS, 210, 128, 216)
    jit = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    pts = [(x + jit * 6 * (hrand(i, 1) - .5), y + jit * 6 * (hrand(i, 2) - .5)) for i, (x, y) in enumerate(resample(bull, 128))]
    for i, (x, y) in enumerate(pts):
        d = math.hypot(x - lamp[0], y - lamp[1])
        lit = max(0.0, min(1.0, 1 - (d - lr) / 30))
        col = grey((1 + 6 * lit) / 7)
        nxt = pts[(i + 1) % len(pts)]
        if v["shape"] > 0.5 and lit > 0.2:                          # painted: continuous strokes
            o.append(seg((x, y), nxt, col, 1.6))
        else:                                                       # incised: a dotted line
            o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(1.6, 6))}" fill="{col}" stroke="none"/>')
    # pigment hatching inside the body (drive)
    rnd = random.Random(9)
    for k in range(int(26 * v["drive"])):
        x, y = rnd.uniform(130, 300), rnd.uniform(110, 160)
        d = math.hypot(x - lamp[0], y - lamp[1])
        o.append(seg((x, y), (x + 7, y - 5), G[4] if d < lr else G[2], HAIR))
    # lamp edge: res sharpens it into bands
    for i in range(1 + round(2 * v["res"])):
        rr = lr + 4 + 6 * i
        if lamp[1] - rr >= 42 and rr < 230:
            o.append(fill(annulus(rr, HAIR, 31), grey((1 + 3 * v["res"] * (1 - 0.3 * i)) / 7)).replace('d="', f'transform="matrix(1 0 0 1 {lamp[0]} {lamp[1]})" d="'))
    rnd = random.Random(12)                                         # calcite speckle (noise)
    for k in range(int(70 * v["noise"])):
        x, y = rnd.uniform(6, 474), rnd.uniform(44, 214)
        o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(1.5, 6))}" fill="{G[2]}" stroke="none"/>')
    o.append(text("PANEL IV · aurochs", 12, 56, 10, G[5]))
    o.append(seg((12, 206), (72, 206), G[4], 1.2))                 # scale bar
    for x in (12, 42, 72):
        o.append(seg((x, 202), (x, 210), G[4]))
    o.append(text("0", 12, 200, 10, G[4], "middle")); o.append(text("50 cm", 72, 200, 10, G[4], "middle"))
    o.append("</svg>")
    return "\n".join(o)


def grey(level):
    return g.grey(level)


CONCEPTS = {"1-spectrum": concept1, "2-patent": concept2, "4-rockart": concept4}


def main():
    D = dict(g.DEFAULTS)
    poses = {"rest": (D, False), "cutoff-000": (dict(D, cutoff=0), False), "cutoff-100": (dict(D, cutoff=1), False),
             "fold-100": (dict(D, fold=1), False), "playing": (D, True)}
    for name, fn in CONCEPTS.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, playing) in poses.items():
            (d / f"{pose}.svg").write_text(fn(vals, playing), encoding="utf-8")
    print("wrote", len(CONCEPTS) * len(poses), "sketch frames")


if __name__ == "__main__":
    main()
