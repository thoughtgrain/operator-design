"""Training mode: proposals that teach the guidelines something new, through draft → audit → review → gate → approval.

A proposal is a list of edit ops plus the evidence for them. Nothing touches the real docs until a person
approves: until then every check runs on a temporary copy of the repo with the ops applied.

States:
    draft ──advance──▶ audit ──pass──▶ review ──pass──▶ gate ──pass──▶ awaiting_approval ──approve──▶ approved
      ▲                  │ changes        │ changes        │ fail                 │ reject
      └──────────────────┴────────────────┴────────────────┘                      ▼
                                   (any stage: reject) ──────────────────────▶ rejected
"""
from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from . import agents, knowledge
from .paths import PROPOSALS, ROOT, TRAINING, ToolError, load_json, rel, write_json

KINDS = ("new_pattern", "new_category", "improve_doc", "constraint_change")
STAGES = ("draft", "audit", "review", "gate", "awaiting_approval", "approved", "rejected")
VERDICTS = ("pass", "changes_requested", "reject")
OPS = ("insert_section", "replace_section", "replace_text", "append", "set_json", "create_file")
EDITABLE = [re.compile(p) for p in (
    r"^opxy/[^/]+\.md$", r"^opxy/(templates|reference)/[^/]+\.md$", r"^opxy/tokens\.json$", r"^opxy/catalog\.json$",
    r"^AGENTS\.md$", r"^library/README\.md$", r"^\.claude/skills/[^/]+/SKILL\.md$", r"^training/agents/[^/]+\.md$",
    r"^training/README\.md$")]
COPY_FOR_GATE = ("opxy", "library", "training/agents", "training/README.md", "AGENTS.md", ".claude/skills")
PATTERN_HEAD = re.compile(r"^## (P(\d+)) · (.+)$", re.M)
BRIEF_DIFF_MAX = 60000  # agents must see the whole change; past this the brief says where the rest is


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "proposal"


