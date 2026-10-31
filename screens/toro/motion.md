# Toro · motion

Every motion answers a turn, a note or a press. At rest nothing moves. Eases are exponential ease-outs that settle in 0.15–0.2 s, computed from `elapsed`, not per frame, so they don't speed up or slow down with frame rate. With `reduced_motion` set, or on a track change or `display_reset`, everything jumps to its end state.

## Turns

| Control | Moves | From → to | Ease | Reduced motion |
| --- | --- | --- | --- | --- |
| spread | β, ζ and the 3 joins that touch them | old pose → new pose | 0.15 s | jump |
| fold | ecliptic outlines 0 and 1 | re-key both paths with the new fold shape | none: the shape follows the detent; the key changes only when fold's value changes | same |
| cutoff | Aldebaran's spike, core and halo | scale and shade step through the greys | 0.15 s | jump |
| res | Pleiades positions (tightness), ring scale and shade | | 0.15 s | jump |
| shape | β, ζ, joins | lift | 0.15 s | jump |
| noise | field stars 53–64 | stars added or removed one at a time, each fading in through `#4B4B4B` → `#969696` | 0.15 s per star | jump to count |
| drive | the 3 Milky Way lines | spread and shade | 0.15 s | jump |
| aphx | standing comet segments 45–47, head 48 | length, kink angles, shade | 0.2 s | jump |

## Notes

| Trigger | Moves | Behaviour | Ends |
| --- | --- | --- | --- |
| note on (serial changes) | Aldebaran | core flares +0.6 scale, halo steps up two greys, then eases back | 0.2 s |
| note on | ecliptic | shade to `#CDCDCD`, eases back to `#969696` | 0.2 s |
| note on | Pleiades | the cluster turns 15° + 45° × res, decelerating | 0.2 s |
| note on | launched comet | with probability 25 % + 70 % × aphx, one of 2 comets crosses: 48 px tail, 0.7–1.2 s flight, fading | at the edge, or when its flight ends |
| held (`held_notes` > 0) | field stars that are out | up to 3 stars per frame brighten to `#CDCDCD` and back; each star changes at most every 350 ms (≤ 3 flashes/s) | hold ended → all return to `#969696` within 0.15 s |
| hold ended | | release: anything still lit eases back | 0.15 s |

Retired from the current port: the sky turn about Aldebaran on every note (moved ~25 nodes per note and never settled at fast tempos), the Pleiades' up-to-2.5 s spin, and the comet that crossed the idle sky every ~9 s.

## Press

Encoder press switches pages through `page_header.hpp`: the edited row grows to 20 px and onto the bar, the other shrinks to 13 px grey, settling in 0.15 s. The chart doesn't move on a press.
