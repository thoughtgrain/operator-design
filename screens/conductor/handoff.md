# Conductor · handoff (revision 2)

This is the spec for implementing the redesign in [OP-XY-Conductor](https://github.com/mmockett/OP-XY-Conductor): `display.cpp`, `words.h`, `tools/artwork.py` and `definition.json`. `gen_frames2.py` is the geometry reference. Its `SHAPES`, `POOLS` and `PAINTS` are the fragment's node shapes, index order and palette. Regenerate the frames rather than patching them.

**2026-11-02 · revision 2.** This replaces revision 1 (the orrery, in `rev1/`). No saved parameter changes. One string change: `kPageNames` becomes `song, lanes, lane, route`.

**Before implementing:** settle the open items in `review.md`. The floors and "picture, not panel" can still move parts of this map.

## Display block

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 245, "texts": 32, "palette": 16}
```

## Node index map (index order is draw order)

| index | pool | n | shape (authored) | used by |
| --- | --- | --- | --- | --- |
| 0–7 | header | 8 | 60 × 20 step | `page_header.hpp` |
| 8–15 | bus | 8 | 1 × 128 | M4: track buses at x = 300 + 22.4 t |
| 16–27 | rule | 12 | 430 × 1.2, origin at right end | M1: line and groove baseline. M2: the edge. M4: lane traces, slid so the end lands on the bus |
| 28 | mask | 1 | 70 × 140, black | M4: hides the traces' left ends behind the lane names |
| 29–48 | hopgap | 20 | 6 × 4, black | M4: where a trace crosses a bus it doesn't join |
| 49–68 | hop | 20 | half-ellipse r 4, stroke only | M4: the hop over that bus |
| 69–76 | pad | 8 | diamond 3.5 | M4: where a trace joins its bus |
| 77–87 | octseg | 11 | 32 × 1.6 | M4: register strip, an octave each |
| 88–89 | cap | 2 | 1.6 × 12 | M4: low and high window caps |
| 90–97 | cell | 8 | 52 × 1.6 | M1: phrase line, half a bar each |
| 98–109 | pctick | 12 | 1 × 6 | M1: pitch-class ticks on the line |
| 110–113 | arc | 4 | half-ellipse rx 102 × ry 51, stroke only | M1: the loop's links. x = midpoint, scale = half-span / 102 |
| 114–120 | tri | 7 | triangle 4 | M1: degrees (scale 0.9 other, 1.3 loop, 1.5 sounding, up to 1.8 evolve candidates) |
| 121–136 | stepS | 16 | 1.2 × 4 | M1: plain groove steps. M2: gate ticks |
| 137–142 | stepT | 6 | 1.6 × 13 | M1: kicks. M2: a bass's lock ticks |
| 143–144 | stepM | 2 | 1.4 × 8 | M1: backbeats |
| 145–152 | tick | 8 | 1.4 × 10 | M1: chord separators (7) and the phrase playhead. M2: accent marks |
| 153–160 | lanetick | 8 | 1.2 × 6 | M2: lane index |
| 161 | lanemark | 1 | 2 × 14 | M2: the shown lane in the index |
| 162–177 | notchgap | 16 | 16.8 × 2, black | M2: opens the edge where a notch is cut |
| 178–193 | notch | 16 | V ribbon, half-width 9, depth 26 | M2: notes, scale = 0.45 + 1.05 · vel/100 (× 0.75 if may vary) |
| 194–198 | octmark | 5 | 6 × 1.2 | M2: octave positions of the edge |
| 199–206 | riserS | 8 | 0.4 × 12, stroke only | M3: leaps under 24 px, scale = leap / 12 |
| 207–214 | riser | 8 | 0.4 × 60, stroke only | M3: longer leaps, scale = leap / 60 |
| 215–230 | tread | 16 | parallelogram 23 wide, depth (9, −6), stroke only | M3: notes; drum hits on voice rows |
| 231 | playhead | 1 | 1.5 × 120 | M2, M3: the step column |
| 232 | bracket | 1 | 2 × 13 | M4: beside the selected lane |
| 233–240 | strike | 8 | 46 × 1.5 | M2, M4: through a muted lane's name (scaled to the name's width) |
| 241–244 | pagemark | 4 | 116 × 2 | the shown page |

**Draw order is load-bearing.**
- M4: bus → rule → mask → hopgap → hop → pad.
- M2: rule → notchgap → notch.
- M3: risers before treads.

## Palette (paints: fill, stroke, width)

| # | fill | stroke | width | for |
| --- | --- | --- | --- | --- |
| 0 | `#000000` | `#000000` | 0.2 | mask, hop gaps, notch gaps |
| 1 | `#323232` | `#323232` | 0.2 | page strip hairline |
| 2 | `#4B4B4B` | `#4B4B4B` | 0.2 | ground lines, buses, pitch-class ticks |
| 3 | `#646464` | `#646464` | 0.2 | quiet marks, playhead, notes that may vary |
| 4 | `#7D7D7D` | `#7D7D7D` | 0.2 | beats, gate ticks |
| 5 | `#969696` | `#969696` | 0.2 | traces, notches, kicks, separators |
| 6 | `#AFAFAF` | `#AFAFAF` | 0.2 | accents, lit register, page mark |
| 7 | `#CDCDCD` | `#CDCDCD` | 0.2 | the step playing, selection, caps |
| 8 | none | `#646464` | 1.5 | other degrees, hops, risers |
| 9 | none | `#7D7D7D` | 1.5 | evolve candidates |
| 10 | none | `#969696` | 1.5 | loop degrees, pads |
| 11 | none | `#969696` | 1.6 | treads |
| 12 | none | `#AFAFAF` | 1.6 | accented treads |
| 13 | none | `#CDCDCD` | 2.2 | the sounding arch, the tread just hit |
| 14 | none | `#646464` | 1.5 | arches not sounding |
| 15 | none | `#CDCDCD` | 1.6 | sounding degree, selected pad and hops |

