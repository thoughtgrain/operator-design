#!/usr/bin/env python3
"""Frames for toro's revised TAURUS screen (screens/toro/brief.md, candidate A).

One model, many poses: every frame comes from `frame(values, playing)` so the
contact sheet always matches the brief. Frames are authored like the panel
fragment (device ids, explicit paint, closed ribbons) with each pose baked in:
in the machine, display.cpp reaches the same poses with place/turn/scale/shade.

Chart geometry (star positions, joins, Pleiades offsets) is from
thoughtgrain/labyrinth opxy/machines/toro/gen_panel.py, MIT, (c) 2026 briannhinton.

    python3 screens/toro/gen_frames.py     # writes screens/toro/frames/*.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "frames"
PREFIX = "toro"

# stock greys only (opxy/tokens.json)
G = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
BLACK, FILL, GROUND, NONTEXT, INACT, SECOND, SECOND2, PRIMARY = G


def grey(level: float) -> str:
    """0..1 → nearest stock grey, so shades fade through the ramp instead of jumping."""
    return G[max(0, min(7, round(level * 7)))]


# ---- chart geometry (labyrinth gen_panel.py) ---------------------------------------------------------------
CX, CY = 240, 134
STARS = {
    "ald": (18, 2, 3.6), "g1": (-6, -14, 2.1), "g2": (-26, -24, 1.8), "g3": (-4, 16, 1.9), "g4": (-28, 28, 1.7),
    "beta": (110, -56, 2.7), "zeta": (96, 44, 2.3), "back": (-70, -6, 1.6), "tail": (-150, 22, 1.6),
}
ORDER = ["g1", "g2", "g3", "g4", "beta", "zeta", "back", "tail"]
JOINS = [("ald", "g1"), ("g1", "g2"), ("ald", "g3"), ("g3", "g4"), ("g1", "beta"), ("g3", "zeta"),
         ("g2", "back"), ("g4", "back"), ("back", "tail")]
PLEIADES = (CX - 120, CY - 28)
PLE7 = [(-8, -4, 1.8), (-2, -7, 1.7), (5, -5, 1.9), (9, 1, 1.7), (3, 5, 1.8), (-5, 6, 1.7), (0, 0, 2.1)]

# ---- revised layout -----------------------------------------------------------------------------------------
ECL_Y, ECL_A, ECL_X0, ECL_X1, ECL_HALF = 204, 11, 24, 456, 0.9     # the ecliptic: baseline, fold amplitude, span
COMET_HEAD, COMET_DIR = (432, 152), -75.0                            # standing comet; tail points up and a little right
BAND_A, BAND_B, BAND_SPREAD = (0, 124), (150, 52), 12                # Milky Way, top left; Drive spreads three lines
LABELS = [("TAURUS", 16, 62, 13, SECOND2), ("α Aldebaran", CX + 18 + 10, CY + 2 + 3.5, 10, INACT),
          ("ο", CX - 150 - 4, CY + 22 + 14, 10, INACT), ("Pleiades", PLEIADES[0], PLEIADES[1] + 28, 10, INACT)]

DEFAULTS = {"spread": 0.06, "fold": 0.18, "cutoff": 0.55, "res": 0.24, "shape": 0.0, "noise": 0.0, "drive": 0.0, "aphx": 0.0}
CONTROLS = list(DEFAULTS)

# node indices (written into handoff.md's node map)
N = {"ECL_L": 0, "ECL_R": 1, "HDR": 2, "ALD": 10, "STAR": 13, "JOIN": 21, "PLE": 30, "RING": 37,
     "CSEG": 45, "CHEAD": 48, "COMET": 49, "TWINKLE": 53, "BAND": 65, "TOTAL": 68}
RING_N, TWINKLE_N = 8, 12
HIDDEN = (640, 320)


def f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts) -> str:
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def dot(r: float, n: int = 10):
    return [(math.cos(k * 2 * math.pi / n) * r, math.sin(k * 2 * math.pi / n) * r) for k in range(n)]


def spike(r: float, inner: float = 0.35):
    return [(math.cos(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner),
             math.sin(-math.pi / 2 + k * math.pi / 4) * (r if k % 2 == 0 else r * inner)) for k in range(8)]


def ring(r: float, w: float, n: int = 24):
    out = [(math.cos(k * 2 * math.pi / n) * (r + w / 2), math.sin(k * 2 * math.pi / n) * (r + w / 2)) for k in range(n)]
    inn = [(math.cos(k * 2 * math.pi / n) * (r - w / 2), math.sin(k * 2 * math.pi / n) * (r - w / 2)) for k in range(n)]
    return out[:-1] + list(reversed(inn[:-1]))


def normals(pts, half):
    ns = []
    for i in range(len(pts)):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        ns.append((-dy / ln * half, dx / ln * half))
    return ns


def ribbon(pts, w):
    ns = normals(pts, w / 2)
    up = [(x + nx, y + ny) for (x, y), (nx, ny) in zip(pts, ns)]
    dn = [(x - nx, y - ny) for (x, y), (nx, ny) in zip(pts, ns)]
    return up + list(reversed(dn))


def taper(length: float, w0: float, w1: float):
    """a segment along +x from the origin, wide at the start, narrow at the end, flat-ended"""
    return [(0, -w0 / 2), (length, -w1 / 2), (length, w1 / 2), (0, w0 / 2)]


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def scale(pts, k):
    return [(x * k, y * k) for x, y in pts]


def fold_signal(s: float) -> float:
    """the wavefolder: reflect at ±1"""
    while s > 1 or s < -1:
        s = 2 - s if s > 1 else -2 - s
    return s


# ---- static sky (unbound artwork) -----------------------------------------------------------------------------
def static_sky():
    out = []
    for k in range(1, 4):                                       # declination arcs as thin filled ribbons
        y = 52 + k * 40
        pts = [(x, y - 8 * math.sin(math.pi * x / 480)) for x in range(0, 481, 30)]
        out.append(f'<path d="{poly(ribbon(pts, 1))}" fill="{FILL}" stroke="none"/>')
    rnd = random.Random(11)
    field, tries = [], 0
    while len(field) < 34 and tries < 4000:
        tries += 1
        x, y = rnd.uniform(8, 472), rnd.uniform(48, 178)
        if not clear(x, y):
            continue
        field.append((x, y))
    for x, y in field[:22]:
        out.append(f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(dot(1.6, 6))}" fill="{GROUND}" stroke="none"/>')
    for text, x, y, size, fill in LABELS:
        anchor = ' text-anchor="middle"' if text == "Pleiades" else (' text-anchor="end"' if text == "ο" else "")
        out.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" font-family="UniversNextPro-Light" font-size="{size}px"{anchor}>{text}</text>')
    return out, field[22:34]


def clear(x, y) -> bool:
    for name, (sx, sy, _) in STARS.items():
        reach = 70 if name in ("beta", "zeta") else 12                  # horn stars travel with Spread and Shape
        if math.hypot(x - (CX + sx), y - (CY + sy)) < reach:
            return False
    if math.hypot(x - PLEIADES[0], y - PLEIADES[1]) < 26 or (95 < x < 145 and 124 < y < 138):
        return False
    if 10 < x < 110 and 46 < y < 68:                                    # TAURUS label
        return False
    if 255 < x < 345 and 126 < y < 146:                                 # α Aldebaran label
        return False
    if 405 < x < 465 and 60 < y < 165:                                  # standing comet
        return False
    return True


# ---- header preview (two pages, page 1 edited) ---------------------------------------------------------------
def header(values: dict) -> list[str]:
    o = ['<g id="preview_header">', f'<rect x="0" y="0" width="480" height="38" fill="{BLACK}" stroke="none"/>']
    for i, c in enumerate(G):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    caps = caption(values)
    for col in range(4):
        light = "#CBCBCB" if col < 2 else "#000000"
        a, b = CONTROLS[col], CONTROLS[col + 4]
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 10)" fill="{light}" font-family="UniversNextPro-Light" font-size="10px">{a}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 17.4)" fill="{light}" font-family="UniversNextPro-Light" font-size="20px">{caps[a]}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 33)" fill="#5A5A5A" font-family="UniversNextPro-Light" font-size="10px">{b}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 33)" fill="#707070" font-family="UniversNextPro-Light" font-size="13px">{caps[b]}</text>')
    o.append("</g>")
    return o


def caption(values: dict) -> dict:
    caps = {k: str(round(v * 100)) for k, v in values.items()}
    caps["spread"] = f"{1 + 0.5 * values['spread']:.2f}"
    return caps


# ---- the frame -------------------------------------------------------------------------------------------------
def node(i: int, x: float, y: float, pts, fill: str, stroke: str = "none", width: float | None = None) -> str:
    sw = f' stroke-width="{f(width)}"' if width is not None else (' stroke-width="0.5"' if stroke != "none" else "")
    return f'<path id="{PREFIX}_node_{i}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="{stroke}"{sw}/>'


def frame(v: dict, playing: bool = False) -> str:
    sky, twinkle_at = static_sky()
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
         '<g id="preview_canvas">', '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>', "</g>"]
    o += header(v)
    o += sky

    # Drive · the Milky Way: three lines that spread apart and brighten (position + shade)
    d = v["drive"] * BAND_SPREAD
    dx, dy = BAND_B[0] - BAND_A[0], BAND_B[1] - BAND_A[1]
    ln = math.hypot(dx, dy)
    px, py = -dy / ln, dx / ln
    for k, off in enumerate((-1, 0, 1)):
        ox, oy = BAND_A[0] + px * d * off, BAND_A[1] + py * d * off
        shade = grey((2 + 3 * v["drive"]) / 7) if off == 0 else grey((1 + 2 * v["drive"]) / 7)
        o.append(node(N["BAND"] + k, ox, oy, ribbon([(0, 0), (dx, dy)], 2), shade))

    # Fold · the ecliptic, the two mutable outlines: an arch at 0 that folds back on itself up to 8 times
    gain = 1 + 7 * v["fold"]
    ecl_shade = PRIMARY if playing else SECOND
    for half, (x0, x1) in enumerate(((ECL_X0, 240), (240, ECL_X1))):
        pts = []
        for k in range(32):
            x = x0 + (x1 - x0) * k / 31
            u = (x - ECL_X0) / (ECL_X1 - ECL_X0)
            pts.append((x, ECL_Y - ECL_A * fold_signal(gain * math.sin(math.pi * u))))
        o.append(f'<path id="{PREFIX}_node_{N["ECL_L"] + half}" d="{poly(ribbon(pts, 2 * ECL_HALF))}" fill="none" stroke="{ecl_shade}" stroke-width="1.5"/>')

    # Spread + Shape · horn stars β and ζ out from the head, lifted by Shape
    pos = {}
    for name, (sx, sy, _) in STARS.items():
        x, y = CX + sx, CY + sy
        if name in ("beta", "zeta"):
            x += v["spread"] * 44
            y += (-8 if name == "beta" else 2) * v["spread"] - v["shape"] * 22      # ζ stays clear of the ecliptic
        pos[name] = (x, y)

    # Cutoff · Aldebaran's magnitude: spike, core and halo scale and brighten together; a note flares it
    flare = 0.6 if playing else 0.0
    mag = 0.5 + 1.4 * v["cutoff"] + flare
    ax, ay = pos["ald"]
    spike_k = min(2.0, 0.3 + 1.2 * v["cutoff"] + flare)
    o.append(node(N["ALD"], ax, ay, spike(3.6 * spike_k + 2), grey((2 + 5 * v["cutoff"]) / 7)))
    o.append(node(N["ALD"] + 1, ax, ay, dot(max(1.7, 3.6 * min(2, mag) * 0.7)), PRIMARY))
    o.append(node(N["ALD"] + 2, ax, ay, ring(8 * min(2, mag), 1.2), grey((1 + 3 * v["cutoff"] + (2 if playing else 0)) / 7)))

    for k, name in enumerate(ORDER):
        x, y = pos[name]
        o.append(node(N["STAR"] + k, x, y, dot(STARS[name][2]), SECOND2))

    # joins: placed at star A, turned toward B. Short joins author 30 px, long 100 px, so uniform scale stays ≤ 2
    for k, (a, b) in enumerate(JOINS):
        (xa, ya), (xb, yb) = pos[a], pos[b]
        dist = math.hypot(xb - xa, yb - ya)
        authored = 30 if dist < 60 else 100
        s = dist / authored
        pts = rot(scale(ribbon([(0, 0), (authored, 0)], 1.4), s), math.degrees(math.atan2(yb - ya, xb - xa)))
        o.append(node(N["JOIN"] + k, xa, ya, pts, NONTEXT))

    # Res · the Pleiades tighten and their ring brightens at rest; a note gives the cluster a short turn
    tight = 1 - 0.4 * v["res"]
    turn = (15 + 45 * v["res"]) if playing else 0
    for k, (dxp, dyp, r) in enumerate(PLE7):
        (rx, ry), = rot([(dxp * tight, dyp * tight)], turn)
        o.append(node(N["PLE"] + k, PLEIADES[0] + rx, PLEIADES[1] + ry, dot(r), PRIMARY if playing else SECOND2))
    for k in range(RING_N):
        a = k * 2 * math.pi / RING_N
        arc = [(math.cos(a + t) * 17 * tight, math.sin(a + t) * 12 * tight) for t in (0, 0.22 / tight, 0.44 / tight)]
        o.append(node(N["RING"] + k, PLEIADES[0], PLEIADES[1], ribbon(arc, 1.4), grey((1 + 3 * v["res"]) / 7)))

    # Aphx · a standing comet: the tail lengthens and kinks, gently then wildly (the engine's curve), and brightens
    a = v["aphx"]
    kink = 0.4 * a + 0.6 * a ** 3
    seg_len = 14 * (1 + kink)                                   # authored 14 px, scale 1..2
    x, y = COMET_HEAD
    heading = COMET_DIR
    for k in range(3):
        heading = COMET_DIR + (1 if k % 2 == 0 else -1) * kink * 35 * (k + 1) / 2
        pts = rot(taper(seg_len, 2.6 - 0.6 * k, 2.0 - 0.6 * k), heading)
        o.append(node(N["CSEG"] + k, x, y, pts, grey((1 + 4 * a - 0.5 * k) / 7)))
        x += math.cos(math.radians(heading)) * seg_len
        y += math.sin(math.radians(heading)) * seg_len
    o.append(node(N["CHEAD"], *COMET_HEAD, dot(2.4), grey((3 + 4 * a) / 7)))

    # launched comets: a note may send one across (odds rise with Aphx); none at rest
    for k in range(2):
        base = N["COMET"] + 2 * k
        if playing and k == 0:
            hx, hy, hd = 176, 76, 18
            o.append(node(base, hx, hy, rot([(0, -1.6), (-26, -0.9), (-48, -0.4), (-48, 0.4), (-26, 0.9), (0, 1.6)], hd), SECOND))
            o.append(node(base + 1, hx, hy, dot(2.2), PRIMARY))
        else:
            o.append(node(base, *HIDDEN, taper(48, 3.2, 0.8), SECOND))
            o.append(node(base + 1, *HIDDEN, dot(2.2), PRIMARY))

    # Noise · how many field stars are out: 2 at 0, all 12 at 100; while a note is held some brighten
    shown = 2 + round(10 * v["noise"])
    for k in range(TWINKLE_N):
        x, y = twinkle_at[k]
        if k < shown:
            lit = playing and v["noise"] > 0 and k % 3 == 0
            o.append(node(N["TWINKLE"] + k, x, y, dot(2.6 if lit else 2.0), PRIMARY if lit else SECOND))
        else:
            o.append(node(N["TWINKLE"] + k, *HIDDEN, dot(1.7), NONTEXT))

    # palette entries, parked off screen (display.cpp repaints with these)
    for i, c in enumerate(G + G[1:]):
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
            values = dict(DEFAULTS, **{name: pct / 100})
            (OUT / f"c{n}-{pct:03d}.svg").write_text(frame(values), encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.svg')))} frames to {OUT}")


if __name__ == "__main__":
    main()
