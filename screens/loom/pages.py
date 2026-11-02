#!/usr/bin/env python3
"""Loom's four pages, mapped from Brian's spec (the four-page screen spec, Nov 2 2026).

Each page is drawn at its resting pose, 480 × 220, at the positions and sizes the spec gives, with plausible state
so every element shows. This is a layout map, not finished artwork: it checks that the parts fit, counts outlines,
nodes and text slots per page against the spec's own limits, and shows where the spec contradicts itself.

Grey only (Brian, Nov 2): no hue anywhere. Every role the spec gave a colour is carried by a shape or a word instead;
map.md has the table.

    python3 pages.py            → maps/m1..m4.svg/.png (1:1), maps/m1..m4-map.png (2×, numbered), maps/pages.png
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "maps"
FONT = 'font-family="UniversNextPro-Light"'


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def G(v):
    return f"#{v:02X}{v:02X}{v:02X}"


K0, K1, K2, K3, K4 = G(0x32), G(0x4B), G(0x64), G(0x96), G(0xCD)        # black is #000000; four greys + white


class Page:
    """collects parts and counts them the way the spec does: outlines (animated, ≤ 4), nodes (≤ 512), texts (≤ 16 free)"""

    def __init__(self, name):
        self.name, self.svg, self.outlines, self.nodes, self.texts, self.marks = name, [], 0, 0, 0, []

    def path(self, pts, stroke, w=1.0, fill="none", close=True, kind="node"):
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else "")
        self.svg.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')
        if kind == "outline":
            self.outlines += 1
        elif kind == "node":
            self.nodes += 1

    def circle(self, x, y, r, stroke, fill="none", w=1.0):
        self.svg.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{f(w)}"/>')
        self.nodes += 1

    def rect(self, x, y, w, h, stroke, fill="none", sw=1.0, kind="node"):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], stroke, sw, fill, kind=kind)

    def text(self, x, y, s, size=10, fill=K4, slot=True):
        self.svg.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{fill}" {FONT} font-size="{size}px">{s}</text>')
        if slot:
            self.texts += 1

    def mark(self, n, x, y, label):
        """a numbered callout for the 2× map (not part of the artwork)"""
        self.marks.append((n, x, y, label))


def ring_pts(cx, cy, r, n=64, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n)]


def ribbon(pts, half=0.5):
    """a line as a thin closed ribbon: out one edge, back a little away (the device draws open lines as streaks)"""
    out, back = [], []
    for i, (x, y) in enumerate(pts):
        x2, y2 = pts[min(i + 1, len(pts) - 1)]
        x1, y1 = pts[max(i - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * half, dx / L * half
        out.append((x + nx, y + ny))
        back.append((x - nx, y - ny))
    return out + back[::-1]


# ---- shared on every page ----------------------------------------------------------------------------------------------
TITLES = {"m1": ("steps", "pulses", "cycles", "division"), "m2": ("repeats", "time", "voicing", "range"),
          "m3": ("velocity", "sustain", "accent", "timing"), "m4": ("pitch", "scale", "channel", "random")}
VALUES = {"m1": ("16", "5", "6", "1/16"), "m2": ("4", "1/32", "climb", "sine"), "m3": ("96", "1/2", "agogo", "58%"),
          "m4": ("F#", "major", "ch 3", "25%")}


def header(pg, page):
    """the SDK's two-page header, y 0–38 (supplied by the SDK; drawn here only so the page reads)"""
    steps = [0x00, 0x32, 0x4B, 0x64, 0x7D, 0x96, 0xAF, 0xCD]
    for i, g in enumerate(steps):
        pg.svg.append(f'<rect x="{60 * i}" y="18" width="60" height="20" fill="{G(g)}" stroke="none"/>')
    for col, (t, v) in enumerate(zip(TITLES[page], VALUES[page])):
        light = "#CBCBCB" if col < 2 else "#000000"
        pg.text(5 + 120 * col, 28, t, 10, light, slot=False)
        pg.text(65 + 120 * col, 36, v, 20 if len(v) <= 4 else 13, light, slot=False)
    pg.text(5, 12, "ctrl names on shift", 10, K2, slot=False)
    pg.mark(0, 240, 9, "SDK two-page header, y 0–38 (16 of the 32 text slots)")


