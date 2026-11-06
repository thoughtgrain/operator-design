#!/usr/bin/env python3
"""drill · subject pass 01 · rest-frame sketches for all five directions.

One model of the sound, five ways of drawing it. Every frame is the rest state
at the definition's defaults (ratio 2.00, teeth 6, wear 0 %, bite 35 %), the
stock header kept, static artwork only (the sketches don't bind nodes yet).

The model (what the trace and the wheels are drawn from):
    wheel turns `ratio` times per oscillator cycle:   w = ratio * phase
    its teeth step that turn:                         s = (floor(w*T) + edge(frac(w*T))) / T
    wear rounds each step edge (and lowers tooth tips unevenly in the drawings)
    bite pushes the read in toward the steps:         p = w + bite * (s - w)
    out = sin(2 pi p) * (1 - phase)   (CZ-style window keeps the note's pitch)

Run: python3 screens/drill/passes/01-subject/sketch.py
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

RATIO, TEETH, WEAR, BITE = 2.0, 6, 0.0, 0.35

G = {0: "#000000", 1: "#323232", 2: "#4B4B4B", 3: "#646464", 4: "#7D7D7D",
     5: "#969696", 6: "#AFAFAF", 7: "#CDCDCD"}
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2
FONT = "UniversNextPro-Light"


# ---------------------------------------------------------------- model --
def edge(u: float, wear: float) -> float:
    """Step edge inside one tooth: a sharp riser at wear 0, a smooth ramp at 1."""
    width = 0.12 + 0.75 * wear
    a = 0.5 - width / 2
    if u <= a:
        return 0.0
    if u >= a + width:
        return 1.0
    t = (u - a) / width
    return t * t * (3 - 2 * t)


def read_phase(ph: float, ratio=RATIO, teeth=TEETH, wear=WEAR, bite=BITE) -> float:
    w = ratio * ph
    k = w * teeth
    s = (math.floor(k) + edge(k - math.floor(k), wear)) / teeth
    return w + bite * (s - w)


def out(ph: float, **kw) -> float:
    return math.sin(2 * math.pi * read_phase(ph, **kw)) * (1 - ph)


def tooth_r(u: float, wear: float = WEAR) -> float:
    """Radial tooth profile for one tooth, u in [0, 1): 0 root, 1 tip."""
    # root 0.0-0.3, flank 0.3-0.45, tip 0.45-0.75, flank 0.75-0.9, root 0.9-1.0
    u %= 1.0
    if u < 0.3 or u >= 0.9:
        v = 0.0
    elif u < 0.45:
        v = (u - 0.3) / 0.15
    elif u < 0.75:
        v = 1.0
    else:
        v = 1 - (u - 0.75) / 0.15
    smooth = 0.5 - 0.5 * math.cos(2 * math.pi * (u - 0.1))
    v = (1 - wear) * v + wear * smooth * 0.8
    return v


TOOTH_U = (0.1, 0.3, 0.45, 0.6, 0.75, 0.9)


# ---------------------------------------------------------------- svg ----
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Svg:
    def __init__(self):
        self.parts: list[str] = []

    def path(self, pts, fill, stroke, sw):
        assert 3 <= len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.parts.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def ribbon(self, pts, width, col):
        """An open polyline as a thin closed ribbon (never a stroke traced back)."""
        pts = dedupe(pts)
        step = 30
        i = 0
        while i < len(pts) - 1:
            chunk = pts[i:i + step + 1]
            self._ribbon(chunk, width, col)
            i += step

    def _ribbon(self, pts, width, col):
        h = max(width - 0.3, 0.4) / 2
        L, R = [], []
        n = len(pts)
        for j, p in enumerate(pts):
            ns = []
            if j > 0:
                ns.append(normal(pts[j - 1], p))
            if j < n - 1:
                ns.append(normal(p, pts[j + 1]))
            nx = sum(a for a, _ in ns)
            ny = sum(b for _, b in ns)
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            if len(ns) == 2:
                c = ns[0][0] * nx + ns[0][1] * ny
                m = min(1 / max(c, 0.35), 2.5)
            else:
                m = 1
            L.append((p[0] + nx * h * m, p[1] + ny * h * m))
            R.append((p[0] - nx * h * m, p[1] - ny * h * m))
        self.path(L + R[::-1], col, col, 0.3)

    def circle(self, cx, cy, r, fill, stroke, sw):
        self.parts.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, col=G[4], size=10):
        self.parts.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" '
                          f'font-family="{FONT}" font-size="{size}px">{s}</text>')

    def write(self, path: Path, title: str):
        tmpl = (HERE.parents[3] / "opxy" / "templates" / "frame.svg").read_text()
        head = tmpl.split("<!-- Palette entries")[0]
        head = head.split("<!--", 1)[0] + head.split("-->", 1)[1]  # drop the starter comment
        pal = ('  <path id="drill_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>\n'
               '  <path id="drill_palette_1" d="M 710 300 L 714 300 L 714 304 Z" fill="#646464" stroke="#646464" stroke-width="2"/>\n')
        hdr = head.replace(">p1<", ">ratio<").replace(">p2<", ">teeth<").replace(">p3<", ">wear<").replace(">p4<", ">bite<")
        vals = iter(["2.00", "6", "0%", "35%"])
        out_lines = []
        for line in hdr.splitlines():
            if 'font-size="20px">0<' in line:
                line = line.replace(">0<", f">{next(vals)}<")
            out_lines.append(line)
        body = "\n".join("  " + p for p in self.parts)
        path.write_text("\n".join(out_lines).rstrip() + f"\n  <title>{title}</title>\n" + pal + body + "\n</svg>\n")


def normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    return (-dy / ln, dx / ln)


def dedupe(pts):
    o = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, o[-1]) > 0.3:
            o.append(p)
    return o


def gear(cx, cy, r_root, depth, teeth, rot=0.0, k=1.0, wear=WEAR, internal=False, us=TOOTH_U):
    """Gear outline: 6 points per tooth (4 with corners only), k squashes y for isometric."""
    pts = []
    for i in range(teeth):
        for u in us:
            a = rot + 2 * math.pi * (i + u) / teeth
            v = tooth_r(u, wear)
            r = r_root - depth * v if internal else r_root + depth * v
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a) * k))
    return pts


def ellipse(cx, cy, r, k=1.0, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n) * k)
            for i in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


def hatch_circle(svg, cx, cy, r, gap, col):
    c = -r * 1.42
    while c < r * 1.42:
        # line x - y = c (45 deg) through the circle centred at origin
        # points (t + c/2, t - c/2); |p|^2 = 2t^2 + c^2/2 = r^2
        disc = (r * r - c * c / 2) / 2
        if disc > 4:
            t = math.sqrt(disc)
            a = (cx - t + c / 2, cy - t - c / 2)
            b = (cx + t + c / 2, cy + t - c / 2)
            svg.ribbon([a, b], HAIR, col)
        c += gap


def leader(svg, a, b, label, lx, ly, col=G[5]):
    svg.ribbon([a, b], HAIR, G[3])
    svg.text(lx, ly, label, col)


def toothed_arc(cx, cy, r_root, depth, teeth, a0, a1, rot=0.0):
    """Part of a big driver's rim, tooth corners only, as an open polyline from a0 to a1."""
    pts = []
    for i in range(-1, teeth + 1):
        for u in (0.1, 0.3, 0.45, 0.6, 0.75, 0.9):
            a = rot + 2 * math.pi * (i + u) / teeth
            a = (a + math.pi) % (2 * math.pi) - math.pi
            if a0 <= a <= a1:
                r = r_root + depth * tooth_r(u)
                pts.append((a, (cx + r * math.cos(a), cy + r * math.sin(a))))
    return [p for _, p in sorted(pts)]


