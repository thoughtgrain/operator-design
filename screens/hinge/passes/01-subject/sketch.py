#!/usr/bin/env python3
"""Subject-pass sketches for hinge: five rest frames, one per direction.

    python3 screens/hinge/passes/01-subject/sketch.py

Writes v1..v5/rest.svg (480 x 220, stock header kept as preview scaffolding).
Every frame shows the defaults: hold 200 ms, creak 0 %, swing 3.2 s, mix 50 %.
These are sketches for picking a subject, not device frames: parts are static
artwork (no bound nodes yet), so the budget is argued in each candidate's risks.

The model all five draw from (the DSP in brief.md):
  the door catches the last `hold` seconds of the send; one pass through the
  slice is one swing, played alternately forwards and backwards; the swing's
  amplitude decays to rest with T60 = `swing`; `creak` makes the playhead
  stick and slip as it slows; `mix` is wet against dry.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 480, 220

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"

# defaults (definition.json), as 0..1 positions and as units
HOLD, CREAK, SWING, MIX = 0.5, 0.0, 0.5, 0.5
HOLD_S = 0.02 * 100 ** HOLD          # 0.2 s slice
SWING_S = 0.5 * 40 ** SWING          # 3.16 s to rest
HEADER = [("hold", "200ms"), ("creak", "0"), ("swing", "3.2s"), ("mix", "50")]


def swing_ratio(swing=SWING_S, hold=HOLD_S):
    """Amplitude kept from one swing to the next (one swing = one pass of the slice)."""
    tau = swing / 6.91
    r = math.exp(-hold / tau)
    # the drawings show ~5 swings, so compress the real ratio into a readable range
    return 0.45 + 0.5 * r ** 0.25


# ----------------------------------------------------------------- helpers
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= 0.3:
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
    pts = dedupe(pts)
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


def dashes(pts, w, fill, on=5.0, off=4.0):
    """A dashed line as separate short ribbons (no stroke-dasharray on the device)."""
    out, cur, acc, drawing = [], [pts[0]], 0.0, True
    seg = on
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = 0.0
        while L - t > 1e-6:
            step = min(seg - acc, L - t)
            t += step
            acc += step
            p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
            if drawing:
                cur.append(p)
            if acc >= seg - 1e-6:
                if drawing and len(cur) > 1:
                    out.append(ribbon(cur, w, fill))
                drawing = not drawing
                seg = on if drawing else off
                acc = 0.0
                cur = [p]
    if drawing and len(cur) > 1 and math.dist(cur[0], cur[-1]) > 1.5:
        out.append(ribbon(cur, w, fill))
    return "\n".join(out)


def arc(cx, cy, r, a0, a1, step_deg=3.0):
    """Points on a circle; angles in degrees, 0 = up (screen -y), clockwise positive."""
    n = max(2, int(abs(a1 - a0) / step_deg) + 1)
    return [(cx + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cy - r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def polar(cx, cy, r, a):
    return (cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a)))


def hatch_rect(x0, y0, x1, y1, gap, w, fill, slope=1):
    """45-degree section hatching inside a rectangle, as ribbons."""
    out = []
    span = (x1 - x0) + (y1 - y0)
    k = gap
    while k < span:
        # line x - slope*y = c, walk its intersections with the box
        pts = []
        for t in range(0, 2):
            pass
        if slope > 0:
            a = (x0 + k, y0) if k <= x1 - x0 else (x1, y0 + k - (x1 - x0))
            b = (x0, y0 + k) if k <= y1 - y0 else (x0 + k - (y1 - y0), y1)
        else:
            a = (x1 - k, y0) if k <= x1 - x0 else (x0, y0 + k - (x1 - x0))
            b = (x1, y0 + k) if k <= y1 - y0 else (x1 - (k - (y1 - y0)), y1)
        if math.dist(a, b) > 2.5:
            out.append(ribbon([a, b], w, fill))
        k += gap
    return "\n".join(out)


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
        *body,
        '</svg>', ""])


def leaf_len(hold=HOLD, lo=50.0, hi=130.0):
    """Door leaf length on screen from hold's 0..1 position (log time, so linear in position)."""
    return lo + (hi - lo) * hold


