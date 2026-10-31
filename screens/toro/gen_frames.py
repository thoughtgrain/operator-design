#!/usr/bin/env python3
"""Frames for toro's TAURUS screen, revision 2 (screens/toro/brief.md).

The Taurus chart never changes: its stars, lines and the Pleiades keep their places and brightness.
Controls act on the sky around it, and cutoff moves the camera in toward Aldebaran until the star
itself shows.

One model, many poses: every frame comes from `frame(values, playing)`, so the contact sheet always
matches the brief. Frames are authored like the panel fragment (device ids, explicit paint, closed
ribbons) with each pose baked in; display.cpp reaches the same poses with place/turn/scale/shade.

Chart geometry is from thoughtgrain/labyrinth opxy/machines/toro/gen_panel.py, MIT, (c) 2026 briannhinton.

    python3 screens/toro/gen_frames.py     # writes screens/toro/frames/*.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "frames"
PREFIX = "toro"
G = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]


def grey(level: float) -> str:
    return G[max(0, min(7, round(level * 7)))]


# ---- the chart (labyrinth gen_panel.py), as offsets from Aldebaran at zoom 1 --------------------------------
ALD = (258, 136)
STARS = {"g1": (-24, -16, 2.1), "g2": (-44, -26, 1.8), "g3": (-22, 14, 1.9), "g4": (-46, 26, 1.7),
         "beta": (92, -58, 2.7), "zeta": (78, 42, 2.3), "back": (-88, -8, 1.6), "tail": (-168, 20, 1.6)}
ORDER = list(STARS)
JOINS = [("ald", "g1"), ("g1", "g2"), ("ald", "g3"), ("g3", "g4"), ("g1", "beta"), ("g3", "zeta"),
         ("g2", "back"), ("g4", "back"), ("back", "tail")]
JOIN_AUTH = [50, 50, 50, 50, 100, 100, 100, 100, 100]   # authored lengths, so uniform scale stays ≤ 2
JOIN_W = 2.6
PLE_OFF = (-138, -30)
PLE7 = [(-8, -4, 1.8), (-2, -7, 1.7), (5, -5, 1.9), (9, 1, 1.7), (3, 5, 1.8), (-5, 6, 1.7), (0, 0, 2.1)]
M1_OFF = (-75, -42)                                       # the Crab Nebula (artistic placement, clear of the lines)

# ---- the sky around it -----------------------------------------------------------------------------------------
MOON_X, MOON_Y0, MOON_Y1, MOON_R = 446, 186, 70, 20       # spread slides it from y 186 to 70
RADIANT, METEOR_N = (150, 214), 12                       # Taurid radiant on the bottom edge
FIELD_N, FIELD_BASE = 180, 40                            # field stars: 40 at noise 0, all 180 at 100
BODY_TOP = 40

DEFAULTS = {"spread": 0.06, "fold": 0.18, "cutoff": 0.55, "res": 0.24, "shape": 0.0, "noise": 0.0, "drive": 0.0, "aphx": 0.0}
CONTROLS = list(DEFAULTS)
HIDDEN = (640, 320)

# node indices: written into handoff.md's node map
N = {"M1_OUTER": 0, "M1_INNER": 1, "HDR": 2, "ALD_CORE": 10, "ALD_DISK": 11, "ALD_SPIKE": 14, "RING": 15,
     "PULSE": 19, "STAR": 21, "JOIN": 29, "PLE": 38, "M1_CORE": 45, "MOON": 46, "METEOR": 55, "COMET": 67, "FIELD": 71}
MOON_PHASES = 8
N["TOTAL"] = N["FIELD"] + FIELD_N


def zoom(cutoff: float) -> float:
    """camera magnification: slow at first, most of it in the top half, like the filter's squared response"""
    return 1 + 2.2 * cutoff ** 3


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts) -> str:
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def dot(r: float, n: int = 10):
    return [(math.cos(k * 2 * math.pi / n) * r, math.sin(k * 2 * math.pi / n) * r) for k in range(n)]


def spike(r: float, inner: float = 0.14):
    return [(math.cos(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner),
             math.sin(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner)) for k in range(8)]