def meshed(wc, rr, dep):
    """Driver pitch radius is ratio x the wheel's: the wheel turns ratio times per cycle."""
    pw = rr + dep / 2
    pd = pw * RATIO
    dc = (wc[0] - pw - pd, wc[1])
    td = round(TEETH * RATIO)
    rot_w = math.pi - 2 * math.pi * 0.1 / TEETH       # a gap faces the driver
    rot_d = -2 * math.pi * 0.6 / td                    # a tip faces the wheel
    return pw, pd, dc, td, rot_w, rot_d


# ---------------------------------------------------------------- v1 -----
def v1():
    """P1 section drawing, typeset diagram: the wheel, its driver and the follower."""
    s = Svg()
    wc = (306, 120)
    rr, dep = 46, 13
    pw, pd, dc, td, rot_w, rot_d = meshed(wc, rr, dep)
    # centre lines
    s.ribbon([(dc[0] - 14, wc[1]), (wc[0] + 80, wc[1])], HAIR, G[2])
    s.ribbon([(wc[0], wc[1] - 76), (wc[0], wc[1] + 76)], HAIR, G[2])
    s.ribbon([(dc[0], wc[1] - 16), (dc[0], wc[1] + 16)], HAIR, G[2])
    # driver: the oscillator's own turn, ratio x the wheel, seen only near the mesh
    rim = toothed_arc(dc[0], dc[1], pd - dep / 2, dep, td, -0.82, 0.82, rot_d)
    s.ribbon(rim, LINE, G[5])
    s.circle(dc[0], dc[1], 8, "#000000", G[5], LINE)
    for a in (-0.62, 0.62):
        r0, r1 = 9, pd - dep / 2 - 6
        s.ribbon([(dc[0] + r0 * math.cos(a), dc[1] + r0 * math.sin(a)),
                  (dc[0] + r1 * math.cos(a), dc[1] + r1 * math.sin(a))], LINE, G[4])
    # the wheel, subject
    s.path(gear(*wc, rr, dep, TEETH, rot=rot_w), "#000000", G[7], SUBJ)
    s.circle(*wc, 20, "#000000", G[4], LINE)
    hatch_circle(s, *wc, 19, 4.5, G[3])
    s.circle(*wc, 6, "#000000", G[5], LINE)
    # follower: lever pivoted top right, tip bitten into the teeth at the right
    piv = (452, 48)
    tip = (wc[0] + rr + dep - BITE * dep * 1.4 + 1, wc[1] - 10)
    s.ribbon([piv, (tip[0] + 8, tip[1] - 10)], LINE, G[6])
    s.path([(tip[0] + 10, tip[1] - 13), (tip[0] + 5, tip[1] - 8), (tip[0], tip[1]), (tip[0] + 2, tip[1] + 1),
            (tip[0] + 12, tip[1] - 9)], G[6], G[6], 0.3)
    s.circle(*piv, 5, "#000000", G[5], LINE)
    # labels, typeset
    leader(s, (dc[0] + 40, dc[1] + 52), (dc[0] + 20, dc[1] + 70), "a", dc[0] + 10, dc[1] + 82)
    leader(s, (wc[0] - 30, wc[1] + 56), (wc[0] - 46, wc[1] + 72), "b", wc[0] - 56, wc[1] + 84)
    leader(s, (412, 86), (430, 104), "c", 433, 116)
    s.text(16, 204, "fig. 1 · drive wheel", G[4])
    return s


