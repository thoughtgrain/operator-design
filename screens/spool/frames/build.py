#!/usr/bin/env python3
"""Spool, frames: the picked subject (pass 02 v1), re-cameraed, plus its motion study.

    python3 screens/spool/frames/build.py            # stills, contact sheet, motion
    python3 screens/spool/frames/build.py --stills   # stills only

A spool of thread rolls on a table and lays its thread behind it in the written
cycle's shape, one repeat per revolution (= one pass of the loop). The camera is
low and in front, a little to the trail's side, so the near flange faces us as a
near-circle on the right and the trail runs off the LEFT edge along the table.
While a note sounds the spool turns in place (treadmill) and the laid trail slides
away to the left.

Everything is one 3D model through one camera (craft.md, Think in 3D). The frames
are authored as device artwork: every part is a bound node `spool_node_<i>` with a
`matrix(1 0 0 1 x y)` origin; nodes 0..3 are the four mutable outlines (three
trail chunks and the free run), 64 points each, hollow ribbons
(two 1.5 px plies) that part as the thread wears. Document order is
paint order. No text below the header; grey only.

Writes into this folder: rest, playing, <control>-0/50/100 (.svg + .png),
contact.png, motion.gif, motion-sheet.png, and prints the measured redraw.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RSVG = shutil.which("rsvg-convert")

B, S2, S, M, G, D, F, K = ("#CDCDCD", "#AFAFAF", "#969696", "#7D7D7D",
                           "#646464", "#4B4B4B", "#323232", "#000000")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2   # craft.md's three weights
PLY = 1.5                          # stroke of each ply: the thread is a hollow ribbon, two plies
GAP = (0.4, 0.4, 0.9, 0.9)         # plies apart when fresh, by voices held: a ~1.9 px line, ~2.4 px for a chord
FRAY, SPLIT = 3.2, 4.2             # plies part with wear, and open wide where the oxide thins
BODY_TOP = 21.0
PATHS, POINTS = 4, 64
CTRL = ["wear", "wow", "length", "bias"]
DEFAULTS = {"wear": 0.0, "wow": 0.0, "length": 0.5, "bias": 0.5}
REV_CAP = 1.25                 # most revolutions per second the screen shows

# ---------------------------------------------------------------- the machine


class Spool:
    """Control positions (0..1) -> mapped values (definition.json)."""

    # the cycle as written: a ramp, a step down to a shelf, a drop, a floor
    WRITTEN = [(0.0, -0.9), (0.55, 0.9), (0.6, -0.1), (0.85, 0.15), (0.9, -0.9), (1.0, -0.9)]

    def __init__(self, **kv: float) -> None:
        v = {**DEFAULTS, **kv}
        self.pos = v
        self.wear = v["wear"] ** 2                          # power 2: erosion per pass
        self.wow = v["wow"]
        self.length = 0.05 * (2.0 / 0.05) ** v["length"]    # s
        self.bias = v["bias"] * 2 - 1                       # -1 under .. +1 over

    def header(self) -> list[str]:
        b = round(self.bias * 100)
        return [str(round(self.wear * 100)), str(round(self.wow * 100)),
                f"{self.length:.2f}s", ("+" if b > 0 else "") + str(b)]

    # what the screen derives
    def rev_rate(self) -> float:
        """Revolutions per second shown: one per pass, capped so the eye can follow."""
        return min(1.0 / self.length, REV_CAP)

    def passes_per_rev(self) -> float:
        """Audio passes each shown revolution stands for (1 when the loop is >= 0.8 s)."""
        return (1.0 / self.length) / self.rev_rate()

    def wavelength(self) -> float:
        """World length of one laid repeat: a longer loop lays a longer repeat."""
        return 0.42 + 1.05 * self.pos["length"]


# ---------------------------------------------------------------- the written cycle, worn

_N = 512
_U = np.arange(_N) / _N
_WX = [p[0] for p in Spool.WRITTEN]
_WY = [p[1] for p in Spool.WRITTEN]
_CYCLE = np.interp(_U, _WX, _WY)
_SPEC = np.fft.rfft(_CYCLE)
_H = np.arange(len(_SPEC))


def worn_table(s: float) -> np.ndarray | None:
    """The cycle after high-partial loss s (0 crisp .. 1 the fundamental alone)."""
    if s <= 1e-4:
        return None
    g = np.ones(len(_SPEC))
    g[2:] = (1 - min(s, 1.0)) ** (0.8 * (_H[2:] - 1))
    return np.fft.irfft(_SPEC * g, _N)


def cycle_at(u: float, table) -> float:
    u = u % 1.0
    if table is None:
        return float(np.interp(u, _WX, _WY))
    i = u * _N
    i0 = int(i) % _N
    t = i - int(i)
    return float(table[i0] * (1 - t) + table[(i0 + 1) % _N] * t)


def warp_inv(uw: float, a: float) -> float:
    """Position in the repeat where written phase uw is laid, under wow depth a.
    Laid phase u -> written phase uw = u + a/(2 pi) sin(2 pi (u - 0.3)) (monotonic for a < 1)."""
    if a <= 1e-6:
        return uw
    lo, hi = uw - 0.2, uw + 0.2
    f = lambda u: u + a / (2 * math.pi) * math.sin(2 * math.pi * (u - 0.3)) - uw
    for _ in range(40):
        m = (lo + hi) / 2
        if f(m) > 0:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


def dropout(u: float, rep: int, depth: float) -> float:
    """0..1 thinning of the thread at laid phase u of repeat rep (oxide thinning)."""
    if depth <= 0:
        return 0.0
    out = 0.0
    for k in range(2):
        c = ((rep * 0.6180339 + k * 0.4142 + 0.13) % 1.0)
        d = min(abs(u - c), 1 - abs(u - c))
        out = max(out, math.exp(-(d / 0.075) ** 4))
    return depth * out


# ---------------------------------------------------------------- 3D

def v3(x, y, z):
    return np.array([x, y, z], dtype=float)


def unit(v):
    return v / np.linalg.norm(v)


class Camera:
    def __init__(self, pos, target, up=(0, 0, 1)):
        self.pos = np.asarray(pos, float)
        fwd = unit(np.asarray(target, float) - self.pos)
        right = unit(np.cross(fwd, up))
        self.fwd, self.right, self.up = fwd, right, np.cross(right, fwd)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = np.asarray(p, float) - self.pos
        z = d @ self.fwd
        return (d @ self.right) / z, (d @ self.up) / z, z

    def __call__(self, p):
        x, y, _ = self.raw(p)
        return (self.cx + self.f * x, self.cy - self.f * y)

    def faces(self, p, normal):
        return float(np.dot(normal, self.pos - np.asarray(p, float))) > 0


def basis(axis):
    a = unit(np.asarray(axis, float))
    t = v3(1, 0, 0) if abs(a[0]) < 0.9 else v3(0, 1, 0)
    u = unit(np.cross(a, t))
    return a, u, np.cross(a, u)


def ring(c, axis, r, n=72, a0=0.0, a1=2 * math.pi):
    _, u, w = basis(axis)
    c = np.asarray(c, float)
    ts = np.linspace(a0, a1, n, endpoint=(a1 - a0) < 2 * math.pi - 1e-9)
    return [c + r * (math.cos(t) * u + math.sin(t) * w) for t in ts], ts


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# ---------------------------------------------------------------- 2D kit

def num(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, gap=0.35, closed=False):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) >= gap:
            out.append(tuple(p))
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < gap:
        out.pop()
    return out


def resample_closed(pts, n):
    """n points spaced evenly round a closed outline."""
    pts = list(pts) + [pts[0]]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    tot = sum(seg)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        t = tot * k / n
        while acc + seg[i] < t:
            acc += seg[i]
            i += 1
        f = (t - acc) / seg[i] if seg[i] else 0
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def simplify(pts, ws, n):
    """Visvalingam down to n points, counting a width change as area too (keeps dropouts)."""
    idx = list(range(len(pts)))
    if len(idx) <= n:
        return [pts[i] for i in idx], [ws[i] for i in idx]

    def cost(k):
        a, b, c = pts[idx[k - 1]], pts[idx[k]], pts[idx[k + 1]]
        area = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
        la, lc = math.dist(a, b), math.dist(b, c)
        t = la / (la + lc) if la + lc else 0.5
        wi = ws[idx[k - 1]] * (1 - t) + ws[idx[k + 1]] * t
        return area + 6.0 * abs(ws[idx[k]] - wi) * (la + lc)
    costs = [math.inf] + [cost(k) for k in range(1, len(idx) - 1)] + [math.inf]
    while len(idx) > n:
        k = int(np.argmin(costs))
        del idx[k]
        del costs[k]
        for j in (k - 1, k):
            if 0 < j < len(idx) - 1:
                costs[j] = cost(j)
    return [pts[i] for i in idx], [ws[i] for i in idx]


def ribbon(pts, ws):
    """Closed ribbon round an open polyline, per-point width, flat ends."""
    left, right = [], []
    for i, p in enumerate(pts):
        normals = []
        for q0, q1 in ((pts[i - 1] if i else None, p), (p, pts[i + 1] if i < len(pts) - 1 else None)):
            if q0 is None or q1 is None:
                continue
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            ln = math.hypot(dx, dy) or 1
            normals.append((-dy / ln, dx / ln))
        nx, ny = sum(v[0] for v in normals), sum(v[1] for v in normals)
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        cos = max(0.55, nx * normals[0][0] + ny * normals[0][1])
        m = ws[i] / 2 / cos
        left.append((p[0] + nx * m, p[1] + ny * m))
        right.append((p[0] - nx * m, p[1] - ny * m))
    return left + right[::-1]


def _clean_edge(edge, centre):
    """Drop edge points that step backwards along the line (the inside of a sharp corner)."""
    pts = [edge[0]]
    cs = [centre[0]]
    for e, c in zip(edge[1:], centre[1:]):
        dx, dy = c[0] - cs[-1][0], c[1] - cs[-1][1]
        ex, ey = e[0] - pts[-1][0], e[1] - pts[-1][1]
        ln = math.hypot(dx, dy) or 1
        if (ex * dx + ey * dy) / ln < 0.35 or math.hypot(ex, ey) < 0.35:
            continue
        pts.append(e)
        cs.append(c)
    if pts[-1] != edge[-1]:
        if len(pts) > 1 and math.dist(pts[-1], edge[-1]) < 0.6:
            pts[-1] = edge[-1]
        else:
            pts.append(edge[-1])
    return pts


def _turn_back(a, b, c):
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    l1, l2 = math.hypot(*v1), math.hypot(*v2)
    if not l1 or not l2:
        return 0.0
    cosv = max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
    return math.degrees(math.acos(cosv))      # 0 = straight back


def polyline_fixed(pts, ws, n_center, total=POINTS):
    """An open line as a closed ribbon of exactly `total` points (mutable outline topology)."""
    pts, ws = list(pts), list(ws)
    keep = [0]
    for i in range(1, len(pts)):
        if math.dist(pts[keep[-1]], pts[i]) >= 0.8:
            keep.append(i)
    if keep[-1] != len(pts) - 1:
        if len(keep) > 1:
            keep[-1] = len(pts) - 1
        else:
            keep.append(len(pts) - 1)
    pts, ws = [pts[i] for i in keep], [ws[i] for i in keep]
    pts, ws = simplify(pts, ws, max(n_center + 10, 2))
    rib = ribbon(pts, ws)
    n = len(pts)
    left, right = rib[:n], rib[n:][::-1]
    left, right = _clean_edge(left, pts), _clean_edge(right, pts)
    poly = left + right[::-1]
    prot = {0, len(left) - 1, len(left), len(poly) - 1}
    # too few: split the longest edges (never an end cap)
    while len(poly) < total:
        k = max((i for i in range(len(poly)) if not ({i, (i + 1) % len(poly)} <= prot)),
                key=lambda i: math.dist(poly[i], poly[(i + 1) % len(poly)]))
        a, b = poly[k], poly[(k + 1) % len(poly)]
        poly.insert(k + 1, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
        prot = {i + 1 if i > k else i for i in prot}
    # too many: Visvalingam on the closed outline, end caps protected, worst tips first
    while len(poly) > total:
        best, bk = math.inf, None
        m = len(poly)
        for i in range(m):
            if i in prot:
                continue
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % m]
            area = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
            if _turn_back(a, b, c) < 6 or math.dist(a, b) < 0.3:
                area = -1
            if area < best:
                best, bk = area, i
        del poly[bk]
        prot = {i - 1 if i > bk else i for i in prot}
    return poly


# ---------------------------------------------------------------- frame

class Frame:
    """Bound nodes in paint order; each is (index, origin, points, fill, stroke, sw, comment)."""

    def __init__(self, values):
        self.values = values
        self.nodes = {}
        self.order = []

    def node(self, i, pts, fill=K, stroke="none", sw=0.0, origin=None, note=""):
        pts = [(float(x), float(y)) for x, y in pts]
        if origin is None:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            origin = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        ox, oy = round(origin[0], 2), round(origin[1], 2)
        rel = [(round(x - ox, 3), round(y - oy, 3)) for x, y in pts]
        self.nodes[i] = dict(origin=(ox, oy), pts=rel, fill=fill, stroke=stroke, sw=sw, note=note)
        self.order.append(i)

    def svg(self, title="spool"):
        steps = [K, F, D, G, M, S, S2, B]
        head = ['<g id="preview_canvas">',
                '  <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', '</g>',
                '<g id="preview_header">']
        for i, c in enumerate(steps):
            head.append(f'  <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, t in enumerate(CTRL):
            col = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'  <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{t}</text>')
            head.append(f'  <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{col}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{self.values[i]}</text>')
        head.append('</g>')
        body = []
        for i in self.order:
            n = self.nodes[i]
            d = "M " + " L ".join(f"{num(x)} {num(y)}" for x, y in n["pts"]) + " Z"
            sw = f' stroke-width="{num(n["sw"])}"' if n["stroke"] != "none" else ""
            body.append(f'<!-- {n["note"]} -->')
            body.append(f'<path id="spool_node_{i}" transform="matrix(1 0 0 1 {num(n["origin"][0])} {num(n["origin"][1])})" '
                        f'd="{d}" fill="{n["fill"]}" stroke="{n["stroke"]}"{sw}/>')
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">\n'
                f'  <!-- {title} -->\n  ' + "\n  ".join(head) + "\n  " + "\n  ".join(body) + "\n</svg>\n")


def changed(a: Frame | None, b: Frame) -> tuple[int, int]:
    """(changed nodes, of which re-keyed paths) between two consecutive frames."""
    if a is None:
        return len(b.nodes), PATHS
    nodes = keys = 0
    for i, n in b.nodes.items():
        m = a.nodes.get(i)
        if m is None or m["origin"] != n["origin"] or m["pts"] != n["pts"] or m["fill"] != n["fill"]:
            nodes += 1
            if m is not None and m["pts"] != n["pts"]:
                keys += 1
    return nodes, keys


# ---------------------------------------------------------------- the scene

RF, RW, LH, TF = 0.40, 0.29, 0.55, 0.06   # flange radius, winding radius, half winding length, flange thickness
AMP = 0.56                                # amplitude of the laid cycle across the table (world)


def camera() -> Camera:
    cam = Camera(v3(-1.55, -3.3, 1.35), v3(-0.9, 0.0, 0.3))
    cam.f = 1.0
    # fit: put the spool's centre and size where the composition wants them
    c = v3(0, 0, RF)
    p0 = cam.raw(c - v3(0, LH + TF, 0))
    p1 = cam.raw(c - v3(0, LH + TF, 0) + v3(0, 0, RF))
    cam.f = 52.0 / abs(p1[1] - p0[1])                 # near flange radius ~52 px tall
    cam.cx = 400 - cam.f * p0[0]
    cam.cy = 124 + cam.f * p0[1]
    return cam


CAM = camera()


class State:
    """What a frame shows besides the controls."""

    def __init__(self, phi: float, marks: list[float], voices: int = 0, slack_mod: float = 0.0):
        self.phi = phi            # revolutions turned (trail phase)
        self.marks = marks        # note-on phases (fresh writes), ascending
        self.voices = voices
        self.slack_mod = slack_mod  # free-run breathing from wow, -1..1


def rest_state(s: Spool) -> State:
    """The record a note leaves: written fresh, held until its first repeat reaches the left edge."""
    reps = visible_reps(s)
    phi = 40.0
    return State(phi, [phi - reps - 0.7])


def visible_reps(s: Spool) -> float:
    lam = s.wavelength()
    L = laying_point(s)
    q = 0.0
    while True:
        p = v3(L[0] - q * lam, 0, 0)
        if CAM(p)[0] < 0:
            return q
        q += 0.05


def laying_point(s: Spool) -> np.ndarray:
    """Where the newest repeat ends, a fixed distance behind the spool (the treadmill's mouth)."""
    return v3(-0.95, 0.0, 0.0)


def wind_off() -> np.ndarray:
    a = math.radians(50)                         # on the winding, up and back toward the trail
    return v3(-RW * math.sin(a), 0.12, RF + RW * math.cos(a))


def trail_point(s: Spool, st: State, q: float):
    """World point and width of the thread laid at phase q (q <= phi)."""
    lam = s.wavelength()
    L = laying_point(s)
    x = L[0] - (st.phi - q) * lam
    mark = max([m for m in st.marks if m <= q + 1e-9], default=st.marks[0] - 1000)
    rel = q - mark
    rep = int(math.floor(rel))
    u = rel - rep
    # wear: passes this repeat has been through since the fresh write
    P = rep * s.passes_per_rev()
    sw = 1 - (1 - 0.35 * s.wear) ** P if s.wear > 0 else 0.0
    b = s.bias
    s_eff = sw + max(b, 0) * 0.35 * (1 - sw)       # over-bias: duller
    table = worn_table(s_eff)
    a = 0.9 * s.wow
    uw = u + a / (2 * math.pi) * math.sin(2 * math.pi * (u - 0.3))
    v = cycle_at(uw, table)
    v *= 1 - 0.58 * sw                             # worn: the highs go and the level with them
    if b < 0:                                      # under-bias: louder, saturates hard
        v = max(-1 + 0.48 * -b, min(1 - 0.48 * -b, v * (1 + 0.35 * -b)))
    else:                                          # over-bias: quieter
        v *= 1 - 0.38 * b
    depth = max(0.0, min(1.0, (sw - 0.25) / 0.4))
    twist = abs(math.sin(math.pi * 5 * u))         # the plies' twist loosens: they part between crossings
    w = GAP[min(st.voices, 3)] + FRAY * sw * (0.35 + 0.65 * twist) + SPLIT * dropout(u, rep + int(mark * 7), depth)
    return v3(x, AMP * v, 0.0), w, rep, mark


def worn_now(s: Spool, st: State) -> float:
    """High-partial loss of the pass being laid now."""
    mark = max([m for m in st.marks if m <= st.phi + 1e-9])
    P = math.floor(st.phi - mark) * s.passes_per_rev()
    return 1 - (1 - 0.35 * s.wear) ** P if s.wear > 0 else 0.0


def shade_for(s: Spool, ws, st: State) -> str:
    """The thread dulls as it wears, two stock steps at most: a stretch reads its mean wear back
    from how far its plies have parted (dropouts excluded by the median)."""
    base = GAP[min(st.voices, 3)]
    worn = (float(np.median(ws)) - base) / (FRAY * 0.75)
    return B if worn < 0.3 else S2 if worn < 0.62 else S


def trail_samples(s: Spool, st: State):
    """Dense screen samples of the trail from the laying point to the left edge, corners kept."""
    a = 0.9 * s.wow
    corners = [p[0] for p in Spool.WRITTEN[:-1]]
    pts, ws = [], []
    q = st.phi
    lam = s.wavelength()
    L = laying_point(s)
    qs = []
    # walk back repeat by repeat; within each, uniform written phase plus the corners
    q_end = st.phi
    while True:
        x = L[0] - (st.phi - q_end) * lam
        if CAM(v3(x, 0, 0))[0] < -30:
            break
        q_end -= 1.0
    marks = st.marks
    for mark_i, mk in enumerate(marks):
        pass
    # collect candidate q values
    lo = q_end
    seg_marks = sorted(set([m for m in marks if lo < m < st.phi]))
    bounds = [lo] + seg_marks + [st.phi]
    for b0, b1 in zip(bounds, bounds[1:]):
        mark = max([m for m in marks if m <= b0 + 1e-9], default=marks[0] - 1000)
        r0 = math.floor(b0 - mark)
        r1 = math.floor(b1 - mark)
        for rep in range(r0, r1 + 1):
            ws_ = list(np.linspace(0, 1, 81)[:-1]) + corners
            for uw in sorted(set(round(x, 6) for x in ws_)):
                for e in (0.0,):
                    u = warp_inv(uw + e, a) if a > 0 else uw + e
                    qv = mark + rep + u
                    if b0 <= qv <= b1:
                        qs.append(qv)
        qs.append(b0)
        qs.append(b1)
        if b1 != st.phi:
            qs.append(b1 - 1e-4)
    qs = sorted(set(qs), reverse=True)            # from the laying point backwards
    for qv in qs:
        p3, w, _, _ = trail_point(s, st, qv)
        pts.append(CAM(p3))
        ws.append(w)
    # cut at the left edge
    out_p, out_w = [], []
    for i, p in enumerate(pts):
        if p[0] >= 0:
            out_p.append(p)
            out_w.append(ws[i])
        else:
            if out_p:
                a_, b_ = out_p[-1], p
                t = a_[0] / (a_[0] - b_[0])
                out_p.append((0.0, a_[1] + (b_[1] - a_[1]) * t))
                out_w.append(out_w[-1])
            break
    return out_p, out_w


def split_chunks(pts, ws, n=3):
    """Split the trail into n runs, each inside a 124 px square round its node origin."""
    x0 = pts[0][0]
    span = x0 - pts[-1][0]
    cuts = [x0 - span * k / n for k in range(1, n)]
    chunks, cur_p, cur_w, ci = [], [pts[0]], [ws[0]], 0
    for i in range(1, len(pts)):
        p = pts[i]
        if ci < len(cuts) and p[0] < cuts[ci]:
            a = cur_p[-1]
            t = (a[0] - cuts[ci]) / (a[0] - p[0]) if a[0] != p[0] else 0
            q = (cuts[ci], a[1] + (p[1] - a[1]) * t)
            wq = cur_w[-1]
            cur_p.append(q)
            cur_w.append(wq)
            chunks.append((cur_p, cur_w))
            cur_p, cur_w = [q], [wq]
            ci += 1
        cur_p.append(p)
        cur_w.append(ws[i])
    chunks.append((cur_p, cur_w))
    while len(chunks) < n:
        chunks.append(None)
    return chunks


def free_run(s: Spool, st: State, touch):
    """The thread between the winding and the table. Under-biased it's taut: one straight
    line from the winding to the trail. Over-biased it's slack: it falls almost at once to
    the table and lies there in a loose bow toward us before the trail begins."""
    W = wind_off()
    T = touch
    slack = 0.5 + 0.5 * s.bias                    # 0 taut .. 1 slack
    slack = min(1.0, max(0.0, slack + 0.22 * st.slack_mod))
    t_drop = 1 - 0.74 * slack
    pts = []
    for t in np.linspace(0, 1, 120):
        p = W * (1 - t) + T * t
        z = W[2] * max(0.0, 1 - t / t_drop) ** (1 + 1.6 * slack)
        bow = slack * 0.62 * math.sin(math.pi * t) ** 2
        sway = slack * 0.16 * math.sin(2 * math.pi * t)
        pts.append(v3(p[0] + sway, p[1] - bow, z))
    return pts


def rest_holes_angle(st: State) -> float:
    return 2 * math.pi * st.phi


def scene(s: Spool, st: State) -> Frame:
    fr = Frame(s.header())
    cam = CAM
    c = v3(0, 0, RF)
    ax = v3(0, 1, 0)
    near0, near1 = c - v3(0, LH + TF, 0), c - v3(0, LH, 0)
    far0, far1 = c + v3(0, LH, 0), c + v3(0, LH + TF, 0)

    def cyl_outline(c0, c1, r, n=96):
        a = np.asarray(c1) - np.asarray(c0)
        r0, _ = ring(c0, a, r, n)
        r1, _ = ring(c1, a, r, n)
        return resample_closed(hull([cam(p) for p in r0 + r1]), 60)

    # 4 far flange
    fr.node(4, cyl_outline(far0, far1, RF), K, M, LINE, note="far flange")
    # 5 winding (barrel of thread between the flanges)
    fr.node(5, cyl_outline(near1, far0, RW), K, M, LINE, note="winding")
    # 6..9 turns of thread on the winding: visible front arcs, as ribbons
    for k, t in enumerate(np.linspace(-LH + 0.13, LH - 0.13, 4)):
        pts, ts = ring(c + v3(0, t, 0), ax, RW, 160)
        _, u, w = basis(ax)
        vis = [cam(p) for p, tt in zip(pts, ts) if cam.faces(p, math.cos(tt) * u + math.sin(tt) * w)]
        # the visible arc is contiguous after a rotation of the list
        arc = []
        flags = [cam.faces(p, math.cos(tt) * u + math.sin(tt) * w) for p, tt in zip(pts, ts)]
        k0 = flags.index(False)
        order = list(range(k0, len(pts))) + list(range(0, k0))
        for i in order:
            if flags[i]:
                arc.append(cam(pts[i]))
        arc = arc[3:-3]
        rib = polyline_fixed(arc, [HAIR] * len(arc), 30)
        fr.node(6 + k, rib, D, "none", 0, note="turn of thread on the winding")

    # trail (nodes 0..2) and free run (node 3): the one bright thing
    tp, tw = trail_samples(s, st)
    chunks = split_chunks(tp, tw, 3)
    for i, ch in enumerate(chunks):
        if ch is None or len(ch[0]) < 2:
            fr.node(i, [(640 + 2 * math.cos(a), 320 + 2 * math.sin(a)) for a in np.linspace(0, 6.2, POINTS)],
                    "none", B, PLY, origin=(640, 320), note="trail chunk (hidden)")
            continue
        fr.node(i, polyline_fixed(ch[0], ch[1], POINTS // 2), "none", shade_for(s, ch[1], st), PLY,
                note=f"trail chunk {i}: mutable, {POINTS} points")
    touch, w_now, _, _ = trail_point(s, st, st.phi)
    fp = free_run(s, st, touch)
    fpts = [cam(p) for p in fp]
    fw = [GAP[min(st.voices, 3)] + FRAY * worn_now(s, st)] * len(fpts)
    fr.node(3, polyline_fixed(fpts, fw, POINTS // 2), "none", shade_for(s, fw, st), PLY,
            note="free run: mutable, 64 points")

    # 10 near flange body, 11 its face, 12 hub, 13 bore, 14..16 holes (they turn with the roll)
    fr.node(10, cyl_outline(near0, near1, RF), K, M, LINE, note="near flange rim")
    face, _ = ring(near0, ax, RF, 120)
    fr.node(11, resample_closed([cam(p) for p in face], 60), K, M, LINE, note="near flange face")
    hub, _ = ring(near0, ax, 0.13, 72)
    fr.node(12, resample_closed([cam(p) for p in hub], 40), K, D, LINE, note="hub")
    bore, _ = ring(near0, ax, 0.055, 48)
    fr.node(13, resample_closed([cam(p) for p in bore], 24), K, M, LINE, note="bore")
    _, u, w = basis(ax)
    ang = rest_holes_angle(st)
    # rolling toward +x turns the near face clockwise as we see it
    for k in range(3):
        a = -ang + k * 2 * math.pi / 3 + 0.4
        hc = near0 + 0.265 * (math.cos(a) * v3(1, 0, 0) + math.sin(a) * v3(0, 0, 1))
        hc2 = cam(hc)
        # the outline is authored once, at the face's centre, and only its origin moves
        ref, _ = ring(near0 + v3(0, 0, 0.0), ax, 0.062, 40)
        rc = cam(near0)
        hc2 = (round(hc2[0], 2), round(hc2[1], 2))
        rel = resample_closed([(x - rc[0], y - rc[1]) for x, y in (cam(p) for p in ref)], 24)
        pts = [(x + hc2[0], y + hc2[1]) for x, y in rel]
        # authored once round the origin; the roll only moves the origin (a circle on the face
        # projects to the same ellipse anywhere on it, to within a fraction of a pixel)
        fr.node(14 + k, pts, K, M, LINE, origin=hc2, note="lightening hole: translates with the roll")
    return fr


# ---------------------------------------------------------------- output

def render_png(svg_path: Path, png_path: Path):
    subprocess.run([RSVG, "-w", "480", "-h", "220", "-b", "black", "-o", str(png_path), str(svg_path)], check=True)


def write_frame(name: str, fr: Frame, out: Path = HERE):
    p = out / f"{name}.svg"
    p.write_text(fr.svg(f"spool · {name}"))
    render_png(p, out / f"{name}.png")
    return p


def stills():
    names = []
    s = Spool()
    write_frame("rest", scene(s, rest_state(s)))
    names.append("rest")
    st = rest_state(s)
    play = State(st.phi + 2.4, st.marks + [st.phi + 0.05], voices=1)
    write_frame("playing", scene(s, play))
    names.append("playing")
    for c in CTRL:
        for v in (0, 50, 100):
            sp = Spool(**{c: v / 100})
            write_frame(f"{c}-{v}", scene(sp, rest_state(sp)))
            names.append(f"{c}-{v}")
    return names


def contact(names):
    from PIL import Image, ImageDraw, ImageFont
    rows = [["rest", "playing"]] + [[f"{c}-{v}" for v in (0, 50, 100)] for c in CTRL]
    gap, lab = 16, 18
    W = gap + 3 * (480 + gap)
    H = gap + len(rows) * (220 + lab + gap)
    sheet = Image.new("RGB", (W, H), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            x, y = gap + c * (480 + gap), gap + r * (220 + lab + gap)
            sheet.paste(Image.open(HERE / f"{name}.png").convert("RGB"), (x, y))
            d.text((x, y + 220 + 3), name, fill=(150, 150, 150), font=font)
    sheet.save(HERE / "contact.png")


# ---------------------------------------------------------------- motion

def simulate(s: Spool, fps=15, t_on=0.5, t_off=4.9, t_end=6.6, chord=(1.7, 3.2), release=0.45):
    """Score: a note held through several revolutions (a second key joins mid-way), then
    released; the spool coasts to a stop with the release and the frame settles still."""
    st0 = rest_state(s)
    phi, marks = st0.phi, list(st0.marks)
    rate = s.rev_rate()
    omega = 0.0
    frames, stamps, counts = [], [], []
    prev = None
    dt = 1.0 / fps
    t = 0.0
    stopped = True
    prev_voices = 0
    while t < t_end + 1e-9:
        voices = 0
        if t_on <= t < t_off:
            voices = 1 + (1 if chord[0] <= t < chord[1] else 0)
        held = voices > 0
        if voices > prev_voices:
            marks.append(phi)                 # every new key is a fresh write: the newest repeat starts crisp
        prev_voices = voices
        if held:
            stopped = False
        if held:
            target = rate
            omega += (target - omega) * (1 - math.exp(-dt / 0.06))   # spins up within ~0.18 s
        else:
            omega *= math.exp(-dt / (release / 3))                   # coasts down with the release
            if omega * dt < 0.0015:
                omega = 0.0
                stopped = True
        # wow: rate swings once per revolution
        wob = math.sin(2 * math.pi * phi)
        phi += omega * dt * (1 + 0.32 * s.wow * wob)
        slack_mod = (wob * s.wow) if omega > 0 else 0.0
        if omega == 0:
            slack_mod = prev_slack if prev is not None else 0.0
        prev_slack = slack_mod
        st = State(phi, marks, voices if held else (1 if omega > 0 else 0), round(slack_mod, 2))
        if not held and omega == 0:
            st.voices = 0
        fr = scene(s, st)
        n, k = changed(prev, fr)
        if prev is not None:
            counts.append((t, n, k, held or omega > 0))
        prev = fr
        frames.append(fr)
        stamps.append(t)
        t += dt
    return frames, stamps, counts


def motion(s: Spool, fps=15):
    from PIL import Image, ImageDraw, ImageFont
    tmp = HERE / "_motion_tmp"
    tmp.mkdir(exist_ok=True)
    frames, stamps, counts = simulate(s, fps)
    imgs = []
    for i, fr in enumerate(frames):
        p = tmp / f"m{i:03d}.svg"
        p.write_text(fr.svg())
        render_png(p, tmp / f"m{i:03d}.png")
        imgs.append(Image.open(tmp / f"m{i:03d}.png").convert("RGB"))
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=64) for im in imgs]
    pal[0].save(HERE / "motion.gif", save_all=True, append_images=pal[1:], duration=int(1000 / fps), loop=0,
                optimize=False, disposal=1)
    # contact of key frames
    keys = [0.3, 0.6, 1.2, 2.2, 3.6, 4.85, 5.2, 6.0]
    pick = [min(range(len(stamps)), key=lambda i: abs(stamps[i] - k)) for k in keys]
    gap, lab = 14, 18
    cols = 2
    rows = (len(pick) + cols - 1) // cols
    W = gap + cols * (480 + gap)
    H = gap + rows * (220 + lab + gap)
    sheet = Image.new("RGB", (W, H), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    labels = {0.3: "rest", 0.6: "note on", 1.2: "rolling", 2.2: "chord (2 keys)", 3.6: "held",
              4.85: "held, last frame", 5.2: "released: coasting", 6.0: "still"}
    for j, i in enumerate(pick):
        x, y = gap + (j % cols) * (480 + gap), gap + (j // cols) * (220 + lab + gap)
        sheet.paste(imgs[i], (x, y))
        d.text((x, y + 220 + 3), f"t = {stamps[i]:.2f} s   {labels[keys[j]]}", fill=(150, 150, 150), font=font)
    sheet.save(HERE / "motion-sheet.png")
    shutil.rmtree(tmp)
    return counts


def report(counts):
    sounding = [n for t, n, k, a in counts if a]
    idle = [n for t, n, k, a in counts if not a]
    keyed = [k for t, n, k, a in counts if a]
    print(f"redraw while moving: avg {np.mean(sounding):.1f} nodes/frame, peak {max(sounding)}, "
          f"avg path re-keys {np.mean(keyed):.1f}; at rest: max {max(idle) if idle else 0}")
    tail = [n for t, n, k, a in counts][-5:]
    print("last frames:", tail)


if __name__ == "__main__":
    names = stills()
    contact(names)
    print("stills:", len(names))
    if "--stills" not in sys.argv:
        for preset, kv in (("attic", dict(wear=0.62, wow=0.35, length=0.38, bias=0.3)),):
            counts = motion(Spool(**kv))
            report(counts)
        # heaviest: everything that re-keys every frame (short loop, full wow and wear, chord)
        heavy = simulate(Spool(wear=1.0, wow=1.0, length=0.0, bias=1.0), 15)[2]
        print("heaviest setting:", end=" ")
        report(heavy)
