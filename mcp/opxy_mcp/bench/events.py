"""Events between the bench page, the server and the agent.

Two streams:
    page  ← server   Server-Sent Events: a pass or frame changed on disk, a generator was edited, a pick landed.
    agent ← server   bench_poll: what the person did (picked, turned a pass down, sent a note), oldest first.

Person events are also appended to screens/<id>/passes/<nn>/events.jsonl (or screens/<id>/bench-events.jsonl when
there's no pass), so there's a record of what happened at the bench beside the pass it happened to. pass.json
stays the authority on the pick itself; the journal is the trail.
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import queue
import threading
from pathlib import Path

from ..paths import machine_dir

PERSON = ("pick", "reject", "message")


class Hub:
    def __init__(self):
        self.lock = threading.Lock()
        self.subscribers: list[tuple[str | None, queue.Queue]] = []
        self.person: queue.Queue = queue.Queue()
        self.ids = itertools.count(1)

    # ── page side ────────────────────────────────────────────────────────────
    def subscribe(self, machine_id: str | None) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=256)
        with self.lock:
            self.subscribers.append((machine_id, q))
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self.lock:
            self.subscribers = [(m, s) for m, s in self.subscribers if s is not q]

    def watched(self) -> set[str]:
        with self.lock:
            return {m for m, _ in self.subscribers if m}

    def publish(self, event: dict) -> dict:
        event = {"id": next(self.ids), "at": dt.datetime.now().isoformat(timespec="seconds"), **event}
        with self.lock:
            subs = list(self.subscribers)
        for machine_id, q in subs:
            if machine_id in (None, event.get("machine")):
                try:
                    q.put_nowait(event)
                except queue.Full:  # a stalled tab drops events rather than holding the server
                    pass
        if event["type"] in PERSON:
            self.person.put(event)
            self._journal(event)
        return event

    # ── agent side ───────────────────────────────────────────────────────────
    def wait(self, timeout: float) -> list[dict]:
        """Block until the person does something (or timeout), then return everything waiting."""
        out = []
        try:
            out.append(self.person.get(timeout=max(0.0, timeout)))
        except queue.Empty:
            return []
        while True:
            try:
                out.append(self.person.get_nowait())
            except queue.Empty:
                return out

    @staticmethod
    def _journal(event: dict) -> None:
        try:
            d = machine_dir(event["machine"])
        except Exception:
            return
        name = event.get("pass")
        target = (d / "passes" / name / "events.jsonl") if name and (d / "passes" / name).is_dir() else d / "bench-events.jsonl"
        record = {k: v for k, v in event.items() if k != "id"}
        with Path(target).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
