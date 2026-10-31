# Toro · review (revision 3)

Evidence is a frame name in `frames/`, a number, or a tool result. **Pending device** means it can only be settled on an OP-XY and nobody has done it yet.

## Craft review (opxy/craft.md)

Rest frame beside labyrinth's first Taurus chart and MNMD's MD KIT / FM STAT at 1:1.

| Question | Answer |
| --- | --- |
| Every element drawn in the named language (star atlas)? | Yes. Grid, labels, figure, Pleiades, radiant symbol, plotted trails, isophote contours, ephemeris track, detail inset with leader |
| Line weights match the table at every setting? | Yes. Hairlines 1–1.2 px for the grid, figure and trails; 1.5 px for contours; nothing scales into a wedge (the inset scales fills, not strokes) |
| Exactly one brightest element? | Yes. Aldebaran and its magnified disk; a note briefly lifts the figure |
| Anything look like an icon? | No. Revision 2's moon disc, sunburst, meteor fan and bullseye are gone |
| Sits in the same set as the references? | Yes, at 1:1 |

## Tools

- `lint_definition.py definition.json`: 0 errors, 0 warnings.
- `lint_frame.py frames/*.svg --definition definition.json --two-page`: 26 frames, 0 errors, 0 warnings. The linter now also checks that mutable outlines stay within ±64 px of their node origin. That's an SDK rule revisions 1 and 2 broke without noticing.
- `perceptibility.py`: **pass**.

| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span |
| --- | --- | --- | --- | --- | --- | --- |
| spread | 4 | 1.60 | 3.36 | 3.35 | 3.34 | 186 |
| fold | 5 | 2.50 | 3.02 | 1.97 | 3.30 | 106 |
| cutoff | 5 | 2.50 | 3.45 | 1.40 | 3.03 | 76 |
| res | 3 | 1.20 | 1.35 | 0.90 | 0.69 | 76 |
| shape | 3 | 1.20 | 1.37 | 0.80 | 0.57 | 40 |
| noise | 2 | 0.80 | 1.59 | 0.79 | 0.80 | 467 |
| drive | 3 | 1.20 | 1.30 | 0.61 | 0.68 | 397 |
| aphx | 2 | 0.80 | 0.98 | 0.95 | 1.01 | 474 |
| note response | — | 2.00 | 2.01 | — | — | 399 |

## Accessibility checklist

- [x] Every frame viewed at 1:1 on `contact.png`
- [x] Text ≥ 8 px: labels 10 px `#7D7D7D` (5.1:1), `TAURUS` 12 px `#AFAFAF`
- [x] Meaningful non-text parts ≥ 3:1: figure lines `#646464` (3.55:1), stars `#AFAFAF`, Aldebaran `#CDCDCD`. Grid, outer contour and Moon body are ground by design
- [x] No part under ~3 px: linter clean
- [x] No state or control effect by shade alone
- [x] Each control visibly different at 0 / 50 / 100, and perceptibility passes
- [x] Travel matches the audible score
- [x] Nothing moves at rest; twinkle ≤ 3 flashes/s per star
- [x] Reduced-motion end states differ by more than shade
- [x] Labels ≤ 8 characters, lower case. **`1.25` pending device**
- [x] No red
- [ ] Device photos: **pending device**

## ux.md "before you submit"

| Item | Status |
| --- | --- |
| Contact sheet at 1:1 in the device font | done at 1:1; fallback font locally, **device font pending** |
| Captions measured | **pending device** |
| Outlines across sweeps of every control and pair | single-control sweeps linted. The Milky Way contours depend only on fold, so pairs can't change their topology. **`sdk.py test` frames pending** |
| Redraw at heaviest | prototype model: held at 100 while playing, avg ≤ 9.6, peak ≤ 19; **host `display()` pending** |
| Device photos, CPU, presets by ear | **pending device** |

## Open notes

- Static labels sit only on things that never move. The magnifier caption ("α Tau") is part of the inset frame.
- Turning aphx moves every visible star; batch the updates.
