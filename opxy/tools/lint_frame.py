#!/usr/bin/env python3
"""Pre-flight lint for OP-XY machine screen frames (480 x 220 SVG).

Checks authored artwork against the device drawing rules in opxy/constraints.md
(which trace to open-xy docs/display.md and docs/ux.md). It's a design-stage
check: open-xy's `sdk.py test` and photos of the real screen stay the authority.

Usage:
    python3 opxy/tools/lint_frame.py FRAME.svg [FRAME.svg ...]
        [--fragment] [--two-page] [--own-header] [--strict] [--json]
        [--tokens PATH]

Exit codes: 0 clean (warnings allowed unless --strict), 1 lint errors,
2 usage, I/O or parse failure.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "tokens.json"

# Elements the device docs and stock template use. Anything else is either
# rejected outright or unverified on hardware.
SUPPORTED = {"svg", "g", "path", "circle", "rect", "text", "title", "desc", "metadata"}
REJECTED = {
    "linearGradient", "radialGradient", "filter", "mask", "clipPath", "use",
    "style", "image", "pattern", "symbol", "foreignObject", "script",
    "animate", "animateTransform", "animateMotion", "set", "marker", "defs",
}
UNVERIFIED = {"line", "polyline", "polygon", "ellipse", "tspan"}
PAINTED = {"path", "circle", "rect", "text", "line", "polyline", "polygon", "ellipse"}
NUMERIC_ATTRS = {
    "d", "transform", "x", "y", "cx", "cy", "r", "rx", "ry", "width", "height",
    "stroke-width", "font-size", "points", "x1", "y1", "x2", "y2", "viewBox",
}
BROWSER_ONLY_ATTRS = {"style", "class", "opacity", "fill-opacity", "stroke-opacity",
                      "filter", "mask", "clip-path", "stroke-dasharray"}

NUM = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
PATH_TOKEN = re.compile(rf"[MmLlHhVvCcSsQqTtAaZz]|{NUM}")
EXPONENT = re.compile(r"\d[eE][-+]?\d")
LONG_FRACTION = re.compile(r"\d\.(\d+)")
IDENTITY_TRANSLATE = re.compile(rf"^\s*matrix\(\s*1[\s,]+0[\s,]+0[\s,]+1[\s,]+({NUM})[\s,]+({NUM})\s*\)\s*$")
TRANSLATE = re.compile(rf"^\s*translate\(\s*({NUM})(?:[\s,]+({NUM}))?\s*\)\s*$")
BOUND_ID = re.compile(r"^(?P<prefix>[A-Za-z0-9]+)_(?P<kind>node|text|palette)_(?P<index>\d+)$")
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
NAMED = {"black": "#000000", "white": "#FFFFFF", "gray": "#808080", "grey": "#808080",
         "silver": "#C0C0C0", "red": "#FF0000"}
ARG_COUNT = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


@dataclass
class Finding:
    file: str
    level: str  # "error" | "warn"
    where: str
    rule: str
    message: str


class LintError(Exception):
    """Raised for problems that stop linting a file (I/O, XML parse, bad tokens)."""


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def load_tokens(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LintError(f"tokens file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LintError(f"tokens file is not valid JSON ({path}): {exc}") from exc


def normalize_colour(value: str) -> str | None:
    """Return #RRGGBB, 'none', or None when the value can't be resolved."""
    v = value.strip()
    if v.lower() == "none":
        return "none"
    if HEX.match(v):
        if len(v) == 4:
            v = "#" + "".join(ch * 2 for ch in v[1:])
        return v.upper()
    if v.lower() in NAMED:
        return NAMED[v.lower()]
    m = re.match(r"^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", v)
    if m:
        r, g, b = (max(0, min(255, int(x))) for x in m.groups())
        return f"#{r:02X}{g:02X}{b:02X}"
    return None


