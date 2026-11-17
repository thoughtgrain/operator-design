"""Bench adapter for toro: any knob position, drawn by gen_frames.frame, the same code as the stills.

gen_frames draws a note as on or off, so a held note shows once the envelope is past halfway.
"""
from __future__ import annotations

import gen_frames as g  # the worker puts this folder on the path


def frame(values: dict[str, float], notes: float) -> str:
    v = {k: values.get(k, g.DEFAULTS[k]) for k in g.CONTROLS}
    return g.frame(v, playing=notes >= 0.5)
