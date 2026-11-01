#!/usr/bin/env python3
"""Theseus, round 2: five designs that look like drums, in the house's grey geometric language.

Every drum is built from a few clean primitives (an ellipse for the head, a band for the shell, small blocks for
lugs and hoops) so drawing quality never depends on a hand-drawn outline, and every part a hit moves is a whole
node that translates or scales.

  d1 kit          a five-piece kit in three-quarter view: kick, snare, two toms, hi-hat
  d2 overhead     the same kit from above: every head is a set of rings, a hit ripples its head
  d3 one drum     theseus is one voice that becomes every drum: a single shell that turns kick → tom → snare →
                  hat with the zone of each hit
  d4 drum tower   drums stacked in a tower from kick at the base to hats at the top; a hit lifts its tier
  d5 pads         a 4 × 4 drum-machine pad grid; each hit presses and lights its pad

Shares the model and header with blocks.py: hits, zones from note + tune, decay, the hit LFO.

    python3 screens/theseus/concepts/drums.py      → d*/<pose>.svg and board-drums.png
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blocks import (DEFAULTS, G, Hits, env, f, frame, lfo_at, path, period, phrase, poly, zone_of)  # noqa: E402

W, H = 480, 220
DARK = "#191919"


# ---- primitives ------------------------------------------------------------------------------------------------------
def ellipse(cx, cy, rx, ry, n=36, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + (0 if a1 - a0 >= 2 * math.pi - 1e-6 else 1))]


def ring(cx, cy, rx, ry, w, n=36):
    """an elliptical ring as one outline (outer round, a hairline seam, inner round back)"""
    out = ellipse(cx, cy, rx, ry, n)
    inn = ellipse(cx, cy, max(0.5, rx - w), max(0.3, ry - w * ry / rx), n)
    return out + [out[0], (inn[0][0] + 0.01, inn[0][1])] + inn[::-1]


def shell(cx, cy, rx, ry, h, side=None, edge=None, lugs=0, lug=None):
    """an upright drum: the side band, a darker right third, the front of the lower hoop, lugs. The head is drawn
    separately because a hit moves it"""
    side = side or G[3]
    front = ellipse(cx, cy + h, rx, ry, 24, math.pi, 0)                          # left → right along the bottom front
    o = [path([(cx - rx, cy)] + front + [(cx + rx, cy)], side)]
    a = math.acos(0.4)
    shade_bottom = ellipse(cx, cy + h, rx, ry, 8, a, 0)                           # from x = 0.4 rx to the right edge
    o.append(path([(cx + 0.4 * rx, cy + ry * math.sin(a))] + shade_bottom[::-1][::-1] + [(cx + rx, cy)], edge or G[1]))
    hoop_out = ellipse(cx, cy + h, rx, ry, 24, math.pi, 0)
    hoop_in = ellipse(cx, cy + h - 2.2, rx, ry, 24, 0, math.pi)
    o.append(path(hoop_out + hoop_in, G[5]))                                      # front of the lower hoop
    for k in range(lugs):                                                         # tension lugs on the front
        t = math.pi * (0.2 + 0.6 * k / max(1, lugs - 1))
        lx, ly = cx + rx * math.cos(t) * 0.98, cy + h * 0.5 + ry * math.sin(t)
        o.append(path([(lx - 1.6, ly - h * 0.22), (lx + 1.6, ly - h * 0.22), (lx + 1.6, ly + h * 0.22), (lx - 1.6, ly + h * 0.22)], lug or G[5]))
    return o


def head(cx, cy, rx, ry, e, v, tone=None):
    """the batter head: a hoop, a skin that dips on the hit, rings that spread with decay"""
    o = []
    dip = e * (1.5 + 4 * v["punch"])
    o.append(path(ellipse(cx, cy, rx, ry), tone or G[5]))
    o.append(path(ellipse(cx, cy + dip * 0.3, rx * 0.86, ry * 0.86), G[4] if e < 0.05 else G[min(7, 4 + round(3 * e * (0.4 + 0.6 * v["cutoff"])))]))
    if e > 0.03:
        for k in range(1 + round(3 * v["decay"])):
            u = ((1 - e) * 0.9 + k * 0.22) % 1
            o.append(path(ring(cx, cy + dip * 0.3, rx * 0.84 * u + 1.5, ry * 0.84 * u + 0.8, 1.4), G[7 if k == 0 else 6]))
    o.append(path(ring(cx, cy, rx, ry, 2.2), G[6]))                              # top hoop
    return o


def cymbal(cx, cy, r, e, v, tilt=0.0, wob=0.0):
    """a cymbal: a thin disc with lathe rings, tipping on a hit"""
    ry = r * (0.22 + 0.12 * wob)
    o = [path(ellipse(cx, cy + 1.5, r, ry), DARK), path(ellipse(cx, cy, r, ry), G[5] if e < 0.05 else G[min(7, 5 + round(2 * e))])]
    for k in range(2, 6):
        o.append(path(ring(cx, cy, r * k / 6, ry * k / 6, 0.9), G[4]))
    o.append(path(ellipse(cx, cy - 1, r * 0.12, ry * 0.3), G[6]))
    if v["fm"] > 0.05 and e > 0.05:                                               # fm: shimmer arcs off the edge
        for k in range(round(1 + 3 * v["fm"])):
            a = -0.4 - 0.5 * k
            o.append(path(ring(cx, cy, r + 4 + 3 * k, ry + 2 + 1.5 * k, 1.0, 24)[:0] or ellipse(cx, cy, r + 4 + 3 * k, ry + 1.5 + k, 10, a - 0.35, a + 0.35) + ellipse(cx, cy, r + 3 + 3 * k, ry + 1 + k, 10, a + 0.35, a - 0.35), G[6]))
    return o


def stand(x, y0, y1, w=1.6):
    return path([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y1), (x - w / 2, y1)], G[3])


def hit_env(v, hits, zone_center, width=0.14):
    """this drum's envelope: the strongest recent hit whose zone falls in its band"""
    e = 0.0
    for i, t, note in hits.played():
        z = zone_of(note, v)
        if abs(z - zone_center) < width:
            e = max(e, env(hits.now - t, v, z))
    return e


