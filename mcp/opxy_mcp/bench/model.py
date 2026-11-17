"""What the bench shows: machines, their passes and variants, and the frame sets the knobs can play.

Read-only. Everything here comes from files the protocol already writes (definition.json, passes/<nn>/pass.json,
v<N>/rest.svg, candidate.json, frames/*.svg); the bench adds nothing to a screen folder except the events journal.

Frame names: the protocol's c<N>-000/050/100.svg, and the older <control id>-0/50/100.svg several screens use.
Both map to the same (control index, value) keyframes.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..paths import ToolError, load_json, machine_dir, rel, screens_dir

MACHINE_ID = re.compile(r"^[a-z][a-z0-9_]{0,14}$")
NUMBERED = re.compile(r"^c(?P<n>\d+)-(?P<v>\d{1,3})$")
NAMED = re.compile(r"^(?P<id>[a-z][a-z0-9_]*)-(?P<v>\d{1,3})$")


def _json(p: Path) -> dict:
    try:
        return load_json(p)
    except ToolError:
        return {}


def machines() -> list[dict]:
    out = []
    root = screens_dir()
    for d in sorted(p for p in root.iterdir() if p.is_dir() and MACHINE_ID.match(p.name)):
        passes = sorted((d / "passes").glob("*/pass.json")) if (d / "passes").is_dir() else []
        frames = d / "frames"
        out.append({"id": d.name, "name": _json(d / "definition.json").get("name") or d.name,
                    "passes": len(passes), "frames": len(list(frames.glob("*.svg"))) if frames.is_dir() else 0,
                    "live": generator_path(d.name) is not None})
    return out


def controls(machine_id: str) -> list[dict]:
    """The definition's parameters in order: index (1-based, the N in c<N>), id, label, default."""
    d = machine_dir(machine_id)
    params = _json(d / "definition.json").get("parameters") or []
    return [{"index": i + 1, "id": p.get("id", f"c{i + 1}"), "label": p.get("label") or p.get("id", f"c{i + 1}"),
             "default": float(p.get("default", 0.0))} for i, p in enumerate(params)]


def keyframes(frames_dir: Path, ctrls: list[dict]) -> dict:
    """{rest, playing, controls: {index: {value: url-path}}} for one folder of drawn frames."""
    ids = {c["id"].lower(): c["index"] for c in ctrls}
    labels = {c["label"].lower(): c["index"] for c in ctrls}
    out: dict = {"rest": None, "playing": None, "controls": {}}
    for f in sorted(frames_dir.glob("*.svg")):
        stem = f.stem.lower()
        if stem in ("rest", "playing"):
            out[stem] = rel(f)
            continue
        m = NUMBERED.match(stem)
        idx = int(m["n"]) if m else None
        if not m:
            m = NAMED.match(stem)
            if m:
                idx = ids.get(m["id"]) or labels.get(m["id"])
        if not m or not idx:
            continue
        v = int(m["v"])
        if 0 <= v <= 100:
            out["controls"].setdefault(str(idx), {})[str(v)] = rel(f)
    return out


def frame_sets(machine_id: str) -> list[dict]:
    """Every folder with drawn frames: the final frames/, then any pass variant that has more than its rest frame."""
    d = machine_dir(machine_id)
    ctrls = controls(machine_id)
    sets = []
    if (d / "frames").is_dir():
        sets.append({"id": "frames", "label": "frames", "keyframes": keyframes(d / "frames", ctrls)})
    for sub in sorted(x for x in d.glob("*/frames") if x.is_dir() and x.parent.name != "passes"):
        # an alternative drawing kept beside the main one (toro's blocks/), on the same controls
        sets.append({"id": f"{sub.parent.name}/frames", "label": sub.parent.name, "keyframes": keyframes(sub, ctrls)})
    for pj in sorted((d / "passes").glob("*/pass.json")) if (d / "passes").is_dir() else []:
        for v in sorted(pj.parent.glob("v[0-9]*")):
            kf = keyframes(v, ctrls)
            if kf["controls"] or kf["playing"]:
                sets.append({"id": f"{pj.parent.name}/{v.name}", "label": f"{pj.parent.name} · {v.name}", "keyframes": kf})
    return [s for s in sets if s["keyframes"]["rest"]]