def changes_hash(changes: list) -> str:
    return hashlib.sha256(json.dumps(changes, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def ppath(pid: str) -> Path:
    if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$", pid or ""):
        raise ToolError("proposal ids look like 2026-11-02-cable-field")
    return PROPOSALS / pid / "proposal.json"


def load(pid: str) -> dict:
    p = ppath(pid)
    if not p.exists():
        raise ToolError(f"no proposal {pid}; training_list shows them")
    return load_json(p)


def save(rec: dict) -> None:
    write_json(ppath(rec["id"]), rec)


def log(rec: dict, stage: str, by: str, event: str, **extra) -> None:
    rec.setdefault("history", []).append({"at": now(), "stage": stage, "by": by, "event": event, **extra})


# ── ops ──────────────────────────────────────────────────────────────────────

def validate_ops(changes: list) -> list[str]:
    errs = []
    if not isinstance(changes, list) or not changes:
        return ["changes must be a non-empty list of ops"]
    for i, op in enumerate(changes):
        where = f"changes[{i}]"
        if not isinstance(op, dict) or op.get("op") not in OPS:
            errs.append(f"{where}: op must be one of {', '.join(OPS)}")
            continue
        f = op.get("file", "")
        if not any(rx.match(f) for rx in EDITABLE):
            errs.append(f"{where}: {f or '(no file)'} isn't editable in training mode (docs, tokens, catalog, skills, agent roles only; code changes go through a normal PR)")
        need = {"insert_section": ("content",), "replace_section": ("heading", "content"), "replace_text": ("find", "replace"),
                "append": ("content",), "set_json": ("pointer",), "create_file": ("content",)}[op["op"]]
        for k in need:
            if k not in op:
                errs.append(f"{where}: {op['op']} needs {k}")
        if op["op"] == "insert_section" and not (op.get("before") or op.get("after")):
            errs.append(f"{where}: insert_section needs before or after (a heading)")
        if op["op"] == "set_json" and not f.endswith(".json"):
            errs.append(f"{where}: set_json only applies to tokens.json or catalog.json")
        if op["op"] == "set_json" and "value" not in op and not op.get("delete"):
            errs.append(f"{where}: set_json needs value (or delete: true)")
    return errs


def _find_heading(text: str, heading: str) -> knowledge.Section:
    want = heading.lstrip("#").strip().lower()
    for s in knowledge.sections(text):
        if s.title.lower() == want:
            return s
    raise ToolError(f"heading not found: {heading}")


def _set_pointer(data, pointer: str, value, delete: bool = False):
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.strip("/").split("/") if p]
    if not parts:
        raise ToolError("set_json pointer can't be the root")
    node = data
    for p in parts[:-1]:
        if isinstance(node, dict):
            node = node.setdefault(p, {})
        elif isinstance(node, list) and p.isdigit():
            node = node[int(p)]
        else:
            raise ToolError(f"can't walk {pointer}")
    last = parts[-1]
    if delete:
        if isinstance(node, dict):
            node.pop(last, None)
        else:
            node.pop(int(last))
    elif isinstance(node, list) and last == "-":
        node.append(value)
    elif isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value


def apply_ops(root: Path, changes: list) -> list[str]:
    """Apply ops under root. Returns the touched files. Raises ToolError on the first op that can't apply."""
    touched = []
    for i, op in enumerate(changes):
        path = root / op["file"]
        kind = op["op"]
        try:
            if kind == "create_file":
                if path.exists():
                    raise ToolError(f"{op['file']} already exists")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(op["content"].rstrip() + "\n", encoding="utf-8")
            elif kind == "set_json":
                data = json.loads(path.read_text(encoding="utf-8"))
                _set_pointer(data, op["pointer"], op.get("value"), bool(op.get("delete")))
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            else:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines()
                if kind == "append":
                    text = text.rstrip() + "\n\n" + op["content"].strip() + "\n"
                elif kind == "replace_text":
                    n = text.count(op["find"])
                    if n != 1:
                        raise ToolError(f"replace_text find matches {n} times in {op['file']}; it must match exactly once")
                    text = text.replace(op["find"], op["replace"])
                elif kind == "replace_section":
                    s = _find_heading(text, op["heading"])
                    block = op["content"].strip().splitlines()
                    text = "\n".join(lines[:s.start] + block + [""] + lines[s.end:]).rstrip() + "\n"
                elif kind == "insert_section":
                    block = op["content"].strip().splitlines()
                    if op.get("before"):
                        s = _find_heading(text, op["before"])
                        at = s.start
                    else:
                        s = _find_heading(text, op["after"])
                        at = s.end
                    pad_before = [""] if at > 0 and lines[at - 1].strip() else []
                    text = "\n".join(lines[:at] + pad_before + block + [""] + lines[at:]).rstrip() + "\n"
                path.write_text(text, encoding="utf-8")
        except FileNotFoundError as exc:
            raise ToolError(f"changes[{i}]: {op['file']} doesn't exist (use create_file for new files)") from exc
        except (json.JSONDecodeError, ValueError, IndexError) as exc:
            raise ToolError(f"changes[{i}] ({kind} on {op['file']}): {exc}") from exc
        except ToolError as exc:
            raise ToolError(f"changes[{i}] ({kind} on {op['file']}): {exc}") from exc
        touched.append(op["file"])
    return list(dict.fromkeys(touched))


class Sandbox:
    """A temporary copy of the parts of the repo training mode can touch, with the proposal applied."""

    def __init__(self, changes: list):
        self.changes = changes
        self.tmp = tempfile.TemporaryDirectory(prefix="opxy-train-")
        self.root = Path(self.tmp.name)
        for item in COPY_FOR_GATE:
            src = ROOT / item
            if src.is_dir():
                shutil.copytree(src, self.root / item, ignore=shutil.ignore_patterns("*.mp4", "*.wav", "__pycache__"))
            elif src.exists():
                (self.root / item).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, self.root / item)
        self.touched = apply_ops(self.root, changes)

    def diff(self, max_chars: int = 20000) -> str:
        out = []
        for f in self.touched:
            before = (ROOT / f).read_text(encoding="utf-8").splitlines() if (ROOT / f).exists() else []
            after = (self.root / f).read_text(encoding="utf-8").splitlines()
            out += difflib.unified_diff(before, after, f"a/{f}", f"b/{f}", lineterm="", n=2)
        text = "\n".join(out)
        return text if len(text) <= max_chars else text[:max_chars] + "\n…(diff truncated)"

    def close(self):
        self.tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ── lifecycle ────────────────────────────────────────────────────────────────

