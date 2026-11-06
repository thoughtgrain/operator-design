#!/usr/bin/env python3
"""Ringer, subject pass 02: five rest-frame sketches from one script.

Five new directions on change ringing (pass.json): tower bells, ropes, the
ringing chamber, the bell turning on its headstock. Nothing from pass 01
(orrery, isometric frame of swung bells, star atlas, single-bell elevation
with a tick strip, scope trace) is reused.

Every frame is 480 x 220, keeps the stock header exactly as the template lays
it out (machine labels and default values in it), and draws the controls at
their defaults: 6 bells, plain bob, 2 blows a beat, stroke 0 %. The row on
show is a real plain bob minor change (426153), so place 1 is bell 4.

No text below the header. States are line weight, brightness, position or
hatching, never a lighter grey fill. 3D parts come from world models through
one camera per variant (craft.md, Think in 3D).

    python3 screens/ringer/passes/02-subject/sketch.py

Device rules kept at sketch stage: one subpath per path, <= 64 points, lines
as closed filled ribbons, explicit paint on every leaf, grey only (never
red), <= 4 fractional digits.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

N = 6                      # bells at default (0.25 of 4..12)
PACE = 2.0                 # blows per beat at default
GAP = 0.0                  # handstroke gap in blows (stroke default 0)
LABELS = ["bells", "method", "pace", "stroke"]
VALUES = ["6", "bob", "2.0", "0"]  # ux.md: amounts 0–100 without %

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"

HAIR, LINE, SUBJ = 1.0, 1.5, 2.0       # the three weights (craft.md)


# ---------------------------------------------------------------- the method
def change(row, places):
    row = list(row)
    i, n = 0, len(row)
    while i < n - 1:
        if (i + 1) in places or (i + 2) in places:
            i += 1
            continue
        row[i], row[i + 1] = row[i + 1], row[i]
        i += 2
    return row


def plain_bob(n, rows):
    lead = []
    for _ in range(n):
        lead.append(set())
        lead.append({1, n})
    lead[-1] = {1, 2}
    out = [list(range(1, n + 1))]
    k = 0
    while len(out) < rows:
        out.append(change(out[-1], lead[k % len(lead)]))
        k += 1
    return out


ROW = plain_bob(N, 8)[3]                  # 4 2 6 1 5 3
PLACE = {b: ROW.index(b) + 1 for b in ROW}  # bell -> place in this change


def bell_scale(b, n=N):
    """Lip radius factor: treble 1, each bell down the major scale bigger (size ~ 1/pitch)."""
    steps = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19]  # descending major scale, semitones below treble
    return 2 ** (steps[b - 1] / 12 * 0.75)            # softened so twelve still fit


# ---------------------------------------------------------------- 3D
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1
    return (a[0] / ln, a[1] / ln, a[2] / ln)


class Camera:
    """Perspective camera: world y is up. fit() places the projection on the screen."""

    def __init__(self, pos, target, fov=1.0):
        self.pos = pos
        self.fwd = norm(sub(target, pos))
        self.right = norm(cross(self.fwd, (0, 1, 0)))
        self.up = cross(self.right, self.fwd)
        self.k, self.ox, self.oy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.pos)
        z = dot(d, self.fwd)
        return dot(d, self.right) / z, -dot(d, self.up) / z, z

    def fit(self, pts, box):
        """Uniform scale and offset so the projected pts fill box (x0, y0, x1, y1), centred."""
        xs, ys = zip(*[self.raw(p)[:2] for p in pts])
        x0, y0, x1, y1 = box
        self.k = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
        self.ox = (x0 + x1) / 2 - self.k * (max(xs) + min(xs)) / 2
        self.oy = (y0 + y1) / 2 - self.k * (max(ys) + min(ys)) / 2

    def p(self, pt):
        x, y, _ = self.raw(pt)
        return (self.ox + self.k * x, self.oy + self.k * y)

    def depth(self, pt):
        return dot(sub(pt, self.pos), self.fwd)


def ring3(c, r, n=40, axis="y"):
    out = []
    for j in range(n):
        a = 2 * math.pi * j / n
        if axis == "y":
            out.append((c[0] + r * math.cos(a), c[1], c[2] + r * math.sin(a)))
        else:   # axis z: a wheel facing the camera
            out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2]))
    return out


def split_arc(pts2, front=True):
    """Of a projected closed ring, the arc between its left and right extremes that is lower
    on screen (front=True, nearer a camera above) or higher (front=False)."""
    n = len(pts2)
    il = min(range(n), key=lambda j: pts2[j][0])
    ir = max(range(n), key=lambda j: pts2[j][0])
    a = [pts2[(il + k) % n] for k in range(((ir - il) % n) + 1)]
    b = [pts2[(ir + k) % n] for k in range(((il - ir) % n) + 1)]
    b = b[::-1]                       # both run left -> right
    ma = sum(p[1] for p in a) / len(a)
    mb = sum(p[1] for p in b) / len(b)
    lower, upper = (a, b) if ma > mb else (b, a)
    return lower if front else upper


# ---------------------------------------------------------------- primitives
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.4:
        out.pop()
    return out


def thin(pts, limit=62):
    if len(pts) <= limit:
        return pts
    step = len(pts) / limit
    return [pts[int(k * step)] for k in range(limit)]


def clip_segment(a, b, poly):
    """Parts of segment a-b inside polygon poly (even-odd)."""
    ts = [0.0, 1.0]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / den
        u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / den
        if 0 < t < 1 and 0 <= u <= 1:
            ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        tm = (t0 + t1) / 2
        m = (a[0] + dx * tm, a[1] + dy * tm)
        if inside(m, poly) and t1 - t0 > 1e-3:
            out.append(((a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)))
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def add(self, s):
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = thin(dedupe(pts))
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def shape(self, pts, stroke, sw, fill=G0):
        """A closed outline over a black body (hidden-line)."""
        self.poly(pts, fill, stroke, sw)

    def ribbon(self, pts, w, colour):
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        i = 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + 31], w, colour)
            i += 30

    def _piece(self, seg, w, colour):
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0 or k == len(seg) - 1:
                j0, j1 = (0, 1) if k == 0 else (k - 1, k)
                dx, dy = seg[j1][0] - seg[j0][0], seg[j1][1] - seg[j0][1]
                ln = math.hypot(dx, dy) or 1
                nx, ny, m = -dy / ln, dx / ln, 1.0
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                n1, n2 = (-ay / la, ax / la), (-by / lb, bx / lb)
                sx, sy = n1[0] + n2[0], n1[1] + n2[1]
                ls = math.hypot(sx, sy)
                if ls < 1e-6:
                    sx, sy, ls = n1[0], n1[1], 1
                nx, ny = sx / ls, sy / ls
                m = min(1 / max(nx * n1[0] + ny * n1[1], 0.2), 2.5)
            left.append((x + nx * h * m, y + ny * h * m))
            right.append((x - nx * h * m, y - ny * h * m))
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        self._piece([a, b], w, colour)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def hatch(self, poly, colour, gap=4.0, w=HAIR):
        """45-degree hairlines >= 3 px apart, clipped to poly."""
        xs, ys = zip(*poly)
        lo, hi = min(xs) - max(ys), max(xs) - min(ys)
        c = lo + (gap - (lo % gap))
        while c < hi:
            a, b = (c + min(ys) - 2, min(ys) - 2), (c + max(ys) + 2, max(ys) + 2)
            for s, e in clip_segment(a, b, poly):
                if math.dist(s, e) > 2.5:
                    self.line(s, e, w, colour)
            c += gap

    def svg(self):
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>ringer · subject pass 02 · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, val in enumerate(VALUES):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{val}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])

    def write(self, variant):
        d = HERE / variant
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(self.svg())


# A bell's outside profile (r, z): r as a fraction of the lip radius, z from crown (0) to lip (1).
BELL = [(0.42, 0.0), (0.52, 0.04), (0.56, 0.14), (0.58, 0.32), (0.62, 0.5),
        (0.70, 0.66), (0.84, 0.82), (0.96, 0.93), (1.0, 1.0)]
# Wall thickness along the profile, as a fraction of the lip radius (thin waist, thick sound bow).
WALL = [0.07, 0.07, 0.06, 0.055, 0.055, 0.06, 0.09, 0.13, 0.11]
BELL_H = 1.45   # height / lip radius


# ======================================================================
# v1 · one detail at large scale · detailed line art
# The sallies at eye height in the ringing chamber. Ropes run up out of the
# frame to the ceiling and down out of it to the tail ends: only the striped
# woollen grips and the ropes between are drawn. A sally's height is its
# bell's place in the change: the lowest is being pulled now.
# ======================================================================
def clip_y(a, b, y0=21.0, y1=219.0):
    """Screen segment a-b cut to the band y0..y1 (a projected straight line stays straight)."""
    (ax, ay), (bx, by) = a, b
    t0, t1 = 0.0, 1.0
    if abs(by - ay) > 1e-9:
        ta, tb = (y0 - ay) / (by - ay), (y1 - ay) / (by - ay)
        t0, t1 = max(0.0, min(ta, tb)), min(1.0, max(ta, tb))
    return (ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)


def v1():
    fr = Frame("v1 sallies at large scale")
    pitch = 4.0
    xs = [(i - (N - 1) / 2) * pitch for i in range(N)]
    amp = 4.0 * (PACE / 2.0) ** -0.35            # pace: how far the wave of sallies spreads
    rs, rr, L = 0.95, 0.24, 7.4                  # sally radius, rope radius, sally length
    cam = Camera((0, 3.0, -34), (0, 1.2, 0))
    span_x = xs[-1] + pitch / 2
    cam.fit([(-span_x, -L / 2 - 0.2, 0), (span_x, amp + L / 2 + 0.2, 0)], (24, 28, 456, 210))

    def sally_y(b):
        y = (PLACE[b] - 1) / (N - 1) * amp
        if PLACE[b] == 1:
            y += GAP * 1.6                       # stroke: the leading sally is held up
        return y

    def radius_at(t):
        taper = 1.0
        if t < taper:
            return rr + (rs - rr) * math.sin(t / taper * math.pi / 2)
        if t > L - taper:
            return rr + (rs - rr) * math.sin((L - t) / taper * math.pi / 2)
        return rs

    for i in range(N):
        b = i + 1                                 # ropes hang in bell order round the room
        x = xs[i]
        y0 = sally_y(b) - L / 2
        bright = PLACE[b] == 1
        edge, sw = (G7, SUBJ) if bright else (G5, LINE)
        band = G5 if bright else G3
        rope = G4 if bright else G3
        # rope above to the ceiling and below to the tail end, both out of the frame
        for ya, yb in ((y0 + L - 0.15, 30.0), (-30.0, y0 + 0.15)):
            la, lb = clip_y(cam.p((x - rr, ya, 0)), cam.p((x - rr, yb, 0)))
            ra, rb = clip_y(cam.p((x + rr, ya, 0)), cam.p((x + rr, yb, 0)))
            fr.shape([la, lb, rb, ra], rope, HAIR)
            # the rope's lay: short diagonal hairlines across it, 6 px apart
            n = int(abs(lb[1] - la[1]) // 6)
            for k in range(1, n):
                t = k / n
                pl = (la[0] + (lb[0] - la[0]) * t, la[1] + (lb[1] - la[1]) * t)
                pr = (ra[0] + (rb[0] - ra[0]) * t, ra[1] + (rb[1] - ra[1]) * t)
                fr.line((pl[0] + 1.2, pl[1] + 1.6), (pr[0] - 1.2, pr[1] - 1.6), HAIR, G2)
        # the sally: its tapered silhouette over black
        ts = [k * L / 40 for k in range(41)]
        left = [cam.p((x - radius_at(t), y0 + t, 0)) for t in ts]
        right = [cam.p((x + radius_at(t), y0 + t, 0)) for t in ts]
        fr.shape(left + right[::-1], edge, sw)
        # the tufted wool: helical stripes, front halves only, the way they wrap the grip
        hp = 1.9                                  # helix pitch (world units per turn)
        y = 1.05
        k = 0
        while y + hp / 2 < L - 1.0:
            pts = []
            for j in range(25):
                th = math.pi + math.pi * j / 24     # front half: z < 0, toward the camera
                pts.append(cam.p((x + rs * 0.97 * math.cos(th), y0 + y + hp * (th - math.pi) / (2 * math.pi),
                                  rs * 0.97 * math.sin(th))))
            fr.ribbon(pts, LINE if k % 3 == 0 else HAIR, edge if k % 3 == 0 else band)
            y += hp / 4
            k += 1
    fr.write("v1")


# ======================================================================
# v2 · the object in the name · hidden-line 3D
# The bells themselves, hung along one frame side and standing in the order
# they strike in this change: the nearest strikes now, the row runs back into
# the tower. A swap is two bells exchanging places along the beam.
# ======================================================================
def bell_hidden(fr, cam, base, R, edge, sw, inner):
    """A hanging bell (mouth down) as a hidden-line solid of revolution: black body, outline, bands."""
    rings = []
    for (rf, z) in BELL:
        c = (base[0], base[1] - z * BELL_H * R, base[2])
        rings.append([cam.p(p) for p in ring3(c, rf * R, 40)])
    lefts = [min(r, key=lambda p: p[0]) for r in rings]
    rights = [max(r, key=lambda p: p[0]) for r in rings]
    lip = split_arc(rings[-1], front=True)
    crown_back = split_arc(rings[0], front=False)
    body = lefts + lip[1:-1] + rights[::-1] + crown_back[::-1][1:-1]
    fr.shape(body, edge, sw)
    fr.ribbon(split_arc(rings[0], front=True), HAIR, inner)          # crown edge
    for k in (4, 6):                                                # waist and sound-bow lines
        fr.ribbon(split_arc(rings[k], front=True), HAIR, inner)
    # the lip's inner edge: a ring just inside the lip, front half, shows the wall's thickness
    c = (base[0], base[1] - BELL_H * R, base[2])
    fr.ribbon(split_arc([cam.p(p) for p in ring3(c, R * 0.9, 40)], front=True), HAIR, inner)


def box(fr, cam, c, hx, hy, hz, edge, sw):
    """An axis-aligned box drawn as its camera-facing faces over black."""
    faces = []
    for ax, sgn in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
        n = [0, 0, 0]
        n[ax] = sgn
        h = (hx, hy, hz)
        fc = list(c)
        fc[ax] += sgn * h[ax]
        if dot(tuple(n), sub(cam.pos, tuple(fc))) <= 0:
            continue
        o = [a for a in range(3) if a != ax]
        pts = []
        for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = list(fc)
            p[o[0]] += s1 * h[o[0]]
            p[o[1]] += s2 * h[o[1]]
            pts.append(cam.p(tuple(p)))
        faces.append(pts)
    for pts in faces:
        fr.shape(pts, edge, sw)


def v2():
    fr = Frame("v2 the bells in striking order")
    R0 = 1.0
    spacing = 3.0 * (PACE / 2.0) ** -0.3          # pace: distance between blows, drawn as distance between bells
    lead = GAP * spacing                          # stroke: an empty bay before the first bell at handstroke
    xs = [lead + k * spacing for k in range(N)]   # place k+1 stands at xs[k]
    top = 0.0                                     # crown height (all bells hang from one beam)
    zr = 2.2                                      # the far frame side
    cam = Camera((-5.0, 4.6, -8.5), (xs[-1] * 0.5, -1.0, 0.6))
    Rmax = R0 * bell_scale(N)
    key = [(-1.8, top + 0.9, -1.4), (xs[-1] + 2.2, top + 0.9, zr + 0.3),
           (-Rmax, top - 0.4 - BELL_H * Rmax, -Rmax), (xs[-1] + 1.5, top - BELL_H * Rmax, 0)]
    cam.fit(key, (18, 30, 462, 208))

    # the far frame side: a long timber the gudgeons bear on
    x0, x1 = -2.0, xs[-1] + 2.4
    box(fr, cam, ((x0 + x1) / 2, top + 0.55, zr), (x1 - x0) / 2, 0.32, 0.22, G3, LINE)
    # its bearings: a short block under each gudgeon
    for k in range(N):
        box(fr, cam, (xs[k], top + 0.55, zr - 0.3), 0.3, 0.26, 0.08, G3, HAIR)
    # an empty bay at the front when the handstroke gap is open (hatched: there but not in use)
    if lead > 0.05:
        pts = [cam.p((xs[0] - lead + 0.3, top + 0.24, zr - 0.38)), cam.p((xs[0] - 0.3, top + 0.24, zr - 0.38)),
               cam.p((xs[0] - 0.3, top + 0.86, zr - 0.38)), cam.p((xs[0] - lead + 0.3, top + 0.86, zr - 0.38))]
        fr.hatch(pts, G2)

    order = sorted(range(N), key=lambda k: -cam.depth((xs[k], top, 0)))   # far to near
    for k in order:
        b = ROW[k]
        R = R0 * bell_scale(b)
        now = k == 0
        edge, sw, inner = (G7, SUBJ, G5) if now else (G4, LINE, G3)
        # gudgeon pin from the headstock to the far side, then the headstock on the crown
        a, c2 = cam.p((xs[k], top + 0.55, 0.9 * R)), cam.p((xs[k], top + 0.55, zr - 0.38))
        fr.line(a, c2, LINE, G3)
        box(fr, cam, (xs[k], top + 0.3, 0), 0.26 * R, 0.28, 0.8 * R, edge if now else G4, LINE)
        bell_hidden(fr, cam, (xs[k], top, 0), R, edge, sw, inner)
    fr.write("v2")


# ======================================================================
# v3 · the mechanism · bold closed outlines
# The wheels of the ring, face on, each rope wound round its wheel from the
# garter hole and falling to the sally. A wheel turns to how far through its
# turn its bell is in this change; the one about to strike is bright.
# ======================================================================
def v3():
    fr = Frame("v3 wheels and ropes")
    pitch = 440 / N
    r = min(31.0, pitch * 0.42)
    cy = 84.0
    sally_y = 176 - 26 * math.log2(PACE / 0.5) / 4    # pace: sallies ride up as the ropes are taken in
    slide = GAP * 14                                 # stroke: the sliders run out
    # the frame head the sliders run under: one long timber
    fr.shape([(8, cy - r - 21), (472, cy - r - 21), (472, cy - r - 14), (8, cy - r - 14)], G3, LINE)
    for i in range(N):
        b = i + 1
        cx = 20 + pitch * (i + 0.5)
        place = PLACE[b]
        now = place == 1
        edge, sw = (G7, 2.5) if now else (G5, SUBJ)
        dim = G6 if now else G4
        # garter hole angle: place 1 is wound furthest, about to pull off; the last barely started
        g = math.radians(25 + (place - 1) / (N - 1) * 130)    # screen angle, y down; rope leaves at 180 deg
        # slider and its runner, above the wheel, with the stay resting toward it
        fr.shape([(cx + 2 + slide, cy - r - 13), (cx + 16 + slide, cy - r - 13),
                  (cx + 16 + slide, cy - r - 8), (cx + 2 + slide, cy - r - 8)], G4, LINE)
        # rim: two closed outlines
        fr.circle(cx, cy, r, G0, edge, sw)
        fr.circle(cx, cy, r - 6, G0, dim, LINE)
        # spokes: closed bars from hub to rim, turned with the wheel
        for s in range(4):
            a = g + math.pi / 4 + s * math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = -uy * 1.8, ux * 1.8
            p0 = (cx + ux * 7, cy + uy * 7)
            p1 = (cx + ux * (r - 6), cy + uy * (r - 6))
            fr.shape([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                      (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)], dim, LINE)
        # stay: a bar from the hub out past the rim, fixed to the wheel
        a = g + math.pi * 0.85
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy * 2.2, ux * 2.2
        p0, p1 = (cx + ux * 7, cy + uy * 7), (cx + ux * (r + 9), cy + uy * (r + 9))
        fr.shape([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                  (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)], dim, LINE)
        fr.circle(cx, cy, 7, G0, edge, sw)
        # the rope wound in the rim's groove from the garter hole round the bottom to the left side
        rr = r + 3.5
        steps = 28
        arc = [(cx + rr * math.cos(g + (math.pi - g) * k / steps), cy + rr * math.sin(g + (math.pi - g) * k / steps))
               for k in range(steps + 1)]
        fr.ribbon(arc, 3.0, edge)
        # garter hole: a bold closed mark where the rope goes through the rim
        hx, hy = cx + (r - 3) * math.cos(g), cy + (r - 3) * math.sin(g)
        fr.circle(hx, hy, 3.2, G0, edge, LINE)
        # the rope falls from the left side of the wheel to the sally and on out of the frame
        x = cx - rr
        fr.shape([(x - 1.5, cy), (x + 1.5, cy), (x + 1.5, 219), (x - 1.5, 219)], edge if now else G4, LINE)
        # sally: a bold closed lozenge on the rope
        sh = 30
        fr.shape([(x, sally_y - sh / 2 - 4), (x + 5, sally_y - sh / 2 + 2), (x + 5, sally_y + sh / 2 - 2),
                  (x, sally_y + sh / 2 + 4), (x - 5, sally_y + sh / 2 - 2), (x - 5, sally_y - sh / 2 + 2)],
                 edge, SUBJ if now else LINE)
    fr.write("v3")


# ======================================================================
# v4 · the material the sound acts on · cutaway section
# The bronze, cut through: every bell of the ring hung in a two-tier frame
# and sectioned on its centre plane, so the cut walls show the thin waist and
# the thick sound bow the clapper strikes. Each clapper hangs as far from
# its strike point as its bell is from striking in this change.
# ======================================================================
def v4():
    fr = Frame("v4 the ring cut through")
    tiers = 2
    per = math.ceil(N / tiers)
    swing = math.radians(24) * (PACE / 2.0) ** -0.25   # pace: how far the clappers stand off across the row
    xw = 444 / per
    Rt = min(0.44 * xw, 50.0)                          # tenor lip radius in px
    s_ten = bell_scale(N)
    for t in range(tiers):
        bells = [b for b in range(1, N + 1) if (b - 1) // per == t]
        lip_y = 110 if t == 0 else 207                 # the biggest bell of the tier reaches this
        Rbig = Rt * bell_scale(bells[-1]) / s_ten
        crown = lip_y - BELL_H * Rbig                  # one gudgeon height per tier: crowns level
        shift = (-0.1 if t == 0 else 0.1) * xw
        x0 = 18 + shift
        # the tier's sill: a long timber in section-elevation, its end grain hatched
        sill = [(x0, crown - 12), (x0 + xw * len(bells), crown - 12), (x0 + xw * len(bells), crown - 7),
                (x0, crown - 7)]
        fr.shape(sill, G3, LINE)
        for j, b in enumerate(bells):
            R = Rt * bell_scale(b) / s_ten
            cx = x0 + xw * (j + 0.5)
            H = BELL_H * R
            place = PLACE[b]
            now = place == 1
            edge = G7 if now else G5
            # headstock in section on the crown, hatched as cut timber
            hs = [(cx - 0.4 * R, crown - 7), (cx + 0.4 * R, crown - 7), (cx + 0.4 * R, crown),
                  (cx - 0.4 * R, crown)]
            fr.shape(hs, G3, LINE)
            fr.hatch(hs, G2, 4.0)
            lip_in = (BELL[-1][0] - 0.17) * R
            # the far inside of the bell, seen through the cut: its lip edge, hairline
            fr.line((cx - lip_in, crown + H - 0.6), (cx + lip_in, crown + H - 0.6), HAIR, G2)
            # the cut walls, left and right: closed sections, hatched as cut bronze
            for side in (-1, 1):
                outer = [(cx + side * rf * R, crown + z * H) for rf, z in BELL]
                inn = [(cx + side * (rf - w) * R, crown + z * H + w * R * 0.4) for (rf, z), w in zip(BELL, WALL)]
                inn[-1] = (cx + side * lip_in, crown + H)
                sec = outer + inn[::-1]
                fr.shape(sec, edge, SUBJ if now else LINE)
                fr.hatch(sec, G4 if now else G3, 3.5)
            # the crown in section
            cr = [(cx - BELL[0][0] * R, crown), (cx + BELL[0][0] * R, crown),
                  (cx + (BELL[1][0] - WALL[1]) * R, crown + 0.06 * H + 2), (cx - (BELL[1][0] - WALL[1]) * R, crown + 0.06 * H + 2)]
            fr.shape(cr, edge, LINE)
            fr.hatch(cr, G3, 3.5)
            # the clapper, hung from the crown staple, swung off its strike point by how far the bell is from striking
            pivot = (cx, crown + 0.06 * H + 4)
            a = -swing * (1 - (place - 1) / (N - 1)) - (GAP * 0.12 if now else 0)
            Lc = H * 0.8
            ball_r = max(3.5, 0.14 * R)
            ux, uy = math.sin(a), math.cos(a)
            bx, by = pivot[0] + Lc * ux, pivot[1] + Lc * uy
            nx, ny = -uy * 1.4, ux * 1.4
            fr.shape([(pivot[0] + nx, pivot[1] + ny), (bx + nx, by + ny), (bx - nx, by - ny),
                      (pivot[0] - nx, pivot[1] - ny)], G6 if now else G4, HAIR)
            fr.circle(bx, by, ball_r, G0, G7 if now else G4, SUBJ if now else LINE)
            fr.circle(pivot[0], pivot[1], 2.0, G0, G4, HAIR)
    fr.write("v4")


# ======================================================================
# v5 · one scene with one subject · exploded view
# The tower pulled apart along its axis: the bell-chamber floor with the ring
# on it lifted clear of the ringing-chamber floor, the ropes falling between
# them, guide lines at the corners. On the ringing floor a line threads the
# ropes in the order they strike in this change.
# ======================================================================
def v5():
    fr = Frame("v5 the tower pulled apart")
    S = 5.0                                   # half the tower's inside width
    gap = 7.0 + GAP * 3.0                     # stroke: the tower pulls further apart
    yb = 0.0                                  # ringing-chamber floor
    yt = yb + gap                             # bell-chamber floor
    rc = 3.3                                  # ringing circle radius
    sally_h = 1.1 + 1.6 * math.log2(PACE / 0.5) / 4   # pace: sallies ride up the ropes
    cam = Camera((-15, 10.5, -22), (0, 3.4, 0))
    key = [(sx * S, y, sz * S) for sx in (-1, 1) for sz in (-1, 1) for y in (yb - 0.6, yt + 2.2)]
    cam.fit(key, (40, 26, 440, 212))
    th = 0.45

    def slab(y, edge):
        """A floor slab: top face, two visible sides, over black."""
        c = [(-S, y, -S), (S, y, -S), (S, y, S), (-S, y, S)]
        d = [(x, yy - th, z) for x, yy, z in c]
        P = [cam.p(p) for p in c]
        Q = [cam.p(p) for p in d]
        fr.shape([P[0], P[1], Q[1], Q[0]], G3, LINE)       # front face (z = -S)
        fr.shape([P[3], P[0], Q[0], Q[3]], G3, LINE)       # left face (x = -S)
        fr.shape(P, edge, LINE)
        return P

    def ang(b):
        return math.pi / 2 + 2 * math.pi * (b - 1) / N   # the ropes fall clockwise from the treble

    rope_pos = {b: (rc * math.cos(ang(b)), rc * math.sin(ang(b))) for b in range(1, N + 1)}

    # explode guides at the four corners, short ribbons between the slabs
    def guide(sx, sz):
        y = yb + 0.2
        while y < yt - th - 0.4:
            fr.line(cam.p((sx * S, y, sz * S)), cam.p((sx * S, min(y + 0.45, yt - th - 0.3), sz * S)), HAIR, G2)
            y += 0.85

    for sx, sz in ((1, 1), (-1, 1)):
        guide(sx, sz)

    # ringing-chamber floor with its boxes' outline (the circle the ringers stand on), hairline
    slab(yb, G4)
    circ = [cam.p((rc * 1.28 * math.cos(2 * math.pi * k / 48), yb, rc * 1.28 * math.sin(2 * math.pi * k / 48)))
            for k in range(48)]
    fr.ribbon(circ + circ[:1], HAIR, G2)
    # the method: one line threading the rope feet in striking order, closed back to the first
    feet = [cam.p((rope_pos[b][0], yb, rope_pos[b][1])) for b in ROW]
    fr.ribbon(feet + feet[:1], SUBJ, G7)
    for k, b in enumerate(ROW):
        p = feet[k]
        fr.circle(p[0], p[1], 3.0 if k == 0 else 2.2, G0, G7 if k == 0 else G5, LINE)

    # ropes from the bell floor down to the ringing floor, drawn far to near; sallies on them
    order = sorted(range(1, N + 1), key=lambda b: -cam.depth((rope_pos[b][0], 0, rope_pos[b][1])))
    for sx, sz in ((1, -1), (-1, -1)):
        guide(sx, sz)
    for b in order:
        x, z = rope_pos[b]
        top = cam.p((x, yt - th, z))
        foot = cam.p((x, yb + 0.9, z))
        now = PLACE[b] == 1
        fr.line(top, foot, LINE if now else HAIR, G6 if now else G4)
        s0, s1 = cam.p((x, yb + sally_h, z)), cam.p((x, yb + sally_h + 1.3, z))
        w = 2.6
        fr.shape([(s0[0] - w, s0[1]), (s0[0] - w, s1[1] + 2), (s0[0], s1[1]), (s0[0] + w, s1[1] + 2),
                  (s0[0] + w, s0[1]), (s0[0], s0[1] + 2)], G6 if now else G4, LINE)

    # bell-chamber floor, lifted, with the ring standing on it: each bell a hidden-line bell, mouth down
    slab(yt, G4)
    bell_order = sorted(range(1, N + 1), key=lambda b: -cam.depth((rope_pos[b][0], yt, rope_pos[b][1])))
    for b in bell_order:
        x, z = rope_pos[b]
        R = 0.62 * bell_scale(b) / bell_scale(N) * (6 / max(N, 6)) ** 0.5 * 1.7
        now = PLACE[b] == 1
        base = (x, yt + BELL_H * R + 0.05, z)
        bell_hidden(fr, cam, base, R, G6 if now else G4, SUBJ if now else LINE, G5 if now else G3)
    fr.write("v5")


if __name__ == "__main__":
    for fn in (v1, v2, v3, v4, v5):
        fn()
    print("row:", "".join(map(str, ROW)), "places:", PLACE)
