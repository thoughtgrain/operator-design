#!/usr/bin/env python3
"""Frames for toro's TAURUS screen, revision 3 (screens/toro/brief.md).

An atlas page. The Taurus chart is static: grid, stars, figure lines, labels. Every control acts on
something an atlas draws in its own conventions:

  spread  the Moon slides along its dotted ephemeris track       shape   the Moon's phase
  fold    the Milky Way's isophote contours fold at the edges    noise   faint stars come out
  cutoff  a magnifier inset on Aldebaran: the star grows to a disk
  res     Airy rings round the magnified star                    drive   plotted Taurid meteor trails
  aphx    stars drift off their places

One drawing language: hairline strokes (1–1.5 px), outlines first, fills only as dark bodies, one
bright subject. Frames are authored like the panel fragment; mutable outlines sit at a node origin
with points inside ±64 px.

Chart geometry is from thoughtgrain/labyrinth opxy/machines/toro/gen_panel.py, MIT, (c) 2026 briannhinton.

    python3 screens/toro/gen_frames.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "frames"
PREFIX = "toro"
G = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
FONT = 'font-family="UniversNextPro-Light"'


def grey(level: float) -> str:
    return G[max(0, min(7, round(level * 7)))]


# ---- the chart (labyrinth gen_panel.py), absolute, static ------------------------------------------------------
CX, CY = 240, 134
STARS = {"ald": (18, 2, 3.2), "g1": (-6, -14, 2.0), "g2": (-26, -24, 1.7), "g3": (-4, 16, 1.8), "g4": (-28, 28, 1.6),
         "beta": (110, -56, 2.5), "zeta": (96, 44, 2.1), "back": (-70, -6, 1.7), "tail": (-150, 22, 1.7)}
POS = {k: (CX + x, CY + y) for k, (x, y, _) in STARS.items()}
JOINS = [("ald", "g1"), ("g1", "g2"), ("ald", "g3"), ("g3", "g4"), ("g1", "beta"), ("g3", "zeta"),
         ("g2", "back"), ("g4", "back"), ("back", "tail")]
PLE = (120, 106)
PLE7 = [(-8, -4, 1.7), (-2, -7, 1.6), (5, -5, 1.8), (9, 1, 1.6), (3, 5, 1.7), (-5, 6, 1.6), (0, 0, 2.0)]

# ---- the sky's other features -----------------------------------------------------------------------------------
MOON_Y, MOON_X0, MOON_X1, MOON_R = 63, 170, 312, 21          # ephemeris track along the top
INSET, INSET_R = (412, 172), 41                              # magnifier on Aldebaran
MW_ORIGIN, MW_A, MW_B = (440, 102), (392, 62), (492, 148)     # Milky Way band, top right (points within ±64 of origin)
RADIANT = (150, 150)
FIELD_N, FIELD_BASE, TRAILS = 165, 40, 16
BODY_TOP = 40
LINE_W, HAIR = 1.2, 1.0

DEFAULTS = {"spread": 0.06, "fold": 0.18, "cutoff": 0.55, "res": 0.24, "shape": 0.0, "noise": 0.0, "drive": 0.0, "aphx": 0.0}
CONTROLS = list(DEFAULTS)
HIDDEN = (640, 320)
N = {"MW": 0, "HDR": 3, "STAR": 11, "JOIN": 20, "INSET_STAR": 29, "INSET_CORE": 30, "SPIKE": 31, "RING": 32,
     "NEIGH": 36, "MOON_BODY": 38, "MOON_LIMB": 39, "MOON": 40, "TRAIL": 48, "FIELD": 64}
N["TOTAL"] = N["FIELD"] + FIELD_N
MOON_PHASES = 8


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts) -> str:
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def dot(r: float, n: int = 10):
    return [(math.cos(k * 2 * math.pi / n) * r, math.sin(k * 2 * math.pi / n) * r) for k in range(n)]


def annulus(r: float, w: float, n: int = 31, gap_deg: float = 1.5):
    angs = [math.radians(gap_deg / 2 + (360 - gap_deg) * k / (n - 1)) for k in range(n)]
    return [(math.cos(a) * (r + w / 2), math.sin(a) * (r + w / 2)) for a in angs] + \
           [(math.cos(a) * (r - w / 2), math.sin(a) * (r - w / 2)) for a in reversed(angs)]


def ribbon(pts, w):
    ns = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        ns.append((-dy / ln * w / 2, dx / ln * w / 2))
    return [(x + nx, y + ny) for (x, y), (nx, ny) in zip(pts, ns)] + \
           [(x - nx, y - ny) for (x, y), (nx, ny) in reversed(list(zip(pts, ns)))]


def line(a, b, w):
    return ribbon([a, b], w)


def taper(length: float, w0: float, w1: float):
    return [(0, -w0 / 2), (length, -w1 / 2), (length, w1 / 2), (0, w0 / 2)]


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def spike(r: float, inner: float = 0.05):
    return [(math.cos(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner),
             math.sin(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner)) for k in range(8)]


def fold_signal(s: float) -> float:
    while s > 1 or s < -1:
        s = 2 - s if s > 1 else -2 - s
    return s


def hrand(i: int, salt: int) -> float:
    x = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return x - math.floor(x)


def moon_phase(lit: float, r: float = MOON_R):
    ts = [-78 + 156 * i / 15 for i in range(16)]
    limb = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in ts]
    term = [((1 - 2 * lit) * r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in reversed(ts)]
    return limb + term


def in_inset(x, y, pad=0):
    return math.hypot(x - INSET[0], y - INSET[1]) < INSET_R + pad


def on_body(x, y):
    return 2 <= x <= 478 and BODY_TOP + 2 <= y <= 218


# ---- seeded layouts ---------------------------------------------------------------------------------------------
def clear_of_marks(x, y):
    if any(math.hypot(x - px, y - py) < 7 for px, py in POS.values()):
        return False
    if math.hypot(x - PLE[0], y - PLE[1]) < 16 or in_inset(x, y, 4):
        return False
    boxes = [(10, 50, 90, 66), (100, 79, 142, 90), (144, 40, 336, 96), (352, 66, 366, 78), (338, 182, 352, 194), (74, 162, 90, 174), (134, 162, 178, 174)]
    return not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes)


def field_layout():
    rnd, pts = random.Random(41), []
    while len(pts) < FIELD_N:
        x, y = rnd.uniform(6, 474), rnd.uniform(BODY_TOP + 4, 214)
        if clear_of_marks(x, y):
            pts.append((x, y, rnd.choice([1.6, 1.6, 1.7, 1.9]), rnd.choice([3, 3, 4, 5])))
    return pts


def trail_layout():
    """meteor trails as an observer plots them: short lines that trace back to the radiant"""
    rnd, out = random.Random(7), []
    while len(out) < TRAILS:
        ang = rnd.uniform(0, 360)
        d0 = rnd.uniform(26, 230)
        length = rnd.uniform(36, 58)
        a = (RADIANT[0] + math.cos(math.radians(ang)) * d0, RADIANT[1] + math.sin(math.radians(ang)) * d0)
        b = (a[0] + math.cos(math.radians(ang)) * length, a[1] + math.sin(math.radians(ang)) * length)
        if not (on_body(*a) and on_body(*b)) or in_inset(*a, 6) or in_inset(*b, 6):
            continue
        if not (clear_of_marks(*a) and clear_of_marks(*b)):
            continue
        out.append((a, ang, length))
    return out


FIELD = field_layout()
TRAIL = trail_layout()


# ---- static artwork -----------------------------------------------------------------------------------------------
def static_back():
    o = []
    for k in range(3):                                           # declination arcs
        y = 70 + k * 52
        pts = [(x, y - 7 * math.sin(math.pi * x / 480)) for x in range(0, 481, 32)]
        o.append(f'<path d="{poly(ribbon(pts, HAIR))}" fill="{G[1]}" stroke="none"/>')
    for k in range(1, 7):                                        # hour lines, slightly converging
        x0 = k * 68
        o.append(f'<path d="{poly(line((x0 - 6, 42), (x0 + 6, 218), HAIR))}" fill="{G[1]}" stroke="none"/>')
    for dx, dy, r in PLE7:                                       # the Pleiades, as the chart has them
        o.append(f'<path transform="matrix(1 0 0 1 {f(PLE[0] + dx)} {f(PLE[1] + dy)})" d="{poly(dot(r))}" fill="{G[6]}" stroke="none"/>')
    for k in range(16):                                          # the Moon's ephemeris track: dots and day ticks
        x = MOON_X0 + (MOON_X1 - MOON_X0) * k / 15
        if k % 5 == 0:
            o.append(f'<path d="{poly(line((x, MOON_Y + MOON_R + 4), (x, MOON_Y + MOON_R + 9), HAIR))}" fill="{G[3]}" stroke="none"/>')
        o.append(f'<path d="{poly(line((x - 1.6, MOON_Y), (x + 1.6, MOON_Y), HAIR))}" fill="{G[2]}" stroke="none"/>')
    rx, ry = RADIANT                                             # Taurid radiant symbol: small circle, four ticks
    o.append(f'<path transform="matrix(1 0 0 1 {rx} {ry})" d="{poly(annulus(4, HAIR, 24))}" fill="{G[4]}" stroke="none"/>')
    for a in (45, 135, 225, 315):
        p0 = (rx + math.cos(math.radians(a)) * 6, ry + math.sin(math.radians(a)) * 6)
        p1 = (rx + math.cos(math.radians(a)) * 10.5, ry + math.sin(math.radians(a)) * 10.5)
        o.append(f'<path d="{poly(line(p0, p1, HAIR))}" fill="{G[4]}" stroke="none"/>')
    return o


def labels():
    items = [("TAURUS", 16, 62, 12, G[6], ""), ("Pleiades", PLE[0], 88, 10, G[4], ' text-anchor="middle"'),
             ("β", POS["beta"][0] + 7, POS["beta"][1] - 3, 10, G[4], ""), ("ζ", POS["zeta"][0] + 7, POS["zeta"][1] + 12, 10, G[4], ""),
             ("ο", POS["tail"][0] - 5, POS["tail"][1] + 13, 10, G[4], ' text-anchor="end"'),
             ("Taurids", RADIANT[0] - 10, RADIANT[1] + 22, 10, G[4], ""),
             ("α Tau", INSET[0], INSET[1] - INSET_R + 12, 10, G[4], ' text-anchor="middle"')]
    return [f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{c}" {FONT} font-size="{s}px"{extra}>{t}</text>' for t, x, y, s, c, extra in items]


def inset_frame():
    """drawn over the sky: a black window, its rim, four reticle ticks and the leader to Aldebaran"""
    ix, iy = INSET
    o = [f'<path transform="matrix(1 0 0 1 {ix} {iy})" d="{poly(dot(INSET_R, 48))}" fill="{G[0]}" stroke="none"/>',
         f'<path transform="matrix(1 0 0 1 {ix} {iy})" d="{poly(annulus(INSET_R, LINE_W, 31))}" fill="{G[4]}" stroke="none"/>']
    for a in (0, 90, 180, 270):
        p0 = (ix + math.cos(math.radians(a)) * (INSET_R - 5), iy + math.sin(math.radians(a)) * (INSET_R - 5))
        p1 = (ix + math.cos(math.radians(a)) * (INSET_R - 1), iy + math.sin(math.radians(a)) * (INSET_R - 1))
        o.append(f'<path d="{poly(line(p0, p1, HAIR))}" fill="{G[4]}" stroke="none"/>')
    ax, ay = POS["ald"]
    ang = math.atan2(iy - ay, ix - ax)
    start = (ax + math.cos(ang) * 8, ay + math.sin(ang) * 8)
    end = (ix - math.cos(ang) * INSET_R, iy - math.sin(ang) * INSET_R)
    o.append(f'<path d="{poly(line(start, end, HAIR))}" fill="{G[3]}" stroke="none"/>')
    return o


# ---- header preview -----------------------------------------------------------------------------------------------
def header(values: dict) -> list[str]:
    o = ['<g id="preview_header">', '<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    for i, c in enumerate(G):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    caps = {k: str(round(v * 100)) for k, v in values.items()}
    caps["spread"] = f"{1 + 0.5 * values['spread']:.2f}"
    for col in range(4):
        light = "#CBCBCB" if col < 2 else "#000000"
        a, b = CONTROLS[col], CONTROLS[col + 4]
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 10)" fill="{light}" {FONT} font-size="10px">{a}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 17.4)" fill="{light}" {FONT} font-size="20px">{caps[a]}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 33)" fill="#5A5A5A" {FONT} font-size="10px">{b}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 33)" fill="#707070" {FONT} font-size="13px">{caps[b]}</text>')
    o.append("</g>")
    return o


def node(i, x, y, pts, fill, visible=True):
    if not visible:
        x, y = HIDDEN
    return f'<path id="{PREFIX}_node_{i}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="none"/>'


# ---- the frame ----------------------------------------------------------------------------------------------------
def frame(v: dict, playing: bool = False) -> str:
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
         '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>']
    o += header(v)
    o += static_back()

    # Fold · the Milky Way's isophote contours: three outlines whose edges fold 1× → 8×
    gain = 1 + 7 * v["fold"]
    amp = 0.6 + 17 * v["fold"] ** 1.4
    ox, oy = MW_ORIGIN
    dx, dy = MW_B[0] - MW_A[0], MW_B[1] - MW_A[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    contour_shades = (G[1], grey((2 + 1.5 * v["fold"]) / 7), grey((3 + 2 * v["fold"] + (1 if playing else 0)) / 7))
    for c, (half, shade) in enumerate(zip((26, 17, 8), contour_shades)):
        side_a, side_b = [], []
        for k in range(32):
            u = k / 31
            cx, cy = MW_A[0] + dx * u, MW_A[1] + dy * u
            taper_k = 0.35 + 0.65 * math.sin(math.pi * min(1.0, 0.1 + 0.9 * u))   # thin at the top, runs off the edge
            lump_a = 0.24 * math.sin((2.3 + 0.7 * c) * math.pi * u + 1.9 * c) + 0.12 * math.sin((5.1 - 0.9 * c) * math.pi * u + 1.3 + c)   # irregular, and each contour its own
            lump_b = 0.22 * math.sin((1.7 + 0.5 * c) * math.pi * u + 2.1 + 1.1 * c) + 0.10 * math.sin((4.3 + 1.3 * c) * math.pi * u + 0.4)
            fa = fold_signal(gain * math.sin((3.7 + 0.6 * c) * math.pi * u + 2 * c)) * amp * (c + 1) / 3
            fb = fold_signal(gain * math.sin((3.1 - 0.4 * c) * math.pi * u + c + 1.7)) * amp * (c + 1) / 3
            wa = (half * (1 + lump_a) + fa) * taper_k
            wb = (half * (1 + lump_b) + fb) * taper_k
            side_a.append((cx + nx * max(1.0, wa) - ox, cy + ny * max(1.0, wa) - oy))
            side_b.append((cx - nx * max(1.0, wb) - ox, cy - ny * max(1.0, wb) - oy))
        pts = side_a + list(reversed(side_b))
        far = max(max(abs(x), abs(y)) for x, y in pts)
        if far > 63.5:                                             # keep the frame's ±64 px: shrink the whole contour, never clamp points
            pts = [(x * 63.5 / far, y * 63.5 / far) for x, y in pts]
        o.append(f'<path id="{PREFIX}_node_{N["MW"] + c}" transform="matrix(1 0 0 1 {ox} {oy})" d="{poly(pts)}" fill="none" stroke="{shade}" stroke-width="1.5"/>')

    # Drive · plotted Taurid meteor trails, each tracing back to the radiant
    shown_trails = 2 + round((TRAILS - 2) * v["drive"])
    for k, ((ax, ay), ang, length) in enumerate(TRAIL):
        lit = playing and k == 3
        o.append(node(N["TRAIL"] + k, ax, ay, rot(taper(length + (18 if lit else 0), 1.6, 0.5), ang),
                      G[7] if lit else grey((3 + 2 * v["drive"]) / 7), visible=k < shown_trails or lit))

    # Noise + Aphx · faint stars: noise sets how many are out, aphx drifts them
    kink = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    shown = FIELD_BASE + round((FIELD_N - FIELD_BASE) * v["noise"])
    for k, (x, y, r, sh) in enumerate(FIELD):
        reach = kink * (6 + 20 * hrand(k, 1))
        a = math.radians(360 * hrand(k, 2))
        px, py = x + math.cos(a) * reach, y + math.sin(a) * reach
        lit = playing and k % 11 == 0 and k < shown
        o.append(node(N["FIELD"] + k, px, py, dot(r * (1.25 if lit else 1)), G[7] if lit else G[sh],
                      visible=k < shown and on_body(px, py)))

    # the chart's figure: lines and stars, brightening on a note
    flash = 1.0 if playing else 0.0
    for k, (a, b) in enumerate(JOINS):
        (xa, ya), (xb, yb) = POS[a], POS[b]
        d = math.hypot(xb - xa, yb - ya)
        o.append(node(N["JOIN"] + k, xa, ya, rot(line((0, 0), (d, 0), LINE_W), math.degrees(math.atan2(yb - ya, xb - xa))),
                      grey((3 + 3 * flash) / 7)))
    for k, name in enumerate(STARS):                               # black halo then the star: lines stop short of stars
        x, y = POS[name]
        r = STARS[name][2]
        o.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(r + 2.2, 12))}" fill="{G[0]}" stroke="none"/>')
        lit = playing and name == "ald"
        o.append(node(N["STAR"] + k, x, y, dot(r * (1.3 if lit else 1)), G[7] if name == "ald" else G[6]))
    o += labels()

    # Spread + Shape · the Moon on its track: spread slides it, shape sets the phase
    mx = MOON_X0 + (MOON_X1 - MOON_X0) * v["spread"]
    phase = round(v["shape"] * (MOON_PHASES - 1))
    o.append(node(N["MOON_BODY"], mx, MOON_Y, dot(MOON_R, 32), G[1]))                 # dark body, moves with the Moon
    for k in range(MOON_PHASES):
        o.append(node(N["MOON"] + k, mx, MOON_Y, moon_phase(0.1 + 0.9 * k / (MOON_PHASES - 1)), G[3], visible=k == phase))
    o.append(node(N["MOON_LIMB"], mx, MOON_Y, annulus(MOON_R, LINE_W, 31), G[6]))

    # Cutoff + Res · the magnifier on Aldebaran
    o += inset_frame()
    ix, iy = INSET
    c = v["cutoff"]
    star_r = 1.8 + 25 * c                                          # a point → a disk filling most of the window
    o.append(node(N["SPIKE"], ix, iy + 4, spike(min(38, star_r + 9 + (7 if playing else 0))), G[6] if playing else G[4]))
    o.append(node(N["INSET_STAR"], ix, iy + 4, dot(star_r * (1.12 if playing else 1), 32), G[5]))
    o.append(node(N["INSET_CORE"], ix, iy + 4, dot(max(1.6, star_r * 0.78), 32), G[7]))
    for i in range(4):
        b = max(0.0, min(1.0, v["res"] * 4 - i + 0.25))
        radius = star_r + 5 + 5.5 * i
        visible = b > 0.05 and radius < INSET_R - 3
        o.append(node(N["RING"] + i, ix, iy + 4, annulus(max(radius, 4), 1.3, 31), grey((1 + 3.5 * b * (1 - 0.12 * i) + (2 if playing and b > 0 else 0)) / 7),
                      visible=visible))
    for k, (dx2, dy2) in enumerate(((13, -9), (-11, 12))):          # two neighbours that move out as you move in
        m = 1 + 3.5 * c ** 2
        x, y = ix + dx2 * m, iy + 4 + dy2 * m
        o.append(node(N["NEIGH"] + k, x, y, dot(1.7), G[5], visible=in_inset(x, y, -4)))

    for i, col in enumerate(G + G[1:] + [G[7]]):
        o.append(f'<circle id="{PREFIX}_palette_{i}" cx="{700 + 6 * i}" cy="300" r="1" fill="{col}" stroke="{col}" stroke-width="0.5"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    (OUT / "rest.svg").write_text(frame(dict(DEFAULTS)), encoding="utf-8")
    (OUT / "playing.svg").write_text(frame(dict(DEFAULTS), playing=True), encoding="utf-8")
    for n, name in enumerate(CONTROLS, start=1):
        for pct in (0, 50, 100):
            (OUT / f"c{n}-{pct:03d}.svg").write_text(frame(dict(DEFAULTS, **{name: pct / 100})), encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.svg')))} frames · {N['TOTAL']} nodes")


if __name__ == "__main__":
    main()
