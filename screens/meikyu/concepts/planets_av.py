#!/usr/bin/env python3
"""meikyu planets in motion, with sound: the real player logic driving all three planet layouts at once.

`Meikyu` is a line-for-line port of press() from labyrinth's opxy/machines/meikyu/player.cpp (xorshift32 register,
weights against density, the scale walk, velocity range, Corrupt rolling steps after they play, the playhead moving
eight steps per press). A sequence of presses runs for 32 s while the controls move:

   0– 6 s  defaults (Dens 60, Crpt 20, minor)
   6–14 s  Dens sweeps 60 → 100 → 10 → 60   planets fill, empty, refill
  14–21 s  Crpt 85                            planets swap between solid and wire every phrase
  21–26 s  Scal pentatonic, then major
  26–32 s  Drum on                            phrases become pads off the held note

The page only changes what the device page can: which planets are solid (steps that play at the density), which
ring segments are lit (the last phrase's tones), the text line, the header and the keyboard's played dots. The
three layouts are stacked top to bottom: o1 system, o2 orrery, o3 binary. The sound is a plain plucked voice
standing in for whatever instrument the track would have.

    python3 planets_av.py <tmpdir>      → planets.mp4 (and planets.wav)
"""
from __future__ import annotations

import math
import struct
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import orbits as O
import pages as P

HERE = Path(__file__).resolve().parent
FPS, SR = 30, 44100
BPM = 120
STEP = 60 / BPM / 4                      # one player step = a 16th
LENGTH = 32.0
GATE = 0.11                              # each tone's length, s


# ---- the player (port of player.cpp) ------------------------------------------------------------------------------------
MASKS = [0x5AD, 0xAB5, 0x4A9, 0xFFF]
PADS = [0, 5, 7, 12, 17, 24, 31, 36]
M32 = 0xFFFFFFFF


class Meikyu:
    def __init__(self):
        self.rng = 0x1AB71217
        self.val, self.wt = [0] * 16, [0] * 16
        self.flip = 0
        for i in range(16):
            self.roll(i)
        self.head, self.last_root, self.last_start, self.last_mask, self.phrases = 0, None, 0, 0, 0

    def rand32(self):
        x = self.rng or 0x6D617A65
        x ^= (x << 13) & M32
        x ^= x >> 17
        x ^= (x << 5) & M32
        self.rng = x
        return x

    def pct(self):
        return (self.rand32() >> 8) % 100

    def roll(self, i):
        self.val[i] = (self.rand32() >> 12) & 15
        self.wt[i] = self.pct()
        self.flip &= ~(1 << i)

    def plays(self, i, density):
        on = self.wt[i] < density
        return (not on) if (self.flip >> i) & 1 else on

    @staticmethod
    def scale_note(root, mask, deg):
        r, n = root % 12, root
        k = 0
        while k < 12 and not (mask >> ((n - r + 120) % 12)) & 1:
            n += 1
            k += 1
        while deg > 0:
            n += 1
            if (mask >> ((n - r + 120) % 12)) & 1:
                deg -= 1
        return n

    def press(self, c, note, velocity):
        """→ list of (delay steps, pitch, velocity)"""
        density, corrupt, mask, drum = c["dens"], c["crpt"], MASKS[c["scal"]], c["drum"]
        rng_ = 3 + (velocity * 13) // 128
        start, tones, sounded = self.head, [], 0
        for k in range(8):
            i = (start + k) % 16
            if self.plays(i, density):
                deg = (self.val[i] * rng_) // 15
                pitch = note + PADS[(deg >> 1) & 7] if drum else self.scale_note(note, mask, deg)
                if 0 <= pitch <= 127:
                    acc = self.wt[i] < density // 4
                    tones.append((k, pitch, min(127, velocity + 27) if acc else velocity))
                    sounded |= 1 << k
            if corrupt and self.pct() < corrupt:
                self.roll(i)
        self.head = (start + 8) % 16
        self.phrases = (self.phrases + 1) % 256
        self.last_root, self.last_start, self.last_mask = note, start, sounded
        return tones


# ---- the score ----------------------------------------------------------------------------------------------------------
ROOTS = [50, 50, 53, 45, 50, 57, 53, 48]          # D3 D3 F3 A2 D3 A3 F3 C3
VELS = [70, 96, 60, 110, 84, 120, 66, 100]


def controls(t):
    c = {"dens": 60, "crpt": 20, "scal": 0, "drum": False}
    if 6 <= t < 14:                               # 60 → 100 → 10 → 60
        u = (t - 6) / 8
        c["dens"] = round(60 + 40 * math.sin(2 * math.pi * u) if u < 0.25 else
                          (100 - 90 * (u - 0.25) / 0.5) if u < 0.75 else 10 + 50 * (u - 0.75) / 0.25)
    if 14 <= t < 21:
        c["crpt"] = 85
    if 21 <= t < 23.5:
        c["scal"] = 2
    elif 23.5 <= t < 26:
        c["scal"] = 1
    if t >= 26:
        c["drum"] = True
    return c


