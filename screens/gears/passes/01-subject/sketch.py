#!/usr/bin/env python3
"""Subject-pass sketches for gears: five rest frames, one per direction.

    python3 screens/gears/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: ratio 3:2, teeth 8, mesh 100 %, scale maj, no
notes, not muted. Sketches for picking a subject, not device frames: every part
is static artwork (no bound nodes yet); each candidate's risks argue the budget.

The model all five draw from (definition.json):
  driver wheel A has `teeth` teeth; follower B has teeth x ratio (8 x 3/2 = 12).
  Both share a tooth pitch, so one tooth pair meshes per step. Step k meshes
  A's tooth k mod 8 with B's tooth k mod 12; A's revolution (8 steps) against
  B's (12 steps) is the 3:2 polyrhythm, repeating every 24 steps.
  mesh: each tooth has a fixed length (Euclidean rank); only teeth long enough
  to reach the other wheel at the set engagement sound. 100 % = every tooth.
  scale: the meshing pair's degree is (i + j) mod 14, read in the scale.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HEADER = [("ratio", "3:2"), ("teeth", "8"), ("mesh", "100%"), ("scale", "maj")]

# ------------------------------------------------------------------ model
TEETH_A = 8
RATIO = (3, 2)
TEETH_B = TEETH_A * RATIO[0] // RATIO[1]          # 12
MESH = 1.0
SCALE = [0, 2, 4, 5, 7, 9, 11]                     # maj
CYCLE = TEETH_A * TEETH_B // math.gcd(TEETH_A, TEETH_B)  # 24


def euclid_rank(n: int) -> list[int]:
    """Rank of each tooth (0 = longest): the order teeth drop out as mesh falls,
    spread evenly round the wheel (Euclidean)."""
    order: list[int] = []
    for k in range(1, n + 1):
        hits = {(i * n) // k for i in range(k)}
        for h in sorted(hits):
            if h not in order:
                order.append(h)
    for i in range(n):
        if i not in order:
            order.append(i)
    return [order.index(i) for i in range(n)]


RANK_A = euclid_rank(TEETH_A)
RANK_B = euclid_rank(TEETH_B)


def sounds(rank: int, n: int, mesh: float = MESH) -> bool:
    return rank < round(mesh * n)


def step(k: int):
    i, j = k % TEETH_A, k % TEETH_B
    deg = (i + j) % 14
    return i, j, deg, sounds(RANK_A[i], TEETH_A) and sounds(RANK_B[j], TEETH_B)


def semis(deg: int) -> int:
    return SCALE[deg % 7] + 12 * (deg // 7)


# ---------------------------------------------------------------- helpers
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.3):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(p)
    return out


def poly(pts, fill, stroke="none", sw=None):
    pts = dedupe(pts)
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.3:
        pts = pts[:-1]
    d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def rect(x, y, w, h, fill, stroke="none", sw=None):
    s = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def circle(cx, cy, r, fill, stroke="none", sw=None):
    s = f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"'
    if stroke != "none":
        s += f' stroke-width="{sw}"'
    return s + "/>"


def text(x, y, s, fill=G4, size=10):
    return (f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" stroke="none" '
            f'font-family="{FONT}" font-size="{size}px">{s}</text>')


def ribbon(pts, w, fill):
    """An open polyline as thin closed ribbons (filled, no stroke), <= 62 points each."""
    pts = dedupe(pts, 0.6)
    if len(pts) < 2:
        return ""
    out = []
    i = 0
    while i < len(pts) - 1:
        out.append(_ribbon(pts[i:i + 31], w, fill))
        i += 30
    return "\n".join(out)


def _ribbon(pts, w, fill):
    h = w / 2
    n = len(pts)
    left, right = [], []
    for k in range(n):
        if k == 0 or k == n - 1:
            a, b = (pts[0], pts[1]) if k == 0 else (pts[-2], pts[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, h
        else:
            ax, ay = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            bx, by = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1, n2 = (-ay / la, ax / la), (-by / lb, bx / lb)
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            m = h / max(0.5, nx * n1[0] + ny * n1[1])
        x, y = pts[k]
        left.append((x + nx * m, y + ny * m))
        right.append((x - nx * m, y - ny * m))
    return poly(left + right[::-1], fill)


def seg(p, q, w, fill):
    return ribbon([p, q], w, fill)


def arc(cx, cy, rx, ry, a0, a1, step_deg=6.0):
    n = max(2, int(abs(a1 - a0) / math.radians(step_deg)) + 1)
    return [(cx + rx * math.cos(a0 + (a1 - a0) * t / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * t / (n - 1))) for t in range(n)]


def dashdot_circle(cx, cy, r, w, fill, dash=9.0, gap=3.0, dot=2.0, ry=None):
    """A centre-line circle (long dash, dot) as ribbons, by arc length."""
    ry = r if ry is None else ry
    out = []
    circ = 2 * math.pi * r
    period = dash + gap + dot + gap
    n = max(1, round(circ / period))
    per = 2 * math.pi / n
    for k in range(n):
        a0 = k * per
        a1 = a0 + per * dash / period
        b0 = a1 + per * gap / period
        b1 = b0 + per * dot / period
        out.append(ribbon(arc(cx, cy, r, ry, a0, a1, 4), w, fill))
        out.append(ribbon(arc(cx, cy, r, ry, b0, b1, 4), w, fill))
    return out


def dashdot_line(p, q, w, fill, dash=9.0, gap=3.0, dot=2.0):
    L = math.dist(p, q)
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    out, t = [], 0.0
    while t < L:
        for length in (dash, dot):
            e = min(L, t + length)
            if e - t > 1.0:
                out.append(seg((p[0] + ux * t, p[1] + uy * t), (p[0] + ux * e, p[1] + uy * e), w, fill))
            t = e + gap
            if t >= L:
                break
    return out


def gear_outline(cx, cy, n, r_root, r_tip, rot=0.0, tip_lengths=None, ry_k=1.0):
    """Spur gear outline: 4 points a tooth (root, flank, tip, flank), flat tips."""
    pts = []
    pitch = 2 * math.pi / n
    for t in range(n):
        a = rot + t * pitch
        rt = r_tip if tip_lengths is None else r_root + tip_lengths[t]
        for da, r in ((-0.30, r_root), (-0.16, rt), (0.16, rt), (0.30, r_root)):
            ang = a + da * pitch
            pts.append((cx + r * math.cos(ang), cy + ry_k * r * math.sin(ang)))
    return pts


def frame(body: list[str]) -> str:
    steps = [G0, G1, G2, G3, G4, G5, G6, G7]
    hdr = [rect(60 * i, 0, 60, 20, c) for i, c in enumerate(steps)]
    for i, (t, v) in enumerate(HEADER):
        ink = "#CBCBCB" if i < 2 else G0
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<g id="preview_canvas">', rect(0, 0, W, H, G0), '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *[b for b in body if b],
        '</svg>', ""])


# ------------------------------------------- v1  P14 Loom · engineering schematic
def v1():
    """The last four revolutions of wheel A woven as cloth: one warp thread per
    tooth of A, one row per revolution, a slab raised where a mesh sounded, its
    height the note. B's index tooth is a centre line stepping across the rows."""
    body = []
    PX, ROWS = 28, 4
    DZX, DZY = 18, 30                  # one row back = 18 px right, 30 px up

    def P(x, y, z):
        return (152 + x + z * DZX, 190 - y - z * DZY)

    edge = [G7, G5, G4, G3]
    # warp threads (hairline) and weft baselines
    for i in range(TEETH_A):
        x = i * PX + 8
        body.append(seg(P(x, 0, -0.35), P(x, 0, ROWS - 0.25), 1, G2))
    for r in range(ROWS):
        body.append(seg(P(-8, 0, r + 0.22), P(TEETH_A * PX - 4, 0, r + 0.22), 1, G1))

    SW, SD = 16, 0.45
    tops = {}
    for r in reversed(range(ROWS)):            # back to front
        for i in range(TEETH_A):
            k = (ROWS - 1 - r) * TEETH_A + i   # row 3 oldest, row 0 the revolution now
            _, j, deg, on = step(k)
            x0, z0 = i * PX, r
            h = 5 + 1.25 * semis(deg)
            if not on:
                h = 2
            fr = [P(x0, 0, z0), P(x0 + SW, 0, z0), P(x0 + SW, h, z0), P(x0, h, z0)]
            rt = [P(x0 + SW, 0, z0), P(x0 + SW, 0, z0 + SD), P(x0 + SW, h, z0 + SD), P(x0 + SW, h, z0)]
            tp = [P(x0, h, z0), P(x0 + SW, h, z0), P(x0 + SW, h, z0 + SD), P(x0, h, z0 + SD)]
            sw = 1.5 if r == 0 else 1.2
            body.append(poly(fr, G0, edge[r], sw))
            body.append(poly(rt, G0, edge[r], sw))
            body.append(poly(tp, G7 if r == 0 else G0, edge[r], sw))
            if j == 0:
                tops[r] = P(x0 + SW / 2, h, z0 + SD / 2)
    # B's index tooth: a centre line (dash-dot) through the slabs where B's tooth 0 meshed
    pts = [tops[r] for r in sorted(tops)]
    for a, b in zip(pts, pts[1:]):
        body += dashdot_line(a, b, 1.2, G6, dash=7, gap=3, dot=2)
    lead = (pts[-1][0] + 2, pts[-1][1] - 12)
    body.append(seg(pts[-1], lead, 1, G4))
    body.append(text(lead[0] + 3, lead[1] - 1, "b0", G5))
    # row callouts
    labels = ["rev", "−1", "−2", "−3"]
    for r in range(ROWS):
        x, y = P(TEETH_A * PX + 2, 0, r + 0.2)
        body.append(text(x, y + 3, labels[r], G4 if r else G5))
    # dimension line: the thread count
    a, b = P(0, 0, -0.42), P((TEETH_A - 1) * PX + SW, 0, -0.42)
    y = 208
    body.append(seg((a[0], y), (b[0], y), 1, G4))
    body.append(seg((a[0], y - 4), (a[0], y + 4), 1, G4))
    body.append(seg((b[0], y - 4), (b[0], y + 4), 1, G4))
    body.append(rect((a[0] + b[0]) / 2 - 14, y - 6, 28, 12, G0))
    body.append(text((a[0] + b[0]) / 2 - 10, y + 4, "8 t", G5))
    # the drive: wheel A and B as schematic pitch circles feeding the warp
    ca, ra = (40, 150), 18
    cb, rb = (ca[0] + ra + 27, ca[1] - 0), 27
    for (c, r, n) in ((ca, ra, TEETH_A), (cb, rb, TEETH_B)):
        body += dashdot_circle(c[0], c[1], r, 1, G4, dash=7, gap=2.5, dot=1.5)
        for t in range(n):
            a = -math.pi / 2 + t * 2 * math.pi / n
            body.append(seg((c[0] + (r + 1.5) * math.cos(a), c[1] + (r + 1.5) * math.sin(a)),
                            (c[0] + (r + 5) * math.cos(a), c[1] + (r + 5) * math.sin(a)), 1.2, G5))
        body.append(seg((c[0] - 4, c[1]), (c[0] + 4, c[1]), 1, G4))
        body.append(seg((c[0], c[1] - 4), (c[0], c[1] + 4), 1, G4))
    body.append(text(ca[0] - 4, ca[1] - ra - 10, "a", G5))
    body.append(text(cb[0] - 4, cb[1] - rb - 10, "b", G5))
    # shaft from A to the warp beam
    body.append(seg((ca[0] + 4, ca[1] + ra + 9), (P(-10, 0, 0)[0], ca[1] + ra + 9), 1, G3))
    body.append(seg((ca[0], ca[1] + 5), (ca[0], ca[1] + ra + 9), 1, G3))
    return frame(body)


