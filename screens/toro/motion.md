# Toro · motion (revision 2)

Every motion answers a turn, a note or a press. At rest nothing moves. Eases are exponential ease-outs that settle in 0.15–0.2 s, computed from `elapsed`, not per frame. With `reduced_motion` set, or on a track change or `display_reset`, everything jumps to its end state and note responses are skipped.

The Taurus chart never animates on its own. Its stars, lines and the Pleiades only move when the camera does (cutoff).

## Turns

| Control | Moves | From → to | Ease | Turning cost |
| --- | --- | --- | --- | --- |
| spread | the Moon (earthshine and the shown phase) | slides along x 446, y 186 → 70 | 0.15 s | 2 nodes |
| fold | M1's two outlines and core | re-key both outlines per detent; core scales and steps through greys | outlines follow the detent; core 0.15 s | 3 nodes |
| cutoff | the camera: every chart star, join and Pleiades star, M1, Aldebaran's core, disk, spike and rings | zoom 1× → 3.2× about Aldebaran | 0.2 s | ~30 nodes |
| res | the 4 rings | each ring fades in through the greys as res passes its quarter | 0.15 s | ≤ 4 nodes |
| shape | the Moon's phase | 8 steps, crescent → full; a step swaps which phase node shows | per step | 2 nodes |
| noise | field stars | stars come out (or go) in a fixed order | per star | ≤ 2 nodes per detent |
| drive | the radiant's streaks | count, length and grey | 0.15 s | ≤ 12 nodes |
| aphx | every visible field star | drift along its own fixed direction | 0.2 s | up to 180 nodes: **update in batches of ≤ 30 per frame** so a fast turn spreads over a few frames |

## Notes

| Trigger | Moves | Behaviour | Ends |
| --- | --- | --- | --- |
| note on | Aldebaran core and spike | flare 1.4× and +0.5 spike, easing back | 0.2 s |
| note on | rings that are lit | +2 grey steps, easing back | 0.2 s |
| note on | 2 shock rings | run out from Aldebaran, 12 → 52 px and 12 → 72 px, fading through the greys | 0.22 s and 0.30 s |
| note on | one radiant streak (the next in a fixed rotation) | lengthens by 24 px and brightens, easing back | 0.2 s |
| note on | launched comet | with probability 25 % + 70 % × aphx, one of 2 comets crosses: 60 px tail, 0.7–1.2 s flight, fading | at the edge, or when its flight ends |
| held | field stars that are out | up to 3 per frame brighten to `#CDCDCD` and back; each star changes at most every 350 ms (≤ 3 flashes/s) | hold ended: all return within 0.15 s |

## Press

Encoder press switches pages through `page_header.hpp`: the edited row grows to 20 px and onto the bar, the other shrinks to 13 px grey, settling in 0.15 s. The sky doesn't move on a press.

## Retired from revision 1

Horn stars moving (spread, shape), Aldebaran's magnitude as cutoff, the Pleiades tightening and turning (res), the folded ecliptic line (fold), the Milky Way lines (drive) and the standing comet (aphx).
