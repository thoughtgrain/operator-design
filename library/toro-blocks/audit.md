# Toro (stacked blocks) · audit

| | |
| --- | --- |
| Audited | 2026-10-31, against tokens `source.ref`: pull/260 (docs/design-guidelines), read 2026-10-31 |
| Author | Brian Hinton (thoughtgrain); confirmed his to share: yes, asked for it to be the reference for screen generation |
| Licence | MIT (labyrinth's OP-XY ports) |
| Material | `screens/toro/definition.json`, `screens/toro/blocks/frames/` (28 frames), `panel.svg.fragment`, `toro-blocks.mp4`, prototype |
| **Verdict** | **meets, with notes** |

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Definition (`lint_definition.py`) | 0 errors, 0 warnings | display: 220 nodes, 0 paths, 0 points, 16 texts, 8 palette |
| Artwork (`lint_frame.py`) | 0 errors in all 28 frames and the fragment | warnings are header-zone (the SDK's own two-page header) and `#FFFFFF` (the note flash) |
| Perceptibility | pass on all eight controls and the note | table below |
| Contact sheet, by eye | one subject, grey only, no text in the body, every state reads at 1:1 | `contact.png` |
| Accessibility checklist | answered | below |
| Motion | idle still; controls ease ~0.15 s; reduced motion jumps the roll and skips lift and ripple, keeps the flash | `screens/toro/blocks/README.md` |
| ux.md before you submit | every control reads at 0/50/100; no red; header uses real units for spread | |

### Perceptibility

Re-scored 2026-10-31 after the slab blocks, the fold drum roll and the wireframe low cubes.

| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| spread | 4 | 1.60 | 11.00 | 7.64 | 8.58 | 267 | ok |
| fold | 5 | 2.50 | 23.68 | 24.96 | 25.92 | 255 | ok |
| cutoff | 5 | 2.50 | 19.30 | 16.23 | 15.20 | 266 | ok |
| res | 3 | 1.20 | 4.85 | 2.29 | 7.14 | 174 | ok |
| shape | 3 | 1.20 | 16.76 | 13.33 | 13.88 | 267 | ok |
| noise | 2 | 0.80 | 8.98 | 6.35 | 5.60 | 266 | ok |
| drive | 3 | 1.20 | 7.34 | 1.96 | 6.71 | 218 | ok |
| aphx | 2 | 0.80 | 13.12 | 6.93 | 11.10 | 266 | ok |
| note | — | 2.00 | 12.61 | — | — | 266 | ok |

### Accessibility

- **Shade alone?** No. Every control changes geometry (heights) as well; res's lit row is the only shade-led change, and it also moves position with the setting.
- **Smallest part.** A cube face is 15 px wide; nothing is under 4 px.
- **Flash.** The note flash is 120 ms of white on six tops, not full-screen, and never repeats faster than the notes.
- **Reduced motion.** Honoured: the roll jumps, the lift and ripple are skipped.

## Notes

- **Redraw is over the ~20 guideline on purpose.** The owner asked for more movement. A note changes about 72 nodes per frame averaged over the next second (peaking near 190). The fallbacks are written into the README in order. This is the first device check.
- **Device pending.** Nobody has photographed this on the panel yet. The other open checks are hairline seams between faces (0.3 px same-colour strokes) and the cost of a full-field ease on a control turn.
