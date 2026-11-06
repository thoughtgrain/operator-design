#!/usr/bin/env python3
"""Vapor subject pass 01: five rest-frame sketches, one per direction.

v1 P15 Cell field      typeset diagram         a cell field laid over the vowel chart
v2 P1  Section drawing orthographic elevation  the throat as a segmented acoustic tube
v3 P2  Diagram + trace survey plan             vowel plot surveyed on the left, spectral profile on the right
v4 P3  Trace as subject patent section          the pressure wave, onset periods ghosted, aspiration below
v5 P11 Instrument stack hidden-line isometric   five vowel resonators stacked on a throat neck (stretch)

All frames show vapor's defaults: vowel a, breath 25 %, throat 1.00, glide 60 ms.
Static artwork only (sketches); bound nodes come in the frames pass.

    python3 screens/vapor/passes/01-subject/sketch.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

G = {"bright": "#CDCDCD", "b2": "#AFAFAF", "mid": "#969696", "m2": "#7D7D7D", "low": "#646464",
     "ground": "#4B4B4B", "dark": "#323232", "black": "#000000"}

# Defaults (definition.json)
VOWEL = "a"
BREATH = 0.25
THROAT = 1.0
GLIDE_V = 0.4147  # normalised; 60 ms

FORMANTS = {  # F1, F2, F3 in Hz, adult tract at throat 1.00
    "u": (300, 870, 2240), "o": (500, 900, 2600), "a": (730, 1090, 2440),
    "e": (530, 1840, 2480), "i": (270, 2290, 3010),
}


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Frame:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def poly(self, pts, stroke="none", sw=0.0, fill="none"):
        pts = dedupe(pts, closed=True)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def ribbon(self, pts, w, col):
        """An open line drawn as a thin closed ribbon (constraints.md: never a stroke traced back)."""
        pts = dedupe(pts, closed=False)
        for chunk in chunks(pts, 31):
            self.poly(ribbon_pts(chunk, w), fill=col)

    def rect(self, x, y, w, h, fill, stroke="none", sw=0.0):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def text(self, x, y, s, col=G["m2"], size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" stroke-width="0" '
                 f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')

    def svg(self) -> str:
        return HEADER + "\n".join("  " + p for p in self.parts) + "\n</svg>\n"


def dedupe(pts, closed):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def chunks(pts, n):
    i = 0
    while i < len(pts) - 1:
        yield pts[i:i + n]
        i += n - 1


def ribbon_pts(pts, w):
    h = w / 2
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        # miter at joints, limited
        if 0 < i < len(pts) - 1:
            d1 = (p[0] - a[0], p[1] - a[1]); l1 = math.hypot(*d1) or 1
            d2 = (b[0] - p[0], b[1] - p[1]); l2 = math.hypot(*d2) or 1
            n1 = (-d1[1] / l1, d1[0] / l1); n2 = (-d2[1] / l2, d2[0] / l2)
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            ml = math.hypot(mx, my) or 1
            mx, my = mx / ml, my / ml
            cos = mx * n1[0] + my * n1[1]
            k = h / max(cos, 0.5)
            nx, ny = mx * k / h, my * k / h
        left.append((p[0] + nx * h, p[1] + ny * h))
        right.append((p[0] - nx * h, p[1] - ny * h))
    return left + right[::-1]


def ellipse(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


HEADER_VALUES = ["a", "25", "1.00", "60ms"]
LABELS = ["vowel", "breath", "throat", "glide"]


def header_svg() -> str:
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    out = ['  <g id="preview_canvas">', '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', "  </g>",
           '  <g id="preview_header">']
    for i, c in enumerate(steps):
        out.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for i, (lab, val) in enumerate(zip(LABELS, HEADER_VALUES)):
        tcol = "#CBCBCB" if i < 2 else "#000000"
        out.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{tcol}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="10px">{lab}</text>')
        out.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{tcol}" stroke="none" '
                   f'font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
    out.append("  </g>")
    return "\n".join(out) + "\n"


HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
          + header_svg())


# ---------------------------------------------------------------- v1 cell field, typeset diagram
def v1() -> Frame:
    """The vowel chart as a field of 20 px cells. The lit clump sits at the vowel (IPA layout:
    front left, back right, close top, open bottom); breath is a grey haze of runs round it;
    throat is the clump's size; glide is a trail of cells from the closed /u/ corner."""
    fr = Frame()
    C, X0, Y0, COLS, ROWS = 20, 0, 32, 24, 9
    lit, haze, trail = set(), set(), set()
    # clump at /a/ (bottom centre), size set by throat 1.00: 9 cells
    lit |= {(11, 7), (12, 7), (13, 7), (12, 6), (13, 6), (10, 8), (11, 8), (12, 8), (14, 7)}
    # glide trail from /u/ at (20,1) toward the clump, length from glide (41 % -> 4 cells)
    path = [(19, 2), (18, 3), (17, 4), (16, 5), (15, 6)]
    n_trail = round(GLIDE_V * len(path) * 1.2)
    trail |= set(path[:n_trail])
    # breath haze: runs of 2-3 round the clump, count from breath
    rng = random.Random(7)
    cand = [(c, r) for c in range(6, 19) for r in range(4, 9)
            if (c, r) not in lit and (c, r) not in trail and 2 <= abs(c - 12) + abs(r - 7) <= 6]
    rng.shuffle(cand)
    want = round(BREATH * 56)
    for c, r in cand:
        if len(haze) >= want:
            break
        run = [(c, r), (c + 1, r)] if rng.random() < 0.6 else [(c, r), (c, r + 1)]
        if all(0 <= x < COLS and 0 <= y < ROWS and (x, y) not in lit and (x, y) not in trail for x, y in run):
            haze |= set(run)
    letters = {"i": (3, 1), "e": (5, 4), "a": (12, 7), "o": (19, 4), "u": (20, 1)}
    for c in range(COLS):
        for r in range(ROWS):
            x, y = X0 + c * C, Y0 + r * C
            if (c, r) in lit:
                fr.rect(x + 1, y + 1, 18, 18, G["bright"])
            elif (c, r) in trail:
                fr.rect(x + 1, y + 1, 18, 18, G["low"])
            elif (c, r) in haze:
                fr.rect(x + 1, y + 1, 18, 18, G["dark"], G["ground"], 1)
            elif (c, r) not in letters.values():
                fr.rect(x + 8.5, y + 8.5, 3, 3, G["ground"])
    for ch, (c, r) in letters.items():
        x, y = X0 + c * C, Y0 + r * C
        col = G["black"] if (c, r) in lit else G["m2"]
        fr.text(x + 7, y + 14, ch, col, 12)
    return fr