def parse_path(d: str) -> tuple[list[dict], list[str]]:
    """Split path data into subpaths of absolute endpoints.

    Returns (subpaths, commands). Each subpath is {"points": [(x, y)...],
    "closed": bool}. Curve endpoints and control points are kept for bounds;
    only endpoints count as points.
    """
    tokens = PATH_TOKEN.findall(d)
    subpaths: list[dict] = []
    commands: list[str] = []
    cx = cy = 0.0
    start = (0.0, 0.0)
    cmd = None
    i = 0
    current: dict | None = None
    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            i += 1
            commands.append(cmd)
            if cmd in "Zz":
                if current is not None:
                    current["closed"] = True
                cx, cy = start
                current = None
                continue
        elif cmd is None:
            raise LintError(f"path data starts with a number: {d[:40]!r}")
        up = cmd.upper()
        n = ARG_COUNT[up]
        args = tokens[i:i + n]
        if len(args) < n or any(a.isalpha() for a in args):
            raise LintError(f"incomplete {cmd} segment in path data: {d[:60]!r}")
        vals = [float(a) for a in args]
        i += n
        rel = cmd.islower()
        if up == "M":
            x, y = (cx + vals[0], cy + vals[1]) if rel else (vals[0], vals[1])
            current = {"points": [(x, y)], "closed": False, "extra": []}
            subpaths.append(current)
            start = (x, y)
            cx, cy = x, y
            cmd = "l" if rel else "L"  # implicit lineto after moveto
            continue
        if current is None:  # drawing after Z without a new M starts at start point
            current = {"points": [(cx, cy)], "closed": False, "extra": []}
            subpaths.append(current)
        if up == "L" or up == "T":
            x, y = (cx + vals[0], cy + vals[1]) if rel else (vals[0], vals[1])
        elif up == "H":
            x, y = (cx + vals[0] if rel else vals[0]), cy
        elif up == "V":
            x, y = cx, (cy + vals[0] if rel else vals[0])
        elif up == "A":
            x, y = (cx + vals[5], cy + vals[6]) if rel else (vals[5], vals[6])
        else:  # C, S, Q: last pair is the endpoint, the rest are controls
            pairs = [(vals[k], vals[k + 1]) for k in range(0, n, 2)]
            if rel:
                pairs = [(cx + px, cy + py) for px, py in pairs]
            current["extra"].extend(pairs[:-1])
            x, y = pairs[-1]
        current["points"].append((x, y))
        cx, cy = x, y
    return subpaths, commands


def translation(transform: str | None) -> tuple[float, float] | None:
    """Offset for identity-matrix or translate transforms; None if anything else."""
    if not transform:
        return (0.0, 0.0)
    m = IDENTITY_TRANSLATE.match(transform) or TRANSLATE.match(transform)
    if not m:
        return None
    x = float(m.group(1))
    y = float(m.group(2)) if m.group(2) else 0.0
    return (x, y)