# ---------------------------------------------- v1  P4 · survey plan
def v1():
    """The doorway in plan, one plan per swing, stacked level above level up the hinge pin."""
    body = []
    L = leaf_len()                       # 90 px leaf
    r = swing_ratio()
    n = 5
    hx0, hy0 = 100, 174                   # the newest swing's hinge, at the front
    rise = 16 + 16 * MIX                 # mix: how far the swings stand apart up the pin
    dx = 16
    squash = 0.42                        # plan oblique: plan depth drawn at 0.42
    A0 = 64.0                            # the oldest (widest) swing, degrees off the closed line

    def P(hx, hy, u, v):
        return (hx + u, hy - squash * v)

    # the hinge pin: the stack's axis, from the newest plan up to the oldest
    top = (hx0 + dx * (n - 1), hy0 - rise * (n - 1))
    body.append(ribbon([(hx0, hy0), top], 1.2, G3))
    for k in reversed(range(n)):         # k = 0 newest (front), n-1 oldest (back)
        hx, hy = hx0 + dx * k, hy0 - rise * k
        amp = A0 * r ** (n - 1 - k)
        side = 1 if k % 2 == 0 else -1   # back and forth
        ink = [G7, G5, G4, G3, G3][k]
        # the swept sector, black, so nearer plans hide the ones behind
        sector = [P(hx, hy, 0, 0)] + [P(hx, hy, L * math.cos(math.radians(a)), L * math.sin(math.radians(a)))
                                       for a in [-amp + 2 * amp * i / 30 for i in range(31)]]
        body.append(poly(sector, G0))
        rim = sector[1:]
        if k == 0:
            body.append(ribbon(rim, 1.2, G4))
        else:
            body.append(dashes(rim, 1.2, ink, 4, 3))
        # wall either side of the opening: survey double line
        for ua, ub in ((-34, -4), (L + 4, L + 30)):
            body.append(ribbon([P(hx, hy, ua, 0), P(hx, hy, ub, 0)], 1.2, G2 if k else G4))
        # leaf at this swing's extreme
        a = side * amp
        tip = P(hx, hy, L * math.cos(math.radians(a)), L * math.sin(math.radians(a)))
        body.append(ribbon([(hx, hy), tip], 2.5 if k == 0 else 1.5, ink))
        body.append(circle(hx, hy, 3.5 if k == 0 else 2.5, G7 if k == 0 else G0, ink, 1.5))
        # level label on the left, like a reduced level on a section of plans
        body.append(text(hx - 64, hy + 3.5, f"s{n - k}", G4 if k == 0 else G3))
        if k == n - 1:
            body.append(text(tip[0] + 6, tip[1] + 3, f"{int(A0)}°", G4))
    # scale bar under the newest plan: the leaf's length is the slice
    for i in range(5):
        x = hx0 + i * L / 4
        body.append(ribbon([(x, 206), (x, 211 if i % 2 == 0 else 209)], 1.2, G3))
    body.append(ribbon([(hx0, 206), (hx0 + L, 206)], 1.2, G3))
    body.append(text(hx0 + L + 6, 211, "0.2 s", G4))
    return frame(body)


# ------------------------------------------ v2  P10 · patent section
def slice_wave(u, hold=HOLD):
    """The caught slice, u in 0..1 across it; a longer hold catches more cycles."""
    cycles = 0.5 + 3.0 * hold
    return (0.75 * math.sin(2 * math.pi * cycles * u)
            + 0.25 * math.sin(2 * math.pi * cycles * 2.3 * u + 0.7)) * (0.7 + 0.3 * math.sin(math.pi * u))


