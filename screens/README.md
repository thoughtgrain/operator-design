# Screens

One folder per machine, named by its machine id. Each follows the layout in `opxy/protocol.md`:

```
screens/<machine-id>/
├── brief.md      phases 0–4 (category in intake)
├── passes/       every design pass: <nn>-<kind>/v1…v5 + pass.json, five unique variants
├── frames/       rest.svg, playing.svg, c<N>-000.svg, c<N>-050.svg, c<N>-100.svg
├── contact.svg   + contact.png
├── motion.md     phase 6
├── review.md     phase 7
└── handoff.md    phase 8
```

Optional: `bench.py`, a `frame(values, notes)` function that draws any knob position with the machine's own generator, so the bench's knobs play the screen live (`mcp/README.md`, The bench). The bench also appends what the person did at it to `passes/<nn>/events.jsonl`. Inside a pass, each `v<N>/` can carry the same `bench.py` plus the knob sweep `design_pass_submit` draws from it (`c<N>-000/050/100.svg`, `playing.svg`), so the person can play every variant before picking.

A folder is done when `handoff.md` exists and every non-device item in `review.md` is answered. Device items stay marked pending until there are photos.
