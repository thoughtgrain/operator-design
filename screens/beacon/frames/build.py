#!/usr/bin/env python3
"""Beacon, refined subject: the headland and the whole lighthouse (subject pass 02, v5, refined).

The owner picked v5 of passes/02-subject and asked for it simplified, with no
cutaway, and the waves on the right turned into surface ripples. Same angle:
the lighthouse on its headland at left, the beam reaching across to the right,
the sea below. This script draws every frame from one model:

    python3 screens/beacon/frames/build.py          # SVGs + PNGs, GIF, sheets

- rest.svg at the defaults (pulse 25, lens 83, sweep 2.4 st, fog 0), no notes
- <control>-0 / -50 / -100 .svg for pulse, lens, sweep and fog, the rest at default
- before-after.png, contact.png and motion.gif, all at 1:1

The beam is modelled in 3D and projected through one camera: the lamp sits at
the tower's depth, the beam turns about the tower's axis (sweep), so as it
turns away its far end draws in toward the horizon and its bands crowd
together. Every frame is 480 x 220, keeps the stock header, has no text below
it, uses greys only, ribbons for lines, <= 64 points per path and <= 4
fractional digits.
"""
from __future__ import annotations

import importlib.util
import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
V5_PNG = HERE.parent / "passes" / "02-subject" / "v5" / "rest.png"

# defaults, as control positions 0..1 (definition.json)
DEFAULTS = {"pulse": 0.25, "lens": 0.7, "sweep": 0.2, "fog": 0.0}
CONTROLS = ["pulse", "lens", "sweep", "fog"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0          # craft.md, Line weights
FONT = "UniversNextPro-Light"
BODY = (0.0, 22.0, 480.0, 219.0)          # artwork keeps 2 px clear of the header
HATCH = 4.0                               # hatch pitch at 1:1 (>= 3)


# ---------------------------------------------------------------- header text
def header_values(c):
    lens = 0.995 * math.sqrt(c["lens"]) * 100          # power, max 0.995, exponent 0.5
    st = 12 * c["sweep"]
    sweep = "0" if st < 0.05 else (f"{st:.1f}" if st < 10 else f"{st:.0f}")
    return [str(round(c["pulse"] * 100)), str(int(lens)), sweep, str(round(c["fog"] * 100))]


# ---------------------------------------------------------------- helpers
def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    """Exponential-ish ease-out on 0..1."""
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def clip_poly(pts, box=BODY):
    x0, y0, x1, y1 = box

    def cut(pts, inside, inter):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(inter(q, p))
                out.append(p)
            elif inside(q):
                out.append(inter(q, p))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            return []
        pts = cut(pts, inside, inter)
    return pts


def clip_line(pts, box=BODY):
    x0, y0, x1, y1 = box
    runs, cur = [], []

    def seg(a, b):
        t0, t1 = 0.0, 1.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
            else:
                t = q / p
                if p < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        if t0 > t1:
            return None
        return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1), t0 > 0, t1 < 1

    for a, b in zip(pts, pts[1:]):
        r = seg(a, b)
        if r is None:
            if cur:
                runs.append(cur)
                cur = []
            continue
        pa, pb, cut_a, cut_b = r
        if not cur or cut_a:
            if cur:
                runs.append(cur)
            cur = [pa]
        cur.append(pb)
        if cut_b:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def poly_line_hits(poly, a, d):
    ts = []
    for i in range(len(poly)):
        p, q = poly[i - 1], poly[i]
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = p[0] - a[0], p[1] - a[1]
        t = (wx * ey - wy * ex) / den
        u = (wx * d[1] - wy * d[0]) / den
        if 0 <= u < 1:
            ts.append(t)
    return sorted(ts)


def dedupe(pts, closed=True):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if closed and len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def vesica(cx, cy, w, h, n=10):
    right = [(cx + w / 2 * math.sin(math.pi * k / n), cy - h / 2 + h * k / n) for k in range(n + 1)]
    left = [(cx - w / 2 * math.sin(math.pi * k / n), cy - h / 2 + h * k / n) for k in range(n - 1, 0, -1)]
    return right + left


