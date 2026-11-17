"""One machine's frame generator, run in its own process so a slow or broken generator can't take the bench down.

    python3 worker.py screens/<id>/bench.py

Reads one JSON request per line on stdin: {"values": {control id: 0..1}, "notes": 0..1}
Writes one JSON reply per line on stdout:  {"svg": "<svg …>"} or {"error": "…"}

The adapter (screens/<id>/bench.py) defines:

    def frame(values: dict[str, float], notes: float) -> str

values holds every control by its definition id, 0..1 like the device passes them; notes is 0 with nothing held
and 1 with a note held and fully lit. It returns one 480 × 220 SVG frame, drawn by the same code as the stills.
Anything the adapter prints goes to stderr so it can't break the protocol.
"""
from __future__ import annotations

import contextlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path


def load(path: Path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("opxy_bench_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"can't load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with contextlib.redirect_stdout(sys.stderr):
        spec.loader.exec_module(mod)
    if not callable(getattr(mod, "frame", None)):
        raise ImportError(f"{path.name} has no frame(values, notes) function")
    return mod


def main() -> int:
    out = sys.stdout
    try:
        mod = load(Path(sys.argv[1]).resolve())
    except Exception as exc:  # report once, then answer every request with the same error
        broken = f"{type(exc).__name__}: {exc}"
        print(traceback.format_exc(), file=sys.stderr)
        mod = None
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            if mod is None:
                raise RuntimeError(broken)
            req = json.loads(line)
            values = {str(k): min(1.0, max(0.0, float(v))) for k, v in (req.get("values") or {}).items()}
            notes = min(1.0, max(0.0, float(req.get("notes", 0))))
            with contextlib.redirect_stdout(sys.stderr):
                svg = mod.frame(values, notes)
            if not isinstance(svg, str) or "<svg" not in svg[:400]:
                raise TypeError("frame() must return SVG text")
            reply = {"svg": svg}
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            reply = {"error": f"{type(exc).__name__}: {exc}"}
        out.write(json.dumps(reply) + "\n")
        out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
