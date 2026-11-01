#!/usr/bin/env python3
"""Theseus, round 1: five designs in the stacked-blocks language (P10 Voice field, after library/toro-blocks).

Theseus is a DFAM-style drum voice: every note is a hit, the note picks the drum (low = kick, middle = toms and
snare, high = hats and metal), and a hit LFO steps once per note, a cycle every 32 .. 2 hits (Rate). So the screen's
heartbeat is the hit, its geography is the zone, and its slow motion is the hit LFO.

  t1 kit towers   five towers, one per drum zone; a hit punches its zone's tower up and decay lets it fall
  t2 step floor   a 16-step bed; each hit raises the cell at its step, in its zone's row; the LFO is a wave across
  t3 labyrinth    a maze of block walls; a token takes one step per hit along a loop whose length is the LFO cycle
  t4 crater       one slab; a hit punches a crater where its zone lands and the rim rings outward with decay
  t5 hit stack    each hit stacks a block in its zone's lane; the stack falls when the LFO completes a cycle

Controls (header): decay punch cutoff fm / noise lfo rate tune.

    python3 screens/theseus/concepts/blocks.py      → t*/<pose>.svg and board-blocks.png
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
sys.path.insert(0, str(HERE.parent.parent / "toro"))
import gen_frames as g  # noqa: E402  (f, poly, G, fold_signal)

f, poly, G = g.f, g.poly, g.G
W, H = 480, 220
CONTROLS = ["decay", "punch", "cutoff", "fm", "noise", "lfo", "rate", "tune"]
DEFAULTS = {"decay": 0.27, "punch": 0.43, "cutoff": 0.49, "fm": 0.24, "noise": 0.12, "lfo": 0.0, "rate": 0.49, "tune": 0.5}
RATES = [32, 24, 18, 14, 10, 8, 6, 4, 3, 2]
FONT = 'font-family="UniversNextPro-Light"'


# ---- theseus's model ---------------------------------------------------------------------------------------------------
def period(v):
    return RATES[min(9, round(v["rate"] * 9))]


def lfo_at(n, v):
    """the hit LFO's value (−1..1) at hit number n: a triangle, one cycle every `period` hits"""
    p = period(v)
    ph = (n % p) / p
    return 1 - 4 * abs(ph - 0.5)


def tau(v, zone):
    """seconds for a hit to decay: 30 ms .. 1.5 s, high drums shorter"""
    return (0.03 + 1.47 * v["decay"] ** 2) * (1 - 0.6 * zone)


def env(age, v, zone):
    return math.exp(-age / tau(v, zone)) if age is not None and age >= 0 else 0.0


def zone_of(note, v):
    """tune shifts which drum a note picks (±24 semitones over a 0..1 zone range)"""
    return max(0.0, min(1.0, note + (v["tune"] - 0.5) * 0.8))


class Hits:
    """a phrase: (time of hit, note 0..1). `now` is the moment drawn"""

    def __init__(self, seq=(), now=0.0):
        self.seq, self.now = list(seq), now

    def played(self):
        return [(i, t, n) for i, (t, n) in enumerate(self.seq) if t <= self.now]

    def last(self):
        p = self.played()
        return p[-1] if p else None

    def count(self):
        return len(self.played())


# ---- drawing helpers -------------------------------------------------------------------------------------------------
def path(pts, fill, x=0.0, y=0.0):
    return f'<path transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="{poly(pts)}" fill="{fill}" stroke="{fill}" stroke-width="0.3"/>'


def cube(x, y, s, h, top, left=None, right=None, d=None):
    """an isometric column with its base centre at (x, y): half-width s, height h, depth ratio 0.5"""
    d = s * 0.5 if d is None else d
    left = left or G[3]
    right = right or G[1]
    t = [(x, y - h - d), (x + s, y - h), (x, y - h + d), (x - s, y - h)]
    l_ = [(x - s, y - h), (x, y - h + d), (x, y + d), (x - s, y)]
    r_ = [(x, y - h + d), (x + s, y - h), (x + s, y), (x, y + d)]
    return [path(l_, left), path(r_, right), path(t, top)]


def iso(i, j, ox, oy, s):
    return ox + (i - j) * s, oy + (i + j) * s * 0.5


