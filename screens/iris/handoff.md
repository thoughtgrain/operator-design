# Iris · handoff

This is for whoever writes `display.cpp` in `operators-xy/machines/iris/`. With this file and `frames/`, you shouldn't need the brief. The geometry comes from `gen_frames.py`, so `gen_panel.py` should share its constants rather than retype them.

## Display block

```json
"display": {"stateBytes": 60, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 140, "texts": 16, "palette": 5}
```

`sdk` 1.7 in `machine.json` (two pages with 16 header texts). Implemented: `operators-xy/machines/iris/display.cpp`, `display.h`, `gen_panel.py` (writes `panel.svg.fragment` and `nodes.h`).

## The model, in one paragraph

The bow is a family of circles about one centre on the horizon, at (240, 204). Bands run sine, triangle, square, saw at radii 156, 140, 124, 108 with 11, 13, 14, 16 cycles across the half-turn, and every wave is ±4.5 px radially. The **mix line** sits at radius `lerp(RADII, morph·3)` with `lerp(CYCLES, morph·3)` cycles. Its radial offset at arc position u (0 = left foot, 1 = right foot) is 5 px × Σ wᵢ · waveᵢ(n_mix · u · (1 + 0.12 · spread · (i − 1.5)) − travel + phase · i/8), with skew applied to every wave except the saw and Tone's drawn low-pass on top (harmonic n × 1/√(1 + (n / 2^(0.5 + 3·tone))⁴)). The weights wᵢ are the engine's: a triangle kernel of width 1 + 3·overlap about morph·3, normalised to sum 1.

## Nodes

| node | part | driven by | channel |
| --- | --- | --- | --- |
| 0–3 | the mix line, a quarter of the half-turn each: a closed ribbon round 32 centreline points (64 points) | morph, overlap, spread, tone, skew, phase, `travel` | path rewrite: the four outlines share one key |
| 4–11 | the two-page header bar (`page_header.hpp`, first node 4) | page, slots | stock |
| 12–75 | raw band cycles: band b, cycle k → 12 + 16b + k | overlap (radius), spread (scale 0.82–1.18 and angular step), phase (angle offset), tone (shown when the band isn't cut) | translate + turn + uniform scale; palette by weight |
| 76–139 | rounded band cycles, the same layout from 76 | tone (shown when the band is cut) | same |
| — | ground mask (black) and horizon (1.2 px, `#4B4B4B`) | — | static art, authored after the bands; not nodes, because a bound black mask would take its palette entry's paint |

A band cycle node is authored as one cycle at the band's rest radius, centred on its own origin at the cycle's mid-angle, with the wave running along +x (the tangent) and its height along −y (outward). `display()` places it at `polar(r_b, φ_k)` and turns it by `90° − φ_k` (tenths of a degree, `rotation()`). Cycle k's mid-angle is φ_k = π − (k + ½ + shift_b) · π / n_b, where n_b = CYCLES[b] / (1 + 0.12·spread·(b − 1.5)) and shift_b = phase · b / 8, wrapped so the chain stays continuous. Show cycles with φ in (0, π) and hide the rest; the ground mask (static, authored after the bands) covers what dips below the horizon. Scale each cycle by r_b · CYCLES[b] / (RADII[b] · n_b) so the chain tiles its arc; that also scales the line a little (up to ~1.35× in the worst corner). Skew doesn't touch the bands: they're fixed shapes, so Skew acts on the mix line only.

Radii when Overlap pulls: r_b = RADII[b] + (r_mix − RADII[b]) · 0.8 · overlap.

`rotation()` is assumed to turn clockwise on screen for positive tenths (as theseus's cymbals use it), and a cycle authored at the top of the bow is turned by `900 − φ` tenths. **Check that sign against the SDK first**: if it's the other way round, every cycle will lean against its arc.

Tone's cut: band b is cut when tone < (0, 0.20, 0.45, 0.65)[b]. The sine is never cut. A cut band shows its rounded chain in place of the raw one.

## Palette

| entry | paint | used for |
| --- | --- | --- |
| 0 | `#AFAFAF` | mix line at rest |
| 1 | `#CDCDCD` | mix line while a note is held |
| 2 | `#646464` | band, weight ≤ ½ of the top weight (and every cut band steps down one level, floor here) |
| 3 | `#7D7D7D` | band, weight about ⅔ of the top |
| 4 | `#969696` | band, top weight |

The band level is `round(3 · wᵢ / max w)` mapped 0, 1 → entry 2, 2 → 3, 3 → 4. A cut band uses one level lower.

## Texts

0–15 belong to the SDK's two-page header. Titles `morph overlap spread tone` / `skew phase`, values from `header_amount` as percent.

## DisplayState

- `PageHeader header`, `NoteTracker notes`
- the six eased control values (Q10), and `travel` (Q10 cycles) with `speed` (Q10 cycles/s)
- `path_key` (u32): the last key written to the four outlines

## Path key policy

The four outlines share one key, a hash of the eased (morph, overlap, spread, tone, skew, phase) values quantised to Q10, plus `travel` quantised to 1/256 cycle. Rewrite the points only when the key changes. At rest the eased values have settled, `travel` has stopped and the key is constant, so nothing redraws. While held, `travel` moves every frame, so the four outlines rewrite every frame (that's the note response).

## Motion

See `motion.md`. Knob eases use τ ≈ 0.05 s. A held note eases `speed` to 0.8 cycles/s and steps the mix to palette 1. Hold ended eases `speed` to 0 over 0.2 s and returns the mix to palette 0. With reduced motion, track change or `display_reset`, values jump and `travel` stops.

## Open device checks

- `rotation()`'s sign (above), `in.held_notes` as the held-note count, and `Point` coordinates in Q10 px: all three are read from how toro and theseus use the API, not from the SDK headers, which aren't in this repo.

- Redraw cost of 4 × 64-point outline rewrites every frame while held. If it's too heavy, rewrite every second frame.
- Caption widths in Univers Next Pro Light (estimate ≤ 51 px against 53).
- Photos at rest, playing and the heaviest setting (spread 100 with overlap 100).
- Whether band cycles joined by a turn show visible kinks at the seams. They meet at zero crossings, so it shouldn't show; that's from the frames, not hardware.
- Presets by ear; CPU.