def badge(pg, mode="pulses"):
    pg.rect(8, 200, 64, 14, K1, K1, 1.0)
    pg.text(14, 210.5, mode, 10, K4)
    pg.mark(90, 40, 207, "pad-mode badge")


STRIP_X, STRIP_Y, CW, CH, GAP = 96.0, 164.0, 32.0, 20.0, 4.0


def strip(pg, cells, lit=(), hollow=(), half=(), texts=False):
    """the 16-cell strip (2 × 8), at rest showing the mode's 16 steps; with texts it's the key view overlay"""
    for i in range(16):
        r, c = divmod(i, 8)
        x, y = STRIP_X + c * (CW + GAP), STRIP_Y + r * (CH + GAP)
        on = cells[i] if cells else False
        fill = K4 if i in lit else (K3 if on else "#000000")
        stroke = K4 if i in lit else (K3 if on else K1)
        pg.rect(x, y, CW, CH, stroke, fill, 1.0)
        if i in half:
            pg.rect(x, y + CH / 2, CW, CH / 2, K3, K3, 0.5)
        if texts:
            pg.text(x + 4, y + 14, str(i + 1), 10, "#000000" if i in lit else K3)
    pg.mark(91, 240, 186, "16-cell strip / key view overlay (2 × 8, 32 × 20)")


MODE_KEYS = ["B", "P", "T", "M", "Cl", "Cp", "S", "Ct"]


def mode_keys(pg, lit=()):
    for i, lab in enumerate(MODE_KEYS):
        r, c = divmod(i, 4)
        x, y = 392 + c * 21.33, 164 + r * 32
        on = i in lit
        pg.rect(x, y, 16, 16, K4 if on else K2, K4 if on else "#000000", 1.0)
        pg.text(x + 3, y + 11.5, lab, 10, "#000000" if on else K3)
    pg.mark(92, 432, 156, "mode keys (2 × 4, 16 × 16)")


# ---- M1 shape: the step ring -------------------------------------------------------------------------------------------
STEPS = 16
EUCLID = {0, 3, 6, 10, 13}
MANUAL = {8}
RETRIG = {12}
HEAD = 6


def m1():
    pg = Page("m1")
    header(pg, "m1")
    cx, cy, r = 240.0, 104.0, 56.0
    pg.path(ring_pts(cx, cy, r + 0.5, 32) + ring_pts(cx, cy, r - 0.5, 32)[::-1], K4, 0.6, kind="outline")   # 32 + 32 = 64
    pg.mark(1, cx + r + 4, cy - 30, "ring · outline 0 (64 pts, ribbon)")
    a = -math.pi / 2 + 2 * math.pi * HEAD / STEPS
    pg.path([(cx + (r - 7) * math.cos(a), cy + (r - 7) * math.sin(a)), (cx + (r + 7) * math.cos(a), cy + (r + 7) * math.sin(a)),
             (cx + (r + 7) * math.cos(a) + 1, cy + (r + 7) * math.sin(a)), (cx + (r - 7) * math.cos(a) + 1, cy + (r - 7) * math.sin(a))],
            K4, 1.0, K4, kind="outline")
    pg.mark(2, cx + (r + 12) * math.cos(a), cy + (r + 12) * math.sin(a), "playhead · outline 1 (advisory)")
    for s in range(STEPS):
        a = -math.pi / 2 + 2 * math.pi * s / STEPS
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if s in RETRIG:
            pg.rect(x - 4, y - 4, 8, 8, K4, K4)
        elif s in MANUAL:
            pg.circle(x, y, 5, K4, K4)
            pg.nodes -= 1
        elif s in EUCLID:
            pg.circle(x, y, 5, K3, K3)
        else:
            pg.circle(x, y, 3, K2, K2)
    pg.circle(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * 8 / 16), cy + r * math.sin(-math.pi / 2 + 2 * math.pi * 8 / 16), 7.5, K3, "none")  # manual's ring (shares the node)
    pg.nodes -= 1
    pg.mark(3, cx + r + 10, cy + 10, "16 step nodes: silent 3 px · Euclid 5 px · manual 5 px + ring · retrig square")
    sa = -math.pi / 2
    pg.circle(cx + (r - 12) * math.cos(sa), cy + (r - 12) * math.sin(sa), 2, K3, K3)
    pg.mark(4, cx + 6, cy - r + 14, "rotation source dot")
    pg.path([(cx - 4, cy - r + 20), (cx, cy - r + 25), (cx + 4, cy - r + 20), (cx, cy - r + 22)], K4, 1.0, K4)
    pg.mark(5, cx - 22, cy - r + 24, "start chevron")
    pg.text(cx - 18, 150, "1/16 free", 10, K3)                       # the word, not a colour, says free-running
    pg.mark(6, cx + 14, 147, "division text (240, 150)")
    for i in range(16):                                                # cycles: 16 tiny squares, y 132
        x = cx - 40 + i * 5.2
        fill = K4 if i == 1 else (K1 if i == 3 else (K3 if i < 6 else "none"))
        stroke = K4 if i == 1 else (K3 if i in (4, 5) else (K1 if i >= 6 else K3))
        pg.rect(x, 130, 3.6, 3.6, stroke, fill if i not in (4, 5) else "none", 0.8)
    pg.mark(7, cx - 46, 132, "16 cycle squares (y 132): lit · current · muted · looped hollow")
    pg.text(cx - 9, cy + 4, "p1/1", 10, K2)
    pg.mark(8, cx, cy + 4, "page text p2/4 (steps > 16)")
    badge(pg)
    strip(pg, [s in EUCLID | MANUAL | RETRIG for s in range(16)], lit={HEAD})
    mode_keys(pg, lit={3})
    return pg


