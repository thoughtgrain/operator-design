"""The owner's bull, rebuilt pixel-exact from the photo of the device (opxy/reference/toro-ink-rest.jpg).

The first trace box-averaged the photo, which smeared every 2 px line into a dotted one. This one point-samples the
photo at the centre of each display pixel (the photo is 2.5 × 2.79 camera px per display px; I search scale and phase
for the crispest result), so the lines come back as clean 2 px strokes. Then:

  1. solid  = everything bright that survives a 2 × 2 opening: the lines, the eye whites, the nostrils, the dot grids,
              the bar glyphs. Isolated 1 px dither doesn't survive, which is the point
  2. cells  = the regions between the lines (gaps closed by dilating the lines 2 px before labelling, then the labels
              grown back up to the lines)
  3. each cell is classified from the photo's own brightness inside it:
        flat   low variance, brighter than the background: the panel shows a fine 1 px checker, which reads as a flat
               dark grey on the device. I draw it as grey G_FINE
        25 %   visible sparse dither (the forehead cap)
        50 %   visible checker (the left horn, the cheek and leg panels)
        dark   background and black cells; their isolated dots (swatches, stars, grain) are kept from the photo

Everything is cached in ink/art.npz so the photo is only read once.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import (binary_dilation, binary_erosion, binary_fill_holes, binary_opening, distance_transform_edt,
                           label, map_coordinates, maximum_filter)

HERE = Path(__file__).resolve().parent
REFDIR = HERE.parent.parent / "opxy" / "reference"
# photo, the display's top-left in it, and the camera px per display px to search around
REFS = {"rest": (REFDIR / "toro-ink-rest.jpg", (83, 71), 2.5, 2.8),
        "smoke": (REFDIR / "toro-ink-smoke.jpg", (66, 50), 1.875, 2.1)}
W, H, TOP = 480, 220, 40
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
_yy, _xx = np.mgrid[0:H, 0:W]
BAY = BAYER[_yy % 4, _xx % 4]

FLAT, D25, D50, DARK = 1, 2, 3, 0                     # cell classes
G_FINE = 75                                           # the flat grey a fine checker reads as on the panel


def sample(name="rest") -> np.ndarray:
    """the photo point-sampled at display-pixel centres, at the scale and phase that make the lines crispest"""
    path, origin, sx0, sy0 = REFS[name]
    a = np.array(Image.open(path).convert("L").filter(ImageFilter.GaussianBlur(0.5 * sx0 / 2.5))).astype(float)
    best = None
    for sx in (sx0 * 0.996, sx0, sx0 * 1.004):
        for sy in (sy0 * 0.996, sy0, sy0 * 1.004):
            for dx in np.arange(-1.0, 1.01, 0.12) * sx0:
                for dy in np.arange(-1.0, 1.01, 0.12) * sy0:
                    X = origin[0] + dx + (_xx + 0.5) * sx
                    Y = origin[1] + dy + (_yy + 0.5) * sy
                    s = map_coordinates(a, [Y, X], order=1)
                    crisp = np.mean(np.abs(s[45:] - 128) > 75)
                    if best is None or crisp > best[0]:
                        best = (crisp, s)
    s = best[1]
    s[:TOP] = 0
    return s


def build(name="rest"):
    s = sample(name)
    solid = binary_opening(s > 105, structure=np.ones((2, 2)))
    wall = binary_dilation(solid, iterations=2)
    lab, n = label(~wall)
    idx = distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    cells = lab[idx[0], idx[1]]
    cells[solid] = 0
    peaks = (s >= maximum_filter(s, size=3)) & (s > 70)
    kind = np.zeros(n + 1, np.int8)
    mean = np.zeros(n + 1, np.float32)
    img = np.zeros((H, W), np.uint8)
    for k in range(1, n + 1):
        m = cells == k
        core = binary_erosion(m, iterations=1)
        use = core if core.sum() >= 20 else m
        mu, sd = (s[use].mean(), s[use].std()) if use.sum() >= 4 else (0.0, 0.0)
        mean[k] = mu
        if k == 1 or mu < 30 or use.sum() < 20:
            kind[k] = DARK
            img[m & ((s > 95) | peaks)] = 255
        elif sd < 16:
            kind[k] = FLAT
            img[m] = G_FINE
        elif mu > 55:
            kind[k] = D50
            img[m] = np.where(BAY[m] < 0.5, 255, 0)
        else:
            kind[k] = D25
            img[m] = np.where(BAY[m] < 0.25, 255, 0)
    img[solid] = 255
    img[:TOP] = 0
    cache = HERE / "ink" / f"art-{name}.npz"
    cache.parent.mkdir(exist_ok=True)
    np.savez_compressed(cache, img=img, cells=cells, kind=kind, solid=solid, mean=mean)
    return img, cells, kind, solid


def load(name="rest"):
    cache = HERE / "ink" / f"art-{name}.npz"
    if cache.exists():
        z = np.load(cache)
        if "mean" in z:
            return z["img"], z["cells"], z["kind"], z["solid"]
    return build(name)


def means(name="rest") -> np.ndarray:
    load(name)
    return np.load(HERE / "ink" / f"art-{name}.npz")["mean"]


def cell_at(cells, x, y) -> int:
    k = int(cells[y, x])
    if k == 0:
        raise ValueError(f"({x}, {y}) is on a line, not in a cell")
    return k


def region(cells, k, fill_holes=True) -> np.ndarray:
    m = cells == k
    return binary_fill_holes(m) if fill_holes else m


def outline(mask: np.ndarray, grow: float = 1.0, cap: int = 62, tol: float = 0.45, smooth: float = 1.4):
    """a mask's outer boundary as one polygon of ≤ cap points, pushed out `grow` px to the centre of its line"""
    from skimage.measure import approximate_polygon, find_contours
    m = binary_dilation(mask, iterations=1) if grow >= 1 else mask
    padded = np.pad(m, 1).astype(float)
    cs = find_contours(padded, 0.5)
    c = max(cs, key=len)
    pts = np.column_stack([c[:, 1] - 1 + 0.5, c[:, 0] - 1 + 0.5])   # index space → SVG space (pixel centres at +0.5)
    if smooth > 0 and len(pts) > 8:                     # a pixel staircase stroked as a vector reads ragged; ease it
        from scipy.ndimage import gaussian_filter1d
        closed = pts[:-1]
        pts = np.column_stack([gaussian_filter1d(closed[:, 0], smooth, mode="wrap"), gaussian_filter1d(closed[:, 1], smooth, mode="wrap")])
        pts = np.vstack([pts, pts[:1]])
    t = tol
    while True:
        simp = approximate_polygon(pts, t)
        if len(simp) - 1 <= cap:
            out = [tuple(map(float, p)) for p in simp[:-1]]
            return dedupe(out)
        t *= 1.25


