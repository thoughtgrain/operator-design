"""End-to-end tests for the operator-design MCP server. Run from the repo root:

    python3 -m unittest discover mcp/tests

Everything runs against a temporary copy of the repo, so screens, passes and proposals made here never touch the
real tree.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REAL = Path(__file__).resolve().parents[2]
TMP = Path(tempfile.mkdtemp(prefix="opxy-mcp-test-"))
COPY = TMP / "repo"
for item in ("mcp", "opxy", "library", "training", "AGENTS.md", ".claude", ".codex", "screens/toro/frames",
             "screens/toro/definition.json", "screens/toro/machine.json"):
    src = REAL / item
    if src.is_dir():
        shutil.copytree(src, COPY / item, ignore=shutil.ignore_patterns("*.mp4", "*.wav", "__pycache__", "tests"))
    elif src.exists():
        (COPY / item).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, COPY / item)
for leftover in (COPY / "training/proposals").glob("*/"):
    shutil.rmtree(leftover)
sys.path.insert(0, str(COPY / "mcp"))

from opxy_mcp import passes, rpc, tools, training  # noqa: E402
from opxy_mcp.paths import ROOT, ToolError  # noqa: E402

HAS_RSVG = shutil.which("rsvg-convert") is not None
SERVER = COPY / "mcp/server.py"


def call(name: str, args: dict) -> tuple[bool, object]:
    r = rpc.Server(out=io.StringIO()).tools_call({"name": name, "arguments": args})
    text = r["content"][0]["text"]
    try:
        return r["isError"], json.loads(text)
    except json.JSONDecodeError:
        return r["isError"], text


def session(messages: list[dict], env: dict | None = None) -> list[dict]:
    lines = "\n".join(json.dumps(m) for m in messages) + "\n"
    res = subprocess.run([sys.executable, str(SERVER)], input=lines, capture_output=True, text=True, timeout=120,
                         env={**os.environ, **(env or {})})
    return [json.loads(line) for line in res.stdout.splitlines() if line.strip()]


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}}


class TestProtocol(unittest.TestCase):
    def test_running_from_the_copy(self):
        self.assertEqual(ROOT, COPY)

    def test_stdio_session(self):
        out = session([INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"},
                       {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                       {"jsonrpc": "2.0", "id": 3, "method": "prompts/list"},
                       {"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "opxy://doc/categories"}},
                       {"jsonrpc": "2.0", "id": 5, "method": "nope"}])
        by_id = {m["id"]: m for m in out}
        self.assertEqual(by_id[1]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(len(by_id[2]["result"]["tools"]), len(tools.TOOLS))
        self.assertIn("design-screen", [p["name"] for p in by_id[3]["result"]["prompts"]])
        self.assertIn("# Categories", by_id[4]["result"]["contents"][0]["text"])
        self.assertEqual(by_id[5]["error"]["code"], -32601)
        self.assertNotIn(None, by_id)  # notifications get no reply

    def test_compact_profile(self):
        out = session([INIT, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}], {"OPXY_PROFILE": "compact"})
        names = [t["name"] for t in out[1]["result"]["tools"]]
        self.assertLessEqual(len(names), 16)
        self.assertNotIn("training_approve", names)

    def test_parse_error_keeps_serving(self):
        res = subprocess.run([sys.executable, str(SERVER)], input="{not json\n" + json.dumps(INIT) + "\n",
                             capture_output=True, text=True, timeout=60)
        msgs = [json.loads(x) for x in res.stdout.splitlines()]
        self.assertEqual(msgs[0]["error"]["code"], -32700)
        self.assertIn("result", msgs[1])

    def test_argument_checks(self):
        err, text = call("opxy_patterns", {"category": "laser"})
        self.assertTrue(err)
        err, text = call("opxy_guide", {"doc": "protocol", "bogus": 1})
        self.assertTrue(err and "unknown argument" in text)

    def test_path_confinement(self):
        err, text = call("lint_frames", {"paths": "/etc/passwd"})
        self.assertTrue(err and "outside the repo" in text)
        err, text = call("lint_frames", {"paths": "../../../../etc/hosts"})
        self.assertTrue(err)


class TestKnowledge(unittest.TestCase):
    def test_catalog_matches_patterns_doc(self):
        text = (ROOT / "opxy/patterns.md").read_text(encoding="utf-8")
        doc = {m.group(1) for m in training.PATTERN_HEAD.finditer(text)}
        cat = json.loads((ROOT / "opxy/catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(doc, set(cat["patterns"]))
        self.assertEqual(cat["iterations"]["perPass"], 5)

    def test_category_filter(self):
        _, data = call("opxy_patterns", {"category": "drum"})
        ids = [p["id"] for p in data["patterns"]]
        self.assertIn("P11", ids)
        self.assertNotIn("P12", ids)
        self.assertIn("P7", ids)  # disciplines apply everywhere

    def test_section_and_search(self):
        _, g = call("opxy_guide", {"doc": "protocol", "section": "Iterations"})
        self.assertIn("exactly five variants", g["content"])
        _, s = call("opxy_search", {"query": "nodes never tilt"})
        self.assertEqual(s["results"][0]["section"], "P10 · Voice field")


@unittest.skipUnless(HAS_RSVG, "rsvg-convert not installed")
class TestChecks(unittest.TestCase):
    def test_lint_matches_cli(self):
        frames = sorted((ROOT / "library/theseus-tower/frames").glob("*.svg"))
        cli = subprocess.run([sys.executable, str(ROOT / "opxy/tools/lint_frame.py"), *map(str, frames), "--two-page", "--json"],
                             capture_output=True, text=True)
        want = json.loads(cli.stdout)
        _, got = call("lint_frames", {"paths": "library/theseus-tower/frames", "two_page": True})
        self.assertEqual((want["errors"], want["warnings"]), (got["errors"], got["warnings"]))

    def test_perceptibility_and_render(self):
        _, p = call("check_perceptibility", {"frames_dir": "library/theseus-tower/frames", "scores": [4, 4, 4, 4, 3, 3, 1, 3]})
        self.assertTrue(p["pass"])
        r = rpc.Server(out=io.StringIO()).tools_call({"name": "render_frame", "arguments": {"path": "library/theseus-tower/frames/rest.svg"}})
        self.assertEqual(r["content"][1]["type"], "image")

    def test_audit_never_writes_into_library(self):
        before = sorted(p.name for p in (ROOT / "library/theseus-tower").iterdir())
        _, a = call("audit_run", {"material_dir": "library/theseus-tower", "scores": [4, 4, 4, 4, 3, 3, 1, 3], "two_page": True})
        self.assertEqual(before, sorted(p.name for p in (ROOT / "library/theseus-tower").iterdir()))
        self.assertTrue(a["report"].startswith("screens/theseus-tower/audit/"))


SUBJECTS = [
    {"variant": "v1", "pattern": "P10", "drawing_language": "hidden-line isometric", "subject": "slabs whose heights follow the folded wave", "controls": ["x"]},
    {"variant": "v2", "pattern": "P4", "drawing_language": "star atlas", "subject": "wavetable frames receding as plates", "controls": ["x"]},
    {"variant": "v3", "pattern": "P1", "drawing_language": "patent section", "subject": "the folder cut open like a patent drawing", "controls": ["x"]},
    {"variant": "v4", "pattern": "P3", "drawing_language": "oscilloscope trace", "subject": "the output waveform drawn big and bright", "controls": ["x"]},
    {"variant": "v5", "pattern": "P15", "drawing_language": "survey plan", "subject": "grain texture cells lit by noise", "controls": ["x"]},
]


class TestPasses(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(ROOT / "screens/passtest", ignore_errors=True)
        err, _ = call("screen_init", {"machine_id": "passtest", "category": "engine"})
        self.assertFalse(err)

    def test_five_distinct_directions(self):
        _, s = call("design_pass_start", {"machine_id": "passtest", "kind": "subject"})
        pairs = {(d["pattern"], d["drawingLanguage"]) for d in s["directions"]}
        self.assertEqual(len(s["directions"]), 5)
        self.assertEqual(len(pairs), 5)
        self.assertEqual(len(s["agentBriefs"]), 5)

    def test_subject_uniqueness_and_pick(self):
        call("design_pass_start", {"machine_id": "passtest", "kind": "subject"})
        err, text = call("design_pass_submit", {"machine_id": "passtest", "variants": SUBJECTS[:4]})
        self.assertTrue(err and "exactly 5" in text)
        dup = [dict(v) for v in SUBJECTS]
        dup[1] = {**SUBJECTS[0], "variant": "v2", "subject": SUBJECTS[0]["subject"] + " shape"}
        _, r = call("design_pass_submit", {"machine_id": "passtest", "variants": dup})
        self.assertEqual(r["state"], "needs_revision")
        err, _ = call("design_pass_select", {"machine_id": "passtest", "variant": "v1", "reason": "r", "chosen_by": "me"})
        self.assertTrue(err)
        _, r = call("design_pass_submit", {"machine_id": "passtest", "variants": SUBJECTS})
        self.assertEqual(r["state"], "ready_for_pick")
        _, r = call("design_pass_select", {"machine_id": "passtest", "variant": "v3", "reason": "r", "chosen_by": "me"})
        self.assertEqual(r["selected"], "v3")

    def test_frames_need_a_subject_first(self):
        err, text = call("design_pass_start", {"machine_id": "passtest", "kind": "frames"})
        self.assertTrue(err and "subject pass" in text)

    @unittest.skipUnless(HAS_RSVG, "rsvg-convert not installed")
    def test_frame_uniqueness(self):
        call("design_pass_start", {"machine_id": "passtest", "kind": "subject"})
        call("design_pass_submit", {"machine_id": "passtest", "variants": SUBJECTS})
        call("design_pass_select", {"machine_id": "passtest", "variant": "v1", "reason": "r", "chosen_by": "me"})
        _, s = call("design_pass_start", {"machine_id": "passtest", "kind": "frames"})
        self.assertEqual(len({d["composition"] for d in s["directions"]}), 5)
        self.assertEqual(len({d["camera"] for d in s["directions"]}), 5)
        p = ROOT / s["pass"]
        lib = ROOT / "library/theseus-tower/frames"
        srcs = [lib / "rest.svg", lib / "c1-100.svg", ROOT / "screens/toro/frames/rest.svg",
                ROOT / "screens/toro/frames/c2-100.svg", ROOT / "opxy/templates/frame.svg"]
        for i, src in enumerate(srcs, 1):
            shutil.copy(src, p / f"v{i}" / "rest.svg")
        _, r = call("design_pass_submit", {"machine_id": "passtest", "two_page": True})
        self.assertEqual(r["state"], "needs_revision")  # toro rest and c2-100 are near-identical
        self.assertTrue(any("v3 and v4" in x for x in r["problems"]))
        shutil.copy(lib / "c3-000.svg", p / "v4" / "rest.svg")
        _, r = call("design_pass_submit", {"machine_id": "passtest", "two_page": True})
        bad = [x for x in r["pairs"] if not x["ok"]]
        self.assertEqual(r["state"] == "ready_for_pick", not bad)


PATTERN = """## P16 · Cable field

