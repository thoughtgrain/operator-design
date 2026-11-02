"""Screen workspace and checks: scaffolding, where a screen is in the protocol, and the opxy tools as calls."""
from __future__ import annotations

import base64
import datetime as dt
import glob
import re
import shutil
from pathlib import Path

from . import runner
from .paths import OPXY, ToolError, catalog, machine_dir, rel, resolve, tokens

FRAME_NAME = re.compile(r"^(rest|playing|c\d+-(000|050|100))\.(svg|png)$")
PHASE_FILES = [
    ("1 intake", "brief.md"),
    ("1A definition", "definition.json"),
    ("5 frames", "frames/rest.svg"),
    ("5 contact sheet", "contact.svg"),
    ("6 motion", "motion.md"),
    ("7 review", "review.md"),
    ("8 handoff", "handoff.md"),
]


def image(png: bytes) -> dict:
    return {"type": "image", "data": base64.b64encode(png).decode("ascii"), "mimeType": "image/png"}


# ── workspace ────────────────────────────────────────────────────────────────

def screen_init(machine_id: str, category: str, kind: str = "synth", name: str | None = None) -> dict:
    cats = catalog()["categories"]
    if category not in cats:
        raise ToolError(f"category must be one of: {', '.join(cats)}")
    if kind not in ("synth", "sample", "effect"):
        raise ToolError("kind is the SDK contract: synth, sample or effect")
    if cats[category]["sdkKinds"] and kind not in cats[category]["sdkKinds"]:
        raise ToolError(f"a {category} machine is SDK kind {' or '.join(cats[category]['sdkKinds'])}, not {kind}")
    d = machine_dir(machine_id, must_exist=False)
    if (d / "brief.md").exists():
        raise ToolError(f"{rel(d)} already has a brief; use screen_status")
    (d / "frames").mkdir(parents=True, exist_ok=True)
    brief = (OPXY / "templates" / "brief.md").read_text(encoding="utf-8")
    brief = brief.replace("# <Machine name>", f"# {name or machine_id}", 1)
    brief = brief.replace("| Machine id | `…` |", f"| Machine id | `{machine_id}` |", 1)
    brief = re.sub(r"\| Kind \| [^\n]*\|", f"| Kind | {kind} (the SDK contract) |", brief, count=1)
    brief = re.sub(r"\| Category \| [^\n]*\|", f"| Category | {category} (`opxy/categories.md`) |", brief, count=1)
    (d / "brief.md").write_text(brief, encoding="utf-8")
    created = [rel(d / "brief.md")]
    rest = d / "frames" / "rest.svg"
    if not rest.exists():
        shutil.copyfile(OPXY / "templates" / "frame.svg", rest)
        created.append(rel(rest))
    fits = [p for p, m in catalog()["patterns"].items() if category in m["categories"] and m["role"] == "subject"]
    return {"machine": machine_id, "created": created, "category": category, "kind": kind,
            "patternsThatFit": fits,
            "next": "Phase 0 (screen or stock page), then intake in brief.md. The subject pass is design_pass_start(kind='subject')."}