def header(v) -> list[str]:
    o = ['<rect x="0" y="0" width="480" height="38" fill="#000000" stroke="none"/>']
    for i, c in enumerate(G):
        o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}" stroke="none"/>')
    def cap(k):
        if k == "rate":
            return str(period(v))
        if k == "tune":
            st = round((v["tune"] - 0.5) * 48)
            return f"{st:+d}" if st else "0"
        return str(round(v[k] * 100))
    for col in range(4):
        light = "#CBCBCB" if col < 2 else "#000000"
        a, b = CONTROLS[col], CONTROLS[col + 4]
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 10)" fill="{light}" {FONT} font-size="10px">{a}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 17.4)" fill="{light}" {FONT} font-size="20px">{cap(a)}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * col} 33)" fill="#5A5A5A" {FONT} font-size="10px">{b}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * col} 33)" fill="#707070" {FONT} font-size="13px">{cap(b)}</text>')
    return o


def frame(v, body):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + body + header(v) + ["</svg>"])


def lit(level):
    return G[max(1, min(7, round(level)))]


def specks(v, hits, cx, cy, spread, seed=0):
    """noise: loose single blocks thrown off the last hit"""
    out = []
    last = hits.last()
    if not last:
        return out
    i, t, note = last
    age = hits.now - t
    e = env(age, v, zone_of(note, v))
    n = round(14 * v["noise"] * (0.3 + 0.7 * zone_of(note, v)))
    rnd = random.Random(seed + i)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = spread * (0.4 + 0.8 * rnd.random()) * (0.4 + 0.6 * (1 - e))
        out += cube(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5 - 18 * e, 3, 3, G[6], G[4], G[2])
    return out


# ---- t1 · kit towers ---------------------------------------------------------------------------------------------------
def towers(v, hits):
    """a kit on a riser: a 9 × 3 slab of blocks; the five drums are the middle row's odd columns, rising on a hit"""
    o = []
    nx, ny, s = 9, 3, 17
    ox, oy = 240 - (nx - ny) * s / 2 - 4, 120
    zones = {1: 0.02, 3: 0.3, 4: 0.5, 5: 0.7, 7: 0.95}
    sway = v["lfo"] * lfo_at(hits.count(), v)
    cells = sorted([(i, j) for i in range(nx) for j in range(ny)], key=lambda c: (c[0] + c[1], c[0]))
    for i, j in cells:
        x, y = iso(i, j, ox, oy, s)
        if j == 1 and i in zones:
            z = zones[i]
            e = 0.0
            for k, t, note in hits.played():
                if abs(zone_of(note, v) - z) < 0.13:
                    e = max(e, env(hits.now - t, v, z))
            rest = 14 + 10 * (1 - z)
            total = rest + (14 + 66 * v["punch"]) * e
            nb = max(1, math.ceil(total / 10))
            hb = total / nb
            for b in range(nb):
                top = lit(4 + 3 * e * (0.4 + 0.6 * v["cutoff"]) * (b + 1) / nb)
                jag = v["fm"] * 4 * (1 if b % 2 else -1) * (0.3 + e)
                o += cube(x + sway * b * 2 + jag, y - b * hb, s * (0.86 - 0.04 * b * v["fm"]), hb, top, G[3], G[1])
        else:
            o += cube(x, y, s, 8 + 2 * ((i + j) % 2), G[2] if (i + j) % 2 else "#3C3C3C", G[1], "#191919")
    o += specks(v, hits, 240, 130, 90, 1)
    return o


