#!/usr/bin/env python3
"""meikyu black hole, the capture model: the hole does the player's work instead of decorating it.

A step plays when its weight is under Dens; a black hole captures what comes inside a radius. So:

  16 steps      16 bodies riding the disc, each in a fixed slot round it
  weight        distance from the hole: light steps sit close in, heavy ones far out
  Dens          the capture ring in the disc. Bodies inside it are captured, which is to say they play: they rise
                off the disc to their pitch. Bodies outside lie flat and dim. Turn Dens up and the ring widens
  accent        a fainter inner ring at Dens/4: bodies inside it are accents, bigger and brighter
  playhead      the bodies keep their slots (the disc only drifts, a turn a minute); the flashes run round in step
                order, half the disc per press, so the playhead is seen as the order things light up in, not as
                spinning. A step in the phrase now playing stands brighter
  value/pitch   height above the disc: the scale degree (melody) or the pad (drums) at this press's velocity
  velocity      wider spread of heights on a hard press (the player's range), and the light flares with it
  Crpt          a re-rolled body is thrown to its new distance, with a streak from where it was
  Rthm          heights become pad lanes; the kick thumps the hole's edge, the snare flashes the ring under it

The camera is tipped up a little from blackhole3 (the disc reads as an open ellipse rather than a line) so distance
from the hole can be seen. Sound: the plucked voice for melody; blackhole_moons' synthesized kit for drums.

    python3 blackhole_capture.py <tmpdir> melody|drum   → capture-melody.mp4 / capture-drum.mp4 (+ stills)
"""
from __future__ import annotations

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import blackhole as B
import blackhole3 as B3
import blackhole_moons as BM
import orbits as O
import orrery4 as M4
import planets_av as A

HERE = Path(__file__).resolve().parent
path, ell, grey, shimmer = O.path, O.ell, B3.grey, B3.shimmer
R = 36.0
K = R / 30                                                            # px sizes (dots, heights) scale with the hole
ASPECT = 0.16                                                         # disc ellipse height ÷ width (blackhole3 is ~0.03)
CX, BASE = B3.CX, B3.CY + B3.DISC_DROP * R + 4
MODE = "melody"


def reach(w):
    """distance from the hole for a weight 0..100 (also the capture ring for Dens)"""
    return R * (1.45 + 3.45 * w / 100)                                 # from the first disc ring to the outermost


def disc_xy(r, a, h=0.0):
    """angle 0 = right, π/2 = the front (nearest us), h = height above the disc in px"""
    return CX + r * math.cos(a), BASE + ASPECT * r * math.sin(a) - h


def ring(r, near, g, w):
    a0 = 0.0 if near else math.pi
    return path([disc_xy(r, a0 + math.pi * q / 48) for q in range(49)], grey(g), w)


# ---- the light, as wireframe ------------------------------------------------------------------------------------------
# blackhole3's shape, drawn as wire instead of stacked bands: a few thin rails with ribs across them, so the arch and the
# ring under the hole read as a lattice and the middle of the page stays mostly black. Nothing near is drawn across the
# hole except the bodies: the near disc, its spokes and the rings break where they'd cross it, so the hole and the dots
# in front of it stay clear.
ARCH_RAILS = [(1.2, 0xE8, 1.1), (1.42, 0x98, 0.9), (1.66, 0x58, 0.8)]   # radius ÷ R, grey, width
UNDER_RAILS = [(1.18, 0xC0, 1.0), (1.38, 0x60, 0.8)]
DISC_RINGS = [(1.45, 0x50), (2.5, 0x40), (3.6, 0x34), (4.9, 0x2A)]       # radius ÷ R, grey
RIB_G = 0x44


def clear(pts):
    """runs of a polyline outside the hole (a little margin), so near lines break across it"""
    runs, cur = [], []
    for x, y in pts:
        if ((x - CX) / (R * 1.06)) ** 2 + ((y - BASE) / (R * 1.03)) ** 2 < 1:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
        else:
            cur.append((x, y))
    if len(cur) > 1:
        runs.append(cur)
    return runs


def near_path(pts, g, w):
    return [path(run, grey(g), w) for run in clear(pts)]


