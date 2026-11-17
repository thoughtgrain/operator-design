"""The bench: a local page for choosing among a pass's five variants and playing a screen with knobs (MIDI too)."""
from .server import Bench, close_bench, open_bench, poll

__all__ = ["Bench", "open_bench", "poll", "close_bench"]