def annulus(r: float, w: float, n: int = 31, gap_deg: float = 1.5):
    """a ring as one closed outline: out around, back in around, joined across a 1.5° slit (one subpath, ≤ 64 points)"""
    angs = [math.radians(gap_deg / 2 + (360 - gap_deg) * k / (n - 1)) for k in range(n)]
    out = [(math.cos(a) * (r + w / 2), math.sin(a) * (r + w / 2)) for a in angs]
    inn = [(math.cos(a) * (r - w / 2), math.sin(a) * (r - w / 2)) for a in angs]
    return out + list(reversed(inn))


def ribbon(pts, w):
    ns = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        ns.append((-dy / ln * w / 2, dx / ln * w / 2))
    return [(x + nx, y + ny) for (x, y), (nx, ny) in zip(pts, ns)] + \
           [(x - nx, y - ny) for (x, y), (nx, ny) in reversed(list(zip(pts, ns)))]


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def scale(pts, k):
    return [(x * k, y * k) for x, y in pts]


def fold_signal(s: float) -> float:
    while s > 1 or s < -1:
        s = 2 - s if s > 1 else -2 - s
    return s


def moon_phase(lit: float, r: float = MOON_R):
    """the lit part of the disk, lit on the right: limb half-circle, then the terminator half-ellipse back.
    The cusps stop short of the poles (±78°) so the outline never turns straight back on itself."""
    ts = [-78 + 156 * i / 15 for i in range(16)]
    limb = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in ts]
    term = [((1 - 2 * lit) * r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in reversed(ts)]
    pts = limb + term
    out = []
    for p in pts:                                     # drop points that land within 1/8 px of the previous one
        if not out or math.dist(p, out[-1]) >= 0.2:
            out.append(p)
    if math.dist(out[0], out[-1]) < 0.3:
        out.pop()
    return out


def hrand(i: int, salt: int) -> float:
    x = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return x - math.floor(x)


def on_screen(x, y, margin=0):
    return -margin <= x <= 480 + margin and BODY_TOP - margin <= y <= 220 + margin


# ---- field star layout (fixed, seeded) -------------------------------------------------------------------------
def field_layout():
    rnd = random.Random(29)
    pts = []
    chart = [(ALD[0] + ox * zoom(DEFAULTS["cutoff"]), ALD[1] + oy * zoom(DEFAULTS["cutoff"])) for ox, oy, _ in STARS.values()]
    while len(pts) < FIELD_N:
        x, y = rnd.uniform(6, 474), rnd.uniform(BODY_TOP + 4, 214)
        if any(math.hypot(x - cx, y - cy) < 9 for cx, cy in chart):
            continue
        if math.hypot(x - ALD[0], y - ALD[1]) < 22:
            continue
        pts.append((x, y, rnd.choice([1.5, 1.6, 1.8, 2.0]), rnd.choice([3, 4, 4, 5])))
    return pts


FIELD = field_layout()


# ---- header preview (two pages, page 1 edited) ---------------------------------------------------------------
def header(values: dict) -> list[str]:
    o = ['<g id="preview_header">', '<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    for i, c in enumerate(G):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    caps = {k: str(round(v * 100)) for k, v in values.items()}
    caps["spread"] = f"{1 + 0.5 * values['spread']:.2f}"
    for col in range(4):
        light = "#CBCBCB" if col < 2 else "#000000"
        a, b = CONTROLS[col], CONTROLS[col + 4]
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 10)" fill="{light}" font-family="UniversNextPro-Light" font-size="10px">{a}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 17.4)" fill="{light}" font-family="UniversNextPro-Light" font-size="20px">{caps[a]}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 33)" fill="#5A5A5A" font-family="UniversNextPro-Light" font-size="10px">{b}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 33)" fill="#707070" font-family="UniversNextPro-Light" font-size="13px">{caps[b]}</text>')
    o.append("</g>")
    return o


def node(i: int, x: float, y: float, pts, fill: str, visible: bool = True) -> str:
    if not visible:
        x, y = HIDDEN
    return f'<path id="{PREFIX}_node_{i}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="none"/>'


