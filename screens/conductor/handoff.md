# Conductor · handoff

This is the spec for implementing the redesign in [OP-XY-Conductor](https://github.com/mmockett/OP-XY-Conductor) (`display.cpp`, `words.h`, `tools/artwork.py`, `definition.json`).

`gen_frames.py` is the reference for geometry: node shapes, positions and paints all come from it. Regenerate the frames rather than patching them by hand.

**2026-11-02 · revision 1.** This replaces all four pages. No saved parameter changes, so saved projects are unaffected.

## Display block

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 251, "texts": 32, "palette": 16}
```

Set `stateBytes` once `DisplayState` is final (see below).

## Node index map

The index is draw order: low draws first. Shapes are authored at the sizes in `gen_frames.py`; every use stays within scale (0, 2]. Round pools are authored at these radii: dot 7.5, moon 6, halo 10.

| index | pool | n | shape | used by → driven by |
| --- | --- | --- | --- | --- |
| 0–7 | header | 8 | 60 × 20 step | `page_header.hpp` (`kBar`) |
| 8–10 | halo | 3 | circle r 10 | M1: evolve's candidate degrees → scale = planet r × (1 + 1.4 · evolve), position = the planet's |
| 11–22 | segment | 12 | the orbit from pitch class k to k+1, gap 0.06 at each end, 1.6 px ribbon | M1: always shown; paint 6 on the transfer arc (sounding → next chord, short way), else paint 2 |
| 23–26 | ringback | 4 | back half of a ring, r = 1.75 × planet, tilted 30° off the orbit plane | M1: loop planets when sevenths are on (prog jazz or cmplx ≥ 65) |
| 27–34 | cell | 8 | 52 × 6 | M1 phrase track: half-bar h; paint 3 when it belongs to the sounding chord, else 1 |
| 35 | band | 1 | 400 × 15, origin at right end | M4: under the selected lane's route |
| 36–43 | rule | 8 | 400 × 1.2, origin at right end | M2 row baselines; M3 root rows (arp) or voice rows (drum); M4 route lines (x = target column, or 110 when muted/off) |
| 44 | mask | 1 | 116 × 144, paint 0 | M4: drawn over the rules and band, under the moons |
| 45–55 | octave | 11 | 30 × 10.9 | M4 register cells: paint 6 where the lane plays (footprint + xpose, inside the window, not muted); paint 11 inside [low, high]; else paint 8 |
| 56–63 | column | 8 | 1 × 136 | M4 track stations at x = 136 + 30.8 t |
| 64–67 | comb | 4 | graduated edge, 8 teeth at 25 px (beats 6 px, steps 3 px) | M2 and M3 table edges: 0–1 top halves, 2–3 bottom halves; x = 60 + 200·half |
| 68–69 | rulercomb | 2 | as comb, 27 px pitch, teeth up | M1 bar ruler axis at y 177.5 |
| 70–85 | tail | 16 | wedge 23 × 18 | M2: behind the open row's bodies, scale = 0.1 + 0.9 · (gate/100)^0.6; none on drum lanes |
| 86–213 | dot | 128 | circle r 7.5 | M1: 0–6 the degree planets, 7–22 the ruler steps. M2: hits (open row: altitude from oct + role register, scale from vel). M3: notes, beads, skipped rings. M4: route ends |
| 214–217 | ringfront | 4 | front half of the ring | M1, with ringback |
| 218–225 | moon | 8 | circle r 6 | lane l on every page; scale = (0.45 + 1.35 · energy/100) × 4/6, × 1.4–1.65 while lit |
| 226–234 | tick | 9 | 2 × 12 (separators, playhead), 1.2 × 6 (c mark) | M1: 0–6 chord separators, 7 the track playhead, 8 the c mark. M2: 0–7 a bass's lock ticks |
| 235–236 | cap | 2 | 42 × 1.5 | M4: low and high caps |
| 237–244 | strike | 8 | label width + 4 × 1.5 | M2, M4: through a muted lane's label |
| 245 | playhead | 1 | 3 × 148 | M2/M3: the step column (paint 3). M4: the register spine (paint 2) |
| 246 | bracket | 1 | 2 × row height | M2, M4: beside the selected lane |
| 247–250 | pagemark | 4 | 116 × 2 | the shown page only |

M1's planets are positioned by the 3D model in `gen_frames.py`, not by hand: one camera at 10.9° elevation and distance 9. Planet size comes from depth, as `pc_angle` / `project` / `px_per_unit` compute it.
- On the device, precompute the twelve pitch-class positions and their depth factors as a Q10 table. Key and scale only ever pick from those twelve.
- While turning key, ease each planet's angle and look the position up along the orbit, so planets travel round it, not across.

## Palette map (paints: fill, stroke, width)

| # | fill | stroke | width | for |
| --- | --- | --- | --- | --- |
| 0 | `#000000` | `#000000` | 0.2 | the mask |
| 1 | `#323232` | `#323232` | 0.3 | ground fills: band, cells, halos |
| 2 | `#4B4B4B` | `#4B4B4B` | 0.3 | hairlines: orbit, rules, edges, stations, tails |
| 3 | `#646464` | `#646464` | 0.3 | quiet marks, the sounding chord's span, the playhead |
| 4 | `#7D7D7D` | `#7D7D7D` | 0.3 | rings, beads, the c mark |
| 5 | `#969696` | `#969696` | 0.3 | hits, kicks, separators, strikes |
| 6 | `#AFAFAF` | `#AFAFAF` | 0.3 | accents, transfer arc, lit cells, track playhead, page mark |
| 7 | `#CDCDCD` | `#CDCDCD` | 0.3 | what a note just hit, bracket, caps |
| 8 | `#000000` | `#4B4B4B` | 1.0 | hollow ground: register cells outside the window |
| 9 | `#000000` | `#646464` | 1.0 | hollow quiet: off lanes, other degrees, skipped steps |
| 10 | `#000000` | `#969696` | 1.2 | hollow second: may-vary bodies, notes still to come |
| 11 | `#323232` | `#646464` | 1.2 | dark body: evolve candidates, plain ruler steps, the register window |
| 12 | `#323232` | `#7D7D7D` | 1.2 | a lane at rest |
| 13 | `#323232` | `#969696` | 1.5 | the loop's chords |
| 14 | `#323232` | `#CDCDCD` | 2.0 | the sounding chord |
| 15 | `#969696` | `#AFAFAF` | 1.2 | a lane that just played |