# ---- M2 shape: repeats and phrase ---------------------------------------------------------------------------------------
def m2():
    pg = Page("m2")
    header(pg, "m2")
    pg.rect(16, 44, 216, 112, K1, "none", 0.6, kind="guide")
    pg.rect(248, 44, 216, 112, K1, "none", 0.6, kind="guide")
    # the repeat ladder: the pulse + 4 repeats accelerating, heights by velocity ramp
    x, gap, base = 40.0, 40.0, 128.0
    for i, vel in enumerate([1.0, 0.82, 0.68, 0.56, 0.46]):
        h = 70 * vel
        pg.rect(x - 3, base - h, 6, h, K4 if i == 0 else K2, K4 if i == 0 else K2)
        x += gap
        gap *= 0.78
    pg.path(ribbon([(37, base + 4), (37 + 40, base + 4)], 0.5), K3, 0.6, kind="outline")
    pg.mark(10, 120, 60, "repeat ladder: ≤ 16 bars, x by time, height by velocity; first = the pulse")
    pg.mark(11, 60, base + 10, "one-step baseline · outline 0")
    pg.text(124, 150, "choke", 10, K3)
    pg.mark(12, 150, 147, "choke / tail text")
    # phrase window: a sine ribbon across 216 px needs more than one outline (reach ±64)
    pts = [(256 + k * 200 / 47, 100 - 30 * math.sin(2 * math.pi * k / 47)) for k in range(48)]
    halves = [pts[:25], pts[23:]]
    for hp in halves:
        pg.path(ribbon(hp, 0.6), K3, 0.6, kind="outline")
    pg.mark(13, 356, 64, "phrase ribbon: outlines 1 + 2 (216 px > the ±64 reach)")
    for i, dy in enumerate([-14, -6, 2, 10]):                          # voicing dashes at the window's left edge
        pg.rect(252, 100 + dy, 10, 2, K4 if i == 0 else K2, K4 if i == 0 else K2)
    pg.mark(14, 266, 112, "voicing: ≤ 8 dashes, first brightest")
    pg.text(356, 52, "climb poly", 10, K3)
    pg.path([(452, 58), (456, 50), (460, 58)], K4, 1.0, K4)
    pg.mark(15, 430, 52, "style text · direction triangle")
    pg.text(356, 150, "×2 · 2 bars", 10, K3)
    pg.mark(16, 410, 147, "phrase speed text")
    badge(pg)
    strip(pg, [True] * 5 + [False] * 11, lit={0}, texts=False)
    mode_keys(pg)
    return pg