# ---- t2 · step floor ---------------------------------------------------------------------------------------------------
def floor(v, hits):
    o = []
    nx, ny, s = 16, 4, 12
    ox, oy = 240 - (nx - ny) * s / 2, 104
    step_h = {}
    for i, t, note in hits.played():
        z = zone_of(note, v)
        cell = (i % nx, min(ny - 1, int(z * ny)))
        e = env(hits.now - t, v, z)
        step_h[cell] = max(step_h.get(cell, 0.0), e)
    head = hits.count() % nx
    cells = sorted([(i, j) for i in range(nx) for j in range(ny)], key=lambda c: (c[0] + c[1], c[0]))
    for i, j in cells:
        x, y = iso(i, j, ox, oy, s)
        wave = v["lfo"] * 8 * math.sin(2 * math.pi * (i - hits.count()) / period(v))
        e = step_h.get((i, j), 0.0)
        h = 8 + max(0.0, wave) + (10 + 44 * v["punch"]) * e
        top = lit(3 + (1 if i % 4 == 0 else 0) + (2 if i == head else 0) + 4 * e * (0.5 + 0.5 * v["cutoff"]))
        if v["fm"] > 0.2 and e > 0.05:                                   # fm: the raised cell splits into two
            o += cube(x - 3, y, s * 0.5, h, top, G[3], G[1])
            o += cube(x + 3, y + 1.5, s * 0.5, h * (1 - 0.4 * v["fm"]), top, G[3], G[1])
        else:
            o += cube(x, y, s * 0.8, h, top, G[3], G[1], d=s * 0.4)
    o += specks(v, hits, 240, 150, 90, 2)
    return o


# ---- t3 · labyrinth ----------------------------------------------------------------------------------------------------
MAZE = ["###########",
        "#.....#...#",
        "#.###.#.#.#",
        "#.#...#.#.#",
        "#.#.###.#.#",
        "#.#.....#.#",
        "#.#######.#",
        "#.........#",
        "###########"]
LOOP = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (4, 3), (3, 3), (3, 4), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5),
        (7, 4), (7, 3), (7, 2), (7, 1), (8, 1), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (8, 7), (7, 7),
        (6, 7), (5, 7), (4, 7), (3, 7), (2, 7), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3), (1, 2)]


def labyrinth(v, hits):
    o = []
    s = 12
    rows, cols = len(MAZE), len(MAZE[0])
    ox, oy = 240 - (cols - rows) * s / 2, 66
    p = period(v)
    loop = [LOOP[round(k * (len(LOOP) - 1) / max(1, p - 1))] for k in range(p)] if p < len(LOOP) else LOOP
    n = hits.count()
    pos = loop[n % len(loop)] if n else loop[0]
    last = hits.last()
    e = env(hits.now - last[1], v, zone_of(last[2], v)) if last else 0.0
    zone = zone_of(last[2], v) if last else 0.0
    trail = {loop[(n - k) % len(loop)]: k for k in range(1, min(len(loop), 6))} if n else {}
    path_set = set(loop)
    cells = sorted([(c, r) for r in range(rows) for c in range(cols)], key=lambda q: (q[0] + q[1], q[0]))
    for c, r in cells:
        x, y = iso(c, r, ox, oy, s)
        if MAZE[r][c] == "#":
            # walls breathe with the last hit: punch lifts them, the zone decides which half of the maze
            near = 1.0 - abs((c / (cols - 1)) - zone)
            h = 10 + (12 * v["punch"] * e * max(0.0, near) ** 2) + v["fm"] * 4 * ((c + r) % 2) * e
            o += cube(x, y, s, h, lit(3 + 2 * v["cutoff"] * e + (1 if (c + r) % 3 == 0 else 0)), G[3], G[1])
        else:
            mark = (c, r) in path_set
            k = trail.get((c, r))
            top = G[2] if not mark else G[3]
            if k:
                top = lit(6 - k)
            o.append(path([(x, y - s * 0.5), (x + s, y), (x, y + s * 0.5), (x - s, y)], top))
            if (c, r) == pos:                                            # Theseus: a raised marker that hops each hit
                o += cube(x, y, s * 0.65, 14 + 22 * e * (0.5 + v["punch"]), G[7], G[5], G[3])
    o += specks(v, hits, 240, 130, 110, 3)
    return o