def sizzle(v, hits, cx, cy, spread, seed=0):
    out = []
    last = hits.last()
    if not last:
        return out
    i, t, note = last
    z = zone_of(note, v)
    e = env(hits.now - t, v, z)
    rnd = random.Random(seed + i)
    for k in range(round(16 * v["noise"] * (0.3 + 0.7 * z) * (0.3 + e))):
        a = rnd.uniform(-math.pi, 0)
        r = spread * (0.3 + rnd.random()) * (1.2 - e)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.6
        out.append(path([(x - 1, y - 1), (x + 1, y - 1), (x + 1, y + 1), (x - 1, y + 1)], G[6]))
    return out


# ---- d1 · kit ----------------------------------------------------------------------------------------------------------
def kit(v, hits):
    o = []
    sway = v["lfo"] * lfo_at(hits.count(), v) * 3
    ek, es, et1, et2, eh = (hit_env(v, hits, z) for z in (0.02, 0.5, 0.33, 0.68, 0.93))
    # floor: a riser
    o.append(path(ellipse(240, 192, 170, 22), "#1E1E1E"))
    # hi-hat on its stand, left
    o.append(stand(118, 112, 192))
    o += cymbal(118 + sway, 112 - 3 * eh, 30, eh, v, wob=eh)
    o += cymbal(118, 117, 30, 0, v)
    # toms on the kick
    o += shell(205, 92, 26, 9, 22, lugs=3)
    o += head(205 + sway * 0.4, 92 - 3 * et1 * v["punch"], 26, 9, et1, v)
    o += shell(275, 92, 28, 10, 24, lugs=3)
    o += head(275 + sway * 0.4, 92 - 3 * et2 * v["punch"], 28, 10, et2, v)
    # the kick, on its side: the front head faces us
    kx, ky = 240, 150
    bulge = 1 + ek * (0.04 + 0.12 * v["punch"])
    o.append(path([(kx - 54, ky - 46), (kx + 54, ky - 46), (kx + 54, ky + 46), (kx - 54, ky + 46)], DARK))   # the shell's depth
    o.append(path(ellipse(kx + 8, ky - 2, 50, 48), G[2]))
    o.append(path(ellipse(kx, ky, 50 * bulge, 48 * bulge), G[4] if ek < 0.05 else G[min(7, 4 + round(3 * ek * (0.4 + 0.6 * v["cutoff"])))]))
    o.append(path(ring(kx, ky, 50 * bulge, 48 * bulge, 4), G[6]))
    o.append(path(ring(kx, ky, 16, 15.5, 2), G[3]))                                 # port hole
    for k in range(8):                                                             # lugs round the hoop
        a = 2 * math.pi * k / 8 + math.pi / 8
        lx, ly = kx + 54 * math.cos(a), ky + 52 * math.sin(a)
        o.append(path([(lx - 2, ly - 2), (lx + 2, ly - 2), (lx + 2, ly + 2), (lx - 2, ly + 2)], G[5]))
    if ek > 0.03:
        for k in range(1 + round(3 * v["decay"])):
            u = ((1 - ek) * 0.9 + k * 0.22) % 1
            o.append(path(ring(kx, ky, 18 + 30 * u, 17 + 29 * u, 1.5), G[7 if k == 0 else 6]))
    # snare, front right, on a stand
    o.append(stand(352, 140, 192))
    o += shell(352, 128, 32, 11, 16, lugs=4)
    o += head(352 + sway * 0.6, 128 - 2 * es * v["punch"], 32, 11, es, v, tone=G[6])
    o += sizzle(v, hits, 240, 80, 140, 1)
    return o


