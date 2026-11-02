# Conductor · review

## Tools

| check | result |
| --- | --- |
| `lint_frame.py frames/*/*.svg --two-page` | **0 errors, 0 warnings** across 99 frames |
| `perceptibility.py` M1 (`perc-m1.txt`) | 7 of 8 controls pass, plus the note response. **prog** misses on the full range only (2.16 % against 2.5 %); each half clears the *full-range* floor (3.04 %, 2.92 %) |
| `perceptibility.py` M2 (`perc-m2.txt`) | **pass**: all 8 controls and the note response |
| `perceptibility.py` M3 (`perc-m3.txt`) | 7 of 8 pass, plus the note response. **tones** fails only on its 50 → 100 half |
| `perceptibility.py` M4 (`perc-m4.txt`) | 5 of 6 pass. **mute** fails only on its 0 → 50 half |
| `lint_definition.py` | 2 errors, 2 warnings, all from SDK-branch features the checker doesn't know yet (see `brief.md`) |
| device limits | The generator asserts these on every frame: every round node within 2× of its pool's authored radius; every node painted from the 16-entry paint palette; no per-page static art (static art shows on every page, so each page's furniture is nodes) |

### The three misses are two protocol questions, not design gaps

Neither is solved by lowering a score.

1. **Two-state switches.** `tones` (chord/scale) and `mute` (off/on) change all at once, so one half of their range never moves. Over the full range both clear their floor (3.11 % against 1.2 %, and 2.55 % against 2.5 %). It's the same question the meikyu audit raised. I'd like a ruling in `opxy/audit.md` rather than faking an ease the control doesn't have.
2. **Unordered enums.** `prog`'s ends, pop and walk, share three of their four chords, so the ends look alike even though every step between them is a big change. Pop → drone and drone → walk each clear the full-range floor. I'd propose that an unordered enum is judged step by step, not end to end.

## Craft (rest frame beside `library/meikyu-orrery/` at 1:1)

| question | answer |
| --- | --- |
| Every element in the named language? | Yes. Orbit, gaps for pitch classes, planets, moons, ephemeris tracks and graduated edges are all drawn as an atlas plate. The phrase track's cells are the plainest element; an atlas's time band is close enough. |
| Line weights match the table? | Yes. Hairlines run 1–1.2 px (orbit 1.6 px ribbon, rules, edges); lines are 1.5 px (loop planets); the subject is 2 px (the sounding planet). Widths come from the palette, so they're fixed per paint. **Pending device**: whether the device scales a paint's stroke with node scale. |
| Exactly one brightest element? | Yes on M1 at rest: the sounding planet's outline. While playing, what a note just hit joins it, which `craft.md` allows. M2–M4 use `#CDCDCD` only for the selection bracket, the caps and what a note just hit. |
| Anything look like an icon? | No. Fixed along the way: halos with outlines round hollow planets read as bullseyes, so halos are now borderless dark bodies and their planets fill. |
| Sits in the same set as the reference? | Mostly. Conductor's planets are plainer than meikyu's (no meridians or bands), because one node per planet is all the 256-node budget allows with eight full lanes on M2. This is my main craft reservation, and it's your call. |

## Accessibility checklist

| item | evidence |
| --- | --- |
| Every frame viewed at 1:1 | Yes: `contact-m*.png` and a side-by-side with the reference |
| Text ≥ 8 px, ≥ 10 px during play | All body text is 10 px; the chord title is 20 px |
| Text greys ≥ 4.5:1 | Labels `#7D7D7D` 5.1:1, `#969696` 7.1:1, `#CBCBCB` 12.9:1. No text in `#646464` or below |
| Non-text parts ≥ 3:1 | Every meaningful outline is ≥ `#646464` (3.55:1). `#323232`/`#4B4B4B` are used only for ground, hairlines and bodies behind such outlines |
| No part under ~3 px; no repeated lines < 3 px apart | Lint is clean. The smallest moon is 3.6 px |
| No state by shade alone | Selected lane: bracket + band + bright label slot. Loop chords: fill + size. Accent: size. Vary: hollow. Muted: strike + hollow + retracted line. Playing: scale + shade. **One exception:** M1's transfer arc is lit by shade alone, with the plate's `next G` line as its second cue |
| Each control differs at 0 / 50 / 100 | Contact sheets, plus `perceptibility.py` (with the three exceptions above) |
| Visual travel matches the audible score | Yes, against the scores in `brief.md`. **Those scores are mine from the code; pending your confirmation** |
| Nothing moves at rest; nothing flashes > 3×/s | See `motion.md`: a retrigger restarts the fade |
| Reduced-motion end states differ by more than shade | Every end state differs by position, scale, count or fill |
| Labels ≤ 8 chars; captions measured | Page names now fit. Planet labels like `Bdim 2·4` are body text, not captions. Widths are measured with `display.cpp`'s device glyph table, but the preview font differs: **pending device** |
| No red | None. 16 grey paints |
| Device photos | **pending device** |

## Known limits of these frames

- The music is a stand-in (`Song`, `Lane`, `Arp` in `gen_frames.py`), not `generator.h`. Shapes and counts are representative, not exact.
- **Text colour is fixed per slot on the device**, so the frames' colours assume the slot assignment in `handoff.md`: the selected lane's label goes to the one bright slot, as the page strip does today.
- M4's track numbers use the existing spaced-string trick (three text slots). The preview font sets spaces narrower than Univers, so they bunch in previews; the existing M4 already lines them up on the device.
- On the device, the eight moons draw over the planets whatever their depth, because nodes draw in index order. At these sizes it reads fine; the frames show it that way.
- Redraw estimates in `brief.md` are host-side counts: **pending device**.
