# Accessibility on a 480 × 220 grey screen

WCAG was written for web pages, but the reasons behind it hold on a hardware screen: people read it in bad light, at arm's length, mid-performance, with less-than-perfect eyesight. I borrow the thresholds where they fit and say where the device forces a trade-off.

## Contrast

Ratios against the black canvas, computed with the WCAG relative-luminance formula. Text needs 4.5:1, meaningful non-text parts (a striker, a trace, a marker the player reads) need 3:1 (WCAG 1.4.3 / 1.4.11).

| Grey | On black | Use it for |
| --- | --- | --- |
| `#CDCDCD` / `#CBCBCB` | 13.2 / 12.9 | Primary subject, active text, the part being edited |
| `#AFAFAF` | 9.6 | Secondary bright parts |
| `#969696` | 7.1 | Secondary parts, body text |
| `#7D7D7D` | 5.1 | Inactive layers that still carry meaning; smallest text I'll use for body labels |
| `#646464` | 3.55 | Non-text parts only (inactive layers, guides). Not for text. |
| `#4B4B4B` | 2.41 | Ground and decoration only: meshes, fields, bodies behind outlines |
| `#323232` | 1.64 | Fills behind bright outlines, ground planes |

Stock trade-off: the inactive page row uses `#5A5A5A` titles (3.0:1) and `#707070` values (4.2:1). That's below 4.5:1 for text, and it's deliberate on TE's side: the grey row is context, the bright row is what you act on. I keep the stock convention so machines feel like one instrument, and I never put information only in that grey row that the player needs before pressing.

Header bar: stock flips text at the midpoint. Black on the lightest-dark step it meets (`#7D7D7D`) is 5.1:1, rising to 13.2:1; `#CBCBCB` on the darkest-light step it meets (`#646464`) is about 3.7:1. That step is the weakest spot in the stock header, so if I draw my own header I don't put my own small text over `#4B4B4B`–`#7D7D7D` without checking it.

## Size

- Text ≥ 8 px is the floor from ux.md; I aim for ≥ 10 px for anything the player reads during play.
- Meaningful parts ≥ 3–4 px in their smallest dimension; strokes ≥ 2 px for the subject, ≥ 1.5 px for secondary lines.
- Repeated lines (hatching, meshes, stacks) ≥ 3 px apart, ≥ 6 px for stacks I want read as separate layers.

## Meaning never rides on one cue

The screen is grey, so colour is out. That makes the next-weakest cue, a small grey step, tempting. I don't let a state or difference rely on it alone:

- Active vs inactive: shade **and** size or weight (the header does both: bright + 20 px vs grey + 13 px).
- A control's effect: a channel from `patterns.md` (rotation, position, scale, shape, count), with shade only as a second cue.
- Which control drives which part: the part moves when that knob turns, and where it fits, it sits in that knob's column (P7).

## Motion

- Idle is still (ux.md), which also means nothing competes for attention when the player isn't doing anything.
- Ease-outs of 0.15–0.2 s; nothing loops at rest.
- No flashing: no element alternates bright/dark more than 3 times a second (WCAG 2.3.1). Fast note rolls are where this sneaks in, so a retrigger should restart an ease, not toggle a fill.
- Reduced motion jumps straight to the end state. The jump must still be visible: the end state differs from the start state by a channel, not only a shade.

## Caption width

Univers Next Pro Light is a licensed Monotype font, so it's usually not installed where I render previews. Until I can measure in the real font, I estimate:

`width ≈ characters × 0.64 × font-size`

That 0.64 comes from ux.md's one data point (`5.5mm` at 20 px needs 64 px). It's conservative for digits and short for strings full of `m` and `w`. At 20 px that gives a 53 px column room for about four characters, which is why ux.md says "about five" and I plan for four. An estimate never closes the caption check in review; measuring in the device font does.

## Review checklist

Copy into `review.md` and answer each with evidence.

- [ ] Every frame viewed at 1:1 (480 × 220), not enlarged
- [ ] Text ≥ 8 px everywhere, ≥ 10 px for anything read during play
- [ ] Text greys ≥ 4.5:1 on their background (excluding the stock inactive row)
- [ ] Meaningful non-text parts ≥ 3:1 on their background
- [ ] No part under ~3 px; no repeated lines closer than ~3 px
- [ ] No state or control effect shown by shade alone
- [ ] Each control visibly different at 0 / 50 / 100 on the contact sheet
- [ ] Visual travel matches the audible score from the brief
- [ ] Nothing moves at rest; nothing flashes more than 3×/s
- [ ] Reduced-motion end states differ by more than shade
- [ ] Labels ≤ 8 characters, lower case; value captions measured in the device font (or marked **pending device**)
- [ ] No red anywhere in machine artwork
- [ ] Device photos at rest, playing, heaviest setting (**pending device** until taken)
