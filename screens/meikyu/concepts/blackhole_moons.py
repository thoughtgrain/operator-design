#!/usr/bin/env python3
"""meikyu black hole, idea 4 animated: four moons round the lensed-disc horizon, in a melody and a drum version.

The horizon is blackhole3's at a fixed size. Four moons circle close in on their own tilted orbits, inner ones faster.

Melody (Rthm off), one plucked voice:
  steps         each moon owns four of the 16 steps, carried as beads trailing behind it on its orbit: filled if
                the step plays at this Dens, hollow if not, brighter while it's in the phrase that's playing
  a note        its bead flashes and its moon fills; the moon stays filled until the phrase moves on
  links         from the moon that sounded last to the one sounding now, a curve bent up over the hole like the
                light round it: draws out fast, fades slowly; a repeat on the same moon just flashes it
  Crpt          a re-rolled step's bead throws off a small ring as it changes
  Scal          the scale only changes the notes; the picture holds still so the change is heard, not seen

Drums (Rthm on, Scal reads Kit), a synthesized kit:
  moons         become the kit: the biggest (outermost) is the kick, then snare, tom, and the small fast inner hat
  a hit         the moon jumps up off its orbit and falls back, height by velocity, and leaves a mark on its orbit
                where it was struck; the marks fade over two seconds, so each orbit shows that drum's recent rhythm
  kick          the hole thumps: the edge thickens and the near disc brightens for a beat
  snare         the ring under the hole flashes
  Kit           kit 1 tight and dry, kit 2 deeper and longer (heard), the header reads Kit / kit N

    python3 blackhole_moons.py <tmpdir> melody|drum   → moons-melody.mp4 / moons-drum.mp4 (+ stills)
"""
from __future__ import annotations

import math
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

import blackhole as B
import blackhole3 as B3
import orbits as O
import orrery2 as R2
import orrery4 as M4
import planets_av as A

HERE = Path(__file__).resolve().parent
path, ell, grey = O.path, O.ell, B3.grey
R = 40.0
CX, BASE = B3.CX, B3.CY + B3.DISC_DROP * R
MODE = "melody"

# ---- the moons ---------------------------------------------------------------------------------------------------------
# (orbit radius ÷ R, lean, size px, start phase, period s): inner ones faster
MOONS = [(2.0, -0.35, 2.6, 0.20, 13.0), (2.35, 0.25, 4.3, 0.42, 16.5), (2.75, -0.15, 3.2, 0.70, 21.0),
         (3.15, 0.10, 5.4, 0.93, 25.5)]
GLYPH_OF = [0, 6, 14, 24]
KIT = {0: 3, 1: 3, 2: 1, 3: 1, 4: 2, 5: 2, 6: 0, 7: 0}               # pad → moon: kick outer, snare, tom, hat inner
KIT_NAME = {3: "kick", 1: "snare", 2: "tom", 0: "hat"}
BEAD_GAP = 0.24                                                       # radians between a moon and each of its beads
JUMP_T, JUMP_H = 0.36, 16.0                                           # a struck moon's hop: seconds, px at full velocity
MARK_LIFE = 2.0


def moon_angle(m, t):
    return 2 * math.pi * (MOONS[m][3] + t / MOONS[m][4])


def orbit_xy(m, a):
    rf, lean = MOONS[m][0], MOONS[m][1]
    x, y = R * rf * math.cos(a), 0.34 * R * rf * math.sin(a)          # tilted toward us, then leaned its own way
    c, s = math.cos(lean), math.sin(lean)
    return CX + x * c - y * s, BASE + x * s + y * c


def near(a):
    return math.sin(a) > 0


# ---- the score ---------------------------------------------------------------------------------------------------------
LENGTH = 26.0