def ring_pts(r, near):
    a0 = 0.0 if near else math.pi
    return [disc_xy(r, a0 + math.pi * q / 48) for q in range(49)]


def arch_pts(r, flare):
    """blackhole3's bell, but standing on the same disc line as everything else (its own drop made each rail's feet
    land at a different height) and ending flat at its feet with no tail, so it meets the disc cleanly"""
    d0 = 0.86 * r
    h0 = 0.97 * math.sqrt(r * r - d0 * d0)
    m0 = -0.97 * d0 / math.sqrt(r * r - d0 * d0)
    w = r * (1 + flare) - d0
    right = []
    for q in range(12):
        tau = (q + 1) / 12
        h00, h10 = 2 * tau ** 3 - 3 * tau ** 2 + 1, tau ** 3 - 2 * tau ** 2 + tau
        right.append((d0 + w * tau, h00 * h0 + h10 * w * m0))
    top = [(-d0 + 2 * d0 * q / 30, 0.97 * math.sqrt(max(0.0, r * r - (-d0 + 2 * d0 * q / 30) ** 2))) for q in range(31)]
    right = [(x, h) for x, h in right if h > 0.1 * r]                  # stop as it comes down to the disc: no flat
    left = [(-x, h) for x, h in reversed(right)]                       # feet running along the disc line
    return [(CX + x, BASE - h) for x, h in left + top + right]


def under_pts(r):
    """the ring under the hole, starting well below the disc line so its ends don't crowd the hole's sides"""
    d = 0.32
    return [(CX + r * math.cos(d + (math.pi - 2 * d) * q / 40), BASE + 0.97 * r * math.sin(d + (math.pi - 2 * d) * q / 40))
            for q in range(41)]


