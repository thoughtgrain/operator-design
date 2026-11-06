# Tide · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a rock pool whose tuned hollows ring when the swell's noise washes into them; each candidate in the subject pass draws that pool its own way.
- It earns a screen: there is one scene the sound acts on (the pool and the waves reaching it), and every control changes something physical in it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `tide` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | A bank of tuned resonators in a rock pool, excited by noise that arrives in waves; notes set the pool's tuning. |
| Sounds like | A pitched wash: bursts of surf noise that swell in and fall away, leaving a chord of ringing tones at the played note that decays before the next wave. Long depth turns it into a sustained, shimmering drone; short depth leaves tuned hiss. |
| Controls | 4: swell, depth, salt, drift (stock header) |
| Control source | new (the source is the DSP below) |

DSP, as the definition assumes it: per voice, eight two-pole resonators tuned to the note times partial ratios `r^(1 + 0.3·salt)` (r = 1..8), fed by white noise shaped by a wave envelope (fast rise, slow fall) that repeats every `swell` seconds from the note-on; each resonator's T60 is `depth`, shortened for higher partials; drift adds a slow independent random walk to each resonator's tuning (up to ±40 cents at 100 %).

### 1A · Port map

New machine, so "source" is the DSP above.

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wave period | 0.25–8 s, exponential, 2.0 s | 0 | swell | exponential 0.25..8 | duration | 0.6 (2.0 s) | keep | Clockwise = longer period, slower waves |
| resonator T60 | 0.05–5 s, exponential, 0.5 s | 1 | depth | exponential 0.05..5 | duration | 0.5 (0.5 s) | keep | Deeper pool rings longer |
| partial stretch | 0–1, linear, 0 | 2 | salt | linear 0..1 | percent | 0 | keep | Inharmonic, crystalline at 100 |
| tuning wander | 0–±40 cents, linear, 0 | 3 | drift | linear 0..1 | percent | 0 | keep | Each resonator wanders on its own |

Presets: `Pool` (the defaults) and `Grotto` (slow swell 4.0 s, depth 2.5 s, salt 35 %, drift 20 %).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/tide/definition.json` → 0 errors, 1 warning.

| warning | resolution |
| --- | --- |
| `depth` reads like a colouring control but defaults to 0.5 | Justified: here depth is the pool's ring time (resonator T60), not a modulation depth. At 0 (50 ms) the resonators barely ring and the machine is tuned hiss, which is not the plainest useful sound. 0.5 s is the plainest setting where the note is clearly pitched. Salt and drift, the colouring controls, default to 0. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | swell: the period rises; depth: ring time rises; salt: stretch rises; drift: wander rises |
| Header values in real units, ≤ ~5 chars | pass, one pending | swell and depth show seconds; salt and drift are 0..1 amounts shown as percent. `0.25s` at swell's minimum may overflow, see Captions |
| Defaults plainest useful; presets sound good (by ear) | pending device | Defaults scored from the DSP; to confirm by ear |
| Engine page holds only the sound's own parameters | pass | swell is the excitation's own rhythm, not an LFO the OP-XY already has: it shapes the noise source, and it restarts on note-on |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `tide` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | swell | 0.25–8 | s | 2.0s | 0.25s / 1.4s / 8.0s | 64 / 51 / 51 | no at 0 (pending: depends how `duration` formats 0.25 s) |
| 2 | depth | 0.05–5 | s | 0.5s | 50ms / 0.5s / 5.0s | 51 / 51 / 51 | yes |
| 3 | salt | 0–1 | % | 0 | 0 / 50 / 100 | 13 / 26 / 38 | yes |
| 4 | drift | 0–1 | % | 0 | 0 / 50 / 100 | 13 / 26 / 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): swell, depth, salt, drift · Page 2: none · Repeated controls: none

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 swell | The rhythm of the whole sound: a rapid flutter of surf at 0.25 s, a slow breathing wash at 8 s. Dramatic and constant. | 5 |
| 2 depth | From tuned hiss (50 ms) to a sustained ringing chord (5 s); decides whether it is a pitched instrument at all. | 5 |
| 3 salt | Partials stretch from a clean harmonic chord to bell-like, metallic beating; clear above ~30 %. | 3 |
| 4 drift | Slow chorusing and beating between resonators; subtle under 40 %, a seasick wobble at 100 %. | 2 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`). Sketches: `passes/01-subject/v1..v5/rest.svg`, generated by `passes/01-subject/sketch.py`. Notes and a ranking: `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P5 Field and figure | oscilloscope trace | One phosphor trace of the pool ringing after the latest swell, over dim receding traces of earlier swells, arrivals ticked in a strip. | swell: strip ticks and trace spacing · depth: tail length · salt: beating ripple · drift: traces shear | open |
| v2 | P10 Voice field | typeset diagram | A Hinton chart of eight resonators over four seconds, squares sized by how loudly each rings. | swell: onset columns · depth: decay length · salt: row spacing · drift: rows go ragged | open |
| v3 | P15 Cell field | orthographic elevation | The shore in elevation as a cell grid: rock hollow, water grey, foam lit. | swell: crest cells · depth: water rows · salt: lit crystal runs · drift: surface tilt | open |
| v4 | P1 Section drawing | survey plan | A surveyed plan of the pool: bright rim open to the sea, depth contours, soundings, tide mark, swell fronts. | swell: front spacing · depth: contour count · salt: faceted rim · drift: tide mark wanders | open |
| v5 | P13 Capture (stretch) | patent section | A patent section through the shore: swell, rim, pool with three chambers of different depth. | swell: crest spacing/height · depth: chamber floors drop · salt: wall facets · drift: surface tilts | open |

Chosen: pending, the owner's pick.
