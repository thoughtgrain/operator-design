#!/usr/bin/env python3
"""Tide · frames and motion study for the picked subject (pass 02, v4: foam at water level).

    python3 screens/tide/frames/build.py            # rest + per-control frames (svg + png)
    python3 screens/tide/frames/build.py --motion   # also motion.gif, motion-sheet.png, budget numbers
    python3 screens/tide/frames/build.py --budget   # only the redraw simulation, printed

Everything is one 3D scene (x right, y away from the viewer, z up) through one camera:
a raft of hemispherical bubbles floating on the pool, ripple lines (swell fronts) on the
water under it. Eight "voiced" bubbles are the eight resonators of a voice, sized by
partial (a bubble rings at a pitch set by its size); a handful of small "spent" bubbles
are foam that has finished ringing, and how many linger follows depth.

Frames are authored the way the fragment will be: every moving part is a bound node
(`tide_node_<i>`) whose geometry is baked at its frame pose, translate-only transforms,
palette entries parked off screen, lines as closed ribbons, <= 64 points per path.
The motion study runs the same node model at 60 fps and counts changed nodes per frame.
"""
from __future__ import annotations

import importlib.util
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKETCH = HERE.parent / "passes" / "02-subject" / "sketch.py"
_spec = importlib.util.spec_from_file_location("tide_sketch", SKETCH)
sk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sk)

Camera, circle3, f2, dedupe = sk.Camera, sk.circle3, sk.f2, sk.dedupe
sub, add, mul, dot, norm, cross = sk.sub, sk.add, sk.mul, sk.dot, sk.norm, sk.cross
W, H, TOP = sk.W, sk.H, sk.TOP
G = [sk.G0, sk.G1, sk.G2, sk.G3, sk.G4, sk.G5, sk.G6, sk.G7]
FONT = sk.FONT
HAIR, LINE, SUBJ = sk.HAIR, sk.LINE, sk.SUBJ
PREFIX = "tide"

# ---------------------------------------------------------------- the definition's mappings
DEFAULTS = {"swell": 0.6, "depth": 0.5, "salt": 0.0, "drift": 0.0}


def swell_s(p): return 0.25 * 32 ** p          # wave period, s
def depth_s(p): return 0.05 * 100 ** p         # resonator T60, s


def fmt_dur(s):
    if s < 0.1:
        return f"{round(s * 1000)}ms"
    if s < 1.0 and abs(round(s, 2) - round(s, 1)) > 1e-9:
        return f"{s:.2f}s"
    return f"{s:.1f}s"


def header_values(c):
    return [("swell", fmt_dur(swell_s(c["swell"]))), ("depth", fmt_dur(depth_s(c["depth"]))),
            ("salt", f"{round(100 * c['salt'])}"), ("drift", f"{round(100 * c['drift'])}")]


# ---------------------------------------------------------------- scene
_ALPHA = math.radians(11.5)             # the camera looks down 11.5 degrees: low, at the water's level
_DIST = 19.0                             # long lens, far back: the pool's depth compresses, so fronts fill the body
CAM = Camera(eye=(0.0, 0.55 - _DIST * math.cos(_ALPHA), _DIST * math.sin(_ALPHA)), target=(0.0, 0.55, 0.0), f=1950, at=(240, 150))
LIGHT = norm((-0.5, 1.0, 0.42))        # low sun behind the raft, up and to the left (points toward the light)
HORIZON_Y = CAM.p((0, 4000, 0))[1]
R1 = 0.68                                # the fundamental's radius, world units
RAFT_C = (0.15, 0.55)                    # raft centre on the water (x, y)


def r_partial(k):
    """Radius by partial at salt 0: a bubble's ring is set by its size, drawn as r ~ k^-0.8
    (true Minnaert would be k^-1; 0.8 keeps the 8th partial above the 3-4 px floor)."""
    return R1 * k ** -0.8


def salt_scale(k, salt):
    """Salt stretches partial k from k to k^(1+0.3 salt). Minnaert: radius ~ 1/frequency, so the
    bubble shrinks by k^(-0.3 salt). The fundamental never changes."""
    return k ** (-0.3 * salt)