def v2():
    """FIG. 1: a section through a louvred leaf; each row of slats is one pass of the slice."""
    body = []
    n_slats = 22
    x0, pitch = 66, 17
    rows_y = [70, 120, 170]
    r = swing_ratio()
    slat = 10 + 24 * MIX                  # mix: slat length, 10 px (dry) .. 34 px (wet)
    # stiles cut in section, hatched (hinge stile left, latch stile right)
    for (sx0, sx1) in ((34, 48), (436, 450)):
        body.append(poly([(sx0, 40), (sx1, 40), (sx1, 200), (sx0, 200)], G0, G4, 1.5))
        body.append(hatch_rect(sx0 + 0.8, 40.8, sx1 - 0.8, 199.2, 4.5, 1, G3))
    # hinge knuckle in section, on the hinge stile's outer face
    body.append(circle(24, 120, 7, G0, G5, 1.5))
    body.append(circle(24, 120, 2.5, G5))
    # rails, top and bottom, as section lines
    body.append(ribbon([(48, 42), (436, 42)], 1.2, G3))
    body.append(ribbon([(48, 198), (436, 198)], 1.2, G3))
    for ri, ry in enumerate(rows_y):
        amp = 70.0 * r ** (2 * ri)              # later passes swing less
        direction = 1 if ri % 2 == 0 else -1    # back and forth: alternate rows run reversed
        ink = [G7, G5, G3][ri]
        w = [2.5, 2, 1.5][ri]
        for i in range(n_slats):
            u = i / (n_slats - 1)
            if direction < 0:
                u = 1 - u
            a = amp * slice_wave(u)
            if CREAK > 0:
                a = round(a / (40 * CREAK)) * 40 * CREAK
            cx = x0 + i * pitch
            p0 = polar(cx, ry, slat / 2, a)
            p1 = polar(cx, ry, slat / 2, a + 180)
            body.append(ribbon([p1, p0], w, ink))
            body.append(circle(cx, ry, 1.6, G0, ink, 1.5))
    # patent numerals with leaders
    body.append(text(392, 214, "FIG. 1", G4))
    body.append(text(458, 58, "10", G4))
    body.append(ribbon([(451, 54), (456, 54)], 1.2, G3))
    body.append(text(x0 + pitch * 2 - 4, 214, "12", G4))
    body.append(ribbon([(x0 + pitch * 2, 204), (x0 + pitch * 2, rows_y[2] + slat / 2 + 3)], 1.2, G3))
    body.append(text(14, 150, "14", G4))
    body.append(ribbon([(20, 140), (23, 128)], 1.2, G3))
    return frame(body)


# --------------------------------------- v3  P15 · hidden-line isometric
def v3():
    """A floor of square cells in isometric; the door's swing is swept into it."""
    body = []
    s = 20.0
    ox, oy = 240, -14                    # screen position of world (0, 0)

    def P(i, j):
        return (ox + (i - j) * s, oy + (i + j) * s / 2)

    # the hinge sits on a floor cell; the door closes along +i and swings both ways
    hi, hj = 3.0, 7.0
    R = 2.5 + 5.0 * HOLD                 # hold: the leaf's reach, in cells (2.5 .. 7.5)
    r = swing_ratio()
    span = 15 + 100 * (r - 0.45) / 0.5   # swing: how far round the fan stays lit, degrees each side
    rise = 3 + 10 * MIX                  # mix: how far caught cells stand up from the floor
    cells = []
    for i in range(-12, 24):
        for j in range(-12, 24):
            quad = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)]
            xs = [q[0] for q in quad]
            ys = [q[1] for q in quad]
            if min(xs) < 6 or max(xs) > 474 or min(ys) < 30 or max(ys) > 214:
                continue
            ci, cj = i + 0.5 - hi, j + 0.5 - hj
            dist = math.hypot(ci, cj)
            ang = math.degrees(math.atan2(cj, ci))
            state = 0
            if dist <= R + 0.2 and abs(ang) <= span + 6:
                if dist > R - 0.8:
                    state = 3                       # the rim: where the leaf's edge travels, lit
                elif abs(abs(ang) - span) < 14 and dist > 1.2:
                    state = 2                       # the two extremes the leaf reached, mid
                elif int(dist) % 2 == 0 and dist > 1.2:
                    state = 1                       # earlier, quieter passes: the grey layer
            if dist < 0.75:
                state = 4                           # the hinge cell
            cells.append((i + j, i, j, quad, state))
    cells.sort()
    for _, i, j, quad, state in cells:
        if state == 0:
            body.append(poly(quad, G0, G2, 1.5))
            continue
        h = {1: 3, 2: rise * 0.6, 3: rise, 4: rise + 4}[state]
        top = [(x, y - h) for x, y in quad]
        left = [quad[3], quad[2], top[2], top[3]]
        right = [quad[2], quad[1], top[1], top[2]]
        lf, rf, tf, te = {1: (G1, G1, G0, G3), 2: (G3, G2, G5, G5),
                          3: (G4, G3, G7, G7), 4: (G3, G2, G0, G6)}[state]
        body.append(poly(left, lf, lf, 0.3))
        body.append(poly(right, rf, rf, 0.3))
        body.append(poly(top, tf, te, 1.5))
    return frame(body)