def dedupe(pts, min_d=0.3):
    out = []
    for p in pts:
        if not out or (abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1])) >= min_d:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 0.6:
        out.pop()
    return out


# ---- pixel-exact outlines ----------------------------------------------------------------------------------------------
# A node drawn as the exact staircase outline of a pixel region, at integer coordinates, renders pixel for pixel like
# the drawing as long as it only moves by whole pixels. That's how the head keeps the photo's look and still moves.

def loops(mask: np.ndarray):
    """the boundary loops of a 4-connected pixel region, as lists of integer corner points, collinear points removed"""
    hgt, wid = mask.shape
    m = np.pad(mask, 1)
    edges = {}
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        py, px = y + 1, x + 1
        if not m[py - 1, px]:
            edges.setdefault((x, y), []).append((x + 1, y))          # top, left → right
        if not m[py, px + 1]:
            edges.setdefault((x + 1, y), []).append((x + 1, y + 1))  # right, top → bottom
        if not m[py + 1, px]:
            edges.setdefault((x + 1, y + 1), []).append((x, y + 1))  # bottom, right → left
        if not m[py, px - 1]:
            edges.setdefault((x, y + 1), []).append((x, y))          # left, bottom → top
    out = []
    while edges:
        start = next(iter(edges))
        loop, cur, prev_dir = [start], start, None
        while True:
            nxts = edges[cur]
            if len(nxts) == 1:
                nxt = nxts.pop()
            else:                                                       # a pinch: take the right-hand turn
                def turn(n):
                    d = (n[0] - cur[0], n[1] - cur[1])
                    if prev_dir is None:
                        return 0
                    return (prev_dir[0] * d[1] - prev_dir[1] * d[0])
                nxts.sort(key=turn, reverse=True)
                nxt = nxts.pop(0)
            if not nxts:
                del edges[cur]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
            loop.append(cur)
        simp = []
        n = len(loop)
        for i in range(n):
            a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                simp.append(b)
        out.append(simp)
    return out


def pieces(mask: np.ndarray, cap: int = 62, min_px: int = 1):
    """split a pixel mask into hole-free 4-connected pieces whose outlines have ≤ cap corners"""
    lab, n = label(mask)
    result = []
    for k in range(1, n + 1):
        comp = lab == k
        if comp.sum() < min_px:
            continue
        ls = loops(comp)
        if len(ls) == 1 and len(ls[0]) <= cap:
            result.append((comp, ls[0]))
            continue
        ys, xs = np.nonzero(comp)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        a, b = comp.copy(), comp.copy()
        if x1 - x0 >= y1 - y0:
            mid = (x0 + x1) // 2
            a[:, mid:] = False
            b[:, :mid] = False
        else:
            mid = (y0 + y1) // 2
            a[mid:, :] = False
            b[:mid, :] = False
        result += pieces(a, cap, min_px) + pieces(b, cap, min_px)
    return result
