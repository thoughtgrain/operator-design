# Conductor · motion

These rules apply to every page:
- Every ease is exponential ease-out and settles in 0.2 s.
- Reduced motion, a track change and a page change all jump straight to the end state.
- Nothing moves while the sequencer is stopped and no knob is turning.

## M1 · song

| trigger | what moves | from → to | time | reduced motion |
| --- | --- | --- | --- | --- |
| turn key | all 7 planets, their labels, rings and halos travel round the orbit; the moons ride with the sounding planet | old pitch class → new, along the orbit (not across it) | 0.2 s | jump |
| turn scale | planets that change pitch class slide one tick; labels re-case | — | 0.2 s | jump |
| turn prog | loop planets grow 1× → 1.55× and fill; others shrink and hollow; the transfer arc re-lights | — | 0.2 s | jump |
| turn dens | moons scale; ruler kicks appear by scaling up from 0.4× | — | 0.2 s | jump |
| turn cmplx | moons glide to their scattered phases; rings scale in from 0 when sevenths switch on at 65 | — | 0.2 s | jump |
| turn hrate | separators slide to their new bars; lit cells change on arrival | — | 0.2 s | jump |
| turn swing | offbeat bodies slide right and down | — | 0.2 s | jump |
| turn evolve | halos scale | — | 0.2 s | jump |
| chord change (playing) | the 8 moons travel the short way round the orbit to the new planet; planet styles swap; the arc re-lights | — | 0.2 s | jump |
| a lane plays | its moon lights to the bright greys at 1.4× | then fades over 0.2 s (today's `glow`) | — | no glow; lit only on the step it plays |
| step | the ruler body under the playhead swells 1.35×; the track playhead steps | — | instant | same |
| freeze (Shift + enc 2) | halos collapse; `evolving` → `frozen` | — | 0.2 s | jump |
| stop | moons return to chord 1's planet, the playhead hides | — | 0.2 s | jump |

## M2–M4

| trigger | what moves | time |
| --- | --- | --- |
| turn lane (M2) | the open row closes as the new one opens; rows below slide | 0.2 s |
| turn oct / vel / gate (M2) | bodies rise, scale, or the tails scale | 0.2 s |
| turn vary (M2) | bodies swap to hollow one by one in a fixed seeded order | instant per body, staggered over 0.2 s |
| step (M2, M3) | the playhead column steps; hits under it go to `#CDCDCD` at 1.5× for one step; M3's notes ahead of it are hollow | instant |
| turn to (M4) | the route line and band slide to the new column | 0.2 s |
| mute (M4) | the line and band slide back behind the mask, the strike scales in from the left | 0.2 s |
| turn low / high / xpose (M4) | caps slide; cells change shade as a cap passes them | 0.2 s |

## Flashing

At 16ths and 180 BPM a moon could relight 12 times a second. A retrigger therefore **restarts the fade**; it doesn't toggle the fill. That keeps each moon to one rise and one fall per note train, under WCAG 2.3.1's three flashes a second. This is already how `glow` behaves in `display.cpp`, so I'm keeping it.
