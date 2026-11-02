# Loom · page map

I took Brian's spec (the four-page screen spec, Nov 2 2026) and drew every page at its resting pose, at the positions and sizes it gives, so we can see whether the parts fit before anyone makes artwork. `pages.py` draws them; `maps/pages.png` has all four at 2× with numbered callouts, and `maps/m1..m4.png` are the 1:1 frames.

Grey only, with shapes and words wherever the spec used a colour (table at the end). Frame lint: 0 errors on all four pages.

## What each page holds

Counts are what the map actually draws, before the header and the 16 palette donors. "Outline" means the 4 animated shapes a page gets; "node" means a placed element; "text" means one of the 16 free text slots.

### M1 · the step ring

| # | element | kind | count | where |
| --- | --- | --- | --- | --- |
| 1 | ring | outline 0 | 1 (32 + 32 points, a ribbon) | centre (240, 104), r 56 |
| 2 | playhead tick | outline 1 | 1 | on the ring |
| 3 | steps: silent / Euclidean / manual (+ ring) / retrigger | node | 16 | on the ring, clockwise from the top |
| 4 | rotation source dot | node | 1 | inside the ring |
| 5 | start chevron | node | 1 | inside the ring at the start step |
| 6 | division | text | 1 | (240, 150) |
| 7 | cycles | node | 16 | y 132, inside the lower third |
| 8 | page `p2/4` | text | 1 | ring centre |

### M2 · repeats and phrase

| # | element | kind | count | where |
| --- | --- | --- | --- | --- |
| 10 | repeat ladder | node | ≤ 16 | left panel x 16–232 |
| 11 | one-step baseline | outline 0 | 1 | under the ladder |
| 12 | choke / tail | text | 1 | (124, 150) |
| 13 | phrase ribbon | outlines 1–2 | **2** | right panel x 248–464 |
| 14 | voicing dashes | node | ≤ 8 | the window's left edge |
| 15 | style text, direction triangle | text + node | 1 + 1 | (356, 52), (456, 52) |
| 16 | phrase speed | text | 1 | (356, 150) |

### M3 · velocity bars

| # | element | kind | count | where |
| --- | --- | --- | --- | --- |
| 20 | baseline | **node** (spec: outline 0) | 1 | y 140, x 24–456 |
| 21 | groove template curve | outlines | **3** (spec: 1) | behind the bars |
| 22 | pulse bars (+ accent caps) | node | 16 (+ ≤ 16 caps) | across the panel |
| 23 | accent / probability | same nodes | — | brightest + cap / hollow, filled by chance |
| 24 | swing | text | 1 | (240, 150) |
| 25 | delay arrow + text | node + text | 1 + 1 | left, under the baseline |
| 26 | length | text | 1 | (440, 52) |

### M4 · keyboard and routing

| # | element | kind | count | where |
| --- | --- | --- | --- | --- |
| 30 | piano keys | node | 24 | from x 16, y 52 |
| 31 | octave bracket | outline 0 | 1 | under the keys |
| 32 | scale name, root + harmony count | text | 2 | (156, 52), (156, 150) |
| 33 | target tracks 1–8 | node + text | 8 + **8** | routing panel |
| 34 | MIDI channels | node | 16 | routing panel |
| 35 | random ribbon | outlines | **2** | the panel's bottom |

### On every page

| # | element | kind | count |
| --- | --- | --- | --- |
| 0 | two-page header | SDK | 16 of the 32 text slots |
| 90 | pad-mode badge | node + text | 1 + 1 |
| 91 | 16-cell strip / key view | node + text | 16 + **16** |
| 92 | mode keys | node + text | 8 + **8** |

## Budget against the spec's own limits

| page | outlines (≤ 4) | nodes (≤ 512) | free texts drawn at rest (≤ 16) | with the key view's 16 cell texts |
| --- | --- | --- | --- | --- |
| M1 | 2 | 58 | 11 | **27** |
| M2 | 3 | 35 | 12 | **28** |
| M3 | 3 (needs 4–8, see below) | 48 | 12 | **28** |
| M4 | 3 | 73 | **22** | **38** |

Nodes are nowhere near 512. Text slots and outlines are where it breaks.

## Where the spec contradicts itself

In order of how much they change the design.

