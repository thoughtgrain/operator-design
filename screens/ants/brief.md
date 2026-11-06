# Ants · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a colony walking a lattice of scale degrees, where the trail it keeps using brightens into a phrase and the trails it leaves fade away.
- Not the stock page: a player has no stock page that can bind nodes (the stock player page is 24 on/off dots), and this machine has one scene its controls act on (the ants, their scent, how fast it fades, the lattice they walk). As a track-control synth on aux track 12 (SDK 1.9) it draws its own page on M1.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `ants` |
| Kind | synth + trackControl |
| Category | player |
| Colour | grey (default) |
| Concept | Ants walk a lattice of scale degrees leaving scent; trails strengthen into repeated phrases and fade when unused. |
| Sounds like | Makes no sound of its own: it plays notes on the instrument tracks it steers, one note per ant per step it lands on a degree. With few ants and strong scent it settles into a short repeating figure; with many ants and fast fade it wanders, half-repeating, like a melody that keeps rewriting its ending. |
| Controls | 4: ants, scent, fade, scale |
| Control source | new (the source is the control code I'm writing: ants step on the lattice each clock tick, choosing the next edge with weight `(ε + τ)^k` where τ is the edge's pheromone and k follows scent; every edge loses a fraction of τ each step set by fade; a walked edge gains a fixed deposit) |
| Muted | Mute is the bypass (`ux.md`, Aux tracks). The control code reads `control::Input.muted` and passes it to the display in its `Overlay::display` words; every candidate below says how its picture shows it |

### 1A · Port map (new machine: the control code's own parameters)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ant count | 1..8 integer, 4 | 1 | ants | enum `1`…`8` | enum | 0.4286 (4) | keep | Each ant can sound a note per step; 8 matches stock's 8 notes per track. An enum so the header shows the whole number |
| scent exponent k | 0..4, linear on the knob, 2 | 2 | scent | linear 0..1 | percent | 0.5 | keep | 0 = ants ignore pheromone (random walk), 100 = they follow the strongest edge almost always. Percent of the 0..4 exponent range; the exponent itself isn't a unit a player thinks in |
| evaporation per step | 0..0.25 of τ per step, linear, 0.075 | 3 | fade | linear 0..1 | percent | 0.3 | keep | Clockwise fades faster, so the number rises with fade. Shown as a percent of the range rather than a half-life, because a half-life would fall clockwise |
| scale | 8 sets, pent | 4 | scale | enum `pent major minor dor phryg lyd mixo chrom` | enum | 0 (pent) | keep | Sets the lattice's degrees (two octaves from the target track's root). Pentatonic is the plainest useful default for a generative player |
| deposit amount | fixed 1.0 per crossing | — | — | — | — | — | drop | Only the ratio of deposit to evaporation matters; fade covers it |
| lattice shape (steps + thirds) | fixed | — | — | — | — | — | drop | One lattice keeps the screen's subject stable |
| clock division | — | — | — | — | — | — | drop | Follows the project's tempo; stock covers it |