def propose(kind: str, title: str, summary: str, rationale: str, changes: list, evidence: list[str] | None = None,
            categories: list[str] | None = None, by: str = "opxy-drafter") -> dict:
    if kind not in KINDS:
        raise ToolError(f"kind is one of: {', '.join(KINDS)}")
    for k, v in (("title", title), ("summary", summary), ("rationale", rationale)):
        if not v or not str(v).strip():
            raise ToolError(f"{k} is required")
    errs = validate_ops(changes)
    if errs:
        raise ToolError("; ".join(errs))
    with Sandbox(changes) as sb:  # fail fast if it doesn't apply
        preview = sb.diff(6000)
    pid = f"{dt.date.today().isoformat()}-{slug(title)}"
    n = 2
    while ppath(pid).exists():
        pid = f"{dt.date.today().isoformat()}-{slug(title)}-{n}"
        n += 1
    rec = {"id": pid, "kind": kind, "title": title.strip(), "summary": summary.strip(), "rationale": rationale.strip(),
           "evidence": evidence or [], "categories": categories or [], "changes": changes,
           "changesHash": changes_hash(changes), "state": "draft", "iteration": 1, "draftedBy": by,
           "created": now(), "audit": None, "review": None, "gate": None, "approval": None, "history": []}
    log(rec, "draft", by, "proposed")
    save(rec)
    return {"id": pid, "state": "draft", "path": rel(ppath(pid).parent), "diffPreview": preview,
            "next": "training_advance to send it to audit."}


def revise(pid: str, changes: list | None = None, note: str = "", by: str = "opxy-drafter", **fields) -> dict:
    rec = load(pid)
    if rec["state"] in ("approved", "rejected"):
        raise ToolError(f"{pid} is {rec['state']}; start a new proposal")
    if changes is not None:
        errs = validate_ops(changes)
        if errs:
            raise ToolError("; ".join(errs))
        with Sandbox(changes):
            pass
        rec["changes"] = changes
        rec["changesHash"] = changes_hash(changes)
    for k in ("title", "summary", "rationale", "evidence", "categories"):
        if fields.get(k) is not None:
            rec[k] = fields[k]
    if not note:
        raise ToolError("say what changed in note")
    rec.update(state="draft", audit=None, review=None, gate=None, iteration=rec.get("iteration", 1) + 1)
    log(rec, "draft", by, "revised", note=note)
    save(rec)
    return {"id": pid, "state": "draft", "iteration": rec["iteration"], "next": "training_advance to re-run audit."}


def get(pid: str, diff: bool = True) -> dict:
    rec = load(pid)
    out = dict(rec)
    if diff:
        try:
            with Sandbox(rec["changes"]) as sb:
                out["diff"] = sb.diff()
        except ToolError as exc:
            out["diff"] = f"(no longer applies to the current docs: {exc})"
    return out


def list_proposals(state: str | None = None) -> dict:
    rows = []
    for p in sorted(PROPOSALS.glob("*/proposal.json")):
        r = load_json(p)
        if state and r["state"] != state:
            continue
        rows.append({"id": r["id"], "kind": r["kind"], "title": r["title"], "state": r["state"],
                     "iteration": r.get("iteration", 1), "categories": r.get("categories", [])})
    return {"state": state, "proposals": rows}


def record(pid: str, stage: str, verdict: str, findings: list | str, by: str) -> dict:
    """An auditor's or reviewer's verdict. Moves the proposal on, or back to draft."""
    rec = load(pid)
    if stage not in ("audit", "review"):
        raise ToolError("stage is audit or review (the gate runs itself; approval is the person's)")
    if rec["state"] != stage:
        raise ToolError(f"{pid} is in {rec['state']}, not {stage}")
    if verdict not in VERDICTS:
        raise ToolError(f"verdict is one of: {', '.join(VERDICTS)}")
    if not by:
        raise ToolError("by: who ran this stage (agent name and client, e.g. opxy-auditor@claude-code)")
    if by == rec.get("draftedBy") or (stage == "review" and by == (rec.get("audit") or {}).get("by")):
        raise ToolError("each stage needs a different agent from the drafter and the earlier stages")
    if isinstance(findings, str):
        findings = [findings] if findings.strip() else []
    if verdict != "pass" and not findings:
        raise ToolError("changes_requested and reject need findings")
    rec[stage] = {"verdict": verdict, "findings": findings, "by": by, "at": now(), "changesHash": rec["changesHash"]}
    log(rec, stage, by, verdict, findings=len(findings))
    rec["state"] = {"pass": "review" if stage == "audit" else "gate", "changes_requested": "draft", "reject": "rejected"}[verdict]
    save(rec)
    return {"id": pid, "state": rec["state"], **_next(rec)}


