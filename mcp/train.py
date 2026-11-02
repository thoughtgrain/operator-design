#!/usr/bin/env python3
"""Training mode from a terminal: the person's side of the pipeline, approval above all.

    python3 mcp/train.py list [--state awaiting_approval]
    python3 mcp/train.py show <id>              history, verdicts, gate and the diff
    python3 mcp/train.py advance <id> [--run]   trigger the next stage (--run uses OPXY_AGENT_ENDPOINT)
    python3 mcp/train.py approve <id> --by "Name" [--note "..."]
    python3 mcp/train.py reject <id> --by "Name" --reason "..."

Approval lives here on purpose: an agent with the MCP tools can draft, audit, review and gate, but applying a change
to the guidelines needs a person at a terminal (or OPXY_APPROVERS set in the server config).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from opxy_mcp import training  # noqa: E402
from opxy_mcp.paths import ToolError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="operator-design training mode")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--state", choices=training.STAGES)
    s = sub.add_parser("show"); s.add_argument("id")
    s = sub.add_parser("advance"); s.add_argument("id"); s.add_argument("--run", action="store_true")
    s = sub.add_parser("approve"); s.add_argument("id"); s.add_argument("--by", required=True); s.add_argument("--note", default="")
    s = sub.add_parser("reject"); s.add_argument("id"); s.add_argument("--by", required=True); s.add_argument("--reason", required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            rows = training.list_proposals(args.state)["proposals"]
            if not rows:
                print("no proposals")
            for r in rows:
                print(f"{r['id']:<48} {r['state']:<18} {r['kind']:<17} {r['title']}")
        elif args.cmd == "show":
            rec = training.get(args.id)
            diff = rec.pop("diff")
            for k in ("id", "kind", "title", "state", "iteration", "summary", "rationale", "evidence", "categories"):
                print(f"{k:>10}: {rec.get(k)}")
            for st in ("audit", "review"):
                if rec.get(st):
                    print(f"{st:>10}: {rec[st]['verdict']} by {rec[st]['by']}")
                    for f in rec[st]["findings"]:
                        print(f"            - {f}")
            if rec.get("gate"):
                print(f"{'gate':>10}: {'pass' if rec['gate']['pass'] else 'fail'}")
                for c in rec["gate"]["checks"]:
                    mark = "ok  " if c["ok"] else ("FAIL" if c["level"] == "error" else "warn")
                    print(f"            {mark} {c['check']}" + (f" ({c['detail']})" if c["detail"] and not c["ok"] else ""))
            print("\n" + diff)
        elif args.cmd == "advance":
            print(json.dumps(training.advance(args.id, run=args.run), indent=1, ensure_ascii=False))
        elif args.cmd == "approve":
            rec = training.load(args.id)
            print(f"Approving {rec['id']}: {rec['title']}")
            r = training.approve(args.id, args.by, args.note, via="cli")
            print("applied: " + ", ".join(r["applied"]))
            print(r["next"])
        elif args.cmd == "reject":
            training.reject(args.id, args.by, args.reason)
            print(f"rejected {args.id}")
    except ToolError as exc:
        print(f"train: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
