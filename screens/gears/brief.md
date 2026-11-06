# Gears · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: two meshed wheels whose teeth play notes as they meet, the ratio between their sizes drawn as the polyrhythm between their revolutions.
- A screen, not stock: the machine's rule is already a physical object (gears), so there's one thing every control acts on. Which drawing of it is the subject pass's question (`passes/01-subject/`).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `gears` |
| Kind | synth + `resources.trackControl` (SDK 1.9, aux track 12) |
| Category | player |
| Colour | grey (default) |
| Concept | Interlocking gears: each tooth that meshes plays a note, ratios between wheels make polyrhythms. |
| Sounds like | A note player for another track. Driver wheel A (teeth) meshes with follower B (teeth × ratio); one tooth pair meets per step and plays a note picked from the scale by the two teeth's places on their wheels, so A's revolution against B's is a polyrhythm (3:2 at the default, repeating every 24 steps). |
| Controls | 4: ratio, teeth, mesh, scale |
| Control source | new |

Muted: mute is a track-control machine's bypass, so the page must show it (`constraints.md`, Which machines draw a screen). Each candidate says how in its risks; the control code passes `muted` to the display in its `Overlay::display` words.

### 1A · Definition (new machine; "source" is the DSP I'm writing)

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| follower:driver ratio | 9 ratios, ascending by value 1:1 … 3:1 / default 3:2 | 0 | ratio | enum `1:1 5:4 4:3 7:5 3:2 5:3 7:4 2:1 3:1` | enum | 0.5 (3:2) | keep | Clockwise raises the ratio. Non-integer B tooth counts round to the nearest whole tooth |
| driver teeth | 3–16, integer / default 8 | 1 | teeth | enum `3`…`16` | enum | 0.3846 (8) | keep | Enum so the header shows a plain count; `ratio`/`percent` would show the wrong number |
| engagement | 0–100 % / linear / default 100 % | 2 | mesh | linear 0..1 | percent | 1.0 | keep | Teeth drop out in Euclidean order as mesh falls; 100 % plays every step (the plainest useful pattern), 0 is silent |
| scale | 8 scales / default maj | 3 | scale | enum `maj min dor phr lyd mix pent hira` | enum | 0.0 (maj) | keep | Labels ≤ 4 characters so they fit the 20 px value column |

Integer conversion: none (new machine). Pitch: step k meshes A's tooth k mod teeth with B's tooth k mod (teeth × ratio); degree = (i + j) mod 14, read in the scale over two octaves.

Presets: `Spur` (the defaults) and `Escapement` (7:4, 12 teeth, mesh 60 %, dor).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/gears/definition.json` → 0 errors, 1 warning (plus the trackControl note).

| warning | resolution |
| --- | --- |
| `voiceCapacity 1; stock plays up to 8 notes per track` | Justified: gears runs on aux track 12, which the SDK keeps silent; it makes no sound of its own and steers the target track's engine, so one voice slot is honest. Same choice as ebb |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | ratio rises, teeth rise, mesh rises (more teeth engage), scale steps through a list (enum; no "rise", ordered major-ish to exotic) |
| Header values in real units, ≤ ~5 chars | pass (estimate) | `3:2`, `8`, `100%`, `maj`: ≤ 4 characters, ≤ 51 px at 20 px |
| Defaults plainest useful; presets sound good (by ear) | defaults pass; presets **pending device** | Spur plays every step at 3:2 in major; Escapement needs listening |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; all four are the player's rule |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | n/a | New machine |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `gears` |

`resources.display` is a placeholder (1 node, 1 palette) until phase 4.

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ratio | 1:1 … 3:1 | ratio | 3:2 | `1:1` / `3:2` / `3:1` | 38 px | yes |
| 2 | teeth | 3 … 16 | teeth | 8 | `3` / `9` (index 6.5 → 9 or 10) / `16` | 26 px | yes |
| 3 | mesh | 0 … 100 | % | 100% | `0%` / `50%` / `100%` | 51 px | yes, tight |
| 4 | scale | maj … hira | name | maj | `maj` / `lyd` / `hira` | 51 px | yes, tight |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 ratio | Changes B's cycle against A's: the accent pattern and how long before the phrase repeats (1:1 loops every revolution, 3:1 and 7:5 run long); the melody's shape changes with it | 4 |
| 2 teeth | Sets the cycle length and so the melody's range and the downbeat spacing; 3 is a tight ostinato, 16 a long line | 4 |
| 3 mesh | From silence through sparse Euclidean hits to every step; the biggest change in the output | 5 |
| 4 scale | Re-colours the pitches; rhythm and contour unchanged | 3 |

## 3 · Subject

Five candidates, one per direction (`passes/01-subject/pass.json`, state ready_for_pick). Full text in each `vN/candidate.json`; sketches in `vN/rest.svg`, all from `passes/01-subject/sketch.py`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P14 Loom | engineering schematic | A's last four revolutions woven as cloth, slabs where meshes sounded, B's index tooth a centre line across the rows | ratio: index line stride · teeth: thread count · mesh: raised slabs · scale: slab heights | owner's pick |
| v2 | P5 Field and figure | oscilloscope trace | X-Y scope of A's angle against B's: a Lissajous figure of the ratio over a graticule floor, beads per mesh, note strip | ratio: figure shape · teeth: bead/bar count · mesh: hollow beads · scale: strip heights | owner's pick |
| v3 | P12 Orrery | typeset diagram | The wheels as two orbits round one arbor with a semitone ring, planets crossing the mesh line | ratio: orbit B radius · teeth: stations on A · mesh: stations drop off · scale: dots on the ring | owner's pick |
| v4 | P13 Capture | orthographic elevation | Two spur gears in elevation; a tooth plays only if it's long enough to reach across the gap | ratio: B's size · teeth: A's outline · mesh: centre distance · scale: corner keyboard | owner's pick |
| v5 | P9 One-bit ink (stretch) | survey plan | Wheel A as a surveyed one-bit plot with numbered lots, a ratio scale bar and a scale section | ratio: scale bar · teeth: lots · mesh: lot tips and tone · scale: section profile | owner's pick; designer's view: doesn't fit |

Chosen: pending, the owner's pick.
