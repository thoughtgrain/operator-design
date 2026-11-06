# Kiln · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a fired ceramic bowl, struck, whose glaze damps its ring and whose cracks pull its modes out of tune.
- Not the stock page: there is one object the sound acts on (the bowl), and every control changes something physical about it (the mallet, the glaze, the cracks, the firing).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `kiln` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | Modal synthesis of fired ceramic: a struck bowl whose glaze damps it and whose cracks make it inharmonic. |
| Sounds like | A struck ceramic bowl: a clear fundamental with the bowl's stretched upper modes (about 1 : 2.7 : 5.2 : 8.4), ringing long when bare and high-fired, short and thuddy when heavily glazed. Cracks split each mode into a beating doublet and pull the partials apart, from a faint shimmer to a buzzing, broken clink. |
| Controls | 4: strike, glaze, crack, fire |
| Control source | new (the source is the DSP I'm writing: a bank of 8 decaying two-pole resonators excited by a shaped mallet impulse) |

### 1A · Port map (new machine: the engine's own controls)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mallet hardness (impulse width 4 ms → 0.15 ms, plus excitation tilt) | 0..1, linear, 0.5 | 1 | strike | linear 0..1 | percent | 0.5 | keep | Harder mallet = narrower impulse = more upper modes excited. Velocity still scales level on top (stock) |
| glaze damping (per-mode T60 multiplier, highs damped harder) | 0..1, linear, 0.3 | 2 | glaze | linear 0..1 | percent | 0.3 | keep | 0 = bare bisque, rings ~6 s; 100 = thick glaze, ~0.3 s. Clockwise raises glaze, so the number rises with damping (not decay time, which falls) |
| crack depth (doublet split + random detune of modes ≥ 2) | 0..1, power 1.6, 0 | 3 | crack | power max 1, exp 1.6 | percent | 0 | keep | Degrading control, defaults off. Power curve spends more of the knob on the subtle shimmer end |
| firing (modal stretch of upper modes + Q) | 1.00..1.24, linear, 1.12 | 4 | fire | linear 1.0..1.24 | ratio | 0.5 (1.12) | keep | Stretch factor applied to upper-mode ratios; vitrified body rings stiffer and brighter. Shown as the stretch ratio, a real unit |
| bowl size / pitch | — | — | — | — | — | — | drop | The note sets the fundamental; stock tune covers transposition |
| amp envelope | — | — | — | — | — | — | drop | The bowl's own decay is glaze; the stock envelope page gates the voice |

Integer conversion: none (new machine, float DSP).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/kiln/definition.json` → 0 errors, 0 warnings. Nothing to justify. `resources.display` is the placeholder (`stateBytes 4, nodes 1, palette 1`) until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | strike (hardness), glaze (damping), crack (depth), fire (stretch) all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, with a note | fire shows its real stretch ratio (1.00–1.24). strike, glaze and crack are amounts with no physical unit the player thinks in, so percent on 0..1; glaze as decay time was rejected because it falls clockwise |
| Defaults plainest useful; presets sound good (by ear) | pass by design, **pending ear** | Default is a plain bowl: medium mallet, light glaze, no crack, mid fire. Presets Bowl / Porcelain / Raku to confirm by ear |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; glaze is the bowl's own damping, not an amp decay |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | pass | New machine; dropped size and envelope listed above |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `kiln` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | strike | 0..1 | percent | 0.5 | 0 / 50 / 100 | 3 × 12.8 = 38 px | yes |
| 2 | glaze | 0..1 | percent | 0.3 | 0 / 50 / 100 | 38 px | yes |
| 3 | crack | 0..1, power 1.6 | percent | 0 | 0 / 33 / 100 | 38 px | yes |
| 4 | fire | 1.00..1.24 | ratio | 0.5 | 1.00 / 1.12 / 1.24 | 4 × 12.8 = 51 px | yes, tight |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device (fire's 1.24 is the one to measure, and how `ratio` rounds).

Page 1 (played most): strike, glaze, crack, fire · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 strike | Soft thump to glassy ping: excitation bandwidth opens from the first two modes to all eight; big change in attack brightness | 4 |
| 2 glaze | Decay from ~6 s ring to a ~0.3 s clunk, highs going first; the largest change on the machine | 5 |
| 3 crack | Silent at 0, faint shimmer to ~30 (power curve), then clear beating and detuned partials to a buzzy broken clink at 100 | 3 |
| 4 fire | Upper modes stretch up to 24 % and ring a little longer; fundamental fixed, so a timbre shift more than a pitch one | 3 |

## 3 · Subject

Five candidates, one per direction from the pass record `passes/01-subject/pass.json` (state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg`, generator `passes/01-subject/sketch.py`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P15 Cell field | hidden-line isometric | The glazed floor of the bowl unrolled into one isometric field of slab tiles, lit where the ring still sounds | strike: lit count · glaze: grey-layer count + shade · crack: wire cells slip along fissures · fire: slab thickness | weakest fit (Gate 0: a mechanism exists) |
| v2 | P1 Section drawing | star atlas | The bowl cut a–a as a bright section, its modes charted above as stars, the mallet a meteor trail onto the rim | strike: trail rotation · glaze: pooled-glaze level · crack: fissure + double stars · fire: star magnitude | candidate |
| v3 | P2 Diagram + trace | engineering schematic | Mallet impulse → four resonators through a glaze dashpot → sum, with the ring trace on the right | strike: pulse shape · glaze: piston position · crack: trace beating · fire: mode-ruler ticks | candidate, dashboard risk |
| v4 | P3 Trace as subject | oscilloscope trace | The bowl's ring big on a scope graticule, the high mode on channel 2, a cursor where it dies | strike: amplitude scale · glaze: −40 dB cursor · crack: trace beating · fire: channel 2 period | candidate, says little about ceramic |
| v5 | P12 Orrery (stretch) | typeset diagram | The bowl in plan as the sun, each mode an orbit, its antinodes the planets | strike: populated orbits · glaze: planet scale · crack: doublet split · fire: orbit spread | stretch; fits as a mode diagram, not as an orrery |

Chosen: pending, the owner's pick.
