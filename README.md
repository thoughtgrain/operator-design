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

## How to use it

Once the server's connected, I talk to the agent in plain language. It reads the protocol, picks the right tools, and stops to ask me whenever a decision is mine. These are the four things I use it for.

### Design a screen

Ask for it by machine, and say what the sound does if the agent can't read the code:

> Design the screen for `toro`, a two-oscillator synth with a wavefolder. Controls come from its OP-1 plugin.

What happens, in order:

1. **Setup.** The agent makes `screens/<id>/` with a brief and asks which category the machine is (engine, drum, sampler, effect, player, sequencer, function) if it can't tell. The category decides which patterns it starts from.
2. **Definition and scores.** It builds or reviews `definition.json`, then scores how much each control changes the sound (1–5). It asks me to confirm the scores, because they size how far each control moves on screen.
3. **Subject pass.** I get **five** candidate subjects, each from a different pattern and drawing style. I pick one and say why; the agent never picks.
4. **Frames pass.** Five rest-frame variants of that subject, shown side by side at 1:1. I pick again, and it draws the full frame set from my pick.
5. **Checks.** Every frame is linted against the device rules, every control is checked for visible change against its score, and I get a contact sheet to look at. Anything that fails goes back a step instead of being waved through.
6. **Motion and an optional video.** After the motion spec, it asks whether I want a video preview, silent or with sound. If I say yes, the agent renders it itself. Any sound is **simulated**: the engine's code run on a computer, not a recording from an OP-XY, and the video says so.
7. **Review and handoff.** A review checklist with evidence, then `handoff.md` for whoever writes `display.cpp`. Anything only a real device can prove stays marked pending.

If a review sends something back, the fix is another pass of five, never a quick patch to one frame.

### Audit a screen

> This is my screen for `theseus`, frames are in this folder. Does it meet the guidelines?

The agent asks whether it's my work and under what licence, runs every automated check that applies, writes a draft report where anything not checked says **not checked**, then does the by-eye checks. The verdict is meets, meets with notes, or not yet with the fixes in order. A passing screen I own can go into `library/`.

### Teach the guidelines something (training mode)

When a screen teaches me something worth keeping (a new pattern, a pitfall, a category nothing fits), I say so:

> The cable drawing on the patch-bay screen worked. Propose it as a new pattern.

The agent drafts a proposal, then hands it to a separate auditor and a separate reviewer, then runs an automated gate. Nothing changes in the docs until I approve it from a terminal:

```sh
python3 mcp/train.py list --state awaiting_approval
python3 mcp/train.py show <id>                         # history, verdicts and the full diff
python3 mcp/train.py approve <id> --by "Brian Hinton"
python3 mcp/train.py reject  <id> --by "Brian Hinton" --reason "…"
```

After approving, I commit the changed docs together with the proposal folder. The whole process is in [`training/README.md`](training/README.md).

### Look something up

> What are the perceptibility floors? Which patterns fit a drum machine? Show me the theseus library entry.

These are answered straight from the docs and the library, with nothing written.

### With a local model

Small local models do best with the compact profile that the LM Studio and Ollama setups turn on. They can also run the auditor and reviewer for training mode themselves: ask the agent to advance a proposal "with run on", and the server sends each stage to the model you set up. Approval still stays with me.

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
