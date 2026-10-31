# Screen design protocol

How I go from a machine's sound and parameters to a screen design that's ready for someone to implement in `display.cpp`. Each phase has an output and a gate. I don't start the next phase until the gate passes, because the expensive mistakes (wrong subject, blown node budget) are cheap to catch early and painful to catch on hardware.

Everything lands in `screens/<machine-id>/`:

```
screens/<machine-id>/
├── brief.md          ← phases 0–4 (incl. port map and definition review), from templates/brief.md
├── definition.json   ← phase 1A draft, when the machine has no XY definition yet
├── frames/           ← phase 5: rest.svg, playing.svg, c<N>-000.svg, c<N>-050.svg, c<N>-100.svg
├── contact.svg       ← phase 5: tools/contact_sheet.py output (+ contact.png if rsvg-convert exists)
├── motion.md         ← phase 6
├── review.md         ← phase 7
└── handoff.md        ← phase 8
```

## Phase 0 · Does it earn a screen?

Read the sound. Ask: is there one object or scene this sound acts on? If not, it gets the stock page (see Gate 0 in `patterns.md`) and the protocol ends here with a one-line note in `brief.md`.

**Gate:** I can name the subject in one sentence, or I've decided on the stock page.

## Phase 1 · Intake

Fill in the top of `brief.md`: machine id, kind (synth, effect), what it sounds like in two sentences, and where the controls come from: an existing XY `definition.json`, a port from another platform (OP-1 plugin, Eurorack module, plugin code), or a new machine.

If the machine is a port and has no XY definition yet, do 1A. If an XY definition already exists, skip to 1B and review it. A new machine with no source starts its definition in 1A too, with "source" meaning the DSP I'm writing.

### Phase 1A · Definition from the port

The screen can only show what the controls do, so the definition comes before the design. I build `definition.json` from the source engine's code, not its manual, because the code is what sounds:

1. **Inventory the source controls.** Every knob, page-2 word, shift function and hidden mode, with its range, curve and default as the source implements it. Note any controls that share a knob (toro's OP-1 DRIV/APHX split one knob down the middle).
2. **Decide each one's fate:** keep, split (one shared source knob becomes two XY slots), merge, or drop. Dropped controls need a reason ("velocity accent: the XY applies velocity after the engine").
3. **Map ranges and curves.** Keep the source's response where the sound depends on it: same min/max, same curve (`linear`, `anchors`, `power`, `exponential`, `enum`). When the source works in a different integer range (OP-1 0..32767), say how the port converts it.
4. **Choose display formats in real units.** `ratio`, `semitones`, `duration`, `enum` over `percent` whenever the musician thinks in that unit. A `percent` display on a non-0..1 range shows the wrong number.
5. **Lay out the pages.** ≤ 4 controls use one page. 5–8 use `"press": "page"`: page 1 is what's played most, each page-2 control names its `control` position, at most one alternate per position, no filler parameters.
6. **Set defaults to the plainest useful sound.** Colouring or degrading controls (drive, noise, drift, crush, mod depth) default to 0.
7. **Carry presets across** with exactly the declared controls, values in [0, 1].
8. **Leave `resources.display` as a placeholder.** Phase 4 sets it from the screen budget.

Output: the draft `definition.json` and a **port map** table in `brief.md`: source control → XY slot, range, curve, default, fate, notes.

**Gate:** every source control appears in the port map with a fate; the draft passes `lint_definition.py` with no errors.

### Phase 1B · Definition review

A definition is a contract with every saved project, so I review it before designing on top of it. Run the checker, then answer the human half:

```sh
python3 opxy/tools/lint_definition.py path/to/definition.json   # reads machine.json beside it
```

The checker covers structure (mirroring the SDK validator: fields, ids, labels ≤ 8 letters/digits/spaces, defaults and presets in [0, 1], mapping kinds, display formats, alternate positions, page rules and the sdk versions they need, display limits) and flags likely review problems (colouring controls defaulting on, envelope/LFO controls on the engine page, `percent` over non-unit ranges, long enum captions).

The judgement calls it can't make go in the brief's review table, each with a verdict and a reason:

| Check | Source |
| --- | --- |
| Every control's name says what rises when turned clockwise | ux.md Controls |
| Header values in real units, ≤ ~5 characters, measured in the device font | ux.md Controls, Screens |
| Defaults are the plainest useful setting; presets sound good straight away (by ear) | ux.md Principles, Controls |
| The engine page holds the sound's own parameters; any envelope/LFO kept has a reason no stock module covers | ux.md Controls |
| Page 1 holds what's played most | ux.md More than four controls |
| Port parity: nothing the source did is silently lost; changes are listed | port map |
| Saved sounds: if the machine is already released, parameter order and mappings are unchanged, and 0 in a new slot sounds as before | ux.md Saved sounds, api.md |
| `id` is final (presets store it forever) | api.md Identity |

**Gate:** zero checker errors; every warning resolved or justified in the brief; every review row has a verdict. Anything only provable by ear on a device stays **pending device**.

After 1B, the header captions come straight from the reviewed definition, which is why caption widths are checked here and not later: labels ≤ 8 characters, values estimated to fit their column (see the width note in `accessibility.md`).

## Phase 2 · Listen and rank

For each control, judge its audible effect across 0 → 100 (by ear in the preview, or by level/band energy) and score it 1–5. This score sizes the control's visual travel in phase 4.

Why: ux.md asks that a control be seen as much as heard. A quiet control with a huge visual swing lies to the player; a loud one with a tiny mark leaves them guessing.

**Gate:** every control has a score and a one-line reason ("cutoff sweep, dramatic: 5"; "drift, subtle until 70: 2").

## Phase 3 · Subject

Write two or three candidate subjects, each in one sentence, each tied to a pattern from `patterns.md` (section drawing, diagram + trace, figure...). For each, sketch in words what every control does to it. Pick one and say why.

This is where I stop and ask if the person hasn't already chosen. The subject is the biggest creative decision and the hardest to change later.

Name the drawing language too (`craft.md`: an atlas, a patent section, a schematic) and one or two references it should sit beside.

**Gate:** one subject, one pattern, one drawing language with a reference, and a sentence per control saying what moves. Reject any candidate where a control has nothing to move, or where the screen reads as a dashboard of meters.

## Phase 4 · Map and budget

Fill the mapping table in `brief.md`:

| control | score | channel | part | travel at 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- |

Rules:

- One primary channel per control, no two controls on the same channel of the same part.
- Travel scales with the score and clears the channel floors in `constraints.md` → Perceptible change (≥ 24 px, ≥ 30°, ≥ 1.6×, ≥ 12 items, shape ≥ 16 px). A score-1 control still has to read at arm's length.
- No control is only an on/off change in the drawing.

Then the budget: declare `paths`, `points`, `nodes`, `texts`, `palette` (this fills the `resources.display` placeholder from 1A; re-run `lint_definition.py` after), and estimate changed nodes per frame at rest (must be 0), playing at defaults, and playing at the heaviest setting (target ~20 average).

**Gate:** budget fits `constraints.md`, rest cost is 0, heaviest playing estimate ≤ ~20 average with a stated peak.

## Phase 5 · Frames

Draw the frames as SVG at exactly 480 × 220, starting from `templates/frame.svg`. Required set:

- `rest.svg`: all controls at default, no notes
- `playing.svg`: defaults, notes held, mid-animation
- `c<N>-000.svg`, `c<N>-050.svg`, `c<N>-100.svg` for each control N, others at default

Authoring rules for frames (they're meant to become `panel.svg.fragment`, so I author them that way from the start):

- Bound parts get device IDs (`<id>_node_<i>`), mutable outlines are `M L… Z` with no fill and distinct points.
- Every leaf has explicit `fill`, `stroke`, `stroke-width`. No group styles, no gradients, filters, masks, `<use>`, CSS.
- Lines are closed ribbons, not strokes traced back.
- Text uses `font-family="UniversNextPro-Light"`. Previews will fall back to another font locally, so I treat rendered widths as approximate.

Run the linter on every frame, then build the contact sheet:

```sh
python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg --definition <definition.json>   # + --two-page for 5–8 controls
python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg
```

Then check that every control changes enough of the screen for its audible score:

```sh
python3 opxy/tools/perceptibility.py screens/<id>/frames --scores <phase 2 scores, in control order> --names <labels>
```

**Gate:** zero lint errors; warnings either fixed or explained in `review.md`; `perceptibility.py` passes for every control and the note response. If a control is under its floor, go back to phase 4 and give it more travel or a stronger channel; don't lower the score to make it pass.

## Phase 6 · Motion

Write `motion.md`: for each trigger (turn per control, note on, held, hold ended, page press) what moves, from what to what, over how long, and the reduced-motion end state. Use the vocabulary at the end of `patterns.md`.

**Gate:** nothing moves at rest; every ease settles in 0.15–0.2 s; held-note motion lasts as long as notes are held; reduced motion and track change jump to the end state.

## Phase 7 · Review

Start with the craft review in `craft.md`: the rest frame beside a reference at 1:1, five questions, any "no" back to phase 5. Gates prove a screen works; this is where it's judged for whether it looks authored.


Copy `checklists` from `accessibility.md` and the "before you submit" items from ux.md into `review.md` and answer each one with evidence (a frame name, a number). Anything only provable on hardware is marked **pending device**, never ticked.

**Gate:** every item answered; nothing ticked that wasn't checked.

## Phase 8 · Handoff

Write `handoff.md` for whoever implements it in the machine's repo:

- The `display` block for `definition.json` with the numbers from phase 4.
- Node index map: node `i` → part → which input drives it → channel.
- Palette map: entry `i` → hex → used for.
- Text slot map, if any.
- What `DisplayState` needs (NoteTracker, eased values, page header).
- Path key policy: which control changes each path's key.
- Open device checks: the pending items from phase 7.

**Gate:** someone who hasn't read the brief can implement `display.cpp` from `handoff.md` and the frames alone.

---

## Revisions

When a design changes after handoff, I update the brief's mapping table first, re-run phases 4–8 for what changed, and note the change at the top of `handoff.md` with a date. Frames get regenerated, not hand-patched, so the contact sheet always matches the brief.