# ---- d2 · overhead -----------------------------------------------------------------------------------------------------
def overhead(v, hits):
    o = []
    drums = [("hat", 106, 120, 30, 0.93, True), ("snare", 176, 150, 30, 0.5, False), ("tom1", 205, 86, 26, 0.33, False),
             ("tom2", 275, 86, 28, 0.68, False), ("kick", 240, 150, 0, 0.02, False), ("ride", 374, 104, 40, 0.8, True),
             ("floor", 322, 160, 34, 0.2, False)]
    sway = v["lfo"] * lfo_at(hits.count(), v) * 4
    # the kick seen from above is a long shell under everything: a band
    ek = hit_env(v, hits, 0.02)
    o.append(path([(208, 132), (272, 132), (272, 206), (208, 206)], G[2]))
    o.append(path([(208, 132), (272, 132), (272, 137 + 8 * ek * v["punch"]), (208, 137 + 8 * ek * v["punch"])], G[min(7, 4 + round(3 * ek))]))
    for name, x, y, r, z, is_cym in drums:
        if name == "kick":
            continue
        e = hit_env(v, hits, z, 0.1)
        if is_cym:
            o.append(path(ellipse(x + sway, y, r, r * 0.92), G[4] if e < 0.05 else G[min(7, 5 + round(2 * e))]))
            for k in range(2, 7):
                o.append(path(ring(x + sway, y, r * k / 7, r * 0.92 * k / 7, 0.8), G[3]))
            o.append(path(ellipse(x + sway, y, 3, 3), G[6]))
        else:
            o.append(path(ellipse(x, y, r + 3, r + 3), G[3]))
            for k in range(8):                                                     # lugs round the shell
                a = 2 * math.pi * k / 8
                lx, ly = x + (r + 4) * math.cos(a), y + (r + 4) * math.sin(a)
                o.append(path([(lx - 2, ly - 2), (lx + 2, ly - 2), (lx + 2, ly + 2), (lx - 2, ly + 2)], G[5]))
            o.append(path(ellipse(x, y, r, r), G[4] if e < 0.05 else G[min(7, 4 + round(3 * e * (0.4 + 0.6 * v["cutoff"])))]))
            if e > 0.03:
                for k in range(1 + round(3 * v["decay"])):
                    u = ((1 - e) * 0.9 + k * 0.22) % 1
                    o.append(path(ring(x, y, 3 + (r - 3) * u, 3 + (r - 3) * u, 1.4), G[7 if k == 0 else 6]))
            o.append(path(ring(x, y, r, r, 2), G[6]))
        if v["fm"] > 0.05 and e > 0.05 and is_cym:
            for k in range(round(1 + 3 * v["fm"])):
                o.append(path(ring(x + sway, y, r + 4 + 4 * k, r * 0.92 + 4 + 4 * k, 1.0), G[5]))
    o += sizzle(v, hits, 240, 130, 160, 2)
    return o