def controls(t):
    c = {"dens": 60, "crpt": 20, "scal": 0, "drum": MODE == "drum"}
    for t0, t1, v0, v1 in ((5, 8, 60, 100), (8, 12, 100, 25), (12, 14, 25, 60)):
        if t0 <= t < t1:
            c["dens"] = round(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
    if 14 <= t < 19:
        c["crpt"] = 85
    if t >= 19:
        c["scal"] = 1                                                  # major, or kit 2
    return c


def hits_of(presses):
    """every sounded step: (time, step, pitch, velocity, pad)"""
    out = []
    for pr, plan in zip(presses, PLANS):
        pads = M4.KITS[controls(pr["t"])["scal"]]
        for k, i, pitch, v in plan:
            out.append((pr["t"] + k * M4.STEP, i, pitch, v, pads.index(pitch - pr["root"]) if MODE == "drum" else None))
    return out


def rerolls(presses):
    """(time, step) for each step a press re-rolled (its weight changed), timed at the step's slot in the phrase"""
    out, prev = [], list(M4.Player().wt)
    for pr in presses:
        for i in range(16):
            if pr["wt"][i] != prev[i]:
                k = (i - pr["start"]) % 16
                out.append((pr["t"] + min(k, 7) * M4.STEP, i))
        prev = pr["wt"]
    return out


PLANS = []


def run():
    """orrery4's run, keeping each press's tones so pads can be read back"""
    m = M4.Player()
    presses, tones = [], []
    t, n = 0.5, 0
    while t < LENGTH - 1.0:
        c = controls(t)
        note, vel = M4.ROOTS[n % 8], M4.VELS[n % 8]
        plan = m.press(c, note, vel)
        presses.append(dict(t=t, wt=list(m.wt), mask=m.last_mask, root=note, start=m.last_start, count=m.phrases, vel=vel,
                            hits=[(t + k * M4.STEP, i) for k, i, _, _ in plan]))
        PLANS.append(plan)
        tones += [(t + k * M4.STEP, t + k * M4.STEP + A.GATE, pitch, v) for k, _, pitch, v in plan]
        t += 8 * M4.STEP
        n += 1
    return presses, tones


# ---- the picture -------------------------------------------------------------------------------------------------------
def scene(p, last, t, hits, rolls):
    back, hole, front = B3.light(R, t)
    recent = [h for h in hits if 0 <= t - h[0] < 2.5]
    behind, over, guides = [], [], []

    if MODE == "drum":                                                 # kick thump and snare flash
        kick = [t - h[0] for h in recent if KIT[h[4]] == 3 and t - h[0] < 0.22]
        snare = [t - h[0] for h in recent if KIT[h[4]] == 1 and t - h[0] < 0.18]
        if kick:
            k = 1 - min(kick) / 0.22
            hole = [path(ell(CX, BASE, R + 1.5 * k, (R + 1.5 * k) * 0.97, n=60), "#F0F0F0", 1.7 + 3.0 * k, fill="#000000", close=True)]
            front.append(path(B3.disc_half(R * 1.9, R * 0.06, R, True), grey(0xF0), 2.0 + 2.0 * k))
        if snare:
            k = 1 - min(snare) / 0.18
            back.append(path(B3.under(R * 1.12, R), grey(0xA0 + 0x50 * k), 2.0 + 3.0 * k))

    sounding_now = {h[1]: t - h[0] for h in recent if t - h[0] < M4.FLASH}
    phrase_steps = {i for _, i in last["hits"]} if last else set()
    phrase_live = last is not None and t - last["t"] < 8 * M4.STEP + 0.3
    pos = {}
    for m in range(4):
        a = moon_angle(m, t)
        side = over if near(a) else behind
        for half in (0, 1):                                            # the orbit: a faint guide under all the light,
            pts = [orbit_xy(m, math.pi * half + math.pi * q / 30) for q in range(31)]   # so it never cuts across it
            guides.append(path(pts, grey(0x34 if half == 0 else 0x24), 0.8))

        if MODE == "melody":
            for j in range(4):                                         # its four steps as beads behind it
                i = 4 * m + j
                ab = a - BEAD_GAP * (j + 1)
                bx, by = orbit_xy(m, ab)
                bs = over if near(ab) else behind
                plays = p.weights[i] < p.density * 100
                if i in sounding_now:
                    bs.append(path(ell(bx, by, 2.6, 2.6, n=12), "#F0F0F0", 1.0, fill="#F0F0F0", close=True))
                else:
                    g = (0xD8 if (i in phrase_steps and phrase_live) else 0x98) if plays else 0x44
                    bs.append(path(ell(bx, by, 1.5, 1.5, n=10), grey(g), 0.9, fill=grey(g) if plays else "#000000", close=True))
                for tr, ir in rolls:                                   # re-rolled: a ring thrown off the bead
                    if ir == i and 0 <= t - tr < 0.5:
                        k = (t - tr) / 0.5
                        bs.append(path(ell(bx, by, 2 + 7 * k, 2 + 7 * k, n=16), grey(0xC0 - 0x90 * k), 0.9, close=True))
        else:                                                          # drum: marks where this drum was struck
            for th, i, pitch, v, pad in recent:
                if KIT[pad] != m or t - th > MARK_LIFE:
                    continue
                am = moon_angle(m, th)
                mx, my = orbit_xy(m, am)
                k = (t - th) / MARK_LIFE
                ms = over if near(am) else behind
                ms.append(path([(mx, my - 2.5), (mx, my + 2.5)], grey(0xD0 - 0xA8 * k), 1.6))

        x, y = orbit_xy(m, a)
        size = MOONS[m][2]
        fill, line = R2.WIRE
        if MODE == "melody":
            mine = [i for i in range(4 * m, 4 * m + 4)]
            if phrase_live and any(i in phrase_steps and last and any(th <= t and ii == i for th, ii in last["hits"]) for i in mine):
                fill, line = R2.FILLED
            if any(i in sounding_now for i in mine):
                fill, line = "#F0F0F0", "#7A7A7A"
        else:
            struck = [(t - h[0], h[3]) for h in recent if KIT[h[4]] == m and t - h[0] < JUMP_T]
            if struck:
                age, v = min(struck)
                f = age / JUMP_T
                hop = JUMP_H * (0.4 + 0.6 * v / 127) * 4 * f * (1 - f)
                side.append(path([(x, y), (x, y - hop)], grey(0x50), 0.8))
                y -= hop
                fill, line = ("#F0F0F0", "#7A7A7A") if age < M4.FLASH else R2.FILLED
        side.append(R2.node(B.GLYPHS[GLYPH_OF[m]][0], x, y, size / 10 * 1.4, fill, line, 0.9))
        pos[m] = (x, y)

    links = []
    if MODE == "melody":
        seq = [h for h in recent if h[0] <= t]
        pairs = [(a_, b_) for a_, b_ in zip(seq, seq[1:]) if a_[1] // 4 != b_[1] // 4 and b_[0] - a_[0] < 0.6]
        for h0, h1 in pairs[-M4.LINKS:]:
            age = t - h1[0]
            if age > M4.CONNECT + M4.FADE:
                continue
            reach = min(1.0, age / M4.CONNECT)
            fade = 1.0 if age < M4.CONNECT else 1.0 - (age - M4.CONNECT) / M4.FADE
            g = 0xF0 if fade > 0.66 else 0x8A if fade > 0.33 else 0x4A
            pts = bent(pos[h0[1] // 4], pos[h1[1] // 4], reach)
            if len(pts) > 1:
                links.append(path(pts, grey(g), 1.6 if g == 0xF0 else 1.2))
    return guides + behind + back + hole + front + over + links


def bent(p0, p1, reach):
    """a link that bends round the hole like light: it travels round the centre (over the top when the moons are on
    opposite sides) and is drawn in toward the photon ring halfway, instead of going straight across"""
    def polar(p):
        dx, dy = p[0] - CX, (p[1] - BASE) / 0.97
        return math.hypot(dx, dy), math.atan2(dy, dx) + math.pi / 2  # 0 = straight up
    (r0, a0), (r1, a1) = polar(p0), polar(p1)
    a0 = (a0 + math.pi) % (2 * math.pi) - math.pi
    a1 = (a1 + math.pi) % (2 * math.pi) - math.pi
    pts = []
    for q in range(int(40 * reach) + 1):
        f = q / 40
        r = r0 + (r1 - r0) * f
        r -= math.sin(math.pi * f) * max(0.0, r - 1.3 * R) * 0.55      # pulled in toward the ring as it passes
        a = a0 + (a1 - a0) * f - math.pi / 2
        pts.append((CX + r * math.cos(a), BASE + 0.97 * r * math.sin(a)))
    return pts


def frame(p, last, body):
    return B.frame(p, body + O.ringed(446, 40, 12, p, ring=(1.45, 1.8 + 1.4 * ((last["vel"] if last else 64) / 127)), tilt=0.3))


# ---- sound -------------------------------------------------------------------------------------------------------------
SR = A.SR


def drums(wav, hits):
    n = int(LENGTH * SR)
    buf = np.zeros(n)
    noise = np.random.default_rng(7).uniform(-1, 1, SR)
    for th, i, pitch, v, pad in hits:
        kit2 = controls(th)["scal"] == 1
        g = (v / 127) ** 1.3
        s0 = int(th * SR)
        drum = KIT_NAME[KIT[pad]]
        L = int(0.6 * SR)
        tt = np.arange(L) / SR
        if drum == "kick":
            f0, f1, dec = (130, 48, 0.32) if not kit2 else (110, 38, 0.6)
            ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt / 0.045)) / SR
            x = np.sin(ph) * np.exp(-tt / dec) * 1.2
        elif drum == "snare":
            dec = 0.13 if not kit2 else 0.22
            body = np.sin(2 * np.pi * (190 if not kit2 else 165) * tt) * np.exp(-tt / 0.06)
            x = 0.55 * body + 0.7 * noise[:L] * np.exp(-tt / dec)
        elif drum == "tom":
            f = (150 if not kit2 else 110) * (1 + 0.25 * np.exp(-tt / 0.05)) * (1 + 0.12 * (pitch % 5) / 4)
            x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (0.18 if not kit2 else 0.32))
        else:
            hp = noise[:L] - np.concatenate([[0.0], noise[:L - 1]])  # a crude high-pass: first difference
            open_ = v > 100
            x = 0.45 * hp * np.exp(-tt / (0.16 if open_ else 0.035 if not kit2 else 0.06))
        e = min(n, s0 + L)
        buf[s0:e] += g * x[:e - s0]
    write(wav, buf)


def write(wav, buf):
    peak = max(1e-9, float(np.max(np.abs(buf))))
    pcm = (buf / peak * 0.89 * 32767).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---- main --------------------------------------------------------------------------------------------------------------
def main():
    global MODE
    tmp, MODE = Path(sys.argv[1]), sys.argv[2]
    tmp.mkdir(parents=True, exist_ok=True)
    M4.controls = controls
    M4.LENGTH = A.LENGTH = LENGTH
    presses, tones = run()
    hits, rolls = hits_of(presses), rerolls(presses)
    wav = tmp / f"moons-{MODE}.wav"
    if MODE == "drum":
        drums(wav, hits)
    else:
        A.sound(wav, tones)
    n = int(LENGTH * A.FPS)
    keep = {int(tt * A.FPS) for tt in (3, 7, 11, 16, 21, 24)}

    def render(i):
        t = i / A.FPS
        p, last = M4.page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(frame(p, last, scene(p, last, t, hits, rolls)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in keep:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    out = HERE / f"moons-{MODE}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
    ims = [Image.open(tmp / f"f{k:04d}.png") for k in sorted(keep)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / f"moons-{MODE}-stills.png")
    print("wrote", out.name, len(hits), "hits")


if __name__ == "__main__":
    main()
