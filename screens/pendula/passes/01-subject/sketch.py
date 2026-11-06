#!/usr/bin/env python3
"""Pendula, subject pass 01: five rest-frame sketches, one per direction.

    python3 screens/pendula/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, from opxy/templates/frame.svg's header) and
v1..v5/candidate.json. Rest = transport stopped, controls at default, no notes:
every pendulum is held at its release point (the moment before a run starts),
which is the honest still state of a pendulum wave.

Sketches only: static art, no bound node ids yet. Bound parts, palette and
budget come in phase 4 once a subject is picked.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- the machine's defaults (definition.json) ------------------------------
LENGTH_T = 0.4771          # 1.2 s, exponential 0.4..4 s
COUNT = 8                  # linear 3..16
SWING = 0.6                # 0..1
SCALE = "pent"
K = 16                     # longest pendulum makes K swings per realign cycle
SCALES = {
    "pent": [0, 2, 4, 7, 9],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dor": [0, 2, 3, 5, 7, 9, 10],
    "hira": [0, 2, 3, 7, 8],
    "chrom": list(range(12)),
}
HEADER_VALUES = ["1.2s", "8", "60", "pent"]
HEADER_TITLES = ["length", "count", "swing", "scale"]

G = {"ground": "#323232", "ground2": "#4B4B4B", "dim": "#646464", "mid": "#7D7D7D",
     "sec": "#969696", "sec2": "#AFAFAF", "hi": "#CDCDCD", "black": "#000000"}

W_HAIR, W_LINE, W_SUBJ = 1.0, 1.5, 2.0


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def swing_deg(t: float = SWING) -> float:
    return 10 + 35 * t


def scale_notes(n: int, scale: str = SCALE) -> list[int]:
    """Semitone of each pendulum, longest (lowest) first."""
    deg = SCALES[scale]
    return [deg[i % len(deg)] + 12 * (i // len(deg)) for i in range(n)]


# ---- drawing primitives: everything is a closed path, circle or text --------
class Svg:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def ribbon(self, pts, w: float, col: str) -> None:
        """An open polyline as thin closed ribbons (filled, no stroke), ≤ 32 centre points each."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        start = 0
        while start < len(pts) - 1:
            chunk = pts[start:start + 31]
            self._ribbon(chunk, w, col)
            start += 30

    def _ribbon(self, pts, w, col):
        h = w / 2
        left, right = [], []
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((p[0] + nx * h, p[1] + ny * h))
            right.append((p[0] - nx * h, p[1] - ny * h))
        ring = dedupe(left + right[::-1])
        self.add(f'<path d="{d_of(ring)}" fill="{col}" stroke="none" stroke-width="0"/>')

    def seg(self, a, b, w, col):
        self.ribbon([a, b], w, col)

    def poly(self, pts, stroke: str, w: float, fill: str = "none") -> None:
        """Closed outline (≤ 64 points)."""
        pts = dedupe(pts)
        self.add(f'<path d="{d_of(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')

    def circle(self, c, r, stroke, w, fill="#000000"):
        self.add(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=0):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}"/>')

    def text(self, x, y, s, col=G["mid"], size=10):
        self.add(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" '
                 f'font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')

    def write(self, path: Path, title: str) -> None:
        head = header()
        body = "\n  ".join(self.items)
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
            f'  <title>{title}</title>\n{head}\n  {body}\n</svg>\n')


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.2:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def d_of(pts) -> str:
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def arc_pts(c, r, a0, a1, n=24):
    """Angles in degrees, 0 = straight down, positive = to the right."""
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((c[0] + r * math.sin(a), c[1] + r * math.cos(a)))
    return out


def header() -> str:
    steps = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    rows = ['  <g id="preview_canvas">', '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            '  </g>', '  <g id="preview_header">']
    for i, c in enumerate(steps):
        rows.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    for i, t in enumerate(HEADER_TITLES):
        col = "#CBCBCB" if i < 2 else "#000000"
        rows.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                    f'font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
    for i, v in enumerate(HEADER_VALUES):
        col = "#CBCBCB" if i < 2 else "#000000"
        rows.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                    f'font-family="UniversNextPro-Light" font-size="20px">{v}</text>')
    rows.append("  </g>")
    return "\n".join(rows)