def run():
    """→ press events [(t, controls, state snapshot after, tones)] and every tone [(t0, t1, pitch, vel)]"""
    m = Meikyu()
    events, tones = [], []
    t, n = 0.5, 0
    while t < LENGTH - 1.0:
        c = controls(t)
        note, vel = ROOTS[n % len(ROOTS)], VELS[n % len(VELS)]
        plan = m.press(c, note, vel)
        snap = dict(wt=list(m.wt), flip=m.flip, mask=m.last_mask, root=m.last_root, start=m.last_start, count=m.phrases)
        events.append((t, snap))
        for k, pitch, v in plan:
            tones.append((t + k * STEP, t + k * STEP + GATE, pitch, v))
        t += 8 * STEP
        n += 1
    return events, tones


# ---- picture ------------------------------------------------------------------------------------------------------------
KEY_LO = 41                                       # the preview keyboard's 24 keys start at F2


def page_at(t, events):
    c = controls(t)
    p = P.Page(density=c["dens"] / 100, scale=c["scal"], corrupt=c["crpt"] / 100, drum=c["drum"])
    last = None
    for et, snap in events:
        if et <= t:
            last = snap
    if last is not None:
        p.weights = [w if not (last["flip"] >> i) & 1 else (99 if w < c["dens"] else -1) for i, w in enumerate(last["wt"])]
        p.phrase, p.root, p.start, p.count = last["mask"], last["root"], last["start"], last["count"]
    else:
        p.weights = list(Meikyu().wt)
    return p


def footer(p, sounding):
    """the SDK's text line and keyboard, with the keys that are sounding right now marked"""
    o = P.footer(P.Page(phrase=None))[:1]
    o[0] = o[0].replace(">meikyu<", f">{p.line()}<")
    white = [k for k in range(24) if (k + 5) % 12 in (0, 2, 4, 5, 7, 9, 11)]
    kw = 480 / len(white)
    xs = {}
    for n, k in enumerate(white):
        x = n * kw
        xs[k] = x + kw / 2
        o.append(f'<rect x="{x + 0.5:.2f}" y="174" width="{kw - 1:.2f}" height="44" fill="#F0F0F0" stroke="none"/>')
    for k in range(24):
        if (k + 5) % 12 in (1, 3, 6, 8, 10):
            x = xs[k - 1] + kw / 2
            xs[k] = x
            o.append(f'<rect x="{x - kw * 0.3:.2f}" y="174" width="{kw * 0.6:.2f}" height="26" fill="#1A1A1A" stroke="none"/>')
    for pitch in sounding:
        k = pitch - KEY_LO
        while k < 0:
            k += 12
        while k > 23:
            k -= 12
        black = (k + 5) % 12 in (1, 3, 6, 8, 10)
        o.append(f'<circle cx="{xs[k]:.2f}" cy="{190 if black else 208}" r="2.5" fill="{"#F0F0F0" if black else "#000000"}" stroke="none"/>')
    return o


def frame_svg(p, sounding, fn):
    return "\n".join(['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
                      '<rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>'] + fn(p) + footer(p, sounding)
                     + P.header(p) + ["</svg>"])


def picture(out: Path, events, tones):
    from PIL import Image
    styles = list(O.STYLES.values())
    cache = {}

    def key_of(t):
        p = page_at(t, events)
        sounding = tuple(sorted({pi for t0, t1, pi, v in tones if t0 <= t < t1}))
        return (tuple(p.weights), p.phrase, p.root, p.count, round(p.density * 100), p.scale, round(p.corrupt * 100), p.drum, sounding), p, sounding

    def render(i):
        t = i / FPS
        key, p, sounding = key_of(t)
        png = out / f"f{i:04d}.png"
        if key in cache:
            src = cache[key]
            png.write_bytes(src.read_bytes())
            return
        sheet = Image.new("RGB", (480, 3 * 220 + 2 * 4), (30, 30, 30))
        for r, fn in enumerate(styles):
            svg = out / f"t{i:04d}-{r}.svg"
            tmp = out / f"t{i:04d}-{r}.png"
            svg.write_text(frame_svg(p, sounding, fn))
            subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(tmp)], check=True)
            sheet.paste(Image.open(tmp).convert("RGB"), (0, r * 224))
            svg.unlink()
            tmp.unlink()
        sheet.save(png)
        cache[key] = png

    for i in range(int(LENGTH * FPS)):                # sequential: the cache makes most frames copies
        render(i)


# ---- sound --------------------------------------------------------------------------------------------------------------
def sound(wav: Path, tones):
    n = int(LENGTH * SR)
    buf = [0.0] * n
    for t0, t1, pitch, vel in tones:
        hz = 440 * 2 ** ((pitch - 69) / 12)
        g = (vel / 127) ** 1.5
        s0 = int(t0 * SR)
        for k in range(int(0.45 * SR)):
            if s0 + k >= n:
                break
            tt = k / SR
            env = math.exp(-tt / 0.16) * min(1.0, tt / 0.003)
            w = 2 * math.pi * hz * tt
            buf[s0 + k] += g * env * (math.sin(w) + 0.35 * math.sin(2 * w) * math.exp(-tt / 0.05) + 0.12 * math.sin(3 * w))
    peak = max(1e-9, max(abs(x) for x in buf))
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.89 * 32767)) for x in buf))


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    events, tones = run()
    print(len(events), "phrases,", len(tones), "tones")
    wav = HERE / "planets.wav"
    sound(wav, tones)
    picture(tmp, events, tones)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:1336:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "planets.mp4")], check=True)
    print("wrote planets.mp4")


if __name__ == "__main__":
    main()
