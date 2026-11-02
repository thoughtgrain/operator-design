#!/usr/bin/env python3
"""operator-design MCP server (stdio). Stdlib Python 3.10+.

    python3 mcp/server.py            serve MCP on stdin/stdout
    python3 mcp/server.py --check    self-test: list tools and read the protocol, then exit

Environment:
    OPXY_PROFILE          full (default) or compact (fewer tools, shorter descriptions, for local models)
    OPXY_WORKSPACE        where screens/ lives, if not this repo
    OPXY_AGENT_ENDPOINT   OpenAI-compatible base URL for run=true (LM Studio http://localhost:1234/v1,
                          Ollama http://localhost:11434/v1)
    OPXY_AGENT_MODEL      model name on that endpoint
    OPXY_AGENT_API_KEY    bearer token, if the endpoint needs one
    OPXY_APPROVERS        comma-separated names allowed to approve training proposals over MCP (off by default)
    OPXY_COLOUR           allow: this harness may design in colour (grey is the default; red is always refused)
    OPXY_SDK              path to a local open-xy checkout, for sdk_test
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("operator-design MCP needs Python 3.10 or newer")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from opxy_mcp import rpc, tools  # noqa: E402
from opxy_mcp.knowledge import guide  # noqa: E402
from opxy_mcp.runner import rsvg  # noqa: E402


def check() -> int:
    names = [t.name for t in tools.visible()]
    print(f"operator-design: {len(names)} tools (profile {tools.profile()})")
    print("  " + ", ".join(names))
    g = guide("protocol")
    print(f"protocol: {len(g['outline'])} sections")
    print(f"rsvg-convert: {rsvg() or 'missing (render_frame, contact PNGs and perceptibility on SVG need it)'}")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        sys.exit(check())
    try:
        rpc.Server().serve()
    except KeyboardInterrupt:
        pass