# ---- d3 · one drum -----------------------------------------------------------------------------------------------------
def one_drum(v, hits):
    o = []
    last = hits.last()
    z = zone_of(last[2], v) if last else 0.5
    e = env(hits.now - last[1], v, z) if last else 0.0
    # the shell morphs with the zone: big and deep (kick) → mid (tom) → shallow with wires (snare) → a cymbal (hat)
    if z > 0.82:
        o.append(stand(240, 120, 200))
        o += cymbal(240, 120 - 6 * e * v["punch"], 92, e, v, wob=e)
        o += cymbal(240, 128, 92, 0, v)
    else:
        rx = 120 - 70 * z
        ry = rx * 0.3
        hgt = 76 - 56 * z
        cy = 150 - hgt / 2 - 6
        o.append(path(ellipse(240, 200, rx + 16, ry * 0.7), "#1E1E1E"))
        o += shell(240, cy, rx, ry, hgt, lugs=4 + round(4 * (1 - z)))
        if 0.38 < z <= 0.82:                                                       # snare wires under the head
            for k in range(6):
                yy = cy + hgt + ry * 0.4 - k * 1.5
                o.append(path([(240 - rx * 0.6, yy), (240 + rx * 0.6, yy), (240 + rx * 0.6, yy + 0.8), (240 - rx * 0.6, yy + 0.8)], G[5]))
        o += head(240, cy - 4 * e * v["punch"], rx, ry, e, v)
    # the next drums waiting: small markers along the bottom for the zones, the current one lit
    for k, zc in enumerate((0.02, 0.33, 0.5, 0.68, 0.93)):
        x = 150 + k * 45
        on = abs(zc - z) < 0.14 and last is not None
        o.append(path(ellipse(x, 212, 8, 2.6), G[6] if on else G[2]))
    o += sizzle(v, hits, 240, 90, 120, 3)
    return o


# ---- d4 · drum tower ---------------------------------------------------------------------------------------------------
def tower(v, hits):
    o = []
    tiers = [(0.02, 80, 24), (0.25, 66, 18), (0.45, 54, 16), (0.65, 44, 12), (0.88, 38, 0)]   # zone, radius, height
    sway = v["lfo"] * lfo_at(hits.count(), v)
    y = 196
    o.append(path(ellipse(240, 200, 100, 14), "#1E1E1E"))
    for k, (z, r, hgt) in enumerate(tiers):
        e = hit_env(v, hits, z, 0.12)
        lift = e * (3 + 10 * v["punch"])
        x = 240 + sway * k * 5
        ry = r * 0.26
        if hgt == 0:                                                               # the top: a hi-hat pair
            o += cymbal(x, y - 8 - lift, r, e, v, wob=e)
            o += cymbal(x, y - 2, r, 0, v)
            break
        top = y - hgt - lift
        o += shell(x, top, r, ry, hgt, lugs=3 + (k == 0))
        o += head(x, top, r, ry, e, v)
        y = top - 4
    o += sizzle(v, hits, 240, 60, 110, 4)
    return o