# ---------------------------------------------------------------- v2 -----
def v2():
    """P2 diagram + trace, orthographic elevation: gear pair left, output right."""
    s = Svg()
    wc = (182, 116)
    rr, dep = 38, 10
    pw, pd, dc, td, rot_w, rot_d = meshed(wc, rr, dep)
    # datum and centre lines
    s.ribbon([(10, 200), (232, 200)], HAIR, G[3])
    s.ribbon([(wc[0], wc[1] - 62), (wc[0], 200)], HAIR, G[2])
    s.ribbon([(10, wc[1]), (wc[0] + 58, wc[1])], HAIR, G[2])
    # pitch circles, the gear-drawing convention, hairline
    s.circle(*wc, pw, "none", G[2], HAIR + 0.5)
    # driver rim and wheel
    s.ribbon(toothed_arc(dc[0], dc[1], pd - dep / 2, dep, td, -0.9, 0.9, rot_d), LINE, G[5])
    s.path(gear(*wc, rr, dep, TEETH, rot=rot_w), "#000000", G[6], LINE)
    s.circle(*wc, 6, "#000000", G[5], LINE)
    s.text(16, 44, "elevation", G[4])
    # the trace
    x0, x1, yc, amp = 262, 466, 116, 62
    s.ribbon([(x0, yc), (x1, yc)], HAIR, G[2])
    s.ribbon([(x0, yc - amp - 6), (x0, yc + amp + 6)], HAIR, G[2])
    n = 120
    pts = [(x0 + (x1 - x0) * i / n, yc - amp * out(i / n)) for i in range(n + 1)]
    s.ribbon(pts, SUBJ, G[7])
    # one tick per tooth passing on the time axis
    for j in range(int(RATIO * TEETH) + 1):
        x = x0 + (x1 - x0) * j / (RATIO * TEETH)
        s.ribbon([(x, yc + amp + 12), (x, yc + amp + 18)], HAIR, G[4])
    s.text(x0, 44, "out", G[4])
    return s


