"""Frames on demand for the knobs: one worker process per machine, a cache, and a restart when the code changes.

A machine opts in with screens/<id>/bench.py (contract in worker.py). Without one, the bench plays only the
drawn keyframes and never blends between them: a crossfade would show a grey ghost no frame contains.
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from collections import OrderedDict
from pathlib import Path

from ..paths import ToolError
from .model import controls, generator_path

WORKER = Path(__file__).with_name("worker.py")
STEP = 200          # values are quantised to 1/200: finer than a MIDI CC (1/127), coarse enough to cache
CACHE = 400         # frames kept per machine
TIMEOUT = 20.0      # seconds a single frame may take before the worker is restarted
MAX_SVG = 4_000_000


def quantise(v: float) -> float:
    return round(min(1.0, max(0.0, v)) * STEP) / STEP


class Worker:
    def __init__(self, machine_id: str, adapter: Path):
        self.machine_id, self.adapter = machine_id, adapter
        self.lock = threading.Lock()
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.proc: subprocess.Popen | None = None
        self.lines: queue.Queue = queue.Queue()
        self.stamp = self._stamp()

    def _watched(self) -> list[Path]:
        """The adapter's folder and frames/: generators import their siblings (gen_frames.py, frames/build.py)."""
        root = self.adapter.parent
        return [p for d in (root, root / "frames") if d.is_dir() for p in d.glob("*.py")]

    def _stamp(self) -> tuple:
        return tuple(sorted((str(p), p.stat().st_mtime_ns) for p in self._watched()))

    def changed(self) -> bool:
        """True (once) when a generator source changed; the next frame comes from a fresh process."""
        now = self._stamp()
        if now != self.stamp:
            self.stamp = now
            self.stop()
            self.cache.clear()
            return True
        return False

    def _start(self) -> None:
        self.proc = subprocess.Popen([sys.executable, "-I", str(WORKER), str(self.adapter)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", bufsize=1, cwd=str(self.adapter.parent))
        self.lines = queue.Queue()
        q, out = self.lines, self.proc.stdout

        def pump():
            for line in out:
                q.put(line)
            q.put(None)
        threading.Thread(target=pump, daemon=True).start()

    def stop(self) -> None:
        proc, self.proc = self.proc, None
        if not proc:
            return
        if proc.poll() is None:
            proc.kill()
        for pipe in (proc.stdin, proc.stdout):
            try:
                if pipe:
                    pipe.close()
            except OSError:
                pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    def frame(self, values: dict[str, float], notes: float) -> str:
        key = json.dumps([sorted(values.items()), notes])
        with self.lock:
            self.changed()
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            if not self.proc or self.proc.poll() is not None:
                self._start()
            assert self.proc and self.proc.stdin
            try:
                self.proc.stdin.write(json.dumps({"values": values, "notes": notes}) + "\n")
                self.proc.stdin.flush()
                line = self.lines.get(timeout=TIMEOUT)
            except (OSError, queue.Empty):
                self.stop()
                raise ToolError(f"{self.machine_id}'s generator didn't answer in {TIMEOUT:.0f} s; restarted it")
            if line is None:
                self.stop()
                raise ToolError(f"{self.machine_id}'s generator exited; check screens/{self.machine_id}/bench.py")
            reply = json.loads(line)
            if "error" in reply:
                raise ToolError(f"{self.machine_id}/bench.py: {reply['error']}")
            svg = reply["svg"]
            if len(svg) > MAX_SVG:
                raise ToolError(f"{self.machine_id}/bench.py returned {len(svg)} bytes; a frame should be far smaller")
            self.cache[key] = svg
            if len(self.cache) > CACHE:
                self.cache.popitem(last=False)
            return svg


class Generators:
    def __init__(self):
        self.workers: dict[str, Worker] = {}
        self.lock = threading.Lock()

    def worker(self, machine_id: str) -> Worker:
        adapter = generator_path(machine_id)
        if not adapter:
            raise ToolError(f"{machine_id} has no bench.py; the knobs play its drawn keyframes only")
        with self.lock:
            w = self.workers.get(machine_id)
            if not w or w.adapter != adapter:
                w = self.workers[machine_id] = Worker(machine_id, adapter)
            return w

    def frame(self, machine_id: str, raw: dict[str, float], notes: float) -> str:
        """Fill missing controls with their defaults, quantise, draw (or reuse) the frame."""
        values = {}
        for c in controls(machine_id):
            v = raw.get(c["id"], c["default"])
            values[c["id"]] = quantise(float(v))
        return self.worker(machine_id).frame(values, quantise(notes))

    def poll_changes(self) -> list[str]:
        with self.lock:
            workers = list(self.workers.values())
        changed = []
        for w in workers:  # a worker busy drawing is checked on its next frame instead
            if w.lock.acquire(blocking=False):
                try:
                    if w.changed():
                        changed.append(w.machine_id)
                finally:
                    w.lock.release()
        return changed

    def close(self) -> None:
        with self.lock:
            for w in self.workers.values():
                w.stop()
            self.workers.clear()
