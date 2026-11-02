# Audit and library

Two things live here: how I check a screen someone hands me ("this is mine, does it meet the guidelines?"), and how a screen that passes goes into `library/` as a reference for every design after it.

The protocol in `protocol.md` is for designing. An audit is for judging something that already exists, whoever made it, by the same rules. Designs I finish through the protocol go through the same audit before they enter the library, so nothing gets in on the strength of having been made here.

## What to hand over

The more of the real machine there is, the more the audit can check by tool instead of by eye.

| You have | Checks that run | Checks done by eye |
| --- | --- | --- |
| `definition.json` + frames (SVG exports from the open-xy preview, or 0/50/100 frames) | everything: `lint_definition`, `lint_frame`, `perceptibility`, contact sheet | motion, subject, by-ear items |
| `definition.json` + `panel.svg.fragment` + screen captures | `lint_definition`, `lint_frame --fragment`, `perceptibility` on the captures | motion, subject |
| screen captures only (PNG, cropped to 480 × 220 or 960 × 440) | `perceptibility` | everything else, from the pictures |
| a video | none until frames are pulled out of it | everything |

Name captures the way the tools expect: `rest`, `playing`, `c<N>-000`, `c<N>-050`, `c<N>-100`, where N is the control's slot in the definition (1–8). A video gets its frames pulled to those names first.

Anything not checked is written down as **not checked**, never as passed.

## The checks

Run in this order; each one's findings go in the audit report (`templates/audit.md`).

1. **Rights.** Who made it, and can it be shared here? The person auditing their own work says so. Someone else's work is audited only as a reference (`opxy/reference/`, linked, not copied) and never enters the library.
2. **Definition** (if given): `lint_definition.py`, plus the 1B review table from the protocol.
3. **Artwork** (if given): `lint_frame.py` on the frames or fragment, with `--definition` and `--two-page` when they apply.
4. **Perceptibility:** `perceptibility.py` with the audible scores. If the author hasn't scored their controls, score them from the sound (or the DSP) and ask them to confirm, as protocol phase 2 does. Scores are never lowered to make a control pass.
5. **Contact sheet** at 1:1, looked at by eye: one subject, every control reads, no dashboard.
6. **Craft** (`craft.md`): rest frame beside a reference at 1:1. One drawing language, the line-weight table, one brightest element, no icons.
7. **Accessibility checklist** from `accessibility.md`.
8. **Motion:** from the author's description, a video or the preview. Still at rest, short eases, reduced motion jumps, no flashing. If the video has sound, record whether it's simulated (engine code run on a computer) or recorded from a device; anything not stated is treated as simulated, and the sound is never evidence of how the instrument sounds.
9. **"Before you submit"** items from PR #260's ux.md (open, not merged; kept as a house checklist), each answered or marked **pending device**.

## Verdicts

| Verdict | Means | Library? |
| --- | --- | --- |
| **Meets the guidelines** | No errors, every perceptibility floor cleared, every checklist item answered. Device items may be pending. | Yes, marked "device pending" until photos exist |
| **Meets, with notes** | As above, plus warnings the author has justified in writing | Yes, with the notes on the card |
| **Not yet** | Any lint error, any control or the note response under its floor, a checklist item that fails, or a craft question answered "no" | No. The report lists what to change, in order of impact |

## Adding to the library

When an audit comes back **meets** (with or without notes) and the author confirms it's theirs to share:

1. Make `library/<machine-id>/`.
2. Copy in the contact sheet, the frames or captures, and the audit report as `audit.md`.
3. Write `README.md` from `templates/library-card.md`: what the screen is, its pattern, the control mapping, what makes it work, the audit verdict and date, licence and credit.
4. Add a row to `library/README.md`.
5. If it shows a pattern better than the examples in `patterns.md`, link it from there.

A library entry is re-audited when `tokens.json` or `constraints.md` changes a floor it was judged against; the card records the `source.ref` it passed under, so that's easy to spot.