**The idea.** Draft pattern: patch cables hang between jacks and each control tensions one.

**Why it works.** Sag reads at arm's length.

**Pitfalls.**

- More than four cables blows the path budget."""
PATTERN_OPS = [
    {"op": "insert_section", "file": "opxy/patterns.md", "before": "## P8 · Headers", "content": PATTERN},
    {"op": "set_json", "file": "opxy/catalog.json", "pointer": "/patterns/P16",
     "value": {"name": "Cable field", "role": "subject", "categories": ["engine"]}},
    {"op": "replace_text", "file": "opxy/categories.md", "find": "| P15 Cell field | ● | | ● | ● | | | |\n",
     "replace": "| P15 Cell field | ● | | ● | ● | | | |\n| P16 Cable field | ● | | | | | | |\n"},
]


class TestTraining(unittest.TestCase):
    def _through_review(self, ops, kind="new_pattern"):
        r = training.propose(kind, f"t {len(training.list_proposals()['proposals'])}", "s", "why", ops, by="drafter@t")
        training.advance(r["id"])
        training.record(r["id"], "audit", "pass", [], "auditor@t")
        training.record(r["id"], "review", "pass", [], "reviewer@t")
        return r["id"]

    def test_editable_files_only(self):
        with self.assertRaises(ToolError):
            training.propose("improve_doc", "x", "s", "r", [{"op": "append", "file": "opxy/tools/lint_frame.py", "content": "#"}])

    def test_stage_independence(self):
        r = training.propose("new_pattern", "indep", "s", "r", PATTERN_OPS, by="drafter@t")
        training.advance(r["id"])
        with self.assertRaises(ToolError):
            training.record(r["id"], "audit", "pass", [], "drafter@t")
        training.record(r["id"], "audit", "pass", [], "auditor@t")
        with self.assertRaises(ToolError):
            training.record(r["id"], "review", "pass", [], "auditor@t")

    def test_full_flow_with_cli_approval(self):
        pid = self._through_review(PATTERN_OPS)
        self.assertEqual(training.gate(pid)["state"], "awaiting_approval")
        with self.assertRaises(ToolError):
            training.approve(pid, "Someone")  # over MCP, without OPXY_APPROVERS
        res = subprocess.run([sys.executable, str(COPY / "mcp/train.py"), "approve", pid, "--by", "Tester"],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("## P16 · Cable field", (ROOT / "opxy/patterns.md").read_text(encoding="utf-8"))
        self.assertIn(pid, (ROOT / "training/CHANGELOG.md").read_text(encoding="utf-8"))
        # undo, so other tests see the original docs
        for f in ("opxy/patterns.md", "opxy/catalog.json", "opxy/categories.md"):
            shutil.copy(REAL / f, ROOT / f)

    def test_gate_blocks_five_iteration_change(self):
        pid = self._through_review([{"op": "set_json", "file": "opxy/catalog.json", "pointer": "/iterations/perPass", "value": 3}],
                                   kind="improve_doc")
        g = training.gate(pid)
        self.assertEqual(g["state"], "draft")
        self.assertTrue(any(c["check"] == "design passes stay at five variants" and not c["ok"] for c in g["checks"]))

    @unittest.skipUnless(HAS_RSVG, "rsvg-convert not installed")
    def test_gate_tokens_need_constraints_and_regression(self):
        pid = self._through_review([{"op": "set_json", "file": "opxy/tokens.json", "pointer": "/perceptibility/minSpanPx", "value": 500}],
                                   kind="constraint_change")
        failed = {c["check"] for c in training.gate(pid)["checks"] if not c["ok"] and c["level"] == "error"}
        self.assertIn("token changes come with a constraints.md change", failed)
        self.assertIn("token changes bump source.ref", failed)
        self.assertIn("no library entry gets worse under the new tokens", failed)

    def test_brief_carries_the_whole_diff(self):
        big = PATTERN + "\n\n" + "\n".join(f"- Detail line {i} that makes this proposal long." for i in range(400))
        ops = [dict(PATTERN_OPS[0], content=big)] + PATTERN_OPS[1:]
        r = training.propose("new_pattern", "long brief", "s", "why", ops, by="drafter@t")
        training.advance(r["id"])
        brief = training.advance(r["id"])["brief"]
        self.assertIn("Detail line 399", brief)
        self.assertNotIn("diff truncated", brief)

    def test_revision_clears_verdicts(self):
        pid = self._through_review(PATTERN_OPS)
        training.revise(pid, note="tweak", by="drafter@t")
        rec = training.load(pid)
        self.assertEqual((rec["state"], rec["audit"], rec["review"]), ("draft", None, None))


class TestSetup(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(COPY / "mcp"))
        import setup as s
        self.s = s
        self.args = argparse.Namespace(python="/usr/bin/python3", profile=None, endpoint=None, model=None,
                                       approver=None, dry_run=False)

    def test_json_merge_keeps_other_servers(self):
        p = TMP / "client.json"
        p.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}))
        self.s.merge_json(p, self.s.stdio_entry(self.args), dry=False)
        data = json.loads(p.read_text())
        self.assertEqual(set(data["mcpServers"]), {"other", "operator-design"})
        self.assertEqual(data["theme"], "dark")

    def test_codex_write_is_idempotent(self):
        import tomllib
        p = TMP / "config.toml"
        p.write_text('model = "x"\n\n[mcp_servers.other]\ncommand = "y"\n')
        self.s.write_codex(p, self.args)
        self.args.model = "m"
        self.s.write_codex(p, self.args)
        data = tomllib.loads(p.read_text())
        self.assertEqual(data["model"], "x")
        self.assertIn("other", data["mcp_servers"])
        self.assertEqual(data["mcp_servers"]["operator_design"]["env"]["OPXY_AGENT_MODEL"], "m")
        self.assertEqual(p.read_text().count("[mcp_servers.operator_design]"), 1)

    def test_generated_agents_match_roles(self):
        import tomllib
        for f in (ROOT / ".codex/agents").glob("*.toml"):
            d = tomllib.loads(f.read_text())
            self.assertNotIn("training_approve(", d["developer_instructions"])
        for f in (ROOT / ".claude/agents").glob("*.md"):
            self.assertNotIn("training_approve", f.read_text().split("---")[1])


class TestPreview(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(ROOT / "screens/prevtest", ignore_errors=True)
        call("screen_init", {"machine_id": "prevtest", "category": "engine"})

    def test_asks_first(self):
        _, r = call("preview_brief", {"machine_id": "prevtest"})
        self.assertEqual(r["state"], "ask_first")
        self.assertTrue(any("simulated" in q for q in r["askThePerson"]))

    def test_needs_motion_then_labels_audio(self):
        args = {"machine_id": "prevtest", "audio": "simulated", "shows": ["rest", "controls"]}
        _, r = call("preview_brief", args)
        self.assertEqual(r["state"], "not_ready")
        d = ROOT / "screens/prevtest"
        (d / "motion.md").write_text("# motion\n")
        for v in ("000", "050", "100"):
            shutil.copy(d / "frames/rest.svg", d / f"frames/c1-{v}.svg")
        _, r = call("preview_brief", args)
        self.assertEqual(r["state"], "ready")
        self.assertIn("not recorded from an OP-XY", r["audioNote"])
        self.assertTrue(any("simulated" in line for line in r["labelling"]))
        self.assertIn("You (the agent) render it", r["whoRenders"])
        self.assertFalse((d / "preview").exists())  # the server never makes the video


class TestColour(unittest.TestCase):
    def setUp(self):
        self.src = (ROOT / "screens/toro/frames/rest.svg").read_text(encoding="utf-8")
        self.dir = Path(tempfile.mkdtemp(dir=ROOT / "screens"))
        (self.dir / "orig.svg").write_text(self.src)
        (self.dir / "blue.svg").write_text(self.src.replace("#646464", "#3A7BD5"))
        (self.dir / "red.svg").write_text(self.src.replace("#646464", "#D02020"))
        (self.dir / "variant.svg").write_text(self.src.replace('id="toro_node_0"', 'id="elsewhere"', 1))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        os.environ.pop("OPXY_COLOUR", None)

    def lint(self, **args):
        return call("lint_frames", {"paths": str(self.dir / args.pop("file")), **args})

    def test_grey_by_default(self):
        _, r = self.lint(file="blue.svg")
        self.assertTrue(r["errors"] and r["byRule"][0]["rule"] == "grey-only")
        err, text = self.lint(file="blue.svg", colour=True)
        self.assertTrue(err and "OPXY_COLOUR" in text)
        self.assertEqual(call("colour_policy", {})[1]["mode"], "grey only")

    def test_harness_config_allows_colour_but_never_red(self):
        os.environ["OPXY_COLOUR"] = "allow"
        _, r = self.lint(file="blue.svg", colour=True)
        self.assertEqual(r["errors"], 0)
        _, r = self.lint(file="red.svg", colour=True)
        self.assertEqual(r["byRule"][0]["rule"], "no-red")

    def test_grayscale_variant_must_match(self):
        _, r = self.lint(file="orig.svg", grayscale_of=str(self.dir / "orig.svg"))
        self.assertEqual(r["errors"], 0)
        _, r = self.lint(file="variant.svg", grayscale_of=str(self.dir / "orig.svg"))
        self.assertIn("variant-match", [x["rule"] for x in r["byRule"]])
        _, r = self.lint(file="blue.svg", grayscale_of=str(self.dir / "orig.svg"))
        self.assertIn("grey-only", [x["rule"] for x in r["byRule"]])


class TestOpenXYSync(unittest.TestCase):
    def lint_def(self, defn: dict, sdk: str, kind: str = "synth") -> set[str]:
        d = Path(tempfile.mkdtemp(dir=TMP))
        (d / "definition.json").write_text(json.dumps(defn))
        (d / "machine.json").write_text(json.dumps({"schema": 1, "sdk": sdk, "kind": kind}))
        res = subprocess.run([sys.executable, str(ROOT / "opxy/tools/lint_definition.py"), str(d / "definition.json"), "--json"],
                             capture_output=True, text=True)
        return {f["message"] for f in json.loads(res.stdout)["findings"] if f["level"] == "error"}

    def test_node_and_text_limits(self):
        defn = json.loads((ROOT / "screens/toro/definition.json").read_text(encoding="utf-8"))
        defn["resources"]["display"].update(nodes=400, texts=24)
        errs = self.lint_def(defn, "1.7")
        self.assertIn("more than 256 nodes need sdk 1.8+", errs)
        self.assertNotIn("more than 16 text slots need sdk 1.7+", errs)
        self.assertFalse(self.lint_def(defn, "1.8") & {"more than 256 nodes need sdk 1.8+"})

    def test_sdk_test_without_a_checkout(self):
        os.environ.pop("OPXY_SDK", None)
        err, text = call("sdk_test", {"machine": "screens/toro"})
        self.assertTrue(err and "OPXY_SDK" in text)

    def test_sdk_test_runs_the_checkout(self):
        fake = Path(tempfile.mkdtemp(dir=TMP))
        (fake / "sdk.py").write_text("import sys; print('ARGS', sys.argv[1:]); sys.exit(0)\n")
        os.environ["OPXY_SDK"] = str(fake)
        try:
            _, r = call("sdk_test", {"machine": "screens/toro"})
        finally:
            os.environ.pop("OPXY_SDK", None)
        self.assertTrue(r["pass"])
        self.assertIn("'test', '--machine'", r["output"])
        self.assertIn("--no-cpu", r["output"])


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
