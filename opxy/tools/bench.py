#!/usr/bin/env python3
"""Open the bench from a terminal: a local page for a pass's five variants at 1:1, and knobs (MIDI too) that play
a screen. The same server the MCP tool bench_open starts, for people without an MCP client.

    python3 opxy/tools/bench.py                     every machine; pick one in the page
    python3 opxy/tools/bench.py beacon              open on beacon's latest pass
    python3 opxy/tools/bench.py beacon --pass 02-subject --port 8470

Prints the URL (it carries a session token) and what the person does there: picks, rejections, notes.
--no-token is only for when something in front of the port already authenticates, like a cloud preview.
--host 0.0.0.0 exposes it beyond this machine; don't, unless you mean to.

Exit: Ctrl-C.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp"))

from opxy_mcp.bench import Bench  # noqa: E402
from opxy_mcp.paths import ToolError  # noqa: E402
from opxy_mcp.bench import model  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("machine", nargs="?")
    ap.add_argument("--pass", dest="pass_name")
    ap.add_argument("--port", type=int, default=8470)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-token", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.machine:
            model.machine_view(args.machine)
        bench = Bench(host=args.host, port=args.port, token=not args.no_token).start()
    except ToolError as exc:
        print(f"bench: {exc}", file=sys.stderr)
        return 2
    print(f"bench: {bench.url(args.machine, args.pass_name)}", flush=True)
    print("bench: open it in Chrome or Edge for MIDI; Ctrl-C to stop", flush=True)
    try:
        while True:
            for event in bench.hub.wait(3600):
                print("bench:", json.dumps(event, ensure_ascii=False), flush=True)
    except KeyboardInterrupt:
        bench.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())
