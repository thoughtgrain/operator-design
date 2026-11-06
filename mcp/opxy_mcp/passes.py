"""Design passes: every generative pass is exactly five unique variants, each from its own direction.

Uniqueness is decided before and after drawing. Before: each variant gets a distinct direction (an angle on the
machine's own idea × a way of drawing for subjects, composition × camera × emphasis for frames), so five designers can work in
parallel without converging. After: submitted variants are compared pairwise, and a pass with near-duplicates
doesn't close.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import re
from pathlib import Path

from . import agents, runner
from .paths import ToolError, catalog, load_json, machine_dir, rel, resolve, write_json

STOP = set("a an the of and or to in on at by for with as is its it this that into from each every one their them "
           "be are was were than then so which who what where when how per".split())


def _settings() -> dict:
    return catalog()["iterations"]


def _category(d: Path, given: str | None) -> str:
    cats = catalog()["categories"]
    if given:
        if given not in cats:
            raise ToolError(f"category must be one of: {', '.join(cats)}")
        return given
    brief = d / "brief.md"
    if brief.exists():
        m = re.search(r"\| Category \| (\w+)", brief.read_text(encoding="utf-8"))
        if m and m.group(1) in cats:
            return m.group(1)
    raise ToolError("no category in brief.md; pass category (engine, drum, sampler, effect, player, sequencer, function)")


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def subject_directions(category: str, machine_id: str, exclude: list[str] | None = None, number: int = 1,
                       used: list[str] | None = None) -> list[dict]:
    """Five angle × language pairs, all on the machine's own idea. Patterns that fit the category are offered as
    inspiration in every brief, never assigned: a direction that copies a pattern's look is the failure this guards against."""
    cat, n = catalog(), _settings()["perPass"]
    angles = list(_settings()["ideaAngles"])
    langs = list(_settings()["drawingLanguages"])
    # A later pass on the same machine starts from different angles and pairings, so a pass the person turned
    # down isn't dealt the same five directions again.
    salt = "" if number <= 1 else f"#{number}"
    ra, rl = _seed(machine_id, category, "angles" + salt) % len(angles), _seed(machine_id, category + salt) % len(langs)
    angles, langs = angles[ra:] + angles[:ra], langs[rl:] + langs[:rl]
    if used:  # angles earlier passes on this machine haven't tried come first
        angles = [a for a in angles if a not in used] + [a for a in angles if a in used]
    fit = [k for k, v in cat["patterns"].items()
           if v["role"] == "subject" and category in v["categories"] and k not in (exclude or [])]
    hint = (f" Patterns that have worked for {category} machines ({', '.join(fit)}) may inspire you, but don't copy their look: "
            "no orbits, surveys or orthographic plates unless this machine's idea is one." if fit else "")
    out = []
    for k in range(n):
        angle, lang = angles[k % len(angles)], langs[k % len(langs)]
        out.append({"variant": f"v{k + 1}", "angle": angle, "drawingLanguage": lang, "inspiration": fit,
                    "brief": (f"Start from what {machine_id} is and does, not from a pattern. Your angle: {angle}. "
                              f"Way of drawing: {lang}." + hint)})
    return out


def frame_directions(machine_id: str, pass_kind: str, focus: str | None) -> list[dict]:
    axes = _settings()["frameAxes"]
    comp, cam, emph = axes["composition"], axes["camera"], axes["emphasis"]
    s = _seed(machine_id, pass_kind, focus or "")
    out = []
    # A Latin-square walk: each axis value used once, so every pair of variants differs on all three axes.
    for k in range(_settings()["perPass"]):
        c, m, e = comp[(k + s) % len(comp)], cam[(2 * k + s) % len(cam)], emph[(3 * k + s) % len(emph)]
        out.append({"variant": f"v{k + 1}", "composition": c, "camera": m, "emphasis": e,
                    "brief": f"{c}; {m}; {e}." + (f" Focus of this pass: {focus}." if focus else "")})
    return out


