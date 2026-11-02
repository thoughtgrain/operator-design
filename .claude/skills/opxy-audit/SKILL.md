---
name: opxy-audit
description: Audit an existing OP-XY machine screen against the operators guidelines ("this is mine, does it meet the guidelines?") and, when it passes and the author confirms it's theirs to share, add it to library/. Use for any screen review, audit or library submission.
---

# OP-XY screen audit

You're running `opxy/audit.md`. Read `opxy/constraints.md` and `opxy/accessibility.md` first.

## Steps

1. **Gather.** Ask for whatever exists: `definition.json`, frames or preview SVG exports, `panel.svg.fragment`, screen captures (cropped to 480 × 220 or 960 × 440, named `rest`, `playing`, `c<N>-000/050/100`), a video. Put them in `screens/<machine-id>/audit/`. Ask, in one line, whether it's their own work and under what licence.
2. **Scores.** Get each control's audible score 1–5 from the author. If they don't have them, score from the sound or DSP and ask them to confirm.
3. **Run what applies:**
   - `python3 opxy/tools/lint_definition.py <definition.json>`
   - `python3 opxy/tools/lint_frame.py <frames or fragment> --definition <definition.json> [--two-page] [--fragment]`
   - `python3 opxy/tools/perceptibility.py <dir> --scores <scores> --names <labels>`
   - `python3 opxy/tools/contact_sheet.py <dir> --out <dir>/contact.svg --png`, and look at it at 1:1.
4. **Judge by eye:** the craft review in `opxy/craft.md` beside a reference at 1:1, one subject, every control reads, the accessibility checklist, motion (from a video or description), "before you submit" from PR #260's ux.md (open; a house checklist).
5. **Report.** Fill `opxy/templates/audit.md`. Anything not checked says **not checked**. Device-only items say **pending device**.
6. **Verdict.** Meets / meets with notes / not yet, per `opxy/audit.md`. For "not yet", list the changes in order of impact. Never lower a score or skip a floor to reach "meets".
7. **Library.** Only on "meets" and only if the author confirmed it's theirs to share: make `library/<id>/` with the contact sheet, frames or captures, `audit.md`, and a `README.md` from `opxy/templates/library-card.md`; add the row to `library/README.md`. Someone else's work goes to `opxy/reference/` as a link and annotation instead, never into the library.
