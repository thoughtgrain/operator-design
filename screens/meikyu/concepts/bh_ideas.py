#!/usr/bin/env python3
"""meikyu black hole, round 2: five ways to put the sequence on the lensed-disc horizon (blackhole3.py), which stays
as it is, at a fixed size. Each idea gets two frames: (a) a phrase playing at the defaults, (b) one other control.

The sequence is meikyu's own: a 16-step register; a press plays 8 steps from the playhead (the steps whose weight is
under Dens), each step's value picks a scale degree, light steps are accents, and Crpt re-rolls steps after they play.

  1 disc register    16 glints ride the disc; a step's ring is its pitch; the sounding one flares   (b) Crpt 85
  2 infall           every note is a body spiralling in, timed to cross the horizon on its step      (b) Rthm on
  3 photon ring      the hole's edge is the register: 16 arcs; the sounding one flares and its
                     lensed echo lights in the ring underneath                                        (b) Crpt 85
  4 four moons       four moons each carry 4 steps as beads; links between sounding moons bend
                     round the hole like light                                                        (b) Rthm on
  5 jets             notes fire pulses up/down polar jets (high up, low down); a phrase start
                     ripples out through the disc                                                     (b) Crpt 85

    python3 bh_ideas.py <outdir>      → idea{1..5}{a,b}.svg and bh-ideas.png (contact sheet, 1:1 frames)
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import blackhole as B
import blackhole3 as B3
import orbits as O
import orrery2 as R2
import orrery4 as M4
import planets_av as A

HERE = Path(__file__).resolve().parent
path, ell, grey = O.path, O.ell, B3.grey
R = 40.0                                                              # fixed: no scaling with Dens any more
CX, BASE = B3.CX, B3.CY + B3.DISC_DROP * R
T = 5.0                                                               # the shimmer phase every frame is drawn at

# ---- a real phrase from the player -------------------------------------------------------------------------------------
_m = A.Meikyu()
VAL, WT = list(_m.val), list(_m.wt)
DENS = 60
PLAYS = [w < DENS for w in WT]
HEAD = 0                                                              # this press plays steps 0..7
SOUNDING = next(i for i in range(8) if PLAYS[i] and i >= 3)           # the step sounding in the frame
ACCENT = [w < DENS // 4 for w in WT]
REROLLED = {1, 5, 6, 11}                                              # what Crpt 85 just re-rolled (for the (b) frames)


def page(dens=DENS, crpt=20, scal=0, drum=False):
    p = M4.P.Page(density=dens / 100, scale=scal, corrupt=crpt / 100, drum=drum)
    p.weights = WT
    return p


def frame(p, body):
    return B.frame(p, body + O.ringed(446, 40, 12, p, ring=(1.45, 2.4), tilt=0.3))


def disc_xy(rx, a):
    """a point on the disc plane: angle 0 at the right, positive toward the viewer (lower on screen)"""
    return CX + rx * math.cos(a), BASE + 0.034 * rx * math.sin(a)


def star(x, y, s, g, w=1.2):
    return [path([(x - s, y), (x + s, y)], grey(g), w), path([(x, y - s * 0.8), (x, y + s * 0.8)], grey(g), w)]


# ---- 1 disc register ---------------------------------------------------------------------------------------------------
def idea1(crpt=False):
    back, hole, front = B3.light(R, T)
    rot = 0.35
    behind, over = [], []
    for i in range(16):
        a = rot + 2 * math.pi * i / 16
        rx = R * (1.7 + 0.18 * VAL[i])                                # higher degree, wider ring
        x, y = disc_xy(rx, a)
        near = math.sin(a) > 0
        in_phrase = HEAD <= i < HEAD + 8
        if crpt and i in REROLLED:                                    # re-rolled: jumps ring, leaves a streak
            x2, _ = disc_xy(R * (1.7 + 0.18 * ((VAL[i] + 7) % 16)), a)
            (over if near else behind).append(path([(x, y), (x2, y)], grey(0xA0), 1.4))
            (over if near else behind).append(path([(x - 3, y - 6), (x + 3, y + 6)], grey(0x60), 1.2))   # the old spot, struck out
            x = x2
        if i == SOUNDING:
            g, s = 0xF0, 15.0 if ACCENT[i] else 12.0
            (over if near else behind).extend(star(x, y, s, g, 1.8) + [path(ell(x, y, 4.0, 4.0, n=16), grey(0xF0), 1.2, fill="#F0F0F0", close=True)])
            continue
        if not PLAYS[i]:
            g, s = 0x48, 2.5
        else:
            g, s = (0xE0 if in_phrase else 0x90), (8.0 if ACCENT[i] else 6.0)
        if not near:
            g = round(g * 0.7)
        (over if near else behind).append(path([(x, y - s), (x, y + s)], grey(g), 1.8))
    return back + behind + hole + front + over


# ---- 2 infall ----------------------------------------------------------------------------------------------------------
def spiral(start_a, r0, turns, upto, tilt=0.38):
    """a body's path from radius r0 to the horizon over `turns`, in a plane tilted `tilt` (screen y squash);
    returns points from the start to fraction `upto` of the way in"""
    pts = []
    for q in range(49):
        f = upto * q / 48
        r = r0 + (R * 1.02 - r0) * f ** 0.7
        a = start_a + 2 * math.pi * turns * f
        pts.append((CX + r * math.cos(a), BASE + tilt * r * math.sin(a)))
    return pts


def trail(pts, head_g=0xE0, w=1.3, keep=14):
    """the last `keep` points, brightening toward the body"""
    out, tail = [], pts[-keep:]
    for j in range(0, len(tail) - 1, 3):
        g = 0x24 + (head_g - 0x24) * (j + 3) / len(tail)
        out.append(path(tail[j:j + 4], grey(g), w))
    return out


def idea2(rhythm=False):
    back, hole, front = B3.light(R, T)
    over = []
    if not rhythm:
        bodies = [(-2.4, 5.6, 0.9, 0.95, 2.2), (0.5, 5.0, 0.85, 0.62, 3.4), (2.2, 5.8, 0.95, 0.3, 2.6)]   # angle, r0/R, turns, how far in, size
        for a0, r0, turns, upto, size in bodies:
            pts = spiral(a0, r0 * R, turns, upto)
            over += trail(pts)
            x, y = pts[-1]
            over.append(path(ell(x, y, size, size, n=16), grey(0xE0), 1.0, fill="#C8C8C8", close=True))
        flash = [path(ell(CX, BASE, R * 1.03, R * 1.0, n=60), grey(0xF0), 3.2, close=True)]   # one just crossed
    else:                                                              # pads: straight plunges along the disc
        flash = []
        for side, frac, g in ((-1, 0.55, 0xF0), (1, 0.82, 0xB0)):     # kick from the left, snare from the right
            x0, x1 = CX + side * 240, CX + side * R * 1.05
            xh = x0 + (x1 - x0) * frac
            over.append(path([(x0 + (xh - x0) * 0.4, BASE), (xh, BASE)], grey(0x50), 2.0))
            over.append(path([(xh - side * 10, BASE), (xh, BASE)], grey(g), 3.0))
            over.append(path(ell(xh, BASE, 3.6, 3.6, n=16), grey(g), 1.0, fill=grey(g), close=True))
        for x, frac in ((CX - 12, 0.7), (CX + 18, 0.35)):             # hats drop onto the arch from above
            y0, y1 = 22.0, BASE - R * 1.6
            yh = y0 + (y1 - y0) * frac
            over.append(path([(x, y0 + (yh - y0) * 0.5), (x, yh)], grey(0x60), 1.2))
            over.append(path(ell(x, yh, 1.8, 1.8, n=12), grey(0xD0), 1.0, fill="#D0D0D0", close=True))
    return back + hole + flash + front + over


# ---- 3 photon ring -----------------------------------------------------------------------------------------------------
def idea3(crpt=False):
    back, hole, front = B3.light(R, T)
    segs, echo = [], []
    rr = R - 4.0                                                      # just inside the edge, on black, so it reads
    gap = 0.07
    for i in range(16):
        a0 = -math.pi / 2 + 2 * math.pi * i / 16 + gap                # step 0 at the top, clockwise
        a1 = a0 + 2 * math.pi / 16 - 2 * gap
        in_phrase = HEAD <= i < HEAD + 8
        r = rr
        if crpt and i in REROLLED:
            r = rr - (6.0 if i % 2 else 10.0)                         # re-rolled arcs knocked in off the ring
        if i == SOUNDING:
            g, w = 0xF0, 4.2
            mid = (a0 + a1) / 2
            for d in (-0.1, 0.0, 0.1):                                # a flare out across the light
                segs.append(path([(CX + (r + 4) * math.cos(mid + d), BASE + 0.97 * (r + 4) * math.sin(mid + d)),
                                  (CX + (r + 30) * math.cos(mid + d * 1.6), BASE + 0.97 * (r + 30) * math.sin(mid + d * 1.6))], grey(0xF0), 1.4))
            ma0, ma1 = -a1, -a0                                       # the lensed echo, mirrored into the ring below
            er = R * 1.25
            echo.append(path([(CX + er * math.cos(ma0 + (ma1 - ma0) * q / 8), BASE + 0.97 * er * math.sin(ma0 + (ma1 - ma0) * q / 8))
                              for q in range(9)], grey(0xF0), 3.6))
        elif not PLAYS[i]:
            g, w = 0x40, 1.4
        else:
            g, w = (0xE0 if in_phrase else 0x78), (4.0 if ACCENT[i] else 3.0)
        segs.append(path([(CX + r * math.cos(a0 + (a1 - a0) * q / 8), BASE + 0.97 * r * math.sin(a0 + (a1 - a0) * q / 8))
                          for q in range(9)], grey(g), w))
    return back + echo + hole + segs + front


# ---- 4 four moons ------------------------------------------------------------------------------------------------------
MOONS = [(2.0, -0.35, 2.4, 0.2), (2.35, 0.25, 4.3, 0.42), (2.75, -0.15, 3.0, 0.7), (3.15, 0.1, 5.2, 0.93)]   # r/R, lean, size, phase


def moon_xy(r, lean, a):
    x, y = r * math.cos(a), 0.34 * r * math.sin(a)                    # each orbit tilted toward us and leaned its own way
    c, s = math.cos(lean), math.sin(lean)
    return CX + x * c - y * s, BASE + x * s + y * c


def idea4(rhythm=False):
    back, hole, front = B3.light(R, T)
    behind, over = [], []
    pos = {}
    for m, (rf, lean, size, ph) in enumerate(MOONS):
        a = 2 * math.pi * ph
        near = math.sin(a) > 0
        side = over if near else behind
        side.append(path([moon_xy(R * rf, lean, 2 * math.pi * q / 60) for q in range(61)], grey(0x30 if near else 0x22), 0.8))
        for j in range(4):                                             # its four steps as beads trailing behind it
            i = 4 * m + j
            ab = a - 0.22 * (j + 1)
            bx, by = moon_xy(R * rf, lean, ab)
            g = 0xF0 if i == SOUNDING else (0xB0 if PLAYS[i] else 0x40)
            side.append(path(ell(bx, by, 1.4, 1.4, n=10), grey(g), 0.8, fill=grey(g) if PLAYS[i] else "#000000", close=True))
        x, y = moon_xy(R * rf, lean, a)
        sounding = SOUNDING // 4 == m
        if rhythm and m in (0, 2):                                    # struck pads jump up off their orbit, then fall back
            side.append(path([(x, y), (x, y - 14)], grey(0x50), 0.8))
            y -= 14
        fill, line = (("#F0F0F0", "#7A7A7A") if sounding or (rhythm and m in (0, 2)) else R2.WIRE)
        side.append(R2.node(B.GLYPHS[[0, 6, 14, 24][m]][0], x, y, size / 10 * 1.4, fill, line, 0.9))
        pos[m] = (x, y)
    if not rhythm:                                                    # the link from the last sounding moon to this one
        (x0, y0), (x1, y1) = pos[(SOUNDING // 4 + 3) % 4], pos[SOUNDING // 4]
        pts = []
        for q in range(41):                                           # a curve bent up over the hole, like the light
            f = q / 40
            bx, by = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            lift = math.sin(math.pi * f) * R * 1.35
            pts.append((bx, by - lift))
        over.append(path(pts, grey(0xE0), 1.3))
    return back + behind + hole + front + over


# ---- 5 jets ------------------------------------------------------------------------------------------------------------
def jet(y0, y1, crpt):
    """a polar jet from y0 to y1: three lines, centre brightest; Crpt kinks it"""
    out = []
    for dx, g in ((-1.6, 0x40), (1.6, 0x40), (0.0, 0x90)):
        pts = []
        for q in range(25):
            f = q / 24
            kink = (6 * math.sin(f * 17.0) * math.sin(f * 5.3) if crpt else 0.0) * f
            pts.append((CX + dx * (1 + 1.5 * f) + kink, y0 + (y1 - y0) * f))
        out.append(path(pts, grey(g), 1.0))
    return out


def idea5(crpt=False):
    back, hole, front = B3.light(R, T)
    top0, bot0 = BASE - R * 1.62, BASE + R * 1.42
    jets = jet(top0, 22, crpt) + jet(bot0, 218, crpt)
    pulses = []
    for frac, up, length, g in ((0.2, True, 9, 0xF0), (0.55, True, 5, 0xB0), (0.85, True, 4, 0x70), (0.4, False, 7, 0xC0)):
        y0, y1 = (top0, 22) if up else (bot0, 218)
        y = y0 + (y1 - y0) * frac
        f = frac
        kink = (6 * math.sin(f * 17.0) * math.sin(f * 5.3) * f) if crpt else 0.0
        d = -1 if up else 1
        pulses.append(path([(CX + kink, y), (CX + kink, y - d * length * 1.8)], grey(g), 3.6))
    ripple = [path(B3.disc_half(R * 3.2, R * 0.12, R, True), grey(0xF0), 3.0)]   # the phrase's downbeat, moving out
    back = back + [path(B3.disc_half(R * 3.2, R * 0.12, R, False), grey(0xC0), 3.0)]
    return back + jets + hole + front + ripple + pulses


IDEAS = [("1 disc register", idea1, {"crpt": 85}), ("2 infall", idea2, {"drum": True}), ("3 photon ring", idea3, {"crpt": 85}),
         ("4 four moons", idea4, {"drum": True}), ("5 jets", idea5, {"crpt": 85})]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, fn, alt in IDEAS:
        n = name.split()[0]
        pair = []
        for tag, kw, p in (("a", {}, page()), ("b", {("rhythm" if "drum" in alt else "crpt"): True}, page(**alt))):
            svg = out / f"idea{n}{tag}.svg"
            svg.write_text(frame(p, fn(**kw)))
            png = out / f"idea{n}{tag}.png"
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(png)], check=True)
            pair.append(Image.open(png))
        rows.append((name, pair))
    sheet = Image.new("RGB", (40 + 960 + 10, 10 + len(rows) * 230), "#1A1A1A")
    d = ImageDraw.Draw(sheet)
    for r, (name, (a, b)) in enumerate(rows):
        y = 10 + r * 230
        d.text((12, y + 100), name.split()[0], fill="#C8C8C8")
        sheet.paste(a, (40, y))
        sheet.paste(b, (530, y))
    sheet.save(HERE / "bh-ideas.png")
    print("wrote bh-ideas.png")


if __name__ == "__main__":
    main()
