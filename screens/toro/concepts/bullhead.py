"""A bull's head, head-on, as data: a silhouette, two horns and a relief (height) field.

Round 6 draws the bull five different ways, and every one of them comes from this single model. That keeps the
anatomy consistent across concepts and lets each style be a rendering decision, not a new drawing. Units are
pixels at scale 1 with the origin between the eyes; y points down. The head runs from the poll (y −46) to the chin
(y 56), and the horns reach about ±70.

    spread  0..1  how far the horns sweep out
    curl    0..1  how far the tips turn up and in (the engine's saw → triangle shape)
"""
from __future__ import annotations

import math

import numpy as np
from matplotlib.path import Path as MPath

# right half of the head outline, poll → ear → cheek → muzzle → chin; mirrored for the left
HALF = [(0, -45), (9, -47), (18, -46), (25, -43), (30, -37), (33, -33),
        (42, -36), (51, -36), (58, -33), (61, -29), (57, -24), (47, -21), (36, -21),
        (34, -14), (32, -4), (29, 6), (25, 16), (22, 25), (23, 33), (25, 41), (25, 48), (21, 54), (12, 58), (0, 59)]


def outline():
    right = HALF[1:-1]
    return [HALF[0]] + right + [HALF[-1]] + [(-x, y) for x, y in reversed(right)]


def bez(p, t):
    a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
    return (a * p[0][0] + b * p[1][0] + c * p[2][0] + d * p[3][0], a * p[0][1] + b * p[1][1] + c * p[2][1] + d * p[3][1])


def horn_spine(sd: int, spread: float, curl: float, n: int = 24):
    """the horn's centreline, root to tip, for side sd = ±1"""
    reach = 52 + 30 * spread
    lift = 22 + 18 * curl - 6 * spread
    p = [(24, -40), (34 + 8 * spread, -50), (reach - 14 * curl, -48 - 4 * spread), (reach - 10 * curl, -40 - lift)]
    return [(sd * x, y) for x, y in (bez(p, i / n) for i in range(n + 1))]


def horn_widths(n: int = 24, root: float = 15.0, tip: float = 1.8):
    return [root + (tip - root) * (i / n) ** 0.85 for i in range(n + 1)]


def tube(spine, widths):
    """offset both sides of a spine into one closed outline"""
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        w = widths[i] / 2
        left.append((x - dy / ln * w, y + dx / ln * w))
        right.append((x + dy / ln * w, y - dx / ln * w))
    return left + right[::-1]


def horn(sd, spread, curl):
    return tube(horn_spine(sd, spread, curl), horn_widths())


def _g(X, Y, cx, cy, sx, sy):
    return np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) / 2)


class Relief:
    """height field over the head and horns, sampled on a grid of `step` px"""

    def __init__(self, spread=0.06, curl=0.0, step=0.5, x0=-100, x1=100, y0=-100, y1=62):
        self.step = step
        xs = np.arange(x0, x1 + step, step)
        ys = np.arange(y0, y1 + step, step)
        self.X, self.Y = np.meshgrid(xs, ys)
        pts = np.column_stack([self.X.ravel(), self.Y.ravel()])
        head = MPath(outline()).contains_points(pts).reshape(self.X.shape)
        from scipy.ndimage import distance_transform_edt, gaussian_filter
        X, Y = self.X, self.Y
        soft = gaussian_filter(head.astype(float), 7 / step)
        h = np.sqrt(np.clip(soft - 0.25, 0, None) / 0.75) * 1.1                      # a rounded mass, no medial crease
        h += 0.30 * _g(X, Y, 0, -30, 20, 12)                                       # forehead dome
        h += 0.22 * (_g(X, Y, 18, -13, 8, 4) + _g(X, Y, -18, -13, 8, 4))          # brow ridges
        h -= 0.38 * (_g(X, Y, 21, -6, 5, 3.6) + _g(X, Y, -21, -6, 5, 3.6))            # eye sockets
        h += 0.20 * _g(X, Y, 0, 10, 7, 26)                                         # nose bridge
        h += 0.34 * _g(X, Y, 0, 42, 17, 10)                                        # muzzle
        h -= 0.40 * (_g(X, Y, 9, 45, 3.2, 2.6) + _g(X, Y, -9, 45, 3.2, 2.6))      # nostrils
        h -= 0.18 * _g(X, Y, 0, 52, 10, 2)                                         # mouth line
        h = np.where(head, h, 0.0)
        self.head = head
        horns = np.zeros_like(h)
        hmask = np.zeros_like(head)
        for sd in (-1, 1):
            m = MPath(horn(sd, spread, curl)).contains_points(pts).reshape(X.shape)
            hd = distance_transform_edt(m) * step
            horns = np.maximum(horns, np.sqrt(hd / 6.0) * 0.8)
            hmask |= m
        self.horns = hmask
        h = np.where(hmask & ~head, horns, h)
        self.h = gaussian_filter(h, 1.2 / step) * (head | hmask)
        self.mask = head | hmask

    def at(self, x, y):
        i = int(round((y - self.Y[0, 0]) / self.step))
        j = int(round((x - self.X[0, 0]) / self.step))
        if 0 <= i < self.h.shape[0] and 0 <= j < self.h.shape[1]:
            return float(self.h[i, j])
        return 0.0

    def normal_light(self, light=(-0.5, -0.7, 0.6), k=24.0):
        gy, gx = np.gradient(self.h * k, self.step)
        n = np.dstack([-gx, -gy, np.ones_like(gx)])
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        l = np.array(light) / np.linalg.norm(light)
        return np.clip((n * l).sum(axis=2), 0, 1)
