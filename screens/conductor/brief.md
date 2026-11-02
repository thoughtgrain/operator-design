# Conductor · screen brief

This folder revises the four pages of [mmockett/OP-XY-Conductor](https://github.com/mmockett/OP-XY-Conductor) against `opxy/protocol.md`. The machine and its code are Matt Mockett's; this folder only holds the design.

**Current design: revision 2.** These are the four designs Brian picked from the concept rounds.

| page | design | generator | frames | sheets |
| --- | --- | --- | --- | --- |
| M1 song | arc diagram | `gen_frames2.py` | `frames2/m1/` | `rev2/contact-m1.png` |
| M2 lanes | notches | `gen_frames2.py` | `frames2/m2/` | `rev2/contact-m2.png` |
| M3 lane | isometric stairs | `gen_frames2.py` | `frames2/m3/`, `frames2/m3-drum/` | `rev2/contact-m3.png` |
| M4 route | circuit traces | `gen_frames2.py` | `frames2/m4/` | `rev2/contact-m4.png` |

The film is `rev2/conductor-pages.mp4`, made by `anim_all.py`. Revision 1 (the harmonic orrery) is kept in `rev1/` for the record, along with `gen_frames.py` and `anim_m1.py`. Revision 2 still imports `gen_frames.py` for the musical stand-in and the header.

## How we got here

Brian's notes on each round drove the next one:

1. **Orrery (rev 1).** Too busy, and the lane dots on the song page meant nothing. Outcome: no moons on M1, only the loop's chords labelled.
2. **No grey fills.** Fills only where they show depth or shaping; every body became an outline.
3. **One lane at a time on M2,** and a calmer M3.
4. **"Not everything needs to be a circle or a square."** This started five shape languages per page (`concepts.py` → `concepts/m1.png` … `m4.png`).
   - Picked: **M1 5, arc diagram** and **M4 4, circuit traces**.
5. **Round 2** for M2 and M3 (`concepts2.py` → `concepts/m2b.png`, `m3b.png`).
   - M2 6 (arches) was built first. Brian then corrected it to **M2 8, notches**.
6. **Round 3, the arp as stairs** (`concepts3.py` → `concepts/m3c.png`).
   - Picked: **M3 13, isometric stairs**.

## 0 · Screen or stock page?

**Subject:** one song that eight lanes follow. That's one chord loop and one groove in the key and scale. M1 draws the loop as arches between the chords that make it; the other pages draw one lane's part of it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `conductor` |
| Kind | `synth`: a silent engine on aux track 12 that plays tracks 1–8 through track control |
| What it does | Decides *what* tracks 1–8 play: one chord loop and one groove every lane leans on, changing a little each four-bar phrase |
| Controls | M1: 8 saved controls (two pages). M2, M3 (by role) and M4: 8, 8 and 6 per lane |
| Control source | existing XY definition |

### 1B · Definition review

`lint_definition.py ../op-xy-conductor/definition.json` → 2 errors, 2 warnings. None is a definition fault:

- **`hidePages` and 32 texts.** These come from the dev SDK branch Conductor needs (open-xy #345), and the checker doesn't know them yet.
- **`hrate` labels.** The display shows `1/2 · 1 · 2 · 4`, which fit the column.
- **`voiceCapacity` 1.** The engine is silent, so one voice is correct.

No parameter changes are proposed, so saved projects are unaffected.

One string change: page names become **song / lanes / lane / route** (`kPageNames`), because `conductor` is over the 8-character label rule.

## 2 · Listen and rank

I scored these from `generator.h`, not by ear. **They are pending your confirmation by ear.**

| page | control: score |
| --- | --- |
| M1 | key 3 · scale 3 · prog 5 · dens 4 · cmplx 3 · hrate 4 · swing 3 · evolve 2 |
| M2 | lane 3 · role 5 · dens 4 · oct 4 · vel 3 · vary 2 · lock 3 (bass only) · gate 3 |
| M3 (arp) | mode 4 · rate 4 · range 4 · steps 3 · skip 3 · accent 2 · tones 3 · jump 2 |
| M4 | lane 3 · to 5 · xpose 3 · mute 5 · low 3 · high 3 |

## 3 · Subject and language

**One language across the four pages:** a line drawing on a ground line, in outlines only, in grey only.

| page | what each part means |
| --- | --- |
| M1 · arc diagram | The twelve pitch classes along a line, and the scale's degrees as triangles under it (the loop's larger). The loop is an arch from each chord to the next, numbered in order; the arch sounding now is the brightest thing on the page. Below the line are the phrase line (where chords change) and the bar's groove (kicks tallest). |
| M2 · notches | The selected lane's bar as a ruler's edge, with a V cut for each note. Velocity sizes the V, a tick shows where it lets go (gate), and accents get a mark under the point. Notes that may vary are smaller and quiet. Oct raises or lowers the edge. |
| M3 · isometric stairs | The arp as a staircase seen in 3D: each note a tread with depth at its pitch, each leap a riser. Accents are brighter treads. Drum lanes use the same treads on eight voice rows. |
| M4 · circuit traces | Eight track buses at the right. Each lane runs along its row and lands on its track's bus with a pad, hopping over the buses it passes. The selected lane's register window sits along the bottom. |

## 4 · Map and budget

### M1 · song

| control | channel | what moves |
| --- | --- | --- |
| key | position | Triangles, labels and arches slide along the line, 36.4 px a semitone |
| scale | position | Degrees move between pitch-class ticks |
| prog | shape | The arches re-route between different chords |
| dens | count | Kicks in the groove, 2 → 6 per bar |
| cmplx | position + text | Kicks pulled off the beat; chord labels gain a 7 at ≥ 65 |
| hrate | count | Separators on the phrase line, 7 → 0 |
| swing | position | Offbeat ticks in the groove move late, up to 11 px |
| evolve | scale | The degrees evolve could swap in grow, 1 → 1.8× |

### M2 · lanes

| control | channel | what moves |
| --- | --- | --- |
| lane | whole page | Which lane is shown |
| role | count + shape | The notches change; drum lanes have no gate ticks |
| dens | count | Number of notches |
| oct | position | The edge moves 14 px per octave |
| vel | scale | Notch size, 0.45 → 1.5× |
| vary | scale + shade | Notes that may vary shrink to 0.75× and go quiet |
| lock | position | On a bass lane, the notes follow the lock and ticks mark the locked steps |
| gate | position | A tick on the edge where the note lets go |

### M3 · lane (arp)

| control | channel | what moves |
| --- | --- | --- |
| mode | shape | The order of the steps |
| rate | count | Number of treads |
| range | position | The span of the stairs |
| steps | shape | How long before the pattern repeats |
| skip | count | Gaps in the stairs |
| accent | shade | Brighter treads |
| tones | position | Chord tones or scale tones |
| jump | position | Treads lifted an octave |

### M4 · route

| control | channel | what moves |
| --- | --- | --- |
| lane | position | Bracket, bright trace, and the register strip |
| to | position | The trace slides to a new bus, 22.4 px a track |
| xpose | shade | Lit octaves on the register strip |
| mute | position | The trace slides back behind the names, and a strike crosses the name |
| low / high | position | Window caps on the register strip |

### Budget

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 245, "texts": 32, "palette": 16}
```

The four page designs need 245 of the 256 nodes. Three device facts shaped them:

- **No mutable outlines.** Everything is a fixed shape moved by translation and a uniform scale.
- **No static art** beyond the page strip's hairline, because static art would show on every page.
- **The palette is sixteen paints.** Each paint sets fill, stroke and width.

Redraw, at the worst moments:

| case | changed nodes per frame |
| --- | --- |
| at rest | 0 |
| playing, M1 | ≈ 3: the playing step tick, the playhead, and one phrase segment at each chord change |
| playing, M2 / M3 | ≈ 3: the playhead and the sounding notch or tread |
| chord change, M1 | ≈ 12, once: 4 arches restyle, plus triangles and labels |
| turning key | 7 triangles + 4 arches + labels each frame of the 0.2 s ease. **Pending device** |

## Open

These are listed in priority order in `review.md`:
- **The perceptibility floors.** Outline-only drawings fall under them.
- **"Picture, not panel"** (`craft.md`, added today). It would move the strips off the resting pages.
- **The M3 mode fix.**
