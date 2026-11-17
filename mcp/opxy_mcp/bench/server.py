"""The bench: a local page for looking at a pass's five variants at 1:1, playing a screen with knobs (MIDI or
mouse), and recording the person's pick. Stdlib only.

Three parties, the way impeccable's live mode splits them:
    page (static/)  ── fetch / SSE ──  this server  ── bench_poll ──  the agent

Safety:
    - binds 127.0.0.1 unless told otherwise;
    - every request carries the session token (cookie set from the URL the server prints, or ?t=);
    - POSTs must be same-origin (Origin matches Host);
    - files are served only from screens/, only .svg and .png, with a CSP that stops any script inside an SVG;
    - the page shows frames through <img>, never inline, for the same reason.

The pick is the person's: the page asks for a name and a reason, and the server records them with the same
design_pass_select call an agent would make, so every gate still applies. Training approval never goes through here.
"""
from __future__ import annotations

import http.cookies
import json
import re
import secrets
import threading
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .. import passes
from ..paths import ROOT, ToolError, colour_policy, pick_preview, rel, screens_dir, shift_policy, tokens
from . import model
from .events import Hub
from .generator import Generators

STATIC = Path(__file__).with_name("static")
STATIC_FILES = {"bench.css": "text/css", "bench.js": "text/javascript", "midi.js": "text/javascript",
                "frames.js": "text/javascript"}
COOKIE = "opxy_bench"
VERBS = ("quieter", "bolder", "distill", "deepen", "steady")
PAGE_CSP = ("default-src 'self'; img-src 'self' blob: data:; style-src 'self' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; connect-src 'self'; script-src 'self'; frame-ancestors 'self'; "
            "base-uri 'none'; form-action 'none'")
SVG_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:"
MAX_BODY = 64_000
# The device face (Univers Next Pro Light) is licensed and rarely installed. Without a fallback the browser draws
# header text in its default serif; the nearest stand-ins are grotesks. Only the served copy changes, never the file.
UNIVERS = re.compile(r'font-family="([^"]*Univers[^"]*)"')
FALLBACK = "'Univers Next Pro', Univers, 'Helvetica Neue', 'Nimbus Sans', Helvetica, sans-serif"
CHECKS = threading.Lock()  # the shared tool loaders and pass records aren't safe to drive from two threads at once


def _svg_for_browser(svg: str) -> bytes:
    return UNIVERS.sub(lambda m: f'font-family="{m.group(1)}, {FALLBACK}"', svg).encode()