# --------------------------------------------- v4  P1 · star atlas
def v4():
    """The hinge cut in section at the pole of a chart; the swing plotted as an ephemeris."""
    body = []
    cx, cy = 240, 202
    Rg = 172                              # graduated rim
    R = 80 + 70 * HOLD                    # hold: leaf length, and where the track starts
    r = swing_ratio()
    n_half = 3 + int(10 * (r - 0.45) / 0.5)    # swing: how many extremes before it rests
    # graduation: outer rim, ticks every 5 degrees, labels every 30
    body.append(ribbon(arc(cx, cy, Rg, -90, 90, 2), 1.2, G3))
    body.append(ribbon(arc(cx, cy, Rg - 6, -90, 90, 2), 1.2, G2))
    for a in range(-90, 91, 5):
        if a % 30 == 0:
            body.append(ribbon([polar(cx, cy, Rg - 12, a), polar(cx, cy, Rg, a)], 1.2, G3))
        else:
            body.append(ribbon([polar(cx, cy, Rg - 6, a), polar(cx, cy, Rg, a)], 1.2, G2))
    for a in (-60, -30, 30, 60):
        lx, ly = polar(cx, cy, Rg + 5, a)
        body.append(text(lx - (20 if a < 0 else -2), ly + (2 if abs(a) == 60 else -1), f"{abs(a)}°", G4))
    # a parallel at half the leaf, hairline
    body.append(ribbon(arc(cx, cy, R * 0.5, -90, 90, 3), 1.2, G1))
    # ephemeris: the leaf tip's path; radius falls with time, the angle swings and decays
    A0 = 60.0
    r_end = 38.0
    track, extremes = [], []
    steps = 60 * n_half
    for q in range(steps + 1):
        t = q / 60                        # in half-swings
        amp = A0 * r ** t
        a = amp * math.cos(math.pi * t)
        rad = r_end + (R - 6 - r_end) * (1 - t / n_half)
        track.append(polar(cx, cy, rad, a))
        if q % 60 == 0:
            extremes.append((t, amp, polar(cx, cy, rad, a), a))
    body.append(ribbon(track, 1.2, G4))
    for k, (t, amp, (x, y), a) in enumerate(extremes):
        mag = (1.8 + 3.0 * (amp / A0)) * (0.6 + 0.8 * MIX)   # mix: magnitude (star size)
        body.append(circle(x, y, mag, G6, G0, 1.5))
        if k in (0, 1):
            sec = t * HOLD_S
            body.append(text(x + (8 if a > 0 else -30), y + 4, f"{sec:.1f} s", G4))
    # the hinge in section: knuckle, pin, the frame leaf on the far side
    body.append(poly([(cx - 46, cy + 4), (cx - 12, cy + 4), (cx - 12, cy + 9), (cx - 46, cy + 9)], G0, G4, 1.5))
    body.append(circle(cx, cy, 12, G0, G5, 1.5))
    body.append(circle(cx, cy, 4.5, G7))
    # the door leaf: the subject, closed along the meridian at rest
    body.append(poly([(cx - 3, cy - 12), (cx + 3, cy - 12), (cx + 3, cy - R), (cx - 3, cy - R)], G0, G7, 2))
    body.append(text(cx + 9, cy - R + 9, "leaf", G4))
    body.append(text(12, 34, "hinge, swing chart", G4))
    return frame(body)


