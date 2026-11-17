"""iris v4 sketch: the surface the sound acts on, seen close and low.

Four wave trains (sine, triangle, square, saw) cross one water surface, each
arriving from its own direction. The surface is a heightfield in world space,
sliced into rows of constant depth and projected through one pinhole camera.
Rows are drawn far to near as black masses with a rim along their top edge
(edge-lit silhouette); nearer rows hide farther ones.

  morph   centre of the mixing window -> which train dominates
  overlap window width                -> how much the other trains cut in
  spread  detune                      -> trains' wavelengths drift apart (moire)
  tone    low-pass                    -> harmonics kept -> crest sharpness
  skew    breakpoint                  -> crests lean (sine/tri/square), saw unchanged
  phase   per-band offset             -> trains slide against each other

Usage: python3 sketch.py [out.svg]
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = dict(morph=0.3333, overlap=0.25, spread=0.0, tone=0.7, skew=0.0, phase=0.0)

# ---- sound -> surface --------------------------------------------------------
def weights(morph, overlap):
    c = morph * 3.0
    width = 1.0 + 2.2 * overlap
    w = [max(0.0, 1.0 - abs(i - c) / width) ** 2 for i in range(4)]
    s = sum(w) or 1.0
    return [v / s for v in w]


def harmonics(tone):
    return 2 + int(round(tone * 12))          # 0% -> nearly a sine swell, 100% -> knife crests


def skewed(ph, skew, band):
    """Phase breakpoint: maps [0,1) so the first half of the cycle takes `b` of it."""
    if band == 3:
        return ph
    b = 0.5 - 0.45 * skew
    return 0.5 * ph / b if ph < b else 0.5 + 0.5 * (ph - b) / (1 - b)


def wave(band, ph, n):
    """Band-limited waveform, value in about [-1, 1]; ph in cycles."""
    x = 2 * math.pi * ph
    if band == 0:
        return math.sin(x)
    out = 0.0
    for k in range(1, n + 1):
        g = math.cos(math.pi * k / (2 * (n + 1))) ** 2           # soft roll-off, no ringing
        if band == 1 and k % 2:
            out += g * (8 / math.pi ** 2) * ((-1) ** ((k - 1) // 2)) * math.sin(k * x) / k ** 2
        elif band == 2 and k % 2:
            out += g * (4 / math.pi) * math.sin(k * x) / k * 0.8
        elif band == 3:
            out += g * (2 / math.pi) * ((-1) ** (k + 1)) * math.sin(k * x) / k * 0.8
    return out


# arrival direction of each train (degrees in the ground plane; 90 = straight at the camera)
DIRS = [104.0, 24.0, 63.0, 146.0]
LAMBDA = 1.25
AMP = 0.16


def height(x, z, p):
    w = weights(p["morph"], p["overlap"])
    n = harmonics(p["tone"])
    h = 0.0
    for i in range(4):
        if w[i] < 1e-4:
            continue
        a = math.radians(DIRS[i])
        cents = (i - 1.5) / 1.5 * 50 * p["spread"]
        lam = LAMBDA / (2 ** (cents / 1200 * 14))    # visual exaggeration of the detune
        ph = (x * math.cos(a) + z * math.sin(a)) / lam + i * 0.25 * p["phase"]
        ph -= math.floor(ph)
        h += w[i] * wave(i, skewed(ph, p["skew"], i), n)
    return AMP * h


# ---- camera ------------------------------------------------------------------
CAM_H = 0.5
HORIZON = 54.0
F = 330.0
CX = 240.0


def proj(x, y, z):
    return CX + F * x / z, HORIZON + F * (CAM_H - y) / z


def rows():
    """Depths for the slices: screen gap grows from ~4.5 px far to ~11 px near."""
    zs, z = [], 1.4
    while z < 7.0:
        zs.append(z)
        base = HORIZON + F * CAM_H / z
        gap = 5.0 + 9.0 * max(0.0, (base - 70) / 150)
        z = F * CAM_H / ((base - gap) - HORIZON)
    return zs


RIM = ["#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF"]


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def ribbon(run, w):
    """A closed ribbon under a run of rim points: the lit lip of a crest."""
    top = [(x, y - 0.2) for x, y in run]
    bot = [(x, y + w) for x, y in reversed(run)]
    pts = top + bot
    return "M " + " L ".join(f"{fmt(a)} {fmt(b)}" for a, b in pts) + " Z"


def svg(p):
    zs = rows()
    nz = len(zs)
    npts = 60
    sxs = [-8 + 496 * s / (npts - 1) for s in range(npts)]
    profiles = []
    for z in zs:
        prof = []
        for sx in sxs:
            x = (sx - CX) * z / F
            h = height(x, z, p)
            prof.append((proj(x, h, z), h))
        profiles.append(prof)
    # envelope of everything nearer than row k (screen y; smaller = higher)
    env = [[999.0] * npts for _ in range(nz + 1)]
    for k in range(nz):
        for s in range(npts):
            env[k + 1][s] = min(env[k][s], profiles[k][s][0][1])
    out = []
    for k in reversed(range(nz)):                      # far to near
        t = 1 - k / max(1, nz - 1)                     # 1 near, 0 far
        prof = profiles[k]
        pts = [q for q, _ in prof] + [(488, 226), (-8, 226)]
        d = "M " + " L ".join(f"{fmt(a)} {fmt(b)}" for a, b in pts) + " Z"
        if k == 0:
            out.append(f'  <path d="{d}" fill="#000000" stroke="#CDCDCD" stroke-width="2.2"/>')
            continue
        out.append(f'  <path d="{d}" fill="#000000" stroke="#323232" stroke-width="1"/>')
        # lit lips: crest points above the threshold that nothing nearer hides
        thr = 0.22 * AMP
        run = []
        runs = []
        for s in range(npts):
            (x, y), h = prof[s]
            vis = y < env[k][s] - 1.0
            if h > thr and vis:
                run.append((x, y))
            else:
                if len(run) >= 2:
                    runs.append(run)
                run = []
        if len(run) >= 2:
            runs.append(run)
        w = 1.0 if t < 0.4 else 1.3 if t < 0.8 else 1.6
        for r in runs:
            peak = max(prof[sxs.index(min(sxs, key=lambda v: abs(v - x)))][1] for x, _ in r)
            lvl = min(len(RIM) - 1, int(t * 3 + (peak / AMP) * 2.2))
            out.append(f'  <path d="{ribbon(r[:31], w)}" fill="{RIM[lvl]}" stroke="none"/>')
    return "\n".join(out)


HEADER = """  <g id="preview_canvas">
    <rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/>
  </g>
  <g id="preview_header">
{steps}
{texts}
  </g>"""


def header():
    greys = ["#000000", "#323232", "#4B4B4B", "#646464", "#7D7D7D", "#969696", "#AFAFAF", "#CDCDCD"]
    steps = "\n".join(f'    <rect x="{60*i}" y="0" width="60" height="20" fill="{g}" stroke="none"/>' for i, g in enumerate(greys))
    t1 = ["morph", "overlap", "spread", "tone"]
    v1 = ["33%", "25%", "0%", "70%"]
    t2 = ["skew", "phase"]
    v2 = ["0%", "0%"]
    texts = []
    for i in range(4):
        dark = i < 2
        c = "#CBCBCB" if dark else "#000000"
        texts.append(f'    <text transform="matrix(1 0 0 1 {5+120*i} 10)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t1[i]}</text>')
        texts.append(f'    <text transform="matrix(1 0 0 1 {65+120*i} 17.44)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{v1[i]}</text>')
    for i in range(2):
        texts.append(f'    <text transform="matrix(1 0 0 1 {5+120*i} 32)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t2[i]}</text>')
        texts.append(f'    <text transform="matrix(1 0 0 1 {65+120*i} 33)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">{v2[i]}</text>')
    return HEADER.format(steps=steps, texts="\n".join(texts))


def frame(p):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">
  <!-- iris v4 rest frame: one water surface, four crossing wave trains, edge-lit. Generated by sketch.py. -->
{header()}
  <path id="iris_palette_0" d="M 700 300 L 704 300 L 704 304 Z" fill="#CDCDCD" stroke="#CDCDCD" stroke-width="2"/>
{svg(p)}
</svg>
"""


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "rest.svg"
    out.write_text(frame(P))
    print(out, len(rows()), "rows")
