#!/usr/bin/env python3
"""hinge v4 cleanup: the star-atlas swing chart, tidied. Writes v4/clean.svg.

    python3 screens/hinge/passes/01-subject/v4/clean.py [hold=.. creak=.. swing=.. mix=..] [OUT.svg]

Model and svg helpers copied from ../sketch.py (unchanged). Not picked yet: this
stays in the pass folder.
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



# ---------------------------------------------- v4, cleaned: star atlas
CX, CY = 240, 200          # the pole: the hinge pin
RG = 170                   # graduated rim
A0 = 60.0                  # first extreme of the swing, degrees off the meridian


def v4_clean(hold=HOLD, swing=SWING, mix=MIX):
    body = []
    R = 80 + 70 * hold                         # hold: leaf length, where the track starts
    r = swing_ratio(0.5 * 40 ** swing, 0.02 * 100 ** hold)
    n_half = 3 + round(10 * swing)             # swing: turning points before rest, 3 .. 13
    r_end = 0.3 * R                            # where the track rests: keeps turns >= 3 px apart

    # the chart: a double rim graduated every 5 degrees, longer every 30, and the horizon;
    # no figures (the header carries the values)
    body.append(ribbon(arc(CX, CY, RG, -90, 90, 2), 1.2, G3))
    body.append(ribbon(arc(CX, CY, RG - 6, -90, 90, 2), 1.0, G2))
    for a in range(-90, 91, 5):
        if a % 30 == 0:
            body.append(ribbon([polar(CX, CY, RG - 12, a), polar(CX, CY, RG, a)], 1.2, G3))
        else:
            body.append(ribbon([polar(CX, CY, RG - 6, a), polar(CX, CY, RG, a)], 1.0, G2))
    body.append(ribbon([(CX - RG, CY), (CX - 44, CY)], 1.0, G2))
    body.append(ribbon([(CX + 16, CY), (CX + RG, CY)], 1.0, G2))

    # ephemeris: the leaf tip's path, radius falling with time, angle swinging and decaying
    track, extremes = [], []
    per = 48
    for q in range(per * n_half + 1):
        t = q / per                             # in half-swings
        amp = A0 * r ** t
        a = amp * math.cos(math.pi * t)
        rad = r_end + (R - 8 - r_end) * (1 - t / n_half)
        track.append(polar(CX, CY, rad, a))
        if q % per == 0:
            extremes.append((amp, polar(CX, CY, rad, a)))
    body.append(ribbon(track, 1.2, G4))
    # turning points as stars, sized by loudness (mix: magnitude); a black ring breaks the track
    for amp, (x, y) in extremes:
        mag = max(1.6, (1.4 + 2.2 * (amp / A0)) * (0.6 + 0.8 * mix))   # never under ~3 px
        body.append(circle(x, y, mag, G5, G0, 1.5))

    # the hinge in section at the pole: the frame's leaf along the horizon, knuckle and pin
    body.append(poly([(CX - 42, CY - 3), (CX - 8, CY - 3), (CX - 8, CY + 3), (CX - 42, CY + 3)], G0, G5, 1.5))
    body.append(circle(CX, CY, 11, G0, G5, 1.5))
    body.append(circle(CX, CY, 3.5, G5))
    # the door's leaf, closed on the meridian, cut in section: black body, bright outline,
    # the one brightest element (it hides the track where the swing crosses it)
    body.append(poly([(CX - 4.5, CY - 10), (CX + 4.5, CY - 10), (CX + 4.5, CY - R), (CX - 4.5, CY - R)], G0, G7, 2))
    return frame(body)


def main():
    import sys
    kw, out = {}, HERE / "clean.svg"
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=")
            kw[k] = float(v)
        else:
            out = Path(arg)
    kw.pop("creak", None)
    out.write_text(v4_clean(**kw), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