# -------------------------------------------- v2  P5 Field and figure · oscilloscope
def v2():
    """X-Y scope: wheel A's angle on x, B's on y. The trace is a Lissajous
    figure whose lobes are the ratio; each mesh is a bead on it."""
    body = []
    # field: the graticule laid down as a receding floor (static, low grey)
    vx, vy = 240, 52
    y_near, y_far = 196, 122
    def floor_y(d):  # d 0 near .. 1 far, perspective spacing
        return vy + (y_near - vy) / (1 + 2.2 * d)
    ys = [floor_y(d / 6) for d in range(7)]
    ys = [y for y in ys if y >= y_far]
    for y in ys:
        k = (y - vy) / (y_near - vy)
        body.append(seg((vx - 250 * k, y), (vx + 250 * k, y), 1, G1))
    for c in range(-10, 11):
        x_near = vx + c * 26
        k_far = (ys[-1] - vy) / (y_near - vy)
        x_far = vx + c * 26 * k_far
        body.append(seg((x_near, y_near), (x_far, ys[-1]), 1, G1))
    # scope axes with minor ticks (behind the trace)
    cx, cy, ax_, ay_ = 240, 104, 118, 58
    body.append(seg((cx - ax_ - 10, cy), (cx + ax_ + 10, cy), 1, G2))
    body.append(seg((cx, cy - ay_ - 8), (cx, cy + ay_ + 8), 1, G2))
    for t in range(-12, 13):
        x = cx + t * 10
        if t:
            body.append(seg((x, cy - 2.5), (x, cy + 2.5), 1, G2))
    for t in range(-6, 7):
        y = cy + t * 10
        if t and abs(t * 10) <= ay_ + 6:
            body.append(seg((cx - 2.5, y), (cx + 2.5, y), 1, G2))
    # figure: x = sin(3 * 2pi t), y = sin(2 * 2pi t)  (A turns 3x while B turns 2x)
    def L(t):
        return (cx + ax_ * math.sin(RATIO[0] * 2 * math.pi * t),
                cy - ay_ * math.sin(RATIO[1] * 2 * math.pi * t))
    trace = [L(t / 360) for t in range(361)]
    body.append(ribbon(trace, 2.2, G7))
    # beads: one per step of the 24-step cycle; downbeats of A and B larger
    for k in range(CYCLE):
        i, j, deg, on = step(k)
        x, y = L(k / CYCLE)
        big = (i == 0) or (j == 0)
        s = 7 if big else 5
        body.append(rect(x - s / 2, y - s / 2, s, s, G0, G5 if big else G4, 1.5))
    # activity strip: the 24 steps, bar height = the meshing pair's note
    x0, dx = 96, 12
    for k in range(CYCLE):
        i, j, deg, on = step(k)
        h = 4 + semis(deg) * 0.45
        ink = G5 if (i == 0 or j == 0) else G3
        body.append(rect(x0 + k * dx, 212 - h, 4, h, ink))
    # readouts, scope style
    body.append(text(10, 36, "x  a · 8", G4))
    body.append(text(10, 48, "y  b · 12", G4))
    body.append(text(426, 36, "x–y", G4))
    return frame(body)


