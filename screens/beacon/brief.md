# Beacon · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a pulse train focused by a comb "lens" into a pitch, with a rotating light sweeping the focus and fog softening it; the screen draws that focusing (which object carries it is the subject pass's question, `passes/01-subject/`).
- Not stock: there is one mechanism every control acts on (the comb and what goes through it), so the custom screen can meet "one subject, every control reads".

## 1 · Intake

| | |
| --- | --- |
| Machine id | `beacon` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | A pulse train through a comb 'lens' that focuses it into a pitch, swept by a rotating light, softened by fog. |
| Sounds like | A clicking pulse train that rings into a clear, glassy pitch as the comb's feedback rises, from a buzzy reed to a bowed-glass tone. The rotating light makes the pitch lean and return like a slow Leslie, and fog darkens and smears it toward a breathy, distant horn. |
| Controls | 4: pulse, lens, sweep, fog (stock header) |
| Control source | new (the "source" is the DSP sketched below; no port) |

DSP as designed (what the definition maps onto): per voice, a band-limited pulse train at a fixed exciter rate drives a feedback comb whose delay is one period of the played note. **pulse** sets each pulse's width as a fraction of the comb period (narrow = bright click, wide = hollow, with a spectral null that walks down the harmonics). **lens** is the comb feedback (focus: how long each pulse rings at the pitch). **sweep** is the depth, in semitones, of a slow rotating modulation of the comb delay (fixed ~0.5 Hz, so the pitch leans and returns). **fog** is a one-pole low-pass plus an allpass diffuser inside the feedback loop. Delay line sized for notes down to ~20 Hz at 48 kHz (`voiceBytes` 12288).

### 1A · Port map (new machine: source = the DSP above)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pulse width | 0–50 % of the comb period, linear | 0 | Pulse | linear 0..1 | percent | 0.25 | keep | 0 = single-sample click, 100 = half-period pulse (square-like). Header shows 0–100 of that range |
| comb feedback | 0–0.995, square-root taper so focus arrives early | 1 | Lens | power, max 0.995, exponent 0.5 | percent | 0.7 (feedback 0.83, header 83) | keep | Capped below 1 so the comb never self-oscillates |
| sweep depth | 0–12 st, linear; rate fixed ~0.5 Hz | 2 | Sweep | linear 0..12 | semitones | 0.2 (2.4 st) | keep | Rate isn't a control: the engine page holds four; a fixed slow turn is the "rotating light" |
| fog | 0–1, low-pass cutoff + diffuser mix | 3 | Fog | linear 0..1 | percent | 0 | keep | Softening control, defaults off |

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/beacon/definition.json` → 0 errors, 0 warnings. No warnings to justify.

`resources.display` is a placeholder (1 path × 64 points, 32 nodes, 6 palette) until phase 4. `machine.json` declares `sdk` 1.7; nothing in the four-control definition needs more than the base SDK, so this can drop when the budget is set.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | pulse widens, lens focuses (more feedback), sweep swings further, fog thickens |
| Header values in real units, ≤ ~5 chars | pass, pending device | sweep in semitones; pulse, lens and fog are 0–1 quantities shown as percent of their own range. Widths estimated, not measured |
| Defaults plainest useful; presets sound good (by ear) | pass by design, pending ear | fog 0; sweep 2.4 st is the machine's character, kept small. "Clear" is the defaults; "Harbour" is wider, more focused, swept and fogged |
| Engine page holds only the sound's own parameters | pass | sweep is the engine's own modulation of the comb (the rotating light is the concept), not a general LFO; its rate isn't exposed |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | n/a | new machine; sweep rate fixed by design, noted above |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `beacon` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | pulse | 0–100 | % | 25 | 0 / 50 / 100 | 3 chars, 38 px | yes |
| 2 | lens | 0–99 | % (feedback) | 83 | 0 / 70 / 99 | 2 chars, 26 px | yes |
| 3 | sweep | 0–12 | st | 2.4 | 0 / 6.0 / 12 (or +12.0 if the format signs and keeps a decimal: 5 chars, 64 px) | 3–5 chars, 38–64 px | yes if 3–4 chars; pending device |
| 4 | fog | 0–100 | % | 0 | 0 / 50 / 100 | 3 chars, 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): all four · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 pulse | click to hollow pulse: brightness falls and a null walks down the harmonics; clear but timbral, not dramatic | 3 |
| 2 lens | the whole identity of the sound: unpitched clicks at 0, a ringing, sharply pitched tone at 100 | 5 |
| 3 sweep | 0 is static; the pitch lean grows to a wide, seasick swing at 12 st; subtle below ~2 st | 3 |
| 4 fog | dark and smeared at 100, a big tonal change, but the pitch survives | 4 |

## 3 · Subject

Five candidates, one per direction in `passes/01-subject/pass.json`; candidates and sketches in `passes/01-subject/v1…v5/`, notes in `passes/01-subject/notes.md`. Uniqueness submitted: `ready_for_pick`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P3 Trace as subject | survey plan | The output traced bright along a chained survey baseline, each input pulse ringing into a run of comb-period teeth, surveyed from a station whose bearing ray is the light | pulse: input path width · lens: teeth per pulse · sweep: bearing ray angle · fog: contour count | candidate |
| v2 | P4 Stack in depth | patent section | The comb lens as stacked sawtooth Fresnel plates behind a lamp housing in section, one plate per trip round the comb | pulse: front tooth profile · lens: plate count · sweep: shutter rotation · fog: plate spacing | candidate |
| v3 | P5 Field and figure | hidden-line isometric | A comb-ringed lens barrel on an isometric sea, its lit window and light patch turning with the sweep, pulses in the strip | pulse: strip mark width · lens: ring count · sweep: window/patch bearing · fog: fog-bank position | candidate |
| v4 | P10 Voice field | star atlas | The spectrum as a star field on a conic atlas, harmonics by trips round the comb, fundamental brightest | pulse: magnitudes by harmonic · lens: magnitudes by row · sweep: beam track rotation · fog: nebula boundary position | candidate |
| v5 | P14 Loom (stretch) | engineering schematic | A schematic of the comb loop whose delay line is woven as cloth, one row per trip | pulse: slab count per row · lens: slab heights · sweep: row shear · fog: slab smear | candidate, weak fit |

Chosen: pending, the owner's pick.
