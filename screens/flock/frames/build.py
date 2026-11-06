#!/usr/bin/env python3
"""Flock · v5 refined: the crank automaton, simplified, with a filled box.

    python3 screens/flock/frames/build.py            # frames, PNGs, before-after, contact, motion.gif
    python3 screens/flock/frames/build.py --check    # also print clearance, contrast and black-body numbers

The pick from subject pass 02 (v5): a wooden box with eight carved birds on rods riding a slot
over a tuned comb. Each rod's pick plucks the tine in front of it; a crank on the front drives it.

What this pass changes (refine.md has the reasons):
- the box is a solid body: three flat greys by their light (lid lightest, front mid, end darkest),
  crisp outlines, no hatching;
- fewer parts: no plinth line, no eyes, no separate wing shape (one carved silhouette a bird),
  no hatched boss or handle; the slot is a plain black groove and the comb a quiet bar;
- the birds sit on four tiers in pairs set far apart along the slot, so they never touch at the
  defaults (checked below), and the flock is spread wider;
- the comb is a real music-box comb: tips in a straight line where the picks reach them, the bar
  stepped behind them (long, low tines on the left);
- the crank sits on the front face, so its turn is a turn in the screen's plane (a device node turn).

One brightest element: the bird that's playing now (at rest, the one that played last).
Everything is modelled in 3D and projected through one camera. No text below the header.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE = ROOT / "opxy" / "templates" / "frame.svg"
V5_PNG = HERE.parent / "passes" / "02-subject" / "v5" / "rest.png"

# ------------------------------------------------------------------ greys and weights
G0, G1, G2, G3, G4, G5, G6, G7 = ("#000000", "#323232", "#4B4B4B", "#646464",
                                  "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD")
LID, FRONT, END = "#464646", "#2C2C2C", "#161616"     # the box's faces, by their light (from the upper left)
HAIR, LINE, SUBJ = 1.1, 1.5, 2.25

SCALES = {  # enum order from definition.json: pent, maj, min, dor, lyd, chr
    "pent": [0, 2, 4, 7, 9], "maj": [0, 2, 4, 5, 7, 9, 11], "min": [0, 2, 3, 5, 7, 8, 10],
    "dor": [0, 2, 3, 5, 7, 9, 10], "lyd": [0, 2, 4, 6, 7, 9, 11], "chr": list(range(12)),
}
SCALE_NAMES = ["pent", "maj", "min", "dor", "lyd", "chr"]


def scale_name(v: float) -> str:
    return SCALE_NAMES[min(len(SCALE_NAMES) - 1, int(v * len(SCALE_NAMES)))]


def degrees(name: str) -> list[int]:
    s = SCALES[name]
    return [12 * o + d for o in range(2) for d in s] + [24]          # two octaves and the top root


def speed_ratio(v: float) -> float:
    return 0.25 * (4 / 0.25) ** v                                      # exponential 0.25..4


# ------------------------------------------------------------------ state
@dataclass(frozen=True)
class State:
    cohere: float = 0.5
    speed: float = 0.5          # control position 0..1 (ratio 0.25..4, exponential)
    scatter: float = 0.0
    scale: float = 0.0          # control position 0..1 (enum)
    # animation (all zero at rest)
    crank_turn: float = 0.0     # extra crank angle while playing, degrees (rest parks at the speed angle)
    drift: float = 0.0          # flock centre offset along the slot, world units
    lit: int = 4                # the bird that played last / is playing now
    pluck: float = 0.0          # 0..1: how hard the lit bird's tine is flicking now (decays to 0)
    bob: float = 0.0            # px the lit bird is lifted by its pluck
    playing: bool = False


DEFAULT = State()

# ------------------------------------------------------------------ geometry helpers
def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) >= 0.25:
            out.append(p)
    while len(out) > 2 and math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    L = math.sqrt(dot(a, a))
    return (a[0] / L, a[1] / L, a[2] / L)


class Camera:
    """Perspective camera, world y up. Screen x right, screen y down."""

    def __init__(self, eye, target, f, centre):
        self.e = eye
        self.fw = norm(sub(target, eye))
        self.rt = norm(cross3((0, 1, 0), self.fw))
        self.up = cross3(self.fw, self.rt)
        self.f, self.c = f, centre

    def __call__(self, p):
        d = sub(p, self.e)
        z = dot(d, self.fw)
        return (self.c[0] + self.f * dot(d, self.rt) / z, self.c[1] - self.f * dot(d, self.up) / z)

    def ppu(self, p):
        """Pixels per world unit at p (size from distance)."""
        return self.f / dot(sub(p, self.e), self.fw)


def orbit(yaw: float, pitch: float, dist: float, target, ppu: float, centre) -> Camera:
    """A camera dist away from target, turned yaw degrees round it (negative: from the left) and
    pitch degrees above it; far and long so the box keeps its proportions and shows its left end."""
    y, p = math.radians(yaw), math.radians(pitch)
    eye = (target[0] + dist * math.sin(y) * math.cos(p), target[1] + dist * math.sin(p),
           target[2] - dist * math.cos(y) * math.cos(p))
    return Camera(eye, target, dist * ppu, centre)


CAM = orbit(-9, 29, 60, (0.1, 0.0, 0.0), 33.5, (240, 147))

# the box (world units): long axis x, lid at y = 0, front face at z = BZ0 facing the camera
BX0, BX1, BY0, BY1, BZ0, BZ1 = -4.7, 4.7, -0.9, 0.0, -1.35, 1.05
SLOT_Z0, SLOT_Z1 = 0.42, 0.58                 # the groove the rods ride in, just behind the comb's tips
SLOT_X0, SLOT_X1 = BX0 + 0.45, BX1 - 0.45
TIP_Z = 0.3                                 # the comb's tips line up here, where the picks reach
BAR_Z = -1.18                                 # the comb's bar, stepped: long tines root further forward
COMB_X0, COMB_X1 = SLOT_X0 + 0.15, SLOT_X1 - 0.15
CRANK_C = (BX1 - 0.95, BY0 + 0.55, BZ0)        # the crank's boss, on the front face
CRANK_R = 1.45

# ------------------------------------------------------------------ the flock on its rods
# Eight birds on four tiers, two a tier, the pair on a tier always more than a bird's length
# apart along the slot (their offsets differ by 1.2 or more), so they can't touch at any cohere.
# offset o (-1..1) along the flock's spread, tier height (rod length above the lid), a small jitter.
# The tiers rise left to right in two runs, so each bird's raised wing (it points back, to the left)
# opens away from its neighbour: neighbours are a tier (0.67) apart and the higher one is ahead.
TIER = {"A": 0.9, "B": 1.57, "C": 2.24, "D": 2.91}
BIRDS = [(-1.00, "A", 0.06), (-0.77, "B", -0.04), (-0.47, "C", 0.05), (-0.22, "D", -0.02),
         (0.20, "A", 0.00), (0.43, "B", 0.07), (0.76, "C", -0.05), (1.00, "D", 0.00)]
# scatter: these three break away (slide out along the slot and lean out); sign = which way
STRAYS = {0: -1, 6: +1, 7: +1}
LEAN_MAX = math.radians(32)
SLIDE_MAX = 0.9
BIRD_LEN = 0.9                                # world units, beak to tail


def spread(cohere: float) -> float:
    """Half-width of the flock along the slot: most of the comb at 0, two or three tines at 100."""
    return 1.0 + (3.75 - 1.0) * (1 - cohere)


CENTRE = 0.0 - 0.20 * spread(0.5)              # the lit bird (offset 0.20) sits on the middle tine at the defaults


def tines(st: State):
    """[(x, length)] for the comb at this scale, low (long) on the left."""
    deg = degrees(scale_name(st.scale))
    n = len(deg)
    out = []
    for i, d in enumerate(deg):
        x = COMB_X0 + (COMB_X1 - COMB_X0) * i / (n - 1)
        out.append((x, 0.62 + 0.72 * 2 ** (-d / 12)))           # longer for lower, about 2:1 over the comb
    return out


def nearest_tine(x: float, ts) -> int:
    return min(range(len(ts)), key=lambda i: abs(ts[i][0] - x))


def rods(st: State):
    """Per bird: foot (world), lean (radians, + leans right), rod length."""
    W = spread(st.cohere)
    centre = CENTRE + st.drift
    ts = tines(st)
    out = []
    for k, (o, tier, jit) in enumerate(BIRDS):
        x = centre + W * o
        lean = 0.0
        if k in STRAYS:
            x += STRAYS[k] * SLIDE_MAX * st.scatter
            lean = STRAYS[k] * LEAN_MAX * st.scatter
        x = max(SLOT_X0 + 0.12, min(SLOT_X1 - 0.12, x))
        if k == st.lit:                          # the bird that played: its pick sits on its tine
            x = ts[nearest_tine(x, ts)][0]
        out.append(((x, BY1, (SLOT_Z0 + SLOT_Z1) / 2), lean, TIER[tier] + jit))
    return out


def rod_top(foot, lean, h):
    return (foot[0] + h * math.sin(lean), foot[1] + h * math.cos(lean), foot[2])


# a carved songbird in profile, facing right (x forward, y up, in bird lengths): the body is one
# silhouette, the wing a second carved blade pinned at the shoulder that the speed control raises.
# Beak tip and tail end have small flat ends (no near-reversals).
BODY = [(0.54, 0.13), (0.54, 0.115), (0.43, 0.09), (0.38, 0.05), (0.30, -0.03), (0.18, -0.09),
        (0.02, -0.12), (-0.14, -0.10), (-0.30, -0.03), (-0.44, 0.05), (-0.56, 0.11), (-0.56, 0.145),
        (-0.38, 0.13), (-0.20, 0.15), (-0.02, 0.17), (0.12, 0.175), (0.20, 0.19), (0.28, 0.26),
        (0.38, 0.26), (0.45, 0.19)]
SHOULDER = (0.08, 0.13)
WING = [(-0.03, -0.05), (0.16, -0.075), (0.40, -0.065), (0.60, -0.016), (0.60, 0.016), (0.40, 0.09),
        (0.16, 0.125), (-0.03, 0.08)]           # along +u from the shoulder; +v is the leading edge


def wing_angle(speed: float) -> float:
    """Degrees from the beak direction, anticlockwise: folded along the back at 0.25, raised at 4.00."""
    return 188 - 84 * speed


def _place(pts, top, lean, bob):
    c = CAM(top)
    s = CAM.ppu(top) * BIRD_LEN
    ca, sa = math.cos(lean), math.sin(lean)     # world lean is a turn in the screen's plane
    out = []
    for x, y in pts:
        X, Y = x * s, (y + 0.02) * s             # rod meets the belly
        rx, ry = X * ca + Y * sa, -X * sa + Y * ca
        out.append((c[0] + rx, c[1] - ry - bob))
    return out


def bird_outline(top, lean, bob=0.0):
    """The carved bird's body on top of its rod, turned with the rod, in screen px."""
    return _place(BODY, top, lean, bob)