# ----------------------------------------------- v3  P12 Orrery · typeset diagram
def v3():
    """The two wheels as two orbits round one arbor, seen from above at a tilt:
    inner orbit A with 8 tooth stations, outer orbit B with 12, and the outer
    index circle of 12 semitones with the scale's degrees set on it. The mesh
    line runs from the arbor toward the reader; both planets sit on it at k=0."""
    body = []
    cx, cy, S = 240, 122, 98.0
    EL = math.radians(27)              # camera elevation above the orbital plane
    SY = math.sin(EL)

    def P(x, z, y=0.0):                # world: x right, z away, y up
        return (cx + S * x, cy - S * SY * z - S * math.cos(EL) * y)

    RA, RB, RC = 0.82, 0.82 * RATIO[0] / RATIO[1], 2.0
    hub_r = 0.16
    hub = P(0, 0, 0.12)

    def orbit(r, back: bool):
        # back half: z > 0 (angles 0..pi measured with z = r sin a)
        a0, a1 = (0, math.pi) if back else (math.pi, 2 * math.pi)
        return [P(r * math.cos(a), r * math.sin(a)) for a in
                [a0 + (a1 - a0) * t / 40 for t in range(41)]]

    def station(r, n, t):
        a = -math.pi / 2 + t * 2 * math.pi / n     # tooth 0 on the mesh line, toward the reader
        return P(r * math.cos(a), r * math.sin(a)), math.sin(a)

    # back halves, behind the arbor
    body.append(ribbon(orbit(RC, True), 1, G2))
    body.append(ribbon(orbit(RB, True), 1.5, G4))
    body.append(ribbon(orbit(RA, True), 1.5, G4))
    # scale circle: 12 semitone ticks, the scale's degrees as dots
    def scale_marks(front: bool):
        out = []
        for s in range(12):
            a = -math.pi / 2 + s * 2 * math.pi / 12
            if (math.sin(a) < 0) != front:
                continue
            p = P(RC * math.cos(a), RC * math.sin(a))
            q = P((RC + 0.07) * math.cos(a), (RC + 0.07) * math.sin(a))
            out.append(seg(p, q, 1.2, G3))
            if s in SCALE:
                out.append(circle(p[0], p[1], 3, G4, G0, 1.5))
        return out
    body += scale_marks(False)
    for r, n in ((RA, TEETH_A), (RB, TEETH_B)):
        for t in range(n):
            p, sa = station(r, n, t)
            if sa > 0:
                body.append(circle(p[0], p[1], 2.6, G4, G0, 1.5))
    # arbor
    body.append(seg(P(0, 0, 0), P(0, 0, 0.62), 1.2, G4))
    body.append(circle(hub[0], hub[1], S * hub_r * 0.62, G0, G5, 1.5))
    # mesh line: from the arbor toward the reader, through tooth 0 of both
    m0, m1 = P(0, -hub_r * 0.8), P(0, -RC + 0.04)
    body.append(seg(m0, m1, 1, G3))
    # front halves
    body.append(ribbon(orbit(RA, False), 1.5, G4))
    body.append(ribbon(orbit(RB, False), 1.5, G4))
    body.append(ribbon(orbit(RC, False), 1, G2))
    body += scale_marks(True)
    for r, n in ((RA, TEETH_A), (RB, TEETH_B)):
        for t in range(1, n):
            p, sa = station(r, n, t)
            if sa <= 0:
                body.append(circle(p[0], p[1], 2.6, G4, G0, 1.5))
    # the planets now meshing (step 0): A's tooth 0 and B's tooth 0
    for r, rad in ((RA, 5.5), (RB, 6.5)):
        p, _ = station(r, 1, 0)
        body.append(circle(p[0], p[1], rad, G7, G0, 1.5))
    # typeset labels with leaders
    def label(world_r, ang_deg, s, dx, dy):
        a = math.radians(ang_deg)
        p = P(world_r * math.cos(a), world_r * math.sin(a))
        q = (p[0] + dx, p[1] + dy)
        return [seg(p, q, 1, G3), text(q[0] + (2 if dx > 0 else -12), q[1] + 3, s, G5)]
    body += label(RA, 160, "a", -20, -24)
    body += label(RB, 150, "b", -24, -20)
    body += label(RC, 20, "scale", 18, -12)
    body.append(text(400, 212, "fig. 1", G4))
    return frame(body)


