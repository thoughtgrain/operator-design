#!/usr/bin/env python3
"""toro stacked blocks with sound: one score drives both the picture (gen_blocks) and toro's real engine.

The first toro video swept the controls in silence. Here a phrase plays the whole way through and each control is
swept up and back while it plays, so every change on screen is a change you hear.

    python3 blocks_av.py <tmpdir>      → blocks/toro-blocks.mp4 (video + audio)
"""
from __future__ import annotations

import math
import struct
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_blocks as G  # noqa: E402
import gen_frames as g  # noqa: E402

FPS, SR, BLOCK = 30, 44100, 64
OPEN_XY = Path("/home/claude/etcetc000/open-xy/sdk/include")
TORO = Path("/home/claude/thoughtgrain/labyrinth/opxy/machines/toro")
# eight keys, one per patch spot on the field: a D minor pentatonic phrase across two octaves
KEY_HZ = [73.42, 87.31, 98.0, 110.0, 130.81, 146.83, 174.61, 196.0]
RIFF = [0, 4, 2, 5, 1, 6, 3, 7, 0, 4, 2, 5, 1, 3, 6, 4]
STEP, HOLD = 0.3, 0.24                                     # a note every 300 ms, held 240 ms


def score():
    D = dict(g.DEFAULTS)
    length = 30.0
    notes = []
    t, k = 0.6, 0
    while t < length - 0.8:
        notes.append((t, t + HOLD, RIFF[k % len(RIFF)]))
        t += STEP
        k += 1
    sweeps = [(4.0, 7.0, "drive", 1.0), (7.0, 10.0, "spread", 1.0), (10.0, 13.0, "cutoff", 1.0), (13.0, 16.0, "cutoff", 0.0),
              (16.0, 19.0, "fold", 1.0), (19.0, 22.0, "res", 1.0), (22.0, 25.0, "shape", 1.0), (25.0, 27.5, "noise", 1.0),
              (27.5, 29.4, "aphx", 1.0)]

    def values(t):
        v = dict(D)
        for t0, t1, name, to in sweeps:
            if t0 <= t <= t1:
                u = math.sin(math.pi * (t - t0) / (t1 - t0))
                v[name] = D[name] + (to - D[name]) * u
        return v

    return notes, values, length


def picture(out: Path, notes, values, length):
    starts = [n[0] for n in notes]

    def render(i):
        t = i / FPS
        last = max((k for k, s in enumerate(starts) if s <= t), default=None)
        since = None if last is None else t - starts[last]
        key = notes[last][2] if last is not None else 0
        before = last if last is not None else 0
        svg = out / f"f{i:04d}.svg"
        svg.write_text(G.frame_svg(values(t), since, key, before))
        subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", str(svg), "-o", str(out / f"f{i:04d}.png")], check=True)
        svg.unlink()

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(render, range(int(length * FPS))))


def sound(wav: Path, notes, values, length):
    exe = HERE / "audio" / "render"
    if not exe.exists():
        subprocess.run(["g++", "-O2", "-std=c++17", f"-I{OPEN_XY}", f"-I{TORO}", str(HERE / "audio" / "render.cpp"), "-o", str(exe)], check=True)
    nb = int(length * SR / BLOCK)
    lines = [f"blocks {nb}"]
    for b in range(nb):
        v = values(b * BLOCK / SR)
        lines.append(" ".join(f"{v[k]:.5f}" for k in g.CONTROLS))
    lines.append(f"notes {len(notes)}")
    for t0, t1, key in notes:
        lines.append(f"{int(round(t0 * SR / BLOCK))} {int(round(t1 * SR / BLOCK))} {KEY_HZ[key]}")
    raw = subprocess.run([str(exe)], input="\n".join(lines).encode(), capture_output=True, check=True).stdout
    n = len(raw) // 4
    xs = struct.unpack(f"{n}f", raw)
    peak = max(1e-9, max(abs(x) for x in xs))
    gain = 0.89 / peak
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x * gain)) * 32767)) for x in xs))


def main():
    tmp = Path(sys.argv[1])
    tmp.mkdir(parents=True, exist_ok=True)
    notes, values, length = score()
    wav = HERE / "audio" / "toro-blocks.wav"
    sound(wav, notes, values, length)
    picture(tmp, notes, values, length)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-i", str(wav),
                    "-vf", "scale=960:440:flags=neighbor", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(HERE / "blocks" / "toro-blocks.mp4")], check=True)
    print("wrote blocks/toro-blocks.mp4")


if __name__ == "__main__":
    main()
