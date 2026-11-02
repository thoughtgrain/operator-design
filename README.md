# operators

My working context for designing for the Teenage Engineering OP-XY. Protocols, patterns, constraints and tooling live here so that I (and any agent I hand work to) design the same way every time.

Right now it holds one module: **`opxy/`**, the protocol for designing the screen a custom machine draws on the OP-XY through the [open-xy SDK](https://github.com/etcetc000/open-xy). More modules can sit beside it later (sequencing workflows, preset design, sound-design notes) without touching it.

It's also an **MCP server** (`mcp/`), so Claude Code, Claude Desktop, Codex, LM Studio and Ollama can run the protocol with the real tools: every generative design pass is five unique variants, and **training mode** (`training/`) is how the guidelines learn, through draft → audit → review → gate → my approval, with a separate agent at each stage.

## Set up the MCP server

Everything runs on Python 3.10+ with no packages to install. The one outside tool is `rsvg-convert`, which renders frames to PNG so agents can look at them (macOS `brew install librsvg`, Debian/Ubuntu `apt install librsvg2-bin`).

Clone the repo first, then pick your client. Every setup command merges into your existing config (other servers stay put), saves the old file as `.bak`, and takes `--dry-run` if you want to see what it'll write first.

```sh
git clone https://github.com/thoughtgrain/operator-design.git
cd operator-design
```

**Claude Code.** Nothing to install for this repo. Open it in Claude Code and approve the `operator-design` server when it asks; `.mcp.json` registers it and `.claude/agents/` brings the designer, drafter, auditor and reviewer subagents. To use it from every project instead:

```sh
python3 mcp/setup.py claude-code --scope user
```

**Claude Desktop.** Writes the server into Desktop's config with the full path to your Python, since Desktop doesn't see your shell's `PATH`. Restart Desktop afterwards.

```sh
python3 mcp/setup.py claude-desktop
```

**Codex.** Adds the server to `~/.codex/config.toml` (or `--scope project` for `.codex/config.toml`, which only loads in trusted projects). The custom agents are already in `.codex/agents/`, and Codex reads `AGENTS.md` on its own.

```sh
python3 mcp/setup.py codex
```

**LM Studio.** Adds it to `~/.lmstudio/mcp.json` with the compact tool profile (15 tools, short descriptions) so it fits a small model's context, and points agent runs at LM Studio's local server. Use a model that supports tool calls.

```sh
python3 mcp/setup.py lmstudio --model qwen3-8b
```

**Ollama.** Ollama has no MCP client of its own, so it goes through [mcp-client-for-ollama](https://pypi.org/project/mcp-client-for-ollama/). Setup writes the server file and prints the command to start it:

```sh
python3 mcp/setup.py ollama --model qwen3:8b
pip install mcp-client-for-ollama
ollmcp -j ~/.config/ollmcp/mcp-servers/operator-design.json -m qwen3:8b
```

**Any other MCP client.** Print the generic stdio entry and paste it into the client's config:

```sh
python3 mcp/setup.py print
```

**Check it worked.** This lists what's in place for each client; a missing client is fine if you don't use it.

```sh
python3 mcp/setup.py check
```

Then try it: ask the agent to design a screen (the `design-screen` prompt in clients that show prompts) and it should start by reading the protocol and the machine's category. Environment settings, the full tool list and how design passes and training mode run are in [`mcp/README.md`](mcp/README.md).

## Layout

```
operators/
├── README.md                      ← you are here
├── AGENTS.md                      ← agent entry point: what to load for which task
├── CLAUDE.md                      ← imports AGENTS.md for Claude Code
├── .mcp.json                      ← registers the MCP server for Claude Code
├── mcp/                           ← the MCP server, client setup and the training CLI
├── training/                      ← training mode: process, agent roles, proposals, changelog
├── .claude/agents/, .codex/agents/ ← designer, drafter, auditor, reviewer (generated from training/agents/)
├── .claude/skills/opxy-screen/    ← skill that runs the screen protocol end to end
├── .claude/skills/opxy-audit/     ← skill that audits a finished screen and adds passing ones to the library
├── opxy/
│   ├── README.md                  ← module index and reading order
│   ├── categories.md              ← engine, drum, sampler, effect, player, sequencer, function
│   ├── catalog.json               ← categories, patterns by category, library, five-iteration settings
│   ├── protocol.md                ← the phases, gates and outputs
│   ├── patterns.md                ← composition patterns and the visual-channel table
│   ├── constraints.md             ← hard limits distilled from open-xy, with sources
│   ├── craft.md                   ← one drawing language, line weights, the side-by-side review
│   ├── accessibility.md           ← legibility, contrast and motion on a 480 × 220 grey screen
│   ├── audit.md                   ← how a finished screen is judged and enters the library
│   ├── tokens.json                ← machine-readable numbers the tools and agents use
│   ├── templates/                 ← brief and starter frame
│   ├── tools/                     ← frame linter and contact-sheet builder (stdlib Python)
│   └── reference/                 ← annotated reference screens
├── screens/                       ← work in progress, one folder per machine
└── library/                       ← audited screens that met the guidelines, kept as references
```

## How it relates to open-xy

open-xy owns the truth about the device: the display ABI, the UX conventions machines are reviewed against, and `sdk.py test`. I don't fork those rules here. `opxy/constraints.md` restates the numbers I design against and links every one back to its source, so when the SDK moves I update one file.

What open-xy doesn't cover is the design process itself: going from "here's a sound and its parameters" to a screen where every control reads, inside the node budget, before anyone writes `display.cpp`. That's what this repo is for.

## Adding a module

1. Make a top-level folder named for the domain (`opxy-presets/`, `sequencing/`).
2. Give it a `README.md` with its reading order, and keep hard limits in one `constraints.md` with sources.
3. Add a routing line to `AGENTS.md` so agents know when to load it.
4. If an agent should run it end to end, add a skill under `.claude/skills/`.
5. If the MCP server should expose it, add its docs to `mcp/opxy_mcp/knowledge.py` → `DOCS` and its tools to `tools.py`.

Not affiliated with Teenage Engineering or the open-xy project. OP-XY is a Teenage Engineering trademark. Nothing in here copies stock artwork.
