# Hinge · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a door on its hinge that catches a slice of the send's sound and swings it back and forth until it comes to rest; each candidate in the subject pass draws that door and its swing its own way.
- It earns a screen: there is one object the sound acts on (the door, its leaf, its hinge and the swing it makes), and every control changes something physical about it: the leaf's length, the hinge's friction, how long it swings, how far it stands open.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `hinge` |
| Kind | effect (SDK 1.7, its own send page) |
| Category | effect |
| Colour | grey (default) |
| Concept | A swinging-door freeze: the door catches a slice of sound and swings it back and forth, creaking as it slows. |
| Sounds like | A caught fragment of whatever is on the send, played forwards then backwards then forwards again, each pass a little slower, lower and quieter, like a door swinging to rest. With creak up, the slowing passes stutter and grind as the playhead sticks and slips. |
| Controls | 4: hold, creak, swing, mix (stock header; no shift row) |
| Control source | new (the source is the DSP below) |

DSP, as the definition assumes it: a 2 s stereo ring buffer records the send. On an onset (a transient detector on the input, with a hold-off of one slice), the door closes on the last `hold` seconds and loops that slice ping-pong: one pass through the slice is one swing. The swing's amplitude is a damped pendulum with T60 = `swing`; amplitude sets both the pass's level and its playback rate (rate falls toward 0.5× as it settles, so pitch drops as the door slows), with short crossfades at each turn. `creak` adds stick-slip friction that grows as the swing slows: the playhead holds for a few ms, then jumps to catch up (a sample-and-hold on its position whose rate and depth scale with creak and with 1 − amplitude), plus a little resonant grit at each slip. `mix` is an equal-power crossfade from dry (0) to the door alone (100).

No shift row: the obvious enum (a trigger mode: onset, or catch on every bar) didn't earn it against the onset default, and a shift row would take Shift's fine steps away from hold and swing, which want them.

### 1A · Port map

New machine, so "source" is the DSP above.

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| slice length | 20 ms–2 s, exponential, 200 ms | 0 | hold | exponential 0.02..2 | duration | 0.5 (200 ms) | keep | Clockwise = longer slice, heavier door, slower swings |
| stick-slip friction | 0–1, linear, 0 | 1 | creak | linear 0..1 | percent | 0 | keep | Colouring, so 0 by default |
| swing T60 | 0.5–20 s, exponential, 3.2 s | 2 | swing | exponential 0.5..20 | duration | 0.5 (3.2 s) | keep | Clockwise = swings longer before rest |
| wet/dry | 0–1, linear, 0.5 | 3 | mix | linear 0..1 | percent | 0.5 | keep | Equal-power |

Presets: `Door` (the defaults) and `Barn` (hold 1.0 s, creak 60 %, swing 9.6 s, mix 70 %).

`resources.display` is the placeholder (1 node, 1 palette entry) until phase 4. `sharedBytes` 384,000 is the 2 s, 48 kHz, 16-bit stereo buffer; to check against api.md's effect resources, which the linter doesn't review beyond structure.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/hinge/definition.json` → 0 errors, 0 warnings (two notes: effects have no browser preview yet, so the page is checked on a device; effect resources aren't reviewed beyond structure).

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | hold: slice length rises; creak: friction rises; swing: time to rest rises; mix: wet share rises |
| Header values in real units, ≤ ~5 chars | pass, one pending | hold and swing in seconds; creak and mix as percent of 0..1 ranges. `200ms` at hold's default may overflow, see Captions |
| Defaults plainest useful; presets sound good (by ear) | pending device | mix 50 % rather than 100 %: on a send the dry path is the send's own return, and 50 % keeps the caught slice audible without losing the source. Scored from the DSP, to confirm by ear |
| Engine page holds only the sound's own parameters | pass | swing is the door's own decay, not an LFO or envelope; nothing here duplicates a stock module |
| Page 1 holds what's played most | pass | one page |
| Port parity: nothing silently lost | n/a | new machine |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `hinge` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hold | 0.02–2 | s | 200ms | 20ms / 200ms / 2.0s | 51 / 64 / 51 | no at 50 (pending: depends how `duration` formats 0.2 s; `0.2s` would be 51) |
| 2 | creak | 0–1 | % | 0 | 0 / 50 / 100 | 13 / 26 / 38 | yes |
| 3 | swing | 0.5–20 | s | 3.2s | 0.5s / 3.2s / 20s | 51 / 51 / 38 | yes |
| 4 | mix | 0–1 | % | 50 | 0 / 50 / 100 | 13 / 26 / 38 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): hold, creak, swing, mix · Page 2: none · Repeated controls: none

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 hold | From a 20 ms buzz (a pitched stutter at the slice's rate) to a 2 s phrase swinging slowly back and forth; changes what the effect is. | 5 |
| 2 creak | Smooth slow-down at 0; clearly grinding, stepped slow-down above ~30 %, mostly on the tail of each swing. | 3 |
| 3 swing | From a quick flick that dies in half a second to a 20 s drone of passes; decides how long the door is heard after each catch. | 4 |
| 4 mix | Balance of dry and frozen; clear but plain, and only as dramatic as the slice is different from the source. | 3 |

## 3 · Subject

Pass record: `passes/01-subject/pass.json`. Sketches: `passes/01-subject/v1..v5/rest.svg`, generated by `passes/01-subject/sketch.py`. Notes and a ranking: `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P4 Stack in depth | survey plan | The doorway in plan once per swing, plans stacked up the hinge pin, newest bright at the front. | hold: leaf length · creak: arcs step · swing: older swings keep their width · mix: levels spread apart | open |
| v2 | P10 Voice field | patent section | FIG. 1, a section through a louvred leaf; slats turn to the slice's level, rows are later passes played the other way. | hold: cycles across a row · creak: angles snap to steps · swing: later rows keep their tilt · mix: slat length | open |
| v3 | P15 Cell field | hidden-line isometric | An isometric cell floor with the door's swing swept into it as a raised fan, rim lit. | hold: fan radius · creak: rim breaks into runs · swing: fan angle · mix: cell height | open |
| v4 | P1 Section drawing | star atlas | The hinge in section at the pole of a graduated half-planisphere, its swing plotted as an ephemeris spiralling to rest. | hold: leaf length · creak: track steps · swing: count of turning stars · mix: star magnitude | open |
| v5 | P11 Instrument stack (stretch) | engineering schematic | A door in elevation as a schematic: hinges on a dash-dot axis, closer on the head, a plank leaf ajar, callouts. | hold: board count · creak: knuckles part · swing: closer arm angle · mix: how far ajar | open |

Chosen: pending, the owner's pick.
