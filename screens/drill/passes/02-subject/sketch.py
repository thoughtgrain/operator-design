#!/usr/bin/env python3
"""drill · subject pass 02 · rest-frame sketches, five views of one crank hand drill.

The owner's direction for this pass: true to the name, an old crank-style hand
drill (a brace, or an eggbeater drill with its gear wheel and handle). Every
variant is that drill, each from its own angle and way of drawing. Every 3D
thing is modelled in world units and projected through one camera per frame
(craft.md, Think in 3D). Rest frames at the definition's defaults:
ratio 2.00, teeth 6, wear 0 %, bite 35 %.

No text below the header: the stock header is copied from the template as-is.
States are line, movement or hatching (45 deg hairlines, >= 3 px apart, clipped
by geometry), never a lighter grey fill. One #CDCDCD element per frame.

Run: python3 screens/drill/passes/02-subject/sketch.py
"""
from __future__ import annotations

import math
import pathlib
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

# defaults, as control positions and as values
RATIO, TEETH, WEAR, BITE = 2.0, 6, 0.0, 0.35
RATIO_N = math.log(RATIO / 0.5) / math.log(16)   # 0.5 at 2.00

G = {0: "#000000", 1: "#323232", 2: "#4B4B4B", 3: "#646464", 4: "#7D7D7D",
     5: "#969696", 6: "#AFAFAF", 7: "#CDCDCD"}
BLACK, BRIGHT = G[0], G[7]
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2
BODY_TOP = 22


# ------------------------------------------------------------- vectors ----

def label_header(svg: str) -> str:
    """Put this machine's titles and default values into the template's header slots (p1–p4, 0),
    taken from the first pass's header (matched by position), so every pass shows the same header."""
    import re as _re
    ref = (pathlib.Path(__file__).resolve().parent.parent / "01-subject" / "v1" / "rest.svg").read_text(encoding="utf-8")
    by_pos = {m.group(1): m.group(2) for m in _re.finditer(r'<text transform="(matrix\([^)]*\))"[^>]*>([^<]*)</text>', ref)}
    return _re.sub(r'(<text transform="(matrix\([^)]*\))"[^>]*>)(p[1-4]|0)(</text>)',
                   lambda m: m.group(1) + by_pos.get(m.group(2), m.group(3)).rstrip("%") + m.group(4), svg)  # ux.md: amounts without %

def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / ln)


class Camera:
    """One pinhole camera: world z is up; screen y grows down."""

    def __init__(self, eye, target, px_per_unit, cx, cy):
        self.eye = eye
        self.fwd = norm(sub(target, eye))
        self.right = norm(cross(self.fwd, (0, 0, 1)))
        self.up = cross(self.right, self.fwd)
        self.f = px_per_unit * math.sqrt(dot(sub(target, eye), sub(target, eye)))
        self.cx, self.cy = cx, cy

    def depth(self, p):
        return dot(sub(p, self.eye), self.fwd)

    def __call__(self, p):
        d = sub(p, self.eye)
        z = dot(d, self.fwd)
        return (self.cx + self.f * dot(d, self.right) / z, self.cy - self.f * dot(d, self.up) / z)

    def proj(self, pts):
        return [self(p) for p in pts]

    def facing(self, p, n):
        """True when the surface normal n at p points at the camera."""
        return dot(n, sub(self.eye, p)) > 0


# ------------------------------------------------------------- svg --------
def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts, closed=True, gap=0.4):
    o = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, o[-1]) > gap:
            o.append(p)
    while closed and len(o) > 3 and math.dist(o[-1], o[0]) < 0.6:
        o.pop()
    return o


