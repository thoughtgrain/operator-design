#!/usr/bin/env python3
"""iris preview: one score drives the picture and the sound.

The picture is iris's real display() (operators-xy machines/iris/display.cpp) run on the host over the score
(display_host.cpp, against host_sdk/, a stand-in for the SDK's draw API), its nodes drawn with the authored geometry in
panel.svg.fragment. The sound is iris's real engine.cpp run block by block over the same score (../audio/render.cpp),
with a stand-in envelope. Audio: simulated (engine code run on a computer, not a device recording).

    python3 make_preview.py            -> iris-preview.mp4 (480 x 220) and iris-preview-2x.mp4 (960 x 440, nearest)
Needs g++, node with Playwright, ffmpeg. Copyright (c) 2026 briannhinton. MIT."""
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MACHINE = Path('/home/user/operators-xy/machines/iris')     # the machine's own repository checkout
FPS, SR, BLOCK = 30, 44100, 64
DEFAULTS = [0.3333, 0.25, 0.0, 0.7, 0.0, 0.0]
NAMES = ['morph', 'overlap', 'spread', 'tone', 'skew', 'phase']
PAL = ['#AFAFAF', '#CDCDCD', '#646464', '#7D7D7D', '#969696']
PHRASE = [110.0, 130.81, 146.83, 164.81, 196.0, 164.81, 146.83, 130.81]   # A minor pentatonic, up and back
LABEL = 'Audio: simulated (engine code run on a computer, not a device recording)'


def build_score():
    """Segments of (seconds, knob function, notes on/off, page). Returns per-time lookups."""
    segs, notes, t = [], [], 0.0

    def seg(dur, knobs, page, play, period=0.4, hold=0.32, step=0):
        nonlocal t
        segs.append((t, t + dur, knobs, page))
        if play:
            k, s = step, t
            while s + hold <= t + dur + 1e-9:
                notes.append((s, s + hold, PHRASE[k % len(PHRASE)])); k += 1; s += period
        t += dur
    still = lambda u: list(DEFAULTS)
    seg(1.5, still, 1, False)                                       # rest: nothing moves
    seg(3.0, still, 1, True, period=0.75, hold=0.55)               # notes held: the line travels and brightens
    seg(0.6, still, 1, False)                                       # hold ended: it settles

    def turn(c):
        d = DEFAULTS[c]

        def knobs(u):                                               # default -> 0 -> 100 -> default, eased
            v = list(DEFAULTS)
            if u < 0.15: x = d + (0 - d) * smooth(u / 0.15)
            elif u < 0.6: x = smooth((u - 0.15) / 0.45)
            elif u < 0.85: x = 1 + (d - 1) * smooth((u - 0.6) / 0.25)
            else: x = d
            v[c] = x
            return v
        return knobs
    for c in range(4):
        seg(3.2, turn(c), 1, True, step=c * 2)
    seg(0.7, still, 2, False)                                       # page press: page 2
    for c in (4, 5):
        seg(3.2, turn(c), 2, True, step=c * 2)
    seg(0.7, still, 1, False)                                       # page press back
    seg(1.5, still, 1, False)                                       # rest again
    return segs, notes, t


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def at(segs, t):
    for a, b, knobs, page in segs:
        if a <= t < b:
            return knobs((t - a) / (b - a)), page
    return list(DEFAULTS), 1