# ---- v1 · P13 Capture · typeset diagram ------------------------------------
def v1() -> Svg:
    """One textbook figure: every pendulum hung from one pivot, nested swing arcs,
    the plumb line through the pivot is the gate that captures a bob as it crosses."""
    s = Svg()
    piv = (240.0, 32.0)
    th = swing_deg()
    rmax = 90 + 90 * LENGTH_T
    n = COUNT
    radii = [rmax * (1 - 0.62 * i / (n - 1)) for i in range(n)]
    # support: a short ceiling line with hatching, typeset-figure style
    s.ribbon([(214, 28), (266, 28)], W_LINE, G["mid"])
    for x in range(216, 266, 6):
        s.ribbon([(x, 27.3), (x + 4, 23.3)], W_HAIR, G["dim"])
    # swing arcs (hairline), one per pendulum
    for r in radii:
        s.ribbon(arc_pts(piv, r, -th - 4, th + 4, 28), W_HAIR, G["ground2"])
    # the gate: plumb line + a narrow capture wedge
    s.ribbon([(piv[0], piv[1] + 3), (piv[0], piv[1] + rmax + 10)], W_LINE, G["sec"])
    for a in (-3.5, 3.5):
        p = arc_pts(piv, rmax + 8, a, a, 1)[0]
        q = arc_pts(piv, radii[-1] - 8, a, a, 1)[0]
        s.ribbon([q, p], W_HAIR, G["dim"])
    s.text(piv[0] - 3, piv[1] + rmax + 22, "0", G["mid"])
    # angle mark at the pivot
    s.ribbon(arc_pts(piv, 22, -th, -1.5, 12), W_HAIR, G["mid"])
    a = arc_pts(piv, 34, -th / 2, -th / 2, 1)[0]
    s.text(a[0] - 3, a[1] + 4, "θ", G["mid"])
    # the release line: every string on one ray, held before the run
    tip = arc_pts(piv, rmax, -th, -th, 1)[0]
    s.ribbon([piv, tip], W_LINE, G["sec"])
    s.circle(piv, 2.5, G["sec"], W_LINE)
    for r in radii:
        c = arc_pts(piv, r, -th, -th, 1)[0]
        s.circle(c, 3.6, G["hi"], W_SUBJ)
    # length label on the ray
    m = arc_pts(piv, rmax * 0.55, -th - 7, -th - 7, 1)[0]
    s.text(m[0] - 10, m[1], "l", G["mid"])
    # scale: pitch-class clock, lower left (P13: controls without a twin get a plain corner figure)
    pc = (52.0, 176.0)
    R = 22
    deg = SCALES[SCALE]
    ring = [(pc[0] + R * math.sin(math.radians(30 * k)), pc[1] - R * math.cos(math.radians(30 * k))) for k in range(12)]
    s.poly([(pc[0] + R * math.sin(math.radians(a)), pc[1] - R * math.cos(math.radians(a))) for a in range(0, 360, 10)],
           G["ground2"], W_HAIR)
    for k, p in enumerate(ring):
        if k in deg:
            continue
        s.circle(p, 1.6, G["dim"], W_HAIR)
    s.poly([ring[k] for k in deg], G["sec"], W_LINE)
    for k in deg:
        s.circle(ring[k], 2.5, G["sec"], W_LINE)
    s.text(pc[0] - 3, pc[1] + R + 14, "c", G["mid"])
    s.text(392, 206, "fig. 1", G["mid"])
    return s