def screen_status(machine_id: str) -> dict:
    d = machine_dir(machine_id)
    phases = [{"phase": ph, "file": f, "present": (d / f).exists()} for ph, f in PHASE_FILES]
    frames = sorted(p.name for p in (d / "frames").glob("*") if FRAME_NAME.match(p.name)) if (d / "frames").is_dir() else []
    controls = sorted({int(m.group(1)) for f in frames if (m := re.match(r"c(\d+)-", f))})
    missing = [f"c{n}-{v}" for n in controls for v in ("000", "050", "100")
               if not any(f.startswith(f"c{n}-{v}.") for f in frames)]
    passes = []
    for pj in sorted((d / "passes").glob("*/pass.json")) if (d / "passes").is_dir() else []:
        from .paths import load_json
        p = load_json(pj)
        passes.append({"pass": pj.parent.name, "kind": p.get("kind"), "state": p.get("state"),
                       "picked": (p.get("selection") or {}).get("variant")})
    category = None
    if (d / "brief.md").exists():
        m = re.search(r"\| Category \| (\w+)", (d / "brief.md").read_text(encoding="utf-8"))
        category = m.group(1) if m and m.group(1) in catalog()["categories"] else None
    nxt = next((ph for ph in phases if not ph["present"]), None)
    open_pass = next((p for p in passes if p["state"] != "selected"), None)
    hint = (f"finish pass {open_pass['pass']} ({open_pass['state']})" if open_pass
            else f"next: phase {nxt['phase']} ({nxt['file']})" if nxt else "handoff exists; device checks stay pending until photographed")
    return {"machine": machine_id, "category": category, "phases": phases, "frames": frames,
            "controlsWithFrames": controls, "missingFrames": missing, "passes": passes, "next": hint}


# ── checks ───────────────────────────────────────────────────────────────────

def _frame_paths(paths: list[str] | str) -> list[Path]:
    items = [paths] if isinstance(paths, str) else list(paths or [])
    out: list[Path] = []
    for item in items:
        p = resolve(item, must_exist=False)
        if p.is_dir():
            out += sorted(p.glob("*.svg"))
        elif any(ch in str(item) for ch in "*?["):
            out += sorted(Path(x) for x in glob.glob(str(p)))
        elif p.exists():
            out.append(p)
        else:
            raise ToolError(f"not found: {item}")
    if not out:
        raise ToolError("no SVG frames matched")
    for p in out:
        resolve(p)  # confinement check on globbed results
    return out


def lint_definition(path: str, machine_json: str | None = None, kind: str | None = None, strict: bool = False) -> dict:
    argv = [resolve(path)]
    if machine_json:
        argv += ["--machine-json", resolve(machine_json)]
    if kind:
        argv += ["--kind", kind]
    if strict:
        argv.append("--strict")
    code, data = runner.run_json("lint_definition", argv)
    data["definition"] = rel(Path(data["definition"]))
    data["pass"] = code == 0
    return data


def lint_frames(paths: list[str] | str, definition: str | None = None, two_page: bool = False, own_header: bool = False,
                fragment: bool = False, strict: bool = False, tokens_path: str | None = None, summary: bool = True) -> dict:
    files = _frame_paths(paths)
    argv: list = [*files]
    if definition:
        argv += ["--definition", resolve(definition)]
    for flag, on in (("--two-page", two_page), ("--own-header", own_header), ("--fragment", fragment), ("--strict", strict)):
        if on:
            argv.append(flag)
    if tokens_path:
        argv += ["--tokens", tokens_path]
    code, data = runner.run_json("lint_frame", argv)
    for entry in data["files"]:
        entry["file"] = rel(Path(entry["file"]))
    data["pass"] = code == 0
    if summary:
        # Local models choke on hundreds of identical warnings; group them by rule and keep every error.
        rules: dict[str, dict] = {}
        for entry in data["files"]:
            for f in entry["findings"]:
                r = rules.setdefault(f"{f['level']}:{f['rule']}", {"level": f["level"], "rule": f["rule"], "count": 0,
                                                                    "example": f"{entry['file']} {f['where']}: {f['message']}"})
                r["count"] += 1
        data["byRule"] = sorted(rules.values(), key=lambda r: (r["level"] != "error", -r["count"]))
        data["files"] = [{"file": e["file"], "nodes": e["stats"].get("nodes"), "maxPoints": e["stats"].get("maxPoints"),
                          "errors": [f"{f['rule']} {f['where']}: {f['message']}" for f in e["findings"] if f["level"] == "error"][:20],
                          "warnings": sum(f["level"] == "warn" for f in e["findings"])}
                         for e in data["files"]]
    return data