def lattice(rails, ribs, lift=0):
    """rails (lists of points, inner to outer, same length) and the ribs joining them at every `ribs`-th point"""
    out = []
    n = len(rails[0])
    n = min(len(r) for r in rails)
    off = [(len(r) - n) // 2 for r in rails]                           # rails can differ in length once feet are cut
    for j in range(ribs // 2, n, ribs):
        out.append(path([(x, y + lift) for x, y in (r[j + o] for r, o in zip(rails, off))], grey(RIB_G), 0.7))
    return out


def light(R_, t, flare=0.0):
    back, front = [], []
    b = 1 + 0.35 * flare                                               # a press brightens the wire by its velocity
    arch = [arch_pts(R_ * s, 0.5 + 0.35 * k) for k, (s, _, _) in enumerate(ARCH_RAILS)]
    for k, (s, g, w) in enumerate(ARCH_RAILS):
        back.append(path(arch[k], grey(shimmer(g, k, t) * b), w))
    back += lattice(arch, 5)
    under = [under_pts(R_ * s) for s, _, _ in UNDER_RAILS]
    for k, (s, g, w) in enumerate(UNDER_RAILS):
        back.append(path(under[k], grey(shimmer(g, k + 5, t) * b), w))
    back += lattice(under, 6)
    spin = 2 * math.pi * t / DRIFT
    for k, (s, g) in enumerate(DISC_RINGS):                            # disc rings: far halves behind, near broken
        back.append(path(ring_pts(R_ * s, False), grey(g * b), 0.8))
        front += near_path(ring_pts(R_ * s, True), g * b, 0.8)
    for i in range(16):                                                # a spoke per step: the lane its body rides
        a = 2 * math.pi * (i / 16) + spin
        pts = [disc_xy(reach(0) + (reach(100) - reach(0)) * q / 8, a) for q in range(9)]
        if math.sin(a) > -0.05:
            front += near_path(pts, 0x2C, 0.7)
        else:
            back.append(path(pts, grey(0x24), 0.7))
    hole = [path(ell(CX, BASE, R_, R_ * 0.97, n=60), "#F0F0F0", 1.4, fill="#000000", close=True)]
    return back, hole, front


# ---- the player, with each press's values kept ------------------------------------------------------------------------
LENGTH = 30.0
DRIFT = 60.0                                                          # seconds per turn of the disc: slow, just alive


def controls(t):
    c = {"dens": 50, "crpt": 10, "scal": 0, "drum": MODE == "drum"}
    for t0, t1, v0, v1 in ((4, 7, 50, 100), (7, 11, 100, 15), (11, 13, 15, 50)):
        if t0 <= t < t1:
            c["dens"] = round(v0 + (v1 - v0) * (t - t0) / (t1 - t0))
    if 14 <= t < 21:
        c["crpt"] = 85
    if t >= 22:
        c["scal"] = 2 if MODE == "melody" else 1                         # pentatonic, or kit 2
    return c


def run():
    m = M4.Player()
    presses, tones, plans = [], [], []
    t, n = 0.5, 0
    w_hist = [[(0.0, w)] for w in m.wt]                                # per step: (time, weight) changes
    v_hist = [[(0.0, v)] for v in m.val]
    while t < LENGTH - 1.0:
        c = controls(t)
        note, vel = M4.ROOTS[n % 8], M4.VELS[n % 8]
        before_w, before_v = list(m.wt), list(m.val)
        plan = m.press(c, note, vel)
        start = m.last_start
        for i in range(16):
            if m.wt[i] != before_w[i] or m.val[i] != before_v[i]:
                k = (i - start) % 16
                when = t + (min(k, 7) + 0.5) * M4.STEP                  # just after its slot: it re-rolls once it has played
                w_hist[i].append((when, m.wt[i]))
                v_hist[i].append((when, m.val[i]))
        presses.append(dict(t=t, wt=list(m.wt), mask=m.last_mask, root=note, start=start, count=m.phrases, vel=vel,
                            hits=[(t + k * M4.STEP, i) for k, i, _, _ in plan]))
        plans.append(plan)
        tones += [(t + k * M4.STEP, t + k * M4.STEP + A.GATE, pitch, v) for k, _, pitch, v in plan]
        t += 8 * M4.STEP
        n += 1
    BM.PLANS[:] = plans
    return presses, tones, w_hist, v_hist


def at(hist, t):
    """the value in force at t and when it last changed"""
    v, since, prev = hist[0][1], -9.0, hist[0][1]
    for tt, x in hist:
        if tt <= t:
            prev, v, since = v, x, tt
    return v, since, prev


# ---- the scene ---------------------------------------------------------------------------------------------------------
def height(i, val, last, c):
    """the pitch a step would sound at in the current press, as px above the disc"""
    vel = last["vel"] if last else 64
    rng_ = 3 + (vel * 13) // 128
    deg = (val * rng_) // 15
    if c["drum"]:
        return K * (4.0 + 5.5 * ((deg >> 1) & 7))                              # pad lanes
    root = last["root"] if last else 50
    return K * (4.0 + 1.9 * (A.Meikyu.scale_note(root, A.MASKS[c["scal"]], deg) - root))


def scene(p, last, t, hits, w_hist, v_hist):
    c = controls(t)
    dens = M4.eased(t, lambda tt: controls(tt)["dens"])
    recent = [h for h in hits if 0 <= t - h[0] < 0.6]
    vel_flare = 0.0
    if last and t - last["t"] < 0.5:                                   # a press flares the light by its velocity
        vel_flare = (last["vel"] / 127) * (1 - (t - last["t"]) / 0.5)
    back, hole, front = light(R, t, vel_flare)
    behind, over = [], []

    if c["drum"]:
        kick = [t - h[0] for h in recent if BM.KIT[h[4]] == 3 and t - h[0] < 0.22]
        snare = [t - h[0] for h in recent if BM.KIT[h[4]] == 1 and t - h[0] < 0.18]
        if kick:
            k = 1 - min(kick) / 0.22
            hole = [path(ell(CX, BASE, R + 1.5 * k, (R + 1.5 * k) * 0.97, n=60), "#F0F0F0", 1.6 + 3.0 * k, fill="#000000", close=True)]
        if snare:
            k = 1 - min(snare) / 0.18
            back.append(path(under_pts(R * 1.18), grey(0xA0 + 0x50 * k), 1.4 + 2.5 * k))

    rc, ra = reach(dens), reach(dens / 4)                              # capture ring and accent ring
    behind += [ring(ra, False, 0x58, 1.0), ring(rc, False, 0xA0, 1.5)]
    over += near_path(ring_pts(ra, True), 0x70, 1.0) + near_path(ring_pts(rc, True), 0xF0, 1.7)

    sounding = {h[1]: t - h[0] for h in recent if t - h[0] < M4.FLASH}
    for i in range(16):
        a = 2 * math.pi * (i / 16 + t / DRIFT)                         # fixed slots; the whole disc drifts slowly
        w, w_since, w_prev = at(w_hist[i], t)
        val, _, _ = at(v_hist[i], t)
        throw = (t - w_since) / 0.45 if 0 <= t - w_since < 0.45 else None
        r = reach(w) if throw is None else reach(w_prev) + (reach(w) - reach(w_prev)) * B.smooth(throw)
        inside = B.smooth((dens - w) / 3 + 0.5)                        # 0 outside the ring … 1 inside: eased across it
        accent = w < dens // 4
        h = height(i, val, last, c) * inside
        x0, y0 = disc_xy(r, a)
        x, y = disc_xy(r, a, h)
        side = over if math.sin(a) > -0.05 else behind
        if throw is not None:                                          # Crpt: thrown to its new distance
            ox, oy = disc_xy(reach(w_prev), a, h)
            side.append(path([(ox, oy), (x, y)], grey(0xC0 - 0x80 * throw), 1.4))
        in_phrase = last is not None and (i - last["start"]) % 16 < 8 and t - last["t"] < 8 * M4.STEP
        if inside > 0.05:
            g = (0x50 + 0x50 * in_phrase) * inside
            side.append(path([(x0, y0), (x, y)], grey(0x20 + g), 0.9))   # the stem: its pitch, above its spot
        if i in sounding:
            age = sounding[i] / M4.FLASH
            side.append(path(ell(x, y, 5.0 * K, 5.0 * K, n=16), "#F0F0F0", 1.0, fill="#F0F0F0", close=True))
            side.append(path(ell(x, y, K * (6 + 9 * age), K * (6 + 9 * age), n=20), grey(0xE0 - 0x90 * age), 1.0, close=True))
        elif inside > 0.5:
            s = 3.6 if accent else 2.7
            g = 0xE8 if accent else 0xB0
            side.append(path(ell(x, y, s * K, s * K, n=14), grey(g), 0.9, fill=grey(g), close=True))
        else:
            side.append(path(ell(x, y, 1.9 * K, 1.9 * K, n=10), grey(0x68), 0.9, fill="#000000", close=True))
    return back + behind + hole + front + over


# ---- main --------------------------------------------------------------------------------------------------------------
def main():
    global MODE
    tmp, MODE = Path(sys.argv[1]), sys.argv[2]
    tmp.mkdir(parents=True, exist_ok=True)
    BM.MODE, BM.controls, BM.LENGTH = MODE, controls, LENGTH
    M4.controls = controls
    M4.LENGTH = A.LENGTH = LENGTH
    presses, tones, w_hist, v_hist = run()
    hits = BM.hits_of(presses)
    wav = tmp / f"capture-{MODE}.wav"
    if MODE == "drum":
        BM.drums(wav, hits)
    else:
        A.sound(wav, tones)
    n = int(LENGTH * A.FPS)
    keep = {int(tt * A.FPS) for tt in (3, 6, 9.2, 12, 17, 25)}

    def render(i):
        t = i / A.FPS
        p, last = M4.page_at(t, presses)
        svg = tmp / f"f{i:04d}.svg"
        svg.write_text(BM.frame(p, last, scene(p, last, t, hits, w_hist, v_hist)))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp / f"f{i:04d}.png")], check=True)
        if i not in keep:
            svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(n)))
    out = HERE / f"capture-{MODE}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(A.FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
    ims = [Image.open(tmp / f"f{k:04d}.png") for k in sorted(keep)]
    sheet = Image.new("RGB", (960, 660))
    for k, im in enumerate(ims):
        sheet.paste(im, (480 * (k % 2), 220 * (k // 2)))
    sheet.save(HERE / f"capture-{MODE}-stills.png")
    print("wrote", out.name, len(hits), "hits")


if __name__ == "__main__":
    main()
