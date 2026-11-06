# Ferry · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a ferry working a timetable between ports that are the held chord's tones, calling at them in route order, held up by swell, and waiting at each for the dwell before it plays that tone.
- Not the stock page: there is one scene the rule acts on (a route between ports), and every control changes it. The stock player page is 24 on/off dots and binds no nodes, so ferry runs as a track-control synth on aux track 12 (SDK 1.9) with its own page on M1.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `ferry` |
| Kind | synth + `resources.trackControl` (SDK 1.9, aux track 12, unique) |
| Category | player |
| Colour | grey (default) |
| Sounds like | No sound of its own: it plays the target track's engine. Hold a chord and it walks the chord's tones one at a time in a set order, an arpeggio with a timetable; swell makes the calls late and uneven, like a boat pushed off schedule. |
| Controls | 4: route, ports, swell, dwell (one page, stock header) |
| Control source | new (the DSP is the control code I'm writing) |
| Mute | Mute is the machine's bypass. The control code reads `control::Input.muted` and passes it to the display in its `Overlay::display` words; the page must show muted by more than shade (each candidate names how in its risks). |

### 1A · Definition (new machine, so the "source" is the control code)

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route | 5 orders: up, down, shuttle, cross (outside in), tramp (seeded random) | 0 | route | enum `up down shtl cross tramp` | enum | 0 (up) | keep | Labels ≤ 5 characters to fit the 20 px value; `shtl` is shuttle |
| ports | 2..8 calls per cycle: the held chord's tones, then their octaves up | 1 | ports | enum `2`..`8` | enum | 0.3333 (4) | keep | An enum of counts so the header shows the integer, not a percent |
| swell | 0..1 of a slot, random lateness per call (seeded per cycle) | 2 | swell | linear 0..1 | percent | 0 | keep | Colouring control, defaults to 0 (dead on time) |
| dwell | slot length, tempo-synced | 3 | dwell | linear 0..1 | division | 0.5 | keep | Clockwise lengthens the stay; assumes the host's division table runs short → long clockwise (**pending SDK check**) |

Integer conversion: none; new machine.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/ferry/definition.json` → 0 errors, 1 warning.

| warning | resolution |
| --- | --- |
| `voiceCapacity 1; stock plays up to 8 notes per track` | Justified: ferry runs on aux track 12, which the SDK keeps silent. It makes no voices of its own; it steers the target track, so one placeholder voice is all it needs (same as the other track-control players here). |

The `trackControl` note (show muted on the page) is carried into Intake above and into every candidate's risks.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes, one pending | route and ports step forward through their lists; swell rises; dwell lengthens only if the division table runs short → long (pending SDK) |
| Header values in real units, ≤ ~5 chars | yes | `up`/`tramp`, `2`..`8`, `0`..`100`, `1/32`..`1/2` |
| Defaults plainest useful; presets sound good (by ear) | defaults yes; presets **pending device** | up, 4 ports, swell 0, 1/8 is a plain arpeggio; Crossing = defaults, Squall = tramp, 8 ports, swell 60 %, shorter dwell |
| Engine page holds only the sound's own parameters | yes | All four are the rule's own; no envelope or LFO |
| Page 1 holds what's played most | yes | One page |
| Port parity: nothing silently lost | n/a | New machine |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | yes | `ferry` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | route | up..tramp | order | up | `up` / `shtl` / `tramp` | 26 / 51 / 64 | `tramp` no (64 px), pending device measure |
| 2 | ports | 2..8 | calls | 4 | `2` / `5` / `8` | 13 | yes |
| 3 | swell | 0..100 | % | 0 | `0` / `50` / `100` | 13 / 26 / 38 | yes |
| 4 | dwell | 1/32..1/2 | division | 1/8 | host-drawn division | ~51 for `1/32` | yes, pending host table |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. `tramp` is the one estimated over (it runs into the next column's title area); fallback is `rand` if the device measure agrees.

Page 1 (played most): route, ports, swell, dwell · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear: there is no audio render yet, so these come from what the control code does to the note stream.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | route: the melodic contour changes outright (rising, falling, turning, leaping, random) though the notes and rhythm stay the same | 3 |
| 2 | ports: 2 → 8 calls, from a two-note trill to a three-octave run; changes range, cycle length and how the line feels | 4 |
| 3 | swell: nothing at 0, loose and human by 30, staggering and lurching at 100; subtle at the low end | 2 |
| 4 | dwell: the rate, 1/32 to 1/2, from a blur to a slow call every half bar; the most dramatic | 5 |

## 3 · Subject

Five candidates, one per direction in `passes/01-subject/pass.json` (state `ready_for_pick`, every pair differs in pattern and language, subject overlap ≤ 0.13). Full text in each `vN/candidate.json`; rest sketches in `vN/rest.svg`, generated by `passes/01-subject/sketch.py`; notes and ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P5 Field and figure | engineering schematic | Ferry in side elevation on a receding sea mesh, timing diagram of the timetable underneath | route: strip contour · ports: strip pulse count · swell: sea waves + hull heel · dwell: strip slot count | owner's pick |
| v2 | P12 Orrery | oscilloscope trace | X-Y graticule, an orbit per octave, ports by pitch class, beam spot as ferry | route: lit arcs · ports: point count across orbits · swell: orbit ripple · dwell: spot size | owner's pick |
| v3 | P13 Capture | typeset diagram | Bay in plan, piers spaced by interval, dashed capture rings, numbered legs | route: legs · ports: piers · swell: leg roughness · dwell: ring radius | owner's pick |
| v4 | P14 Loom | orthographic elevation | Timetable woven as cloth in elevation, slabs raised to pitch, rows per voyage | route: skyline · ports: levels · swell: slabs slip late · dwell: thread count | owner's pick |
| v5 | P4 Stack in depth (stretch) | survey plan | Survey sheets of each port stacked in route order, berth as long as dwell | route: stack order (labels) · ports: sheet count · swell: contours · dwell: berth length | owner's pick |

Chosen: pending, the owner's pick.