def design_pass_start(machine_id: str, kind: str, category: str | None = None, focus: str | None = None,
                      exclude_patterns: list[str] | None = None, run: bool = False) -> dict:
    s = _settings()
    if kind not in s["passKinds"]:
        raise ToolError(f"kind is one of: {', '.join(s['passKinds'])}")
    d = machine_dir(machine_id)
    cat = _category(d, category)
    passes = d / "passes"
    existing = sorted(passes.glob("*/pass.json")) if passes.is_dir() else []
    open_ = [p for p in existing if load_json(p).get("state") not in ("selected", "rejected")]
    if open_:
        raise ToolError(f"pass {open_[0].parent.name} is still open; submit it, then select a variant or reject the pass")
    if kind == "revision" and not focus:
        raise ToolError("a revision pass needs focus: what the review or audit sent back")
    if kind == "frames" and not any(load_json(p).get("kind") == "subject" and load_json(p).get("state") == "selected"
                                    for p in existing):
        raise ToolError("run and select a subject pass before a frames pass")
    num = len(existing) + 1
    pdir = passes / f"{num:02d}-{kind}"
    used = [d.get("angle") for p in existing for d in load_json(p).get("directions", []) if d.get("angle")]
    directions = subject_directions(cat, machine_id, exclude_patterns, num, used) if kind == "subject" else frame_directions(machine_id, kind, focus)
    if len(directions) < s["perPass"]:
        raise ToolError(f"only {len(directions)} distinct directions available; the catalog needs more patterns or languages")
    for v in directions:
        (pdir / v["variant"]).mkdir(parents=True, exist_ok=True)
    chosen_subject = None
    if kind != "subject":
        prior = [load_json(p) for p in existing if load_json(p).get("state") == "selected"]
        chosen_subject = prior[-1].get("selection") if prior else None
    record = {"machine": machine_id, "category": cat, "kind": kind, "number": num, "state": "open",
              "created": dt.datetime.now().isoformat(timespec="seconds"), "focus": focus,
              "subject": chosen_subject, "directions": directions, "variants": [], "uniqueness": None, "selection": None}
    write_json(pdir / "pass.json", record)
    briefs = [agents.designer_brief(record, v, pdir) for v in directions]
    result = {"pass": rel(pdir), "kind": kind, "category": cat, "directions": directions,
              "fanOut": "Run five designer agents in parallel, one per direction (Claude Code: the opxy-designer subagent; "
                        "Codex: opxy_designer). Each writes only into its own v<N>/ folder. Then call design_pass_submit.",
              "agentBriefs": briefs}
    if run:
        result["endpointRuns"] = agents.run_designers(record, pdir, briefs)
    return result


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in STOP and len(w) > 2}


def overlap(a: str, b: str) -> float:
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 1.0
    return len(wa & wb) / len(wa | wb)


def _approach(v: dict) -> str:
    """The direction a subject variant took: its angle on the idea, or for older candidates, its pattern."""
    return (v.get("angle") or v.get("pattern") or "").strip().lower()


def _latest_open(d: Path, pass_name: str | None) -> Path:
    if pass_name:
        p = d / "passes" / pass_name / "pass.json"
        if not p.exists():
            raise ToolError(f"no pass {pass_name}")
        return p
    passes = sorted((d / "passes").glob("*/pass.json")) if (d / "passes").is_dir() else []
    if not passes:
        raise ToolError("no passes yet; run design_pass_start")
    return passes[-1]


def design_pass_submit(machine_id: str, variants: list[dict] | None = None, pass_name: str | None = None,
                       two_page: bool = False, definition: str | None = None) -> dict:
    d = machine_dir(machine_id)
    pj = _latest_open(d, pass_name)
    rec = load_json(pj)
    if rec["state"] == "selected":
        raise ToolError(f"{pj.parent.name} is already selected; start a new pass")
    n, s = _settings()["perPass"], _settings()
    pdir = pj.parent
    problems: list[str] = []
    pairs: list[dict] = []

    if rec["kind"] == "subject":
        if not variants:  # designers may have written candidate.json into their own folders
            files = [pdir / x["variant"] / "candidate.json" for x in rec["directions"]]
            variants = [load_json(f) for f in files if f.exists()]
        if not variants or len(variants) != n:
            raise ToolError(f"a subject pass submits exactly {n} variants, one per direction")
        ids = [v.get("variant") for v in variants]
        if sorted(ids) != sorted(x["variant"] for x in rec["directions"]):
            raise ToolError(f"variant ids must be {', '.join(x['variant'] for x in rec['directions'])}")
        for v in variants:
            for key in ("drawing_language", "subject", "controls"):
                if not v.get(key):
                    problems.append(f"{v['variant']}: missing {key}")
            if not (v.get("angle") or v.get("pattern")):
                problems.append(f"{v['variant']}: missing angle (the direction it takes on the machine's idea)")
            p = (v.get("pattern") or "").upper()
            if p and p != "NONE" and p not in catalog()["patterns"]:
                problems.append(f"{v['variant']}: unknown pattern {v['pattern']} (inspiration is optional; say none)")
        for a, b in itertools.combinations(variants, 2):
            same_p = _approach(a) == _approach(b)
            same_l = (a.get("drawing_language") or "").strip().lower() == (b.get("drawing_language") or "").strip().lower()
            ov = overlap(a.get("subject", ""), b.get("subject", ""))
            same_s = ov >= s["maxSubjectOverlap"]
            differs = 3 - (same_p + same_l + same_s)
            ok = differs >= 2
            pairs.append({"pair": f"{a['variant']}–{b['variant']}", "sameAngle": same_p, "sameLanguage": same_l,
                          "subjectOverlap": round(ov, 2), "ok": ok})
            if not ok:
                problems.append(f"{a['variant']} and {b['variant']} are too alike (need to differ in two of angle, language, subject)")
        for v in variants:
            (pdir / v["variant"]).mkdir(exist_ok=True)
            write_json(pdir / v["variant"] / "candidate.json", v)
        rec["variants"] = variants
    else:
        frames = []
        for x in rec["directions"]:
            f = pdir / x["variant"] / "rest.svg"
            if not f.exists():
                problems.append(f"{x['variant']}: missing {rel(f)}")
            frames.append(f)
        if not problems:
            from .screens import lint_frames
            lum = {}
            for f in frames:
                lint = lint_frames([str(f)], definition=definition, two_page=two_page)
                if lint["errors"]:
                    problems.append(f"{f.parent.name}: {lint['errors']} lint error(s); first: {lint['byRule'][0]['example']}")
                lum[f.parent.name] = runner.luminance(f)
            top = 38 if two_page else 20
            for a, b in itertools.combinations(sorted(lum), 2):
                pct = runner.body_diff_pct(lum[a], lum[b], top)
                ok = pct >= s["minPairwiseBodyDiffPct"]
                pairs.append({"pair": f"{a}–{b}", "bodyDiffPct": round(pct, 2), "ok": ok})
                if not ok:
                    problems.append(f"{a} and {b} differ on only {pct:.2f}% of the body (need ≥ {s['minPairwiseBodyDiffPct']}%)")
        rec["variants"] = [{"variant": f.parent.name, "frame": rel(f)} for f in frames if f.exists()]
        if variants:  # optional notes per variant
            notes = {v.get("variant"): v for v in variants}
            for v in rec["variants"]:
                v.update({k: val for k, val in notes.get(v["variant"], {}).items() if k != "variant"})

    rec["uniqueness"] = {"pairs": pairs, "problems": problems,
                         "checked": dt.datetime.now().isoformat(timespec="seconds")}
    rec["state"] = "needs_revision" if problems else "ready_for_pick"
    write_json(pj, rec)
    return {"pass": rel(pdir), "state": rec["state"], "problems": problems, "pairs": pairs,
            "next": ("Revise the weakest duplicate into a new direction and submit again; never drop below five."
                     if problems else
                     "Show the five to the person side by side at 1:1 (contact_sheet on the pass folder for frames) and ask them to pick. Then design_pass_select.")}