# ---------------------------------------------------------------- v2 section drawing, orthographic elevation
def area_profile(vowel: str, n: int):
    """Radius per tube section, glottis to lips (a crude Fant-style area function)."""
    shapes = {
        "a": lambda t: 4 + 9 * max(0.0, (t - 0.45) / 0.55) ** 0.8 if t > 0.45 else 4.5 - 1.5 * math.sin(t / 0.45 * math.pi),
        "u": lambda t: 8 - 5 * math.exp(-((t - 0.7) / 0.12) ** 2) - (4 if t > 0.92 else 0),
        "i": lambda t: 11 - 8 * math.exp(-((t - 0.78) / 0.12) ** 2) if t > 0.1 else 5,
    }
    fn = shapes.get(vowel, shapes["a"])
    return [max(2.5, fn((k + 0.5) / n)) for k in range(n)]


def v2() -> Frame:
    """The throat as an acoustic tube in elevation: sixteen cylinder sections from the glottis
    (left) to the lips (right), drawn about a centre line. Vowel reshapes the radii; throat sets
    the length; breath is turbulence streaks at the glottis; glide draws the onset profile and
    the intermediate profiles it passes through."""
    fr = Frame()
    N, x0, cy = 16, 92, 112
    L = 240 * THROAT
    seg = L / N
    K = 4.0  # px per radius unit
    prof = area_profile("a", N)
    onset = area_profile("u", N)

    def outline(radii):
        top, bot = [], []
        for k, r in enumerate(radii):
            xa, xb = x0 + k * seg, x0 + (k + 1) * seg
            top += [(xa, cy - r * K), (xb, cy - r * K)]
            bot += [(xa, cy + r * K), (xb, cy + r * K)]
        return top + bot[::-1]

    # centre line, dash-dot as short ribbons
    x = 60
    while x < x0 + L + 30:
        fr.ribbon([(x, cy), (x + 12, cy)], 1, G["ground"])
        fr.ribbon([(x + 15, cy), (x + 17, cy)], 1, G["ground"])
        x += 20
    # glide: intermediate profiles between onset /u/ and /a/ (count from glide), hairline
    n_mid = max(0, round(GLIDE_V * 2.5))
    for j in range(n_mid + 1):
        t = j / (n_mid + 1)
        radii = [o + (p - o) * t for o, p in zip(onset, prof)]
        col = G["low"] if j == 0 else G["dark"]
        fr.poly(outline(radii), stroke=col, sw=1)
    # the tube at the vowel: subject outline
    fr.poly(outline(prof), stroke=G["bright"], sw=2.5, fill="none")
    # glottis: two vocal-fold wedges at the left end
    gx = x0 - 2
    fr.poly([(gx - 14, cy - 30), (gx, cy - 30), (gx, cy - 4), (gx - 6, cy - 4)], stroke=G["mid"], sw=1.5, fill=G["dark"])
    fr.poly([(gx - 6, cy + 4), (gx, cy + 4), (gx, cy + 30), (gx - 14, cy + 30)], stroke=G["mid"], sw=1.5, fill=G["dark"])
    # breath: turbulence streaks just past the glottis, count from breath
    rng = random.Random(3)
    n_streak = round(BREATH * 20)
    for k in range(n_streak):
        sx = x0 + 6 + rng.uniform(0, 40)
        sy = cy + rng.uniform(-9, 9)
        fr.ribbon([(sx, sy), (sx + 10, sy + rng.uniform(-1.5, 1.5))], 1.5, G["mid"])
    # dimension line under the tube
    dy = 186
    fr.ribbon([(x0, dy), (x0 + L, dy)], 1, G["low"])
    fr.ribbon([(x0, dy - 6), (x0, dy + 6)], 1, G["low"])
    fr.ribbon([(x0 + L, dy - 6), (x0 + L, dy + 6)], 1, G["low"])
    fr.text(x0 + L / 2 - 18, dy + 15, f"{17.5 * THROAT:.1f} cm", G["m2"])
    fr.text(x0 - 44, 66, "glottis", G["m2"])
    fr.text(x0 + L + 8, 66, "lips", G["m2"])
    return fr