def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]),
                    (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts


# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self, title: str, values):
        self.title = title
        self.values = values
        self.items: list[str] = []
        self.count: dict[str, int] = {}
        self.part = "misc"

    def add(self, s: str) -> None:
        self.items.append(s)
        self.count[self.part] = self.count.get(self.part, 0) + 1

    def poly(self, pts, fill, stroke="none", sw=0.0, clip=True):
        if clip:
            pts = clip_poly(list(pts))
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def body(self, pts, edge, sw, fill=G0):
        self.poly(pts, fill, edge, sw)

    def ribbon(self, pts, w, colour, min_len=3.0):
        for run in clip_line(list(pts)):
            run = dedupe(run, closed=False)
            if len(run) < 2:
                continue
            xs, ys = [p[0] for p in run], [p[1] for p in run]
            if max(max(xs) - min(xs), max(ys) - min(ys)) < min_len:
                continue
            pieces = max(1, math.ceil((len(run) - 1) / 28))
            n = math.ceil((len(run) - 1) / pieces)
            i = 0
            while i < len(run) - 1:
                self._piece(run[i:i + n + 1], w, colour)
                i += n

    def _piece(self, seg, w, colour):
        h = w / 2
        left, right = [], []
        for k, (x, y) in enumerate(seg):
            if k == 0:
                dx, dy = seg[1][0] - x, seg[1][1] - y
            elif k == len(seg) - 1:
                dx, dy = x - seg[k - 1][0], y - seg[k - 1][1]
            else:
                ax, ay = x - seg[k - 1][0], y - seg[k - 1][1]
                bx, by = seg[k + 1][0] - x, seg[k + 1][1] - y
                la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
                dx, dy = ax / la + bx / lb, ay / la + by / lb
                if math.hypot(dx, dy) < 1e-6:
                    dx, dy = ax, ay
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * h, y + ny * h))
            right.append((x - nx * h, y - ny * h))
        self.poly(left + right[::-1], colour, clip=False)

    def line(self, a, b, w, colour):
        self.ribbon([a, b], w, colour)

    def circle(self, cx, cy, r, fill, stroke="none", sw=0.0):
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ""
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def hatch(self, poly, colour=G3, pitch=HATCH, slope=1, w=HAIR, min_len=3.0):
        """45-degree hairlines clipped to a convex-ish polygon (craft.md, semi-opaque areas)."""
        poly = clip_poly(list(poly))
        if len(poly) < 3:
            return
        d = (1.0, -1.0) if slope > 0 else (1.0, 1.0)
        key = (lambda p: p[0] + p[1]) if slope > 0 else (lambda p: p[0] - p[1])
        cs = [key(p) for p in poly]
        step = pitch * math.sqrt(2)
        c = math.floor(min(cs) / step) * step + step
        while c < max(cs):
            a = (c, 0.0)
            ts = poly_line_hits(poly, a, d)
            for t0, t1 in zip(ts[0::2], ts[1::2]):
                p0 = (a[0] + d[0] * t0, a[1] + d[1] * t0)
                p1 = (a[0] + d[0] * t1, a[1] + d[1] * t1)
                if math.dist(p0, p1) >= min_len:
                    self.ribbon([p0, p1], w, colour, min_len=min_len)
            c += step

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>beacon · refined subject · {self.title}</title>",
            '  <g id="preview_canvas">',
            '    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>',
            "  </g>",
            '  <g id="preview_header">',
        ]
        for i, c in enumerate([G0, G1, G2, G3, G4, G5, G6, G7]):
            head.append(f'    <rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
        for i, lab in enumerate(CONTROLS):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="10px">{lab}</text>')
        for i, val in enumerate(self.values):
            c = "#CBCBCB" if i < 2 else "#000000"
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{val}</text>')
        head.append("  </g>")
        return "\n".join(head + ["  " + s for s in self.items] + ["</svg>", ""])


# ---------------------------------------------------------------- the scene
TX = 110.0                 # tower axis
LAMP = (TX, 68.0)          # the lamp, centre of the lantern
HORIZON = 150.0
VX = 240.0                 # vanishing point x (camera axis)
FOCAL = 420.0              # focal length, px; the tower stands at depth FOCAL (1 world unit = 1 px there)
LAMP_UP = HORIZON - LAMP[1]   # lamp height above the eye, world units
LW = 250.0 - (TX - VX)     # beam length in world units: reaches x 490 when it lies across the frame
S0 = 12.0                  # the beam leaves the lantern glazing
PERIOD = 30.0              # one comb period of the pulse train, world units along the beam
SWEEP_MAX = 68.0           # degrees the beam leans away at sweep 100
FOG_TOP = 105.0            # px the fog bank's top rises above the horizon at fog 100
FOG_FOOT = HORIZON + 14    # the bank's foot on the sea
ROWS = [3, 7, 12, 19, 28, 40, 55, 67]   # ripple rows, px below the horizon: closer together with distance


def half_angle(lens):
    """lens: the beam focuses from a 5.2 degree half-spread to 1.0 degree."""
    return math.radians(lerp(5.2, 1.0, lens))


def project(s, theta, up):
    """A point s along the beam (world), turned theta away from the picture plane, `up` above its axis."""
    X = (TX - VX) + s * math.cos(theta)
    d = FOCAL + s * math.sin(theta)
    k = FOCAL / d
    return (VX + X * k, HORIZON - (LAMP_UP + up) * k)


def beam_point(s, theta, lens, side):
    r = 2.0 + s * math.tan(half_angle(lens))
    return project(s, theta, side * r)


def headland():
    pts = [(-2, 160), (28, 161), (60, 166), (82, 172), (138, 174), (156, 176), (169, 182),
           (180, 193), (188, 206), (193, 221)]
    return chaikin(pts, 2)


def draw(c, *, note=0.0, theta=None, front=None, cascade=1.0, shimmer=0.0, title="rest"):
    """c: control positions. note: 0 at rest .. 1 lit (eases in and out with attack and release).
    theta: the beam's turn (radians) for this frame; default is the rest pose, leaned fully by sweep.
    front: index of the band whose wavefront is lit (held notes). cascade: 0..1, how far out along the
    beam the bands have brightened (attack) or still are bright (release)."""
    F = Frame(title, header_values(c))
    lens, pulse, fog = c["lens"], c["pulse"], c["fog"]
    if theta is None:
        theta = math.radians(SWEEP_MAX * c["sweep"])

    # ------------------------------------------------ the beam (behind everything)
    F.part = "beam edges"
    edge_c = G4 if note > 0.5 else G3
    for side in (-1, 1):
        F.line(beam_point(S0, theta, lens, side), beam_point(LW, theta, lens, side), HAIR, edge_c)

    F.part = "beam bands"
    band = 3.0 + 24.0 * pulse                       # pulse: each band's width, as a share of the period
    k, sb = 0, S0 + 4.0
    while sb < LW - 1:
        se = min(sb + band, LW)
        quad = [beam_point(sb, theta, lens, -1), beam_point(se, theta, lens, -1),
                beam_point(se, theta, lens, 1), beam_point(sb, theta, lens, 1)]
        lit = note > 0 and (sb - S0) / (LW - S0) <= cascade
        F.part = "beam hatching"
        F.hatch(quad, G4 if lit else G3)
        F.part = "band wavefronts"
        wf = G6 if (front is not None and k % 4 == front % 4 and note > 0.5) else (G4 if lit else G3)
        if se - sb >= 2.5 or k == 0 or True:
            F.line(quad[1], quad[2], HAIR, wf)       # the band's outer edge: the front of the pulse
        k += 1
        sb += PERIOD

    # ------------------------------------------------ the sea: horizon, ripple rows, glitter
    F.part = "horizon"
    F.line((0, HORIZON), (480, HORIZON), HAIR, G3)

    # glitter follows the beam: centred under the beam's far reaches (72 % of its length)
    gx = project(0.72 * LW, theta, 0)[0]
    spread = lerp(1.6, 0.6, lens)                  # a wider beam lights a wider path
    rng = random.Random(11)
    rows = []
    for off in ROWS:
        y = HORIZON + off
        q = off / ROWS[-1]
        dashes, x = [], 146 + rng.uniform(0, 8)
        while x < 480:
            L = (5 + 34 * q) * rng.uniform(0.7, 1.3)
            dashes.append((x, min(x + L, 482)))
            x += L + (4 + 16 * q) * rng.uniform(0.7, 1.4)
        glints = []
        n = 1 if q < 0.3 else 2
        for j in range(n):
            u = (-1 if (j + len(rows)) % 2 else 1) * (0.25 + 0.6 * j) * rng.uniform(0.6, 1.2)
            cx = gx + u * (3 + 16 * q) * spread + shimmer * 2.0 * math.sin(2.1 * len(rows) + 3.3 * j + 6 * shimmer)
            gl = (3 + 10 * q) * (0.6 + 0.4 * spread)
            glints.append((cx - gl / 2, cx + gl / 2))
        rows.append((y, q, dashes, glints))

    def draw_row(y, q, dashes, glints):
        F.part = "ripples"
        col = G2 if q < 0.45 else G3
        for a, b in dashes:
            F.line((a, y), (b, y), HAIR, col)
        F.part = "glints"
        for a, b in glints:
            if b > 150:
                F.line((max(a, 150), y), (b, y), HAIR if q < 0.5 else LINE, G5 if note > 0.5 else G4)

    for y, q, dashes, glints in rows:
        if y < FOG_FOOT:
            draw_row(y, q, dashes, glints)

    # ------------------------------------------------ fog: a hatched bank rising off the sea
    if fog > 0:
        F.part = "fog"
        yt = HORIZON - FOG_TOP * fog
        top = [(x, yt + 2.5 * math.sin(x / 19 + 1) + 1.5 * math.sin(x / 7.3)) for x in range(-4, 489, 16)]
        bank = top + [(484, FOG_FOOT), (-4, FOG_FOOT)]
        F.poly(bank, G0)
        F.hatch(bank, G3, pitch=6.0, slope=-1)
        F.ribbon(top, HAIR, G3)

    for y, q, dashes, glints in rows:
        if y >= FOG_FOOT:
            draw_row(y, q, dashes, glints)

    # ------------------------------------------------ the headland: one clean profile
    F.part = "headland"
    prof = headland()
    F.poly(prof + [(195, 221), (-2, 221)], G0)
    F.ribbon(prof, LINE, G4)

    # ------------------------------------------------ the lighthouse, whole, from outside
    F.part = "tower"
    yb, ys, yd = 168.0, 90.0, 80.0          # base, shaft top, gallery deck top
    F.body([(TX - 27, 174), (TX - 27, yb), (TX + 27, yb), (TX + 27, 174)], G4, LINE)   # plinth
    outline = [(TX - 21, yb), (TX - 13, ys), (TX - 20, 84), (TX - 20, yd), (TX + 20, yd), (TX + 20, 84),
               (TX + 13, ys), (TX + 21, yb)]
    F.body(outline, G5, SUBJ)
    F.line((TX - 13, ys), (TX + 13, ys), HAIR, G4)                 # corbel line under the gallery
    # door, arched, at the foot
    door = [(TX - 4, yb)] + [(TX - 4 * math.cos(math.pi * k / 8), yb - 11 - 4 * math.sin(math.pi * k / 8))
                             for k in range(9)] + [(TX + 4, yb)]
    F.body(door, G4, HAIR)
    # two small windows up the shaft
    for wy in (138.0, 112.0):
        F.body([(TX - 2.5, wy - 4), (TX + 2.5, wy - 4), (TX + 2.5, wy + 4), (TX - 2.5, wy + 4)], G4, HAIR)
    # gallery rail: top rail and posts
    F.line((TX - 19, 71), (TX + 19, 71), HAIR, G4)
    for k in range(5):
        x = TX - 19 + k * 38 / 4
        if abs(x - TX) > 12:
            F.line((x, 71), (x, yd), HAIR, G4)
    # lantern: glazing, two astragals and a sill, black so the beam starts behind its glass
    lw, lt = 11.0, 56.0
    F.body([(TX - lw, yd), (TX - lw, lt), (TX + lw, lt), (TX + lw, yd)], G5, LINE)
    for s in (-1, 1):
        F.line((TX + s * 6, lt + 1), (TX + s * 6, 76), HAIR, G4)
    F.line((TX - lw, 76), (TX + lw, 76), HAIR, G4)
    # dome, ventilator ball and finial
    dome = [(TX + 13 * math.cos(math.pi * k / 14), lt - 11 * math.sin(math.pi * k / 14)) for k in range(15)]
    F.body(dome, G5, LINE)
    F.circle(TX, lt - 13.6, 2.6, G0, G5, LINE)
    F.line((TX, lt - 16.5), (TX, lt - 22), HAIR, G5)

    # the lamp: the one brightest thing. Hollow at rest, lit and larger on a note
    F.part = "lamp"
    sc = lerp(1.0, 1.6, note)
    shape = vesica(LAMP[0], LAMP[1], 4.5 * sc, 11 * sc)
    if note > 0.02:
        F.poly(shape, G7)
    else:
        F.poly(shape, G0, G7, HAIR)
    return F


# ---------------------------------------------------------------- output
def render(svg_path: Path, png_path: Path):
    subprocess.run(["rsvg-convert", "-o", str(png_path), str(svg_path)], check=True)


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "opxy" / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def black_share(png: Path) -> float:
    rows = load_tool("perceptibility").decode_png(png.read_bytes())
    body = [v for r in rows[21:] for v in r]
    return sum(1 for v in body if v < 8) / len(body)


def main():
    frames = {"rest": (dict(DEFAULTS), {})}
    for name in CONTROLS:
        for v in (0, 50, 100):
            c = dict(DEFAULTS)
            c[name] = v / 100
            frames[f"{name}-{v}"] = (c, {})
    written = []
    for stem, (c, kw) in frames.items():
        F = draw(c, title=stem, **kw)
        p = HERE / f"{stem}.svg"
        p.write_text(F.svg())
        render(p, p.with_suffix(".png"))
        written.append(p)
        if stem == "rest":
            print("rest node count by part:", F.count, "total", sum(F.count.values()))
    for p in written:
        print(f"{p.stem:10s} black {black_share(p.with_suffix('.png')) * 100:5.1f} %")

    with tempfile.TemporaryDirectory(dir=HERE, prefix="_tmp_") as td:
        td = Path(td)
        # before / after at 1:1
        subprocess.run(["montage", "-background", "#161616", "-fill", "#969696", "-pointsize", "11",
                        "-label", "v5 (pass 02)", str(V5_PNG), "-label", "refined rest",
                        str(HERE / "rest.png"), "-tile", "2x1", "-geometry", "+16+12",
                        str(HERE / "before-after.png")], check=True)
        # contact sheet at 1:1: rest, then each control 0 / 50 / 100
        args = ["montage", "-background", "#161616", "-fill", "#969696", "-pointsize", "11"]
        args += ["-label", "rest", str(HERE / "rest.png"), "null:", "null:"]
        for name in CONTROLS:
            for v in (0, 50, 100):
                args += ["-label", f"{name} {v}", str(HERE / f"{name}-{v}.png")]
        args += ["-tile", "3x5", "-geometry", "+16+12", str(HERE / "contact.png")]
        subprocess.run(args, check=True)
        motion(td)
        playing(td)


def motion(td: Path):
    """A note held while the light sweeps, then the release settling. 25 fps, 1:1.
    Sweep is set to 50 (6.0 st) so the turn is easy to see; everything else at default."""
    c = dict(DEFAULTS)
    c["sweep"] = 0.5
    fps, total = 25, 6.4
    on, off = 0.6, 4.6
    tmax = math.radians(SWEEP_MAX * c["sweep"])
    out = td / "gif"
    out.mkdir()
    for i in range(int(total * fps)):
        t = i / fps
        if t < on:
            note, cas, theta, front, sh = 0.0, 0.0, tmax, None, 0.0
        elif t < off:
            a = t - on
            note = ease(a / 0.18)
            cas = ease(a / 0.3)
            theta = tmax * (0.5 + 0.5 * math.cos(math.pi * a))      # 0.5 Hz: leans in and returns
            front = int(a * 12.5)                                    # one band per two frames
            sh = a
        else:
            r = t - off
            note = 1 - ease(r / 0.6)
            cas = 1 - ease(r / 0.6)
            a = off - on
            theta = tmax + (tmax * (0.5 + 0.5 * math.cos(math.pi * a)) - tmax) * (1 - ease(r / 0.4))
            front = None
            sh = (off - on) if r < 0.6 else (off - on)
            if note < 0.02:
                note, cas = 0.0, 0.0
        F = draw(c, note=note, theta=theta, front=front, cascade=cas, shimmer=sh if note > 0 else 0.0,
                 title=f"motion {i}")
        svg = out / f"f{i:04d}.svg"
        svg.write_text(F.svg())
        render(svg, svg.with_suffix(".png"))
    gif = HERE / "motion.gif"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(out / "f%04d.png"),
                    "-vf", "split[a][b];[a]palettegen=max_colors=32[p];[b][p]paletteuse=dither=none",
                    "-loop", "0", str(gif)], check=True)
    print("wrote", gif.relative_to(REPO))


def playing(td: Path):
    """A held-note frame for the note-response check (not kept): defaults, lit, a front out."""
    F = draw(dict(DEFAULTS), note=1.0, cascade=1.0, front=2, shimmer=1.3, title="playing")
    (HERE / "_playing.svg").write_text(F.svg())
    print("playing node count by part:", F.count)


if __name__ == "__main__":
    sys.exit(main())