# --------------------------------- v5  P11 · engineering schematic (stretch)
def v5():
    """The door in elevation, its parts stacked on the hinge axis: hinges, closer, leaf."""
    body = []
    jl, jr = 192, 296                    # inner faces of the jambs
    head, floor = 54, 204
    # frame: jambs and head as double outlines, the floor line
    body.append(poly([(jl - 9, head - 18), (jr + 9, head - 18), (jr + 9, floor), (jr, floor), (jr, head),
                      (jl, head), (jl, floor), (jl - 9, floor)], G0, G4, 1.5))
    body.append(ribbon([(140, floor), (348, floor)], 1.2, G3))
    # leaf, ajar: mix opens it, so its seen width shrinks and a gap opens at the latch side
    open_deg = 10 + 60 * MIX
    lw = (jr - jl - 2) * math.cos(math.radians(open_deg))
    lx0, lx1 = jl + 1, jl + 1 + lw
    body.append(poly([(lx0, head + 2), (lx1, head + 2), (lx1, floor - 3), (lx0, floor - 3)], G0, G7, 2))
    # the leaf's edge, seen because it stands open
    edge = 5 * math.sin(math.radians(open_deg)) + 2
    body.append(poly([(lx1, head + 2), (lx1 + edge, head + 4), (lx1 + edge, floor - 3), (lx1, floor - 3)], G0, G4, 1.5))
    # boards: hold sets how many (3 .. 12), drawn as hairlines across the leaf
    n_boards = 3 + round(9 * HOLD)
    for b in range(1, n_boards):
        x = lx0 + lw * b / n_boards
        body.append(ribbon([(x, head + 5), (x, floor - 6)], 1.2, G3))
    # ledges: two rails across the boards
    for y in (head + 34, floor - 34):
        body.append(poly([(lx0 + 4, y), (lx1 - 4, y), (lx1 - 4, y + 7), (lx0 + 4, y + 7)], G0, G5, 1.5))
    # three hinges on the hinge axis: barrels of knuckles; creak pulls the knuckles apart
    gapk = 1 + 6 * CREAK
    for hy in (head + 18, (head + floor) / 2, floor - 22):
        k = 5
        kh = 5
        total = k * kh + (k - 1) * gapk
        y = hy - total / 2
        for q in range(k):
            body.append(poly([(jl - 4, y), (jl + 4, y), (jl + 4, y + kh), (jl - 4, y + kh)], G0, G5, 1.5))
            y += kh + gapk
        # strap on the leaf
        body.append(poly([(jl + 5, hy - 3), (jl + 24, hy - 2), (jl + 24, hy + 2), (jl + 5, hy + 3)], G0, G4, 1.5))
    # hinge axis centreline, dash-dot, through the knuckles
    body.append(dashes([(jl, head - 16), (jl, floor + 10)], 1.2, G3, 9, 4))
    # closer on the head, its arm folded back to the leaf; swing turns the arm (valve)
    cbx, cby = jl + 6, head - 14
    body.append(poly([(cbx, cby), (cbx + 42, cby), (cbx + 42, cby + 9), (cbx, cby + 9)], G0, G5, 1.5))
    piv = (cbx + 36, cby + 4.5)
    arm_deg = 40 + 60 * SWING            # swing: arm angle from the closer
    elbow = (piv[0] + 30 * math.sin(math.radians(arm_deg)), piv[1] - 30 * math.cos(math.radians(arm_deg)))
    shoe = (lx0 + lw * 0.3, head + 10)
    body.append(ribbon([piv, elbow], 2, G5))
    body.append(ribbon([elbow, shoe], 2, G5))
    for p in (piv, elbow, shoe):
        body.append(circle(p[0], p[1], 2.5, G0, G5, 1.5))
    # dimension: the leaf's width is the slice
    dy = 212
    body.append(ribbon([(lx0, dy), (lx1, dy)], 1.2, G4))
    body.append(poly([(lx0, dy), (lx0 + 6, dy - 2.5), (lx0 + 6, dy + 2.5)], G4))
    body.append(poly([(lx1, dy), (lx1 - 6, dy - 2.5), (lx1 - 6, dy + 2.5)], G4))
    body.append(text(lx1 + 10, dy + 3.5, "200 ms", G4))
    # callout balloons with leaders
    calls = [((jl - 4, head + 18), (150, 72), "1"), (((cbx + 42), cby + 4), (338, 38), "2"),
             ((lx0 + lw * 0.5, 120), (338, 120), "3")]
    for (px, py), (bx, by), lab in calls:
        body.append(ribbon([(px, py), (bx + (8 if bx < px else -8), by)], 1.2, G3))
        body.append(circle(bx, by, 8, G0, G4, 1.5))
        body.append(text(bx - 3, by + 3.5, lab, G5))
    return frame(body)


def main():
    for name, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        out = HERE / name / "rest.svg"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(fn(), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