def check_perceptibility(frames_dir: str, scores: list[int], names: list[str] | None = None,
                         header_bottom: int | None = None, two_page: bool = True, tokens_path: str | None = None) -> dict:
    if not scores or not all(isinstance(s, int) and 1 <= s <= 5 for s in scores):
        raise ToolError("scores are the audible scores 1–5, in control order")
    if names and len(names) != len(scores):
        raise ToolError("names must match scores one to one")
    hb = header_bottom if header_bottom is not None else (38 if two_page else 20)
    argv: list = [resolve(frames_dir), "--scores", ",".join(map(str, scores)), "--header-bottom", hb]
    if names:
        argv += ["--names", ",".join(names)]
    if tokens_path:
        argv += ["--tokens", tokens_path]
    code, data = runner.run_json("perceptibility", argv)
    data["under"] = [r["control"] for r in data["results"] if not r["ok"]]
    if data["under"]:
        data["advice"] = "Give those controls more travel or a stronger channel (phase 4). Never lower a score to pass."
    return data


def contact_sheet(frames_dir: str, out: str | None = None, png: bool = True, show: bool = True) -> list:
    src = resolve(frames_dir)
    target = resolve(out, must_exist=False) if out else src.parent / "contact.svg"
    argv: list = [src, "--out", target]
    if png:
        argv.append("--png")
    code, stdout, err = runner.run_cli("contact_sheet", argv)
    if code != 0:
        raise ToolError(err or "contact_sheet failed")
    result = {"svg": rel(target), "log": stdout.strip().splitlines(), "warning": err or None}
    pngp = target.with_suffix(".png")
    content: list = [{"type": "json", "data": result}]
    if png and show and pngp.exists():
        result["png"] = rel(pngp)
        if pngp.stat().st_size <= 4_000_000:
            content.append(image(pngp.read_bytes()))
        else:
            result["note"] = "PNG too large to attach; open it from the path"
    return content


def render_frame(path: str, scale: int = 1) -> list:
    p = resolve(path)
    if scale not in (1, 2):
        raise ToolError("scale is 1 (judge at 1:1) or 2 (inspection only)")
    if p.suffix.lower() == ".png":
        data = p.read_bytes()
    elif p.suffix.lower() == ".svg":
        data = runner.render_png(p, scale)
    else:
        raise ToolError("render_frame takes an .svg frame or a .png capture")
    note = "judge at 1:1" if scale == 1 else "2× is for inspection only; judge at 1:1"
    return [{"type": "json", "data": {"frame": rel(p), "scale": scale, "note": note}}, image(data)]


# ── audit ────────────────────────────────────────────────────────────────────

