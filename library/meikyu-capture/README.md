# Meikyu (capture)

![contact sheet](contact.png)

| | |
| --- | --- |
| Machine | `meikyu` · note player · [labyrinth](https://github.com/thoughtgrain/labyrinth) (OP-XY port of the OP-1 sequencer) |
| Author | Brian Hinton (thoughtgrain) · MIT |
| Pattern | P13 Capture (from `opxy/patterns.md`) |
| Audit | **not yet** on one floor a two-state switch can't meet (Drum's 50→100 half); all else passes or is device pending · 2026-11-01 · tokens `pull/260` · [audit.md](audit.md). Kept as a pattern reference |
| Device | **needs the player page to bind nodes**; device pending |
| Source | `screens/meikyu/concepts/blackhole_capture.py` (also `blackhole3.py` for the lensed-disc shape, `blackhole_moons.py` for the kit sound); `python3 blackhole_capture.py <dir> melody\|drum\|frames` |
| Video | [capture-melody.mp4](capture-melody.mp4), [capture-drum.mp4](capture-drum.mp4): the real player logic (a port of `press()`) with a stand-in voice and a synthesized kit |

## The screen

A black hole in wireframe: the lensed disc of the reference image (an arch over the hole, a ring under it, a flat disc crossing in front) drawn as thin rails, ribs, rings and one spoke per step. The hole isn't decoration: it does the player's job. A step plays when its weight is under Dens, and a black hole captures what comes inside a radius, so each step is a body at a distance set by its weight and Dens is the capture ring. What's inside plays.

## Controls

| control | score | channel | what the player sees |
| --- | --- | --- | --- |
| Dens | 5 | position, height | the capture ring widens; bodies it reaches rise on stems to their pitch, the rest lie flat and hollow; an inner ring at Dens/4 marks accents |
| Scal | 3 | shape | the arch's inner band is a 12-note wheel, low left to high right; only the scale's notes are cells, so the scale is the arch's shape. Stems move to the new pitches |
| Crpt | 3 | position | re-rolled bodies are thrown along their spoke to their new distance, with a streak |
| Rthm (now Drum) | 5 | shape, height | the arch empties and the ring under the hole becomes the 8 pads, spaced by the current kit's intervals; stems become pad lanes; the kick thumps the hole's edge, the snare the ring |
| a press | — | weight, flash | the phrase's 8 spokes and stems thicken and brighten; each body flashes as its step sounds, and its note's cell (or pad) lights; the wire brightens by velocity |

## What makes it work

- **The metaphor does the work.** Find the player's own rule (weight under Dens) and a physical thing with the same shape (inside the capture radius). Then the picture explains the player without a legend.
- **The light carries the harmony.** The bodies show the pattern; the arch shows the scale and the ring under the hole shows the kit, using lines that are already there.
- **Keep the middle clear.** Nothing near is drawn across the hole except the bodies; the wire is thin and dim, so the bodies, the capture ring and the hole's edge lead.
- **Still at rest, no spin.** Steps keep fixed slots and the playhead is the order things light in. A spinning disc tied to the step rate was too fast, and a drifting one redrew everything every frame.

## Notes

- Drum's half-step floor: a protocol question for two-state switches (see the audit).
- The wire is open strokes; a device build redraws it as thin closed ribbons.
- Needs labyrinth changes: player page bound nodes, short Scal labels, `Rthm`, Kit as Scal in drum mode.
- Device checks pending.