# ---- d5 · pads ---------------------------------------------------------------------------------------------------------
def pads(v, hits):
    o = []
    n, s = 4, 26
    ox, oy = 240, 92
    pressed = {}
    for i, t, note in hits.played():
        z = zone_of(note, v)
        idx = min(15, int(z * 16))
        pressed[idx] = max(pressed.get(idx, 0.0), env(hits.now - t, v, z))
    cursor = hits.count() % period(v) if hits.count() else -1
    # the case
    cx = [(ox, oy - 8), (ox + n * s + 10, oy + n * s * 0.5 - 3), (ox, oy + n * s + 2), (ox - n * s - 10, oy + n * s * 0.5 - 3)]
    o.append(path([(p[0], p[1] + 14) for p in cx[1:3]] + [cx[2], cx[1]][::-1] if False else [cx[3], cx[2], (cx[2][0], cx[2][1] + 14), (cx[3][0], cx[3][1] + 14)], G[2]))
    o.append(path([cx[2], cx[1], (cx[1][0], cx[1][1] + 14), (cx[2][0], cx[2][1] + 14)], G[1]))
    o.append(path(cx, G[3]))
    cells = sorted([(i, j) for i in range(n) for j in range(n)], key=lambda c: (c[0] + c[1], c[0]))
    for i, j in cells:
        idx = j * n + i
        x = ox + (i - j) * s
        y = oy + (i + j) * s * 0.5 + s * 0.5
        e = pressed.get(idx, 0.0)
        press = e * (2 + 3 * v["punch"])
        h = 6 - press
        sw = s * 0.82
        top = G[min(7, 4 + round(3 * e * (0.4 + 0.6 * v["cutoff"])))] if e > 0.05 else (G[5] if idx == cursor % 16 and v["lfo"] > 0 else G[4])
        t_ = [(x, y - h - sw * 0.5), (x + sw, y - h), (x, y - h + sw * 0.5), (x - sw, y - h)]
        l_ = [(x - sw, y - h), (x, y - h + sw * 0.5), (x, y + sw * 0.5), (x - sw, y)]
        r_ = [(x, y - h + sw * 0.5), (x + sw, y - h), (x + sw, y), (x, y + sw * 0.5)]
        o += [path(l_, G[2]), path(r_, G[1]), path(t_, top)]
        if e > 0.05 and v["fm"] > 0.05:                                             # fm: the pad's glow splits into rings
            for k in range(round(1 + 2 * v["fm"])):
                g_ = 1 + 0.25 * (k + 1) * (1.2 - e)
                ring_pts = [(x, y - h - sw * 0.5 * g_), (x + sw * g_, y - h), (x, y - h + sw * 0.5 * g_), (x - sw * g_, y - h)]
                o.append(path(ring_pts + [ring_pts[0], (x, y - h - sw * 0.5 * g_ + 1.2)] + [(x - sw * g_ + 2.4, y - h), (x, y - h + sw * 0.5 * g_ - 1.2), (x + sw * g_ - 2.4, y - h), (x, y - h - sw * 0.5 * g_ + 1.2)][::-1], G[6]))
    o += sizzle(v, hits, 240, 120, 150, 5)
    return o


STYLES = {"d1-kit": kit, "d2-overhead": overhead, "d3-one-drum": one_drum, "d4-tower": tower, "d5-pads": pads}


def main():
    D = dict(DEFAULTS)
    poses = {
        "rest": (D, Hits()),
        "kick": (D, Hits([(0.0, 0.02)], 0.05)),
        "snare": (D, Hits([(0.0, 0.5)], 0.05)),
        "hat": (D, Hits([(0.0, 0.93)], 0.05)),
        "phrase": (dict(D, lfo=0.7, rate=0.6, decay=0.5), phrase(D, 1.7)),
        "all-100": (dict(D, decay=1, punch=1, cutoff=1, fm=1, noise=1, lfo=1, rate=0.85), phrase(D, 1.3)),
    }
    for name, fn in STYLES.items():
        d = HERE / name
        d.mkdir(exist_ok=True)
        for pose, (vals, hits) in poses.items():
            (d / f"{pose}.svg").write_text(frame(vals, fn(vals, hits)), encoding="utf-8")
    cols, P_ = len(poses), 8
    sheet = Image.new("RGB", (P_ + cols * (W + P_), P_ + 18 + len(STYLES) * (H + P_)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for j, pose in enumerate(poses):
            dr.text((P_ + j * (W + P_), P_), pose, fill=(200, 200, 200))
        for i, name in enumerate(STYLES):
            for j, pose in enumerate(poses):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (P_ + j * (W + P_), P_ + 18 + i * (H + P_)))
    sheet.save(HERE / "board-drums.png")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