# ---- t4 · crater -------------------------------------------------------------------------------------------------------
def crater(v, hits):
    o = []
    nx, ny, s = 14, 6, 11
    ox, oy = 240 - (nx - ny) * s / 2, 92
    tilt = v["lfo"] * lfo_at(hits.count(), v)
    cells = sorted([(i, j) for i in range(nx) for j in range(ny)], key=lambda c: (c[0] + c[1], c[0]))
    impacts = []
    for i, t, note in hits.played():
        z = zone_of(note, v)
        impacts.append((z * (nx - 1), (ny - 1) / 2, hits.now - t, z))
    for i, j in cells:
        x, y = iso(i, j, ox, oy, s)
        h = 16 + tilt * 8 * (i / (nx - 1) - 0.5) * 2
        bright = 3
        for cx, cy, age, z in impacts[-4:]:
            d = math.hypot(i - cx, (j - cy) * 1.6)
            e = env(age, v, z)
            depth = (6 + 22 * v["punch"]) * e * math.exp(-(d / 1.4) ** 2)
            speed = 6 + 10 * v["cutoff"]
            ring = (5 + 10 * v["punch"]) * e * math.exp(-((d - speed * age) / (1.0 + 2 * v["fm"])) ** 2)
            h += -depth + ring
            bright += 4 * ring / 15
        o += cube(x, y, s * 0.9, max(3, h), lit(bright + (0.6 if (i + j) % 2 else 0)), G[3], G[1], d=s * 0.45)
    o += specks(v, hits, impacts[-1][0] * 11 + 140 if impacts else 240, 120, 60, 4)
    return o


# ---- t5 · hit stack ----------------------------------------------------------------------------------------------------
def stack(v, hits):
    o = []
    lanes = 4
    s = 20
    ox, oy = 228, 176
    p = period(v)
    n = hits.count()
    since = n % p if n else 0
    lane_blocks = [[] for _ in range(lanes)]
    played = hits.played()
    for i, t, note in played[len(played) - since:] if since else []:
        z = zone_of(note, v)
        lane_blocks[min(lanes - 1, int(z * lanes))].append((i, t, z))
    for lane in range(lanes):
        x = ox + (lane - 1.5) * 2 * s * 1.15
        y = oy - (lane - 1.5) * 8
        o += cube(x, y, s, 6, G[2], G[2], G[1])
        hgt = 6
        for b, (i, t, z) in enumerate(lane_blocks[lane]):
            e = env(hits.now - t, v, z)
            th = 9 + 7 * v["punch"]
            shift = v["fm"] * 5 * math.sin(i * 2.3) + v["lfo"] * 6 * lfo_at(i, v)
            o += cube(x + shift, y - hgt, s * (0.92 - 0.04 * b), th, lit(3 + 4 * e * (0.5 + 0.5 * v["cutoff"])), G[3], G[1])
            hgt += th
    # the cycle counter: a column of ticks at the right, one per hit until the stack falls
    for k in range(p if p <= 16 else 16):
        on = k < (since * min(16, p) / p)
        o.append(path([(430, 196 - k * 9), (444, 196 - k * 9), (444, 192 - k * 9), (430, 192 - k * 9)], G[6] if on else G[2]))
    o += specks(v, hits, 240, 140, 90, 5)
    return o


STYLES = {"t1-towers": towers, "t2-floor": floor, "t3-labyrinth": labyrinth, "t4-crater": crater, "t5-stack": stack}


def phrase(v, upto):
    """a bar of sixteenths: kick, hat, snare, hat … with a tom fill"""
    notes = [0.02, 0.9, 0.5, 0.9, 0.02, 0.9, 0.5, 0.85, 0.02, 0.9, 0.5, 0.9, 0.3, 0.4, 0.5, 0.65]
    seq = [(k * 0.125, n) for k, n in enumerate(notes)]
    return Hits(seq, upto)


def main():
    D = dict(DEFAULTS)
    poses = {
        "rest": (D, Hits()),
        "kick": (D, Hits([(0.0, 0.02)], 0.04)),
        "snare": (D, Hits([(0.0, 0.5)], 0.04)),
        "hat": (D, Hits([(0.0, 0.92)], 0.04)),
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
            dr.text((2, P_ + 18 + i * (H + P_) + 2), "", fill=(200, 200, 200))
            for j, pose in enumerate(poses):
                png = Path(tmp) / f"{name}-{pose}.png"
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(HERE / name / f"{pose}.svg"), "-o", str(png)], check=True)
                sheet.paste(Image.open(png).convert("RGB"), (P_ + j * (W + P_), P_ + 18 + i * (H + P_)))
    sheet.save(HERE / "board-blocks.png")
    print("wrote", len(STYLES) * len(poses), "frames")


if __name__ == "__main__":
    main()
