---
name: opxy-screen
description: Design or revise the screen an OP-XY machine draws with the open-xy SDK, including building and reviewing its definition.json from a port (OP-1 plugin or other source) — subject, control mapping, node budget, 480x220 SVG frames, contact sheet, motion spec and display.cpp handoff. Use for any OP-XY machine screen, port definition, header layout or screen review.
---

# OP-XY machine screen

You're running the protocol in `opxy/protocol.md`. Read `opxy/constraints.md`, `opxy/patterns.md` and `opxy/craft.md` before drawing anything; `opxy/accessibility.md` before review. Outputs go in `screens/<machine-id>/`.

Start from the library. `library/toro-blocks/` is the house reference: an abstract field (P10 Voice field) driven by a small model of the machine's signal path, built from translated slab nodes, with quiet and scattered parts drawn as hidden-line wireframes and one control (fold) rolling the whole field into a drum. `library/theseus-tower/` is the second (P11 Instrument stack): when the machine plays an instrument people know by sight, draw that instrument from clean geometric primitives as a line drawing, and move only what plays. `library/meikyu-orrery/` (P12 Orrery, not audited) is the reference for a player or anything cyclic: a 3D solar system projected through one camera, items as planets, sequences as links along orbits. `library/meikyu-capture/` (P13 Capture) goes further: find the machine's own rule and draw a physical thing with the same shape (meikyu's weight-under-Dens is a black hole's capture radius), so the picture explains the machine; fixed slots, no spin, the middle kept clear. `library/loom-pages/` (P14 Loom, drafts) is the reference for sequencer pages and multi-page machines: a sequence as cloth (steps as threads, passes as rows, slabs as notes), the same slab language and camera on every page, each page the stock header plus one drawing that the knobs change, never a panel of cells. Avoid hand-drawn figures (animals, traced photos); they kept failing for toro. `screens/toro/gen_blocks.py` is the worked generator to copy from (heights model, slab nodes, wireframe palette swap, the fold drum roll, fragment, prototype, video with the real engine code as a simulated soundtrack). Read P10's pitfalls before faking any rotation: nodes only slide.

## Steps

1. **Gate 0.** Decide screen vs stock page. If there's no single object the sound acts on, recommend the stock page and stop.
2. **Brief.** Copy `opxy/templates/brief.md` and fill intake, including the category (`opxy/categories.md`). Note where the controls come from.
3. **Definition from the port (1A)**, when there's no XY `definition.json` yet: read the source engine's code (not its manual), inventory every control including shared knobs and hidden modes, give each a fate (keep / split / merge / drop with a reason), keep the source's ranges and curves, pick real-unit display formats, lay out pages (page 1 = played most, one alternate per position, no filler), clean defaults, carry presets. Write the port map into the brief and the draft to `screens/<id>/definition.json`, leaving `resources.display` as a placeholder.
4. **Definition review (1B):** run `python3 opxy/tools/lint_definition.py <definition.json>`. Fix errors; resolve or justify each warning in the brief; give every row of the review table a verdict. By-ear and device checks stay **pending device**.
5. **Captions and ranking.** Captions from the reviewed definition (labels ≤ 8 chars lower case, values estimated at chars × 0.64 × 20 against 53 px). Rank each control's audible effect 1–5. If you can't hear the machine, score from the DSP and ask the person to confirm.
6. **Subject pass.** Five candidates, one per direction (`design_pass_start` with kind `subject` if the operator-design MCP server is connected; by hand otherwise: five different pattern × drawing-language pairs that fit the machine's category in `opxy/categories.md`). Each has a named drawing language and a reference from `opxy/reference/` or `library/`. When revising an existing screen, score it against the protocol alongside the five. Record them with `design_pass_submit`, which checks they're unique. **Ask the person to choose** unless they already have.
7. **Map + budget.** One channel per control, travel scaled to score with a visible floor, no on/off-only controls. Fill `resources.display` and re-run `lint_definition.py`. Rest = 0 changed nodes; heaviest playing ≈ 20 average.
8. **Frames.** Open with a frames pass: five `rest.svg` variants of the chosen subject, each from its own direction, submitted and checked for uniqueness, and the person picks one. Then start from `opxy/templates/frame.svg`. Draw `rest`, `playing`, and `c<N>-000/050/100` per control. Generate frames from one script when there are many, so they stay consistent; never hand-patch a single frame out of sync with the brief.
9. **Lint.** `python3 opxy/tools/lint_frame.py screens/<id>/frames/*.svg --definition <definition.json>` (the definition tells it which nodes are mutable outlines and how many points they need; `--two-page` for 5–8 controls, `--own-header` if covering the header). Fix every error; fix or justify every warning in `review.md`.
10. **Perceptibility.** `python3 opxy/tools/perceptibility.py screens/<id>/frames --scores <scores> --names <labels>`. Every control and the note response must pass. Under the floor → back to step 7 with more travel or a stronger channel; never lower a score to pass.
11. **Contact sheet.** `python3 opxy/tools/contact_sheet.py screens/<id>/frames --out screens/<id>/contact.svg --png`, then look at the PNG at 1:1. If any control's three frames look alike, go back to step 7.
12. **Craft review.** Rest frame beside the reference at 1:1 (`opxy/craft.md`). Any "no" → back to step 8.
13. **Motion.** Write `motion.md`.
14. **Video preview: ask.** Ask whether they want one, silent or with sound, and what it shows (`preview_brief` returns the questions, then the spec). You render it with your own tools; the server only specifies it. Engine audio is a **simulation** (engine code run on a computer, not a device recording): label it in the file metadata, the notes file and every caption or card that links it.
15. **Review, handoff.** Write `review.md` (checklist from `accessibility.md`) and `handoff.md` per protocol phase 8.

## Hard rules

- Every design pass is exactly five unique variants (`opxy/protocol.md`, Iterations). Never fewer, never five tweaks of one idea.

- 480 × 220, grey by default, never red. Colour only when the harness's MCP config allows it (`colour_policy`); then a role table in the brief and a designed `panel.grayscale.svg.fragment` linted with `--grayscale-of`. Univers Next Pro Light, ≥ 8 px.
- Bound mutable outlines: `M L… Z`, `fill="none"`, distinct points ≥ 1/8 px apart, closing edge ≥ 1/4 px, no turn within 2.5° of straight back, ≤ 64 points, one subpath.
- Lines are closed ribbons. Parts that meet share an outline or pivot.
- Every control clears the perceptibility floors (tokens.json `perceptibility`).
- Nothing moves at rest. Eases settle in 0.15–0.2 s. Reduced motion jumps.
- One drawing language per screen, three line weights that don't thicken with zoom, one brightest element, no icons (`opxy/craft.md`).
- Anything with depth is modelled in 3D and projected through one camera: spacing in the world, order by distance to the camera, size from depth (`opxy/craft.md`, Think in 3D). Never bend 2D curves to fake it.
- Don't copy stock artwork or other machines' drawings.
- Engine audio in a preview is always labelled simulated. Never describe it as how the OP-XY sounds.
- Device-only checks (caption widths in the real font, rasterization, redraw on hardware, photos) are **pending device** until someone does them. Never mark them done.
- open-xy `docs/display.md` and `docs/ux.md` override this repo if they disagree.