# ---- v2 · P14 Loom · orthographic elevation --------------------------------
def v2() -> Svg:
    """Front elevation of the row: strings are the warp, and every crossing is
    woven into the cloth below as a slab on its thread; four rows of history."""
    s = Svg()
    n = COUNT
    notes = scale_notes(n)
    span = 300
    xs = [90 + span * nt / notes[-1] for nt in notes]   # threads spaced by the scale's intervals
    beam_y = 30.0
    lpx = 55 + 75 * LENGTH_T
    th = math.radians(swing_deg())
    lens = [lpx * (K / (K + i)) ** 2 for i in range(n)]
    # beam in elevation
    s.poly([(70, beam_y - 4), (410, beam_y - 4), (410, beam_y + 3), (70, beam_y + 3)], G["mid"], W_LINE, G["ground"])
    # cloth: four rows, newest on top
    top, rowh, gap = 150.0, 13.0, 3.0
    rows = 4
    s.ribbon([(70, top - 6), (410, top - 6)], W_LINE, G["dim"])  # breast beam
    for r in range(rows + 1):
        y = top + r * (rowh + gap) - gap / 2
        if r:
            s.ribbon([(74, y), (406, y)], W_HAIR, G["ground"])
    for x in xs:
        s.ribbon([(x, top - 6), (x, top + rows * (rowh + gap))], W_HAIR, G["ground2"])
    # crossings in the last four beats of the run before it stopped
    T = K * 1.2
    beat = 0.3
    t_end = T * 0.29
    greys = [G["sec2"], G["mid"], G["dim"], G["ground2"]]
    hh = 4 + 8 * SWING
    for r in range(rows):
        t1 = t_end - r * beat
        t0 = t1 - beat
        for i, x in enumerate(xs):
            fr = (K + i) / T
            if math.floor(2 * fr * t1) != math.floor(2 * fr * t0):
                y = top + r * (rowh + gap) + (rowh - hh) / 2
                s.rect(x - 6, y, 12, hh, "#000000", greys[r], W_LINE)
    # pendulums held back for release: seen face on, the bobs ride up towards the viewer
    for i, x in enumerate(xs):
        by = beam_y + 3 + lens[i] * math.cos(th)
        s.ribbon([(x, beam_y + 3), (x, by - 5)], W_HAIR, G["sec"])
        s.circle((x, by), 5, G["hi"], W_SUBJ)
    s.text(414, top + 10, "now", G["mid"])
    s.text(414, top + 3 * (rowh + gap) + 10, "-3", G["mid"])
    return s


# ---- v3 · P5 Field and figure · survey plan --------------------------------
def v3() -> Svg:
    """Seen from above like a survey plan: the row lies along a datum, each bob's
    lane crosses it, and the release board holds every bob on one bright line."""
    s = Svg()
    n = COUNT
    # field: survey grid, ground grey, stops short of the strip
    for x in range(36, 460, 24):
        s.ribbon([(x, 34), (x, 182)], W_HAIR, G["ground"])
    for y in range(38, 184, 24):
        s.ribbon([(24, y), (456, y)], W_HAIR, G["ground"])
    datum = 110.0
    # datum line, dashed as separate pieces
    x = 24
    while x < 456:
        s.ribbon([(x, datum), (min(x + 10, 456), datum)], W_LINE, G["mid"])
        x += 16
    s.text(24, datum - 6, "datum", G["mid"])
    xs = [120 + 240 * i / (n - 1) for i in range(n)]
    lpx = 0.55 + 0.45 * LENGTH_T          # plan span of a lane scales with pendulum length
    amp = 70 * lpx                        # same release displacement for every bob
    lanes = [amp * (K / (K + i)) ** 2 * 1.0 + 8 for i in range(n)]
    # beam on the datum (seen from above)
    s.poly([(xs[0] - 14, datum - 3), (xs[-1] + 14, datum - 3), (xs[-1] + 14, datum + 3), (xs[0] - 14, datum + 3)],
           G["sec"], W_LINE, G["black"])
    for i, x in enumerate(xs):
        a = max(lanes[i], amp)
        s.ribbon([(x, datum - a), (x, datum + a)], W_HAIR, G["dim"])
        for yy in (datum - a, datum + a):
            s.ribbon([(x - 3, yy), (x + 3, yy)], W_HAIR, G["dim"])
        s.circle((x, datum), 1.8, G["sec"], W_HAIR)
    # the release board, holding every bob at the same displacement
    by = datum - amp
    s.poly([(xs[0] - 18, by - 9), (xs[-1] + 18, by - 9), (xs[-1] + 18, by - 6), (xs[0] - 18, by - 6)], G["sec"], W_LINE, G["sec"])
    rr = 3 + 4 * SWING                    # proportional symbol: how hard each bob will cross
    for x in xs:
        s.circle((x, by), rr, G["hi"], W_SUBJ)
    # strip: two octaves of semitone ticks, the scale's tones tall, each pendulum's note marked
    notes = scale_notes(n)
    deg = set(SCALES[SCALE])
    y0 = 208.0
    s.ribbon([(96, y0), (384, y0)], W_HAIR, G["ground2"])
    for k in range(25):
        x = 96 + 12 * k
        tall = (k % 12) in deg
        s.ribbon([(x, y0 - (9 if tall else 4)), (x, y0)], W_HAIR if not tall else W_LINE, G["mid"] if tall else G["dim"])
    for nt in notes:
        if nt <= 24:
            s.rect(96 + 12 * nt - 2.5, y0 - 16, 5, 5, G["sec"])
    return s


