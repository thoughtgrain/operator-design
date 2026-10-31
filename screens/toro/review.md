# Toro · review (revision 2)

Evidence is a frame name in `frames/`, a number, or a tool result. **Pending device** means it can only be settled on an OP-XY and nobody has done it yet.

## Tools

- `lint_definition.py screens/toro/definition.json`: 0 errors, 0 warnings.
- `lint_frame.py frames/*.svg --definition definition.json --two-page`: 26 frames, 0 errors, 0 warnings. M1's outlines have exactly the 64 declared points; every moon phase ends its cusps at ±78° (the first draft turned within 2.5° of straight back there, which the linter caught).
- `perceptibility.py frames --scores 4,5,5,3,3,2,3,2`: **pass**, every control and the note response.

| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span |
| --- | --- | --- | --- | --- | --- | --- |
| spread | 4 | 1.60 | 2.90 | 2.91 | 2.90 | 156 |
| fold | 5 | 2.50 | 2.74 | 1.32 | 2.71 | 72 |
| cutoff | 5 | 2.50 | 12.23 | 5.61 | 13.12 | 353 |
| res | 3 | 1.20 | 2.65 | 1.40 | 1.83 | 104 |
| shape | 3 | 1.20 | 1.30 | 0.75 | 0.57 | 40 |
| noise | 2 | 0.80 | 1.74 | 0.89 | 0.86 | 471 |
| drive | 3 | 1.20 | 2.18 | 0.72 | 1.90 | 120 |
| aphx | 2 | 0.80 | 1.02 | 0.99 | 1.02 | 466 |
| note response | — | 2.00 | 2.96 | — | — | 423 |

Revision 1 failed on spread (1.44), cutoff (0.28), res (0.31), noise (0.18) and aphx (0.26).

## Accessibility checklist (opxy/accessibility.md)

- [x] Every frame viewed at 1:1 on `contact.png`
- [x] Text ≥ 8 px: the only text is the stock two-page header (chart labels removed)
- [x] Meaningful non-text parts ≥ 3:1: chart lines `#646464` (3.55:1), stars `#AFAFAF`, Aldebaran `#CDCDCD`, M1 outline `#7D7D7D`. Earthshine and dim field stars are ground by design
- [x] No part under ~3 px: linter clean at every 0/50/100 extreme
- [x] No state or control effect by shade alone: every control has a position, scale, shape or count channel
- [x] Each control visibly different at 0 / 50 / 100, and `perceptibility.py` passes
- [x] Travel matches the audible score: cutoff and fold (5) change the most; noise and aphx (2) the least that still clears its floor
- [x] Nothing moves at rest (prototype model: 0 within ~1 s of the last note); twinkle ≤ 3 flashes/s per star
- [x] Reduced-motion end states differ by more than shade
- [x] Labels ≤ 8 characters, lower case. **`1.25` measurement pending device**
- [x] No red anywhere
- [ ] Device photos at rest, playing, heaviest setting: **pending device**

## ux.md "before you submit"

| Item | Status |
| --- | --- |
| Contact sheet, every control at 0/50/100, 1:1, device font | done at 1:1; header text in a fallback font locally, **device font pending** |
| Every caption measured | estimated; **pending device** |
| Outlines across sweeps of every control and pair | single-control sweeps linted. M1's outlines depend on fold and cutoff, so the fold × cutoff pair needs checking; **pending `sdk.py test` preview frames** |
| Redraw at the heaviest setting | prototype model: held at 100 while playing, avg ≤ 9.5, peak ≤ 16; **host `display()` pending** |
| Photos on a device | **pending device** |
| CPU readout | DSP unchanged; **pending device** |
| Presets by ear, clean defaults | defaults pass; presets **pending device**; APHX/drive parity note in the brief |

## Open notes

- 251 of 256 nodes. Any addition needs fewer field stars.
- Turning aphx moves every visible star. Batch the updates (≤ 30 per frame) so fast turns don't spike the device.
- M1 sits north of the Hyades for clarity; the real Crab Nebula is near ζ Tauri, which the zoom would push off screen. Artistic placement, noted here so it isn't mistaken for chart data.
