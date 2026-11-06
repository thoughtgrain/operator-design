# Bell · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a diving bell lowered on its cable, whose depth below the surface is the threshold, whose trapped air pocket is the release, and whose way of settling is the knee, with the signal it presses drawn from the compressor's own model.

It earns a screen because the compressor already has one object (the bell) that every control acts on; the stock FX page would show four numbers whose relationship (threshold against knee against release) is the thing people find hard to hear.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `bell` |
| Kind | effect (its send page, SDK 1.7) |
| Category | effect |
| Colour | grey (default) |
| Concept | A compressor as a diving bell: depth is the threshold, the air pocket is the release, the knee is how the bell settles. |
| Sounds like | A feed-forward peak compressor on the send: at its default it gently holds the loudest hits down by a few dB and lifts the rest back up, so the return sounds denser and steadier than the dry track. Deep and short it pumps audibly with the beat; shallow, soft and slow it glues the send without being heard as an effect. |
| Controls | 4: depth, air, knee, gain (stock header, no shift row) |
| Control source | new |

The DSP the scores and sketches are taken from (also in `passes/01-subject/sketch.py`, `run()`): a peak detector in dB, `x = 20 log10 |in|`; a static gain computer with threshold `T = −depth`, fixed ratio 4:1 and a soft knee of width `K` (`y = x` below `T − K/2`, `T + (x − T)/4` above `T + K/2`, the quadratic blend between); the gain reduction `y − x` smoothed with a fixed 5 ms attack and a release time constant of `air`; output `in · 10^(gr/20) · gain`.

Shift row: considered and left out. A ratio choice (2:1, 4:1, 8:1, limit) is the one control that would earn it, but it would cost the two-page band on the screen and Shift's fine steps, and 4:1 with a variable knee covers the send-compression uses. Revisit if presets keep wanting a limiter.

What the screen can show: an effect page gets the eight slots, the track, Shift and the shift row's choices, not the audio (`constraints.md`, Which machines draw a screen). Every trace in the variants is the model run on one fixed reference passage, recomputed when a control turns. Nothing follows the live signal, and nothing moves at rest.

### 1A · Port map

New machine; no source to port. The definition is drafted from the DSP above.

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold, as depth below 0 dBFS | 0–48 dB, linear, 12 dB | 0 | depth | linear 0..48 | ratio | 0.25 (12 dB) | new | Clockwise lowers the threshold, so the depth number rises. At 0 the bell sits at the surface and the effect passes the send through untouched |
| release time constant | 20 ms–2 s, exponential, 0.2 s | 1 | air | exponential 0.02..2 | duration | 0.5 (0.2 s) | new | More air in the pocket = slower refill = longer release |
| knee width | 0–24 dB, linear, 6 dB | 2 | knee | linear 0..24 | ratio | 0.25 (6 dB) | new | 0 is a hard knee |
| makeup gain | ×1–×16 (0 to +24 dB), exponential, ×2 | 3 | gain | exponential 1..16 | ratio | 0.25 (×2.00, +6 dB) | new | Shown as an amplitude ratio, a real unit the `ratio` format can print |
| ratio | fixed 4:1 | — | — | — | — | — | fixed | See Shift row above |
| attack | fixed 5 ms | — | — | — | — | — | fixed | Fast enough to catch hits; a bell sinks quickly and rises slowly |

