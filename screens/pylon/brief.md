# Pylon · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a span of power line between two pylons, its wire singing the standing wave the wind locks it into, with the mains humming under it.
- It earns a screen: there is one object the sound acts on (the wire), and every control changes something about it you could draw.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `pylon` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Sounds like | An aeolian harp: a breathy, whistling partial that sits on one harmonic of the played note and jumps up the series as the wind rises, with neighbours shimmering in when the span is long. Under it, an optional mains buzz at 50 Hz and its odd harmonics. |
| Concept | An aeolian harp: power lines sung by wind, the span and gusts setting which modes speak, with a mains hum under it. |
| Controls | 4: wind, span, gust, hum (stock header) |
| Control source | new (the DSP below is the source) |

### 1A · Port map (new machine: inventory of the DSP being written)

The voice is a bank of up to 12 two-pole resonators at `n · f_note` (the wire's modes; the note sets the fundamental), excited by filtered noise whose spectrum peaks at the vortex-shedding frequency. The lock-in mode is `n* = v · L / 160` (Strouhal frequency over the span's mode spacing, scaled so the defaults lock mode 3); each mode's excitation is a Gaussian in `n − n*`.

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wind speed `v` | 0.5–20 m/s, exponential, 4 m/s | 0 | wind | exponential 0.5..20 | ratio | 0.5637 (4.0 m/s) | keep | Sets shedding frequency, so which mode locks; also overall level (∝ v²) |
| span length `L` | 20–400 m, exponential, 120 m | 1 | span | exponential 20..400 | ratio | 0.5981 (120 m) | keep | Mode density: long spans put more modes near the lock (a cluster), short spans isolate one partial |
| gust intensity | 0–1, linear, 0 | 2 | gust | linear 0..1 | percent | 0 | keep | Turbulence on `v`: widens the lock (σ 0.55 → 2.15) and makes it wander between neighbours with slow swells. Colouring, so 0 |
| mains hum | 0–1, linear, 0 | 3 | hum | linear 0..1 | percent | 0 | keep | 50 Hz with odd harmonics, up to −18 dB under the voice, not key-tracked. Colouring, so 0 |
| wire diameter `d` | fixed 4 mm | — | — | — | — | — | drop | Folded into the 160 constant; another control would only re-scale wind |

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/pylon/definition.json` → 0 errors, 0 warnings.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | wind speed, span length, gust intensity and hum level all rise clockwise |
| Header values in real units, ≤ ~5 chars | pass, pending device | wind in m/s, span in metres via `ratio`; gust and hum are true 0..1 amounts. How `ratio` formats 20.0 and 400 is pending; fallback is `header[i]` text override with whole numbers |
| Defaults plainest useful; presets sound good (by ear) | pass by design, pending ear | defaults: a steady 4 m/s on a 120 m span, no gust, no hum: one clean sung partial |
| Engine page holds only the sound's own parameters | pass | no envelope or LFO; gust is the wind's own turbulence, not a modulation amount |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | pass | wire diameter dropped with a reason |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | yes | `pylon` |

`resources.display` is a placeholder (1 path, 64 nodes); phase 4 sets it from the chosen subject. v1 would need ~270 nodes at span 100 (sdk 1.8).

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | wind | 0.5–20 | m/s | 4.0 | 0.5 / 3.2 / 20.0 | 4 × 12.8 = 51 | yes, just |
| 2 | span | 20–400 | m | 120 | 20 / 89 / 400 | 3 × 12.8 = 38 | yes |
| 3 | gust | 0–100 | % | 0 | 0 / 50 / 100 | 38 | yes |
| 4 | hum | 0–100 | % | 0 | 0 / 50 / 100 | 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. `ratio` decimals pending (if it prints two decimals, `20.00` won't fit: use the header override).

Page 1 (played most): wind, span, gust, hum · Page 2: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 wind | Climbs the harmonic series (mode 1 → ~15) and rises in level ∝ v²: the biggest change in pitch and loudness | 5 |
| 2 span | One isolated partial at 20 m to a shimmering, beating cluster at 400 m; also moves the lock up for the same wind | 4 |
| 3 gust | Steady whistle to uneven swells with partials jumping between neighbours; obvious, but the pitch centre stays | 3 |
| 4 hum | A quiet 50 Hz buzz under the voice, never louder than −18 dB | 2 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`), sketches `passes/01-subject/v*/rest.svg`, notes `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | P10 Voice field | patent section | Floating slabs, one row per conductor, heights the standing wave, between hatched cross-arm sections | open |
| v2 | P15 Cell field | hidden-line isometric | The wake: raised cells as vortex rolls downwind of one bright wire | open |
| v3 | P1 Section drawing | star atlas | The span on a sky chart, the wire a chain of standing-wave loops on its catenary | open |
| v4 | P2 Diagram + trace | engineering schematic | Shedding source tapping a ladder of tuned modes, summed with mains into the output trace | open |
| v5 | P14 Loom (stretch) | oscilloscope trace | Recent wire shapes woven as rows on a scope, warp threads through the nodes | open |

Chosen: pending the owner's pick.