# ---- M3 groove: velocity bars -------------------------------------------------------------------------------------------
def m3():
    pg = Page("m3")
    header(pg, "m3")
    vel = [110, 0, 64, 80, 0, 96, 50, 0, 120, 70, 0, 88, 60, 0, 100, 76]
    sus = [0.5, 0, 0.3, 0.5, 0, 0.8, 0.3, 0, 0.5, 0.4, 0, 0.6, 0.3, 0, 0.9, 0.5]
    accent = {0, 8, 14}
    prob = {6, 12}
    x0, dx, base = 24.0, 27.0, 140.0
    # baseline across 432 px: as static nodes (an outline can't reach it)
    pg.rect(x0, base, 432, 1, K2, K2, 0.5)
    pg.mark(20, 30, base + 6, "baseline: 432 px, needs 4 outlines or one static node")
    tmpl = [(x0 + k * 432 / 63, 92 - 30 * math.sin(2 * math.pi * k / 21)) for k in range(64)]
    pg.path(ribbon(tmpl[:22], 0.5), K1, 0.5, kind="outline")
    pg.path(ribbon(tmpl[21:43], 0.5), K1, 0.5, kind="outline")
    pg.path(ribbon(tmpl[42:], 0.5), K1, 0.5, kind="outline")
    pg.mark(21, 240, 58, "groove template curve: 432 px = 3–4 outlines")
    for s in range(16):
        x = x0 + 8 + s * dx + (3 if s % 2 else 0)                     # swing pushes even pulses
        if vel[s] == 0:
            pg.rect(x, base - 2, 1, 4, K1, K1, 0.5)
            continue
        h = 4 + (vel[s] - 1) / 126 * 92
        w = max(3, 22 * sus[s])
        if s in prob:
            pg.rect(x, base - h, w, h, K4, "none", 1.0)
            pg.rect(x, base - h * 0.5, w, h * 0.5, K3, K3, 0.5)
        else:
            pg.rect(x, base - h, w, h, K4 if s in accent else K3, K4 if s in accent else K3, 0.5)
        if s in accent:
            pg.rect(x, base - h - 4, w, 2, K4, K4, 0.5)
    pg.mark(22, 120, 50, "16 pulse bars: height velocity, width sustain")
    pg.mark(23, 250, 40, "accent: brightest + 2 px cap · probability: hollow, filled by chance")
    pg.text(240, 150, "swing 58%", 10, K3)
    pg.mark(24, 290, 147, "swing text; even pulses offset")
    pg.path([(30, 154), (44, 154), (44, 151), (50, 155), (44, 159), (44, 156), (30, 156)], K3, 0.8, K3)
    pg.text(54, 158, "−1/8", 10, K3)
    pg.mark(25, 40, 162, "track delay arrow + text")
    pg.text(440, 52, "len ∞", 10, K3)
    pg.mark(26, 450, 55, "length text")
    badge(pg)
    strip(pg, [v > 0 for v in vel], lit={5})
    mode_keys(pg)
    return pg


# ---- M4 tonal + setup: keyboard strip and routing -----------------------------------------------------------------------
WHITE = [0, 2, 4, 5, 7, 9, 11]
BLACK_LEFT = {1: 1, 3: 2, 6: 4, 8: 5, 10: 6}