def relax(bubbles, targets, iters=600):
    """Pack the raft: each bubble pulled to its target, pushed out of its neighbours until they touch."""
    for _ in range(iters):
        for b, t in zip(bubbles, targets):
            b["x"] += (t[0] - b["x"]) * 0.02
            b["y"] += (t[1] - b["y"]) * 0.02
        for i in range(len(bubbles)):
            for j in range(i + 1, len(bubbles)):
                a, b = bubbles[i], bubbles[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                d = math.hypot(dx, dy) or 1e-6
                need = (a["r"] + b["r"]) * 1.01
                if d < need:
                    push = (need - d) / 2
                    wa = b["r"] / (a["r"] + b["r"])
                    a["x"] -= dx / d * push * 2 * wa
                    a["y"] -= dy / d * push * 2 * wa
                    b["x"] += dx / d * push * 2 * (1 - wa)
                    b["y"] += dy / d * push * 2 * (1 - wa)


def build_raft():
    # voiced bubbles: hand-composed targets (world), then packed
    tgt = {1: (0.30, 0.75), 2: (-0.85, 0.70), 3: (1.20, 0.55), 4: (-0.20, -0.05),
           5: (0.75, 0.00), 6: (-1.55, 0.35), 7: (1.85, 0.20), 8: (-0.75, 0.05)}
    voiced = [{"k": k, "r": r_partial(k), "x": tgt[k][0], "y": tgt[k][1], "kind": "voiced"} for k in range(1, 9)]
    relax(voiced, [tgt[b["k"]] for b in voiced])
    # spent foam: small bubbles packed against the raft's back and ends, in the order they linger
    rnd = random.Random(7)
    spent = []
    allb = list(voiced)
    N = 30
    while len(spent) < N:
        best, bestscore = None, -1e9
        for _ in range(2500):
            host = rnd.choice(allb)
            ang = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0.09, 0.16)
            gap = rnd.uniform(1.03, 1.5)
            x = host["x"] + (host["r"] + r) * gap * math.cos(ang)
            y = host["y"] + (host["r"] + r) * gap * math.sin(ang)
            if any(math.hypot(x - b["x"], y - b["y"]) < (r + b["r"]) * 1.02 for b in allb):
                continue
            if not (-2.2 < x < 2.3 and -1.1 < y < 2.2):
                continue
            # touch something, stay near the raft
            near = min(math.hypot(x - b["x"], y - b["y"]) - (r + b["r"]) for b in allb)
            # and stay in sight: its crown must not fall inside a nearer dome
            cs = CAM.p((x, y, r))
            dz = CAM.depth((x, y, 0))
            hidden = False
            for b in allb:
                bd = CAM.depth((b["x"], b["y"], 0))
                if bd < dz + 0.05:
                    bc = CAM.p((b["x"], b["y"], 0))
                    br = CAM.f * b["r"] / bd
                    if math.dist(cs, bc) < br + 2 and cs[1] < bc[1] + 1:
                        hidden = True
            # and don't crowd at 1:1: its drawn dome may tuck into a neighbour's only a little
            mine = (CAM.p((x, y, 0)), CAM.f * r / dz)
            for b in allb:
                bd = CAM.depth((b["x"], b["y"], 0))
                if math.dist(mine[0], CAM.p((b["x"], b["y"], 0))) < 0.6 * (mine[1] + CAM.f * b["r"] / bd):
                    hidden = True
                    break
            if hidden:
                continue
            # spread the lingering foam along the raft instead of piling it in one place
            far = min([math.hypot(x - b["x"], y - b["y"]) for b in spent] + [1.2])
            score = -near * 8 + 1.4 * far - 0.35 * y + rnd.uniform(0, 0.3)
            if score > bestscore:
                best, bestscore = (x, y, r), score
        if best is None:
            raise SystemExit(f"spent foam: only {len(spent)} fit")
        x, y, r = best
        b = {"k": 0, "r": r, "x": x, "y": y, "z": 0.0, "kind": "spent", "host": None}
        spent.append(b)
        allb.append(b)
    # foam that lasts piles up: small bubbles stacked on the backs of the big ones, peeking over the raft
    stacked = []
    tries = 0
    while len(stacked) < 0 and tries < 4000:
        tries += 1
        host = rnd.choices(voiced[:5], weights=[5, 3, 2, 1.2, 1])[0]
        r = rnd.uniform(0.09, 0.15)
        az = math.radians(rnd.choice([rnd.uniform(15, 70), rnd.uniform(110, 165)]))           # round the back
        el = math.radians(rnd.uniform(15, 45))
        d = (host["r"] + r) * 1.01
        P = (host["x"] + d * math.cos(el) * math.cos(az), host["y"] + d * math.cos(el) * math.sin(az), d * math.sin(el))
        if any(math.dist(P, (b["x"], b["y"], b.get("z", 0.0))) < (r + b["r"]) * 1.03 for b in allb + stacked if b is not host):
            continue
        # how much of it shows over the nearer domes (sample its outline)
        ring = CAM.ps(sphere_contour(P, r, 24))
        dP = CAM.depth(P)
        vis = 0
        for q in ring:
            cover = False
            for b in allb + stacked:
                bz = b.get("z", 0.0)
                if CAM.depth((b["x"], b["y"], bz)) < dP:
                    bc = CAM.p((b["x"], b["y"], bz))
                    br = CAM.f * b["r"] / CAM.depth((b["x"], b["y"], bz))
                    if math.dist(q, bc) < br and (bz > 0 or q[1] < bc[1]):
                        cover = True
                        break
            vis += not cover
        if not 0.3 <= vis / len(ring) <= 0.65:
            continue
        # off the crown (two on top read as ears), and clear of every lit edge's light
        hc, hr = CAM.p((host["x"], host["y"], 0)), CAM.f * host["r"] / CAM.depth((host["x"], host["y"], 0))
        if abs(CAM.p(P)[0] - hc[0]) < 0.6 * hr:
            continue
        if any(CAM.p(P)[1] < bc[1] - 0.8 * br for bc, br in [(CAM.p((b["x"], b["y"], 0)), CAM.f * b["r"] / CAM.depth((b["x"], b["y"], 0))) for b in voiced]
               if abs(CAM.p(P)[0] - bc[0]) < br):
            continue
        mine = CAM.p(P), CAM.f * r / dP
        if any(math.dist(mine[0], CAM.p((b["x"], b["y"], b["z"]))) < 0.75 * (mine[1] + CAM.f * b["r"] / CAM.depth((b["x"], b["y"], b["z"])))
               for b in stacked):
            continue
        stacked.append({"k": 0, "r": r, "x": P[0], "y": P[1], "z": P[2], "kind": "spent", "host": host})
    # the order they linger in as depth rises: floating and stacked foam alternate
    order = []
    fl, st = list(spent), list(stacked)
    while fl or st:
        if fl:
            order.append(fl.pop(0))
        if st and (len(order) % 3 != 1 or not fl):
            order.append(st.pop(0))
    for i, b in enumerate(order):
        b["order"] = i
    spent = order
    for i, b in enumerate(voiced + spent):
        b["seed"] = random.Random(100 + i).uniform(0, 2 * math.pi)
        b.setdefault("z", 0.0)
    return voiced, spent


