#!/usr/bin/env python3
"""The d4 video's soundtrack, from theseus's real engine: the same groove and control automation as the video.

    python3 soundtrack.py out.wav      (builds ./render from render.cpp first if it's missing)
"""
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "concepts"))
from d4_video import score  # noqa: E402
from blocks import CONTROLS  # noqa: E402

SR, BLOCK = 44100, 64
OPEN_XY = Path("/home/claude/etcetc000/open-xy/sdk/include")
THESEUS = Path("/home/claude/thoughtgrain/labyrinth/opxy/machines/theseus")


def main():
    out = Path(sys.argv[1])
    exe = HERE / "render"
    if not exe.exists():
        subprocess.run(["g++", "-O2", "-std=c++17", f"-I{OPEN_XY}", f"-I{THESEUS}", str(HERE / "render.cpp"), "-o", str(exe)], check=True)
    seq, values, length = score()
    nb = int(length * SR / BLOCK)
    lines = [f"blocks {nb}"]
    for b in range(nb):
        v = values(b * BLOCK / SR)
        lines.append(" ".join(f"{v[k]:.5f}" for k in CONTROLS))
    lines.append(f"hits {len(seq)}")
    for t, note in seq:
        lines.append(f"{int(round(t * SR / BLOCK))} {55 * 2 ** (4 * note):.3f}")   # 4 octaves from 55 Hz: the engine's zones
    raw = subprocess.run([str(exe)], input="\n".join(lines).encode(), capture_output=True, check=True).stdout
    n = len(raw) // 4
    xs = struct.unpack(f"{n}f", raw)
    peak = max(1e-9, max(abs(x) for x in xs))
    g = 0.89 / peak
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * g)) * 32767)) for x in xs))
    print(f"{n / SR:.1f} s, peak {peak:.3f} (normalised)")


if __name__ == "__main__":
    main()
