#!/usr/bin/env python3
"""Planet kinds for the meikyu orrery: each kind is one path (≤ 64 points) so a planet stays one bound node.

Every closed loop winds clockwise and everything else retraces itself, so a nonzero fill covers the whole disc and
the inner lines show as strokes. Kinds:

  wire    the house wireframe: outline, two front meridians that step round (spin variants), front equator
  smooth  a clean sphere: outline and one terminator arc, nothing else (no spin variants: a smooth ball doesn't show it)
  banded  a gas giant: outline and two front latitude bands (no spin variants)
  rocky   a slightly lumpy outline with a terminator (two tumble variants)
"""
from __future__ import annotations

import math
import random

import orrery2 as R2


def _circle(r, a0, a1, n):
    """points on the outline from angle a0 to a1 (0 = top, clockwise on screen), excluding the start"""
    return [(r * math.sin(a0 + (a1 - a0) * k / n), -r * math.cos(a0 + (a1 - a0) * k / n)) for k in range(1, n + 1)]


def smooth(r=10.0):
    pts = [(0.0, -r)] + _circle(r, 0, 2 * math.pi, 28)
    term = [(0.42 * r * math.sin(math.pi * k / 10), -r * math.cos(math.pi * k / 10)) for k in range(1, 11)]   # top → bottom
    pts += term + term[::-1][1:] + [(0.0, -r)]                         # out and back along the terminator
    return pts


def banded(r=10.0, lats=(-0.42, 0.22)):
    pts = [(0.0, -r)] + _circle(r, 0, 2 * math.pi, 20)
    a_prev = 0.0
    for lat in lats:                                                     # walk round to the band's right end, cross, back
        y = r * lat
        a_end = math.acos(-lat)                                          # angle from the top where the band meets the rim
        pts += _circle(r, a_prev, a_end, 3)
        half = math.sqrt(max(0.0, r * r - y * y))
        chord = [(half * math.cos(math.pi * k / 5), y + 0.28 * half * math.sin(math.pi * k / 5)) for k in range(1, 6)]
        pts += chord + chord[::-1][1:] + [(half, y)]
        a_prev = a_end
    pts += _circle(r, a_prev, 2 * math.pi, 8)                            # back round to the top: no closing chord
    assert len(pts) <= 64, len(pts)
    return pts


def rocky(seed, turn=0, r=10.0):
    """a slightly lumpy body (radius 0.88–1.0 round its rim) with the smooth sphere's terminator: rocky, not odd"""
    rnd = random.Random(seed)
    n = 16
    radii = [r * rnd.uniform(0.88, 1.0) for _ in range(n)]
    rot = turn * math.pi / 4
    outline = [(radii[k] * math.sin(rot + 2 * math.pi * k / n), -radii[k] * math.cos(rot + 2 * math.pi * k / n)) for k in range(n)]
    k0 = (-turn * n // 8) % n                                          # the vertex that sits at the top in this variant
    outline = outline[k0:] + outline[:k0]
    top, bottom = outline[0], outline[n // 2]                          # both on the vertical axis
    term = [(0.4 * r * math.sin(math.pi * k / 8), top[1] + (bottom[1] - top[1]) * (1 - math.cos(math.pi * k / 8)) / 2)
            for k in range(1, 9)]                                       # the terminator, top to bottom, inside the rim
    pts = outline + [top] + term + term[::-1][1:] + [top]
    assert len(pts) <= 64, len(pts)
    return pts


SPINS = {"wire": 3, "smooth": 1, "banded": 1, "rocky": 2}


def glyph(kind, variant, seed):
    if kind == "wire":
        return R2.planet_glyph(variant * 30 / 22.5, r=10.0)
    if kind == "smooth":
        return smooth()
    if kind == "banded":
        return banded()
    return rocky(seed, variant)