# ---- v4 · P12 Orrery · patent section ---------------------------------------
def v4() -> Svg:
    """A patent drawing of conical pendulums on one spindle: each bob circles its
    own orbit (its shadow on the section plane is the swing), all held on one
    radius before the run; the section plane through the spindle is the gate."""
    s = Svg()
    n = COUNT
    th = math.radians(swing_deg())
    L0 = 70 + 70 * LENGTH_T
    lens = [L0 * (1 - 0.55 * i / (n - 1)) for i in range(n)]
    e = math.radians(22)
    cam = math.radians(28)            # camera turned so the section plane shows edge-on but not as a point
    cx, piv_y = 240.0, 38.0

    def P(x, y, z):  # world: x right, y away, z up; pivot at origin
        xr = x * math.cos(cam) - y * math.sin(cam)
        yr = x * math.sin(cam) + y * math.cos(cam)
        return (cx + xr, piv_y - (z * math.cos(e)) - yr * math.sin(e))

    def circ(r, z, a0, a1, m=30):
        return [P(r * math.cos(a0 + (a1 - a0) * k / m), r * math.sin(a0 + (a1 - a0) * k / m), z) for k in range(m + 1)]

    base_z = -140.0
    br = 84
    # base plate and its dial
    s.poly(circ(br, base_z, 0, 2 * math.pi, 60)[:-1], G["dim"], W_LINE, G["black"])
    deg = set(SCALES[SCALE])
    for k in range(12):
        a = math.pi / 2 + 2 * math.pi * k / 12
        r0 = br - (12 if k in deg else 6)
        s.ribbon([P(r0 * math.cos(a), r0 * math.sin(a), base_z), P((br - 2) * math.cos(a), (br - 2) * math.sin(a), base_z)],
                 W_LINE if k in deg else W_HAIR, G["mid"] if k in deg else G["dim"])
    # the gate: the section plane x = 0, its trace on the plate with heavy ends (cutting-plane line)
    for y0, y1 in ((-br - 18, -br - 4), (br + 4, br + 18)):
        s.ribbon([P(0, y0, base_z), P(0, y1, base_z)], 2.5, G["sec"])
    yy = -br + 2
    while yy < br - 2:
        s.ribbon([P(0, yy, base_z), P(0, min(yy + 8, br - 2), base_z)], W_HAIR, G["mid"])
        yy += 13
    a_lab = P(0, -br - 22, base_z)
    s.text(a_lab[0] - 4, a_lab[1] + 12, "A", G["mid"])
    a_lab = P(0, br + 18, base_z)
    s.text(a_lab[0] + 6, a_lab[1] + 2, "A", G["mid"])
    orbits = [(L * math.sin(th), -L * math.cos(th)) for L in lens]
    # back halves (far side, y > 0 after the turn is roughly a in (0, pi) shifted by cam)
    lo, hi = -cam, math.pi - cam
    for r, z in orbits:
        s.ribbon(circ(r, z, lo, hi), W_HAIR, G["ground2"])
    # spindle and hub
    for dx in (-3.5, 3.5):
        s.ribbon([P(dx, 0, 4), P(dx, 0, base_z)], W_LINE, G["mid"])
    hub = [P(-9, 0, 9), P(9, 0, 9), P(9, 0, -5), P(-9, 0, -5)]
    s.poly(hub, G["sec"], W_LINE, G["black"])
    for k in range(4):
        x0 = -8 + 4.5 * k
        s.ribbon([P(x0, 0, -4), P(min(x0 + 5, 8), 0, 8)], W_HAIR, G["dim"])
    # front halves
    for r, z in orbits:
        s.ribbon(circ(r, z, hi, lo + 2 * math.pi), W_HAIR, G["dim"])
    # held at release: every bob on one radius, front left
    az = math.radians(200)
    tip = lens[0]
    s.ribbon([P(0, 0, -3), P(tip * math.sin(th) * math.cos(az), tip * math.sin(th) * math.sin(az), -tip * math.cos(th))],
             W_LINE, G["sec"])
    for r, z in orbits:
        s.circle(P(r * math.cos(az), r * math.sin(az), z), 3.6, G["hi"], W_SUBJ)
    # reference numerals
    hubp = P(9, 0, 4)
    s.ribbon([hubp, (hubp[0] + 30, hubp[1] - 4)], W_HAIR, G["dim"])
    s.text(hubp[0] + 33, hubp[1] - 1, "10", G["mid"])
    r, z = orbits[0]
    op = P(r * math.cos(-0.2), r * math.sin(-0.2), z)
    s.ribbon([op, (op[0] + 44, op[1] - 6)], W_HAIR, G["dim"])
    s.text(op[0] + 47, op[1] - 3, "12", G["mid"])
    dp = P(br * math.cos(-0.5), br * math.sin(-0.5), base_z)
    s.ribbon([dp, (dp[0] + 26, dp[1] + 2)], W_HAIR, G["dim"])
    s.text(dp[0] + 29, dp[1] + 6, "14", G["mid"])
    s.text(24, 206, "FIG. 1", G["mid"])
    return s


