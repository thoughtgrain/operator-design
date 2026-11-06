# Nave · screen brief

## 0 · Screen or stock page?

- Subject in one sentence: a stone nave and the sound it gives back, which the four controls change: how long the nave is, how hard its stone, how carved its choir, how far back its doors.
- Not stock: a reverb has one space the sound acts on, and every control is a property of that space, so one subject can carry all four. The subject pass decides how that space is drawn (`passes/01-subject/`).

## 1 · Intake

| | |
| --- | --- |
| Machine id | `nave` |
| Kind | effect (SDK 1.7, own send page, stock header) |
| Category | effect |
| Colour | grey (default) |
| Sounds like | A send reverb modelled on a stone nave: a stone room whose tail runs from a small chapel to a cathedral, bright or dark with the stone. The choir's carving smears early echoes into a wash, and the doors set the gap before the room answers. |
| Concept | A reverb modelled on a stone nave: its length, stone hardness, the choir's diffusion and the doors' pre-delay. |
| Controls | 4: nave, stone, choir, doors |
| Control source | new (the definition below is written against the DSP being designed: an FDN tail with a high-shelf damping filter in the loop, an allpass diffuser chain before it and a pre-delay line in front) |
| Shift row | none. No enum earns its place yet (a "room shape" or "modulation" enum was considered and dropped: it would add a mode the screen can't show without a legend) |

### 1A · Definition (new machine)

| XY slot | label | DSP | mapping | display | default | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | nave | RT60 of the tail | exponential 0.4 to 12 s | duration | 0.5 (2.2 s) | the room's size; a plain medium hall at default |
| 1 | stone | how long the highs last against the broadband tail (HF RT ratio 0.2 to 0.95, via the loop's high shelf) | linear 0 to 1 | percent | 0.5 | tone, not colouring: 0 is dark soft stone, 100 bright hard stone; 50 is neutral |
| 2 | choir | diffusion: allpass gain and stage count before the tank | linear 0 to 1 | percent | 0.6 | 0 is grainy, discrete echoes (flutter); default sits where tails are smooth |
| 3 | doors | pre-delay | power, exponent 2, 0 to 250 ms | duration | 0.2828 (20 ms) | the power curve gives fine control under 50 ms where most settings live |

Presets: **Chapel** (defaults), **Cathedral** (nave 0.85 → 7.2 s, stone 0.7, choir 0.8, doors 0.55 → 76 ms), **Crypt** (nave 0.2 → 0.79 s, stone 0.25, choir 0.35, doors 0.1 → 2.5 ms).

### 1B · Definition review

`python3 opxy/tools/lint_definition.py screens/nave/definition.json` → 0 errors, 0 warnings. Two notes, both informational: effects have no browser preview yet (design from stills, check on a device), and effect resources beyond `display` aren't reviewed by the tool. `resources.display` is a placeholder until phase 4.

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | longer nave, harder stone, more choir (diffusion), doors further back (more pre-delay) |
| Header values in real units, ≤ ~5 chars | pass, pending device measure | `2.2s`, `12s`, `20ms`, `250ms` (5 chars, est. 64 px: tight, see captions) |
| Defaults plainest useful; presets sound good (by ear) | pass in principle; by ear **pending** | no colouring control defaults on; presets pending a listen |
| Effect page holds only the sound's own parameters | pass | four properties of the room, no envelope or LFO |
| Page 1 holds what's played most | pass | one page |
| Port parity | n/a | new machine |
| Saved sounds compatible | n/a | unreleased |
| `id` final | yes | `nave` |

### Captions

| # | label | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | nave | 0.4 to 12 | s | 2.2 s | 0.4s / 2.2s / 12s | 51 px (4 chars) | yes |
| 2 | stone | 0 to 100 | % | 50 | 0 / 50 / 100 | 38 px | yes |
| 3 | choir | 0 to 100 | % | 60 | 0 / 50 / 100 | 38 px | yes |
| 4 | doors | 0 to 250 | ms | 20 ms | 0ms / 63ms / 250ms | 64 px at 250ms (5 chars) | **no, by estimate**; 100ms and up overrun. Measure in Univers Next Pro Light; if it overruns, the stock duration format may print `.25s` (pending device) |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

## 2 · Listen and rank

Scored from the DSP, to confirm by ear.

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 nave | 0.4 s room to 12 s cathedral: the biggest change the machine makes | 5 |
| 2 stone | dark, woolly tail to bright ringing one; obvious on cymbals and vocals, smaller on bass | 3 |
| 3 choir | flutter and discrete slaps at 0 to a smooth wash; clear on drums, subtle on pads | 2 |
| 4 doors | under 30 ms barely heard as delay (it separates source and room); above ~80 ms an audible gap | 3 |

## 3 · Subject

Pass: `passes/01-subject/` (state `ready_for_pick`). Each candidate's channels and risks are in `vN/candidate.json`; sketches in `vN/rest.svg`; notes and a ranking in `notes.md`.

| candidate | pattern | drawing language | subject in one sentence | verdict |
| --- | --- | --- | --- | --- |
| v1 | P1 Section drawing | survey plan | The church measured in plan, porch to apse, with one sound ray bouncing wall to wall from the door. | open |
| v2 | P2 Diagram + trace | patent section | Fig. 1 cuts the nave lengthwise, fig. 2 plots the impulse it returns after the doors' gap. | open |
| v3 | P3 Trace as subject | hidden-line isometric | The decay as a waterfall of twelve frequency slices, bass in front, treble at the back. | open |
| v4 | P4 Stack in depth | star atlas | Five charts of echoes stacked in depth from first reflections to late tail, lit from the door's source star. | open |
| v5 | P9 One-bit ink (stretch) | engineering schematic | A one-bit church in side elevation with schematic dimension and decay glyphs. | open |

Chosen: pending, the owner's pick.