# ---------------------------------------------------------------- v3 diagram + trace, survey plan
def resonance_db(freq, formants, bw=(90, 110, 160), amps=(1.0, 0.6, 0.3)):
    """Parallel formant bank magnitude in dB (each band peaks at its amp), -40 dB floor."""
    h = 0.0
    for F, B, A in zip(formants, bw, amps):
        h += A * (B * freq) / math.sqrt((F * F - freq * freq) ** 2 + (B * freq) ** 2)
    return max(-40.0, 20 * math.log10(max(h, 1e-4)))


def v3() -> Frame:
    """Left: the vowel quadrilateral surveyed as a plot (boundary, stations at the five vowels,
    a traverse from the onset station to the vowel with chainage ticks). Right: the spectral
    profile, drawn as a long section over a frequency datum, with breath as the ground line."""
    fr = Frame()
    # --- plan (x 0-240). Chart: F2 2400..700 Hz left->right, F1 250..800 Hz top->bottom, scaled by throat about its origin
    def plan_xy(F1, F2):
        s = 1 / THROAT
        F1, F2 = F1 * s, F2 * s
        x = 30 + (2400 - F2) / 1700 * 190
        y = 46 + (F1 - 250) / 550 * 140
        return x, y
    corners = [plan_xy(270, 2290), plan_xy(300, 870), plan_xy(730, 1000), plan_xy(730, 1500)]
    fr.poly(corners, stroke=G["low"], sw=1.2)
    # parcel bearings: short hairline offsets along the boundary? keep plain: station marks + labels
    stations = {v: plan_xy(*FORMANTS[v][:2]) for v in "uoaei"}
    for v, (x, y) in stations.items():
        if v == VOWEL:
            continue
        fr.poly([(x, y - 5), (x + 5, y + 4), (x - 5, y + 4)], stroke=G["mid"], sw=1.2)
        fr.text(x + 7, y + 4, v, G["m2"])
    # traverse from the onset station (u) to the vowel, chainage ticks from glide
    ux, uy = stations["u"]
    ax, ay = stations[VOWEL]
    fr.ribbon([(ux, uy), (ax, ay)], 1.2, G["mid"])
    n_tick = round(GLIDE_V * 14)
    L = math.dist((ux, uy), (ax, ay))
    tx, ty = (ax - ux) / L, (ay - uy) / L
    for k in range(1, n_tick + 1):
        px, py = ux + tx * L * k / (n_tick + 1), uy + ty * L * k / (n_tick + 1)
        fr.ribbon([(px - ty * 4, py + tx * 4), (px + ty * 4, py - tx * 4)], 1, G["mid"])
    # the vowel station: a filled ring, secondary brightness
    fr.poly(ellipse(ax, ay, 6, 6, 24), stroke=G["b2"], sw=2, fill=G["dark"])
    fr.text(ax + 10, ay + 4, VOWEL, G["b2"])
    fr.text(26, 206, "plan  F1 / F2", G["low"])
    # zone divider
    fr.ribbon([(240, 40), (240, 206)], 1, G["dark"])
    # --- section (x 256-468): spectral envelope over 0..4 kHz
    X0, X1, base = 256, 468, 186
    fr.ribbon([(X0, base), (X1, base)], 1, G["low"])
    for k in range(5):
        x = X0 + (X1 - X0) * k / 4
        fr.ribbon([(x, base), (x, base + 5)], 1, G["low"])
        if k in (0, 2, 4):
            fr.text(x - 3, base + 16, f"{k}k" if k else "0", G["low"])
    form = tuple(F / THROAT for F in FORMANTS[VOWEL])
    pts = []
    for i in range(62):
        fq = 60 + (4000 - 60) * i / 61
        db = resonance_db(fq, form)
        x = X0 + (X1 - X0) * fq / 4000
        y = base - 6 - (db + 40) * 3.0
        pts.append((x, min(base - 4, max(42, y))))
    # breath: a ground line of noise under the profile (survey: existing ground), height from breath
    rng = random.Random(5)
    floor = base - 8 - BREATH * 40
    g = [(X0 + (X1 - X0) * i / 40, floor + rng.uniform(-2.5, 2.5)) for i in range(41)]
    fr.ribbon(g, 1.2, G["low"])
    fr.ribbon(pts, 2.2, G["bright"])
    fr.text(300, 46, "section  dB / Hz", G["low"])
    return fr