Integer conversion: none (new machine). The enum controls index by `round(value × (n − 1))`.

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/ants/definition.json` → 0 errors, 0 warnings, 1 note (trackControl: runs on aux track 12 with its own page on M1; show muted). `machine.json` declares `kind: synth`, `sdk: 1.9`; `resources.trackControl` is `{stateBytes 256, stateAlignment 8, savedBytes 128, aux [12], unique true}`. `resources.display` is the placeholder (`stateBytes 4, nodes 1, palette 1`) until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | more ants, more scent-following, faster fade, scales ordered from fewest degrees to most (pent → chrom) |
| Header values in real units, ≤ ~5 chars | pass, with a note | ants is a count; scale names the scale. scent and fade are percent of their range: neither the exponent nor evaporation-per-step is a unit a player thinks in. Scale names up to 5 characters: see Captions |
| Defaults plainest useful; presets sound good (by ear) | pass by design, **pending ear** | Default 4 ants, half scent, light fade, pentatonic: settles into a phrase within a few bars and keeps evolving. Presets Colony (defaults), Mill (3 ants, scent 90, fade 10, minor: an ant mill that locks onto one loop), Raid (8 ants, scent 25, fade 70, dorian: restless) |
| Engine page holds only the sound's own parameters | pass | No envelope or LFO; every control is the colony's own |
| Page 1 holds what's played most | pass | One page, four controls |
| Port parity: nothing silently lost | pass | New machine; the three dropped internals are listed above |
| Saved sounds compatible (if released) | n/a | Unreleased |
| `id` final | pass | `ants` |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ants | 1..8 | count (enum) | 4 | 1 / 5 / 8 | 1 × 12.8 = 13 px | yes |
| 2 | scent | 0..1 | percent | 50 | 0 / 50 / 100 | 3 × 12.8 = 38 px | yes |
| 3 | fade | 0..1 | percent | 30 | 0 / 50 / 100 | 38 px | yes |
| 4 | scale | 8 scales | enum | pent | pent / lyd / chrom | 4 × 12.8 = 51 px (pent); 64 px (major, minor, phryg, chrom) | pent and the 3-letter names yes; the 5-letter names **no by estimate** |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device. The estimate is pessimistic for lower-case letters, but `major`, `minor`, `phryg` and `chrom` are the ones to measure; if they overflow, the fallback labels are `maj`, `min`, `phr`, `chr`.

Page 1 (played most): ants, scent, fade, scale · Page 2: none · Repeated controls: none.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear. (The "DSP" here is the control code's walk model; the player makes no sound itself, so the scores are what the steered track does.)

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 ants | One voice line to eight overlapping ones: note density and polyphony rise at every step, the largest change on the machine | 4 |
| 2 scent | Random wandering at 0 to a locked repeating phrase at 100; the change is in whether you hear repetition, clear within a bar or two | 4 |
| 3 fade | How long a phrase survives once ants leave it: slow to hear (takes several passes), subtle until ~40, then phrases visibly fail to settle | 2 |
| 4 scale | Changes the pitch set at once: pent to chrom is dramatic, neighbouring modes differ by one or two degrees | 3 |

## 3 · Subject

Five candidates, one per direction from the pass record `passes/01-subject/pass.json` (state `ready_for_pick`). Sketches: `passes/01-subject/v1…v5/rest.svg` (+ `rest.png` at 1:1), generator `passes/01-subject/sketch.py`, notes and a ranking in `passes/01-subject/notes.md`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P12 Orrery | typeset diagram | The nest as a sphere, each octave an orbit, each degree a planet at its pitch-class angle, the trail a run of bright links between planets | ants: count of bodies · scent: trail shape (scattered arcs → one loop) · fade: count of grey old trails · scale: planets per orbit | candidate; trail doubles up at 1:1 |
| v2 | P13 Capture | orthographic elevation | An elevation across the lattice where walked degrees build mounds of scent and fade is a waterline that drowns what isn't walked | ants: count on crests · scent: mound profile · fade: waterline position · scale: mound count | candidate; loses the phrase order, waveform risk |
| v3 | P14 Loom | survey plan | A plan of recent passes, each a traverse across eight step stations, older passes stepping back, a set phrase repeated down the plan | ants: count on the front traverse · scent: how alike the rows are · fade: rows kept · scale: degree quantisation | candidate; reads close to a chart |
| v4 | P5 Field and figure | patent section | The lattice as a ground field cut at its front edge, the trail one bright loop over it, a step strip below | ants: count on loop + strip · scent: strands → one loop · fade: ghost loops · scale: field columns | candidate; section is decoration |
| v5 | P11 Instrument stack (stretch) | hidden-line isometric | A formicarium, one chamber per degree, galleries winding up by octave, the trail the bright tunnel | ants: count in tunnels · scent: tunnel bore · fade: collapsing tunnels · scale: chambers per gallery | stretch; recognisable, but of the wrong thing |

Chosen: pending, the owner's pick.