def gate(pid: str) -> dict:
    """Deterministic checks on the repo with the proposal applied. No agent and no judgement here."""
    rec = load(pid)
    if rec["state"] != "gate":
        raise ToolError(f"{pid} is in {rec['state']}; the gate runs after a passing review")
    checks = run_gate(rec)
    ok = all(c["ok"] for c in checks if c["level"] == "error")
    rec["gate"] = {"pass": ok, "checks": checks, "at": now(), "changesHash": rec["changesHash"]}
    rec["state"] = "awaiting_approval" if ok else "draft"
    log(rec, "gate", "operator-design gate", "pass" if ok else "fail",
        failed=[c["check"] for c in checks if not c["ok"] and c["level"] == "error"])
    save(rec)
    return {"id": pid, "state": rec["state"], "checks": checks, **_next(rec)}


def run_gate(rec: dict) -> list[dict]:
    checks: list[dict] = []

    def add(name, ok, detail="", level="error"):
        checks.append({"check": name, "ok": bool(ok), "level": level, "detail": detail})

    h = rec["changesHash"]
    for st in ("audit", "review"):
        s = rec.get(st) or {}
        add(f"{st} passed on these exact changes", s.get("verdict") == "pass" and s.get("changesHash") == h,
            f"{st}: {s.get('verdict', 'missing')} by {s.get('by', '—')}")
    ids = [rec.get("draftedBy"), (rec.get("audit") or {}).get("by"), (rec.get("review") or {}).get("by")]
    add("drafter, auditor and reviewer are different agents", len(set(ids)) == 3 and None not in ids, " / ".join(map(str, ids)))
    errs = validate_ops(rec["changes"])
    add("every op is valid and editable", not errs, "; ".join(errs))
    if errs:
        return checks
    try:
        sb = Sandbox(rec["changes"])
    except ToolError as exc:
        add("applies cleanly to the current docs", False, f"rebase needed: {exc}")
        return checks
    add("applies cleanly to the current docs", True, ", ".join(sb.touched))
    try:
        _gate_content(rec, sb, add)
    finally:
        sb.close()
    return checks


