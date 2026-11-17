#!/usr/bin/env python3
"""Draw a variant's knob sweep: a short run of frames that lets the person turn the knobs before they pick.

    python3 opxy/tools/sweep.py screens/<id>/passes/03-frames/v2 --definition screens/<id>/definition.json
    python3 opxy/tools/sweep.py <variant dir> --definition <definition.json> --steps 0,25,50,75,100 --json

The variant folder holds a bench.py with the same contract as a machine's own screens/<id>/bench.py:

    def frame(values: dict[str, float], notes: float) -> str

values has every control by its definition id, 0..1 like the device passes them; notes is 0 at rest and 1 with a
note held. It returns one 480 × 220 SVG frame. From it I write, next to rest.svg:

    c<N>-000.svg, c<N>-050.svg, c<N>-100.svg   each control N at that value, the others at their defaults
    playing.svg                                 every control at default, a note held

Those are the protocol's own keyframe names (protocol.md, phase 5), so the bench plays them with no extra wiring and
the frame set drawn after the pick can start from the same code. rest.svg is written only when it's missing; when
it's there and the generator draws something else at the defaults, that's reported, because the board would show
one drawing and the knobs another.

Why a subprocess: bench.py is a designer's script. Running it in its own interpreter (isolated, its own folder as
the working directory, a time limit) means a slow or broken one can't hang or pollute whatever called me, the MCP
server included.

Exit codes: 0 written, 1 the generator failed or drew something that isn't a frame, 2 usage or missing files.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

STALE = re.compile(r"^c\d+-\d{3}\.svg$")
TIMEOUT = 120.0     # seconds for the whole sweep; a frame should take well under a second
MAX_SVG = 4_000_000


def parse_steps(text: str) -> list[int]:
    try:
        steps = sorted({int(s) for s in text.split(",") if s.strip()})
    except ValueError:
        raise ValueError(f"steps are whole percentages separated by commas, not {text!r}")
    if not steps or steps[0] < 0 or steps[-1] > 100:
        raise ValueError("steps run from 0 to 100")
    if len(steps) < 2:
        raise ValueError("a sweep needs at least two steps, or the knob has nothing to move between")
    return steps


def controls(definition: Path) -> list[dict]:
    params = json.loads(definition.read_text(encoding="utf-8")).get("parameters") or []
    return [{"id": p.get("id", f"c{i + 1}"), "default": min(1.0, max(0.0, float(p.get("default", 0.0))))}
            for i, p in enumerate(params)]


def jobs(ctrls: list[dict], steps: list[int]) -> list[dict]:
    """Every frame the sweep draws, as {name, values, notes}."""
    base = {c["id"]: c["default"] for c in ctrls}
    out = [{"name": "rest.svg", "values": base, "notes": 0.0},
           {"name": "playing.svg", "values": base, "notes": 1.0}]
    for n, c in enumerate(ctrls, start=1):
        for s in steps:
            out.append({"name": f"c{n}-{s:03d}.svg", "values": {**base, c["id"]: s / 100}, "notes": 0.0})
    return out


# ── the child: loads bench.py, draws every job, prints {name: svg} ────────────
def _child(folder: Path, payload: str) -> int:
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location("opxy_variant_bench", folder / "bench.py")
    if spec is None or spec.loader is None:
        print(json.dumps({"error": "can't load bench.py"}))
        return 1
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    out = sys.stdout
    try:
        with contextlib.redirect_stdout(sys.stderr):  # anything the generator prints stays off the reply
            spec.loader.exec_module(mod)
            if not callable(getattr(mod, "frame", None)):
                raise ImportError("bench.py has no frame(values, notes) function")
            drawn = {}
            for j in json.loads(payload):
                svg = mod.frame(dict(j["values"]), float(j["notes"]))
                if not isinstance(svg, str) or "<svg" not in svg[:400]:
                    raise TypeError(f"frame() returned {type(svg).__name__} for {j['name']}, not SVG text")
                if len(svg) > MAX_SVG:
                    raise ValueError(f"{j['name']} is {len(svg)} bytes; a frame should be far smaller")
                drawn[j["name"]] = svg
    except Exception as exc:
        out.write(json.dumps({"error": f"{type(exc).__name__}: {exc}"}))
        return 1
    out.write(json.dumps({"frames": drawn}))
    return 0


def draw(folder: Path, todo: list[dict], timeout: float = TIMEOUT) -> dict[str, str]:
    """Run bench.py in its own interpreter and hand back {file name: svg}. Raises RuntimeError with its message."""
    try:
        p = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--child", str(folder)],
                           input=json.dumps(todo), capture_output=True, text=True, encoding="utf-8",
                           cwd=str(folder), timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"bench.py took longer than {timeout:.0f} s for {len(todo)} frames")
    try:
        reply = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        reply = {}
    if "frames" in reply:
        return reply["frames"]
    tail = (p.stderr or "").strip().splitlines()[-3:]
    raise RuntimeError(reply.get("error") or ("bench.py exited without a reply: " + " | ".join(tail)))


def sweep(folder: Path, definition: Path, steps: list[int]) -> dict:
    if not (folder / "bench.py").is_file():
        raise FileNotFoundError(f"{folder}/bench.py not found; it draws the frames the knobs play")
    ctrls = controls(definition)
    if not ctrls:
        raise ValueError(f"{definition} has no parameters, so there's nothing for a knob to sweep yet")
    todo = jobs(ctrls, steps)
    drawn = draw(folder, todo)
    warnings, written = [], []
    for f in folder.glob("c*-*.svg"):  # a sweep with other steps leaves frames the knobs would snap to
        if STALE.match(f.name) and f.name not in drawn:
            f.unlink()
    for name, svg in drawn.items():
        path = folder / name
        if name == "rest.svg" and path.exists():
            if path.read_text(encoding="utf-8") != svg:
                warnings.append("rest.svg isn't what bench.py draws at the defaults; the board shows rest.svg and the "
                                "knobs start from bench.py, so make one come from the other")
            continue
        path.write_text(svg, encoding="utf-8")
        written.append(name)
    return {"folder": str(folder), "steps": steps, "controls": len(ctrls), "written": sorted(written),
            "frames": len(written), "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--child"]:
        return _child(Path(argv[1]).resolve(), sys.stdin.read())
    ap = argparse.ArgumentParser(description="Draw a variant's knob sweep from its bench.py.")
    ap.add_argument("folder", help="the variant folder (holds bench.py and rest.svg)")
    ap.add_argument("--definition", required=True, help="the machine's definition.json (controls, defaults)")
    ap.add_argument("--steps", default="0,50,100", help="percentages to draw each control at (default 0,50,100)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    folder, definition = Path(a.folder).resolve(), Path(a.definition).resolve()
    try:
        steps = parse_steps(a.steps)
        if not definition.is_file():
            raise FileNotFoundError(f"{a.definition} not found")
        result = sweep(folder, definition, steps)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"sweep: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        if a.json:
            print(json.dumps({"folder": str(folder), "error": str(exc)}))
        print(f"sweep: {exc}", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['frames']} frame(s) in {folder}: {result['controls']} controls at {', '.join(map(str, steps))}, "
              f"plus playing" + ("" if "rest.svg" not in result["written"] else " and rest"))
        for w in result["warnings"]:
            print(f"warning: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