def normal2(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    return (-dy / ln, dx / ln)


def offset(pts, h, closed=False):
    """Offset a polyline by h (mitred, capped)."""
    n = len(pts)
    out = []
    for j in range(n):
        ns = []
        if closed or j > 0:
            ns.append(normal2(pts[j - 1], pts[j]))
        if closed or j < n - 1:
            ns.append(normal2(pts[j], pts[(j + 1) % n]))
        nx = sum(a for a, _ in ns)
        ny = sum(b for _, b in ns)
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        m = 1.0
        if len(ns) == 2:
            c = ns[0][0] * nx + ns[0][1] * ny
            m = min(1 / max(c, 0.35), 2.5)
        out.append((pts[j][0] + nx * h * m, pts[j][1] + ny * h * m))
    return out


class Svg:
    def __init__(self):
        self.parts: list[str] = []

    def path(self, pts, fill, stroke, sw):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        if len(pts) > 64:
            raise ValueError(f"outline with {len(pts)} points")
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        self.parts.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def ribbon(self, pts, width, col):
        """An open polyline as a thin closed ribbon (never a stroke traced back)."""
        pts = dedupe(pts, closed=False)
        if len(pts) < 2:
            return
        step = 28
        i = 0
        while i < len(pts) - 1:
            chunk = pts[i:i + step + 1]
            h = max(width - 0.3, 0.4) / 2
            L = offset(chunk, h)
            R = offset(chunk, -h)
            self.path(L + R[::-1], col, col, 0.3)
            i += step

    def loop(self, pts, width, col):
        """A closed polyline drawn as a ribbon all the way round (two halves)."""
        n = len(pts)
        half = n // 2
        self.ribbon(pts[:half + 1], width, col)
        self.ribbon(pts[half:] + [pts[0]], width, col)

    def write(self, path: Path, title: str):
        tmpl = (ROOT / "opxy" / "templates" / "frame.svg").read_text()
        head = tmpl.split("  <!-- Palette entries")[0]
        head = head.split("<!--", 1)[0] + head.split("-->", 1)[1].lstrip("\n")  # drop the starter comment
        pal = ('  <path id="drill_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>\n'
               '  <path id="drill_palette_1" d="M 710 300 L 714 300 L 714 304 Z" fill="#646464" stroke="#646464" stroke-width="2"/>\n')
        body = "\n".join("  " + p for p in self.parts)
        path.write_text(label_header(head.rstrip() + f"\n  <title>{title}</title>\n" + pal + body + "\n</svg>\n"))


# ------------------------------------------------------------- hatching ---
def hatch(svg, rings, gap=4.0, col=G[2], width=HAIR, phase=0.0, clip_top=BODY_TOP):
    """45 deg hairlines inside the even-odd union of `rings`, clipped by geometry."""
    r2 = math.sqrt(0.5)
    edges = []
    for ring in rings:
        for a, b in zip(ring, ring[1:] + ring[:1]):
            edges.append((a, b))
    cs = [(p[0] + p[1]) * r2 for ring in rings for p in ring]
    c = math.floor(min(cs) / gap) * gap + phase
    while c < max(cs):
        hits = []
        for a, b in edges:
            ca, cb = (a[0] + a[1]) * r2, (b[0] + b[1]) * r2
            if (ca - c) * (cb - c) < 0:
                t = (c - ca) / (cb - ca)
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                hits.append(((x - y) * r2, x, y))
        hits.sort()
        for (s0, x0, y0), (s1, x1, y1) in zip(hits[::2], hits[1::2]):
            # pull the ends in a little so hatching never touches the outline
            ln = s1 - s0
            if ln < 4:
                continue
            k = 1.6 / ln
            p0 = (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
            p1 = (x1 - (x1 - x0) * k, y1 - (y1 - y0) * k)
            if p0[1] < clip_top and p1[1] < clip_top:
                continue
            if p0[1] < clip_top:
                t = (clip_top - p0[1]) / (p1[1] - p0[1]); p0 = (p0[0] + (p1[0] - p0[0]) * t, clip_top)
            if p1[1] < clip_top:
                t = (clip_top - p1[1]) / (p0[1] - p1[1]); p1 = (p1[0] + (p0[0] - p1[0]) * t, clip_top)
            svg.ribbon([p0, p1], width, col)
        c += gap


# ------------------------------------------------------------- solids -----
def ring_pts(c, r, u, v, n=40, a0=0.0, a1=2 * math.pi):
    return [add(c, add(mul(u, r * math.cos(a0 + (a1 - a0) * i / n)), mul(v, r * math.sin(a0 + (a1 - a0) * i / n))))
            for i in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-9 else 1))]


def revolve_x(cam, profile, y0, z0, n=24):
    """A solid of revolution about the line (y0, z0) along x.

    profile: [(x, r), ...]. Returns the projected silhouette and, per profile
    station, the projected visible half-ring (the arcs the camera sees).
    """
    top, bot, arcs = [], [], []
    for x, r in profile:
        c = (x, y0, z0)
        pts = ring_pts(c, r, (0, 1, 0), (0, 0, 1), n)
        scr = cam.proj(pts)
        # silhouette: extremes across the axis direction on screen
        a = cam((x - 1, y0, z0)); b = cam((x + 1, y0, z0))
        ax = norm((b[0] - a[0], b[1] - a[1], 0))
        nrm = (-ax[1], ax[0])
        ds = [(p[0] - scr[0][0]) * nrm[0] + (p[1] - scr[0][1]) * nrm[1] for p in scr]
        top.append(scr[ds.index(min(ds))])
        bot.append(scr[ds.index(max(ds))])
        vis = [scr[i] for i in range(n) if cam.facing(pts[i], sub(pts[i], c))]
        arcs.append(vis)
    return top + bot[::-1], arcs