1. **Text slots.** The spec gives each page 16 free text slots and promises to use at most 8. But the key view strip alone needs 16 cell texts, the mode keys add 8 labels, and M4's target squares add 8 more. Every page is over 16 once the strip shows its labels. My suggestion: draw the cell labels and mode-key letters as **nodes** (pre-drawn digit and glyph shapes that show and hide) rather than text. Keep text for the live values only: division, swing, root, scale name, the badge.
2. **Outline reach on long shapes.** An outline can't reach more than ±64 px from its origin, so it spans at most about 128 px.
   - M3: the 432 px baseline and the 432 px template curve would need about 4 outlines each, 8 in all, against a limit of 4.
   - M2: the phrase ribbon (216 px) needs 2.
   - M4: the random ribbon (152 px) needs 2.

   My suggestion: anything that only changes on a knob turn, like the baseline or a template's shape, is a static node or a set of pre-drawn nodes swapped in, not an outline. That leaves outlines for shapes that actually animate, like the playhead, the breathing ring and the jitter. M3 then uses 0–1 outlines.
3. **M4's keyboard doesn't fill its region.** Two octaves of 10 px white keys is 140 px, but the strip is given x 16–296 (280 px). Either the keys are 20 × 44, or the strip is 140 px wide and the scale and root text sit beside it. The 10 × 44 size matches the SDK's output keyboard, so I'd keep it and pull the routing panel left.
4. **M1's ring touches the strip.** The ring runs to y 160, and a 5 px step at the bottom reaches y 165. The strip starts at y 164. The cycle row at y 132 also crowds the left- and right-hand steps. Move the ring up to y 98, or the radius down to 52, which gives a 6 px gap.
5. **Mode keys:** the spec lists 7 keys (bank, pattern, temp, mute, clear, copy, select, ctrl reads as 8 once mute and clear are split) in a 2 × 4 grid. I drew 8; confirm the set.
6. **Roles in grey.** Some roles only differed by hue. Each now has a shape or a word (table at the end): accents get a cap, channels are circles and tracks squares, free-running says `free`.

## Grey only: shapes and words instead of colour

Brian's call (Nov 2): no colour other than grey. Every role the spec gave a hue is carried by a shape or a word, and brightness is only ever the second cue.

**Palette (16 entries, all grey).**

| entry | grey | used for |
| --- | --- | --- |
| 0 | `#000000` | ground, hollow fills |
| 1 | `#323232` | ground lines, guides |
| 2 | `#4B4B4B` | inactive, silent steps |
| 3 | `#646464` | dim marks, outlines of unselected cells |
| 4 | `#7D7D7D` | secondary marks |
| 5 | `#969696` | placed but not active (pulses, bars) |
| 6 | `#AFAFAF` | secondary bright |
| 7 | `#CDCDCD` | active, the step playing, selected |
| 8–15 | spares | the same greys with other stroke widths (hairline, ribbon, cap), since the palette pairs fill, stroke and width |

**Roles.**

| spec role (was a colour) | shape | word |
| --- | --- | --- |
| Euclidean pulse (amber) | filled circle, 5 px | — |
| Manual pulse (orange) | filled circle with a ring | — |
| Retrigger (red) | square | — |
| Rotation source (amber) | 2 px dot inside the ring | — |
| Start point (green) | chevron | — |
| Free-running division (red) | — | `free` after the division |
| Cycles (red-orange) | squares: filled = exists, brightest = current, short bar = muted, hollow = in the loop | — |
| Edits / cc (teal) | half-filled cell | badge reads `edits` / `cc` |
| Keys / fx (magenta) | — | badge reads `keys` |
| Bank / scale (green) | — | mode key `B`; scale name text |
| Pattern / target (blue) | target tracks are **squares** | `trk` |
| MIDI channels (green) | channels are **circles** | `ch` |
| Root (green) | the root key filled brightest, with a dot under it | root name, e.g. `F#` |
| Harmony pitches (blue) | keys filled mid grey with a ring | `+3` count |
| Random (rose) | the jittered ribbon | `rnd 25%` |
| Phrase / range (lilac) | the phrase ribbon | phrase name in the header |
| Accent (cream) | brightest bar plus a 2 px cap | — |
| Probability | hollow bar, filled up to the chance | — |

The map frames now use the words and shapes: M1 shows `1/16 free`, and M4 draws tracks as squares labelled `trk` and channels as circles labelled `ch`. That adds two words on M4, which is 22 texts against 16, one more reason for point 1 above (labels as nodes).

## Next

Once the six points above are settled, I'll redraw the four pages as real fragments (`loom_` ids in the agreed order, palette donors, outlines at exactly 64 points) with the key view overlay on and off, and run them through the operators protocol.
