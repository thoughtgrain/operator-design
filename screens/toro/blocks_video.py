"""Render toro-blocks.mp4: notes, then each control swept 0 → 100 → default. python3 ink_video.py <tmpdir>, then ffmpeg (see ink/README.md)."""
import sys, subprocess, math
sys.path.insert(0, '/home/claude/operators/screens/toro')
import gen_blocks as G, gen_frames as g
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
out = Path(sys.argv[1]); FPS = 30
D = dict(g.DEFAULTS)
timeline = []   # (values, seconds since last note or None, key)
def hold(sec, v=None, notes=()):
    v = v or D
    n = int(sec * FPS)
    for k in range(n):
        t = k / FPS
        last = max([s for s in notes if s <= t], default=None)
        timeline.append((dict(v), None if last is None else t - last, int(round(last / 0.45)) % 8 if last is not None else 0))
def sweep(name, lo=0.0, hi=1.0, up=1.4, stay=0.5, back=0.9, notes_at_top=False):
    d0 = D[name]
    for seg, a, b in ((up, d0, lo), (up, lo, hi)):
        n = int(seg * FPS / 2) if a == d0 else int(seg * FPS)
        for k in range(n):
            u = k / max(1, n - 1); u = u * u * (3 - 2 * u)
            timeline.append((dict(D, **{name: a + (b - a) * u}), None, 0))
    hold(stay, dict(D, **{name: hi}), notes=(0.0,) if notes_at_top else ())
    n = int(back * FPS)
    for k in range(n):
        u = k / max(1, n - 1); u = u * u * (3 - 2 * u)
        timeline.append((dict(D, **{name: hi + (d0 - hi) * u}), None, 0))
hold(1.0)
hold(3.2, notes=(0.0, 0.45, 0.9, 1.35, 1.8, 2.25))
sweep('drive', stay=1.6, notes_at_top=True)
hold(1.6, dict(D, drive=0.6), notes=(0.2, 0.8))
for name in ('spread', 'cutoff', 'fold', 'res', 'shape', 'noise', 'aphx'):
    sweep(name)
hold(1.6, dict(D, drive=0.5, fold=0.6, noise=0.5), notes=(0.0, 0.55, 1.1))
hold(0.6)
print(len(timeline), 'frames')
def render(i):
    v, t, key = timeline[i]
    svg = out / f'f{i:04d}.svg'
    svg.write_text(G.frame_svg(v, t, key))
    subprocess.run(['rsvg-convert', '-w', '480', '-h', '220', str(svg), '-o', str(out / f'f{i:04d}.png')], check=True)
    svg.unlink()
with ThreadPoolExecutor(8) as ex:
    list(ex.map(render, range(len(timeline))))