# ---------------------------------------------------------------- v4 trace as subject, patent section
def wave(t_ms, formants, amps=(1.0, 0.55, 0.18), bw=(80, 90, 120)):
    v = 0.0
    for F, A, B in zip(formants, amps, bw):
        v += A * math.exp(-math.pi * B * t_ms / 1000) * math.sin(2 * math.pi * F * t_ms / 1000)
    return v


def v4() -> Frame:
    """The pressure wave at the lips, drawn as a patent figure: four glottal periods, the first
    ones still gliding from a closed /u/ (grey) into the vowel (bright), the aspiration noise
    drawn as its own trace below, numerals with leaders. Vowel is the ringing inside each period,
    throat the trace's scale, breath the lower trace's amplitude, glide how many periods are ghosts."""
    fr = Frame()
    X0, X1, cy, A = 40, 440, 100, 46
    periods = 4
    P = (X1 - X0) / periods  # px per period (8 ms at 125 Hz)
    ms_per_px = 8.0 / P / THROAT
    n_ghost = max(1, round(GLIDE_V * 4))  # 41 % -> 2
    fr.ribbon([(X0 - 10, cy), (X1 + 10, cy)], 1, G["dark"])
    for p in range(periods):
        t = min(1.0, p / n_ghost) if n_ghost else 1.0
        form = tuple(fu + (fa - fu) * t for fu, fa in zip(FORMANTS["u"], FORMANTS[VOWEL]))
        form = tuple(F / THROAT for F in form)
        pts = []
        steps = 60
        for i in range(steps + 1):
            x = X0 + p * P + P * i / steps
            tm = (x - X0 - p * P) * ms_per_px
            y = cy - A * wave(tm, form) * (0.75 + 0.25 * t)
            pts.append((x, y))
        col = G["bright"] if p >= n_ghost else (G["low"] if p == 0 else G["m2"])
        w = 2.2 if p >= n_ghost else 1.5
        fr.ribbon(pts, w, col)
    # aspiration trace: noise bursts at each glottal opening, amplitude from breath
    rng = random.Random(11)
    by = 172
    pts = []
    for i in range(121):
        x = X0 + (X1 - X0) * i / 120
        ph = ((x - X0) % P) / P
        env = math.exp(-ph * 5) * 0.8 + 0.2
        pts.append((x, by + (rng.uniform(-1, 1) * 40 * BREATH * env)))
    fr.ribbon(pts, 1.2, G["mid"])
    fr.ribbon([(X0 - 10, by), (X0 - 2, by)], 1, G["low"])
    # patent numerals and leaders
    def lead(nx, ny, tx, ty, s):
        fr.ribbon([(nx, ny), (tx, ty)], 1, G["low"])
        fr.text(nx - (12 if nx < tx else -3), ny + 4, s, G["m2"])
    lead(X0 + 3.4 * P, 44, X0 + 3 * P + 6, cy - 30, "10")
    lead(X0 + 3.75 * P + 12, 150, X0 + 3 * P + 40, cy + 8, "12")
    lead(X0 + 0.6 * P, 140, X0 + 0.35 * P, cy + 10, "16")
    lead(X0 + 2.1 * P, 204, X0 + 2.0 * P + 6, by + 4, "14")
    fr.text(X0 - 6, 212, "FIG. 1", G["m2"])
    return fr