# ---------------------------------------------------------------- v3 -----
def v3():
    """P3 trace as subject, survey plan: the bent wave as a proposed alignment."""
    s = Svg()
    x0, x1, yc, amp = 24, 456, 120, 58
    # survey grid crosses
    for gx in range(64, 460, 80):
        for gy in (52, 120, 188):
            s.ribbon([(gx - 4, gy), (gx + 4, gy)], HAIR, G[1])
            s.ribbon([(gx, gy - 4), (gx, gy + 4)], HAIR, G[1])
    # existing alignment: the unbent wave, broken line
    n = 160
    plain = [(x0 + (x1 - x0) * i / n, yc - amp * math.sin(2 * math.pi * RATIO * i / n) * (1 - i / n)) for i in range(n + 1)]
    for i in range(0, n, 4):
        s.ribbon(plain[i:i + 3], HAIR, G[3])
    # proposed alignment, subject
    pts = [(x0 + (x1 - x0) * i / n, yc - amp * out(i / n)) for i in range(n + 1)]
    s.ribbon(pts, SUBJ, G[7])
    # stations: one cross-tick per tooth along the alignment
    steps = int(RATIO * TEETH)
    for j in range(steps + 1):
        ph = j / steps
        x = x0 + (x1 - x0) * ph
        y = yc - amp * out(min(ph, 0.9999))
        s.ribbon([(x, y - 7), (x, y + 7)], HAIR, G[5])
    # chainage along the baseline
    s.ribbon([(x0, 200), (x1, 200)], HAIR, G[3])
    for j in range(int(RATIO) + 1):
        x = x0 + (x1 - x0) * j / RATIO
        s.ribbon([(x, 194), (x, 206)], HAIR, G[4])
        s.text(x + 4 if j < RATIO else x - 26, 198, f"{j}+00", G[4])
    s.text(x0, 44, "plan · alignment", G[4])
    return s


# ---------------------------------------------------------------- v4 -----
def v4():
    """P4 stack in depth, patent section: the rim unrolled, one strip per turn."""
    s = Svg()
    x0, width, base_y = 52, 270, 186
    pitch = width / (TEETH + 0.5)
    dep, body = 16, 22
    layers = 5
    dx, dy = 18, -22
    stagger = (RATIO % 1.0) * pitch

    def strip(ox, oy, shift):
        """One turn of the rim, unrolled: tooth corners only, closed to a base."""
        corners = {0.3: 0.0, 0.45: 1.0, 0.75: 1.0, 0.9: 0.0}
        top = [(ox, oy - body)]
        t = math.floor(-shift / pitch) - 1
        while t * pitch + shift <= width:
            for q, v in corners.items():
                x = (t + q) * pitch + shift
                if 0.5 < x < width - 0.5:
                    top.append((ox + x, oy - body - dep * v))
            t += 1
        top.append((ox + width, oy - body))
        return top + [(ox + width, oy), (ox, oy)]

    for i in reversed(range(1, layers)):
        ox, oy = x0 + dx * i, base_y + dy * i
        col = G[2] if i > 2 else G[3]
        s.path(strip(ox, oy, stagger * i), "#000000", col, LINE)
    # front strip: section, hatched, subject edge bright
    front = strip(x0, base_y, 0)
    s.path(front, "#000000", G[5], LINE)
    for k in range(0, int(width + body), 6):
        a = (x0 + k, base_y)
        b = (x0 + k + body - 3, base_y - body + 3)
        if b[0] > x0 + width - 2:
            continue
        s.ribbon([a, b], HAIR, G[3])
    s.ribbon(front[:-2], SUBJ, G[7])
    # pawl: the follower, pivoted above, its tip bitten into the front strip
    tipx = x0 + pitch * 2.6
    tipy = base_y - body - dep * (1 - BITE) - 2
    piv = (tipx - 46, 62)
    s.ribbon([piv, (tipx - 3, tipy - 8)], LINE, G[6])
    s.path([(tipx - 7, tipy - 12), (tipx, tipy), (tipx + 2, tipy - 1), (tipx + 1, tipy - 10)], G[6], G[6], 0.3)
    s.circle(*piv, 5, "#000000", G[5], LINE)
    # reference numerals
    leader(s, (x0 + width + 4, base_y - 10), (x0 + width + 30, base_y - 2), "10", x0 + width + 34, base_y + 2)
    leader(s, (x0 + width + dx * 4 + 4, base_y + dy * 4 - 10), (x0 + width + dx * 4 + 26, base_y + dy * 4 - 4),
           "12", x0 + width + dx * 4 + 30, base_y + dy * 4)
    leader(s, (piv[0] - 6, piv[1] - 2), (piv[0] - 24, piv[1] - 10), "14", piv[0] - 40, piv[1] - 10)
    s.text(380, 204, "Fig. 4", G[4])
    return s


