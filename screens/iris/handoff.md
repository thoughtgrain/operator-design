# Iris · handoff

**2026-11-17 (revision 03):** the bow's centre moved below the screen (ends run off the bottom, no horizon), rings 10 px apart, and rings in the blend slide onto the bright line and swell while the rest shrink to a ripple. Node map, cut thresholds and Tone's drawn range below are current; `operators-xy/machines/iris/display.cpp` implements them.

**2026-11-17:** skew and phase moved from a second page to the Shift row, and the second header row is gone (brief, Revision).

This is for whoever writes `display.cpp` in `operators-xy/machines/iris/`. With this file and `frames/`, you shouldn't need the brief. The geometry comes from `gen_frames.py`, so `gen_panel.py` should share its constants rather than retype them.

## Display block

```json
"display": {"stateBytes": 60, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 204, "texts": 8, "palette": 5}
```

`sdk` 1.13 in `machine.json` (the synth Shift row). Implemented: `operators-xy/machines/iris/display.cpp`, `display.h`, `gen_panel.py` (writes `panel.svg.fragment` and `nodes.h`).

## The model, in one paragraph

The bow is a family of circles about one centre below the screen, at (240, 232), so the bands run off the bottom edge. Bands run sine, triangle, square, saw at radii 156, 146, 136, 126 with 11, 13, 14, 16 cycles across the half-turn. A band's wave is ±5.5 px when it's in the blend and a 0.8 px ripple when it isn't. The **mix line** sits at radius `lerp(RADII, morph·3)` with `lerp(CYCLES, morph·3)` cycles. Its radial offset at arc position u (0 = left foot, 1 = right foot) is 5 px × Σ wᵢ · waveᵢ(n_mix · u · (1 + 0.12 · spread · (i − 1.5)) − travel + phase · i/8), with skew applied to every wave except the saw and Tone's drawn low-pass on top (harmonic n × 1/√(1 + (n / 2^(3.5·tone))⁴), the engine's curve fitted to what the line can resolve). The weights wᵢ are the engine's: a triangle kernel of width 1 + 3·overlap about morph·3, normalised to sum 1.

## Nodes

| node | part | driven by | channel |
| --- | --- | --- | --- |
| 0–3 | the mix line, a quarter of the half-turn each: a closed ribbon round 32 centreline points (64 points) | morph, overlap, spread, tone, skew, phase, `travel` | path rewrite: the four outlines share one key |
| 4–11 | the header bar, one row (`page_header.hpp`, first node 4) | slots; Shift swaps the texts | stock |
| 12–203 | band chains, 16 one-cycle nodes each: chain = kind · 4 + band, kind 0 ripple (out of the blend), 1 full height, 2 full height rounded (in the blend, cut by Tone) | morph and overlap (weights → radius, kind), spread (scale and angular step), phase (angle offset), tone (cut) | translate + turn + uniform scale; palette by weight; the band's other two chains hidden |

A band cycle node is authored as one cycle at the band's rest radius, centred on its own origin at the cycle's mid-angle, with the wave running along +x (the tangent) and its height along −y (outward). `display()` places it at `polar(r_b, φ_k)` and turns it by `90° − φ_k` (tenths of a degree, `rotation()`). Cycle k's mid-angle is φ_k = π − (k + ½ + shift_b) · π / n_b, where n_b = CYCLES[b] / (1 + 0.12·spread·(b − 1.5)) and shift_b = phase · b / 8, wrapped so the chain stays continuous. Show cycles with φ in (0, π) and hide the rest; below φ ≈ 5° they're off the bottom edge anyway. Scale each cycle by r_b · CYCLES[b] / (RADII[b] · n_b) so the chain tiles its arc; that also scales the line a little (up to ~1.35× in the worst corner). Skew doesn't touch the bands: they're fixed shapes, so Skew acts on the mix line only.

Radii: r_b = RADII[b] + (r_mix − RADII[b]) · min(1, wₙ · (0.6 + 0.6 · overlap)), where wₙ = w_b / max w. A band out of the blend (level 0) keeps its own radius and shows its ripple chain.

`rotation()` is assumed to turn clockwise on screen for positive tenths (as theseus's cymbals use it), and a cycle authored at the top of the bow is turned by `900 − φ` tenths. **Check that sign against the SDK first**: if it's the other way round, every cycle will lean against its arc.

Tone's cut: band b is cut when tone < (0, 0.25, 0.60, 0.65)[b]. The sine is never cut. A cut band in the blend shows its rounded chain; a band out of the blend shows its ripple either way.

`panel.svg.fragment` must stay under the SDK preview's 64 KiB (it's 62,972 bytes): band chains are written at one decimal, the mix at two. Don't add chains without taking bytes out elsewhere.

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

0–7 belong to the single-row header: titles 0–3, values 4–7. Normally `morph overlap spread tone`. While `shift_row(in).held`, pass `skew phase` and two blanks with the Shift row's values in their place (don't pass the row to `page_header`, which would stack it). Values come from `header_amount`, as percent.

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
- The Shift row: the `synth_shift` field's shape, `shift_row(in).values[]` as Q31 words, `page_header` called with a single row of slots, and the engine reading the Shift values as `p[4]` and `p[5]`. All four follow `constraints.md`'s notes on SDK 1.13, not the SDK headers.

- Redraw cost of 4 × 64-point outline rewrites every frame while held. If it's too heavy, rewrite every second frame.
- Caption widths in Univers Next Pro Light (estimate ≤ 51 px against 53).
- Photos at rest, playing and the heaviest setting (spread 100 with overlap 100).
- Whether band cycles joined by a turn show visible kinks at the seams. They meet at zero crossings, so it shouldn't show; that's from the frames, not hardware.
- Presets by ear; CPU.