# ---------------------------------------------------------------- v5 instrument stack, hidden-line isometric
def v5() -> Frame:
    """Five vowel resonators stacked on a throat neck, like the short resonators of a vox humana
    organ stop: u at the base to i on top, each chamber its own shape. The sung vowel's chamber
    is drawn solid and slid out; throat is the neck's height; breath is rings rising off the top;
    glide lights the chambers between /u/ and the vowel."""
    fr = Frame()
    cx, base = 240, 206
    ry_k = 0.32
    neck_h = 34 * THROAT
    # reed boot / glottis: a short cone, then the neck
    def cyl(x, y_bot, r_bot, r_top, h, edge, fill, sw=1.5, dx=0.0):
        """A frustum from y_bot up by h, hidden-line silhouette and top ellipse."""
        y_top = y_bot - h
        back = ellipse(x + dx, y_top, r_top, r_top * ry_k, 24, math.pi, 2 * math.pi)  # left -> right via back (top half)
        front = ellipse(x + dx, y_bot, r_bot, r_bot * ry_k, 24, 0, math.pi)           # right -> left via front
        fr.poly(back + front, stroke=edge, sw=sw, fill=fill)
        fr.poly(ellipse(x + dx, y_top, r_top, r_top * ry_k, 40), stroke=edge, sw=sw, fill=fill)
        return y_top
    # floor ellipse in the same projection
    fr.poly(ellipse(cx, base, 70, 70 * ry_k, 48), stroke=G["dark"], sw=1.2)
    y = cyl(cx, base, 26, 12, 16, G["low"], G["black"])           # boot (glottal source)
    y = cyl(cx, y, 6, 6, neck_h, G["low"], G["black"])             # throat neck
    tiers = [("u", 22, 18, 20), ("o", 26, 24, 18), ("a", 34, 30, 18), ("e", 24, 16, 16), ("i", 14, 10, 14)]
    rank = {v: k for k, (v, *_rest) in enumerate(tiers)}
    sel = rank[VOWEL]
    for k, (v, rb, rt, h) in enumerate(tiers):
        if k == sel:
            y2 = cyl(cx, y, rb, rt, h, G["bright"], G["dark"], sw=2.2)
        else:
            lit = k < sel and (sel - k) <= max(1, round(GLIDE_V * 4))
            edge = G["m2"] if lit else G["low"]
            y2 = cyl(cx, y, rb, rt, h, edge, G["black"])
        fr.text(cx + max(rb, rt) + 8, y - h / 2 + 4, v, G["bright"] if k == sel else G["m2"])
        y = y2
    # breath: rings rising off the top, count from breath
    n_ring = max(1, round(BREATH * 10))
    for j in range(n_ring):
        rr = 8 + j * 5
        fr.poly(ellipse(cx, y - 8 - j * 7, rr, rr * ry_k, 32), stroke=G["ground"], sw=1.2)
    return fr


def main() -> None:
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(fn().svg(), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