# ---- the frame -------------------------------------------------------------------------------------------------
def frame(v: dict, playing: bool = False) -> str:
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
         '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>']
    o += header(v)
    flare = 1.0 if playing else 0.0
    Z = zoom(v["cutoff"])
    at = lambda off: (ALD[0] + off[0] * Z, ALD[1] + off[1] * Z)

    # Noise + Aphx · field stars: noise sets how many are out; aphx drifts them off their places
    kink = 0.4 * v["aphx"] + 0.6 * v["aphx"] ** 3
    shown = FIELD_BASE + round((FIELD_N - FIELD_BASE) * v["noise"])
    for k, (x, y, r, sh) in enumerate(FIELD):
        reach = kink * (7 + 22 * hrand(k, 1))
        ang = 360 * hrand(k, 2)
        px, py = x + math.cos(math.radians(ang)) * reach, y + math.sin(math.radians(ang)) * reach
        lit = playing and k % 9 == 0 and k < shown
        o.append(node(N["FIELD"] + k, px, py, dot(r * (1.3 if lit else 1)), G[7] if lit else G[sh],
                      visible=k < shown and on_screen(px, py)))

    # Drive · the Taurid radiant: more streaks, longer, brighter
    count = 3 + round((METEOR_N - 3) * v["drive"])
    length = 18 + 42 * v["drive"]
    for k in range(METEOR_N):
        ang = 200 + 140 * (k + 0.5) / METEOR_N                      # fan from up-left to up-right
        pts = rot([(6, -0.6), (6 + length, -1.4), (6 + length, 1.4), (6, 0.6)], ang)
        o.append(node(N["METEOR"] + k, RADIANT[0], RADIANT[1], pts, grey((3 + 3 * v["drive"] + (1 if playing and k == 5 else 0)) / 7),
                      visible=k < count))

    # Fold · M1, the Crab Nebula: its edge is the wavefolder's output wrapped into a ring; it grows and frays
    gain = 1 + 7 * v["fold"]
    R = (10 + 19 * v["fold"]) * Z / zoom(DEFAULTS["cutoff"])
    mx, my = at(M1_OFF)
    vis_m1 = on_screen(mx, my, -R)
    for half, (rr, phase, shade) in enumerate(((1.0, 0.0, G[4]), (0.62, 0.7, G[3]))):
        pts = []
        for k in range(64):
            th = 2 * math.pi * k / 64
            rad = R * rr * (1 + 0.32 * fold_signal(gain * math.sin(3 * th + phase)))
            pts.append((mx + math.cos(th) * rad, my + math.sin(th) * rad) if vis_m1 else (HIDDEN[0] + math.cos(th) * 4, HIDDEN[1] + math.sin(th) * 4))
        o.append(f'<path id="{PREFIX}_node_{N["M1_OUTER"] + half}" d="{poly(pts)}" fill="none" stroke="{shade}" stroke-width="1.5"/>')
    o.append(node(N["M1_CORE"], mx, my, dot(R * 0.72, 16), grey((1.5 + 2.5 * v["fold"]) / 7), visible=vis_m1))

    # the chart: fixed stars and lines, seen through the camera (drawn before Aldebaran, so lines stop at the star)
    pos = {"ald": ALD}
    for k, name in enumerate(ORDER):
        ox, oy, r = STARS[name]
        x, y = at((ox, oy))
        pos[name] = (x, y)
        o.append(node(N["STAR"] + k, x, y, dot(r * (1 + 0.25 * (Z - 1))), G[6], visible=on_screen(x, y, 4)))
    for k, (a, b) in enumerate(JOINS):
        (xa, ya), (xb, yb) = pos[a], pos[b]
        dist = math.hypot(xb - xa, yb - ya)
        s = min(2.0, dist / JOIN_AUTH[k])
        if yb < ya and ya > BODY_TOP:                              # pointing up: stop at the header's edge
            s = min(s, (ya - BODY_TOP) / max(1e-6, (ya - yb) / dist) / JOIN_AUTH[k])
        pts = rot(scale(ribbon([(0, 0), (JOIN_AUTH[k], 0)], JOIN_W), s), math.degrees(math.atan2(yb - ya, xb - xa)))
        visible = (on_screen(xa, ya, 30) or on_screen(xb, yb, 30)) and ya > BODY_TOP and s * JOIN_AUTH[k] > 4
        o.append(node(N["JOIN"] + k, xa, ya, pts, G[3], visible=visible))
    px0, py0 = at(PLE_OFF)
    for k, (dx, dy, r) in enumerate(PLE7):
        x, y = px0 + dx * Z, py0 + dy * Z
        o.append(node(N["PLE"] + k, x, y, dot(r), G[6], visible=on_screen(x, y, 4)))

    # Cutoff · the camera moves in on Aldebaran; past ~2× the star shows as a shaded disk
    disk_k = max(0.0, min(1.0, (Z - 1.6) / 1.6))
    core_r = 2.6 * min(2.0, Z * (1 + 0.4 * flare))
    o.append(node(N["ALD_CORE"], *ALD, dot(core_r), G[7]))
    for k, (rr, sh) in enumerate(((36, G[4]), (29, G[6]), (19, G[7]))):
        o.append(node(N["ALD_DISK"] + k, *ALD, dot(rr * (disk_k if disk_k > 0.05 else 1), 24), sh, visible=disk_k > 0.05))
    o.append(node(N["ALD_SPIKE"], *ALD, spike(12 * min(2.0, 0.5 + 0.47 * Z + 0.5 * flare)), grey((4 + 3 * v["cutoff"]) / 7)))

    # a note: two shock rings run out from Aldebaran (snapshot mid-flight in the playing frame)
    for k, (rr, sh) in enumerate(((30, G[5]), (46, G[4]))):
        o.append(node(N["PULSE"] + k, *ALD, annulus(rr, 3.2), sh, visible=playing))

    # Res · diffraction rings around Aldebaran: more and brighter as res rises
    base = 14 + 34 * disk_k + 2 * (Z - 1)
    for i in range(4):
        b = max(0.0, min(1.0, v["res"] * 4 - i + 0.25))
        radius = min(60, base + 12 * i)
        o.append(node(N["RING"] + i, *ALD, annulus(radius, 1.8 + 0.6 * b), grey((1 + 4 * b + (2 if playing and b > 0 else 0)) / 7),
                      visible=b > 0.05))

    # Spread + Shape · the Moon: spread slides it away from the chart, shape sets its phase (crescent → full)
    my2 = MOON_Y0 + (MOON_Y1 - MOON_Y0) * v["spread"]
    o.append(node(N["MOON"], MOON_X, my2, dot(MOON_R, 32), G[1]))                       # earthshine: the whole disk, faint
    phase = round(v["shape"] * (MOON_PHASES - 1))
    for k in range(MOON_PHASES):
        o.append(node(N["MOON"] + 1 + k, MOON_X, my2, moon_phase(0.12 + 0.88 * k / (MOON_PHASES - 1)), G[6], visible=k == phase))

    # launched comets: a note may send one across (odds rise with aphx); none at rest
    for k in range(2):
        base_i = N["COMET"] + 2 * k
        tail = rot([(0, -1.8), (-30, -1.0), (-60, -0.4), (-60, 0.4), (-30, 1.0), (0, 1.8)], 20)
        show = playing and k == 0
        o.append(node(base_i, 200, 70, tail, G[5], visible=show))
        o.append(node(base_i + 1, 200, 70, dot(2.4), G[7], visible=show))

    for i, c in enumerate(G + G[1:] + [G[7]]):
        o.append(f'<circle id="{PREFIX}_palette_{i}" cx="{700 + 6 * i}" cy="300" r="1" fill="{c}" stroke="{c}" stroke-width="0.5"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    (OUT / "rest.svg").write_text(frame(dict(DEFAULTS)), encoding="utf-8")
    (OUT / "playing.svg").write_text(frame(dict(DEFAULTS), playing=True), encoding="utf-8")
    for n, name in enumerate(CONTROLS, start=1):
        for pct in (0, 50, 100):
            (OUT / f"c{n}-{pct:03d}.svg").write_text(frame(dict(DEFAULTS, **{name: pct / 100})), encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.svg')))} frames to {OUT} · {N['TOTAL']} nodes")


if __name__ == "__main__":
    main()