def design_pass_select(machine_id: str, variant: str, reason: str, chosen_by: str, pass_name: str | None = None,
                       apply: bool = False) -> dict:
    d = machine_dir(machine_id)
    pj = _latest_open(d, pass_name)
    rec = load_json(pj)
    if rec["state"] != "ready_for_pick":
        raise ToolError(f"{pj.parent.name} is {rec['state']}; it needs five unique variants before a pick")
    if variant not in {v["variant"] for v in rec["variants"]}:
        raise ToolError(f"variant must be one of: {', '.join(v['variant'] for v in rec['variants'])}")
    if not reason or not chosen_by:
        raise ToolError("record who picked it and why; the pick is the person's")
    picked = next(v for v in rec["variants"] if v["variant"] == variant)
    rec["selection"] = {"variant": variant, "reason": reason, "chosenBy": chosen_by,
                        "at": dt.datetime.now().isoformat(timespec="seconds"), **picked}
    rec["state"] = "selected"
    applied = None
    if apply and rec["kind"] != "subject":
        src = pj.parent / variant / "rest.svg"
        dst = d / "frames" / "rest.svg"
        dst.parent.mkdir(exist_ok=True)
        dst.write_bytes(src.read_bytes())
        applied = rel(dst)
    write_json(pj, rec)
    return {"pass": rel(pj.parent), "selected": variant, "applied": applied,
            "next": ("Fill brief.md section 3 with the five candidates and the pick, then phase 4 (map and budget)."
                     if rec["kind"] == "subject" else
                     "Draw the full frame set from the picked rest frame (phase 5), then lint, perceptibility and contact sheet.")}


def design_pass_reject(machine_id: str, reason: str, chosen_by: str, pass_name: str | None = None) -> dict:
    """The person saw the five and wants none of them. Closes the pass so a new one can start; nothing is picked."""
    d = machine_dir(machine_id)
    pj = _latest_open(d, pass_name)
    rec = load_json(pj)
    if rec["state"] == "selected":
        raise ToolError(f"{pj.parent.name} already has a pick ({rec['selection']['variant']})")
    if not reason or not chosen_by:
        raise ToolError("record who turned the pass down and why; the next pass starts from that reason")
    rec["state"] = "rejected"
    rec["rejection"] = {"reason": reason, "chosenBy": chosen_by, "at": dt.datetime.now().isoformat(timespec="seconds")}
    write_json(pj, rec)
    return {"pass": rel(pj.parent), "state": "rejected",
            "next": "Start a new pass with design_pass_start; put the reason in focus so the five new directions answer it."}


def design_pass_get(machine_id: str, pass_name: str | None = None) -> dict:
    d = machine_dir(machine_id)
    pj = _latest_open(d, pass_name)
    return {"path": rel(pj), **load_json(pj)}
