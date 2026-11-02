"""Read-only access to the protocol docs, the pattern index, tokens and the library."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import LIBRARY, OPXY, ROOT, TRAINING, ToolError, catalog, rel, tokens

DOCS: dict[str, Path] = {
    "index": OPXY / "README.md",
    "protocol": OPXY / "protocol.md",
    "categories": OPXY / "categories.md",
    "constraints": OPXY / "constraints.md",
    "patterns": OPXY / "patterns.md",
    "craft": OPXY / "craft.md",
    "accessibility": OPXY / "accessibility.md",
    "audit": OPXY / "audit.md",
    "reference": OPXY / "reference" / "README.md",
    "agents": ROOT / "AGENTS.md",
    "library": LIBRARY / "README.md",
    "training": TRAINING / "README.md",
    "template-brief": OPXY / "templates" / "brief.md",
    "template-audit": OPXY / "templates" / "audit.md",
    "template-library-card": OPXY / "templates" / "library-card.md",
}

HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
DEFAULT_MAX = 12000


@dataclass
class Section:
    level: int
    title: str
    start: int  # line index of the heading
    end: int    # exclusive


def sections(text: str) -> list[Section]:
    """Headings and the span each one owns (up to the next heading at the same or a higher level)."""
    lines = text.splitlines()
    heads: list[tuple[int, int, str]] = []
    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = []
    for j, (i, level, title) in enumerate(heads):
        end = len(lines)
        for k in range(j + 1, len(heads)):
            if heads[k][1] <= level:
                end = heads[k][0]
                break
        out.append(Section(level, title, i, end))
    return out


def doc_text(name: str) -> str:
    path = DOCS.get(name)
    if path is None:
        raise ToolError(f"unknown doc '{name}'; one of: {', '.join(DOCS)}")
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ToolError(f"{rel(path)} is missing") from exc


def find_section(text: str, query: str) -> tuple[Section, str]:
    q = query.strip().lower()
    secs = sections(text)
    exact = [s for s in secs if s.title.lower() == q]
    starts = [s for s in secs if s.title.lower().startswith(q)]
    contains = [s for s in secs if q in s.title.lower()]
    hit = (exact or starts or contains or [None])[0]
    if hit is None:
        titles = ", ".join(s.title for s in secs[:40])
        raise ToolError(f"no section matching '{query}'. Sections: {titles}")
    lines = text.splitlines()
    return hit, "\n".join(lines[hit.start:hit.end]).strip()


def clip(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    cut = text.rfind("\n", 0, max_chars)
    return text[: cut if cut > max_chars // 2 else max_chars] + "\n\n…(truncated; ask for a section)", True


def guide(doc: str = "index", section: str | None = None, max_chars: int = DEFAULT_MAX) -> dict:
    text = doc_text(doc)
    outline = [{"level": s.level, "title": s.title} for s in sections(text)]
    if section:
        sec, body = find_section(text, section)
        body, cut = clip(body, max_chars)
        return {"doc": doc, "path": rel(DOCS[doc]), "section": sec.title, "content": body, "truncated": cut}
    body, cut = clip(text, max_chars)
    return {"doc": doc, "path": rel(DOCS[doc]), "outline": outline, "content": body, "truncated": cut}


def search(query: str, limit: int = 8, docs: list[str] | None = None) -> dict:
    """Rank sections by how many query terms they contain (title hits count triple)."""
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 1]
    if not terms:
        raise ToolError("query needs at least one word")
    hits = []
    for name in docs or [d for d in DOCS if not d.startswith("template-")]:
        try:
            text = doc_text(name)
        except ToolError:
            continue
        lines = text.splitlines()
        for s in sections(text):
            own_end = s.end
            # score only the section's own lines up to its first child heading
            for k in range(s.start + 1, s.end):
                if HEADING.match(lines[k]):
                    own_end = k
                    break
            body = "\n".join(lines[s.start + 1:own_end]).lower()
            title = s.title.lower()
            score = sum(body.count(t) + 3 * title.count(t) for t in terms)
            if all(t in body or t in title for t in terms):
                score *= 2
            if score:
                snippet = next((ln.strip() for ln in lines[s.start + 1:own_end]
                                if any(t in ln.lower() for t in terms)), "")
                hits.append({"doc": name, "section": s.title, "score": score, "snippet": snippet[:240]})
    hits.sort(key=lambda h: -h["score"])
    return {"query": query, "results": hits[:max(1, min(limit, 25))]}


def _pattern_summary(text: str, pid: str) -> str:
    try:
        _, body = find_section(text, f"{pid} ·")
    except ToolError:
        return ""
    m = re.search(r"\*\*The idea\.\*\*\s*(.+?)(?<=[.!?])\s", body + " ", re.S)
    if m:
        return " ".join(m.group(1).split())
    first = next((ln for ln in body.splitlines()[1:] if ln.strip()), "")
    return first.strip()[:240]


def patterns(pattern_id: str | None = None, category: str | None = None) -> dict:
    cat = catalog()
    text = doc_text("patterns")
    if category and category not in cat["categories"]:
        raise ToolError(f"unknown category '{category}'; one of: {', '.join(cat['categories'])}")
    if pattern_id:
        pid = pattern_id.upper().strip()
        meta = cat["patterns"].get(pid)
        if meta is None:
            raise ToolError(f"unknown pattern '{pattern_id}'; one of: {', '.join(cat['patterns'])}")
        _, body = find_section(text, f"{pid} ·")
        return {"id": pid, **meta, "content": body}
    rows = []
    for pid, meta in cat["patterns"].items():
        fits = meta["categories"]
        if category and category not in fits and "*" not in fits:
            continue
        rows.append({"id": pid, **meta, "idea": _pattern_summary(text, pid)})
    return {"category": category, "patterns": rows}


def token_value(pointer: str | None = None) -> dict:
    data = tokens()
    if not pointer:
        return data
    node = data
    for part in [p for p in pointer.strip("/").split("/") if p]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            raise ToolError(f"no token at {pointer}")
    return {"pointer": pointer, "value": node}


def library(entry: str | None = None, category: str | None = None) -> dict:
    cat = catalog()
    lib = cat.get("library", {})
    if entry:
        d = LIBRARY / entry
        if not d.is_dir() or entry not in lib:
            raise ToolError(f"no library entry '{entry}'; one of: {', '.join(lib)}")
        files = sorted(rel(p) for p in d.rglob("*") if p.is_file())
        out = {"id": entry, **lib[entry], "files": files[:80],
               "card": (d / "README.md").read_text(encoding="utf-8") if (d / "README.md").exists() else ""}
        if (d / "audit.md").exists():
            out["audit"], _ = clip((d / "audit.md").read_text(encoding="utf-8"), 6000)
        return out
    if category and category not in cat["categories"]:
        raise ToolError(f"unknown category '{category}'; one of: {', '.join(cat['categories'])}")
    rows = [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "regression"}}
            for k, v in lib.items() if not category or v.get("category") == category]
    return {"category": category, "entries": rows}


def categories() -> dict:
    cat = catalog()
    pats = cat["patterns"]
    out = {}
    for cid, meta in cat["categories"].items():
        out[cid] = {**meta,
                    "patterns": [p for p, m in pats.items() if cid in m["categories"]],
                    "library": [k for k, v in cat.get("library", {}).items() if v.get("category") == cid]}
    return {"categories": out}