# ---- v5 · P6 Figures · hidden-line isometric -------------------------------
def v5() -> Svg:
    """A swing set in hidden-line isometric: one block rider per pendulum, chains
    of slowly different lengths, a tuned bar on a post under each seat that the
    rider's feet strike as they pass the bottom. Held back at rest."""
    s = Svg()
    n = COUNT
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    ox, oy = 140.0, 36.0

    def P(x, y, z):  # x along the beam (to lower right), y across (to lower left), z up
        return (ox + (x - y) * c30, oy + (x + y) * s30 - z)

    th = math.radians(swing_deg())
    L0 = 50 + 30 * LENGTH_T
    lens = [L0 * (K / (K + i)) ** 2 for i in range(n)]
    ground = -L0 - 16
    xa, xb = -6.0, 160.0
    xs = [6 + 148 * i / max(n - 1, 1) for i in range(n)]
    notes = scale_notes(n)
    # ground line under the frame, and the back legs
    s.ribbon([P(xa, -22, ground), P(xb, -22, ground)], W_HAIR, G["ground2"])
    s.ribbon([P(xa, -22, ground), P(xa, 0, 0), P(xa, 22, ground)], W_LINE, G["mid"])
    s.ribbon([P(xa, 0, 0), P(xb, 0, 0)], W_SUBJ, G["mid"])
    fy, fz = math.cos(th), -math.sin(th)      # forward along the seat (tangent to the arc)
    uy, uz = math.sin(th), math.cos(th)       # up along the chains
    for i, x in enumerate(xs):
        L = lens[i]
        # tuned bar on a post under the bottom of this swing: lower note, longer bar
        bz = -L - 13
        bl = 30 - 1.0 * notes[i]
        s.ribbon([P(x, 0, ground), P(x, 0, bz - 2)], W_HAIR, G["ground2"])
        top = [P(x - 3, -bl / 2, bz), P(x + 3, -bl / 2, bz), P(x + 3, bl / 2, bz), P(x - 3, bl / 2, bz)]
        s.poly(top, G["mid"], W_LINE, G["ground"])
        # rider held back
        yb, zb = -L * math.sin(th), -L * math.cos(th)

        def Q(dx, fwd, up):
            return P(x + dx, yb + fwd * fy + up * uy, zb + fwd * fz + up * uz)
        for dx in (-5, 5):
            s.ribbon([P(x + dx, 0, 0), Q(dx, 0, 0)], W_HAIR, G["sec"])
        s.poly([Q(-6, -5, 0), Q(6, -5, 0), Q(6, 5, 0), Q(-6, 5, 0)], G["sec"], W_LINE, G["black"])        # seat
        s.poly([Q(-4, 4, 0), Q(4, 4, 0), Q(4, 6, -11), Q(-4, 6, -11)], G["hi"], W_LINE, G["black"])        # shins
        s.poly([Q(-5, -4, 1), Q(-5, 2, 1), Q(-5, 2, 13), Q(-5, -4, 13)], G["sec"], W_LINE, G["black"])     # torso side
        s.poly([Q(-5, 2, 1), Q(5, 2, 1), Q(5, 2, 13), Q(-5, 2, 13)], G["hi"], W_LINE, G["black"])         # torso front
        s.circle(Q(0, -1, 18), 4.0, G["hi"], W_LINE)                                                      # head
    s.ribbon([P(xb, -22, ground), P(xb, 0, 0), P(xb, 22, ground)], W_LINE, G["mid"])
    return s