# =========================================================================
# v1 · the mark the process leaves: the shaving curl out of the bored hole,
#      single-weight contour
# =========================================================================
def v1():
    s = Svg()
    cam = Camera(eye=(-60, -470, 210), target=(120, 0, 30), px_per_unit=1.05, cx=240, cy=128)
    W = LINE  # the one weight this language uses (hatching would be hairline; none here)

    # the board: a slab with the bored hole, top face at z = 0
    bx0, bx1, by0, by1, bt = -120, 52, -40, 60, 26
    top = [(bx0, by0, 0), (bx1, by0, 0), (bx1, by1, 0), (bx0, by1, 0)]
    front = [(bx0, by0, 0), (bx1, by0, 0), (bx1, by0, -bt), (bx0, by0, -bt)]
    side = [(bx1, by0, 0), (bx1, by1, 0), (bx1, by1, -bt), (bx1, by0, -bt)]
    for face in (side, front, top):
        s.path(cam.proj(face), BLACK, G[3], W)
    # end grain on the front edge: the plank's growth lines, a few, ≥ 6 px apart
    for k, z in enumerate((-7, -15)):
        pts = [(bx0 + 6 + i * (bx1 - bx0 - 12) / 12, by0, z + 1.6 * math.sin(i * 0.9 + k)) for i in range(13)]
        s.ribbon(cam.proj(pts), W, G[2])

    hole_r = 11
    hole = ring_pts((0, 0, 0), hole_r, (1, 0, 0), (0, 1, 0), 36)
    s.path(cam.proj(hole), BLACK, G[3], W)
    # the far inner wall of the bore, seen through the mouth
    wall = [add(p, (0, 0, -9)) for p in ring_pts((0, 0, 0), hole_r, (1, 0, 0), (0, 1, 0), 18, math.pi, 2 * math.pi)]
    s.ribbon(cam.proj(wall), W, G[2])

    # the shaving: a helical strip rising out of the hole along an axis
    axis = norm((1.0, 0.06, 0.3))
    u = norm(cross(axis, (0, 0, 1)))
    v = cross(u, axis)
    L = 330.0
    coils = 2.5 + 1.25 * (RATIO * 1.0)        # ratio: coils per length (5 at 2.00)
    width = 4 + BITE * 18                       # bite: how thick a shaving the bite takes
    rad = 18.0
    seg = 18
    n = int(coils * seg)
    rng = random.Random(3)
    tear = [WEAR * 4 * (rng.random() - 0.5) for _ in range(n + 1)]

    def P(i, e):
        t = i / n
        th = 2 * math.pi * coils * t
        sp = 8 + (L - 8) * t + e * width
        r = rad * (0.55 + 0.45 * min(1, t * 4))   # tight where it leaves the hole
        return add(add(mul(axis, sp), mul(u, r * math.cos(th))), mul(v, r * math.sin(th)))

    quads = []
    for i in range(n):
        a0, a1 = P(i, 0), P(i + 1, 0)
        b0, b1 = P(i, 1), P(i + 1, 1)
        mid = mul(add(add(a0, a1), add(b0, b1)), 0.25)
        th = 2 * math.pi * coils * (i + 0.5) / n
        outward = add(mul(u, math.cos(th)), mul(v, math.sin(th)))
        quads.append((cam.depth(mid), i, a0, a1, b0, b1, cam.facing(mid, outward)))
    quads.sort(key=lambda q: -q[0])
    for _, i, a0, a1, b0, b1, out in quads:
        A0, A1, B0, B1 = cam.proj((a0, a1, b0, b1))
        s.path([A0, A1, B1, B0], BLACK, "none", 0)
        col = BRIGHT if out else G[3]
        # wear tears the leading edge
        da = tear[i] if out else 0
        s.ribbon([A0, A1], W, col)
        s.ribbon([(B0[0], B0[1] + da), (B1[0], B1[1] + tear[i + 1] if out else B1[1])], W, col)
        # teeth: a chatter mark across the strip at each tooth (TEETH per coil)
        if out and (i % max(1, round(seg / TEETH))) == 0:
            s.ribbon([((A0[0] + A1[0]) / 2, (A0[1] + A1[1]) / 2), ((B0[0] + B1[0]) / 2, (B0[1] + B1[1]) / 2)], W, G[2])
    # the cut end of the shaving
    e0, e1 = cam(P(n, 0)), cam(P(n, 1))
    s.ribbon([e0, e1], W, BRIGHT)
    return s


