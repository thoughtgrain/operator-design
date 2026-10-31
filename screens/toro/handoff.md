# Toro · handoff (revision 2)

For implementing the TAURUS screen in `thoughtgrain/labyrinth` → `opxy/machines/toro`. The frames are the target poses and `prototype.html` is the moving reference. `gen_frames.py` holds the exact geometry and maths, so port from it rather than measuring pictures.

## What changes in the machine

| File | Change |
| --- | --- |
| `gen_panel.py` | New node order (below). Chart stars, joins and Pleiades as before, but joins authored 50 px (the four short ones) or 100 px wide 2.6 px, so zoom keeps uniform scale ≤ 2. Paths 0/1 become M1's outlines. New: Aldebaran disk (3 nested discs r 36/29/19), spike r 12, 4 ring annuli r 30 (1.5° slit, one subpath), 2 shock-ring annuli r 30, M1 core r 10, Moon earthshine r 20 plus 8 phase shapes, 12 radiant streaks, 2 comets, 180 field stars. Remove the static field, Milky Way scatter, grid arcs and all labels. Header cover path gets `stroke="none"`. Greys limited to the stock ramp. |
| `display.cpp` | Rewrite the drawing per this handoff and `motion.md`. The camera is one function: `screen = ALD + offset × Z`, `Z = 1 + 2.2·cutoff³`. |
| `display.h` | New `DisplayState` (below). |
| `definition.json` | `resources.display` → the block below. Parameters unchanged. |

## Display block

```json
"display": {"stateBytes": 200, "stateAlignment": 4,
            "paths": 2, "points": 64, "nodes": 251, "texts": 16, "palette": 16}
```

## Node map

| Nodes | Part | Driven by | Channel |
| --- | --- | --- | --- |
| 0, 1 | M1 outer and inner outline (mutable, 64 points) | fold, cutoff | shape: `r(θ) = R·rr·(1 + 0.32·fold(g·sin(3θ + φ)))`, `g = 1 + 7·fold`, `R = (10 + 19·fold)·Z/Z₀`; rr 1.0/0.62, φ 0/0.7 |
| 2–9 | header bar | `page_header.hpp` | stock |
| 10 | Aldebaran core | cutoff, note | scale `min(2, Z·(1 + 0.4·flare))` |
| 11–13 | Aldebaran disk (r 36, 29, 19) | cutoff | scale `clamp((Z − 1.6)/1.6, 0, 1)`; hidden under 0.05 |
| 14 | Aldebaran spike | cutoff, note | scale `min(2, 0.5 + 0.47·Z + 0.5·flare)`, grey `(4 + 3·cutoff)/7` |
| 15–18 | diffraction rings | res, cutoff, note | ring i brightness `clamp(4·res − i + 0.25)`; radius `min(60, 14 + 34·disk + 2(Z − 1) + 12i)` → scale radius/30 |
| 19, 20 | shock rings | note | radius 12 → 52 / 72 px over 0.22 / 0.30 s, fading; hidden at rest |
| 21–28 | chart stars g1–g4, β, ζ, back, tail | cutoff | position `ALD + off·Z`, scale `1 + 0.25(Z − 1)`; hidden off screen |
| 29–37 | joins | cutoff | place at A, turn to B, scale dist/authored ≤ 2; pointing up, stop at y 40; hidden when both ends are off screen |
| 38–44 | Pleiades | cutoff | position `ALD + PLE_OFF·Z + d·Z` |
| 45 | M1 core | fold, cutoff | scale `0.72·R/10`, grey `(1.5 + 2.5·fold)/7` |
| 46 | Moon earthshine | spread | position y `186 − 116·spread` |
| 47–54 | Moon phases (lit 0.12 → 1.0) | shape, spread | show phase `round(7·shape)`, same position |
| 55–66 | Taurid radiant streaks | drive, note | show `3 + round(9·drive)`; length `18 + 42·drive`; grey `(3 + 3·drive)/7`; fan 200°–340° from (150, 214) |
| 67–70 | launched comets (2 × tail, head) | note × aphx | odds `0.25 + 0.7·aphx` per note |
| 71–250 | field stars | noise, aphx, held | show `40 + round(140·noise)` in fixed order; drift `kink·(7 + 22·h₁)` along `360°·h₂`, `kink = 0.4a + 0.6a³` |

Streak length changes with drive. Author streaks at 60 px and scale (0.3–1.0) rather than reshaping, since there are no paths to spare.

## Palette

Entries 0–7 are the stock ramp `#000000 #323232 #4B4B4B #646464 #7D7D7D #969696 #AFAFAF #CDCDCD`; 8–15 spare.

## DisplayState (estimate: 200 bytes)

| Field | Bytes |
| --- | --- |
| `PageHeader header` | 20 |
| `NoteTracker notes` | 16 |
| `u32 serial`, `i32 note_ms` | 8 |
| `i32 eased[8]` | 32 |
| `u32 m1_key`, `i32 m1_fold`, `i32 m1_zoom` | 12 |
| `u8 star_lit[23]` bitfield for 180 stars, `u16 twinkle_ms[3]` round-robin | 30 |
| `i32 drift_cursor` (batched aphx updates) | 4 |
| comets 2 × (`t`, `x`, `y`, `angle`, `life`) | 40 |
| `u32 seed`, `u32 clock`, `u32 meteor_next`, `u32 initialized` | 16 |
| padding to 200 | 22 |

Set `stateBytes` to `sizeof(DisplayState)` and let the SDK check it.

## Path key policy

M1's outlines re-key when fold's detent value or the eased zoom changes, never on time. A note never re-keys them.

## Open device checks

Photos (rest, playing, heaviest) · caption `1.25` in the device font · host `display()` redraw at heaviest and while turning aphx · `sdk.py test` frames for fold × cutoff · CPU readout · presets by ear.
