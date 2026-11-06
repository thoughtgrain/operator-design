# Lathe · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a lacquer disc being cut on a lathe, where the stylus digs the signal into a groove, saturating as it's driven harder, and the groove comes back worn and rumbling on playback.
- Not the stock page: there's one object the sound acts on (the groove, and the cutter making it), and each control changes something physical about it: how hard it's cut, how far in toward the label, how worn it is, how much the platter rumbles.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `lathe` |
| Kind | effect (send page, SDK 1.7) |
| Category | effect |
| Colour | grey (default) |
| Concept | A record-cutting lathe: the signal is cut into a groove, saturating at the cutter, with wear and rumble on playback. |
| Sounds like | The send comes back as if it had been cut to lacquer and played: warm, rounded saturation and a high-frequency limit as the cutter is driven, getting duller and grittier (tracing distortion) toward the inner grooves. Wear adds crackle, ticks and a dulled top; rumble adds a low, slowly wandering platter rumble under it. |
| Controls | 4: cut, groove, wear, rumble (one page, stock header) |
| Control source | new (the source is the DSP I'm writing: drive into a cutter model of tanh saturation plus a slew limit on the cut velocity, a radius-dependent low-pass and tracing-distortion stage, a crackle/tick generator with a wear-dependent shelf, and a filtered-noise rumble with slow wow) |

Shift row: none. A cutting-speed enum (33 / 45 / 78) was considered and dropped; it would only rescale groove's high-frequency loss, and groove already covers that range. It doesn't earn the row.

Effects get no note input on their page (`slots`, `track`, `shift`, `choices` only), so this screen moves only when a knob turns. There's no browser preview for effect pages yet: design from stills, check on a device.

### 1A · Port map (new machine: the effect's own controls)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cutting level (gain into the cutter, saturation + slew limit) | 0.5×..4.0×, exponential, 1.0× | 1 | cut | exponential 0.5..4.0 | ratio | 0.3333 (1.00) | keep | Unity at the default (clean below the knee); above ~1.4× the tanh and slew limit bite. Shown as the gain ratio, a real unit |
| groove radius (rim → label) | 0..1, linear, 0 | 2 | groove | linear 0..1 | percent | 0 | keep | 0 = outer rim (full bandwidth), 100 = last groove before the label (~−9 dB at 10 kHz plus tracing distortion). Radius in mm would fall clockwise, so it's shown as how far in |
| wear (crackle density, ticks, top-end shelf) | 0..1, power 1.5, 0 | 3 | wear | power max 1, exp 1.5 | percent | 0 | keep | Degrading, defaults off. Power curve spends more of the knob on light surface noise |
| rumble (filtered noise below ~40 Hz + slow wow) | 0..1, power 2, 0 | 4 | rumble | power max 1, exp 2 | percent | 0 | keep | Degrading, defaults off. Squared so the first half stays a faint floor |
| cutting speed (33/45/78) | enum | — | — | — | — | — | drop | See shift row note above |
| dry/wet | — | — | — | — | — | — | drop | It's a send; the send level is the mix |

Integer conversion: none (new machine, float DSP).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/lathe/definition.json` → 0 errors, 0 warnings (two notes: effects have no browser preview; effect resources not reviewed beyond structure). `resources.display` is the placeholder (`stateBytes 4, nodes 1, palette 1`) until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | cut (gain), groove (how far in), wear (amount), rumble (level) all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, with a note | cut shows its gain ratio (0.50–4.00). groove, wear and rumble have no unit the player thinks in, so percent on 0..1 |
| Defaults plainest useful; presets sound good (by ear) | pass by design, **pending ear** | Default is cut at unity, outer groove, no wear, no rumble: the cleanest lacquer. cut isn't at 0 because 0.5× is a level drop, not "off"; unity is the plain setting. Presets Lacquer / Dubplate / Old 78 to confirm by ear |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; rumble's wow is the platter's own, not a mod amount |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | pass | New machine; dropped speed and dry/wet listed above |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `lathe` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cut | 0.5..4.0, exponential | ratio | 0.3333 | 0.50 / 1.41 / 4.00 | 4 × 12.8 = 51 px | yes, tight |
| 2 | groove | 0..1 | percent | 0 | 0 / 50 / 100 | 38 px | yes |
| 3 | wear | 0..1, power 1.5 | percent | 0 | 0 / 35 / 100 | 38 px | yes |
| 4 | rumble | 0..1, power 2 | percent | 0 | 0 / 25 / 100 | 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device (cut's 4.00 is the one to measure, and how `ratio` rounds).

Page 1 (played most): cut, groove, wear, rumble · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 cut | From a 6 dB quieter clean copy, through unity, to dense saturation with rounded transients and a hard top-end limit; the biggest change on the machine | 4 |
| 2 groove | Progressive dulling and a gritty tracing distortion on loud highs toward the label; gentle to ~50, obvious past 70 | 3 |
| 3 wear | Light surface noise early (power curve), then ticks, crackle and a dulled top; obvious on quiet material, partly masked on dense | 3 |
| 4 rumble | Sub-40 Hz rumble and slow wow; faint until ~60 (squared), and small speakers hide much of it | 2 |

## 3 · Subject

Five candidates, one per direction from the pass record `passes/01-subject/pass.json` (state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg`, generator `passes/01-subject/sketch.py`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P1 Section drawing | typeset diagram | The cutting stylus mid-cut in a textbook cross-section of the lacquer blank, its V sunk into the coat, swarf coiling off | cut: groove V depth + flat floor (shape) · groove: blank slides under the stylus, rim out, label in (position) · wear: chips on cut grooves (count) · rumble: platter line waves (shape) | candidate |
| v2 | P2 Diagram + trace | orthographic elevation | The lathe side-on as an elevation, the groove wall as played traced beside it | cut: trace amplitude + flat peaks (shape) · groove: head along the rail (position) · wear: crackle ticks (count) · rumble: trace centre line bends (shape) | candidate |
| v3 | P3 Trace as subject | survey plan | A sector of the side from above as a survey plan, the groove being cut bright among grey earlier turns | cut: groove swing + squared crests (shape) · groove: label edge rises (position) · wear: spot marks (count) · rumble: earlier turns go eccentric (position) | candidate |
| v4 | P4 Stack in depth | patent section | Five section slices from rim to label stacked like a patent figure, the one under the stylus lit | cut: lit edge swells + flattens (shape) · groove: which slice is lit (position + shade) · wear: nicks (count) · rumble: slices go out of line (position) | candidate |
| v5 | P11 Instrument stack (stretch) | hidden-line isometric | The lathe itself assembled in hidden-line isometric, head over the disc on its arm | cut: swarf coil (scale) · groove: carriage along the rail (position) · wear: dust specks (count) · rumble: disc outline turns in plane (rotation) | stretch; mostly doesn't fit |

Chosen: pending, the owner's pick.