def angle_turn_back(a: tuple, b: tuple, c: tuple) -> float | None:
    """Degrees short of a full reversal at b (0 = straight back). None if degenerate."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return None
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return 180.0 - math.degrees(math.acos(cos))


class FrameLinter:
    def __init__(self, tokens: dict, *, fragment: bool, two_page: bool, own_header: bool):
        self.t = tokens
        self.fragment = fragment
        self.header_bottom = tokens["header"]["twoPage" if two_page else "stock"]["bottom"]
        self.own_header = own_header
        self.known_greys = {k.upper() for k in tokens["greys"]}

    # -- entry --------------------------------------------------------------
    def lint(self, path: Path) -> tuple[list[Finding], dict]:
        self.file = str(path)
        self.findings: list[Finding] = []
        self.stats = {"nodes": 0, "texts": 0, "palette": 0, "maxPoints": 0, "prefixes": set()}
        try:
            root = ET.parse(path).getroot()
        except FileNotFoundError as exc:
            raise LintError(f"file not found: {path}") from exc
        except ET.ParseError as exc:
            raise LintError(f"not well-formed XML ({path}): {exc}") from exc
        if local(root.tag) != "svg":
            raise LintError(f"root element is <{local(root.tag)}>, expected <svg> ({path})")
        if not self.fragment:
            self.check_canvas(root)
        seen_ids: dict[str, int] = {}
        self.walk(root, seen_ids, inherited_offset=(0.0, 0.0))
        for ident, count in seen_ids.items():
            if count > 1:
                self.add("error", ident, "unique-id", f"id used {count} times; device binds by id")
        if len(self.stats["prefixes"]) > 1:
            self.add("warn", "svg", "one-prefix",
                     f"bound ids use several prefixes {sorted(self.stats['prefixes'])}; a machine uses one")
        stats = dict(self.stats, prefixes=sorted(self.stats["prefixes"]))
        return self.findings, stats

    def add(self, level: str, where: str, rule: str, message: str) -> None:
        self.findings.append(Finding(self.file, level, where, rule, message))

    # -- canvas -------------------------------------------------------------
    def check_canvas(self, root: ET.Element) -> None:
        w, h = self.t["canvas"]["width"], self.t["canvas"]["height"]
        vb = (root.get("viewBox") or "").replace(",", " ").split()
        try:
            vb_ok = [float(v) for v in vb] == [0, 0, w, h]
        except ValueError:
            vb_ok = False
        if not vb_ok:
            self.add("error", "svg", "canvas", f'viewBox must be "0 0 {w} {h}" (got {root.get("viewBox")!r})')
        for attr, want in (("width", w), ("height", h)):
            got = root.get(attr)
            if got is not None and got.replace("px", "").strip() != str(want):
                self.add("error", "svg", "canvas", f"{attr} must be {want} (got {got!r}); judge frames at 1:1")

    # -- tree ---------------------------------------------------------------
    def walk(self, el: ET.Element, seen_ids: dict, inherited_offset: tuple) -> None:
        tag = local(el.tag)
        ident = el.get("id")
        where = f"<{tag}{' #' + ident if ident else ''}>"
        if ident:
            seen_ids[ident] = seen_ids.get(ident, 0) + 1
        if tag == "g" and ident and ident.startswith("preview_"):
            return  # preview-only scaffolding (stock header stand-in); never shipped

        if tag in REJECTED:
            self.add("error", where, "unsupported-element", f"<{tag}> isn't drawn by the device; author it as plain shapes")
            return
        if tag in UNVERIFIED:
            self.add("warn", where, "unverified-element", f"<{tag}> isn't in the device docs; prefer <path>/<circle>/<rect>")
        elif tag not in SUPPORTED:
            self.add("warn", where, "unknown-element", f"<{tag}> is unknown here; check it on the device")

        self.check_attributes(el, tag, where)

        offset = translation(el.get("transform"))
        abs_offset = None if offset is None or inherited_offset is None else (
            inherited_offset[0] + offset[0], inherited_offset[1] + offset[1])

        if tag == "g":
            for attr in ("fill", "stroke", "stroke-width", "font-family", "font-size"):
                if el.get(attr) is not None:
                    self.add("warn", where, "no-inheritance", f"group sets {attr}; the device doesn't inherit group styles, set it on each leaf")

        bound = BOUND_ID.match(ident) if ident else None
        if bound:
            self.stats["prefixes"].add(bound["prefix"])

        if tag in PAINTED:
            self.check_paint(el, tag, where, bound)
        if tag == "path":
            self.check_path(el, where, bound, abs_offset)
        elif tag in ("circle", "rect"):
            self.check_simple_shape(el, tag, where, bound, abs_offset)
        elif tag == "text":
            self.check_text(el, where, bound)

        if bound:
            kind = bound["kind"]
            self.stats["nodes" if kind == "node" else "texts" if kind == "text" else "palette"] += 1
            if kind in ("node", "text"):
                t = el.get("transform")
                if t and not IDENTITY_TRANSLATE.match(t):
                    self.add("error", where, "bound-transform", f"bound element transform must be matrix(1 0 0 1 x y) or none (got {t!r})")

        for child in el:
            self.walk(child, seen_ids, abs_offset)

    def check_attributes(self, el: ET.Element, tag: str, where: str) -> None:
        for raw_name, value in el.attrib.items():
            name = local(raw_name)
            if name in BROWSER_ONLY_ATTRS:
                level = "error" if name in ("style", "class", "filter", "mask", "clip-path") else "warn"
                self.add(level, where, "browser-only", f"{name}= isn't supported on the device; use explicit fill/stroke attributes")
            if name == "href" or name.endswith("href"):
                self.add("error", where, "no-references", "references aren't supported; draw the element in place")
            if name in NUMERIC_ATTRS:
                if EXPONENT.search(value):
                    self.add("error", where, "number-format", f"{name} uses exponent notation")
                for frac in LONG_FRACTION.findall(value):
                    if len(frac) > self.t["device"]["maxFractionDigits"]:
                        self.add("error", where, "number-format",
                                 f"{name} has a number with more than {self.t['device']['maxFractionDigits']} fractional digits")
                        break

    # -- paint --------------------------------------------------------------
    def check_paint(self, el: ET.Element, tag: str, where: str, bound) -> None:
        for attr in ("fill", "stroke"):
            value = el.get(attr)
            if value is None:
                self.add("error", where, "explicit-paint", f"missing {attr}=; every leaf needs explicit paint (use \"none\" for no {attr})")
                continue
            self.check_colour(value, where, attr)
        if el.get("stroke", "none").strip().lower() != "none":
            sw = el.get("stroke-width")
            if sw is None:
                self.add("error", where, "explicit-paint", "stroke set without stroke-width")
            else:
                try:
                    width = float(sw.replace("px", ""))
                except ValueError:
                    self.add("error", where, "explicit-paint", f"stroke-width isn't a number ({sw!r})")
                else:
                    if not (bound and bound["kind"] == "palette") and width < self.t["legibility"]["secondaryStrokeMin"]:
                        self.add("warn", where, "legibility", f"stroke-width {width} is under {self.t['legibility']['secondaryStrokeMin']} px; thin lines vanish at 1:1")

    def check_colour(self, value: str, where: str, attr: str) -> None:
        if value.strip().lower() == "currentcolor":
            self.add("error", where, "explicit-paint", f"{attr}=currentColor relies on inheritance")
            return
        hexv = normalize_colour(value)
        if hexv is None:
            self.add("error", where, "colour", f"{attr}={value!r} isn't a colour the device can use; write #RRGGBB")
            return
        if hexv == "none":
            return
        r, g, b = int(hexv[1:3], 16), int(hexv[3:5], 16), int(hexv[5:7], 16)
        if not (r == g == b):
            if r > g + 40 and r > b + 40:
                self.add("error", where, "no-red", f"{attr} {hexv} is reddish; red is reserved for stock recording and p-locks")
            else:
                self.add("error", where, "grey-only", f"{attr} {hexv} isn't grey; OP-XY screen graphics are greyscale")
        elif hexv not in self.known_greys:
            self.add("warn", where, "palette", f"{attr} {hexv} is grey but not in tokens.json; prefer the stock greys")

    # -- geometry -----------------------------------------------------------
    def check_path(self, el: ET.Element, where: str, bound, offset) -> None:
        d = el.get("d")
        if not d:
            self.add("error", where, "path", "path has no d=")
            return
        try:
            subpaths, commands = parse_path(d)
        except LintError as exc:
            self.add("error", where, "path", str(exc))
            return
        if not subpaths:
            self.add("error", where, "path", "path draws nothing")
            return
        dev = self.t["device"]
        if len(subpaths) > dev["maxSubpaths"]:
            self.add("error", where, "one-subpath", f"{len(subpaths)} subpaths; the device needs one per path. Split into elements")
        sp = subpaths[0]
        pts = sp["points"]
        # A closed path that ends on its start point repeats it; don't count that twice.
        if sp["closed"] and len(pts) > 1 and math.dist(pts[0], pts[-1]) == 0:
            pts = pts[:-1]
        self.stats["maxPoints"] = max(self.stats["maxPoints"], len(pts))
        if len(pts) > dev["maxPointsPerPath"]:
            self.add("error", where, "max-points", f"{len(pts)} points; at most {dev['maxPointsPerPath']} per path")

        is_node = bound is not None and bound["kind"] == "node"
        outline_level = "error" if is_node else "warn"

        if is_node:
            letters = "".join(commands).upper()
            if not re.fullmatch(r"ML*Z", letters):
                self.add("error", where, "bound-topology", "bound path must be exactly M, L…, Z (no H/V/curves)")
            if el.get("fill", "").strip().lower() != "none":
                self.add("error", where, "bound-topology", "bound (mutable) path must have fill=\"none\"; mutable outlines draw hollow")

        if not sp["closed"] and el.get("stroke", "none").lower() != "none":
            self.add(outline_level, where, "closed-ribbon",
                     "open stroked path; the device draws streaks from open/out-and-back lines. Draw a thin closed ribbon")

        if len(pts) >= 2:
            seen = set()
            for p in pts:
                key = (round(p[0], 4), round(p[1], 4))
                if key in seen:
                    self.add(outline_level, where, "distinct-points", f"repeated point {key}; the device merges repeats and stops reshaping")
                    break
                seen.add(key)
            ring = pts + [pts[0]] if sp["closed"] else pts
            for a, b in zip(ring, ring[1:]):
                gap = math.dist(a, b)
                if 0 < gap < dev["minPointSpacing"]:
                    self.add(outline_level, where, "point-spacing", f"points {gap:.4f} px apart; keep ≥ {dev['minPointSpacing']} px")
                    break
            if sp["closed"] and len(pts) >= 3:
                closing = math.dist(pts[-1], pts[0])
                if 0 < closing < dev["minClosingEdge"]:
                    self.add(outline_level, where, "closing-edge",
                             f"closing edge {closing:.4f} px; start the outline where both edges are long (≥ {dev['minClosingEdge']} px)")
            corners = pts + pts[:2] if sp["closed"] else pts
            for a, b, c in zip(corners, corners[1:], corners[2:]):
                short = angle_turn_back(a, b, c)
                if short is not None and short < dev["nearReversalDeg"]:
                    self.add(outline_level, where, "near-reversal",
                             f"turn at {tuple(round(v, 2) for v in b)} is {short:.2f}° from straight back; give the tip a small flat end")
                    break

        self.check_bounds(where, bound, offset, pts + sp.get("extra", []))

    def check_simple_shape(self, el: ET.Element, tag: str, where: str, bound, offset) -> None:
        try:
            if tag == "circle":
                cx, cy, r = (float(el.get(k, "0")) for k in ("cx", "cy", "r"))
                box = [(cx - r, cy - r), (cx + r, cy + r)]
            else:
                x, y = float(el.get("x", "0")), float(el.get("y", "0"))
                w, h = float(el.get("width", "0")), float(el.get("height", "0"))
                box = [(x, y), (x + w, y + h)]
        except ValueError:
            self.add("error", where, "geometry", f"<{tag}> has non-numeric geometry")
            return
        if bound and bound["kind"] == "node" and tag == "rect":
            self.add("error", where, "bound-topology", "bound nodes are a <path> or <circle>, not <rect>")
        self.check_bounds(where, bound, offset, box)

    def check_bounds(self, where: str, bound, offset, pts: list) -> None:
        if offset is None or not pts:
            return  # rotated/scaled authored transform: skip position checks
        xs = [p[0] + offset[0] for p in pts]
        ys = [p[1] + offset[1] for p in pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        W, H = self.t["canvas"]["width"], self.t["canvas"]["height"]
        if bound and bound["kind"] == "palette":
            if x1 >= 0 and x0 <= W and y1 >= 0 and y0 <= H:
                self.add("warn", where, "palette-parked", "palette entry is on screen; park it off canvas")
            return
        if x1 < 0 or x0 > W or y1 < 0 or y0 > H:
            return  # parked/hidden element
        minpart = self.t["legibility"]["minPartPx"]
        if (x1 - x0) < minpart and (y1 - y0) < minpart:
            self.add("warn", where, "legibility", f"part is {x1 - x0:.1f} × {y1 - y0:.1f} px; parts under ~{minpart} px don't read at 1:1")
        if not self.own_header and y0 < self.header_bottom:
            self.add("warn", where, "header-zone",
                     f"reaches y={y0:.1f}, inside the header (0–{self.header_bottom}); this covers stock header content. Pass --own-header if intended")

    # -- text ---------------------------------------------------------------
    def check_text(self, el: ET.Element, where: str, bound) -> None:
        ty = self.t["type"]
        family = el.get("font-family")
        if family is None:
            self.add("error", where, "text", "text needs an explicit font-family")
        elif ty["fontFamily"] not in family:
            self.add("warn", where, "text", f"font-family {family!r}; the device draws {ty['fontFamily']}")
        size_raw = el.get("font-size")
        if size_raw is None:
            self.add("error", where, "text", "text needs an explicit font-size")
        else:
            try:
                size = float(size_raw.replace("px", ""))
            except ValueError:
                self.add("error", where, "text", f"font-size isn't a number ({size_raw!r})")
            else:
                if size < ty["minSize"]:
                    self.add("error", where, "text", f"font-size {size} px is under the {ty['minSize']} px floor")
                elif size < ty["readDuringPlayMin"]:
                    self.add("warn", where, "text", f"font-size {size} px; aim for ≥ {ty['readDuringPlayMin']} px for anything read during play")
        content = "".join(el.itertext())
        if len(content) > self.t["frame"]["texts"]["textChars"]:
            self.add("error", where, "text", f"{len(content)} characters; a text slot holds {self.t['frame']['texts']['textChars']}")
        if bound and bound["kind"] == "text" and (el.get("x") is not None or el.get("y") is not None):
            self.add("error", where, "bound-text", "bound text is positioned by transform only, no x/y")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint OP-XY machine screen frames against device drawing rules.")
    ap.add_argument("files", nargs="+", type=Path, help="SVG frames to check")
    ap.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS, help="tokens.json (default: opxy/tokens.json)")
    ap.add_argument("--fragment", action="store_true", help="artwork fragment: skip the 480 × 220 canvas check")
    ap.add_argument("--two-page", action="store_true", help="two-page header: reserve y 0–38 instead of 0–20")
    ap.add_argument("--own-header", action="store_true", help="the machine draws its own header; allow artwork in the header zone")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        tokens = load_tokens(args.tokens)
        linter = FrameLinter(tokens, fragment=args.fragment, two_page=args.two_page, own_header=args.own_header)
    except (LintError, KeyError) as exc:
        print(f"lint_frame: {exc}", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    report = []
    failed_io = False
    for path in args.files:
        try:
            findings, stats = linter.lint(path)
        except LintError as exc:
            print(f"lint_frame: {exc}", file=sys.stderr)
            failed_io = True
            continue
        all_findings.extend(findings)
        report.append({"file": str(path), "stats": stats, "findings": [asdict(f) for f in findings]})

    errors = sum(f.level == "error" for f in all_findings)
    warns = sum(f.level == "warn" for f in all_findings)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warns, "files": report}, indent=2))
    else:
        for entry in report:
            s = entry["stats"]
            print(f"{entry['file']}  nodes={s['nodes']} texts={s['texts']} palette={s['palette']} maxPoints={s['maxPoints']}")
            for f in entry["findings"]:
                mark = "E" if f["level"] == "error" else "W"
                print(f"  {mark} {f['rule']:<18} {f['where']}: {f['message']}")
        print(f"{errors} error(s), {warns} warning(s)")

    if failed_io:
        return 2
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