def header(vals, page):
    steps = ['#000000', '#323232', '#4B4B4B', '#646464', '#7D7D7D', '#969696', '#AFAFAF', '#CDCDCD']
    rows = [[0, 1, 2, 3], [4, 5, None, None]] if page == 1 else [[4, 5, 2, 3], [0, 1, None, None]]
    pct = lambda v: f'{round(v * 100)}%'
    g = ['<rect x="0" y="0" width="480" height="38" fill="#000000"/>']
    g += [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{c}"/>' for i, c in enumerate(steps)]
    for i, k in enumerate(rows[0]):
        ink = '#CBCBCB' if i < 2 else '#000000'
        g.append(f'<text x="{120 * i + 5}" y="10" fill="{ink}" font-family="UniversNextPro-Light, Univers, Helvetica, Arial" font-size="10px">{NAMES[k]}</text>')
        g.append(f'<text x="{120 * i + 65}" y="17.44" fill="{ink}" font-family="UniversNextPro-Light, Univers, Helvetica, Arial" font-size="20px">{pct(vals[k])}</text>')
    for i, k in enumerate(rows[1]):
        if k is None: continue
        g.append(f'<text x="{120 * i + 5}" y="33" fill="#5A5A5A" font-family="UniversNextPro-Light, Univers, Helvetica, Arial" font-size="10px">{NAMES[k]}</text>')
        g.append(f'<text x="{120 * i + 65}" y="33" fill="#707070" font-family="UniversNextPro-Light, Univers, Helvetica, Arial" font-size="13px">{pct(vals[k])}</text>')
    return '\n'.join(g)


def main():
    work = Path(tempfile.mkdtemp(prefix='iris-preview-'))
    segs, notes, total = build_score()
    nf = int(round(total * FPS))

    # the picture: real display() over the score
    exe = work / 'display_host'
    subprocess.run(['g++', '-std=c++11', '-O2', f'-I{HERE / "host_sdk"}', f'-I{MACHINE}', str(HERE / 'display_host.cpp'), '-o', str(exe)], check=True)
    rows, knob_rows = [f'frames {nf}'], []
    for f in range(nf):
        t = f / FPS
        v, page = at(segs, t)
        held = any(a <= t < b for a, b, _ in notes)
        knob_rows.append((v, page))
        rows.append(' '.join(f'{x:.5f}' for x in v) + f' {1 if held else 0}')
    dump = subprocess.run([str(exe)], input='\n'.join(rows) + '\n', capture_output=True, text=True, check=True).stdout.splitlines()

    frag = (MACHINE / 'panel.svg.fragment').read_text()
    geo = {int(m.group(1)): m.group(2) for m in re.finditer(r'id="iris_node_(\d+)" transform="[^"]*" d="([^"]*)"', frag)}
    static = re.findall(r'<path transform="(matrix\([^)]*\))" d="([^"]*)" fill="([^"]*)" stroke="none"/>', frag)
    svgdir = work / 'svg'; svgdir.mkdir()
    keys = []
    for f, line in enumerate(dump):
        a = list(map(int, line.split()))
        keys.append(a[-1])
        nodes = [a[7 * n: 7 * n + 7] for n in range(140)]
        pts = a[980:-1]
        o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
             '<rect width="480" height="220" fill="#000000"/>', header(*knob_rows[f])]
        for n in range(12, 140):
            x, y, s, p, c, si, on = nodes[n]
            if not on: continue
            k = s / 1024; cc, ss = c / 1024 * k, si / 1024 * k
            o.append(f'<path transform="matrix({cc:.5f} {ss:.5f} {-ss:.5f} {cc:.5f} {x / 1024:.3f} {y / 1024:.3f})" d="{geo[n]}" fill="{PAL[p]}"/>')
        for tr, d, fill in static:
            o.append(f'<path transform="{tr}" d="{d}" fill="{fill}"/>')
        for q in range(4):
            x, y, s, p, c, si, on = nodes[q]
            seg = pts[128 * q: 128 * q + 128]
            d = 'M ' + ' L '.join(f'{seg[2 * k] / 1024:.3f} {seg[2 * k + 1] / 1024:.3f}' for k in range(64)) + ' Z'
            o.append(f'<path transform="translate({x / 1024:.3f} {y / 1024:.3f})" d="{d}" fill="{PAL[p]}"/>')
        o.append('</svg>')
        (svgdir / f'{f:05d}.svg').write_text('\n'.join(o))
    pngdir = work / 'png'
    subprocess.run(['node', str(HERE / 'render_frames.js'), str(svgdir), str(pngdir)], check=True)

    # the sound: real engine.cpp over the same score
    rexe = work / 'render'
    subprocess.run(['g++', '-std=c++11', '-O2', f'-I{HERE / "host_sdk"}', f'-I{MACHINE}', str(HERE.parent / 'audio' / 'render.cpp'), '-o', str(rexe)], check=True)
    nb = int(math.ceil((total + 0.5) * SR / BLOCK))
    lines = [f'blocks {nb}']
    for b in range(nb):
        v, _ = at(segs, b * BLOCK / SR)
        lines.append(' '.join(f'{x:.5f}' for x in v))
    lines.append(f'notes {len(notes)}')
    lines += [f'{int(a * SR / BLOCK)} {int(b * SR / BLOCK)} {hz}' for a, b, hz in notes]
    raw = subprocess.run([str(rexe)], input=('\n'.join(lines) + '\n').encode(), capture_output=True, check=True).stdout
    import array
    s = array.array('f'); s.frombytes(raw)
    peak = max(abs(x) for x in s) or 1.0
    gain = 10 ** (-3 / 20) / peak                                   # peaks at -3 dBFS
    pcm = array.array('h', (int(max(-1, min(1, x * gain)) * 32767) for x in s))
    import wave
    with wave.open(str(HERE.parent / 'audio' / 'iris-preview.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

    out = HERE / 'iris-preview.mp4'
    common = ['-metadata', f'comment={LABEL}', '-metadata', 'title=iris, rainbow screen preview',
              '-c:a', 'aac', '-b:a', '160k', '-shortest']
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(pngdir / '%05d.png'),
                    '-i', str(HERE.parent / 'audio' / 'iris-preview.wav'), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                    '-pix_fmt', 'yuv420p'] + common + [str(out)], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(out), '-vf', 'scale=960:440:flags=neighbor',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                    '-metadata', f'comment={LABEL}', str(HERE / 'iris-preview-2x.mp4')], check=True)
    for f in (0, 30, 120, 165):                                     # stills for the notes file
        shutil.copy(pngdir / f'{f:05d}.png', HERE / f'still-{f:05d}.png')
    rest_rewrites = sum(1 for i in range(1, 45) if keys[i] != keys[i - 1])
    print(f'{nf} frames, {total:.1f} s, {len(notes)} notes; mix rewrites during the opening rest: {rest_rewrites}')
    shutil.rmtree(work)


if __name__ == '__main__':
    main()
