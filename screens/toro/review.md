# Toro · review

Evidence is a frame name in `frames/`, a number, or a tool result. **Pending device** means it can only be settled on an OP-XY and nobody has done it yet.

## Tools

- `lint_definition.py` on the port's `definition.json`: 0 errors, 0 warnings.
- `lint_frame.py frames/*.svg --definition … --two-page`: 26 frames, 0 errors, 0 warnings. Mutable outlines 0 and 1 have exactly the 64 declared points.
- The current port's panel, for comparison: 1 error (header cover path without stroke), open stroked grid lines, 9 px labels, ~250 sub-3 px stars. All are addressed in the revised art.

## Accessibility checklist (opxy/accessibility.md)

- [x] Every frame viewed at 1:1 on `contact.png`
- [x] Text ≥ 8 px everywhere; labels are 10 px, `TAURUS` 13 px (the 8–9 px labels and the RA/Dec line are gone)
- [x] Text greys ≥ 4.5:1: labels `#7D7D7D` (5.1:1), `TAURUS` `#AFAFAF` (9.6:1). The stock inactive header row is excluded as documented
- [x] Meaningful non-text parts ≥ 3:1: joins `#646464` (3.55:1), stars `#AFAFAF`, ecliptic `#969696`. Ground (grid, static field) is `#323232`/`#4B4B4B` by design
- [x] No part under ~3 px: the linter is clean at every 0/50/100 extreme
- [x] No state or control effect by shade alone: every control has a position, scale, shape or count channel; shade is second
- [x] Each control visibly different at 0 / 50 / 100: rows c1–c8 of `contact.png`
- [x] Travel matches the audible score: fold and cutoff (5) have the largest changes; noise (2) is a count of small stars; aphx follows its own curve
- [x] Nothing moves at rest (`motion.md`); twinkle capped at ≤ 3 flashes/s per star
- [x] Reduced-motion end states differ by more than shade: they're the same poses as the 0/50/100 frames
- [x] Labels ≤ 8 characters, lower case. Value captions estimated to fit; **`1.25` measurement pending device**
- [x] No red anywhere
- [ ] Device photos at rest, playing and heaviest setting: **pending device**

## ux.md "before you submit"

| Item | Status |
| --- | --- |
| Contact sheet of every control at 0, 50, 100, at 1:1, in the device font | done at 1:1; text renders in a fallback font locally, **device font pending** |
| Every caption measured | estimated; **pending device** |
| Outlines checked across a sweep of every control and every pair | single-control sweeps linted; pairs not yet. The ecliptic is the only reshaping outline and depends on fold alone, so pairs can't change its topology. **Pending: run `sdk.py test` preview frames** |
| Redraw measured at the heaviest setting | estimated ~17 avg / ~22 peak; **pending host measurement** |
| Photos on a device | **pending device** |
| CPU readout | unchanged DSP; **pending device** per profiling.md |
| Presets by ear, clean defaults | defaults pass; presets **pending device**; see the APHX parity note in the brief |

## Open notes

- The ecliptic's two halves meet at x = 240. Both are authored in place with no transform, so they share an origin. Confirm on the device that the joint doesn't gap.
- Spread and shape both move the horn stars (out vs up). At 1:1 they read as different, but a player turning both at once sees one combined move. Accepted: the header says which control is being turned.