CANDIDATES = {
    "v1": {
        "variant": "v1", "pattern": "P13", "drawing_language": "typeset diagram",
        "subject": ("A textbook figure with every pendulum hung from a single pivot on nested swing arcs, where the "
                    "plumb line is a gate that captures each bob as it crosses and that crossing is the note."),
        "controls": [
            "length: the radius of the whole nest of arcs (scale, 90 to 180 px), so longer pendulums hang visibly deeper from the pivot.",
            "count: how many nested arcs and bobs hang from the pivot (count, 3 to 16), the inner arcs packing in towards the pivot.",
            "swing: the angle the arcs open to and the bobs are held at, marked θ at the pivot (rotation, 10° to 45° either side).",
            "scale: the polygon on the pitch-class clock in the lower left (shape), a pentagon for pent up to the full twelve-gon for chrom.",
        ],
        "muted": "The gate (plumb line and wedge) drops to the ground grey and the bobs go hollow mid-grey; they still swing, nothing is captured.",
        "reference": "library/meikyu-capture",
        "risks": ("Drawing every pendulum from one pivot is a diagram, not the apparatus; players who know the real row of "
                  "pendulums may not recognise it. At 16 the inner bobs sit ~7 px apart along the ray and need a smaller bob. "
                  "At rest every bob sits on one ray, so the drift only shows when playing (it opens into a spiral). "
                  "The pitch-class clock is a corner figure, the P13 fallback for a control with no twin in the metaphor."),
    },
    "v2": {
        "variant": "v2", "pattern": "P14", "drawing_language": "orthographic elevation",
        "subject": ("A front elevation of the row whose strings run on down as warp threads into a woven cloth, where every "
                    "crossing of the last four beats is a slab on its thread and the drift shows as diagonals."),
        "controls": [
            "length: how far each bob hangs below the beam (position, 55 to 130 px for the longest), the bob line sloping as the real apparatus does.",
            "count: how many strings and warp threads there are (count, 3 to 16).",
            "swing: how high the bobs ride towards the viewer when held back, and how tall each woven slab is (position plus slab height, 4 to 12 px).",
            "scale: the spacing of the threads, set by the scale's intervals so the cloth's gaps are the scale (shape: gaps of 1 to 3 semitones).",
        ],
        "muted": "The weaving stops: the newest row stays empty with a hairline across it and the cloth stops advancing; bobs go mid-grey.",
        "reference": "library/loom-pages",
        "risks": ("Front-on, the swing goes towards the viewer, so swing only reads as the bobs lifting (~26 px at most); "
                  "a side elevation would show it but splits the subject. Four rows is little history for a pendulum wave's "
                  "slow pattern; rows are beats, not cycles. Slab rows are expensive (P14) at 16 threads."),
    },
    "v3": {
        "variant": "v3", "pattern": "P5", "drawing_language": "survey plan",
        "subject": ("A survey plan seen from overhead in which the row lies along a dashed datum on a grid and a bright "
                    "release board holds every bob on one line, ready to snake across it."),
        "controls": [
            "length: the span of every bob's lane across the datum, and so how far the board sits from it (position/scale, ~38 to 70 px).",
            "count: how many lanes cross the datum (count, 3 to 16).",
            "swing: the size of each bob's proportional symbol, how hard it will cross (scale, 3 to 7 px radius).",
            "scale: which ticks stand tall on the two-octave strip along the bottom, with each pendulum's note marked above its tick (count and position in the strip).",
        ],
        "muted": "The release board comes back down onto the bobs wherever they are and the strip's marks go hollow: held, not playing.",
        "reference": "opxy/reference/field-and-figure.jpg",
        "risks": ("Seen from above the pendulum's length is invisible, so length borrows the lane span (which physically "
                  "also grows with swing); swing is then a symbol size, a map convention rather than a physical part. "
                  "The grid is ground decoration and costs nothing, but it is the most 'chart-like' of the five."),
    },
    "v4": {
        "variant": "v4", "pattern": "P12", "drawing_language": "patent section",
        "subject": ("A patent sheet of conical pendulums on one spindle, each bob orbiting its own circle whose shadow on "
                    "the section plane is its swing, so the bobs form an orrery and a crossing of that plane plays."),
        "controls": [
            "length: how far the cone of rods drops from the hub and how wide the orbits open with it (scale, 1.6x).",
            "count: how many orbits and bobs ring the spindle (count, 3 to 16).",
            "swing: the cone's half-angle: orbits widen and rise towards the hub as it opens (shape of the stack, 10° to 45°).",
            "scale: which ticks on the base dial are long, one per scale degree of the octave (shape of the dial).",
        ],
        "muted": "The section plane line drops to ground grey and the bobs stop on their orbits, hollow.",
        "reference": "library/meikyu-orrery",
        "risks": ("A conical pendulum is a different machine; its projection is the swing, but it asks the player to "
                  "accept that. Nested ellipses at 16 get dense near the hub. Patent numerals are decoration unless "
                  "they stay few. The base dial is the weak control, a ring of ticks."),
    },
    "v5": {
        "variant": "v5", "pattern": "P6", "drawing_language": "hidden-line isometric",
        "subject": ("A swing set in hidden-line isometric with a block rider on every seat and chains of slowly different "
                    "lengths, whose feet strike a tuned bar on the ground as each rider passes the bottom."),
        "controls": [
            "length: the chain lengths, riders hanging lower as it rises (position, ~30 px).",
            "count: how many riders hang from the beam (count, 3 to 16).",
            "swing: how far back the riders are held (rotation of each chain about the beam, 10° to 45°).",
            "scale: the lengths of the tuned bars on the ground, longer for lower notes (shape).",
        ],
        "muted": "Riders sit still at the bottom, feet clear of the bars; the bars go ground grey.",
        "reference": "library/theseus-tower",
        "risks": ("Stretch, and I don't think it earns the exception: the pendulum is already the performer, so a rider "
                  "adds a character without adding a meaning, and figures invite idle animation and the drawing-quality "
                  "trap toro hit. The only case for it is warmth: a row of swings reads instantly. A node can't tilt out "
                  "of the screen's plane, so the swinging riders need pre-drawn poses per angle step, and 16 riders is a crowd."),
    },
}


def main() -> None:
    for vid, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / vid
        d.mkdir(exist_ok=True)
        fn().write(d / "rest.svg", f"pendula {vid} rest")
        (d / "candidate.json").write_text(json.dumps(CANDIDATES[vid], indent=2, ensure_ascii=False) + "\n")
    print("wrote v1..v5")


if __name__ == "__main__":
    main()