# -------------------------------------------- v4  P13 Capture · orthographic elevation
def v4():
    """Two spur gears in front elevation. Each tooth's length is its weight; a
    tooth meshes and plays only if it reaches across the gap between the wheels,
    so mesh is the centre distance. Scale sits apart, on a plain octave."""
    body = []
    ra, rb = 40.0, 60.0                # pitch radii, 8 and 12 teeth at one module
    gap = (1 - MESH) * 14
    ca = (104.0, 122.0)
    cb = (ca[0] + ra + rb + gap, ca[1])
    # tooth lengths from their rank: longest 9 px, shortest 4 px
    la = [9 - 5 * RANK_A[t] / (TEETH_A - 1) for t in range(TEETH_A)]
    lb = [9 - 5 * RANK_B[t] / (TEETH_B - 1) for t in range(TEETH_B)]
    # centre lines, long, past both wheels
    body += dashdot_line((ca[0] - ra - 22, ca[1]), (cb[0] + rb + 22, cb[1]), 1, G3, dash=12, gap=3, dot=2)
    for c, r in ((ca, ra), (cb, rb)):
        body += dashdot_line((c[0], c[1] - r - 20), (c[0], c[1] + r + 20), 1, G3, dash=12, gap=3, dot=2)
    # wheels: hidden-line bodies (black fill), tooth outlines at line weight
    rota = 0.0                          # A's tooth 0 points at the mesh point (right)
    rotb = math.pi + math.pi / TEETH_B  # B's tooth space sits opposite, so the teeth interleave
    for c, r, n, rot, ls in ((ca, ra, TEETH_A, rota, la), (cb, rb, TEETH_B, rotb, lb)):
        root = r - 4
        body.append(poly(gear_outline(c[0], c[1], n, root, 0, rot, [4 + l for l in ls]), G0, G5, 2))
        body += dashdot_circle(c[0], c[1], r, 1, G3, dash=8, gap=3, dot=1.5)
        body.append(circle(c[0], c[1], 9, G0, G4, 1.5))                      # bore
        body.append(rect(c[0] - 2.5, c[1] - 12, 5, 4, G0, G4, 1.5))          # keyway
        body.append(circle(c[0], c[1], r * 0.55, G0, G2, 1.5))               # web relief
        body.append(circle(c[0], c[1], 9, G0, G4, 1.5))
    # the meshing pair at the mesh point: A's tooth 0, filled bright
    t0 = gear_outline(ca[0], ca[1], TEETH_A, ra - 4, 0, rota, [4 + l for l in la])[0:4]
    body.append(poly(t0, G7, G7, 1))
    # the capture line: how far a tooth of A must reach to engage B (hidden-line dashes)
    re_ = math.dist(ca, cb) - (ra - 4) - 3.5
    for k in range(-3, 4):
        a0 = math.pi + math.radians(k * 7 - 2.2)
        body.append(ribbon(arc(cb[0], cb[1], re_, re_, a0, a0 + math.radians(4.4), 1.5), 1.2, G6))
    # timing marks: tooth 0 of each wheel
    for c, r, ang in ((ca, ra, 0.0), (cb, rb, math.pi)):
        p = (c[0] + (r - 12) * math.cos(ang), c[1] + (r - 12) * math.sin(ang))
        body.append(circle(p[0], p[1], 2.5, G5, G0, 1))
    # dimension: the centre distance (what mesh sets)
    y = 206
    body.append(seg((ca[0], y), (cb[0], y), 1, G4))
    for x in (ca[0], cb[0]):
        body.append(seg((x, y - 4), (x, y + 4), 1, G4))
    mid = (ca[0] + cb[0]) / 2
    body.append(rect(mid - 16, y - 6, 32, 12, G0))
    body.append(text(mid - 13, y + 4, "c 100", G5))
    body.append(text(ca[0] - 4, ca[1] - ra - 18, "a", G5))
    body.append(text(cb[0] + 6, cb[1] - rb - 10, "b", G5))
    # scale: a plain one-octave keyboard, lower right, the scale's notes dotted
    kx, ky, kw, kh = 342, 150, 17, 46
    whites = [0, 2, 4, 5, 7, 9, 11]
    for n, s in enumerate(whites):
        body.append(rect(kx + n * kw, ky, kw, kh, G0, G3, 1.5))
    for s, pos in ((1, 1), (3, 2), (6, 4), (8, 5), (10, 6)):
        body.append(rect(kx + pos * kw - 5, ky, 10, 27, G1, G3, 1.5))
    for s in SCALE:
        if s in whites:
            x = kx + whites.index(s) * kw + kw / 2
            y2 = ky + kh - 9
        else:
            x = kx + {1: 1, 3: 2, 6: 4, 8: 5, 10: 6}[s] * kw
            y2 = ky + 19
        body.append(circle(x, y2, 3 if s else 4, G5, G0, 1))
    body.append(text(342, 142, "elev. a–b", G4))
    return frame(body)