"none" paints use stroke-only paint, so overlapping arches, hops and treads don't hide each other. **Pending device:** whether stroke width scales with node scale.

## Text slots

Slots 0–15 are the header's; 16–19 hold the page strip (one bright slot, three grey). A slot's colour is fixed, so the selected item's string moves into the bright slot.

| page | slots 20+ |
| --- | --- |
| M1 | title (20 px, bright) · `next X` · four chord labels (one bright for the sounding chord) · four arch numbers · `frozen` |
| M2 | title `5 arp` (20 px, bright) |
| M3 | two range labels · corner label (or eight drum voice names) |
| M4 | eight lane names (one bright) · two spaced strings for the bus numbers (a digit plus six spaces = 22.4 px in Univers) |

## What the control must tell the display (`words.h`)

| page | new words |
| --- | --- |
| M1 | the kick bitmap after cmplx displacement (already in `kPhraseRhythm`), the swing value, and the evolve candidates (≤ 3 degrees) |
| M2 | the shown lane's 16 velocities (or 2-bit soft / mid / accent), its gate, its may-vary bitmap, and a bass's lock steps |
| M3 | per note: step, pitch, accent, skipped |
| M4 | the selected lane's pitch footprint for the phrase |

## DisplayState

- `PageHeader`.
- Eased Q10 values for:
  - M1: triangle x (7), arch midpoint and scale (4 × 2), separators (7), offbeat swing offset.
  - M2: edge y, notch scale.
  - M3: tread y (16), riser scale.
  - M4: trace ends (8), caps (2).

Roughly 70 × 2 bytes; set `stateBytes` to match.

## Open device checks

1. Stroke width under node scale (arches, notches, risers, hops).
2. Caption and label widths in Univers Next Pro Light, including M4's spaced bus numbers.
3. Redraw: a chord change on M1, and turning key.
4. Photos: M1 playing, M2 at dens 100, M3 arp playing, M4 with a re-route and a mute.
5. The audible scores in `brief.md`, by ear.
6. Rulings on the perceptibility floor for outline drawings, two-state switches and unordered enums.
