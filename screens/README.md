# Screens

One folder per machine, named by its machine id. Each follows the layout in `opxy/protocol.md`:

```
screens/<machine-id>/
├── brief.md      phases 0–4
├── frames/       rest.svg, playing.svg, c<N>-000.svg, c<N>-050.svg, c<N>-100.svg
├── contact.svg   + contact.png
├── motion.md     phase 6
├── review.md     phase 7
└── handoff.md    phase 8
```

A folder is done when `handoff.md` exists and every non-device item in `review.md` is answered. Device items stay marked pending until there are photos.
