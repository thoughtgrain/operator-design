# Lattice · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a struck metal plate held at its edges, ringing in a standing-wave pattern that size, tension and damping reshape, with the pickup's place on it marked.
- It earns a screen: there is one physical object every control acts on (the plate), and each control has a part of it to move (its mesh, its stiffness, a damper, a pickup).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `lattice` |
| Kind | synth |
| Category | engine |
| Colour | grey (default) |
| Concept | A 2D waveguide plate: a metal sheet held at its edges, excited at one point and heard at another. |
| Sounds like | A struck sheet of metal tuned to the note: a small tight mesh rings like a tin tray or a bar, a large stiff one like a gong or thunder sheet. Damp takes it from a long shimmering wash to a dead clank, and moving the pickup changes which partials you hear without changing the pitch. |
| Controls | 4: size, tension, damp, pickup (stock header) |
| Control source | new (the DSP sketched below; no port) |

### 1A · Definition (new machine; "source" is the DSP)

The engine sketched here: a rectangular 2D digital waveguide mesh (rectilinear, 4-port scattering junctions), aspect 1.3:1, edges terminated with a reflection of −1 (clamped). The note sets the junction delay, so the plate's lowest mode tracks the note. A raised-cosine strike is injected at a fixed point (0.30, 0.35); the output is read at the pickup. Each port carries a one-pole loss filter and a first-order allpass.

| source control | range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mesh size | 4, 6, 8, 10, 12 junctions per side | 0 | size | enum `4 6 8 10 12` | enum | 0.5 (8) | keep | more junctions carry more modes below the note's Nyquist: sparse and bar-like at 4, dense and gong-like at 12. Stepped because the mesh is; the screen eases between steps |
| stiffness (allpass dispersion) | 0..1 linear, 0.4 | 1 | tension | linear 0..1 | percent | 0.4 | keep | 0 = membrane (modes close to harmonic), 1 = stiff plate (upper modes stretched, clangorous). Clockwise raises tension and stretches the partials |
| loss (one-pole per port) | 0..1 linear, 0.3 | 2 | damp | linear 0..1 | percent | 0.3 | keep | T60 at the fundamental ≈ 8 s at 0, ≈ 1.5 s at 0.3, ≈ 0.08 s at 1; highs die first. Shown as a percent because `duration` would fall as damp rises (clockwise must make the number rise) |
| pickup position | 0..1 along the diagonal from the strike point to (0.88, 0.82) | 3 | pickup | linear 0..1 | percent | 0.6 | keep | 0 sits on the strike point (bright, every mode present); moving away notches the modes whose nodal lines it crosses |
| strike position | fixed (0.30, 0.35) | — | — | — | — | — | drop | four controls on one page; the pickup carries the "where" axis, and a fixed strike keeps the picture's anchor still |
| strike hardness | fixed raised cosine, 3 junctions wide | — | — | — | — | — | drop | velocity already brightens the strike in the engine; a hardness knob would be a second brightness control |

Presets: **Plate** (defaults), **Gong** (size 12, tension 80, damp 8, pickup 85), **Tin** (size 4, tension 20, damp 65, pickup 30).

Resources: `voiceBytes` 4800 = 12 × 12 junctions × 4 ports × 2 (in/out) × 4 bytes (4608) + loss/allpass state and envelope (192), aligned 16. `voiceCapacity` 8. `display` is the phase-1A placeholder (1 node, 1 palette entry); phase 4 sets it. CPU note: a 12 × 12 mesh at full rate across 8 voices is heavy; the engine may run the mesh at a reduced rate for size ≥ 10. **Pending device** (CPU profiling).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/lattice/definition.json` → 0 errors, 0 warnings.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | size: more junctions; tension: stiffer; damp: more loss; pickup: further from the strike |
| Header values in real units, ≤ ~5 chars | pass | size shows the junction count (`4`..`12`, ≤ 2 chars); the other three are 0..1 controls shown as `0`..`100` |
| Defaults plainest useful; presets sound good (by ear) | pass / **pending device** | defaults are a mid plate, nothing colouring is on; presets to confirm by ear |
| Engine page holds only the sound's own parameters | pass | no envelope/LFO; damp is the plate's own loss, not an amp envelope |
| Page 1 holds what's played most | pass | one page, four controls |
| Port parity: nothing silently lost | pass | not a port; the two dropped engine settings are listed above with reasons |
| Saved sounds compatible (if released) | n/a | unreleased |
| `id` final | pass | `lattice` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | size | 4..12 | junctions per side | 8 | `4` / `8` / `12` | 26 px | yes |
| 2 | tension | 0..100 | % | 40 | `0` / `50` / `100` | 38 px | yes |
| 3 | damp | 0..100 | % | 30 | `0` / `50` / `100` | 38 px | yes |
| 4 | pickup | 0..100 | % | 60 | `0` / `50` / `100` | 38 px | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): size, tension, damp, pickup · Page 2: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 size | mode density from a sparse, almost bar-like few partials (4) to a dense metallic wash (12); the clearest change of character | 4 |
| 2 tension | near-harmonic, almost tonal membrane at 0 to a clangorous stretched plate at 100; strong but the pitch stays put | 4 |
| 3 damp | ring from ~8 s with slow beating to a dead 80 ms clank; the biggest change on the page | 5 |
| 4 pickup | timbre shifts as modes drop into and out of nodal lines; clear on sustained notes, subtle on short ones | 3 |

## 3 · Subject

Five candidates, one per direction handed out for this pass. Pass record: `passes/01-subject/pass.json` (state `ready_for_pick`); sketches `passes/01-subject/v1..v5/rest.svg`, generated by `passes/01-subject/sketch.py`; notes and a ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P15 Cell field | patent section | The plate face on as a square field of junction cells lit by how far each swings, in a hatched clamp frame keyed with patent numerals. | size: cell count · tension: lit pattern · damp: felt line moves in · pickup: bright cell walks | candidate |
| v2 | P1 Section drawing | hidden-line isometric | A sheet bolted into a frame, its mesh bent into the standing wave, striker over one point, stylus at another, felt damper above. | size: mesh count + footprint · tension: surface shape · damp: damper drops · pickup: stylus slides | candidate |
| v3 | P2 Diagram + trace | star atlas | The plate charted as a star field with a constellation line from strike to pickup, beside the light curve the pickup records. | size: star count · tension: line sags/straightens · damp: curve length · pickup: star moves | candidate |
| v4 | P3 Trace as subject | engineering schematic | The wave cut along strike→pickup, drawn as a beam between fixed supports with force arrow, probe and dimensioned span. | size: span · tension: trace shape · damp: swing scale · pickup: probe slides | candidate |
| v5 | P12 Orrery (stretch) | oscilloscope trace | Each mode a body on its own orbit round the strike, x-y scope style, phosphor trail as long as the mode rings. | size: orbit count · tension: radii spacing · damp: trail length · pickup: body sizes | candidate (stretch; designer's read: doesn't fit) |

Chosen: **the owner's pick**, not made here.
