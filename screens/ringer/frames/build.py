#!/usr/bin/env python3
"""Ringer: the picked subject (pass 02, v2) turned straight on.

The bells hang in a row from one level beam, seen from the front and a few
degrees below (looking up at them, as you would in a tower), standing in the
order they strike in this change: place 1 on the left. Larger bells are lower
in pitch and hang lower, because every headstock sits on the same axle line.

The camera is orthographic, pitched up PITCH degrees, no yaw: every bell is
seen exactly the same way wherever it hangs, so a bell trading places along
the beam is a pure translation on the device, and a bell's drawing only
depends on its own size (craft.md, Think in 3D: one camera, modelled solids).

A bell is drawn as nested bands, each a black-filled closed outline from one
ring of the profile down to the lip: body (crown), shoulder, waist and sound
bow. Each band's top edge is a band line, so the detail is all edges of
closed shapes, and a band too close to its neighbour at 1:1 (< 3 px) is
dropped by hiding its node. A fill-none outline goes over the bands so the
body edge stays one weight, then the mouth (the lip ellipse, seen from below)
and the clapper's flight hanging below the lip.

A strike: the striking bell tips up toward you about its headstock axle (out
of the screen plane, up to SWING_MAX), drawn with the four mutable outlines
(body, waist line, sound-bow line, mouth) re-projected per frame while that
bell's six static body nodes are hidden. Its headstock and flight stay put (the
headstock's change is under a pixel at this angle; the clapper hangs plumb as
the bell rises to meet it). It lights for the swing and falls back still.

    python3 screens/ringer/frames/build.py            # frames, pngs, sheets, gif
    python3 screens/ringer/frames/build.py --svg-only
    python3 screens/ringer/frames/build.py --check     # lint + perceptibility (scratch, removed)

Needs shapely (silhouette of the swung bell), rsvg-convert, Pillow.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORIGINAL_V2 = HERE.parent / "passes" / "02-subject" / "v2" / "rest.png"

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0
LABELS = ["bells", "method", "pace", "stroke"]
METHODS = ["hunt", "bob", "gran", "sted", "kent", "camb"]
DEFAULTS = {"bells": 0.25, "method": 0.2, "pace": 0.5, "stroke": 0.0}

PITCH = math.radians(9.0)      # camera looks up at the bells by this much
SP, CP = math.sin(PITCH), math.cos(PITCH)
AXLE_Y = 112.0                 # screen y of the headstock axle line (all bells)
BEAM_DROP = 15.0               # beam underside sits this far above the axle
BEAM_H, BEAM_D = 10.0, 22.0    # beam front-face height and depth (px)
BEAM_X0, BEAM_X1 = 12.0, 468.0
ROW_W = 440.0                  # widest row (slowest pace, full stroke) fits this
SWING_MAX = math.radians(22)   # how far toward you a striking bell swings (a stand-in for the full circle)
HATCH_H, HATCH_GAP = 18.0, 4.0  # the open-lead band: line height and spacing (px)
MIN_SEP = 3.0                  # detail lines closer than this at 1:1 are dropped


# ---------------------------------------------------------------- controls -> values
def n_bells(v):
    return int(round(4 + 8 * v))


def method_index(v):
    return min(5, int(v * 6))


def pace_value(v):
    return 0.5 * 16 ** v       # exponential 0.5..8


def header_values(c):
    n = n_bells(c["bells"])
    return [str(n), METHODS[method_index(c["method"])], f"{pace_value(c['pace']):.1f}",
            str(int(round(c["stroke"] * 100)))]   # ux.md: amounts 0-100 without %


# ---------------------------------------------------------------- methods (place notation)
def change(row, places):
    """Apply one change: pairs not in `places` (1-based) swap, scanning from the front."""
    row = list(row)
    i, n = 0, len(row)
    while i < n - 1:
        if (i + 1) in places:
            i += 1
            continue
        row[i], row[i + 1] = row[i + 1], row[i]
        i += 2
    return row


def pn(s, n):
    """Parse 'x.16.x' style notation for stage n into a list of place sets."""
    out = []
    for tok in s.replace("-", ".x.").split("."):
        if tok in ("", ):
            continue
        out.append(set() if tok == "x" else {int(c, 16) for c in tok})
    return out


def sym(a, le):
    """&a,le: a palindromic half lead plus its lead end."""
    return a + a[-2::-1] + le


def lead_of(method, n):
    """One lead's changes for `method` on n bells. Odd methods on an even stage ring
    with the tenor covering (its place is always made), as towers do."""
    work = n if method in ("hunt", "bob", "kent", "camb") else (n - 1 if n % 2 == 0 else n)
    cover = set(range(work + 1, n + 1))
    X = set() if work % 2 == 0 else {work}
    if method == "hunt":
        lead = [X, {1, work}] if work % 2 == 0 else [{work}, {1}]
        lead = lead * work
    elif method == "bob":
        if work % 2 == 0:
            lead = [X, {1, work}] * work
            lead[-1] = {1, 2}
        else:
            lead = [{work}, {1}] * work
            lead[-1] = {1, 2, work} if work > 3 else {1}
    elif method == "gran":
        lead = [{3}, {1}] + [{work}, {1}] * (work - 1)
    elif method == "sted":
        lead = pn(f"3.1.{work}.3.1.3.1.3.{work}.1.3.1", work)
    elif method == "kent":
        if work == 6:
            lead = sym(pn("34.x.34.16.x.12.x.16.x.12.x.16", 6), [{1, 2}])
        else:  # treble bob on other even stages: plain treble bob hunting with kent's 34 places
            lead = sym([{3, 4}, set(), {3, 4}] + [{1, work}, set()] * (work - 2), [{1, 2}])
    elif method == "camb":
        if work == 6:
            lead = sym(pn("x.36.x.14.x.12.x.36.x.14.x.56", 6), [{1, 2}])
        elif work == 8:
            lead = sym(pn("x.38.x.14.x.1258.x.36.x.14.x.58.x.16.x.78", 8), [{1, 2}])
        else:
            lead = sym([set(), {3, work}, set(), {1, 4}] + [set(), {1, work}] * (work - 2), [{1, 2}])
    return [p | cover for p in lead]


def rows_of(method, n, count):
    out = [list(range(1, n + 1))]
    lead = lead_of(method, n)
    k = 0
    while len(out) < count:
        out.append(change(out[-1], lead[k % len(lead)]))
        k += 1
    return out


def shown_row_index(n=6):
    """The change shown at rest: the first row (past the start) where all six methods
    stand in different orders and none is rounds."""
    rounds = list(range(1, n + 1))
    for r in range(3, 40):
        rows = [tuple(rows_of(m, n, r + 1)[r]) for m in METHODS]
        if len(set(rows)) == 6 and tuple(rounds) not in rows:
            return r
    return 15


ROW_INDEX = shown_row_index()


# ---------------------------------------------------------------- bell model
# Outside profile (r, z): r as a fraction of the lip radius, z from crown (0) to lip (1).
BELL = [(0.42, 0.0), (0.52, 0.04), (0.56, 0.14), (0.58, 0.32), (0.62, 0.5),
        (0.70, 0.66), (0.84, 0.82), (0.96, 0.93), (1.0, 1.0)]
BELL_H = 1.45                 # height / lip radius
BANDS = {"shoulder": 2, "waist": 4, "bow": 6}
HEAD = (0.62, 0.13, 0.30)     # headstock half sizes (x, y, z) / lip radius


def hy_of(R):
    """Headstock half-height: in proportion, but never under 2.5 px so a small bell's
    headstock stays a box at 1:1 rather than a blob."""
    return max(HEAD[1] * R, 2.5)


def bell_scale(b):
    """Lip radius factor: treble 1, each bell down the major scale bigger (size ~ 1/pitch)."""
    steps = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19]
    return 2 ** (steps[b - 1] / 12 * 0.75)


def gap_px(s, u):
    """Pace: the space between neighbouring lips, wide at 0.5 a beat, nearly touching at 8."""
    return 3.5 + s * 0.55 * (1 - u)


def size_for(n):
    """Treble lip radius (px) so the widest row (pace 0, stroke 100) fits ROW_W."""
    widths = sum(2 * bell_scale(b) for b in range(1, n + 1))
    mean = widths / n
    # widths*s + (n-1)*(3.5+0.55s) + bay(mean*s + 3.5 + 0.55s) = ROW_W
    a = widths + (n - 1) * 0.55 + mean + 0.55
    c = (n - 1) * 3.5 + 3.5
    return (ROW_W - c) / a


def layout(c, order):
    """x centre of each place, the bay (x0, x1) or None, and the treble radius."""
    n = n_bells(c["bells"])
    s = size_for(n)
    g = gap_px(s, c["pace"])
    widths = [2 * s * bell_scale(b) for b in order]
    mean = sum(2 * s * bell_scale(b) for b in range(1, n + 1)) / n
    bay = c["stroke"] * (mean + g)
    total = sum(widths) + (n - 1) * g + bay
    x = 240 - total / 2
    bay_span = (x, x + bay - g * c["stroke"]) if bay > 0.5 else None
    x += bay
    xs = []
    for w in widths:
        xs.append(x + w / 2)
        x += w + g
    return xs, bay_span, s


# ---------------------------------------------------------------- projection
def P(X, Y, Z, cx=0.0):
    """World (px, axle at Y=0, Z toward the back) to screen. Orthographic, pitched up."""
    return (cx + X, AXLE_Y - (Y * CP - Z * SP))


def depth(X, Y, Z):
    return Y * SP + Z * CP


def ring(R, k, n=40):
    rf, z = BELL[k]
    hy = hy_of(R)
    Y = -hy - z * BELL_H * R
    return [(rf * R * math.cos(2 * math.pi * j / n), Y, rf * R * math.sin(2 * math.pi * j / n)) for j in range(n)]


def arc(R, k, near=True, cx=0.0, n=40):
    """The near (upper, seen from below) or far (lower) half of ring k, left to right."""
    rf, z = BELL[k]
    Y = -hy_of(R) - z * BELL_H * R
    r = rf * R
    pts = []
    for j in range(n // 2 + 1):
        a = math.pi * j / (n // 2)
        X = -r * math.cos(a)
        Z = -r * math.sin(a) if near else r * math.sin(a)
        pts.append(P(X, Y, Z, cx))
    return pts


def side(R, k, sgn, cx=0.0):
    rf, z = BELL[k]
    return P(sgn * rf * R, -hy_of(R) - z * BELL_H * R, 0, cx)


# ---------------------------------------------------------------- svg primitives
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if not out or math.dist(out[-1], p) >= 0.3:
            out.append(p)
    while len(out) > 2 and math.dist(out[0], out[-1]) < 0.4:
        out.pop()
    return out


def thin(pts, limit=62):
    if len(pts) <= limit:
        return pts
    step = len(pts) / limit
    return [pts[int(k * step)] for k in range(limit)]


def resample(pts, count):
    """Exactly `count` points evenly along a closed outline (mutable outlines share one count)."""
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    lens = [math.dist(a, b) for a, b in segs]
    total = sum(lens)
    out, acc, i = [], 0.0, 0
    for k in range(count):
        t = total * k / count
        while acc + lens[i] < t:
            acc += lens[i]
            i += 1
        a, b = segs[i]
        u = (t - acc) / lens[i] if lens[i] else 0
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


class Frame:
    def __init__(self, title, values):
        self.title, self.values, self.items = title, values, []

    def path(self, pts, fill, stroke="none", sw=0.0, exact=False):
        pts = pts if exact else thin(dedupe(pts))
        if len(pts) < 3:
            return
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.items.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, pts, w, colour):
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(pts):
            j0, j1 = max(k - 1, 0), min(k + 1, len(pts) - 1)
            dx, dy = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.path(left + right[::-1], colour)

    def hatch(self, poly, colour, gap=4.0, w=HAIR):
        """45-degree hairlines >= 3 px apart, clipped to poly (craft.md: semi-opaque is hatched)."""
        shape = Polygon(poly)
        x0, y0, x1, y1 = shape.bounds
        c = x0 - (y1 - y0)
        from shapely.geometry import LineString
        while c < x1:
            seg = LineString([(c, y1 + 1), (c + (y1 - y0) + 2, y0 - 1)]).intersection(shape)
            for g in getattr(seg, "geoms", [seg]):
                if not g.is_empty and g.length > 2.5:
                    self.ribbon(list(g.coords), w, colour)
            c += gap

    def svg(self):
        head = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                f"  <title>ringer · straight on · {self.title}</title>",
                '  <g id="preview_canvas">',
                '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
                "  </g>", '  <g id="preview_header">']
        for i, col in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{col}" stroke="none"/>')
        for i, lab in enumerate(LABELS):
            col = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, val in enumerate(self.values):
            col = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{val}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


# ---------------------------------------------------------------- drawing
def beam(fr):
    yb = BEAM_DROP
    front = [P(BEAM_X0, yb, -BEAM_D / 2), P(BEAM_X1, yb, -BEAM_D / 2),
             P(BEAM_X1, yb + BEAM_H, -BEAM_D / 2), P(BEAM_X0, yb + BEAM_H, -BEAM_D / 2)]
    under = [P(BEAM_X0, yb, -BEAM_D / 2), P(BEAM_X1, yb, -BEAM_D / 2),
             P(BEAM_X1, yb, BEAM_D / 2), P(BEAM_X0, yb, BEAM_D / 2)]
    # node: the beam's whole silhouette (front face and the underside you see from below)
    fr.path([front[3], front[2], front[1], under[2], under[3], front[0]], G0, G3, LINE)
    # node: the arris between front face and underside
    fr.ribbon([front[0], front[1]], HAIR, G3)


def hangers(fr, R, cx, colour):
    """Two straps from the beam's underside to the gudgeons at the headstock's ends: an
    outlined strap where it's wide enough to read (>= 5 px), a single line where it isn't."""
    hx = HEAD[0] * R
    w = 0.11 * R
    for sgn in (-1, 1):
        if w < 5:
            x = sgn * (hx + 1.0)
            fr.ribbon([P(x, BEAM_DROP, -BEAM_D * 0.2, cx), P(x, -hy_of(R) * 0.9, -BEAM_D * 0.2, cx)], LINE, colour)
            continue
        xa, xb = sorted((sgn * hx, sgn * (hx + w)))
        fr.path([P(xa, BEAM_DROP, -BEAM_D * 0.2, cx), P(xb, BEAM_DROP, -BEAM_D * 0.2, cx),
                 P(xb, -hy_of(R) * 0.9, -BEAM_D * 0.2, cx), P(xa, -hy_of(R) * 0.9, -BEAM_D * 0.2, cx)],
                G0, colour, HAIR)


def headstock(R, theta=0.0, cx=0.0):
    hx, hz = HEAD[0] * R, HEAD[2] * R
    hy = hy_of(R)
    if theta == 0.0:
        return [P(-hx, hy, -hz, cx), P(hx, hy, -hz, cx), P(hx, -hy, -hz, cx), P(-hx, -hy, -hz, cx)]
    pts = [P(*rot((sx * hx, sy * hy, sz * hz), theta), cx) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return list(Polygon(pts).convex_hull.exterior.coords)[:-1]


def detail_kept(R):
    """Which band lines stay: drop any closer than MIN_SEP to the crown edge, the lip
    or the band kept below it (all measured at the bell's centre line, the closest point)."""
    def top_y(k):
        return arc(R, k, near=True)[len(arc(R, k)) // 2][1]
    lip = top_y(8)
    kept, last = [], lip
    for name in ("bow", "waist", "shoulder"):
        y = top_y(BANDS[name])
        if last - y >= MIN_SEP and y - top_y(0) >= MIN_SEP:
            kept.append(name)
            last = y
    return kept


def flight(fr, R, cx, inner):
    """The clapper's flight, hanging plumb below the lip. Authored after everything else,
    so it shows in the swung bell's mouth too: the clapper hangs still while the bell rises."""
    if R < 13:
        return
    ylip = P(0, -hy_of(R) - BELL_H * R, 0)[1]
    w = max(1.6, 0.06 * R)
    tip = ylip + R * SP + max(4.0, 0.2 * R)
    fr.path([(cx - w, ylip - 0.2 * R * SP), (cx + w, ylip - 0.2 * R * SP), (cx + w * 0.7, tip),
             (cx - w * 0.7, tip)], G0, inner, HAIR)


def bell_static(fr, R, cx, now, head_only=False):
    """A hanging bell at rest: headstock, nested bands, outline, mouth (flight drawn later)."""
    edge, sw, inner = (G7, SUBJ, G5) if now else (G4, LINE, G3)
    fr.path(headstock(R, cx=cx), G0, G5 if (now or head_only) else G3, LINE)
    if head_only:
        return
    body = (arc(R, 0, True, cx) + [side(R, k, 1, cx) for k in range(1, 8)]
            + arc(R, 8, False, cx)[::-1] + [side(R, k, -1, cx) for k in range(7, 0, -1)])
    fr.path(body, G0)                                         # body: black fill, hides what's behind
    for name in ("shoulder", "waist", "bow"):
        if name not in detail_kept(R):
            continue
        k = BANDS[name]
        band = (arc(R, k, True, cx) + [side(R, j, 1, cx) for j in range(k + 1, 8)]
                + arc(R, 8, False, cx)[::-1] + [side(R, j, -1, cx) for j in range(7, k, -1)])
        fr.path(band, G0, inner, HAIR)                        # band: its top edge is the band line
    fr.path(body, "none", edge, sw)                           # outline over the bands' sides
    mouth = arc(R, 8, True, cx) + arc(R, 8, False, cx)[::-1][1:-1]
    fr.path(mouth, G0, edge, sw)                              # the lip, and the dark inside


def rot(p, th):
    """Swing about the axle (world X): the mouth comes toward you (-Z) and up."""
    x, y, z = p
    return (x, y * math.cos(th) - z * math.sin(th), y * math.sin(th) + z * math.cos(th))


def bell_swung(fr, R, cx, theta, lit):
    """The striking bell in its swing, drawn as the four mutable outlines (48 points each)."""
    edge, sw, inner = (G7, SUBJ, G5) if lit else (G4, LINE, G3)
    hy = hy_of(R)
    prof = []
    for i in range(len(BELL) - 1):                            # dense rings for the silhouette
        for t in (0, 0.34, 0.67):
            (r0, z0), (r1, z1) = BELL[i], BELL[i + 1]
            prof.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
    prof.append(BELL[-1])

    def ring_pts(rf, z, n=40):
        Y = -hy - z * BELL_H * R
        return [rot((rf * R * math.cos(2 * math.pi * j / n), Y, rf * R * math.sin(2 * math.pi * j / n)), theta)
                for j in range(n)]

    sil = unary_union([Polygon([P(*q, cx) for q in ring_pts(rf, z)]).buffer(0) for rf, z in prof])
    if isinstance(sil, MultiPolygon):
        sil = max(sil.geoms, key=lambda g: g.area)
    body = list(sil.exterior.coords)[:-1]
    # band lines: the half of each ring facing the camera
    view = (0, -SP, -CP)                                      # toward the camera
    lines = []
    for name in ("waist", "bow"):
        if name not in detail_kept(R):
            continue
        rf, z = BELL[BANDS[name]]
        pts3 = ring_pts(rf, z, 48)
        centre = rot((0, -hy - z * BELL_H * R, 0), theta)
        vis = [j for j, q in enumerate(pts3) if sum((q[i] - centre[i]) * view[i] for i in range(3)) > 0]
        if not vis:
            continue
        start = next(j for j in vis if (j - 1) % 48 not in vis)
        run, j = [], start
        while j in vis:
            run.append(P(*pts3[j], cx))
            j = (j + 1) % 48
            if j == start:
                break
        lines.append(run)
    lip = [P(*q, cx) for q in ring_pts(1.0, 1.0, 48)]
    fr.path(resample(body, 48), G0, edge, sw, exact=True)                     # path 0: body
    for run in lines:
        fr.ribbon(run, HAIR, inner)                                           # paths 1, 2: waist, sound bow
    fr.path(resample(lip, 48), G0, edge, sw, exact=True)                      # path 3: the mouth, lit lip


def draw(c, row, title, swing=None, positions=None, lit=None, values=None):
    """One frame. `swing` = (bell, theta) for the bell in its strike; `positions` overrides
    x centres per bell (trades in progress); `lit` is the one bright bell."""
    n = n_bells(c["bells"])
    fr = Frame(title, values or header_values(c))
    xs, bay, s = layout(c, row)
    xpos = {b: xs[k] for k, b in enumerate(row)}
    if positions:
        xpos.update(positions)
    beam(fr)
    if bay:
        # the open lead: a hatched band of fixed-length 45-degree hairlines under the beam,
        # one node each from a pool, shown as many as the bay holds (count, not reshaping)
        y0 = P(0, BEAM_DROP, -BEAM_D / 2)[1] + 3
        x = bay[0]
        while x + HATCH_H <= bay[1] + 0.01:
            fr.ribbon([(x, y0 + HATCH_H), (x + HATCH_H, y0)], HAIR, G2)
            x += HATCH_GAP
    lit = row[0] if lit is None else lit
    for b in sorted(range(1, n + 1), reverse=True):           # tenor first: smaller bells pass in front
        R = s * bell_scale(b)
        hangers(fr, R, xpos[b], G3)
    for b in sorted(range(1, n + 1), reverse=True):
        bell_static(fr, s * bell_scale(b), xpos[b], b == lit and not swing,
                    head_only=bool(swing and b == swing[0]))
    if swing:                                                  # mutable outlines, authored after the bells
        b, th = swing
        bell_swung(fr, s * bell_scale(b), xpos[b], th, True)
    for b in sorted(range(1, n + 1), reverse=True):           # flights last: plumb in every mouth
        flight(fr, s * bell_scale(b), xpos[b], G5 if (b == lit) else G3)
    return fr


def control_frames():
    out = {"rest": dict(DEFAULTS)}
    for name in LABELS:
        for v in (0, 50, 100):
            c = dict(DEFAULTS)
            c[name] = v / 100
            out[f"{name}-{v}"] = c
    return out


def row_for(c, r=ROW_INDEX):
    return rows_of(METHODS[method_index(c["method"])], n_bells(c["bells"]), r + 1)[r]


# ---------------------------------------------------------------- outputs
def write(name, fr, where=HERE):
    p = where / f"{name}.svg"
    p.write_text(fr.svg())
    return p


def png(svg, out=None):
    out = out or svg.with_suffix(".png")
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-o", str(out), str(svg)], check=True)
    return out


def ease_out(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3


def motion(tmp, fps=25):
    """Two changes rung at the defaults (plain bob minor, 2 blows a beat at 120 bpm),
    then still. Each bell swings toward you as it strikes and lights; behind the strike
    front, neighbours that trade in the next change slide past each other along the beam."""
    from PIL import Image
    c = dict(DEFAULTS)
    n = n_bells(c["bells"])
    blow = 60 / 120 / pace_value(c["pace"])               # seconds per blow
    T = min(0.24, 0.95 * blow)                             # swing length
    trade = min(0.15, blow)                                # a trade eases this long
    rows = rows_of("bob", n, ROW_INDEX + 3)[ROW_INDEX:ROW_INDEX + 3]
    # schedule: (time, bell, x_from, x_to)
    events, moves, t = [], [], 0.3
    for r in range(2):
        cur, nxt = rows[r], rows[r + 1]
        xs_cur, _, _ = layout(c, cur)
        xs_nxt, _, _ = layout(c, nxt)
        hand = (ROW_INDEX + r) % 2 == 0
        t += c["stroke"] * blow if hand else 0
        for k, b in enumerate(cur):
            events.append((t, b))
            j = nxt.index(b)
            if j != k:                                     # trades once both of the pair have struck
                start = t + T if j < k else t + blow + T
                moves.append((start, b, xs_cur[k], xs_nxt[j]))
            t += blow
    end = t + 0.6
    frames = []
    nf = int(end * fps)
    final_row = rows[2]
    for i in range(nf):
        now = i / fps
        swing, lit = None, None
        for (t0, b) in events:
            if t0 <= now < t0 + T:
                swing = (b, SWING_MAX * math.sin(math.pi * (now - t0) / T))
                lit = b
        pos = {}
        xs0, _, _ = layout(c, rows[0])
        for k, b in enumerate(rows[0]):
            pos[b] = xs0[k]
        for (t0, b, x0, x1) in sorted(moves):
            if now >= t0:
                pos[b] = x0 + (x1 - x0) * ease_out((now - t0) / trade)
        row_shown = rows[0]
        if now > events[-1][0] + T:
            row_shown = final_row
        if now < events[0][0]:
            lit = rows[0][0]                                # still, before the first blow
        elif now > events[-1][0] + T:
            lit = final_row[0]                              # settled: the next lead
        fr = draw(c, row_shown, f"motion {i}", swing=swing, positions=pos, lit=lit or -1)
        p = write(f"m{i:03d}", fr, tmp)
        frames.append(Image.open(png(p)).convert("P", palette=Image.ADAPTIVE, colors=32))
    hold = [int(1000 / fps)] * (len(frames) - 1) + [1500]
    frames[0].save(HERE / "motion.gif", save_all=True, append_images=frames[1:], duration=hold, loop=0)
    return blow, T


def sheets():
    from PIL import Image
    # before / after at 1:1
    a, b = Image.open(ORIGINAL_V2).convert("RGB"), Image.open(HERE / "rest.png").convert("RGB")
    ba = Image.new("RGB", (480 * 2 + 12, 220), (24, 24, 24))
    ba.paste(a, (0, 0))
    ba.paste(b, (492, 0))
    ba.save(HERE / "before-after.png")
    # contact: rest on top, then each control's 0 / 50 / 100
    gap = 12
    W, H = 3 * 480 + 2 * gap, 5 * 220 + 4 * gap
    sheet = Image.new("RGB", (W, H), (24, 24, 24))
    sheet.paste(Image.open(HERE / "rest.png").convert("RGB"), (0, 0))
    for r, name in enumerate(LABELS, start=1):
        for k, v in enumerate((0, 50, 100)):
            sheet.paste(Image.open(HERE / f"{name}-{v}.png").convert("RGB"), (k * (480 + gap), r * (220 + gap)))
    sheet.save(HERE / "contact.png")


def playing_frame():
    """A representative frame mid-row at the defaults: the bell in third place at the top
    of its swing, the first two (already struck) halfway through trading places."""
    c = dict(DEFAULTS)
    rows = rows_of("bob", n_bells(c["bells"]), ROW_INDEX + 2)
    row, nxt = rows[ROW_INDEX], rows[ROW_INDEX + 1]
    xs, _, _ = layout(c, row)
    xn, _, _ = layout(c, nxt)
    pos = {b: (xs[k] + xn[nxt.index(b)]) / 2 for k, b in enumerate(row[:2])}
    return draw(c, row, "playing", swing=(row[2], SWING_MAX), positions=pos, lit=row[2])


def check():
    """Lint every frame, then perceptibility on c<N>-000/050/100 copies + rest/playing,
    in a scratch folder that is removed afterwards."""
    svgs = sorted(str(p) for p in HERE.glob("*.svg"))
    subprocess.run([sys.executable, str(ROOT / "opxy/tools/lint_frame.py"), *svgs])
    tmp = HERE / "_percept"
    tmp.mkdir(exist_ok=True)
    try:
        for i, name in enumerate(LABELS, start=1):
            for v in (0, 50, 100):
                shutil.copy(HERE / f"{name}-{v}.svg", tmp / f"c{i}-{v:03d}.svg")
        shutil.copy(HERE / "rest.svg", tmp / "rest.svg")
        write("playing", playing_frame(), tmp)
        subprocess.run([sys.executable, str(ROOT / "opxy/tools/perceptibility.py"), str(tmp),
                        "--scores", "4,3,5,2", "--names", ",".join(LABELS)])
        # a lone first blow (only the lead swinging), for the record
        c = dict(DEFAULTS)
        row = row_for(c)
        write("playing", draw(c, row, "first blow", swing=(row[0], SWING_MAX), lit=row[0]), tmp)
        print("first blow alone:")
        subprocess.run([sys.executable, str(ROOT / "opxy/tools/perceptibility.py"), str(tmp),
                        "--scores", "4,3,5,2", "--names", ",".join(LABELS)])
    finally:
        shutil.rmtree(tmp)


def main():
    if "--check" in sys.argv:
        check()
        return
    svg_only = "--svg-only" in sys.argv
    print("row index", ROW_INDEX, {m: "".join(map(str, rows_of(m, 6, ROW_INDEX + 1)[ROW_INDEX])) for m in METHODS})
    for name, c in control_frames().items():
        row = row_for(c)
        p = write(name, draw(c, row, name))
        if not svg_only:
            png(p)
    if svg_only:
        return
    tmp = HERE / "_scratch"
    tmp.mkdir(exist_ok=True)
    try:
        motion(tmp)
    finally:
        shutil.rmtree(tmp)
    sheets()


if __name__ == "__main__":
    main()
