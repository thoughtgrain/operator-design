#!/usr/bin/env python3
"""Review a machine's definition.json against open-xy's contract and UX rules.

Two layers:
  structure  mirrors the main rules of open-xy tooling/definitions.py (the SDK's
             validator stays the authority; run `sdk.py test` before shipping)
  review     ux.md and api.md conventions the validator can't judge: clean
             defaults, engine-page scope, page layout, sdk version needs,
             display budget against the screen brief

Usage:
    python3 opxy/tools/lint_definition.py path/to/definition.json
        [--machine-json PATH] [--kind synth|sample|effect] [--strict] [--json]

machine.json beside the definition is read automatically for kind and sdk.
Exit codes: 0 clean (warnings allowed unless --strict), 1 findings at error
level, 2 usage, I/O or parse failure.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DISPLAY_FORMATS = ("ratio", "percent", "bipolar", "duration", "semitones", "enum", "division")
DISPLAY_LIMITS = {"paths": (0, 4), "points": (0, 64), "nodes": (1, 256), "texts": (0, 16), "palette": (1, 16)}
CONTROLS = {"synth": (4, 8), "sample": (1, 8), "effect": (1, 8)}
RESOURCES = {
    "synth": ("voiceBytes", "voiceAlignment", "voiceCapacity", "sharedBytes", "outputPeakQ31", "display"),
    "sample": ("voiceCapacity",),
    "effect": (),
}
LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ]{0,7}$")
MACHINE_ID = re.compile(r"^[a-z][a-z0-9_]{0,14}$")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ENUM_LABEL = re.compile(r"^[A-Za-z0-9 .:*+_-]{1,15}$")

# ux.md: controls that colour or degrade the sound default to off.
COLOURING = re.compile(r"crush|bits?\b|drift|noise|nois|drive|driv|dirt|grit|dust|wow|flutter|"
                       r"distort|satur|fuzz|mod|depth|aphx|chaos|random|rand|glitch|lofi|wobble", re.I)
# ux.md: the engine page holds the sound's own parameters, not another envelope/LFO/mod amount.
STOCK_DUTY = re.compile(r"^(attack|att|decay|dcy|dec|sustain|sus|release|rel|env|lfo|lfo ?rate|lfo ?depth)$", re.I)


@dataclass
class Finding:
    level: str  # "error" | "warn" | "note"
    where: str
    rule: str
    message: str


class Review:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, level: str, where: str, rule: str, message: str) -> None:
        self.findings.append(Finding(level, where, rule, message))

    def require(self, ok: bool, where: str, rule: str, message: str) -> bool:
        if not ok:
            self.add("error", where, rule, message)
        return ok


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def sdk_tuple(v) -> tuple[int, ...] | None:
    if not isinstance(v, str):
        return None
    try:
        return tuple(int(p) for p in v.split("."))
    except ValueError:
        return None


def check_mapping(r: Review, where: str, p: dict) -> None:
    m = p.get("mapping")
    if not r.require(isinstance(m, dict), where, "mapping", "mapping must be an object"):
        return
    kind = m.get("kind")
    r.require((p.get("display") == "enum") == (kind == "enum"), where, "mapping", "enum mapping and enum display must go together")
    expected = {
        "linear": ("kind", "minimum", "maximum"),
        "anchors": ("kind", "values"),
        "power": ("kind", "maximum", "exponent"),
        "exponential": ("kind", "minimum", "maximum"),
        "enum": ("kind", "labels"),
    }
    if not r.require(kind in expected, where, "mapping", f"unsupported mapping kind {kind!r}"):
        return
    extra = set(m) - set(expected[kind])
    missing = set(expected[kind]) - set(m)
    r.require(not extra and not missing, where, "mapping",
              f"{kind} mapping needs exactly {list(expected[kind])} (missing {sorted(missing)}, unknown {sorted(extra)})")
    if missing:
        return
    if kind == "linear":
        if r.require(is_number(m["minimum"]) and is_number(m["maximum"]), where, "mapping", "linear bounds must be numbers"):
            r.require(m["minimum"] < m["maximum"], where, "mapping", "linear mapping must increase (clockwise goes up)")
    elif kind == "anchors":
        vals = m["values"]
        if r.require(isinstance(vals, list) and 3 <= len(vals) <= 256 and all(is_number(v) for v in vals),
                     where, "mapping", "anchors need 3..256 numbers; use linear for two"):
            r.require(all(a < b for a, b in zip(vals, vals[1:])), where, "mapping", "anchors must increase")
    elif kind == "power":
        r.require(is_number(m["maximum"]) and 0 <= m["maximum"], where, "mapping", "power maximum must be ≥ 0")
        r.require(is_number(m["exponent"]) and 0.01 <= m["exponent"] <= 32 and m["exponent"] != 1,
                  where, "mapping", "power exponent in 0.01..32 and not 1 (that's linear)")
    elif kind == "exponential":
        r.require(is_number(m["minimum"]) and m["minimum"] > 0 and is_number(m["maximum"]) and m["maximum"] >= m["minimum"],
                  where, "mapping", "exponential needs 0 < minimum ≤ maximum")
    elif kind == "enum":
        labels = m["labels"]
        r.require(isinstance(labels, list) and 2 <= len(labels) <= 256 and len(set(labels)) == len(labels)
                  and all(isinstance(s, str) and ENUM_LABEL.match(s) for s in labels),
                  where, "mapping", "enum labels: 2..256 unique strings of ≤ 15 plain characters")
        if isinstance(labels, list):
            long = [s for s in labels if isinstance(s, str) and len(s) > 5]
            if long:
                r.add("warn", where, "caption-width",
                      f"enum labels over ~5 characters may not fit the 20 px header column: {long[:4]}")
    if p.get("display") == "division":
        r.require(m == {"kind": "linear", "minimum": 0, "maximum": 1}, where, "mapping", "a division control maps linearly 0..1")


def review(defn: dict, kind: str, sdk: tuple[int, ...] | None) -> Review:
    r = Review()
    top = {"schema", "id", "name", "parameters", "presets", "resources"} | ({"press"} if "press" in defn else set())
    r.require(set(defn) == top, "definition", "fields",
              f"fields must be exactly {sorted(top)} (unknown {sorted(set(defn) - top)}, missing {sorted(top - set(defn))})")
    r.require(defn.get("schema") == 1, "definition", "schema", "schema must be 1")
    r.require(isinstance(defn.get("id"), str) and bool(MACHINE_ID.match(defn.get("id", ""))), "definition", "id",
              "id: a lowercase letter, then letters, digits or _, at most 15. It never changes once published")

    params = defn.get("parameters")
    if not r.require(isinstance(params, list), "parameters", "parameters", "parameters must be a list"):
        return r
    lo, hi = CONTROLS[kind]
    r.require(lo <= len(params) <= hi, "parameters", "count", f"{kind} needs {lo}..{hi} parameters (has {len(params)})")

    ids: list[str] = []
    positions: list[int] = []
    for i, p in enumerate(params):
        where = f"parameters[{i}]" + (f" {p.get('id')}" if isinstance(p, dict) else "")
        if not r.require(isinstance(p, dict), where, "parameter", "parameter must be an object"):
            continue
        alternate = kind in ("synth", "effect") and i >= 4
        named = alternate and (kind == "synth" or "control" in p)
        want = {"id", "label", "default", "mapping", "display"} | ({"control"} if named else set())
        r.require(set(p) == want, where, "fields",
                  f"needs exactly {sorted(want)} (unknown {sorted(set(p) - want)}, missing {sorted(want - set(p))})")
        pid = p.get("id")
        if r.require(isinstance(pid, str) and bool(IDENT.match(pid)), where, "id", "parameter id must be an identifier"):
            r.require(pid not in ids, where, "id", "duplicate parameter id")
            ids.append(pid)
        label = p.get("label", "")
        r.require(isinstance(label, str) and bool(LABEL.match(label)), where, "label",
                  f"label {label!r}: at most eight letters, digits or spaces")
        d = p.get("default")
        r.require(is_number(d) and 0 <= d <= 1, where, "default", "default must be a number in [0, 1]")
        r.require(p.get("display") in DISPLAY_FORMATS, where, "display", f"display must be one of {DISPLAY_FORMATS}")
        check_mapping(r, where, p)
        if named:
            c = p.get("control")
            r.require(isinstance(c, int) and not isinstance(c, bool) and 0 <= c < 4, where, "control", "alternate names control 0..3")
            positions.append(c if isinstance(c, int) else -1)
        elif alternate:
            positions.append(i - 4)

        # review layer
        if isinstance(label, str) and COLOURING.search(label) and is_number(d) and d > 0:
            r.add("warn", where, "clean-defaults",
                  f"{label!r} reads like a colouring/degrading control but defaults to {d}; ux.md asks these to default off")
        if isinstance(label, str) and STOCK_DUTY.match(label.strip()):
            r.add("warn", where, "engine-scope",
                  f"{label!r} looks like an envelope/LFO control; the OP-XY already has those. Keep it only if it's the sound's own (say why in the brief)")
        if p.get("display") == "percent" and isinstance(p.get("mapping"), dict) and p["mapping"].get("kind") == "linear":
            mn, mx = p["mapping"].get("minimum"), p["mapping"].get("maximum")
            if is_number(mn) and is_number(mx) and (mn, mx) != (0, 1):
                r.add("warn", where, "real-units",
                      f"percent display over a {mn}..{mx} range; the header will show 0–100, not the real unit. Consider ratio/semitones/duration or header text")

    # pages
    if "press" in defn:
        r.require(defn["press"] == "page" and kind == "synth" and 5 <= len(params) <= 8 and len(set(positions)) == len(positions),
                  "press", "pages", '"press": "page" needs 5..8 synth parameters and at most one alternate per position')
        if sdk:
            if len(params) == 8:
                r.require(sdk >= (1, 3), "press", "sdk", "eight-parameter pages need sdk 1.3+")
            elif sdk < (1, 4):
                r.add("error", "press", "sdk", "partial second pages (5–7 parameters) need sdk 1.4+")
    elif kind == "synth" and len(params) > 4:
        r.add("warn", "press", "pages",
              'five or more synth parameters without "press": "page"; ux.md asks for two pages and the shared header')

    # presets
    presets = defn.get("presets")
    if r.require(isinstance(presets, dict) and len(presets) <= 64, "presets", "presets", "presets must be an object of ≤ 64"):
        for name, preset in presets.items():
            where = f"presets.{name}"
            if not r.require(isinstance(preset, dict), where, "preset", "preset must be an object"):
                continue
            r.require(set(preset) == set(ids), where, "preset",
                      f"must hold exactly the declared controls (missing {sorted(set(ids) - set(preset))}, unknown {sorted(set(preset) - set(ids))})")
            bad = [k for k, v in preset.items() if not (is_number(v) and 0 <= v <= 1)]
            r.require(not bad, where, "preset", f"values must be in [0, 1]: {bad}")
        if not presets:
            r.add("note", "presets", "presets", "no presets; ux.md wants presets that sound good straight away")

    # resources
    res = defn.get("resources")
    if r.require(isinstance(res, dict), "resources", "resources", "resources must be an object"):
        need = set(RESOURCES[kind])
        if kind == "synth":
            r.require(need <= set(res), "resources", "resources", f"synth resources need {sorted(need)} (missing {sorted(need - set(res))})")
            vb, va = res.get("voiceBytes"), res.get("voiceAlignment")
            if isinstance(vb, int) and isinstance(va, int):
                r.require(vb >= 4 and va in (4, 8, 16) and vb % va == 0, "resources", "voice", "voiceBytes whole words, alignment 4/8/16")
            cap = res.get("voiceCapacity")
            if isinstance(cap, int):
                r.require(1 <= cap <= 256, "resources", "voice", "voiceCapacity 1..256")
                if cap < 8:
                    r.add("warn", "resources", "voice", f"voiceCapacity {cap}; stock plays up to 8 notes per track")
            disp = res.get("display")
            if isinstance(disp, dict):
                for f, (a, b) in DISPLAY_LIMITS.items():
                    v = disp.get(f)
                    r.require(isinstance(v, int) and a <= v <= b, "resources.display", "display", f"{f} must be {a}..{b} (got {v!r})")
                if isinstance(disp.get("paths"), int) and isinstance(disp.get("points"), int):
                    r.require((disp["points"] >= 2) == (disp["paths"] > 0), "resources.display", "display",
                              "paths have 2..64 points; a display without paths declares 0 points")
                sb, sa = disp.get("stateBytes"), disp.get("stateAlignment")
                r.require(isinstance(sb, int) and isinstance(sa, int) and sb >= 4 and sa in (4, 8, 16) and sb % sa == 0,
                          "resources.display", "display", "stateBytes whole words with alignment 4/8/16")
                texts = disp.get("texts")
                if isinstance(texts, int) and texts > 4 and sdk is not None:
                    r.require(sdk >= (1, 3), "resources.display", "sdk", "more than 4 text slots need sdk 1.3+")
                if "press" in defn and isinstance(texts, int) and texts < 16:
                    r.add("note", "resources.display", "header",
                          "two pages without 16 text slots: fine with the stock header, but page_header.hpp takes all sixteen")
        else:
            r.add("note", "resources", "resources", f"{kind} resources not reviewed beyond structure; check api.md")
    return r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Review definition.json against open-xy's contract and UX rules.")
    ap.add_argument("definition", type=Path)
    ap.add_argument("--machine-json", type=Path, help="machine.json (default: beside the definition)")
    ap.add_argument("--kind", choices=sorted(CONTROLS), help="override the kind from machine.json")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        defn = json.loads(args.definition.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"lint_definition: file not found: {args.definition}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"lint_definition: not valid JSON ({args.definition}): {exc}", file=sys.stderr)
        return 2
    if not isinstance(defn, dict):
        print("lint_definition: definition must be a JSON object", file=sys.stderr)
        return 2

    mj_path = args.machine_json or args.definition.with_name("machine.json")
    machine: dict = {}
    if mj_path.exists():
        try:
            machine = json.loads(mj_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"lint_definition: machine.json is not valid JSON ({mj_path}): {exc}", file=sys.stderr)
            return 2
    elif args.machine_json:
        print(f"lint_definition: file not found: {mj_path}", file=sys.stderr)
        return 2
    kind = args.kind or machine.get("kind") or "synth"
    sdk = sdk_tuple(machine.get("sdk"))

    r = review(defn, kind, sdk)
    errors = sum(f.level == "error" for f in r.findings)
    warns = sum(f.level == "warn" for f in r.findings)
    if args.json:
        print(json.dumps({"definition": str(args.definition), "kind": kind, "sdk": machine.get("sdk"),
                          "errors": errors, "warnings": warns, "findings": [asdict(f) for f in r.findings]}, indent=2))
    else:
        n = len(defn.get("parameters", [])) if isinstance(defn.get("parameters"), list) else 0
        print(f"{args.definition}  kind={kind} sdk={machine.get('sdk', '?')} parameters={n}")
        for f in r.findings:
            mark = {"error": "E", "warn": "W", "note": "·"}[f.level]
            print(f"  {mark} {f.rule:<15} {f.where}: {f.message}")
        print(f"{errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
