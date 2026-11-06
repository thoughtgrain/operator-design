#!/usr/bin/env python3
"""Relay, picked v3 (pass 02) cleaned up for 1:1: a cradle of hanging steel balls.

The owner picked v3 of passes/02-subject (a long cradle of hanging balls, hatched
mass: a blow handed ball to ball down the row and out the far end, swinging back
in as the recirculation) and asked for clean-up and readability. Same idea and
composition; what changed is in refine.md. In short:

    camera      lower, more frontal, closer: the balls are ~2x the area, the frame
                is two end posts and one top rail pair instead of crossing wireframe
    strings     one narrow V per ball (front rail, back rail, same x), no fan
    balls       one light (upper left): hatched shadow crescent lower right, a
                hairline highlight upper left; the output ball is the one bright thing
    swings      each end ball's path drawn as a dashed Line under the ball, not a
                faint dashed hairline through its centre
    base        a quiet outline slab, no hatch

Controls (definition.json), 0..1:

    stages    count: 7 .. 18 balls in a row of fixed length (they shrink as they multiply)
    leak      shape: interior balls take a flat on their struck (left) face, the lost cap
              hatched, lose their shine and shrink a little so they stop touching
    clock     position: each ball hangs on its own string length, up to ~±20 px
    feedback  rotation: how far the input ball has swung back out, 0 .. 40 degrees

An effect page gets its controls (slots), track, shift and elapsed, not the audio,
so the swing is a notional test note, frozen at the moment it leaves the far end.

    python3 screens/relay/frames/build.py

Device rules kept: one subpath per path, <= 64 points, open lines as closed filled
ribbons, explicit paint on every leaf, grey only (never red), <= 4 fractional digits.
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULTS = {"stages": 0.5, "leak": 0.0, "clock": 0.0, "feedback": 0.35}
LABELS = ["stages", "leak", "clock", "feedback"]

G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
FONT = "UniversNextPro-Light"
HAIR, LINE, SUBJ = 1.0, 1.5, 2.0          # the three weights (craft.md)


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- header values
def header_values(c: dict) -> list[str]:
    secs = 0.01 * (100.0 ** c["stages"])              # exponential 0.01 .. 1.0 s
    if secs >= 0.9995:
        st = f"{secs:.1f}s"
    else:
        st = f"{round(secs * 1000)}ms"
    return [st, f"{round(c['leak'] * 100)}", f"{c['clock']:.2f}", f"{round(c['feedback'] * 100)}"]


# ---------------------------------------------------------------- 2D primitives
def dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if not out or math.dist(out[-1], p) >= 0.25:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


class Frame:
    def __init__(self, title: str, values: list[str]):
        self.title = title
        self.values = values
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{f(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def face(self, pts, colour, sw=LINE, fill=G0):
        """A closed outline over a black body (hidden-line)."""
        self.poly(pts, fill, colour, sw)

    def ribbon(self, pts, w, colour):
        """An open line of width w drawn as filled closed ribbons, <= 30 points a piece."""
        pts = dedupe(pts)
        if len(pts) < 2:
            return
        n, i = 30, 0
        while i < len(pts) - 1:
            self._piece(pts[i:i + n + 1], w, colour)
            i += n

    def _piece(self, seg, w, colour):
        if len(seg) < 2:
            return
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
        self.poly(left + right[::-1], colour)

    def line(self, a, b, w, colour):
        if math.dist(a, b) >= 3.0:  # anything shorter doesn't read at 1:1
            self._piece([a, b], w, colour)

    def dashed(self, pts, w, colour, on=5.0, off=3.0):
        """A dashed open line: dashes as separate ribbons, each >= 3 px long."""
        pts = dedupe(pts)
        acc, draw, cur = 0.0, True, [pts[0]] if pts else []
        for a, b in zip(pts, pts[1:]):
            seg = math.dist(a, b)
            t = 0.0
            while t < seg:
                lim = on if draw else off
                step = min(lim - acc, seg - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg)
                if draw:
                    cur.append(p)
                if acc >= lim - 1e-9:
                    if draw and len(cur) > 1:
                        self.ribbon(cur, w, colour)
                    draw, acc, cur = not draw, 0.0, [p]
        if draw and len(cur) > 1 and acc >= 3:
            self.ribbon(cur, w, colour)

    def hatch(self, poly, colour=G3, gap=3.2, w=HAIR, minlen=4.6):
        """45° hairlines clipped to a polygon (any simple shape), gap px apart."""
        poly = dedupe(poly)
        if len(poly) < 3:
            return
        us = [x + y for x, y in poly]
        step = gap * math.sqrt(2)
        c = math.floor(min(us) / step) * step + step / 2
        while c < max(us):
            hits = []
            for i in range(len(poly)):
                (x1, y1), (x2, y2) = poly[i - 1], poly[i]
                u1, u2 = x1 + y1, x2 + y2
                if (u1 - c) * (u2 - c) < 0:
                    t = (c - u1) / (u2 - u1)
                    hits.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
            hits.sort(key=lambda p: p[0] - p[1])
            for a, b in zip(hits[0::2], hits[1::2]):
                if math.dist(a, b) >= minlen:
                    self.line(a, b, w, colour)
            c += step

    def svg(self) -> str:
        head = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
            f"  <title>relay · cradle · {self.title}</title>",
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
            head.append(f'    <text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{c}" stroke="none" '
                        f'font-family="{FONT}" font-size="20px">{self.values[i]}</text>')
        head.append("  </g>")
        body = ['  <g id="relay_art">'] + ["    " + s for s in self.items] + ["  </g>"]
        return "\n".join(head + body + ["</svg>", ""])


# ---------------------------------------------------------------- 3D: one camera
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add3(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / ln)


class Camera:
    """Perspective camera, z up, placed by yaw/pitch/distance round a target."""

    def __init__(self, target, yaw_deg, pitch_deg, dist):
        yw, pt = math.radians(yaw_deg), math.radians(pitch_deg)
        self.eye = (target[0] + dist * math.cos(pt) * math.sin(yw),
                    target[1] - dist * math.cos(pt) * math.cos(yw),
                    target[2] + dist * math.sin(pt))
        self.fwd = norm(sub(target, self.eye))
        self.right = norm(cross(self.fwd, (0, 0, 1)))
        self.up = cross(self.right, self.fwd)
        self.f, self.cx, self.cy = 1.0, 0.0, 0.0

    def raw(self, p):
        d = sub(p, self.eye)
        z = dot(d, self.fwd)
        return dot(d, self.right) / z, -dot(d, self.up) / z

    def fit(self, pts, box):
        r = [self.raw(p) for p in pts]
        xs, ys = [p[0] for p in r], [p[1] for p in r]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        x0, y0, x1, y1 = box
        self.f = min((x1 - x0) / bw, (y1 - y0) / bh)
        self.cx = (x0 + x1) / 2 - self.f * (min(xs) + max(xs)) / 2
        self.cy = (y0 + y1) / 2 - self.f * (min(ys) + max(ys)) / 2
        return self

    def p(self, P):
        x, y = self.raw(P)
        return (self.cx + self.f * x, self.cy + self.f * y)

    def ps(self, pts):
        return [self.p(P) for P in pts]

    def depth(self, P):
        return dot(sub(P, self.eye), self.fwd)


def box_corners(o, ux, uy, uz):
    c = {}
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                c[i, j, k] = add3(add3(add3(o, mul(ux, i)), mul(uy, j)), mul(uz, k))
    return c


BOX_FACES = {
    "x0": [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
    "x1": [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)],
    "y0": [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)],
    "y1": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
    "z0": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
    "z1": [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)],
}


def visible_faces(cam, c):
    centre = mul(add3(c[0, 0, 0], c[1, 1, 1]), 0.5)
    out = []
    for name, keys in BOX_FACES.items():
        W = [c[k] for k in keys]
        n = cross(sub(W[1], W[0]), sub(W[3], W[0]))
        fc = mul(add3(W[0], W[2]), 0.5)
        if dot(n, sub(fc, centre)) < 0:
            n = mul(n, -1)
        if dot(n, sub(cam.eye, fc)) > 0:
            out.append((name, W, cam.ps(W)))
    return out


def circle_pts(cx, cy, r, n=40, a0=0.0, a1=2 * math.pi, closed=True):
    m = n if closed else n + 1
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(m)]


def crescent(cx, cy, r, k=0.42, n=18):
    """The shadow side of a ball lit from the upper left: the lower-right half of its
    outline, back along a flattened half-ellipse (the terminator)."""
    a0 = math.atan2(0.8, 0.6)                      # direction away from the light
    outer = [(cx + r * math.cos(a0 - math.pi / 2 + math.pi * j / n), cy + r * math.sin(a0 - math.pi / 2 + math.pi * j / n))
             for j in range(n + 1)]
    ax, ay = math.cos(a0 + math.pi / 2), math.sin(a0 + math.pi / 2)
    dx, dy = math.cos(a0), math.sin(a0)
    term = []
    for j in range(1, n):
        t = math.pi * j / n
        u, v = math.cos(t), math.sin(t) * k
        term.append((cx + r * (ax * u + dx * v), cy + r * (ay * u + dy * v)))
    return outer + term


# ---------------------------------------------------------------- the model
ROW = 26.0            # the row's length in world units, whatever the count
HANG = 6.2            # pivot to ball centre
W = 3.3               # half the rail spacing: each ball hangs in a V from both rails
OUT = math.radians(36)            # the note leaving at the far end (fixed)
FB_MAX = math.radians(60)         # how far the input ball can come back
XR = ROW / 2 + HANG * math.sin(OUT) + 1.1       # end posts clear both swinging balls
XL = -(ROW / 2 + HANG * math.sin(FB_MAX) + 1.1)  # at their largest (the input swings further)
XM = (XL + XR) / 2
TOP = HANG                        # rail height; balls hang at z = 0
BASE_Z = -3.6                     # top of the base slab
SEED = 5


def model(c: dict):
    """Balls as (centre, radius, pivot x, role, dent) from the four controls."""
    st, lk, ck, fb = c["stages"], c["leak"], c["clock"], c["feedback"]
    n = int(round(7 + 11 * st))            # 7 .. 18
    rnd = random.Random(SEED)
    r = ROW / (2 * n)
    # seeded per-ball draws, taken in a fixed order so they don't reshuffle as n moves
    jit = [rnd.uniform(-1, 1) for _ in range(18)]
    prio = [rnd.random() for _ in range(18)]
    xs = [-ROW / 2 + r + 2 * r * i for i in range(n)]
    # leak: the interior balls with the lowest priority dent first, more as leak rises
    k_dent = int(round(lk * 0.55 * (n - 2)))
    interior = sorted(range(1, n - 1), key=lambda i: prio[i])
    dented = set(interior[:k_dent])
    depth = 0.28 + 0.22 * lk                # how deep the flat cuts, as a share of r
    back = FB_MAX * fb
    balls = []
    for i in range(n):
        l = HANG + ck * 1.55 * jit[i]      # clock: each ball on its own string length
        rr = r * (0.84 if i in dented else 1.0)
        if i == n - 1:
            a, role = OUT, "out"
        elif i == 0:
            a, role = -back, "in"
        else:
            a, role = 0.0, "mid"
        centre = (xs[i] + l * math.sin(a), 0.0, TOP - l * math.cos(a))
        balls.append({"c": centre, "r": rr, "px": xs[i], "l": l, "a": a, "role": role,
                      "dent": depth if i in dented else 0.0})
    return balls


def camera():
    cam = Camera(target=(XM, 0.0, 1.2), yaw_deg=8.0, pitch_deg=13.0, dist=78.0)
    key = [(XL - 0.6, -W - 0.7, BASE_Z - 0.5), (XR + 0.6, -W - 0.7, BASE_Z - 0.5),
           (XL, W, TOP + 0.3), (XR, W, TOP + 0.3), (XL, -W, TOP + 0.3), (XR, -W, TOP + 0.3)]
    return cam.fit(key, (10, 34, 470, 206))


def draw(c: dict, title: str) -> Frame:
    fr = Frame(title, header_values(c))
    cam = camera()
    balls = model(c)

    # base: a quiet slab, outline only
    base = box_corners((XL - 0.6, -W - 0.7, BASE_Z - 0.5), (XR - XL + 1.2, 0, 0), (0, 2 * W + 1.4, 0), (0, 0, 0.5))
    for name, _, S in visible_faces(cam, base):
        fr.face(S, G2, LINE)

    # end posts: one solid post at each end, centred between the rails, shadow face hatched
    pw = 0.55
    for px in (XL, XR):
        post = box_corners((px - pw / 2, -pw / 2, BASE_Z), (pw, 0, 0), (0, pw, 0), (0, 0, TOP - BASE_Z + 0.35))
        for name, _, S in visible_faces(cam, post):
            if name == "z1":
                continue
            fr.face(S, G4 if name == "y0" else G3, LINE)
            if name in ("x0", "x1"):
                fr.hatch(S, G2, gap=3.2, minlen=4.6)

    # back rail and the crossbars that carry both rails
    rail = lambda dy: [cam.p((XL, dy, TOP)), cam.p((XR, dy, TOP))]
    fr.ribbon(rail(W), LINE, G3)
    for px in (XL, XR):
        fr.line(cam.p((px, -W, TOP)), cam.p((px, W, TOP)), LINE, G3)

    # swept bands: the room each end ball has swung through, hatched as a ghost
    # (there, but not a body), under everything that hangs
    for b in balls:
        if b["role"] == "mid" or abs(b["a"]) < math.radians(2):
            continue
        a1, l, rb = b["a"], b["l"], b["r"]
        steps = max(4, int(abs(a1) / math.radians(3)))
        arc = [a1 * t / steps for t in range(steps + 1)]
        band = [(b["px"] + (l + rb) * math.sin(a), 0, TOP - (l + rb) * math.cos(a)) for a in arc] + \
               [(b["px"] + (l - rb) * math.sin(a), 0, TOP - (l - rb) * math.cos(a)) for a in reversed(arc)]
        fr.hatch(cam.ps(band), G2, gap=3.0)

    # strings: one V per ball, back leg then front leg, drawn under the balls
    for b in balls:
        cx, _, cz = b["c"]
        tip = (cx, 0.0, cz)
        hot = b["role"] != "mid"
        colour = G4 if hot else G3
        for dy in (W, -W):
            fr.line(cam.p((b["px"], dy, TOP)), cam.p(tip), LINE if hot else HAIR, colour)

    # swing paths: each end ball's track, a dashed Line just outside its bottom
    for b in balls:
        if b["role"] == "mid" or abs(b["a"]) < math.radians(2):
            continue
        rad = b["l"] + b["r"] + 0.45
        a1 = b["a"]
        steps = max(4, int(abs(a1) / math.radians(3)))
        pts = [cam.p((b["px"] + rad * math.sin(a1 * t / steps), 0, TOP - rad * math.cos(a1 * t / steps)))
               for t in range(steps + 1)]
        fr.dashed(pts, LINE, G5, on=5, off=3.5)

    # balls, far to near
    for b in sorted(balls, key=lambda b: -cam.depth(b["c"])):
        cx, cy = cam.p(b["c"])
        rr = b["r"] * cam.f / cam.depth(b["c"])
        out = b["role"] == "out"
        edge, ew = (G7, SUBJ) if out else ((G5, LINE) if b["role"] == "in" else (G4, LINE))
        if b["dent"] > 0:
            # a dent pushed into the struck (left) face; the metal it lost is
            # hatched inside the ball's old outline, and a dented ball loses its shine
            d, th, h = b["dent"], math.pi, math.radians(58)
            def R(a):
                u = (a - th + math.pi) % (2 * math.pi) - math.pi
                return rr * (1 - d * math.cos(u / h * math.pi / 2) ** 2) if abs(u) < h else rr
            ring = [(cx + R(a) * math.cos(a), cy + R(a) * math.sin(a))
                    for a in [2 * math.pi * k / 48 for k in range(48)]]
            fr.face(ring, edge, ew)
            arc = [th - h + 2 * h * k / 14 for k in range(15)]
            lost = [(cx + rr * math.cos(a), cy + rr * math.sin(a)) for a in arc] + \
                   [(cx + R(a) * math.cos(a), cy + R(a) * math.sin(a)) for a in reversed(arc[1:-1])]
            fr.hatch(lost, G3, gap=3.0, minlen=4.6)
        else:
            fr.face(circle_pts(cx, cy, rr), edge, ew)
        fr.hatch(crescent(cx, cy, rr - 1.4), G4 if out else G3, gap=3.2)
        if b["dent"] == 0:
            # the highlight: a short hairline arc on the lit side
            hl = circle_pts(cx, cy, rr * 0.62, n=8, a0=math.radians(198), a1=math.radians(252), closed=False)
            if math.dist(hl[0], hl[-1]) >= 3.0:
                fr.ribbon(hl, HAIR, G7 if out else G5)

    # front rail last, over the strings' tops
    fr.ribbon(rail(-W), LINE, G4)
    return fr


# ---------------------------------------------------------------- frames
def frames():
    yield "rest", dict(DEFAULTS)
    for name in LABELS:
        for v in (0, 50, 100):
            c = dict(DEFAULTS)
            c[name] = v / 100
            yield f"{name}-{v}", c


def sheet(rows, out: Path, label_h=16, gap=12, pad=12) -> None:
    """Tile 1:1 PNGs into rows on a dark ground, a small label over each (outside the frame)."""
    from PIL import Image, ImageDraw
    cols = max(len(r) for r in rows)
    w = pad * 2 + cols * 480 + (cols - 1) * gap
    h = pad * 2 + len(rows) * (220 + label_h) + (len(rows) - 1) * gap
    im = Image.new("RGB", (w, h), (38, 38, 38))
    dr = ImageDraw.Draw(im)
    for j, row in enumerate(rows):
        for i, (label, path) in enumerate(row):
            x = pad + i * (480 + gap)
            y = pad + j * (220 + label_h + gap)
            dr.text((x, y + 2), label, fill=(200, 200, 200))
            im.paste(Image.open(path).convert("RGB"), (x, y + label_h))
    im.save(out)


def main(argv) -> None:
    for stem, c in frames():
        svg = HERE / f"{stem}.svg"
        svg.write_text(draw(c, stem).svg())
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-b", "black", str(svg),
                        "-o", str(HERE / f"{stem}.png")], check=True)
        print(svg)
    v3 = HERE.parent / "passes" / "02-subject" / "v3" / "rest.png"
    sheet([[("v3 as picked (pass 02)", v3), ("cleaned rest", HERE / "rest.png")]], HERE / "before-after.png")
    rows = [[("rest", HERE / "rest.png")]]
    for name in LABELS:
        rows.append([(f"{name} {v}", HERE / f"{name}-{v}.png") for v in (0, 50, 100)])
    sheet(rows, HERE / "contact.png")
    print(HERE / "before-after.png", HERE / "contact.png")


if __name__ == "__main__":
    main(sys.argv[1:])
