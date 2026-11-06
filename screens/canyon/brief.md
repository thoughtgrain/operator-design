# Canyon · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a shout thrown into a canyon and the train of echoes its walls send back, each one later, quieter and duller than the last.
- A custom screen earns its place: there is one scene the sound acts on (the canyon and its returning echoes), and all four controls change it (how far the walls are, how many there are, how soft the rock is, how hard the wind blows). The stock FX page would show four numbers with no sense of the tap pattern.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `canyon` |
| Kind | effect (send page, SDK 1.7) |
| Category | effect |
| Colour | grey (default) |
| Concept | Multi-tap echo shaped by canyon walls: the distance sets the delay, walls set the tap count, rock absorbs highs, wind modulates. |
| Sounds like | A multi-tap echo whose taps arrive evenly spaced, each one lower and darker than the one before, like a shout coming back off successive canyon walls. Close walls give a slap or a metallic flutter; far walls give slow, separate repeats, and wind makes them waver like a tape echo in a gust. |
| Controls | 4: distance, walls, absorb, wind (stock header) |
| Control source | new |

### 1A · Port map (new machine: the source is the DSP being written)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tap spacing | 40 ms – 1.6 s, exponential, 253 ms | 0 | distance | exponential 0.04..1.6 | duration | 0.5 (253 ms) | new | time between taps (one round trip to the next wall); ~43 m one way at 253 ms |
| tap count | 1–12, stepped, 4 | 1 | walls | enum 1,2,3,4,5,6,8,12 | enum | 0.4286 (4) | new | number of reflecting walls; each wall returns 0.8 of what reached it, less what the rock takes |
| rock absorption | 0–1, linear, 0.35 | 2 | absorb | linear 0..1 | percent | 0.35 | new | one-pole low-pass per reflection, cutoff falling as absorb rises, plus a small extra level loss per wall; compounds along the train |
| wind | 0–1, linear, 0 | 3 | wind | linear 0..1 | percent | 0 | new | slow random modulation of each tap's time (independent per tap, up to ±6 % of its delay) and a little level flutter; defaults off as a colouring control |

No integer conversion: values come straight from the SDK's Q31 positions through the mappings above. No shift row: there's no mode the four controls don't already cover, so it doesn't earn its place (and keeping it off keeps Shift's fine steps for distance).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/canyon/definition.json` → 0 errors, 0 warnings (two notes: effects have no browser preview yet; effect resources not reviewed beyond structure). `resources.display` is a placeholder (1 path × 64 points, 96 nodes, 8 palette entries) until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | distance (delay time), walls (tap count), absorb (high loss) and wind (modulation depth) all rise clockwise |
| Header values in real units, ≤ ~5 chars | **at risk, pending device** | `253ms` is 5 characters (est. 64 px > 53 px); in the fallback preview font it runs into the `walls` title. If the device font confirms it, either narrow the range so the default reads in seconds or set `header[0]` to drop the unit (`253`) |
| Defaults plainest useful; presets sound good (by ear) | pass, pending device | wind off; four walls at a quarter second with some darkening is a plain, useful echo. Presets: Gorge (defaults), Slot (short, 12 walls, dark: a flutter), Mesa (long, two walls, bright, some wind) |
| Engine page holds only the sound's own parameters | pass | wind is the echo's own tap-time modulation, not a general LFO; no envelope or LFO controls |
| Page 1 holds what's played most | pass | one page, four controls |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | not released |
| `id` final | pass | `canyon` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | distance | 40 ms – 1.6 s | time | 253 ms | `40ms` / `253ms` / `1.60s` | 51 / 64 / 64 px | **no at 50 and 100 (estimate)**, pending device font |
| 2 | walls | 1–12 | taps | 4 | `1` / `4` / `12` | 13–26 px | yes |
| 3 | absorb | 0–100 | % | 35 | `0` / `50` / `100` | 38 px | yes |
| 4 | wind | 0–100 | % | 0 | `0` / `50` / `100` | 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. `distance` is exactly 8 characters as a title (10 px, ~51 px est.), which fits its 60 px title step.

Page 1 (played most): distance, walls, absorb, wind · Page 2: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 distance | from a 40 ms metallic flutter to 1.6 s separate repeats; the most obvious control, and turning it while audio passes pitch-glides the echo | 5 |
| 2 walls | one slap-back to a long tail of twelve taps; strong at the low end (1 → 4), less from 6 → 12 as late taps are quiet and dark | 4 |
| 3 absorb | taps go from as bright as the source to a dull thud after the second wall; clear on bright material, mild on bass | 3 |
| 4 wind | subtle waver below ~40, an audible seasick chorus on the taps above 70 | 2 |

## 3 · Subject

Five candidates from `passes/01-subject/pass.json` (state `ready_for_pick`, every pair unique on pattern and language). Each has `candidate.json` and a rest sketch `rest.svg` beside it, generated by `passes/01-subject/sketch.py`; `passes/01-subject/notes.md` ranks them. The pick is the owner's.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P4 Stack in depth | survey plan | A survey plan of the gorge from above: each reflecting wall a contoured rock bench, stacked back up a dashed chainage line from the station at the mouth, the nearest bench bright. | distance position (bench spacing), walls count (benches), absorb shape (rims jagged → smooth), wind rotation (benches swing) | owner's pick |
| v2 | P10 Voice field | patent section | Fig. 1 of a patent: the echo's impulse response in longitudinal section as a row of hatched rock columns, each tap a peak, with reference numerals. | distance shape (peak spacing), walls shape (peak count), absorb shape (peaks slump and broaden), wind position (jitter) | owner's pick |
| v3 | P15 Cell field | hidden-line isometric | The canyon floor as an isometric grid of cells, each echo front lighting a ring of raised blocks out from the shout's block. | distance position (ring spacing), walls count (rings), absorb count (raised → grey tiles), wind position (rings break into staggered runs) | owner's pick |
| v4 | P1 Section drawing | star atlas | The canyon cut across and charted like a sky atlas: the walls as the dark limb, the echoes as lettered stars of falling magnitude on a zig-zag constellation line. | distance position (walls apart), walls count (stars), absorb scale (magnitudes fall faster), wind position (proper-motion drift) | owner's pick |
| v5 | P5 Field and figure (stretch) | engineering schematic | An engineering elevation of the two walls dimensioned across the gap over a receding floor grid, with the tap train ticked along a time strip. | distance scale (wall pair), walls count (strip ticks), absorb shape (tick envelope), wind position (floor grid slides) | owner's pick |

Chosen: pending the owner.