def passes(machine_id: str) -> list[dict]:
    d = machine_dir(machine_id)
    out = []
    for pj in sorted((d / "passes").glob("*/pass.json")) if (d / "passes").is_dir() else []:
        r = _json(pj)
        out.append({"name": pj.parent.name, "kind": r.get("kind"), "state": r.get("state"), "focus": r.get("focus"),
                    "selected": (r.get("selection") or {}).get("variant")})
    return out


def _direction_words(kind: str, direction: dict) -> list[str]:
    if kind == "subject":
        return [w for w in (direction.get("angle") or direction.get("patternName"), direction.get("drawingLanguage")) if w]
    return [w for w in (direction.get("composition"), direction.get("camera"), direction.get("emphasis")) if w]


def _as_list(v) -> list[str]:
    """candidate.json says controls and risks as a list or as one paragraph; the page wants a list either way."""
    if not v:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def pass_view(machine_id: str, pass_name: str) -> dict:
    d = machine_dir(machine_id)
    pdir = (d / "passes" / pass_name)
    if not re.match(r"^\d{2}-[a-z]+$", pass_name) or not (pdir / "pass.json").exists():
        raise ToolError(f"no pass {pass_name} for {machine_id}")
    r = _json(pdir / "pass.json")
    kind = r.get("kind", "subject")
    submitted = {v.get("variant"): v for v in r.get("variants") or []}
    pairs = (r.get("uniqueness") or {}).get("pairs") or []
    ctrls = controls(machine_id)
    variants = []
    for direction in r.get("directions") or []:
        vid = direction["variant"]
        vdir = pdir / vid
        cand = submitted.get(vid) or _json(vdir / "candidate.json")
        rest = vdir / "rest.svg"
        kf = keyframes(vdir, ctrls) if vdir.is_dir() else {"controls": {}, "playing": None}
        variants.append({
            "variant": vid,
            "direction": _direction_words(kind, direction),
            "brief": direction.get("brief"),
            "subject": cand.get("subject"),
            "drawingLanguage": cand.get("drawing_language"),
            "angle": cand.get("angle"),
            "controls": _as_list(cand.get("controls")),
            "risks": _as_list(cand.get("risks")),
            "frame": rel(rest) if rest.exists() else None,
            "pairs": [p for p in pairs if "pair" in p and vid in p["pair"].split("–")],
            # the Play view's frame-set id for this variant, when it has a knob sweep to play
            "set": f"{pass_name}/{vid}" if (kf["controls"] or kf["playing"]) and rest.exists() else None,
            "sweep": {"controls": len(kf["controls"]),
                      "steps": sorted({int(v) for c in kf["controls"].values() for v in c})},
        })
    return {"machine": machine_id, "pass": pass_name, "kind": kind, "state": r.get("state"), "focus": r.get("focus"),
            "subject": r.get("subject"), "variants": variants,
            "notes": [p["note"] for p in pairs if "note" in p] + ((r.get("uniqueness") or {}).get("problems") or []),
            "selection": r.get("selection"), "rejection": r.get("rejection"),
            "preview": r.get("preview") or {"mode": "none", "steps": [], "set": "opened before knob sweeps existed"},
            "pickable": r.get("state") == "ready_for_pick",
            "rejectable": r.get("state") not in ("selected", "rejected")}


def generator_path(machine_id: str) -> Path | None:
    """screens/<id>/bench.py, if the machine ships one: it draws a frame for any control values (see generator.py)."""
    p = screens_dir() / machine_id / "bench.py"
    return p if p.is_file() else None


def machine_view(machine_id: str) -> dict:
    d = machine_dir(machine_id)
    gen = generator_path(machine_id)
    return {"id": machine_id, "name": _json(d / "definition.json").get("name") or machine_id,
            "controls": controls(machine_id), "passes": passes(machine_id), "frameSets": frame_sets(machine_id),
            "generator": rel(gen) if gen else None}
