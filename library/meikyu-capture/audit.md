# Meikyu (capture) · audit

| | |
| --- | --- |
| Audited | 2026-11-01, against tokens `source.ref`: pull/260 (docs/design-guidelines), read 2026-10-31 |
| Author | Brian Hinton (confirmed his to share: yes, his own port, MIT like labyrinth) |
| Licence | MIT |
| Material | design frames rendered from `screens/meikyu/concepts/blackhole_capture.py` (`frames` mode: rest, playing, c1–c4 at 0/50/100), two videos with sound (melody, drums), labyrinth's `opxy/machines/meikyu/definition.json` |
| **Verdict** | **not yet**, on one floor a two-state switch can't meet (Drum's 50→100 half, below) and the redraw cost of the turning disc (author's call, below). Everything else passes or is pending device. Kept in the library as a pattern reference, as `meikyu-orrery` was |

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Definition (`lint_definition.py`) | **not checked as a player**: the tool knows synth / sample / effect only and stops on `kind: player`. Run as `--kind effect` for the generic checks: 0 errors, 3 warnings (percent display on Dens and Crpt; `pentatonic` and `chromatic` too long for the 20 px column) | |
| Artwork (`lint_frame.py`) | 0 errors, 172 warnings over 14 frames | `lint` output below |
| Perceptibility | pass on Dens, Scal, Crpt, note response; Drum passes its full range, its 50→100 half is 0 | table below |
| Contact sheet, by eye | one subject, every control reads, no dashboard | `contact.png` |
| Accessibility checklist | 13 of 13 answered: 9 pass, 3 with notes, 1 pending device | below |
| Motion | still at rest; eases 0.2 s; no element flashes over 3/s; reduced motion jumps to end states that differ by position, height or shape | below |
| ux.md before you submit | answered below; device items pending | below |

### Perceptibility

Scores are the author's to confirm. I scored them from the sound: Dens 5 (it decides how many of the 8 steps play), Scal 3 (same rhythm, different notes), Crpt 3 (the pattern drifts phrase to phrase), Drum 5 (melody becomes drums).

| control | score | need % | 0→100 % | 0→50 % | 50→100 % | span | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dens | 5 | 2.50 | 4.28 | 2.43 | 4.04 | 400 | ok |
| Scal | 3 | 1.20 | 1.25 | 1.16 | 1.40 | 322 | ok |
| Crpt | 3 | 1.20 | 2.26 | 2.20 | 2.96 | 378 | ok |
| Drum | 5 | 2.50 | 2.71 | 2.71 | 0.00 | 465 | **under** (half-step rule) |
| note response | — | 2.00 | 4.13 | — | — | 394 | ok |

Scal passes on the keyboard in the lower left (its dots take the new scale's shape) plus the stems moving to new pitches. Drum passes its full range on the scale keyboard giving way to the kit's spacing ruler in the lower right, plus the stems becoming pad lanes.

Drum is an enum with two labels, off and on: its 50 % frame is already "on", so its 50→100 half can't move whatever is drawn. Whether the half-step rule applies to a two-state switch is a protocol decision. Kit (Scal in drum mode) changes the ruler to that kit's spacing; each kit has its own shape, and the header names it (stack, roll, fill, clust).

### Lint warnings, by kind

| warning | count | why it's there |
| --- | --- | --- |
| `closed-ribbon` | 56 | every wire line is an open stroke; the device draws open/out-and-back lines as streaks. A device build redraws rails, rings and spokes as thin closed ribbons. **pending device** |
| `legibility` | 56 | the ground wire (rails, ribs, disc rings, spokes) is 0.7–1.1 px on purpose so the bodies, capture ring and hole edge lead. Everything that carries meaning is ≥ 1.5 px: stems 1.5 / 2.2, capture ring 1.7, cells filled |
| `header-zone` | 56 | the stock header drawn into the frames for review, not machine artwork |
| `distinct-points` | 4 | short broken runs where near lines stop at the hole's edge |

## Accessibility checklist

- [x] Every frame viewed at 1:1: the contact sheet's frames are 480 × 220 each.
- [x] Text ≥ 8 px: the only text is the stock header.
- [x] Text greys: stock header only.
- [x] Meaningful non-text ≥ 3:1. The capture ring and hole edge are `#CDCDCD` (13.2:1). The accent ring, hollow bodies and out-of-phrase stems are `#646464` or brighter (≥ 3.55:1). Only decoration (rails, ribs, disc rings, idle spokes) sits lower.
- [x] No part under ~3 px: the smallest body is 4.6 px across; the ruler's ticks are 3 × 6 px. Note: near the left and right of the disc, spokes seen edge-on come closer than 3 px. They're decoration, and each body's own position carries its lane.
- [x] No state by shade alone. Captured vs not is height, size and fill. Accent is size and shade. The playing phrase is stem weight and shade, and spoke weight and shade.
- [x] Each control visibly different at 0 / 50 / 100: yes; Drum's second half is the two-state note above.
- [x] Visual travel matches the audible score: Dens and Drum move the most (5), Crpt and Scal less (3).
- [x] Nothing moves at rest, nothing flashes over 3/s. The disc turns (a circle a minute) only while the player plays and eases to a stop with the music; the wire no longer shimmers. Lit keys stay lit 0.3 s, so repeats merge. Kick and snare thumps are paced to one per 0.34 s; a body flashes once per 2 s at most.
- [x] Reduced-motion end states differ by more than shade: ring radius, stem height, body distance, cell layout.
- [x] Labels ≤ 8 characters. Note: Scal's enum labels `pentatonic` and `chromatic` are too long for the column; the mock-up shows `pent` / `chrom`, which needs the change in labyrinth's `definition.json`, as does the `Rthm` label (currently `Drum`). Captions **pending device font**.
- [x] No red: grey only, every grey a stock step (9 entries including black and the header text).
- [ ] Device photos at rest, playing, heaviest setting: **pending device**.

## Motion

Still at rest. While the player plays, the disc turns a full circle a minute, easing up and down over 0.5 s; it's what makes it read as a black hole, so Brian keeps it. Dens and the capture ring ease 0.2 s. A re-rolled body slides 0.45 s to its new distance with a streak, which is an event, not a control ease. A press brightens the wire by its velocity for 0.5 s. No element alternates faster than 3/s (see above).

## ux.md before you submit

- Redraw: about 100–110 parts on screen including the header and a corner. Zero at rest. **Over budget while playing:** the turning disc moves every spoke, body and stem each frame (about 50 changed parts a frame against the ~20 average ux.md allows). Brian keeps the rotation as crucial; on a device it could step (redraw every few frames) or turn only the spokes. **pending device** measurement.
- Parts fit 256; palette 9 of 16.
- Mutable outlines: the capture and accent rings change size with Dens (uniform scale about the hole would do for the far halves; the near halves are cut at the hole, so 4 mutable outlines). Stems change length per press: on a device they need length variants per body or bound scaling. Like the orrery, **this needs the player page ABI to grow bound nodes** (today a player page is 24 on/off dots and a text line).
- Presets: none in the definition yet (ux.md wants some).

## What to change (most important first)

1. Fit the turning disc into the redraw budget on a device (step it, or turn fewer parts).
2. Decide the half-step rule for two-state switches (proposal: `perceptibility.py` applies only the full-range floor to a two-label enum). That's a protocol change, so it's Brian's call.
3. Labyrinth: the player page ABI for bound nodes; Scal's short labels; `Drum` → `Rthm`; Kit as Scal in drum mode (`player.cpp`).
4. Device build: closed ribbons for the wire; measure redraw; photos.
5. `lint_definition.py` doesn't know `kind: player` yet.

## Notes the author justified

- Thin ground wire (`legibility`): deliberate, so the bodies lead. Meaning never rides on it.
- Rotation while playing: crucial to the picture; costs redraw (above).
- The scale and kit keyboards are drawn from C, as shapes, not at the pressed root: the root is the key the player is holding.
