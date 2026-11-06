# Flock · screen brief

> Protocol: `opxy/protocol.md`. Phases 0–3 here; phase 3's pick is the owner's.

## 0 · Screen or stock page?

- Subject in one sentence: a small flock of birds flying over a two-octave pitch field, each bird sounding the scale degree under it as it crosses into a new cell.
- Not stock: the player's rule (position over a field decides the pitch) is spatial, so there's one obvious scene for every control to act on, and the stock player page (24 dots, no bound nodes) can't show it.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `flock` |
| Kind | synth + trackControl (`machine.json`: kind `synth`, sdk `1.9`; aux track 12, unique) |
| Category | player |
| Colour | grey (default) |
| Concept | A flock over a pitch field: birds play the pitch under them; cohesion clusters notes, speed sets density. |
| Sounds like | Eight birds steer the instrument track it controls with short phrases that bunch into close clusters or spread into wide, wandering lines; the result is a gently shifting arpeggio whose register drifts with the flock. Faster birds cross more cells, so more notes; scatter lets a few birds break away for stray notes outside the cluster. |
| Controls | 4: cohere, speed, scatter, scale (stock header) |
| Control source | new (the DSP is the boids model I'm specifying; no port) |

Mute is the machine's bypass on aux track 12: the control code sees `muted` and passes it to the display through `Overlay::display`, and every candidate has to show it on the page (named per variant in its `risks`).

### 1A · Definition from the DSP (new machine, no source to port)

| model control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cohesion weight (pull to the flock's centre) | 0–1, linear, 0.5 | 0 | Cohere | linear 0..1 | percent | 0.5 | keep | 0 % = birds ignore the centre (wide pitch spread), 100 % = tight knot of 2–3 neighbouring degrees |
| flight speed (cells crossed a beat) | 0.25–4, exponential, 1 | 1 | Speed | exponential 0.25..4 | ratio | 0.5 (→ 1.00) | keep | each cell crossing triggers a note, so this is note density per bird; tempo-synced to the project |
| separation + heading noise | 0–1, linear, 0 | 2 | Scatter | linear 0..1 | percent | 0 | keep | degrades the formation, so it defaults off |
| pitch-field quantiser | enum, pent | 3 | Scale | enum (pent, maj, min, dor, lyd, chr) | enum | 0 (pent) | keep | the field's cells are this scale's degrees over two octaves from the track's root |
| alignment weight | fixed 0.6 | — | — | — | — | — | drop | folded into cohere/scatter; a fifth knob would need two pages for a minor effect |
| bird count | fixed 8 | — | — | — | — | — | drop | 8 = one voice per bird, matching stock's 8 notes a track |

Integer conversion: none (no source integer range).

Presets: **Murmur** (defaults), **Starling** (cohere 85 %, speed 2.00, scatter 15 %, min), **Gulls** (cohere 20 %, speed 0.50, scatter 60 %, dor).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/flock/definition.json` → 0 errors, 0 warnings (one note: trackControl runs on aux track 12; show mute on the page, handled above).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | cohere rises = tighter; speed rises = faster; scatter rises = more strays; scale steps through the list |
| Header values in real units, ≤ ~5 chars | pass | %, cells a beat as `1.00`, scale names cut to ≤ 4 characters (`pent`, `chr`) so the 20 px value fits; `ratio` rendering of speed pending device |
| Defaults plainest useful; presets sound good (by ear) | pass / **pending device** | scatter (degrading) defaults 0; cohere mid, speed 1 cell a beat; presets not yet heard |
| Engine page holds only the sound's own parameters | pass | no envelope/LFO; all four are flock parameters |
| Page 1 holds what's played most | pass | one page |
| Port parity | n/a | new machine; dropped model parameters listed in 1A |
| Saved sounds compatible | n/a | unreleased |
| `id` final | pass | `flock` |

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cohere | 0–100 | % | 50 | 0 / 50 / 100 | 3 × 12.8 = 38 | yes |
| 2 | speed | 0.25–4.00 | cells a beat | 1.00 | 0.25 / 1.00 / 4.00 | 4 × 12.8 = 51 | yes, tight |
| 3 | scatter | 0–100 | % | 0 | 0 / 50 / 100 | 38 | yes |
| 4 | scale | 6 names | enum | pent | pent / dor / chr | 4 × 12.8 = 51 | yes, tight |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1: cohere, speed, scatter, scale · no page 2.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 cohere | pitch range of the phrase collapses from two octaves to two or three neighbouring degrees: from wandering lines to a repeated cluster | 4 |
| 2 speed | note density from one note every four beats per bird to four a beat (16×): the most obvious change on the track | 5 |
| 3 scatter | at 0 nothing; past ~30 % stray notes outside the cluster, frequent by 100; subtle at the low end | 2 |
| 4 scale | changes which notes sound, not how many or where; clear on a change between pent and chr, smaller between neighbouring modes | 3 |

## 3 · Subject

Pass: `passes/01-subject/` (`pass.json`, `v1…v5/candidate.json` + `rest.svg`, `sketch.py`, `notes.md`). State: ready for pick.

| candidate | pattern | drawing language | subject in one sentence |
| --- | --- | --- | --- |
| v1 | P5 Field and figure | star atlas | the pitch field as a conic atlas sheet, the flock as one asterism with proper-motion vectors |
| v2 | P12 Orrery | engineering schematic | birds orbit the flock's centre of gravity; a graduated two-octave rim reads the pitch at each bearing |
| v3 | P13 Capture | oscilloscope trace | each bird's pitch over time as a stepped trace; cohesion is two capture cursors the traces are pulled between |
| v4 | P14 Loom | typeset diagram | the last four bars woven as cloth; threads are pitches, slabs are what the birds played |
| v5 | P11 Instrument stack (stretch) | orthographic elevation | birds on telegraph wires, one wire per scale degree; perched birds sound their wire |

Per-control sentences and risks are in each `candidate.json`. Chosen: pending the owner's pick.