class Bench:
    """One running bench: its HTTP server, the event hub, generators and a watcher for files that change."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8470, token: bool = True):
        self.hub, self.generators = Hub(), Generators()
        self.token = secrets.token_urlsafe(18) if token else None
        self.host = host
        self.httpd = self._bind(host, port)
        self.httpd.bench = self  # type: ignore[attr-defined]
        self.stamps: dict[str, tuple] = {}
        self.stopping = threading.Event()
        self.threads: list[threading.Thread] = []

    @staticmethod
    def _bind(host: str, port: int) -> ThreadingHTTPServer:
        last: OSError | None = None
        for p in range(port, port + 30):
            try:
                srv = ThreadingHTTPServer((host, p), Handler)
                srv.daemon_threads = True
                return srv
            except OSError as exc:
                last = exc
        raise ToolError(f"no free port from {port} to {port + 29}: {last}")

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    def url(self, machine_id: str | None = None, pass_name: str | None = None) -> str:
        host = "127.0.0.1" if self.host in ("0.0.0.0", "") else self.host
        q = {k: v for k, v in (("t", self.token), ("m", machine_id), ("p", pass_name)) if v}
        return f"http://{host}:{self.port}/" + (f"?{urllib.parse.urlencode(q)}" if q else "")

    def start(self) -> "Bench":
        for target in (self.httpd.serve_forever, self._watch):
            t = threading.Thread(target=target, daemon=True)
            t.start()
            self.threads.append(t)
        return self

    def stop(self) -> None:
        self.stopping.set()
        self.httpd.shutdown()
        self.httpd.server_close()
        self.generators.close()

    # ── watcher: tell open pages when something they show changed on disk ───
    def _stamp(self, machine_id: str) -> tuple:
        d = screens_dir() / machine_id
        files = list(d.glob("passes/*/pass.json")) + list(d.glob("passes/*/v*/*.svg")) + list(d.glob("frames/*.svg"))
        out = []
        for f in files:
            try:
                out.append((str(f), f.stat().st_mtime_ns))
            except OSError:
                pass
        return tuple(sorted(out))

    def _watch(self) -> None:
        while not self.stopping.wait(1.0):
            for m in self.hub.watched():
                try:
                    now = self._stamp(m)
                except OSError:
                    continue
                if m in self.stamps and self.stamps[m] != now:
                    self.hub.publish({"type": "changed", "machine": m})
                self.stamps[m] = now
            for m in self.generators.poll_changes():
                self.hub.publish({"type": "generator", "machine": m})

    # ── actions from the page ────────────────────────────────────────────────
    def pick(self, body: dict) -> dict:
        m, p, v = _need(body, "machine"), _need(body, "pass"), _need(body, "variant")
        reason, who = _need(body, "reason", "say why this one"), _need(body, "chosenBy", "say who picked it")
        with CHECKS:
            result = passes.design_pass_select(m, v, reason, who, p)
        self.hub.publish({"type": "pick", "machine": m, "pass": p, "variant": v, "reason": reason, "chosenBy": who,
                          "source": "bench", "next": result.get("next")})
        return result

    def reject(self, body: dict) -> dict:
        m, p = _need(body, "machine"), _need(body, "pass")
        reason, who = _need(body, "reason", "say why none of the five"), _need(body, "chosenBy", "say who turned it down")
        with CHECKS:
            result = passes.design_pass_reject(m, reason, who, p)
        self.hub.publish({"type": "reject", "machine": m, "pass": p, "reason": reason, "chosenBy": who,
                          "source": "bench", "next": result.get("next")})
        return result

    def message(self, body: dict) -> dict:
        m, text = _need(body, "machine"), _need(body, "text", "write the note")
        verb = body.get("verb") or None
        if verb and verb not in VERBS:
            raise ToolError(f"verb is one of {', '.join(VERBS)}")
        event = self.hub.publish({"type": "message", "machine": m, "pass": body.get("pass") or None,
                                  "variant": body.get("variant") or None, "verb": verb, "text": text[:2000],
                                  "chosenBy": body.get("chosenBy") or None, "source": "bench"})
        return {"queued": event["id"]}


def _need(body: dict, key: str, why: str | None = None) -> str:
    v = body.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ToolError(why or f"{key} is required")
    return v.strip()


class Handler(BaseHTTPRequestHandler):
    server_version = "opxy-bench"
    protocol_version = "HTTP/1.1"

    @property
    def bench(self) -> Bench:
        return self.server.bench  # type: ignore[attr-defined]

    def log_message(self, fmt, *args):  # quiet: the MCP server talks on stdout, and the CLI prints its own lines
        pass

    # ── plumbing ─────────────────────────────────────────────────────────────
    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _authorised(self, query: dict) -> bool:
        token = self.bench.token
        if token is None:
            return True
        given = (query.get("t") or [None])[0] or self.headers.get("X-Bench-Token")
        if not given:
            cookie = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
            given = cookie[COOKIE].value if COOKIE in cookie else None
        return bool(given) and secrets.compare_digest(given, token)

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True  # non-browser clients (curl, tests) don't send one; the token still applies
        return urllib.parse.urlsplit(origin).netloc == self.headers.get("Host")

    # ── routes ───────────────────────────────────────────────────────────────
    def do_GET(self):  # noqa: N802
        url = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(url.query)
        path = url.path
        if path == "/api/health":
            return self._json({"ok": True, "port": self.bench.port})
        if not self._authorised(query):
            return self._send(403, b"This bench needs the URL it printed when it started (it carries a token).\n",
                              "text/plain; charset=utf-8")
        try:
            if path == "/":
                return self._index(query)
            if path.startswith("/static/"):
                return self._static(path[len("/static/"):])
            if path == "/events":
                return self._events((query.get("machine") or [None])[0])
            if path == "/api/config":
                t = tokens()
                return self._json({"canvas": t["canvas"], "header": t["header"], "motion": t["motion"],
                                   "greys": list(t["greys"]), "colour": colour_policy(), "shift": shift_policy(),
                                   "verbs": VERBS, "renderer": _renderer_name(),
                                   "pickPreview": pick_preview()})
            if path == "/api/machines":
                return self._json(model.machines())
            parts = path.strip("/").split("/")
            if parts[:2] == ["api", "machine"] and len(parts) == 3:
                return self._json(model.machine_view(parts[2]))
            if parts[:2] == ["api", "pass"] and len(parts) == 4:
                return self._json(model.pass_view(parts[2], parts[3]))
            if parts[:2] == ["api", "lint"] and len(parts) == 3:
                return self._lint(parts[2], (query.get("path") or [""])[0])
            if parts[0] == "gen" and len(parts) == 2 and parts[1].endswith(".svg"):
                return self._generate(parts[1][:-4], query)
            if parts[0] == "file":
                return self._file("/".join(parts[1:]))
        except ToolError as exc:
            return self._error(400, str(exc))
        except Exception as exc:  # keep serving; the page shows the message
            return self._error(500, f"{type(exc).__name__}: {exc}")
        return self._error(404, "not found")

    do_HEAD = do_GET

    def do_POST(self):  # noqa: N802
        url = urllib.parse.urlsplit(self.path)
        if not self._authorised(urllib.parse.parse_qs(url.query)):
            return self._error(403, "token required")
        if not self._same_origin():
            return self._error(403, "cross-origin request refused")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._error(413, "request too large")
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ToolError("send a JSON object")
            action = {"/api/pick": self.bench.pick, "/api/reject": self.bench.reject,
                      "/api/message": self.bench.message}.get(url.path)
            if not action:
                return self._error(404, "not found")
            return self._json(action(body))
        except json.JSONDecodeError:
            return self._error(400, "body isn't JSON")
        except ToolError as exc:
            return self._error(400, str(exc))
        except Exception as exc:
            return self._error(500, f"{type(exc).__name__}: {exc}")

    # ── handlers ─────────────────────────────────────────────────────────────
    def _index(self, query: dict) -> None:
        html = (STATIC / "index.html").read_bytes()
        extra = {"Content-Security-Policy": PAGE_CSP}
        if self.bench.token:
            extra["Set-Cookie"] = f"{COOKIE}={self.bench.token}; Path=/; HttpOnly; SameSite=Strict"
        self._send(200, html, "text/html; charset=utf-8", extra)

    def _static(self, name: str) -> None:
        if name not in STATIC_FILES:
            return self._error(404, "not found")
        self._send(200, (STATIC / name).read_bytes(), STATIC_FILES[name] + "; charset=utf-8")

    def _file(self, relpath: str) -> None:
        root = screens_dir().resolve()
        p = (ROOT / urllib.parse.unquote(relpath)).resolve()
        if root not in p.parents or p.suffix.lower() not in (".svg", ".png") or not p.is_file():
            return self._error(404, "frames are served from screens/ only (.svg, .png)")
        if p.suffix.lower() == ".svg":
            body, ctype = _svg_for_browser(p.read_text(encoding="utf-8", errors="replace")), "image/svg+xml"
        else:
            body, ctype = p.read_bytes(), "image/png"
        self._send(200, body, ctype, {"Content-Security-Policy": SVG_CSP})

    def _lint(self, machine_id: str, relpath: str) -> None:
        from ..screens import lint_frames
        p = (ROOT / relpath).resolve()
        if (screens_dir().resolve() / machine_id) not in p.parents or p.suffix != ".svg":
            raise ToolError("lint takes an .svg under the machine's own folder")
        definition = screens_dir() / machine_id / "definition.json"
        two_page = len(model.controls(machine_id)) > 4
        with CHECKS:
            try:
                res = lint_frames([str(p)], definition=str(definition) if definition.exists() else None, two_page=two_page)
            except ToolError:  # a definition the linter can't read shouldn't hide the frame's own findings
                res = lint_frames([str(p)], two_page=two_page)
        self._json({"frame": rel(p), "errors": res["errors"], "warnings": res["warnings"],
                    "byRule": res["byRule"][:12]})

    def _generate(self, machine_id: str, query: dict) -> None:
        raw = (query.get("v") or [""])[0]
        ctrls = model.controls(machine_id)
        values = {}
        if raw:
            nums = raw.split(",")
            if len(nums) != len(ctrls):
                raise ToolError(f"v needs {len(ctrls)} values, in definition order")
            values = {c["id"]: float(n) for c, n in zip(ctrls, nums)}
        notes = float((query.get("n") or ["0"])[0])
        svg = self.bench.generators.frame(machine_id, values, notes)
        self._send(200, _svg_for_browser(svg), "image/svg+xml", {"Content-Security-Policy": SVG_CSP})

    def _events(self, machine_id: str | None) -> None:
        q = self.bench.hub.subscribe(machine_id)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(b"retry: 2000\n\n")
            self.wfile.flush()
            last = time.monotonic()
            while not self.bench.stopping.is_set():
                try:
                    event = q.get(timeout=1.0)
                    self.wfile.write(f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode())
                    self.wfile.flush()
                except Exception:
                    if time.monotonic() - last > 15:  # keep proxies from closing an idle stream
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                        last = time.monotonic()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.bench.hub.unsubscribe(q)


def _renderer_name() -> str:
    from ..runner import rsvg
    tool = rsvg()
    return Path(tool).stem if tool else "browser"


# ── one bench per process, for the MCP tools ─────────────────────────────────
_running: Bench | None = None
_lock = threading.Lock()


def open_bench(machine_id: str | None = None, pass_name: str | None = None, port: int = 8470) -> dict:
    global _running
    if machine_id:
        model.machine_view(machine_id)  # fails early on an unknown machine
    if pass_name and machine_id:
        model.pass_view(machine_id, pass_name)
    with _lock:
        if _running is None:
            _running = Bench(port=port).start()
        b = _running
    return {"url": b.url(machine_id, pass_name), "port": b.port, "renderer": _renderer_name(),
            "tell": "Give the person this URL to open in Chrome or Edge (Web MIDI needs one of them; the rest works in "
                    "any browser). In a cloud session, also report the port so the app can show it. Then call bench_poll "
                    "to wait for what they do there: a pick, a rejection, or a note.",
            "rules": ["The pick and its reason are the person's; the page records them through design_pass_select.",
                      "The bench is a preview, not the device: nothing it shows ticks a device check."]}


def poll(timeout: float = 120) -> dict:
    if _running is None:
        raise ToolError("no bench is open; call bench_open first")
    events = _running.hub.wait(min(max(timeout, 0), 600))
    return {"events": events, "url": _running.url(),
            "next": ("Nothing yet. Poll again if you're waiting for the person." if not events else
                     "Act on these in order. A pick or rejection is already recorded in pass.json; read it back to the "
                     "person in one line and follow its next step. A message is the person's note: answer it. When a "
                     "rejection or a note calls for new work, open a new pass with design_pass_start (the reason or note, "
                     "and its verb, as focus) and fan out: one opxy-designer agent per direction, all five started at "
                     "once, each drawing only into its own v<N>/. Never draw the five yourself in sequence. Each variant "
                     "shows up on the person's board as its frame lands; submit when all five are in.")}


def close_bench() -> dict:
    global _running
    with _lock:
        if _running is None:
            return {"closed": False, "note": "no bench was open"}
        _running.stop()
        _running = None
    return {"closed": True}