# =========================================================================
# v2 · one detail at large scale: the face wheel's rim meeting the pinion,
#      hatched mass; wheel and spindle run off the frame's edges
# =========================================================================
def v2():
    s = Svg()
    cam = Camera(eye=(0, -1200, 0), target=(0, 0, 0), px_per_unit=1.0, cx=240, cy=120)
    R = 150 + 150 * RATIO_N                   # ratio: the wheel grows, its rim flattens
    rim_x = 196                                # the rim's right-most point stays put
    C = (rim_x - 240 - R, 0, 2)                # wheel centre, world (camera looks along +y)
    lugs = 6 * TEETH                           # teeth: lugs round the face (about a seventh in view)
    lug_in, lug_out = R - 26, R - 5
    round_k = WEAR                             # wear: lug corners round off

    def wp(r, a, y=0.0):
        return (C[0] + r * math.cos(a), y, C[2] + r * math.sin(a))

    span = 0.75
    # rim body: outer edge to the lug ring's inside, with the cast web hatched
    outer = [wp(R, a) for a in [-span + 2 * span * i / 30 for i in range(31)]]
    web_r = lug_in - 8
    web = [wp(web_r, a) for a in [span - 2 * span * i / 30 for i in range(31)]]
    rim_poly = clip_top(cam.proj(outer + web))
    s.path(rim_poly, BLACK, G[3], LINE)
    # the web: hatched mass, with a lightening hole cut out of it
    edge = cam.proj([wp(web_r - 5, a) for a in [-span + 2 * span * i / 40 for i in range(41)]])
    web_poly = edge + [(-6, edge[-1][1]), (-6, edge[0][1])]
    hole_c = wp(web_r - 52, -0.08)
    hole = cam.proj(ring_pts(hole_c, 30, (1, 0, 0), (0, 0, 1), 40))
    hatch(s, [web_poly, hole], gap=4.0, col=G[2])
    s.ribbon([p for p in edge if p[1] >= BODY_TOP], LINE, G[3])
    s.path(hole, BLACK, G[3], LINE)

    # lugs: solid bodies on the face, black with a line edge
    pitch = 2 * math.pi / lugs
    half = pitch * 0.27
    for k in range(-lugs, lugs):
        a = k * pitch + pitch * 0.5
        if abs(a) > span - 0.02:
            continue
        rr = 3.5 * round_k
        pts = []
        for r, aa in ((lug_in, a - half), (lug_out, a - half * 0.8), (lug_out, a + half * 0.8), (lug_in, a + half)):
            pts.append(wp(r, aa, -4))
        scr = cam.proj(pts)
        if rr > 0.2:
            scr = rounded(scr, rr)
        if min(p[1] for p in scr) < BODY_TOP + 1:
            continue
        s.path(scr, BLACK, G[5], LINE)

    # the spindle runs across the frame, in front of the face
    sy, sz = -24, 4
    spindle, _ = revolve_x(cam, [(-260, 4), (260, 4)], sy, sz, 16)
    s.path(spindle, BLACK, G[3], LINE)
    # bite: the pinion slides along the spindle onto the lug ring
    px = rim_x - 240 + 18 - BITE * 40
    rp, pl = 15, 30
    sil, arcs = revolve_x(cam, [(px - pl / 2, rp - 2), (px - pl / 2 + 2, rp), (px + pl / 2 - 2, rp), (px + pl / 2, rp - 2)],
                          sy, sz, 24)
    s.path(sil, BLACK, BRIGHT, SUBJ)
    # its teeth: lines along the axis where the ring of teeth is ≥ 3 px apart on screen
    nteeth = 12
    last = None
    for k in range(nteeth):
        a = 2 * math.pi * k / nteeth + 0.13
        p0 = (px - pl / 2 + 3, sy + rp * math.cos(a), sz + rp * math.sin(a))
        if math.cos(a) > 0:   # far side
            continue
        sp0 = cam(p0)
        if last is not None and abs(sp0[1] - last) < 3.2:
            continue
        if abs(sp0[1] - cam((px, sy, sz + rp))[1]) < 3 or abs(sp0[1] - cam((px, sy, sz - rp))[1]) < 3:
            continue
        last = sp0[1]
        s.ribbon([sp0, cam((px + pl / 2 - 3, p0[1], p0[2]))], HAIR, G[5])
    # chuck, cropped by the right edge: the rest of the drill implied
    chuck, _ = revolve_x(cam, [(200, 5), (206, 13), (260, 13)], sy, sz, 16)
    s.path(chuck, BLACK, G[3], LINE)
    hatch(s, [chuck], gap=4.0, col=G[2])
    return s