Every node uses fill-and-stroke paint from this table. **Pending device:** whether a paint's stroke width scales with node scale. If it does, small bodies thin out; check M1's ruler steps and dens-0 moons first.

## Text slot map

Slots 0–15 are the header's. A slot's colour and size are fixed in the fragment, so state changes by *moving a string to a slot of the right colour* (the way `kPageLabel` / `kOtherPages` already work).

| slots | size | colour | M1 | M2 | M3 | M4 |
| --- | --- | --- | --- | --- | --- | --- |
| 16 | 10 | `#CBCBCB` | shown page name | ← | ← | ← |
| 17–19 | 10 | `#7D7D7D` | other page names | ← | ← | ← |
| 20 | 10 | `#CBCBCB` | sounding chord's label (`C 1`) | selected lane (`5 arp`) | lane title (`5 arp`) | selected lane |
| 21–23 | 10 | `#969696` | the other loop chords' labels | lanes, in order | top / bottom range label, root label | lanes |
| 24–27 | 10 | `#969696` | (spare) | lanes | — | lanes |
| 28–30 | 10 | `#7D7D7D` | non-loop degrees' labels | — | drum voice names (8, using 21–28) | track numbers (spaced strings) |
| 31 | 20 | `#CBCBCB` | the plate title: sounding chord (`Fm`) | — | — | — |

The frames also use these, which need a slot each:
- M1's `next G` and `evolving`/`frozen` lines (10 px, `#7D7D7D`).
- M3 drum's eight voice names.

This table is the starting allocation. Re-balance it in `artwork.py` once the final strings are known; the frames' colours are what it has to reproduce.

## What the control must tell the display (`words.h`)

These are new words, on top of today's.

| page | needs | why |
| --- | --- | --- |
| M1 | each lane's energy (dens + lane dens − 50, 7 bits × 8) | moon size |
| M1 | the evolve candidates (≤ 3 degrees) | halos. Candidates = degrees `build()` could pick for chords 2–4 from the current table |
| M1 | the kick bitmap after cmplx displacement (already in `kPhraseRhythm`); swing value | ruler |
| M2 | per hit: velocity (2 bits: soft, mid, accent) for all lanes; the open lane's 16 velocities and gates (4 bits each), its may-vary bitmap (seeded) | body size, tails, hollows |
| M3 | per note: start step, length in steps, accent, skipped | bodies, beads, rings |
| M4 | the selected lane's pitch footprint (lowest, highest note this phrase) | register cells |

## DisplayState

- `PageHeader header` (as today).
- `u16 glow[8]` (as today; drives paints 12 → 15 and the moon scale).
- Eased Q10 values for:
  - M1: planet angles (7), moon positions (8 × 2), halo scale (3), ruler swing offset (1).
  - M2: open-row height and position (1), body altitude (1), tail scale (1).
  - M4: route ends (8), caps (2).
- That's roughly 50 × 2 bytes, plus the header. Set `stateBytes` to match.

## Path key policy

There are no mutable outlines, so there are no keys.

## Open device checks

1. Caption and label widths in Univers Next Pro Light, especially planet labels like `Bdim 2·4` and M4's spaced track numbers.
2. Redraw: rest = 0; a chord change while playing (≈ 26 peak); turning key with cmplx ≥ 65 (rings on).
3. Whether palette stroke widths scale with node scale.
4. Moons overdraw planets regardless of depth (index order); confirm it reads.
5. Photos: M1 rest, M1 playing, M2 playing at dens 100, M4 with a muted lane.
6. The audible scores in `brief.md`, by ear.
7. A ruling on two-state switches and unordered enums in `opxy/audit.md` (see `review.md`).
