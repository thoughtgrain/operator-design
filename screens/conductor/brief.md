# Conductor · screen brief

Revision of [mmockett/OP-XY-Conductor](https://github.com/mmockett/OP-XY-Conductor)'s four pages, run through `opxy/protocol.md`. The machine and its code are Matt Mockett's; this folder only holds the design. Frames come from `gen_frames.py`, so nothing here is hand-patched.

## 0 · Screen or stock page?

**Subject in one sentence:** one song that eight lanes follow, drawn as a harmonic orrery: the scale's seven chords are planets on a graduated orbit, and the eight lanes are moons that ride with whichever chord is sounding.

It clearly earns a screen. Conductor has no sound of its own, so the stock page would show eight numbers and nothing about what the song is doing.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `conductor` |
| Kind | `synth` (silent engine on aux track 12; plays tracks 1–8 through track control) |
| Sounds like | Whatever is loaded on tracks 1–8. Conductor decides *what* they play: one chord loop and one groove that every lane leans on, changing a little each four-bar phrase. |
| Controls | 8 saved on M1 (two pages, `"press": "page"`), plus 8 per-lane controls each on M2, M3 (by role) and M4 (6 used) |
| Control source | existing XY definition |

### 1B · Definition review

`python3 opxy/tools/lint_definition.py ../op-xy-conductor/definition.json` → 2 errors, 2 warnings.

| finding | resolution |
| --- | --- |
| E `hidePages` is an unknown field | The checker mirrors the SDK on `staging`; `hidePages` comes from the dev SDK branch Conductor needs (open-xy #345). Not a definition fault. I'm leaving it and flagging that the checker needs to learn the field once it lands. |
| E `texts` 32 > 16 | Same reason: sixteen display words plus the header's sixteen come from `sdk/control-notes`. Again, the checker needs to catch up. |
| W `hrate` labels over 5 characters | The definition's labels (`0.5 bar`…) are only stored. `display.cpp` shows `kHarmonyNames` (`1/2`, `1`, `2`, `4`), which fit. Justified. |
| W `voiceCapacity` 1 | The engine is silent and plays other tracks' machines. Justified. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | dens, cmplx, swing, evolve rise; key/scale/prog/hrate are enums |
| Header values in real units, ≤ ~5 chars | pass | longest is `drone`, `chord`, `hmin` (measured with the device glyph table in `display.cpp`) |
| Defaults plainest useful; presets sound good | **pending device** | can't judge by ear from here |
| Engine page holds only the sound's own parameters | pass | all eight are song-level |
| Page 1 holds what's played most | pass | key, scale, prog, dens |
| Port parity | n/a | not a port |
| Saved sounds compatible | pass | no parameter changes proposed; this revision is display-only |
| `id` final | pass | `conductor` |

### Captions

Unchanged from the machine. One text change: the page strip names become **song / lanes / lane / route**, because `conductor` is 9 characters, over the 8-character label rule (`kPageNames` in `specs.h`).

## 2 · Listen and rank

I scored these from the generator code, not by ear, so **please confirm or correct them**. Perceptibility is checked against these numbers, and I never lowered one to make a control pass.

**M1 (song)**

| control | what it does to the sound | score |
| --- | --- | --- |
| key | transposes everything | 3 |
| scale | changes three or four chord qualities and every melody | 3 |
| prog | a different chord loop | 5 |
| dens | kick count 2–6 per bar, plus every lane's energy | 4 |
| cmplx | kick displacement, sevenths at ≥ 65, every lane's complexity | 3 |
| hrate | chords last ½–4 bars | 4 |
| swing | offbeats up to 10/24 of a step late | 3 |
| evolve | up to 35 % change a phrase; heard over time | 2 |

**M2 (lanes)**

| control | score |
| --- | --- |
| lane | 3 (a selector; given 3 so it's held to a floor) |
| role | 5 |
| dens | 4 |
| oct | 4 |
| vel | 3 |
| vary | 2 |
| lock | 3 (bass only, see `generator.h`) |
| gate | 3 |

**M3 (arp role)**

| control | score |
| --- | --- |
| mode | 4 |
| rate | 4 |
| range | 4 |
| steps | 3 |
| skip | 3 |
| accent | 2 |
| tones | 3 |
| jump | 2 |

**M4 (route)**

| control | score |
| --- | --- |
| lane | 3 |
| to | 5 |
| xpose | 3 |
| mute | 5 |
| low | 3 |
| high | 3 |

## 3 · Subject

| candidate | pattern | verdict |
| --- | --- | --- |
| A · current screens | none (dashboard) | Rejected. Five zones on M1 and four white elements tie for brightest. Swing, evolve, cmplx and hrate have no channel. Several states rely on shade alone, and parts sit under 3:1. |
| B · barrel organ | P13 Capture | Strong metaphor (a pinned barrel replays exactly until re-pinned), but turning it moves ~128 pins a step, far over the redraw budget. |
| C · harmonic orrery | P12 Orrery | **Chosen by Brian.** Cheapest redraw, and it reuses `library/meikyu-orrery/`. |
| D · engraved score | P11 | Most literal; its staves turn into hatching at 1:1. |

**Drawing language:** an ephemeris plate from a star atlas.
- Bodies are outlines over dark fills.
- Orbits and graduations are hairlines.
- Tracks carry bodies at intervals.
- Small labels sit in a mid grey.

**Reference:** `library/meikyu-orrery/`.

The one idea that ties all four pages together: **every lane is a moon, on every page**. A moon's size is how much the lane plays; it's hollow when the lane is off or muted, and it lights when the lane plays.

## 4 · Map and budget

### M1 · song

| control | channel | part | travel | what the player sees |
| --- | --- | --- | --- | --- |
| key | rotation | the seven planets round the 12-tick orbit | 0 → 330° | the whole chord set turns; the `c` tick stays put as the reference |
| scale | position | planets slide between pitch-class ticks | 1 tick each (≈ 20–100 px) | the scale's shape on the orbit; chord names re-case (`Dm` → `D`) |
| prog | count + fill | loop planets solid and 1.85×, the rest hollow; transfer arc | 4 planets, arc up to 6 segments | which chords the loop uses, with each one's position in its label (`Am 3`) |
| dens | scale | moons 0.45× → 1.8×; kick bodies on the ruler | 2 → 6 kicks | the lanes swell as they play more |
| cmplx | position | moons scatter from a neat row onto eccentric orbits; ringed planets at ≥ 65 | up to 2 × orbit radius | a busy, irregular system; sevenths get Saturn rings |
| hrate | count + shade | the phrase track's half-bar cells and the separators between chords | 7 → 0 separators; lit span 54 → 432 px | how long each chord holds |
| swing | position | offbeat bodies on the bar ruler move late (right) and plot low | 11 px right, 20 px down | lag drawn as depth below the on-time axis |
| evolve | scale | dark halos round the degrees evolve could swap in | 1× → 2.4× planet radius | which chords might arrive next phrase, and how likely; halos collapse on freeze |
| note | scale + shade | lit moons 1.4× in the bright greys; playhead on track and ruler | — | the ensemble firing round the sounding chord |

### M2 · lanes

All eight rows are always visible. The selected lane's row opens to 52 px.

| control | channel | travel |
| --- | --- | --- |
| lane | position | which row opens |
| role | count + position | the hits, their register band and the tails all change; an off lane's open row is sixteen hollow rings |
| dens | count | hits added and removed |
| oct | position | the open row's bodies rise 7 px an octave (28 px over −2…+2) |
| vel | scale | bodies 0.8× → 1.9× |
| vary | fill | bodies that may change go hollow (wireframe), 0 → all |
| lock | position | the bass's hits move to the kick, the accents or its own grid; lock ticks under the row |
| gate | scale | comet tails 0.1× → 1× behind each body |

### M3 · lane (arp)

Pitch runs up the page and time across it.
- Notes are bodies, and accents are 1.5×.
- A held note trails beads.
- A skipped step is a hollow ring.
- Root rows get a hairline rule plus range labels.
- There is no per-cell grid any more.

Every arp control moves bodies: mode reorders them, rate and steps change the count, range adds rows, skip leaves hollow rings, accent scales bodies, tones swaps the pitch set, and jump lifts bodies an octave. Drum lanes get eight labelled voice rows instead.

### M4 · route

| control | channel | travel |
| --- | --- | --- |
| lane | position | bracket, ground band and the register panel's footprint |
| to | position | the route line slides out from behind the lane column to its track; 30.8 px a track |
| xpose | position | the lit octave cells shift ±2 octaves |
| mute | position + fill | the line and band retract behind the mask, the end body goes, a strike crosses the name, the moon goes hollow, and the register cells go dark |
| low / high | position + shade | the window caps move; cells outside the window go black |

### Budget

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 251, "texts": 32, "palette": 16}
```

Three device facts shaped this budget:

- **No mutable outlines.** Lines span up to 400 px and a mutable outline only reaches ±64 px, so every moving part is a translated or uniformly scaled node.
- **No per-page static art.** Static artwork shows on every page, so each page's furniture (orbit, graduated edges, stations, the mask) is a node the other pages hide. The only static art is the hairline under the page strip.
- **The palette is paints, not colours.** Each entry lends fill, stroke and width together, so the sixteen entries are sixteen paints. `gen_frames.py` refuses any other combination.

251 of 256 nodes are spoken for; `handoff.md` has the pools. `stateBytes` is set during implementation (eased values, glow).

| case | changed nodes / frame |
| --- | --- |
| at rest | 0 |
| playing, defaults (16ths) | avg ≈ 8: one ruler body, the track playhead, up to 6 moon glows fading |
| playing, chord change (heaviest, M1) | peak ≈ 26 over 0.2 s (8 moons move, 2 planets restyle, ≤ 6 arc segments, ≤ 7 labels), then ≈ 8 |
| playing, M2 at dens 100 | avg ≈ 12: the playhead, ≤ 8 hits brightening, moon glows |
| turning key (worst turn) | 7 planets + 8 ring halves + 8 moons + labels each frame of the 0.2 s ease. Turns aren't notes, but this is **pending device** |
