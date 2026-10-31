# Toro · motion (revision 3)

Every motion answers a turn, a note or a press. At rest nothing moves. Eases are exponential ease-outs that settle in 0.15–0.2 s, computed from `elapsed`. With `reduced_motion` set, or on a track change or `display_reset`, everything jumps to its end state and note responses are skipped.

The atlas page itself (grid, figure, labels, Pleiades, radiant symbol, ephemeris track, magnifier frame) never moves.

## Turns

| Control | Moves | From → to | Ease | Turning cost |
| --- | --- | --- | --- | --- |
| spread | the Moon (body, shown phase, limb) | slides along its track, x 170 → 312 | 0.15 s | 3 nodes |
| fold | the Milky Way's 3 contours | re-key per detent; inner contours step through the greys | follows the detent | 3 nodes |
| cutoff | magnified star, core, spikes, rings, 2 neighbours | star radius 1.8 → 27 px; neighbours move out of the window | 0.2 s | ≤ 9 nodes |
| res | the 4 Airy rings | each fades in as res passes its quarter; outer rings stay dimmer | 0.15 s | ≤ 4 nodes |
| shape | the Moon's phase | 8 steps, crescent → full | per step | 2 nodes |
| noise | faint stars | come out (or go) in a fixed order | per star | ≤ 2 per detent |
| drive | meteor trails | 2 → 16, brighter | per trail | ≤ 2 per detent |
| aphx | every visible faint star | drift along its own fixed direction | 0.2 s | up to 165: **batch ≤ 30 per frame** |

## Notes

| Trigger | Moves | Behaviour | Ends |
| --- | --- | --- | --- |
| note on | the 9 figure lines | brighten `#646464` → `#AFAFAF`, ease back | 0.2 s |
| note on | Aldebaran (chart star) | 1.3×, ease back | 0.2 s |
| note on | magnified star and spikes | star 1.12×, spikes +7 px, ease back | 0.2 s |
| note on | lit Airy rings | +2 grey steps, ease back | 0.2 s |
| note on | Milky Way core contour | +1 grey step | 0.2 s |
| note on | one meteor trail (fixed rotation) | lengthens 1.4× and brightens | 0.2 s |
| held | faint stars that are out | up to 3 per frame brighten and back; each at most every 350 ms (≤ 3 flashes/s) | hold ended: all return within 0.15 s |

## Press

Encoder press switches pages through `page_header.hpp` (edited row grows to 20 px onto the bar, the other shrinks to 13 px grey, 0.15 s). The page doesn't move on a press.