Presets: `Plain` (the defaults), `Pump` (depth 28.8 dB, air 0.06 s, hard knee, ×4.00) and `Glue` (depth 7.2 dB, air 0.63 s, knee 14.4 dB, ×1.39).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/bell/definition.json` → 0 errors, 1 warning. `resources.display` is a placeholder until phase 4.

| warning | resolution |
| --- | --- |
| `clean-defaults`: 'Depth' reads like a colouring control (the checker matches "depth" as in mod depth) but defaults to 0.25 | Justified. Here depth is the compressor's threshold, not a modulation amount. At 0 the compressor does nothing at all, which isn't the plainest *useful* setting for a compressor; 12 dB with ×2 makeup is a light, standard send compression. Kept at 0.25 |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | yes | depth (dB below full scale), air (release time), knee (width), gain (makeup) all rise with the number shown |
| Header values in real units, ≤ ~5 chars | yes, pending device | `12`, `0.2s`, `6.0`, `2.00`. `ratio` printing dB values for depth and knee is a stretch of the format: a bare number with no unit. Fallback: `header[i]` override (`-12`, `6dB`). How `ratio` and `duration` round is pending device |
| Defaults plainest useful; presets sound good (by ear) | pending device | defaults from the DSP (light compression, makeup matching it); presets not heard yet |
| Engine page holds only the sound's own parameters | yes | no envelope, LFO or mod amount; air is the compressor's own release, not an envelope page duty |
| Page 1 holds what's played most | yes | one page |
| Port parity: nothing silently lost | n/a | new machine; ratio and attack fixed and listed above |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | yes | `bell` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | depth | 0–48 | dB below 0 dBFS | 12 | 0 / 24 / 48 | 2 × 12.8 = 26 | yes (if `ratio` prints `12.0`, 4 × 12.8 = 51, yes, just) |
| 2 | air | 0.02–2 | s | 0.2s | `20ms` / `0.2s` / `2.0s` | 4 × 12.8 = 51 | yes, just; `100ms`-style captions in the 100–999 ms band would be 64, **pending device** |
| 3 | knee | 0–24 | dB | 6.0 | 0.0 / 12.0 / 24.0 | 4 × 12.8 = 51 | yes, just |
| 4 | gain | 1–16 | × amplitude | 2.00 | 1.00 / 4.00 / 16.0 | 4 × 12.8 = 51 | yes, just |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): depth, air, knee, gain · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | depth: from no compression at all (threshold at 0 dBFS) to 48 dB of it, where every hit is squashed flat and the tails swell up between them; the biggest change in the machine | 5 |
| 2 | air: 20 ms recovers inside each hit (distorts low notes, sounds like loudness), 2 s never recovers between hits (the send sits pressed); audible as pumping only when depth is past ~12 dB | 3 |
| 3 | knee: hard to soft changes the onset of compression around the threshold; heard mostly on material that hovers near it, subtle on hits that go far past | 2 |
| 4 | gain: +0 to +24 dB of level on the return; plain loudness, but a lot of it, and it decides how much of the compressed send you hear in the mix | 4 |

## 3 · Subject

Five candidates from `passes/01-subject/pass.json` (state `ready_for_pick`); sketches at `passes/01-subject/v*/rest.svg`, notes in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P2 Diagram + trace | patent section | Fig. 1 the bell in section on its cable, water risen inside to the air pocket; fig. 2 the passage's output pressed down from its grey input | depth: bell position · air: waterline · knee: shoulder radius · gain: trace scale | candidate |
| v2 | P3 Trace as subject | hidden-line isometric | The passage's output envelope extruded into a wall, pressed down through a water plane, on a makeup plinth | depth: plane position · air: post-crest slope · knee: band planes · gain: plinth height | candidate |
| v3 | P4 Stack in depth | star atlas | Depth strata as stacked atlas plates; the bell a plotted body whose lit phase is the air pocket | depth: position down the stack · air: phase · knee: track's approach · gain: magnitude (scale) | candidate |
| v4 | P10 Voice field | engineering schematic | A row of air columns, one per input level, as tall as the bell lets that level out: the transfer curve built from parts | depth: threshold position + pressed crowns · air: second crowns · knee: tolerance band · gain: datum | candidate |
| v5 | P6 Figures (stretch) | oscilloscope trace | A diver traced in one beam under the bell on channel 2 | depth: bell position · air: escaping dots · knee: the diver's crouch · gain: scale | stretch; doesn't fit |

Chosen: pending, the owner's pick.
