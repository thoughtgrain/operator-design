# Pylon v5 · clean

- I removed the `ch1` and `ch2` labels; they were the only text in the drawing (lint now 0 errors, 0 warnings).
- I replaced them with channel marks in the graticule's own hairline: a short tick just outside the left edge at each trace's zero line, one stroke for the wire (y 150), two strokes 4 px apart for the mains (y 196). It's how a scope marks a channel's ground level, so it reads as part of the instrument, not as an icon.
- I kept everything else as the owner picked it: the graticule, the four receding wire rows with the front one the only `#CDCDCD` element, the warp threads and the mains trace, all at the same weights and positions.
- Still open from the sketch, not from this cleanup: the frame binds six outlines (four rows, plus the mains trace split into two pieces), and four rows plus the mains need at least five mutable outlines against a limit of four. Phase 4 has to solve that, e.g. by drawing hum as pre-drawn variants.