# --------------------------------------------- v5  P9 One-bit ink · survey plan
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(inside, level, x0, y0, x1, y1, cell=2, ink=G7):
    out = []
    for gy in range(int(y0) // cell, int(y1) // cell + 1):
        run = None
        for gx in range(int(x0) // cell, int(x1) // cell + 2):
            x, y = gx * cell + cell / 2, gy * cell + cell / 2
            lit = inside(x, y) and (BAYER[gy % 4][gx % 4] + 0.5) / 16 < level
            if lit and run is None:
                run = gx
            if not lit and run is not None:
                out.append(rect(run * cell, gy * cell, (gx - run) * cell, cell, ink))
                run = None
    return out


def v5():
    """Wheel A as a surveyed plot in one-bit ink: each tooth a lot, numbered,
    its tone the mesh; the web dithered. Two glyphs: the ratio as a two-row
    scale bar (3 against 2), the scale as a stepped section profile."""
    body = []
    c = (178.0, 120.0)
    r_root, r_tip, r_bore = 56.0, 76.0, 15.0
    pitch = 2 * math.pi / TEETH_A
    rot = -math.pi / 2
    # web: static, 25 % dither, inside a 1 px black gutter
    def in_web(x, y):
        d = math.dist((x, y), c)
        return r_bore + 5 < d < r_root - 4
    body += dither(in_web, 0.25, c[0] - r_root, c[1] - r_root, c[0] + r_root, c[1] + r_root)
    # outline of the whole wheel (2 px), hub ring
    body.append(poly(gear_outline(c[0], c[1], TEETH_A, r_root, r_tip, rot), "none", G7, 2))
    body.append(circle(c[0], c[1], r_root - 2, "none", G7, 2))
    body.append(circle(c[0], c[1], r_bore + 2, "none", G7, 2))
    # lots: each tooth a flat 50 % plane (moving part: flat grey standing for dither)
    for t in range(TEETH_A):
        a = rot + t * pitch
        q = []
        for da, r in ((-0.27, r_root + 1), (-0.15, r_tip - 3.5), (0.15, r_tip - 3.5), (0.27, r_root + 1)):
            q.append((c[0] + r * math.cos(a + da * pitch), c[1] + r * math.sin(a + da * pitch)))
        on = sounds(RANK_A[t], TEETH_A)
        body.append(poly(q, G4 if on else G0, "none"))
        # bearing tick and lot number outside the tip
        p0 = (c[0] + (r_tip + 3) * math.cos(a), c[1] + (r_tip + 3) * math.sin(a))
        p1 = (c[0] + (r_tip + 8) * math.cos(a), c[1] + (r_tip + 8) * math.sin(a))
        body.append(seg(p0, p1, 2, G7))
        lx = c[0] + (r_tip + 15) * math.cos(a) - 3
        ly = c[1] + (r_tip + 15) * math.sin(a) + 4
        body.append(text(lx, ly, str(t + 1), G7))
    # the mesh station: where the lot under it plays (tooth 1, top)
    # survey traverse from the bore to the station, 2 px
    body.append(seg((c[0], c[1] - r_bore - 3), (c[0], c[1] - r_root + 3), 2, G7))
    # glyph: ratio as a scale bar, two rows (3 against 2)
    bx, by, bw = 330, 166, 132
    for row, n in ((0, RATIO[0]), (1, RATIO[1])):
        for s in range(n):
            x = bx + s * bw / n
            y = by + row * 10
            fill = G7 if (s + row) % 2 == 0 else G0
            body.append(rect(x, y, bw / n, 8, fill, G7, 2))
    body.append(text(bx, by + 34, "0", G7))
    body.append(text(bx + bw - 12, by + 34, "24", G7))
    # glyph: the scale as a section profile (each step rises by its interval), upper right
    sx, sy, run = 330, 112, 18
    steps = [SCALE[k + 1] - SCALE[k] for k in range(6)] + [12 - SCALE[6]]
    levels, y = [], sy
    for st in steps:
        levels.append(y)
        y -= st * 3
    pts = [(sx, sy)]
    for k, lv in enumerate(levels):
        pts.append((sx + k * run, lv)) if k else None
        pts.append((sx + (k + 1) * run, lv))
    pts.append((sx + len(levels) * run, y))
    pts.append((sx + len(levels) * run + 6, y))
    body.append(ribbon(pts, 2, G7))

    def in_section(px, py):
        k = int((px - sx) // run)
        if not (0 <= k < len(levels)) or px - sx - k * run < 3 or (k + 1) * run - (px - sx) < 3:
            return False
        return levels[k] + 4 < py < sy + 3
    body += dither(in_section, 0.5, sx, sy - 40, sx + len(levels) * run, sy + 4)
    body.append(seg((sx - 4, sy + 6), (sx + len(levels) * run + 6, sy + 6), 2, G7))
    return frame(body)


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "rest.svg").write_text(fn())
        print(d / "rest.svg")


if __name__ == "__main__":
    main()
