# Iris · motion

Everything here eases out exponentially and settles in 0.15–0.2 s unless it says otherwise. With reduced motion, and on a track change or `display_reset`, every value jumps to its end state. Nothing moves at rest.

| trigger | what moves | from → to | timing | reduced motion |
| --- | --- | --- | --- | --- |
| turn morph | the mix line's radius and shape; band greys follow the window weights | old → new setting, the radius eased, the shape following the eased value | τ ≈ 0.05 s (settles in 0.18 s) | jump |
| turn overlap | band chains slide radially toward the mix line; the mix's shape | eased the same way | as morph | jump |
| turn spread | band cycle nodes rescale along their arcs (0.82–1.18); the mix's beating along the arc | eased | as morph | jump |
| turn tone | the mix's drawn bandwidth (eased); a band crossing its cut swaps raw ↔ rounded chain | bandwidth eased; the swap is a step per band, but the sweep across four bands makes the knob continuous | as morph | jump |
| turn skew (Shift + encoder 1) | the mix's breakpoint | eased | as morph | jump |
| turn phase (Shift + encoder 2) | band chains slide along their arcs (band i by i/8 cycle); the mix's shape | eased | as morph | jump |
| note on (hold started) | the mix line steps from `#AFAFAF` to `#CDCDCD` and starts to travel along the arc | travel speed eases from 0 to 0.8 cycles/s | ease-in τ 0.05 s | no travel; the colour step only |
| held | the mix line keeps travelling (its phase advances, the four outlines rewritten each frame) | — | as long as any note is held | still, bright |
| hold ended | travel slows to a stop and the line returns to `#AFAFAF` | speed → 0, colour back | settles in 0.2 s | jump to rest |
| Shift held | header text only: the four slots show skew, phase, blank, blank (Shift replaces the header's contents; no second row) | — | one frame | — |
| Shift released | the page's titles and values come back | — | one frame | — |
| Shift + encoder 1 / 2 | skew / phase, eased like any turn | as their rows above | as morph | jump |
| parameter reset | that control eases back to its default as if turned | — | as its turn | jump |

The mix line travels in its own phase; it doesn't scroll the bands. The bands are the inputs and stay where the knobs put them. The line carries a note's sense of movement, so a held note looks alive and a stopped one looks still.

Where a note lands doesn't apply here: the display isn't told the pitch, and iris's picture doesn't depend on it.

Redraw: at rest 0 changed nodes. While held, the 4 mix outlines every frame (4 nodes, 4 × 64 points). After hold ended, at most 0.2 s of the same, then 0. A knob turn moves up to the 64 visible band nodes for the length of its ease, and nothing once it settles. Heavy-path cost **pending device**.