# ---------------------------------------------------------------- v5 -----
def v5():
    """P12 orrery, hidden-line isometric: an epicyclic train, planet in a toothed ring."""
    s = Svg()
    k = 0.5
    c = (240, 122)
    ring_r, ring_dep = 98, 9
    planet_r = ring_r / (RATIO + 1.0)
    dep = 7
    orbit = ring_r - ring_dep - planet_r - dep / 2 + (BITE * 6)
    ang = math.radians(40)
    pc = (c[0] + orbit * math.cos(ang), c[1] + orbit * math.sin(ang) * k)
    # ring gear: outer rim and internal teeth
    s.path(ellipse(c[0], c[1] + 8, ring_r + 8, k, 56), "#000000", G[3], LINE)
    s.path(gear(*c, ring_r, ring_dep, TEETH * 2, rot=0.1, k=k, internal=True, us=(0.3, 0.45, 0.75, 0.9)),
           "#000000", G[5], LINE)
    # orbit, hairline
    s.ribbon(ellipse(*c, orbit, k, 60, 0, 2 * math.pi) + [ellipse(*c, orbit, k, 60)[0]], HAIR, G[2])
    # sun (the driver) with its arbor
    s.ribbon([(c[0], c[1]), (c[0], c[1] - 46)], LINE, G[4])
    s.path(ellipse(c[0], c[1] + 4, 20, k, 32), "#000000", G[4], LINE)
    s.path(ellipse(*c, 20, k, 32), "#000000", G[5], LINE)
    s.circle(c[0], c[1] - 46, 3, G[4], G[4], 1)
    # carrier arm
    s.ribbon([(c[0], c[1] - 46), (pc[0], pc[1] - 46), (pc[0], pc[1] - 10)], LINE, G[4])
    # planet wheel, subject: thickness skirt then face
    s.path(gear(pc[0], pc[1] + 5, planet_r, dep, TEETH, rot=0.3, k=k), "#000000", G[3], LINE)
    s.path(gear(*pc, planet_r, dep, TEETH, rot=0.3, k=k), "#000000", G[7], SUBJ)
    s.path(ellipse(*pc, 5, k, 16), "#000000", G[5], LINE)
    s.text(20, 44, "train, iso", G[4])
    return s


def main():
    titles = {
        "v1": "drill v1 · P1 section drawing · typeset diagram",
        "v2": "drill v2 · P2 diagram + trace · orthographic elevation",
        "v3": "drill v3 · P3 trace as subject · survey plan",
        "v4": "drill v4 · P4 stack in depth · patent section",
        "v5": "drill v5 · P12 orrery · hidden-line isometric",
    }
    for v, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        (HERE / v).mkdir(exist_ok=True)
        fn().write(HERE / v / "rest.svg", titles[v])
        print(HERE / v / "rest.svg")


if __name__ == "__main__":
    main()