# ---------------------------------------------------------------- per-bubble geometry (authored at rest pose)
def sphere_contour(c, r, n=72):
    """The sphere's outline as the camera sees it: its contour circle, as 3D points with their angle."""
    e = sub(CAM.eye, c)
    L2 = dot(e, e)
    cc = add(c, mul(e, r * r / L2))
    rho = r * math.sqrt(1 - r * r / L2)
    w = norm(e)
    u = norm(cross(w, (0, 0, 1)))
    v = cross(w, u)                     # roughly 'up' on screen
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        out.append(add(cc, add(mul(u, rho * math.cos(a)), mul(v, rho * math.sin(a)))))
    return out


def shadowed(P, me):
    """True when the ray from P toward the light hits another bubble (all hemispheres sit on z=0)."""
    for b in VOICED:
        if b is me:
            continue
        c = (b["x"], b["y"], 0.0)
        oc = sub(P, c)
        bq = dot(oc, LIGHT)
        cq = dot(oc, oc) - b["r"] ** 2
        disc = bq * bq - cq
        if disc > 0:
            t = -bq - math.sqrt(disc)
            if t > 1e-4 or (-bq + math.sqrt(disc)) > 1e-4 and cq < 0:
                return True
    return False


VOICED, SPENT = build_raft()
BUBBLES = VOICED + SPENT


def stacked_parts(b):
    """A spent bubble resting on a big one's back: a whole small sphere, drawn hollow (black body,
    mid-grey outline); the host's dome, nearer, hides its lower half."""
    P = (b["x"], b["y"], b["z"])
    ring = CAM.ps(sphere_contour(P, b["r"], 40))
    centre = CAM.p(P)
    return {"centre": centre, "dome": dedupe(ring, 0.3), "rp": CAM.f * b["r"] / CAM.depth(P)}


