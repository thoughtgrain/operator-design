#!/usr/bin/env python3
"""Build prototype.html from the same model as the frames.

Static artwork, star and trail layouts, and every constant come from gen_frames.py, so the moving
prototype can't drift from the contact sheet. The page shell (styles, controls, meter) lives in
prototype_shell.html; the per-frame drawing below mirrors gen_frames.frame() with motion from motion.md.

    python3 screens/toro/build_prototype.py
"""
from __future__ import annotations

import json
from pathlib import Path

import gen_frames as g

HERE = Path(__file__).resolve().parent


def static_halos() -> str:
    out = []
    for name, (x, y) in g.POS.items():
        r = g.STARS[name][2]
        out.append(f'<path transform="matrix(1 0 0 1 {g.f(x)} {g.f(y)})" d="{g.poly(g.dot(r + 2.2, 12))}" fill="#000000" stroke="none"/>')
    return "\n".join(out)


def main() -> None:
    model = {
        "G": g.G, "POS": g.POS, "STARS": {k: v[2] for k, v in g.STARS.items()}, "JOINS": g.JOINS,
        "MOON": {"y": g.MOON_Y, "x0": g.MOON_X0, "x1": g.MOON_X1, "r": g.MOON_R, "phases": g.MOON_PHASES},
        "INSET": g.INSET, "INSET_R": g.INSET_R, "MW": {"origin": g.MW_ORIGIN, "a": g.MW_A, "b": g.MW_B},
        "FIELD": [[round(x, 1), round(y, 1), r, sh] for x, y, r, sh in g.FIELD],
        "TRAIL": [[round(a[0], 1), round(a[1], 1), round(ang, 1), round(ln, 1)] for a, ang, ln in g.TRAIL],
        "FIELD_BASE": g.FIELD_BASE, "BODY_TOP": g.BODY_TOP, "LINE_W": g.LINE_W, "HAIR": g.HAIR,
        "CONTROLS": g.CONTROLS, "DEFAULTS": g.DEFAULTS,
    }
    layers = {"back": "\n".join(g.static_back()), "halos": static_halos(), "labels": "\n".join(g.labels()),
              "inset": "\n".join(g.inset_frame())}
    script = (HERE / "prototype_model.js").read_text(encoding="utf-8")
    shell = (HERE / "prototype_shell.html").read_text(encoding="utf-8")
    page = shell + "<script>\nconst MODEL = " + json.dumps(model, separators=(",", ":")) + ";\nconst LAYERS = " + \
        json.dumps(layers) + ";\n" + script + "\n</script>\n"
    (HERE / "prototype.html").write_text(page, encoding="utf-8")
    print(f"wrote prototype.html ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
