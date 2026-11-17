# iris · revision pass 03 · notes

The owner's feedback was "more overlap of the rings", "the ends of the rainbow shouldn't be visible at the bottom" and "the other rings should change more when each is blending".

`design_pass_start` handed out composition and camera directions. The owner had already picked the centred layout, and this feedback is about how the rings behave, so I replaced those directions with five ring responses and kept the layout. All five share two changes:

- **The ends run off the bottom.** The bow's centre moves below the screen (y 232), so the bands leave through the bottom edge, and there's no horizon. The bow can't grow: every quarter of the mix line has to stay within ±64 px of its node, which caps the outer radius at about 158 px.
- **More overlap.** The bands are 10 px apart (it was 16) with waves of about ±5 px, so neighbouring crests interlock even at rest.

| | ring response | device cost |
| --- | --- | --- |
| v1 | **slide**: each blended ring slides onto the bright line by its share of the mix (and further with Overlap) | moves only |
| v2 | **swell**: blended rings at full wave height, a ring out of the blend shrinks to a ripple | three pre-drawn heights per band (+128 nodes) |
| v3 | **slide + swell** | both (+128 nodes) |
| v4 | **weight**: blended rings get a heavier, brighter line, the others thin to hairlines | three pre-drawn widths per band (+128 nodes) |
| v5 | **gather**: any ring with a share of the blend lands on the bright line, and rings out of it are pushed away | moves only |

All 20 sketch frames lint clean. At rest every pair differs by 4.1–5.6 % of the body (floor 4 %). `sheet.png` shows each variant at rest, at Morph 50 (triangle and square blending) and at Overlap 100.

The pick is the owner's.