def bubble_parts(b):
    """Dome (black body), waterline (hairline, front half), lit edge (tapered ribbon along the back
    edge, lit by the real 3D light with neighbours' shadows), inner reflection (big bubbles)."""
    c = (b["x"], b["y"], 0.0)
    r = b["r"]
    ring = sphere_contour(c, r, 96)
    # walk the contour above the water, from one waterline crossing over the top to the other
    n = len(ring)
    above = [P[2] >= 0 for P in ring]
    start = next(i for i in range(n) if not above[i - 1] and above[i])
    arc3 = []
    i = start
    # crossing in
    A, B = ring[i - 1], ring[i]
    t = A[2] / (A[2] - B[2])
    arc3.append(add(A, mul(sub(B, A), t)))
    while above[i % n]:
        arc3.append(ring[i % n])
        i += 1
    A, B = ring[(i - 1) % n], ring[i % n]
    t = A[2] / (A[2] - B[2])
    arc3.append(add(A, mul(sub(B, A), t)))
    # the waterline's front half between the two crossings
    ang = lambda P: math.atan2(P[1] - c[1], P[0] - c[0])
    a0, a1 = ang(arc3[-1]), ang(arc3[0])
    # go from the arc's end round the front (y < c.y, angles near -pi/2) back to its start
    if a0 > 0:
        a0 -= 2 * math.pi if a0 > math.pi / 2 else 0
    span = (a1 - a0) % (2 * math.pi)
    front_is_neg = math.sin(a0 + span / 2) < 0
    if not front_is_neg:
        span -= 2 * math.pi
    wl3 = [(c[0] + r * math.cos(a0 + span * j / 24), c[1] + r * math.sin(a0 + span * j / 24), 0.0) for j in range(25)]
    arc2 = CAM.ps(arc3)
    wl2 = CAM.ps(wl3)
    # resample the dome outline to <= 60 points
    step = max(1, math.ceil(len(arc2) / 36))
    dome = dedupe(arc2[::step] + [arc2[-1]] + wl2[1:-1], 0.3)
    centre = CAM.p(c)
    parts = {"centre": centre, "dome": dome, "wl": wl2}
    rp = math.dist(centre, arc2[len(arc2) // 2])
    parts["rp"] = rp
    if b["kind"] == "spent":
        return parts
    # rim light: back-lit film, brightest where the outline's normal faces the light; neighbours shade it
    I = []
    for P in arc3[1:-1]:
        nn = norm(sub(P, c))
        lit = max(0.0, dot(nn, LIGHT))
        # the water's meniscus darkens the film's foot: the rim light lifts off the waterline
        zz = max(0.0, min(1.0, P[2] / (0.5 * r)))
        fres = zz * zz * (3 - 2 * zz)
        I.append(0.0 if shadowed(P, b) else lit ** 1.6 * fres)
    pts3 = arc3[1:-1]
    thr = 0.28
    runs, cur = [], []
    for P, v in zip(pts3, I):
        if v > thr:
            cur.append((P, v))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    if not runs:            # fully shadowed: keep its brightest sliver so the bubble can still ring
        best = max(range(len(I)), key=lambda j: max(0, dot(norm(sub(pts3[j], c)), LIGHT)))
        runs = [[(pts3[j], 0.3) for j in range(max(0, best - 4), min(len(pts3), best + 5))]]
    run = max(runs, key=lambda rr: sum(v for _, v in rr))
    peak = max(v for _, v in run)
    wmax = 2.3 if b["k"] == 1 else (1.8 if b["k"] <= 3 else 1.9)   # small ones authored heavier: salt shrinks them
    # resample the run to 26 points along its length
    P2 = [CAM.p(P) for P, _ in run]
    V = [v for _, v in run]
    if len(P2) < 2:
        P2 = [P2[0], (P2[0][0] + 1, P2[0][1])]
        V = V * 2
    L = [0.0]
    for a_, b_ in zip(P2, P2[1:]):
        L.append(L[-1] + math.dist(a_, b_))
    m = 26
    outer, inner = [], []
    for j in range(m):
        s = L[-1] * j / (m - 1)
        q = max(0, min(len(L) - 2, next((q for q in range(len(L) - 1) if L[q + 1] >= s), len(L) - 2)))
        f = 0 if L[q + 1] == L[q] else (s - L[q]) / (L[q + 1] - L[q])
        x = P2[q][0] + (P2[q + 1][0] - P2[q][0]) * f
        y = P2[q][1] + (P2[q + 1][1] - P2[q][1]) * f
        v = V[q] + (V[q + 1] - V[q]) * f
        w = max(0.55, wmax * (v / peak) ** 0.7)
        dx, dy = centre[0] - x, centre[1] - y
        dl = math.hypot(dx, dy) or 1
        outer.append((x, y))
        inner.append((x + dx / dl * w, y + dy / dl * w))
    parts["edge"] = dedupe(outer + inner[::-1], 0.15)
    parts["edge_mid"] = outer[m // 2]
    # inner reflection: light through the dome lands on the inside of its front film, opposite the lit edge
    if rp > 20:
        mx, my = outer[m // 2]
        th = math.atan2(my - centre[1], mx - centre[0]) + math.pi
        pts = [(centre[0] + 0.68 * rp * math.cos(th + math.radians(a)), centre[1] + 0.62 * rp * math.sin(th + math.radians(a)))
               for a in [-22 + 44 * j / 10 for j in range(11)]]
        pts = [p for p in pts if p[1] < centre[1] - 2]
        if len(pts) >= 3:
            parts["refl"] = pts
    return parts


for _b in BUBBLES:
    _b["parts"] = stacked_parts(_b) if _b.get("host") else bubble_parts(_b)


def ribbon(pts, w):
    """Open polyline -> closed ribbon point list (the sketch's _ribbon, returned as points)."""
    h = w / 2
    n = len(pts)
    left, right = [], []
    for k in range(n):
        if k in (0, n - 1):
            a, b = (pts[0], pts[1]) if k == 0 else (pts[-2], pts[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            Lh = math.hypot(dx, dy) or 1
            nx, ny, m = -dy / Lh, dx / Lh, h
        else:
            ax, ay = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            bx, by = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            n1, n2 = (-ay / la, ax / la), (-by / lb, bx / lb)
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln, ny / ln
            m = h / max(0.5, nx * n1[0] + ny * n1[1])
        x, y = pts[k]
        left.append((x + nx * m, y + ny * m))
        right.append((x - nx * m, y - ny * m))
    return dedupe(left + right[::-1], 0.2)


for _b in VOICED:
    p = _b["parts"]
    p["wl_rib"] = ribbon(p["wl"], HAIR)
    if "refl" in p:
        p["refl_rib"] = ribbon(p["refl"], HAIR)

# ---------------------------------------------------------------- ripple lines (swell fronts)
K_LINES = 30
D_RAFT = RAFT_C[1]                     # crest timing is set at the raft's centre line
MIN_GAP = 3.6                           # fronts closer than this on screen are hidden (craft: lines >= 3 px apart)
Y_BOTTOM = H + 4


def wavelength(T):
    """World spacing of the fronts: longer period, longer wave (deep water: lambda ~ T^2; drawn as T^0.5
    so the fast end stays above the 3 px hatching floor and the slow end keeps several fronts in view)."""
    return 0.95 * (T / 2.0) ** 0.5


def depth_for_y(y):
    """Water depth (world y) whose centre line projects to screen y."""
    lo, hi = -6.0, 4000.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if CAM.p((0, mid, 0))[1] > y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


D_NEAR = depth_for_y(Y_BOTTOM)
LINE_BASE = []
for _j in range(K_LINES):
    # neighbouring fronts stay nearly parallel: the phase walks once round the ring of K nodes,
    # so a node that wraps from the near edge to the far one still matches its new neighbours
    _ph = 2 * math.pi * _j / K_LINES
    LINE_BASE.append([(x, 1.1 * math.sin(2 * math.pi * x / 170 + _ph) + 0.5 * math.sin(2 * math.pi * x / 67 - 2 * _ph))
                      for x in [-292 + 584 * i / 30 for i in range(31)]])
LINE_RIB = [ribbon(b, HAIR) for b in LINE_BASE]


def line_scale(y):
    """Perspective swells a front a little as it nears (in plane, uniform, <= 2): 0.86 at the top,
    1.22 at the bottom edge. Ribbons stay 0.95-1.34 px: hairline to line."""
    t = max(0.0, min(1.0, (y - TOP) / (H - TOP)))
    return 0.86 + 0.36 * t


def line_shade(y, crest):
    base = 1 if y < 60 else (2 if y < 150 else 3)
    return min(5, base + crest)


def fronts(T, phase):
    """World depth of every visible front: wave w sits at D_RAFT + lambda (w + A - phase); it crosses the
    raft's centre line when phase = w + A, the moment the wave envelope peaks (A = its rise)."""
    lam = wavelength(T)
    a = rise_frac(T)
    out = []
    w0 = math.floor((D_NEAR - D_RAFT) / lam - a + phase) - 1
    w = w0
    last_y = None
    while len(out) < K_LINES:
        d = D_RAFT + lam * (w + a - phase)
        if d >= D_NEAR:
            y = CAM.p((0, d, 0))[1]
            if y < TOP + 3 or (last_y is not None and last_y - y < MIN_GAP):
                break
            out.append((w, d))
            last_y = y
        w += 1
    return out, lam


# ---------------------------------------------------------------- sound model (the brief's DSP, as the screen reads it)
def rise_s(T): return max(0.03, min(0.6, 0.15 * T))
def rise_frac(T): return rise_s(T) / T


def wave_env(t_since_on, T):
    """Fast rise, slow fall, repeating every T seconds from the note-on."""
    if t_since_on < 0:
        return 0.0
    ph = t_since_on % T
    a = rise_s(T)
    if ph < a:
        return math.sin(0.5 * math.pi * ph / a) ** 2
    return math.exp(-(ph - a) / (0.3 * T))


def partial_amp(k): return k ** -0.5
def partial_t60(k, depth): return depth * k ** -0.5


# ---------------------------------------------------------------- node model
# Node order = paint order: the ripple fronts, then every bubble far to near (dome, waterline, edge, reflection).
NODES = []          # (name, bubble or line index, part)
for j in range(K_LINES):
    NODES.append(("line", j, "rib"))
for b in sorted(BUBBLES, key=lambda b: -CAM.depth((b["x"], b["y"], b["z"]))):
    if b["kind"] == "spent":
        NODES.append(("spent", b, "dome"))
    else:
        NODES.append(("voiced", b, "dome"))
        NODES.append(("voiced", b, "wl"))
        NODES.append(("voiced", b, "edge"))
        if "refl" in b["parts"]:
            NODES.append(("voiced", b, "refl"))
PALETTE = G[:]          # palette entry i = stock grey step i


def base_edge_shade(k):
    return 6 if k == 1 else (5 if k <= 3 else 4)


def spent_count(depth_p):
    """Foam that has finished ringing and lingers on the water: none at 50 ms (it pops as it rings),
    all 28 at 5 s. Linear in the knob's position, which is already logarithmic in time."""
    return round(len(SPENT) * depth_p)


DRIFT_A = 0.27          # world units of wander at drift 100 (about 28 px across the screen)


def raft_layout(c, thetas):
    """Where every bubble floats for these controls. Drift: each bubble is pushed off its packed place
    in its own direction (theta: seeded at rest, a slow random walk while notes sound), mostly sideways,
    then a short relaxation pushes touching bubbles apart so none overlaps. The same few lines run on the
    device (24 bubbles, 276 pairs, a handful of passes) and only while drift is non-zero and something moves."""
    n_spent = spent_count(c["depth"])
    live = [b for b in BUBBLES if (b["kind"] == "voiced" or b["order"] < n_spent) and not b.get("host")]
    pos = {}
    for b in live:
        th = thetas[id(b)]
        pos[id(b)] = [b["x"] + c["drift"] * DRIFT_A * math.cos(th), b["y"] + c["drift"] * 0.35 * DRIFT_A * math.sin(th)]
    if c["drift"] > 0:
        rad = {id(b): b["r"] * (salt_scale(b["k"], c["salt"]) if b["kind"] == "voiced" else 1.0) for b in live}
        for _ in range(40):
            moved = False
            for i in range(len(live)):
                for j in range(i + 1, len(live)):
                    a, b = pos[id(live[i])], pos[id(live[j])]
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    d = math.hypot(dx, dy) or 1e-6
                    need = (rad[id(live[i])] + rad[id(live[j])]) * 1.02
                    if d < need:
                        ra, rb = rad[id(live[i])], rad[id(live[j])]
                        wa = rb ** 2 / (ra ** 2 + rb ** 2)          # the smaller bubble gives way
                        push = need - d
                        a[0] -= dx / d * push * wa; a[1] -= dy / d * push * wa
                        b[0] += dx / d * push * (1 - wa); b[1] += dy / d * push * (1 - wa)
                        moved = True
            if not moved:
                break
    return pos


def pose_bubble(b, c, layout, bob_px=0.0):
    """Screen translation and uniform scale for a bubble's nodes (about its projected centre).
    A stacked bubble rides its host: same translation, and its offset from the host scales with it."""
    if b.get("host"):
        h = b["host"]
        (hdx, hdy), hs = pose_bubble(h, c, layout, bob_px)
        hc = h["parts"]["centre"]
        mc = b["parts"]["centre"]
        nx = hc[0] + hdx + (mc[0] - hc[0]) * hs
        ny = hc[1] + hdy + (mc[1] - hc[1]) * hs
        return (round(nx - mc[0]), round(ny - mc[1])), hs
    x, y = layout[id(b)]
    c0 = b["parts"]["centre"]
    c1 = CAM.p((x, y, 0.0))
    persp = CAM.depth((b["x"], b["y"], 0)) / CAM.depth((x, y, 0))
    s = persp * (salt_scale(b["k"], c["salt"]) if b["kind"] == "voiced" else 1.0)
    return (round(c1[0] - c0[0]), round(c1[1] - c0[1] - bob_px)), round(s * 64) / 64


def node_state(c, sim=None):
    """Every node's (dx, dy, scale, shade, hidden) for controls c and an optional sim snapshot."""
    T = swell_s(c["swell"])
    phase = sim["phase"] if sim else 0.0
    fr, lam = fronts(T, phase)
    st = {}
    # fronts: assign wave w to node w mod K (a node keeps its front while it travels)
    used = {}
    for w, d in fr:
        used.setdefault(w % K_LINES, (w, d))
    for j in range(K_LINES):
        if j not in used:
            st[("line", j)] = None
            continue
        w, d = used[j]
        y = round(CAM.p((0, d, 0))[1])
        crest = 0
        if sim:
            near = math.exp(-((d - D_RAFT) / (0.45 * lam)) ** 2)
            crest = round(2 * sim["wave"] * near)
        st[("line", j)] = (0, y, round(line_scale(y) * 64) / 64, line_shade(y, crest))
    n_spent = spent_count(c["depth"])
    thetas = sim["theta"] if sim else {id(b): b["seed"] for b in BUBBLES}
    layout = raft_layout(c, thetas)
    for kind, b, part in NODES:
        if kind == "line":
            continue
        if kind == "spent" and b["order"] >= n_spent:
            st[(id(b), part)] = None
            continue
        bob = 0.0
        if sim and sim["wave"] > 0:
            lam_ = lam
            # distance from the bubble to the nearest front, in wavelengths
            u = ((b["y"] - D_RAFT) / lam_ - rise_frac(T) + phase) % 1.0
            u = min(u, 1 - u)
            bob = 2.2 * max(0.0, min(1.0, (T - 0.5) / 1.5)) * sim["wave"] * math.cos(math.pi * u) ** 8
        (dx, dy), s = pose_bubble(b, c, layout, round(bob))
        shade = 0
        if part == "edge":
            steps = sim["steps"][b["k"]] if sim else 0
            shade = min(7, base_edge_shade(b["k"]) + steps)
        elif part in ("wl", "refl"):
            shade = 3
        elif kind == "spent":
            shade = 3          # stroke shade; its fill stays black: a hollow, quiet bubble (wireframe, toro-style)
        st[(id(b), part)] = (dx, dy, s, shade)
    return st


# ---------------------------------------------------------------- SVG
def path_d(pts):
    return "M " + " L ".join(f"{f2(x)} {f2(y)}" for x, y in pts) + " Z"


def xf(pts, origin, dx, dy, s):
    ox, oy = origin
    return [(ox + dx + (x - ox) * s, oy + dy + (y - oy) * s) for x, y in pts]


def render(c, sim=None):
    st = node_state(c, sim)
    out = []
    for i, (kind, ref, part) in enumerate(NODES):
        nid = f"{PREFIX}_node_{i}"
        if kind == "line":
            v = st[("line", ref)]
            pts = LINE_RIB[ref]
            if v is None:
                out.append(f'<path id="{nid}" transform="matrix(1 0 0 1 640 320)" d="{path_d(pts)}" fill="{G[2]}" stroke="none"/>')
                continue
            _, y, s, shade = v
            pts = [(240 + x * s, y + yy * s) for x, yy in pts]
            out.append(f'<path id="{nid}" d="{path_d(pts)}" fill="{G[shade]}" stroke="none"/>')
            continue
        b = ref
        p = b["parts"]
        v = st[(id(b), part)]
        src = {"dome": p["dome"], "wl": p.get("wl_rib"), "edge": p.get("edge"), "refl": p.get("refl_rib")}[part]
        if v is None:
            out.append(f'<path id="{nid}" transform="matrix(1 0 0 1 640 320)" d="{path_d(src)}" '
                       f'fill="#000000" stroke="{G[3]}" stroke-width="{HAIR}"/>')
            continue
        dx, dy, s, shade = v
        pts = xf(src, p["centre"], dx, dy, s)
        if part == "dome" and kind == "voiced":
            out.append(f'<path id="{nid}" d="{path_d(pts)}" fill="#000000" stroke="none"/>')
        elif part == "dome":
            out.append(f'<path id="{nid}" d="{path_d(pts)}" fill="#000000" stroke="{G[shade]}" stroke-width="{HAIR}"/>')
        else:
            out.append(f'<path id="{nid}" d="{path_d(pts)}" fill="{G[shade]}" stroke="none"/>')
    # palette donors, parked off screen
    for i, g in enumerate(PALETTE):
        out.append(f'<circle id="{PREFIX}_palette_{i}" cx="{700 + 12 * i}" cy="300" r="4" fill="{g}" stroke="{g}" stroke-width="{HAIR}"/>')
    return frame_svg(out, header_values(c))


def frame_svg(body, header):
    steps = G
    hdr = [f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{col}" stroke="none"/>' for i, col in enumerate(steps)]
    for i, (t, v) in enumerate(header):
        ink = "#CBCBCB" if i < 2 else G[0]
        hdr.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * i} 10)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="10px">{t}</text>')
        hdr.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * i} 17.44)" fill="{ink}" stroke="none" '
                   f'font-family="{FONT}" font-size="20px">{v}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<g id="preview_canvas">', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{G[0]}" stroke="none"/>', '</g>',
        '<g id="preview_header">', *hdr, '</g>',
        *body, '</svg>', ""])


def to_png(svg_path, png_path):
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-b", "black", "-o", str(png_path), str(svg_path)], check=True)


# ---------------------------------------------------------------- motion simulation
class Sim:
    """The display's own model, stepped at the device's frame rate (60 fps assumed). Voices are
    (t_on, t_off). Amp release is a stand-in (SDK 1.10 `amp` would pace it on the device)."""

    def __init__(self, c, voices, release=0.5, fps=60, seed=5):
        self.c, self.voices, self.release, self.fps = c, voices, release, fps
        self.T = swell_s(c["swell"])
        self.depth = depth_s(c["depth"])
        self.phase = 0.0
        self.res = {(v, k): 0.0 for v in range(len(voices)) for k in range(1, 9)}
        self.theta = {id(b): b["seed"] for b in BUBBLES}
        self.rnd = random.Random(seed)
        self.t = 0.0
        self.lock = None      # the voice the fronts follow (oldest sounding)

    def amp(self, v, t):
        on, off = self.voices[v]
        if t < on:
            return 0.0
        if off is None or t < off:
            return min(1.0, (t - on) / 0.01)
        a = math.exp(-(t - off) * 6.91 / self.release)
        return a if a > 1e-3 else 0.0

    def step(self):
        dt = 1 / self.fps
        t = self.t = self.t + dt
        amps = [self.amp(v, t) for v in range(len(self.voices))]
        sounding = [v for v, a in enumerate(amps) if a > 0]
        # fronts follow the oldest sounding voice's clock; while its noise fades, they slow and stop
        if sounding:
            lock = min(sounding, key=lambda v: self.voices[v][0])
            if lock != self.lock:
                self.lock = lock
                self.ease_from = (self.phase - (t - self.voices[lock][0]) / self.T + 0.5) % 1.0 - 0.5
                self.ease_t0 = t
            target = (t - self.voices[lock][0]) / self.T
            e = math.exp(-(t - self.ease_t0) / 0.05)        # settles in ~0.2 s
            speed = amps[lock] ** 0.5
            if speed >= 0.999:
                self.phase = target + self.ease_from * e
            else:
                self.phase += speed / self.T * dt
        wave = 0.0
        for v, a in enumerate(amps):
            if a <= 0:
                continue
            ev = wave_env(t - self.voices[v][0], self.T) * a
            wave = max(wave, ev)
            for k in range(1, 9):
                u = ev * partial_amp(k)
                r = self.res[(v, k)]
                if u > r:
                    r += (u - r) * (1 - math.exp(-dt / 0.02))
                else:
                    r *= math.exp(-dt * 6.91 / partial_t60(k, self.depth))
                self.res[(v, k)] = r
        for v, a in enumerate(amps):
            if a <= 0:
                for k in range(1, 9):
                    self.res[(v, k)] *= math.exp(-dt * 6.91 / partial_t60(k, self.depth))
        steps = {}
        for k in range(1, 9):
            Lk = math.sqrt(sum(self.res[(v, k)] ** 2 for v in range(len(self.voices))))
            db = 20 * math.log10(Lk) if Lk > 1e-6 else -120
            steps[k] = max(0, min(3, int((db + 18) // 6)))
        self.wave = wave
        # drift: a slow random walk while anything sounds
        if sounding and self.c["drift"] > 0:
            for b in BUBBLES:
                self.theta[id(b)] += self.rnd.gauss(0, 0.25 * math.sqrt(dt))
        return {"phase": self.phase, "wave": wave, "steps": steps, "theta": dict(self.theta), "sounding": bool(sounding)}


def redraw(c, voices, seconds, release=0.5):
    sim = Sim(c, voices, release)
    prev = node_state(c, None)
    counts = []
    for _ in range(int(seconds * sim.fps)):
        snap = sim.step()
        st = node_state(c, snap)
        counts.append(sum(1 for k in st if st[k] != prev.get(k)))
        prev = st
    return counts


def budget_report():
    rows = []
    D = dict(DEFAULTS)
    heavy = {"swell": 0.0, "depth": 1.0, "salt": 1.0, "drift": 1.0}
    cases = [
        ("defaults, one note held 6 s", D, [(0.0, 6.0)], 9.0),
        ("defaults, 4-note chord rolled", D, [(0.0, 6.0), (0.3, 6.0), (0.55, 6.0), (0.9, 6.0)], 9.0),
        ("swell 0 (0.25 s), one note", dict(D, swell=0.0), [(0.0, 6.0)], 9.0),
        ("swell 100 (8 s), one note", dict(D, swell=1.0), [(0.0, 12.0)], 15.0),
        ("drift 100, one note", dict(D, drift=1.0), [(0.0, 6.0)], 9.0),
        ("heaviest: swell 0, depth/salt/drift 100, 8 voices", heavy,
         [(0.07 * i, 6.0) for i in range(8)], 18.0),
    ]
    for name, c, voices, secs in cases:
        cnt = redraw(c, voices, secs)
        last_on = max(on for on, _ in voices)
        last_off = max(off for _, off in voices)
        fps = 60
        sounding = cnt[: int(last_off * fps)]
        sounding = sounding[int(last_on * fps):] or sounding
        tail = cnt[int(last_off * fps):]
        still_at = next((i for i in range(len(tail)) if all(x == 0 for x in tail[i:])), len(tail))
        avg = sum(sounding) / len(sounding)
        rows.append((name, avg, max(cnt), still_at / fps, sum(tail[still_at:])))
    return rows


# ---------------------------------------------------------------- outputs
def control_frames():
    files = []
    c = dict(DEFAULTS)
    (HERE / "rest.svg").write_text(render(c))
    files.append(HERE / "rest.svg")
    for name in ("swell", "depth", "salt", "drift"):
        for v in (0, 50, 100):
            cc = dict(DEFAULTS, **{name: v / 100})
            pth = HERE / f"{name}-{v}.svg"
            pth.write_text(render(cc))
            files.append(pth)
    for pth in files:
        to_png(pth, pth.with_suffix(".png"))
    return files


def motion(out_gif=HERE / "motion.gif", sheet=HERE / "motion-sheet.png", fps_out=20):
    from PIL import Image, ImageDraw, ImageFont
    c = dict(DEFAULTS)
    T = swell_s(c["swell"])
    t_on, t_off, total = 0.6, 0.6 + 2.6 * T, 0.6 + 2.6 * T + 2.2
    sim = Sim(c, [(t_on, t_off)])
    tmp = HERE / "_motion_tmp"
    tmp.mkdir(exist_ok=True)
    frames, times = [], []
    every = sim.fps // fps_out
    n = int(total * sim.fps)
    for i in range(n):
        snap = sim.step()
        if i % every:
            continue
        svgp = tmp / f"f{i:05d}.svg"
        svgp.write_text(render(c, snap))
        pngp = svgp.with_suffix(".png")
        to_png(svgp, pngp)
        frames.append(Image.open(pngp).convert("L").convert("P"))
        times.append(sim.t)
    frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=int(1000 / fps_out), loop=0, optimize=False)
    # key frames: rest, note on, first crest, between, second crest, note off, tail, rest again
    peak = rise_s(T)
    keys = [0.3, t_on + 0.1, t_on + peak, t_on + peak + 0.5, t_on + T + peak, t_off + 0.05, t_off + 0.35, total - 0.1]
    labels = ["rest", "note on +0.1 s", "1st crest", "+0.5 s", "2nd crest", "note off", "release +0.35 s", "rest again"]
    pick = [min(range(len(times)), key=lambda j: abs(times[j] - k)) for k in keys]
    cols, pad, lab = 4, 12, 18
    sw = cols * W + (cols + 1) * pad
    sh = 2 * (H + lab) + 3 * pad
    img = Image.new("L", (sw, sh), 40)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    for idx, (j, label) in enumerate(zip(pick, labels)):
        r, q = divmod(idx, cols)
        x = pad + q * (W + pad)
        y = pad + r * (H + lab + pad)
        draw.text((x, y), f"t = {times[j] - t_on:+.2f} s  ·  {label}", fill=210, font=font)
        img.paste(frames[j].convert("L"), (x, y + lab))
    img.save(sheet)
    # note-response pair for perceptibility (scratch)
    crest = min(range(len(times)), key=lambda j: abs(times[j] - (t_on + T + peak)))
    for f in tmp.iterdir():
        if f.suffix == ".svg" and f.stem != f"f{pick[4] * 0 + int(times[crest] * sim.fps) - 1:05d}":
            pass
    return tmp, times, crest, every, sim.fps


def main():
    files = control_frames()
    print("\n".join(str(f) for f in files))
    if "--motion" in sys.argv:
        tmp, times, crest, every, fps = motion()
        print("motion frames in", tmp, "crest frame index", crest)
    if "--budget" in sys.argv or "--motion" in sys.argv:
        for name, avg, peak, still, after in budget_report():
            print(f"{name:55s} avg {avg:5.1f}  peak {peak:3d}  still {still:4.2f} s after last note-off  (changes after still: {after})")


if __name__ == "__main__":
    main()