def wing_outline(top, lean, speed, bob=0.0):
    """The wing, turned about the shoulder by the speed control (a node turn about its own origin)."""
    a = math.radians(wing_angle(speed))
    ca, sa = math.cos(a), math.sin(a)
    # +v (leading edge) on the upper side whichever way the wing points back
    pts = [(SHOULDER[0] + u * ca + v * sa, SHOULDER[1] + u * sa - v * ca) for u, v in WING]
    return _place(pts, top, lean, bob)


# ------------------------------------------------------------------ frame writer
class Frame:
    def __init__(self, title: str):
        self.title = title
        self.items: list[str] = []

    def poly(self, pts, fill, stroke="none", sw=0.0):
        pts = dedupe(pts)
        if len(pts) < 3:
            return
        assert len(pts) <= 64, len(pts)
        d = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"
        sws = f' stroke-width="{fmt(sw)}"' if stroke != "none" else ' stroke-width="0"'
        self.items.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}"{sws}/>')

    def ribbon(self, a, b, w, colour):
        """A straight line of width w as a closed filled ribbon (never a traced stroke)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 3.2:
            return
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        self.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)],
                  colour)

    def svg(self, header: list[str]) -> str:
        head = TEMPLATE.read_text(encoding="utf-8")
        s0 = head.index('  <g id="preview_canvas">')
        s1 = head.index("  <!-- Palette entries")
        body = head[s0:s1].rstrip()
        titles = ["cohere", "speed", "scatter", "scale"]
        for i, t in enumerate(titles):
            body = re.sub(rf">p{i + 1}</text>", f">{t}</text>", body, count=1)
        # values: the template's four value slots are the 20px texts, in column order
        vals = iter(header)
        body = re.sub(r'(font-size="20px">)([^<]*)(</text>)', lambda m: m.group(1) + next(vals) + m.group(3), body)
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
               f"  <title>flock · v5 refined · {self.title}</title>", body]
        out += ["  " + s for s in self.items]
        out.append("</svg>")
        return "\n".join(out) + "\n"


def header_values(st: State) -> list[str]:
    return [f"{round(st.cohere * 100)}", f"{speed_ratio(st.speed):.2f}", f"{round(st.scatter * 100)}",
            scale_name(st.scale)]


# ------------------------------------------------------------------ the drawing
def draw(st: State, title: str) -> Frame:
    F = Frame(title)
    C = lambda pts: [CAM(p) for p in pts]

    # --- the box: a solid body, three faces in flat greys by their light, crisp outlines
    end = C([(BX0, BY1, BZ0), (BX0, BY1, BZ1), (BX0, BY0, BZ1), (BX0, BY0, BZ0)])
    front = C([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY0, BZ0), (BX0, BY0, BZ0)])
    lid = C([(BX0, BY1, BZ0), (BX1, BY1, BZ0), (BX1, BY1, BZ1), (BX0, BY1, BZ1)])
    F.poly(end, END, G4, LINE)
    F.poly(front, FRONT, G4, LINE)
    F.poly(lid, LID, G4, LINE)

    # --- the slot: a plain black groove in the lid
    F.poly(C([(SLOT_X0, BY1, SLOT_Z0), (SLOT_X1, BY1, SLOT_Z0), (SLOT_X1, BY1, SLOT_Z1), (SLOT_X0, BY1, SLOT_Z1)]),
           G0)

    # --- the comb: steel tongues with their tips in a line at TIP_Z (where the picks reach them),
    #     rooted in a bar that steps forward under the long, low tines on the left
    ts = tines(st)
    n = len(ts)
    pitch = (COMB_X1 - COMB_X0) / (n - 1)
    pad = 0.5 * pitch
    feet = rods(st)
    lit_tine = nearest_tine(feet[st.lit][0][0], ts)
    # the bar: a dark steel block on the lid, its back edge stepping with the tongues' lengths
    bar = [(COMB_X0 - pad, BY1, BAR_Z), (COMB_X1 + pad, BY1, BAR_Z)]
    for i in range(n - 1, -1, -1):
        x, L = ts[i]
        bar += [(x + pad, BY1, TIP_Z - L), (x - pad, BY1, TIP_Z - L)]
    F.poly(C(bar), FRONT, G5, HAIR)
    # the tongues: thin steel lines from the bar to the tip line
    for i, (x, L) in enumerate(ts):
        flick = 0.06 * st.pluck if i == lit_tine else 0.0     # tip pushed sideways by the pick, ringing down
        playing = i == lit_tine and st.playing
        F.ribbon(CAM((x, BY1, TIP_Z - L - 0.03)), CAM((x + flick, BY1, TIP_Z)),
                 SUBJ if playing else LINE, G6 if playing else G5)

    # --- the crank on the front face: arm round the boss, a stud for the axle, the knob end-on;
    #     it parks at the speed angle and turns about the stud (a turn in the screen's plane)
    park = -135 + 270 * st.speed
    ang = math.radians(park + st.crank_turn)
    cc = CAM(CRANK_C)
    R = CRANK_R * CAM.ppu(CRANK_C)
    ux, uy = math.sin(ang), -math.cos(ang)
    nx, ny = -uy, ux
    tip = (cc[0] + R * ux, cc[1] + R * uy)
    rb, rt = 8.0, 4.0
    arm = [(cc[0] + rb * (math.cos(a) * nx - math.sin(a) * ux), cc[1] + rb * (math.cos(a) * ny - math.sin(a) * uy))
           for a in [math.radians(t) for t in range(0, 181, 15)]]
    arm += [(tip[0] - nx * rt, tip[1] - ny * rt), (tip[0] + nx * rt, tip[1] + ny * rt)]
    F.poly(arm, G0, G5, LINE)
    F.poly([(cc[0] + 2.8 * math.cos(2 * math.pi * k / 12), cc[1] + 2.8 * math.sin(2 * math.pi * k / 12))
            for k in range(12)], G5)
    F.poly([(tip[0] + 7.5 * math.cos(2 * math.pi * k / 24), tip[1] + 7.5 * math.sin(2 * math.pi * k / 24))
            for k in range(24)], G0, G5, LINE)

    # --- rods (each with its pick, a short leg from the foot forward over the comb's tips), then the birds
    for k, (foot, lean, h) in enumerate(feet):
        lit = k == st.lit
        hot = lit and st.playing
        flick = 0.06 * st.pluck if lit else 0.0
        F.ribbon(CAM(foot), CAM((foot[0] + flick, BY1, TIP_Z - 0.08)), 1.5, G6 if hot else G5)
        top = rod_top(foot, lean, h)
        F.ribbon(CAM(foot), CAM(top), 1.5, G5)
    for k, (foot, lean, h) in enumerate(feet):
        lit = k == st.lit
        top = rod_top(foot, lean, h)
        bob = st.bob if lit else 0.0
        F.poly(bird_outline(top, lean, bob), G0, G7 if lit else G5, SUBJ if lit else LINE)
        F.poly(wing_outline(top, lean, st.speed, bob), G0, G7 if lit else G5, LINE)
    return F


# ------------------------------------------------------------------ checks
def lum(hexc: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def inside(p, poly):
    x, y = p
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def poly_gap(P, Q):
    """Smallest gap between two closed outlines (0 if they overlap)."""
    if any(inside(p, Q) for p in P) or any(inside(q, P) for q in Q):
        return 0.0
    d = min(seg_dist(p, a, b) for p in P for a, b in zip(Q, Q[1:] + Q[:1]))
    return min(d, min(seg_dist(q, a, b) for q in Q for a, b in zip(P, P[1:] + P[:1])))


def bird_gaps(st: State) -> float:
    feet = rods(st)
    outs = [(bird_outline(rod_top(f, l, h), l), wing_outline(rod_top(f, l, h), l, st.speed)) for f, l, h in feet]
    return min(poly_gap(a, b) for i in range(8) for j in range(i + 1, 8) for a in outs[i] for b in outs[j]) \
        - SUBJ / 2 - LINE / 2


def top_of_drawing(st: State) -> float:
    feet = rods(st)
    return min(min(y for _, y in bird_outline(rod_top(f, l, h), l, st.bob if k == st.lit else 0)
                   + wing_outline(rod_top(f, l, h), l, st.speed, st.bob if k == st.lit else 0))
               for k, (f, l, h) in enumerate(feet))


# ------------------------------------------------------------------ outputs
CONTROL_FRAMES = [("cohere", "cohere"), ("speed", "speed"), ("scatter", "scatter"), ("scale", "scale")]


def write(st: State, stem: str, title: str, out: Path = HERE) -> Path:
    p = out / f"{stem}.svg"
    p.write_text(draw(st, title).svg(header_values(st)), encoding="utf-8")
    return p


def render(svg: Path, png: Path | None = None) -> Path:
    png = png or svg.with_suffix(".png")
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-o", str(png), str(svg)], check=True)
    return png


def frames() -> list[Path]:
    made = [write(DEFAULT, "rest", "rest at the defaults")]
    for name, field in CONTROL_FRAMES:
        for v in (0, 50, 100):
            made.append(write(replace(DEFAULT, **{field: v / 100}), f"{name}-{v}", f"{name} {v}"))
    return made


def phrase() -> list[State]:
    """A short phrase at the defaults: eight notes, the crank turning, the flock riding, then the coast."""
    fps = 20
    order = [2, 5, 3, 6, 1, 4, 2, 7]             # which bird crosses into a new cell, note by note
    step = 0.25                                   # s between notes (speed 1.00 at 120 bpm, sketch)
    out = []
    t_end = step * len(order)
    total = t_end + 1.2
    crank = 0.0
    drift = 0.0
    lit = DEFAULT.lit
    for f in range(int(total * fps)):
        t = f / fps
        playing = t < t_end + 0.35
        # crank: one turn a beat at speed 1.00 while notes come, then an ease-out coast to its park angle
        if t < t_end:
            crank += 360 * speed_ratio(DEFAULT.speed) / 2 / fps * 2
            drift = 0.55 * math.sin(math.pi * t / t_end)
        n = min(len(order) - 1, int(t / step)) if t < t_end else len(order) - 1
        since = t - n * step
        lit = order[n]
        pluck = math.exp(-since / 0.12) * math.cos(2 * math.pi * since / 0.09) if since < 0.45 else 0.0
        bob = 4.0 * math.exp(-since / 0.07) if since < 0.3 else 0.0
        if t >= t_end:
            k = 1 - math.exp(-(t - t_end) / 0.18)
            target = math.ceil(crank / 360) * 360
            crank_draw = crank + (target - crank) * k
        else:
            crank_draw = crank
        out.append(replace(DEFAULT, crank_turn=crank_draw % 360, drift=drift, lit=lit, pluck=pluck,
                           bob=round(bob), playing=playing and since < 0.3))
    return out


def gif(states: list[State], path: Path, scratch: Path) -> None:
    from PIL import Image
    ims = []
    for i, st in enumerate(states):
        s = write(st, f"_m{i:03d}", "motion", scratch)
        ims.append(Image.open(render(s)).convert("RGB"))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=50, loop=0, optimize=True)


def before_after(rest_png: Path, path: Path) -> None:
    from PIL import Image
    a, b = Image.open(V5_PNG).convert("RGB"), Image.open(rest_png).convert("RGB")
    gap = 16
    sheet = Image.new("RGB", (480 * 2 + gap * 3, 220 + gap * 2), (22, 22, 22))
    sheet.paste(a, (gap, gap))
    sheet.paste(b, (480 + gap * 2, gap))
    sheet.save(path)


def black_fraction(png: Path) -> float:
    from PIL import Image
    im = Image.open(png).convert("L")
    w, h = im.size
    px = im.load()
    body = [(x, y) for y in range(20, h) for x in range(w)]
    return sum(1 for x, y in body if px[x, y] <= 6) / len(body)


def main(argv: list[str]) -> int:
    if not shutil.which("rsvg-convert"):
        print("needs rsvg-convert", file=sys.stderr)
        return 2
    made = frames()
    for p in made:
        render(p)
    before_after(HERE / "rest.png", HERE / "before-after.png")
    scratch = HERE / "_scratch"
    scratch.mkdir(exist_ok=True)
    # contact sheet through the repo's tool (it wants c<N>-000 names): copies in scratch
    cs = scratch / "contact"
    shutil.rmtree(cs, ignore_errors=True)
    cs.mkdir()
    shutil.copy(HERE / "rest.svg", cs / "rest.svg")
    for i, (name, _) in enumerate(CONTROL_FRAMES):
        for v in (0, 50, 100):
            shutil.copy(HERE / f"{name}-{v}.svg", cs / f"c{i + 1}-{v:03d}.svg")
    subprocess.run([sys.executable, str(ROOT / "opxy" / "tools" / "contact_sheet.py"), str(cs),
                    "--out", str(scratch / "contact.svg"), "--png"], check=True, capture_output=True)
    shutil.copy(scratch / "contact.png", HERE / "contact.png")
    gif(phrase(), HERE / "motion.gif", scratch)
    if "--check" in argv:
        print("contrast (WCAG):")
        for what, a, b in (("bird #969696 on lid", G5, LID), ("lit bird #CDCDCD on lid", G7, LID),
                           ("rod/pick/tine #969696 on lid", G5, LID), ("crank #969696 on front", G5, FRONT),
                           ("bird #969696 on black", G5, G0), ("box edge #7D7D7D on black", G4, G0),
                           ("lid vs front", LID, FRONT), ("front vs end", FRONT, END), ("lid vs black", LID, G0)):
            print(f"  {what}: {contrast(a, b):.2f}")
        for st, name in [(DEFAULT, "rest")] + [(replace(DEFAULT, **{f: v / 100}), f"{f}-{v}")
                                                for f, _ in CONTROL_FRAMES for v in (0, 50, 100)] + \
                [(replace(DEFAULT, cohere=1.0, scatter=1.0), "cohere-100+scatter-100"),
                 (replace(DEFAULT, cohere=0.0, scatter=1.0), "cohere-0+scatter-100")]:
            print(f"  {name}: closest birds {bird_gaps(st):.1f} px apart (stroke to stroke), "
                  f"top of drawing y {top_of_drawing(st):.1f}")
        print(f"  black body at rest: {100 * black_fraction(HERE / 'rest.png'):.1f}%")
        for p in made:
            print(f"  {p.stem}: black {100 * black_fraction(p.with_suffix('.png')):.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