def clip_top(pts, y0=BODY_TOP):
    """Sutherland-Hodgman: keep the part of a polygon below y0 (the frame's edge under the header)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i - 1], pts[i]
        ina, inb = a[1] >= y0, b[1] >= y0
        if inb:
            if not ina:
                t = (y0 - a[1]) / (b[1] - a[1]); out.append((a[0] + (b[0] - a[0]) * t, y0))
            out.append(b)
        elif ina:
            t = (y0 - a[1]) / (b[1] - a[1]); out.append((a[0] + (b[0] - a[0]) * t, y0))
    return out


def rounded(pts, r):
    """Round a polygon's corners with a short arc each (wear)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1 = math.dist(a, b); d2 = math.dist(b, c)
        k1 = min(r, d1 * 0.45) / d1; k2 = min(r, d2 * 0.45) / d2
        p = (b[0] + (a[0] - b[0]) * k1, b[1] + (a[1] - b[1]) * k1)
        q = (b[0] + (c[0] - b[0]) * k2, b[1] + (c[1] - b[1]) * k2)
        for t in (0, 0.33, 0.66, 1):
            # quadratic bezier p -> b -> q
            x = (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * b[0] + t * t * q[0]
            y = (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * b[1] + t * t * q[1]
            out.append((x, y))
    return out


# =========================================================================
# v3 · the object, literally: a carpenter's brace boring into a board,
#      edge-lit silhouette
# =========================================================================
def lit_edges(svg, poly, col, width, light=(-0.45, -0.89), thresh=0.3):
    """Draw the runs of a closed outline whose outward normal faces the light."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    sgn = 1 if area > 0 else -1   # screen coords: y down
    run = []
    n = len(poly)
    best = None
    flags = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = (dy / ln) * sgn, (-dx / ln) * sgn
        flags.append(nx * light[0] + ny * light[1] > thresh)
    # start at an unlit edge so runs don't wrap
    start = flags.index(False) if False in flags else 0
    for k in range(n):
        i = (start + k) % n
        if flags[i]:
            if not run:
                run = [poly[i]]
            run.append(poly[(i + 1) % n])
        elif run:
            svg.ribbon(run, width, col); run = []
    if run:
        svg.ribbon(run, width, col)


def v3():
    s = Svg()
    cam = Camera(eye=(30, -1400, 120), target=(30, 0, 0), px_per_unit=0.9, cx=238, cy=112)
    rod = 4.0
    throw = 32 + 40 * RATIO_N            # ratio: the brace's sweep (52 at 2.00)
    # the brace's centreline, in its own plane (x-z), y = 0
    cl = [(-176, 0, 0), (-128, 0, 0), (-118, 0, -4), (-110, 0, -throw + 6), (-102, 0, -throw),
          (-22, 0, -throw), (-14, 0, -throw + 6), (-6, 0, -4), (4, 0, 0), (18, 0, 0)]
    scl = cam.proj(cl)
    parts = []
    # head pad: a mushroom knob on the end
    head_prof = [(-214, 6), (-212, 16), (-206, 22), (-198, 23), (-190, 20), (-184, 12), (-180, 7), (-176, 5)]
    sil, _ = revolve_x(cam, head_prof, 0, 0, 24)
    parts.append(("head", sil))
    # the bent rod
    rodp = offset(scl, rod) + offset(scl, -rod)[::-1]
    parts.append(("rod", rodp))
    # the grip sleeve on the sweep
    gx0, gx1 = -92, -32
    grip_prof = [(gx0, 5), (gx0 + 3, 8), (gx1 - 3, 8), (gx1, 5)]
    gsil, _ = revolve_x(cam, grip_prof, 0, -throw, 24)
    parts.append(("grip", gsil))
    # ratchet collar and the chuck's shell
    rsil, _ = revolve_x(cam, [(14, 7), (16, 10), (36, 10), (38, 8)], 0, 0, 24)
    parts.append(("ratchet", rsil))
    csil, _ = revolve_x(cam, [(38, 9), (42, 11), (70, 9), (82, 6)], 0, 0, 24)
    parts.append(("chuck", csil))

    # the auger bit, into a board shown in section
    bit_r = 4.2
    bx0, tip = 82, 222
    depth = 14 + BITE * 70                # bite: how far the bit has sunk (38 at 35 %)
    board_x = tip - depth
    bit = [(bx0, -2.4), (bx0 + 18, -2.4), (bx0 + 22, -bit_r), (tip - 12, -bit_r), (tip - 6, -bit_r + 1.2 + 1.5 * WEAR),
           (tip - 1 - 4 * WEAR, -0.8 - 1.2 * WEAR), (tip - 1 - 4 * WEAR, 0.8 + 1.2 * WEAR),
           (tip - 6, bit_r - 1.2 - 1.5 * WEAR), (tip - 12, bit_r), (bx0 + 22, bit_r), (bx0 + 18, 2.4), (bx0, 2.4)]
    bitp = cam.proj([(x, 0, z) for x, z in bit])
    # wear: the screw point blunts into a stub
    screw = [(tip - 1 - 4 * WEAR, 0.8 + 1.2 * WEAR), (tip + 12 - 8 * WEAR, 0.6 + 1.6 * WEAR),
             (tip + 12 - 8 * WEAR, -0.6 - 1.6 * WEAR), (tip - 1 - 4 * WEAR, -0.8 - 1.2 * WEAR)]
    screwp = cam.proj([(x, 0, z) for x, z in screw])

    # board in section: solid above and below the bore, the bore ending at the tip
    hb, bore = 78, bit_r + 6
    bend = tip + 13
    board = [(board_x, hb), (300, hb), (300, -hb), (board_x, -hb), (board_x, -bore), (bend - 6, -bore),
             (bend, -2), (bend, 2), (bend - 6, bore), (board_x, bore)]
    boardp = cam.proj([(x, 0, z) for x, z in board])

    # draw: silhouettes black with a dark edge, then the lit edges in the one bright grey
    for name, poly in parts:
        s.path(poly, BLACK, G[2], LINE)
    s.path(bitp, BLACK, G[2], LINE)
    s.path(screwp, BLACK, G[2], LINE)
    # teeth: the twist's flutes, one hairline groove per turn, TEETH turns along the cutting length
    flute0, flute1 = bx0 + 24, tip - 8
    for k in range(TEETH):
        x = flute0 + (flute1 - flute0) * (k + 0.5) / TEETH
        s.ribbon(cam.proj([(x - 3, 0, bit_r - 1.2), (x + 3, 0, -bit_r + 1.2)]), HAIR, G[3])
    # the ratchet's pawl ring: two hairline rings on the collar
    for x in (22, 30):
        s.ribbon(cam.proj([(x, 0, 9), (x, 0, -9)]), HAIR, G[2])
    for x in (50, 60):
        s.ribbon(cam.proj([(x, 0, 9.5), (x, 0, -9.5)]), HAIR, G[2])
    s.path(boardp, BLACK, G[4], LINE)
    # the board's grain, end-on in section: hairlines across the cut, ≥ 6 px apart
    for z in (-70, -48, -26, 26, 48, 70):
        s.ribbon(cam.proj([(board_x + 4, 0, z), (300, 0, z + 3)]), HAIR, G[2])
    for name, poly in parts:
        lit_edges(s, poly, BRIGHT, SUBJ)
    lit_edges(s, bitp, BRIGHT, SUBJ)
    lit_edges(s, boardp, G[5], LINE)
    return s


# =========================================================================
# v4 · the mechanism in the hand: eggbeater drill, crank, face wheel and
#      pinion, detailed line art
# =========================================================================
def v4():
    s = Svg()
    cam = Camera(eye=(-180, -480, 150), target=(22, 0, 6), px_per_unit=1.32, cx=238, cy=128)
    R, t = 54.0, 7.0
    W = (0.0, 0.0, 0.0)
    ex, ez = (1, 0, 0), (0, 0, 1)
    draws = []   # (depth, fn)

    def disc(c, r, n=48):
        return cam.proj(ring_pts(c, r, ex, ez, n))

    # crank, in front of the wheel: axle boss, arm, and the turned grip toward the hand
    ca = math.radians(128)
    arm_len = R * 1.4
    yb = -30
    arm0 = (0, yb, 0)
    arm1 = (arm_len * math.cos(ca), yb, arm_len * math.sin(ca))
    grip_c = arm1

    def crank():
        a, b = cam(arm0), cam(arm1)
        nrm = normal2(a, b)
        w = 4.5
        s.path([(a[0] + nrm[0] * w, a[1] + nrm[1] * w), (b[0] + nrm[0] * w * 0.7, b[1] + nrm[1] * w * 0.7),
                (b[0] - nrm[0] * w * 0.7, b[1] - nrm[1] * w * 0.7), (a[0] - nrm[0] * w, a[1] - nrm[1] * w)],
               BLACK, G[4], LINE)
        # the grip: a turned handle along +y, drawn as a solid of revolution about y
        prof = [(0, 4), (4, 7), (18, 8), (30, 7), (34, 4)]
        top, bot = [], []
        for dy, r in prof:
            c = add(grip_c, (0, -dy - 2, 0))
            pts = ring_pts(c, r, ex, ez, 24)
            scr = cam.proj(pts)
            p0, p1 = cam(grip_c), cam(add(grip_c, (0, -40, 0)))
            nrm = normal2(p0, p1)
            ds = [(q[0] - p0[0]) * nrm[0] + (q[1] - p0[1]) * nrm[1] for q in scr]
            top.append(scr[ds.index(min(ds))]); bot.append(scr[ds.index(max(ds))])
        s.path(top + bot[::-1], BLACK, G[4], LINE)
        for dy in (10, 22):
            arc = cam.proj(ring_pts(add(grip_c, (0, -dy - 2, 0)), 7.6, ex, ez, 16, math.pi * 0.5, math.pi * 1.5))
            s.ribbon(arc, HAIR, G[3])
        s.path(disc(arm0, 7, 20), BLACK, G[4], LINE)
        s.loop(disc(arm0, 2.5, 12), HAIR, G[3])
    draws.append((cam.depth(arm0) - 60, crank))

    # the wheel: back face, front face with its spokes' openings, lugs on the front
    def wheel():
        s.path(disc((0, t, 0), R), BLACK, G[3], LINE)
        s.path(disc(W, R), BLACK, G[4], LINE)
        # inner structure, hairline: the web's ring and four lightening holes
        s.loop(disc(W, R - 14, 48), HAIR, G[3])
        for k in range(4):
            a = math.radians(45 + 90 * k)
            c = (R * 0.5 * math.cos(a), 0, R * 0.5 * math.sin(a))
            s.path(disc(c, 11, 28), BLACK, G[3], HAIR)
            # through the hole, the back face's inner edge
        s.path(disc(W, 9, 24), BLACK, G[4], LINE)
        s.loop(disc(W, 4, 16), HAIR, G[3])
        # lugs: teeth on the front face, TEETH of them, worn by WEAR
        for k in range(TEETH):
            a = 2 * math.pi * k / TEETH + 0.0
            hw = math.pi / TEETH * 0.55
            r0, r1 = R - 11, R - 1.5
            body = [(r0, a - hw), (r1, a - hw * (0.8 - 0.4 * WEAR)), (r1, a + hw * (0.8 - 0.4 * WEAR)), (r0, a + hw)]
            pts = [(r * math.cos(aa), -4, r * math.sin(aa)) for r, aa in body]
            back = [(r * math.cos(aa), 0, r * math.sin(aa)) for r, aa in body]
            sp, bp = cam.proj(pts), cam.proj(back)
            # side wall then face (hidden-line by order)
            for q in ([bp[0], bp[1], sp[1], sp[0]], [bp[3], bp[2], sp[2], sp[3]], [bp[1], bp[2], sp[2], sp[1]]):
                ar = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(q, q[1:] + q[:1]))) / 2
                if ar > 6:
                    s.path(q, BLACK, G[3], HAIR)
            s.path(sp, BLACK, G[5], LINE)
    draws.append((cam.depth(W), wheel))

    # spindle in front of the wheel, along x, through the head, pinion, chuck and bit
    sy, sz = -17.0, 0.0
    rp = 9.0
    ratio_scale = 1.6 - 0.8 * RATIO_N      # ratio: the pinion's size against the wheel

    def spindle():
        sil, _ = revolve_x(cam, [(-R - 34, 3), (R + 40, 3)], sy, sz, 16)
        s.path(sil, BLACK, G[3], LINE)
    draws.append((cam.depth((0, sy, sz)) + 5, spindle))

    def head():
        prof = [(-R - 92, 5), (-R - 88, 11), (-R - 78, 14), (-R - 60, 13), (-R - 46, 10), (-R - 38, 7), (-R - 34, 5)]
        sil, arcs = revolve_x(cam, prof, sy, sz, 24)
        s.path(sil, BLACK, G[4], LINE)
        for i in (2, 4):
            s.ribbon(arcs[i], HAIR, G[3])
    draws.append((cam.depth((-R - 60, sy, sz)), head))

    bit_len = 34 + BITE * 50                 # bite: how much bit stands out of the chuck

    def chuck_and_bit():
        x0 = R + 40
        sil, arcs = revolve_x(cam, [(x0 - 6, 5), (x0, 9), (x0 + 16, 9.5), (x0 + 28, 6)], sy, sz, 24)
        bsil, _ = revolve_x(cam, [(x0 + 28, 2.6), (x0 + 28 + bit_len - 6, 2.6), (x0 + 28 + bit_len, 0.4)], sy, sz, 12)
        s.path(bsil, BLACK, G[4], LINE)
        # twist flutes, hairline diagonals ≥ 3 px apart
        xx = x0 + 34
        while xx < x0 + 28 + bit_len - 10:
            s.ribbon([cam((xx, sy - 3, sz + 2.2)), cam((xx + 4, sy - 3, sz - 2.2))], HAIR, G[3])
            xx += 7
        s.path(sil, BLACK, G[4], LINE)
        # jaws' knurl: hairline rings
        for i in (1, 2):
            s.ribbon(arcs[i], HAIR, G[3])
    draws.append((cam.depth((R + 60, sy, sz)), chuck_and_bit))

    def pinion():
        rr = rp * ratio_scale
        cxp = R - 6
        prof = [(cxp - 7, rr - 1.5), (cxp - 5.5, rr), (cxp + 5.5, rr), (cxp + 7, rr - 1.5)]
        sil, _ = revolve_x(cam, prof, -4 - rr, sz, 24)
        s.path(sil, BLACK, BRIGHT, SUBJ)
        # teeth along the pinion: lines on the visible half, ≥ 3 px apart on screen
        last = None
        for k in range(10):
            a = 2 * math.pi * k / 10
            p0 = (cxp - 5, -4 - rr + rr * math.cos(a), sz + rr * math.sin(a))
            if not cam.facing(p0, (0, math.cos(a), math.sin(a))):
                continue
            sp = cam(p0)
            if last is not None and math.dist(sp, last) < 3.4:
                continue
            last = sp
            s.ribbon([sp, cam((cxp + 5, p0[1], p0[2]))], HAIR, G[5])
    draws.append((cam.depth((R - 6, -4 - rp, 0)) - 30, pinion))

    for _, fn in sorted(draws, key=lambda d: -d[0]):
        fn()
    return s


# =========================================================================
# v5 · the material, close: a laminated block cut through the bore,
#      hidden-line 3D
# =========================================================================
def v5():
    s = Svg()
    cam = Camera(eye=(230, -380, 230), target=(10, 40, -58), px_per_unit=1.16, cx=246, cy=133)
    X0, X1, Y0, Y1, H = -120, 120, 0, 80, 110
    r = 26.0
    depth = 26 + BITE * 90               # bite: how deep the bore has gone (57.5 at 35 %)
    plies = TEETH * 2                    # teeth: the plies the block is laid up from (12 at 6)
    pitch = 34 / RATIO                   # ratio: the bit's score marks wind tighter

    # the bore's far half-wall: score lines (helix), seen through the cut
    zb = -depth
    for k in range(40):
        z_top = -2 - k * pitch
        if z_top < zb + 2:
            break
        pts = []
        for i in range(17):
            th = math.pi * i / 16
            z = z_top - pitch * th / (2 * math.pi)
            if z < zb + 1:
                break
            pts.append((r * math.cos(th), r * math.sin(th), z))
        if len(pts) > 2:
            s.ribbon(cam.proj(pts), HAIR, G[3])
    # the bore's floor: the cone the lips cut, with the centre spur's prick
    cone = [(r * math.cos(math.pi * i / 16), r * math.sin(math.pi * i / 16), zb) for i in range(17)]
    apex = (0, 0, zb - 12)
    s.ribbon(cam.proj(cone), HAIR, G[4])
    for i in (0, 4, 8, 12, 16):
        s.ribbon(cam.proj([cone[i], apex]), HAIR, G[2])

    # the block: back half (y >= 0), faces drawn as solid bodies, black with line edges
    rng = random.Random(7)
    tear = [WEAR * 5 * rng.random() for _ in range(25)]
    top = [(X0, Y0, 0), (-r, Y0, 0)]
    for i in range(1, 24):                 # the half-hole in the top face, torn by wear
        th = math.pi - math.pi * i / 24
        rr = r + tear[i]
        top.append((rr * math.cos(th), rr * math.sin(th), 0))
    top += [(r, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0)]
    front = [(X0, Y0, 0), (-r, Y0, 0), (-r, Y0, zb), (0, Y0, zb - 12), (r, Y0, zb), (r, Y0, 0),
             (X1, Y0, 0), (X1, Y0, -H), (X0, Y0, -H)]
    side = [(X1, Y0, 0), (X1, Y1, 0), (X1, Y1, -H), (X1, Y0, -H)]
    s.path(cam.proj(side), BLACK, G[3], LINE)
    s.path(cam.proj(top), BLACK, G[3], LINE)
    s.path(cam.proj(front), BLACK, G[4], LINE)

    # plies: glue lines on the cut face and the side, hairline, each stopped at the bore
    for k in range(1, plies):
        z = -H * k / plies
        if z > zb:
            segs = [[(X0 + 1.5, Y0, z), (-r - 1.5, Y0, z)], [(r + 1.5, Y0, z), (X1 - 1.5, Y0, z)]]
        elif z > zb - 12:
            xc = r * (1 - (zb - z) / -12) if False else r * (z - (zb - 12)) / 12
            segs = [[(X0 + 1.5, Y0, z), (-xc - 1.5, Y0, z)], [(xc + 1.5, Y0, z), (X1 - 1.5, Y0, z)]]
        else:
            segs = [[(X0 + 1.5, Y0, z), (X1 - 1.5, Y0, z)]]
        for seg in segs:
            if seg[1][0] - seg[0][0] > 3:
                s.ribbon(cam.proj(seg), HAIR, G[2])
        s.ribbon(cam.proj([(X1, Y0 + 1.5, z), (X1, Y1 - 1.5, z)]), HAIR, G[2])
    # the cut through the bore: the one bright edge, where the bit has been
    cut = [(-r, Y0, 0), (-r, Y0, zb), (0, Y0, zb - 12), (r, Y0, zb), (r, Y0, 0)]
    s.ribbon(cam.proj(cut), SUBJ, BRIGHT)
    return s


def main():
    titles = {
        "v1": "drill v2.1 · the shaving's curl · single-weight contour",
        "v2": "drill v2.2 · face wheel and pinion, close · hatched mass",
        "v3": "drill v2.3 · the brace boring a board · edge-lit silhouette",
        "v4": "drill v2.4 · eggbeater drill's crank and gear train · detailed line art",
        "v5": "drill v2.5 · laminated block cut through the bore · hidden-line 3D",
    }
    for v, fn in (("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5)):
        (HERE / v).mkdir(exist_ok=True)
        fn().write(HERE / v / "rest.svg", titles[v])
        print(HERE / v / "rest.svg")


if __name__ == "__main__":
    main()