def m4():
    pg = Page("m4")
    header(pg, "m4")
    root, scale = 6, {0, 2, 4, 5, 7, 9, 11}                             # F# major
    harmony = {10, 13, 17}
    played = {13}
    kx, ky = 16.0, 52.0
    for black in (False, True):
        for n in range(24):
            o, pc = divmod(n, 12)
            if (pc in BLACK_LEFT) != black:
                continue
            rel = (n - root) % 12
            in_scale = rel in scale
            if black:
                x = kx + (o * 7 + BLACK_LEFT[pc]) * 10 - 3
                w, h = 6, 27
            else:
                x = kx + (o * 7 + WHITE.index(pc)) * 10
                w, h = 10, 44
            if n == root:
                fill = K4
            elif n in played:
                fill = K4
            elif n in harmony:
                fill = K3
            else:
                fill = (K2 if in_scale else K1) if not black else (K1 if in_scale else "#000000")
            pg.rect(x, ky, w, h, K2, fill, 0.6)
    pg.mark(30, 90, 46, "24 keys, white 10 × 44 / black 6 × 27: 2 octaves = 140 px wide, not 280")
    pg.path(ribbon([(kx + 42, ky + 50), (kx + 112, ky + 50)], 0.5), K3, 0.6, kind="outline")
    pg.mark(31, kx + 120, ky + 50, "octave bracket · outline 0")
    pg.text(156, 52, "major", 10, K3)
    pg.text(156, 150, "F#  +3", 10, K4)
    pg.mark(32, 196, 150, "scale name · root name + harmony count")
    for i in range(8):                                                 # target tracks
        r, c = divmod(i, 4)
        x, y = 320 + c * 20, 52 + r * 20
        sel = i in (2, 4)
        own = i == 0
        pg.rect(x, y, 16, 16, K4 if sel else K2, K3 if sel else "#000000", 1.0 if not own else 1.6)
        pg.text(x + 5, y + 12, str(i + 1), 10, "#000000" if sel else K3)
    pg.mark(33, 404, 62, "8 target squares (1 hollow = own)")
    pg.text(306, 64, "trk", 10, K2)
    for i in range(16):                                                # MIDI channels: circles, so they never read as tracks
        r, c = divmod(i, 8)
        x, y = 326 + c * 16, 106 + r * 16
        pg.circle(x, y, 5.5, K4 if i == 2 else K2, K3 if i == 2 else "#000000", 1.0)
    pg.text(306, 110, "ch", 10, K2)
    pg.mark(34, 456, 106, "16 channel circles (word 'ch'; tracks are squares, word 'trk')")
    rnd = [(316 + k * 144 / 47, 140 + 4 * math.sin(k * 2.7) * math.cos(k * 1.3)) for k in range(48)]
    pg.path(ribbon(rnd[:25], 0.5), K3, 0.6, kind="outline")
    pg.path(ribbon(rnd[24:], 0.5), K3, 0.6, kind="outline")
    pg.text(388, 156, "rnd 25% bar", 10, K3)
    pg.mark(35, 330, 150, "random ribbon: 152 px = 2 outlines")
    badge(pg, "keys")
    strip(pg, [True] * 16, lit={0})
    mode_keys(pg)
    return pg


# ---- render ------------------------------------------------------------------------------------------------------------
def render(pg):
    svg = "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                     '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + pg.svg + ["</svg>"])
    (OUT / f"{pg.name}.svg").write_text(svg)
    png = OUT / f"{pg.name}.png"
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(OUT / f"{pg.name}.svg"), "-o", str(png)], check=True)
    big = Image.open(png).convert("RGB").resize((960, 440), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for n, x, y, _ in pg.marks:                                        # numbered callouts
        X, Y = 2 * x, 2 * y
        d.ellipse((X - 9, Y - 9, X + 9, Y + 9), fill="#FFFFFF", outline="#000000")
        d.text((X - (6 if n >= 10 else 3), Y - 6), str(n), fill="#000000")
    big.save(OUT / f"{pg.name}-map.png")
    return png


def main():
    OUT.mkdir(exist_ok=True)
    pages = [m1(), m2(), m3(), m4()]
    ims = []
    for pg in pages:
        render(pg)
        ims.append(Image.open(OUT / f"{pg.name}-map.png"))
        print(f"{pg.name}: outlines {pg.outlines}/4 · nodes {pg.nodes} (+ header, palette donors) · texts {pg.texts}/16 free")
    sheet = Image.new("RGB", (960, 4 * 450), "#1A1A1A")
    for k, im in enumerate(ims):
        sheet.paste(im, (0, k * 450))
    sheet.save(OUT / "pages.png")


if __name__ == "__main__":
    main()
