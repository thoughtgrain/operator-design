# Reference screens

Screens I learn from, annotated against `constraints.md` and `patterns.md`. Only my own captures live in this folder; other people's work is linked, not copied.

## field-and-figure.jpg

![Face-like outline over a receding mesh, with a step strip along the bottom](field-and-figure.jpg)

A capture at roughly 2× (962 × 453), so everything below is measured back at 1:1.

**Pattern:** P5 Field and figure. A ground mesh, one figure, an activity strip.

What works:

- **One subject.** The face-like outline is the only bright thing in the body; the mesh sits back in a low grey. Nobody wonders where to look.
- **Stock header, used well.** Real-unit values (`3.4` for pH, `62` for dew point) and named modes (`auto`). The values fit their columns.
- **Weight carries hierarchy.** The figure's outline is a thick ribbon (~3–4 px at 1:1); the inner detail is thin. Brightness and weight agree.
- **Strip as a separate layer.** The step strip along the bottom reads as timing information without competing with the figure.

What I'd check before shipping:

- **Label length.** `dew point` is 9 characters; ux.md caps labels at 8. `dewpt` or `dew` would fit the rule.
- **Inner dashes.** The small dash marks inside the figure are about 4–5 × 1 px at 1:1. That's under the ~3–4 px part guidance in the thin dimension, and if each is its own node, they're also the most likely thing to blow the ~20 changed-nodes budget when they move.
- **Mesh density.** The mesh is fine in the foreground, but anywhere it converges (toward a horizon) line gaps can fall under 3 px and turn into a grey smear. Fade it out before it gets that dense.
- **Mesh cost.** If the mesh moves, it has to move as a few nodes, never as re-keyed paths.
- **Strip markers.** The smallest strip squares look ~2–3 px at 1:1. Make the smallest state at least 4 px, and make "active" differ by size as well as brightness.

## Linked references

- **MNMD** by Max Mockett ([site](https://mmockett.github.io/OP-XY/#mnmd), [source](https://github.com/mmockett/OP-XY-MNMD)). The clearest set of open-xy screens I've found. MD KIT draws each drum's sounding part in section like a patent drawing (P1); FM STAT, VO-6 and DPRO-DENS split structure left and output trace right (P2); SID-6581 and SWAVE-PULSE make the trace the subject (P3); DPRO-WAVE stacks wave frames in depth (P4). Two-page header throughout, inactive row in grey.
- **Found Motive kit** ([site](https://foundmotive.com/opxy/)). Useful as the counter-example: several machines (Shaker, Upright Bass, Phase, Tape, Tape Loop) keep the stock page, and Choir uses a figurative singers animation (P6). Shows that Gate 0 is a real decision, not a formality.
- **open-xy core machines** ([source](https://github.com/etcetc000/open-xy-core-machines)). Macro Osc is the reference implementation for every ux.md convention, including the two-page header; 2op FM shows outlines and pulses in `display.cpp`.