def _gate_content(rec, sb: Sandbox, add) -> None:
    root, touched = sb.root, set(sb.touched)
    # JSON stays valid and consistent
    try:
        cat = json.loads((root / "opxy/catalog.json").read_text(encoding="utf-8"))
        tok = json.loads((root / "opxy/tokens.json").read_text(encoding="utf-8"))
        add("tokens.json and catalog.json are valid JSON", True)
    except json.JSONDecodeError as exc:
        add("tokens.json and catalog.json are valid JSON", False, str(exc))
        return
    cats = set(cat.get("categories", {}))
    bad = [f"{p}: {c}" for p, m in cat.get("patterns", {}).items() for c in m.get("categories", []) if c != "*" and c not in cats]
    bad += [f"library {k}: {v.get('category')}" for k, v in cat.get("library", {}).items() if v.get("category") not in cats]
    add("every pattern and library category exists", not bad, ", ".join(bad))
    add("design passes stay at five variants", cat.get("iterations", {}).get("perPass") == 5,
        f"perPass = {cat.get('iterations', {}).get('perPass')}")

    # pattern numbering and structure
    pat_text = (root / "opxy/patterns.md").read_text(encoding="utf-8")
    heads = PATTERN_HEAD.findall(pat_text)
    nums = [h[0] for h in heads]
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    add("pattern numbers are unique", not dupes, ", ".join(dupes))
    in_doc, in_cat = set(nums), set(cat.get("patterns", {}))
    add("every pattern in patterns.md has a catalog.json row and vice versa", in_doc == in_cat,
        f"doc only: {sorted(in_doc - in_cat)}, catalog only: {sorted(in_cat - in_doc)}")
    old_nums = set(PATTERN_HEAD.findall((ROOT / "opxy/patterns.md").read_text(encoding="utf-8")))
    new_pats = [h for h in heads if h not in old_nums and h[0] not in {o[0] for o in old_nums}]
    if rec["kind"] == "new_pattern":
        add("a new pattern is added", bool(new_pats), "no new '## P<n> · Name' heading")
        cat_md = (root / "opxy/categories.md").read_text(encoding="utf-8")
        for pid, _, name in new_pats:
            _, body = knowledge.find_section(pat_text, f"{pid} ·")
            missing = [lead for lead in ("**The idea.**", "**Why it works.**", "**Pitfalls.**") if lead not in body]
            add(f"{pid} has the house structure", not missing, "missing " + ", ".join(missing) if missing else "")
            add(f"{pid} is in the categories.md table", re.search(rf"^\| {pid} ", cat_md, re.M) is not None)
            fits = cat.get("patterns", {}).get(pid, {}).get("categories", [])
            add(f"{pid} names the categories it fits", bool(fits), ", ".join(fits))
            if not re.search(r"library/|reference/|draft pattern", body, re.I):
                add(f"{pid} cites a worked example or says it's a draft pattern", False, level="warn")
    if rec["kind"] == "new_category":
        new_cats = cats - set(json.loads((ROOT / "opxy/catalog.json").read_text(encoding="utf-8"))["categories"])
        add("a new category is added to catalog.json", bool(new_cats))
        cat_md = (root / "opxy/categories.md").read_text(encoding="utf-8")
        for c in new_cats:
            add(f"category {c} is described in categories.md", f"**{c}**" in cat_md)

    # numbers travel together (AGENTS.md)
    if "opxy/tokens.json" in touched:
        old_tok = json.loads((ROOT / "opxy/tokens.json").read_text(encoding="utf-8"))
        add("token changes come with a constraints.md change", "opxy/constraints.md" in touched)
        add("token changes bump source.ref", tok.get("source", {}).get("ref") != old_tok.get("source", {}).get("ref"))
        _regression(root, add)

    # links and colour in changed markdown
    for f in sorted(t for t in touched if t.endswith(".md")):
        text = (root / f).read_text(encoding="utf-8")
        broken = []
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
            if re.match(r"^[a-z]+://|^mailto:", target):
                continue
            if not ((root / f).parent / target).resolve().exists() and not (ROOT / Path(f).parent / target).exists():
                broken.append(target)
        add(f"links resolve in {f}", not broken, ", ".join(broken[:10]))
        old = (ROOT / f).read_text(encoding="utf-8") if (ROOT / f).exists() else ""
        added = "\n".join(ln for ln in text.splitlines() if ln not in set(old.splitlines()))
        reds = [hx for hx in re.findall(r"#([0-9A-Fa-f]{6})\b", added) if _is_colour(hx)]
        add(f"no colour introduced in {f} (grey only; red is stock)", not reds, ", ".join("#" + r for r in reds))
        if re.search(r"\b(we|our|you should)\b", added, re.I):
            add(f"first-person voice in {f}", False, "the docs are written as 'I'; check added lines", level="warn")