def audit_run(material_dir: str, scores: list[int] | None = None, names: list[str] | None = None,
              definition: str | None = None, two_page: bool = False, fragment: str | None = None,
              author: str | None = None, licence: str | None = None, write_report: bool = True,
              out_dir: str | None = None) -> dict:
    """Every check that applies to what's there, and a draft report where anything not run says 'not checked'.

    Outputs (contact sheet, audit-draft.md) go next to the material when it's under screens/, otherwise to
    screens/<name>/audit/, so auditing a library entry never overwrites its published files.
    """
    from .paths import screens_dir
    d = resolve(material_dir)
    sd = screens_dir().resolve()
    out = resolve(out_dir, must_exist=False) if out_dir else (d if sd in d.parents else sd / d.name / "audit")
    out.mkdir(parents=True, exist_ok=True)
    results: dict = {}
    defn = resolve(definition) if definition else (d / "definition.json" if (d / "definition.json").exists() else None)
    if defn:
        results["definition"] = lint_definition(str(defn))
    frames_dir = d / "frames" if (d / "frames").is_dir() else d
    svgs = sorted(p for p in frames_dir.glob("*.svg") if FRAME_NAME.match(p.name))
    if svgs:
        results["artwork"] = lint_frames([str(p) for p in svgs], definition=str(defn) if defn else None, two_page=two_page)
    elif fragment:
        results["artwork"] = lint_frames(fragment, definition=str(defn) if defn else None, two_page=two_page, fragment=True)
    if scores:
        results["perceptibility"] = check_perceptibility(str(frames_dir), scores, names, two_page=two_page)
    if svgs:
        try:
            content = contact_sheet(str(frames_dir), out=str(out / "contact.svg"), png=True, show=False)
            results["contactSheet"] = content[0]["data"]
        except ToolError as exc:
            results["contactSheet"] = {"error": str(exc)}

    blockers = []
    if results.get("definition", {}).get("errors"):
        blockers.append("definition has lint errors")
    if results.get("artwork", {}).get("errors"):
        blockers.append("artwork has lint errors")
    if results.get("perceptibility") and not results["perceptibility"]["pass"]:
        blockers.append("under the perceptibility floor: " + ", ".join(results["perceptibility"]["under"]))
    automated = "not yet" if blockers else "no automated blockers (verdict still needs the by-eye checks)"

    report_path = None
    if write_report:
        report_path = out / "audit-draft.md"
        report_path.write_text(_audit_report(d.name, results, author, licence, automated, blockers), encoding="utf-8")
    return {"material": rel(d), "results": results, "blockers": blockers, "automatedVerdict": automated,
            "report": rel(report_path) if report_path else None,
            "byEye": ["contact sheet at 1:1: one subject, every control reads, no dashboard",
                      "craft review beside a reference (opxy/craft.md)", "accessibility checklist",
                      "motion", "ux.md before you submit", "rights: author confirms it's theirs to share"]}


def _audit_report(name, results, author, licence, automated, blockers) -> str:
    ref = tokens()["source"]["ref"]
    today = dt.date.today().isoformat()

    def row(key, label):
        r = results.get(key)
        if r is None:
            return f"| {label} | not checked | |"
        return f"| {label} | {r.get('errors', 0)} errors, {r.get('warnings', 0)} warnings | |"

    lines = [f"# {name} · audit (draft)", "",
             "> Drafted by the operator-design MCP server from the automated checks. Everything by eye is **not checked** until someone does it.", "",
             "| | |", "| --- | --- |",
             f"| Audited | {today}, against tokens `source.ref`: {ref} |",
             f"| Author | {author or '…'} (confirmed theirs to share: not checked) |",
             f"| Licence | {licence or '…'} |",
             f"| Material | {', '.join(k for k in ('definition', 'artwork', 'perceptibility') if k in results) or 'none checked'} |",
             f"| **Verdict** | {('**not yet**' if blockers else 'pending by-eye checks')} |", "",
             "## Results", "", "| Check | Result | Evidence |", "| --- | --- | --- |",
             row("definition", "Definition (`lint_definition.py`)"),
             row("artwork", "Artwork (`lint_frame.py`)")]
    p = results.get("perceptibility")
    lines.append("| Perceptibility | " + ("not checked" if p is None else "pass" if p["pass"] else "under on: " + ", ".join(p["under"])) + " | table below |")
    lines += ["| Contact sheet, by eye | not checked | `contact.png` |", "| Accessibility checklist | not checked | |",
              "| Motion | not checked | |", "| ux.md before you submit | not checked | |", ""]
    if p:
        lines += ["### Perceptibility", "", "| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span | |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        f = lambda v: "—" if v is None else f"{v:.2f}"
        for r in p["results"]:
            lines.append(f"| {r['control']} | {r['score'] or '—'} | {r['need']:.2f} | {r['full']:.2f} | {f(r['lowHalf'])} | "
                         f"{f(r['highHalf'])} | {r['span']} | {'ok' if r['ok'] else 'UNDER'} |")
        lines.append("")
    lines += ["## What to change (for \"not yet\", most important first)", ""]
    lines += [f"{i}. {b}" for i, b in enumerate(blockers, 1)] or ["1. …"]
    lines += ["", f"Automated verdict: {automated}.", ""]
    return "\n".join(lines)