def _is_colour(hx: str) -> bool:
    r, g, b = (int(hx[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b) > 12


def _regression(root: Path, add) -> None:
    """Library entries judged under the old tokens, re-checked under the new ones (audit.md: re-audit when a floor moves)."""
    from . import screens
    cat = json.loads((ROOT / "opxy/catalog.json").read_text(encoding="utf-8"))
    old_t, new_t = str(ROOT / "opxy/tokens.json"), str(root / "opxy/tokens.json")
    worse = []
    for entry, meta in cat.get("library", {}).items():
        reg = meta.get("regression")
        if not reg:
            continue
        frames = ROOT / "library" / entry / reg["frames"]
        two = bool(reg.get("twoPage"))
        hb = reg.get("headerBottom")
        try:
            svgs = sorted(frames.glob("*.svg"))
            if svgs:
                before = screens.lint_frames([str(p) for p in svgs], two_page=two, tokens_path=old_t)["errors"]
                after = screens.lint_frames([str(p) for p in svgs], two_page=two, tokens_path=new_t)["errors"]
                if after > before:
                    worse.append(f"{entry}: lint errors {before} → {after}")
            p0 = screens.check_perceptibility(str(frames), reg["scores"], reg.get("names"), header_bottom=hb, two_page=two, tokens_path=old_t)
            p1 = screens.check_perceptibility(str(frames), reg["scores"], reg.get("names"), header_bottom=hb, two_page=two, tokens_path=new_t)
            newly = sorted(set(p1["under"]) - set(p0["under"]))
            if newly:
                worse.append(f"{entry}: now under the floor on {', '.join(newly)}")
        except ToolError as exc:
            add(f"library regression ran for {entry}", False, str(exc), level="warn")
    add("no library entry gets worse under the new tokens", not worse,
        "; ".join(worse) + (" (re-audit these, or note the re-audit in the proposal)" if worse else ""))


def approve(pid: str, approver: str, note: str = "", via: str = "mcp") -> dict:
    rec = load(pid)
    if via == "mcp":
        allowed = [a.strip() for a in os.environ.get("OPXY_APPROVERS", "").split(",") if a.strip()]
        if not allowed:
            raise ToolError("approval over MCP is off. Approve from a terminal: python3 mcp/train.py approve "
                            f"{pid} --by \"<your name>\" (or set OPXY_APPROVERS in this server's config to allow it here)")
        if approver not in allowed:
            raise ToolError(f"{approver} isn't in OPXY_APPROVERS")
    if rec["state"] != "awaiting_approval":
        raise ToolError(f"{pid} is in {rec['state']}; only a proposal that passed the gate can be approved")
    if (rec.get("gate") or {}).get("changesHash") != rec["changesHash"]:
        raise ToolError("the changes moved after the gate ran; send it back through the gate")
    touched = apply_ops(ROOT, rec["changes"])
    rec["approval"] = {"by": approver, "at": now(), "note": note, "via": via}
    rec["state"] = "approved"
    log(rec, "approval", approver, "approved", via=via)
    save(rec)
    _changelog(rec, touched)
    return {"id": pid, "state": "approved", "applied": touched,
            "next": "Commit the changed docs with the proposal folder, e.g. git add -A && git commit -m \"training: "
                    + rec["title"] + "\""}


def reject(pid: str, by: str, reason: str) -> dict:
    rec = load(pid)
    if rec["state"] in ("approved", "rejected"):
        raise ToolError(f"{pid} is already {rec['state']}")
    if not reason:
        raise ToolError("say why")
    rec["state"] = "rejected"
    log(rec, rec["state"], by, "rejected", reason=reason)
    save(rec)
    return {"id": pid, "state": "rejected"}


def _changelog(rec: dict, touched: list[str]) -> None:
    path = TRAINING / "CHANGELOG.md"
    head = "# Training changelog\n\nEvery proposal approved through training mode, newest first.\n"
    text = path.read_text(encoding="utf-8") if path.exists() else head
    body = text[len(head):] if text.startswith(head) else "\n" + text
    entry = (f"\n## {rec['approval']['at'][:10]} · {rec['title']}\n\n"
             f"- Proposal: [`{rec['id']}`](proposals/{rec['id']}/proposal.json) · {rec['kind']} · iteration {rec.get('iteration', 1)}\n"
             f"- Drafted by {rec['draftedBy']}; audited by {rec['audit']['by']}; reviewed by {rec['review']['by']}; "
             f"approved by {rec['approval']['by']}\n"
             f"- Changed: {', '.join(f'`{t}`' for t in touched)}\n"
             f"- {rec['summary']}\n")
    path.write_text(head + entry + body, encoding="utf-8")


# ── triggering the next agent ────────────────────────────────────────────────

def _context_for(rec: dict, stage: str) -> str:
    with Sandbox(rec["changes"]) as sb:
        full = sb.diff(10**9)
    diff = full if len(full) <= BRIEF_DIFF_MAX else full[:BRIEF_DIFF_MAX] + (
        f"\n…(diff truncated at {BRIEF_DIFF_MAX} of {len(full)} characters. Read the whole diff with "
        f"training_get(id=\"{rec['id']}\") or `python3 mcp/train.py show {rec['id']}` before giving a verdict; "
        "a verdict on a partial diff doesn't count.)")
    evidence = []
    for e in rec.get("evidence", []):
        exists = (ROOT / e).exists() if not re.match(r"^[a-z]+://", e) else None
        evidence.append(f"- {e}" + ("" if exists is None else " (exists)" if exists else " (MISSING)"))
    parts = [f"Proposal {rec['id']} · {rec['kind']} · iteration {rec.get('iteration', 1)}",
             f"Title: {rec['title']}", f"Summary: {rec['summary']}",
             f"Categories: {', '.join(rec.get('categories') or []) or '—'}"]
    if stage == "audit":  # the reviewer judges fresh; the rationale is the drafter's argument, which the auditor tests
        parts.append(f"Rationale: {rec['rationale']}")
    parts += ["Evidence:", *(evidence or ["- none cited"]), "", "Diff against the current docs:", "```diff", diff, "```", "",
              "Answer with one ```json block: {\"verdict\": \"pass\" | \"changes_requested\" | \"reject\", "
              "\"findings\": [\"…\"]}. Findings are numbered fixes, most important first; empty for pass."]
    return "\n".join(parts)


def _next(rec: dict) -> dict:
    st = rec["state"]
    if st == "draft":
        r = agents.role("draft")
        if rec["history"][-1]["event"] in ("changes_requested", "fail"):
            findings = []
            for s in ("audit", "review"):
                if rec.get(s):
                    findings += [f"[{s}] {f}" for f in rec[s]["findings"]]
            if rec.get("gate"):
                findings += [f"[gate] {c['check']}: {c['detail']}" for c in rec["gate"]["checks"] if not c["ok"]]
            return {"nextStage": "draft", "agent": r["name"], "codexAgent": r["codex_name"], "howToRun": agents.how_to_run(r),
                    "brief": f"Revise proposal {rec['id']} with training_revise. Fix:\n" + "\n".join(f"- {f}" for f in findings)}
        return {"nextStage": "audit", "brief": "Call training_advance to send it to audit."}
    if st in ("audit", "review"):
        r = agents.role(st)
        return {"nextStage": st, "agent": r["name"], "codexAgent": r["codex_name"], "howToRun": agents.how_to_run(r),
                "brief": _context_for(rec, st) + f"\n\nRecord with training_record(id=\"{rec['id']}\", stage=\"{st}\", by=\"{r['name']}@<client>\")."}
    if st == "gate":
        return {"nextStage": "gate", "brief": "Call training_gate (deterministic; no agent)."}
    if st == "awaiting_approval":
        return {"nextStage": "approval", "brief": "Show the person the diff (training_get) and the gate results. Approval is theirs: "
                f"python3 mcp/train.py approve {rec['id']} --by \"<name>\", or training_approve if OPXY_APPROVERS allows it."}
    return {"nextStage": None, "brief": f"{rec['id']} is {st}."}


def advance(pid: str, run: bool = False, max_steps: int = 4) -> dict:
    """Move the proposal to its next stage and hand back (or, with run=true, run) the agent that stage needs."""
    rec = load(pid)
    steps = []
    for _ in range(max(1, min(max_steps, 8))):
        st = rec["state"]
        if st == "draft":
            if rec["history"][-1]["event"] in ("proposed", "revised"):
                rec["state"] = "audit"
                log(rec, "audit", "operator-design", "submitted")
                save(rec)
                steps.append("submitted to audit")
                continue
            break  # sent back: the drafter has to revise
        if st in ("audit", "review") and run:
            r = agents.role(st)
            data = agents.run_json_role(st, _context_for(rec, st))
            verdict = data.get("verdict")
            if verdict not in VERDICTS:
                raise ToolError(f"the {st} agent's verdict '{verdict}' isn't one of {VERDICTS}")
            by = f"{r['name']}@{os.environ.get('OPXY_AGENT_MODEL', 'endpoint')}#{st}"
            record(pid, st, verdict, data.get("findings") or [], by)
            rec = load(pid)
            steps.append(f"{st}: {verdict} ({by})")
            continue
        if st == "gate":
            g = gate(pid)
            rec = load(pid)
            steps.append(f"gate: {'pass' if rec['gate']['pass'] else 'fail'}")
            continue
        break
    return {"id": pid, "state": rec["state"], "steps": steps, **_next(rec)}
