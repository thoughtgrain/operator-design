# meikyu player page: wheels

Brian picked p2 wheels from round 1 (`../concepts/board-pages.png`). `gen_wheels.py` writes everything here: `panel.svg.fragment` (the device artwork), `panel-lint.svg`, `frames/` and `board.png` (every state at 1:1).

## The idea

meikyu plays phrases out of a 16-step shift register split into two halves, A and B. I wanted the register to look like the thing it is, a loop, so it's drawn as a pair of dials: A's eight steps around the outer wheel, B's around the inner, both starting at the notch at the top and running clockwise. The last phrase's eight tones sit on an arc to the right, read left to right like a meter.

A player page can't move anything; it only switches its 24 dots on and off. So every state has to read from which lamps are lit:

| What changes | What the page shows | Why it reads |
| --- | --- | --- |
| Dens | the wheels fill (100) or empty (0); a step's lamp is lit when it plays at this density | density is literally which steps play |
| Crpt | between phrases, a few step lamps switch (compare `crpt-before` and `crpt-after`) | corrupt rewrites steps after they play |
| a press | the arc lights the tones that sounded; the text names the root, the half it started in, and the phrase count | the phrase is eight steps, so eight lamps |
| Scal | the header value and the keyboard's played dots | the page has no other channel for it |
| Drum | the header value | same |

Scal and Drum only change the header. That's the player ABI's limit, not an oversight: 24 dots are all spoken for, and the keyboard row already shows which pitches the scale produced.

## Device mapping (unchanged from meikyu's `player.cpp`)

- `meikyu_dot_0..7`: A steps on the outer wheel (step 0 just clockwise of the notch)
- `meikyu_dot_8..15`: B steps on the inner wheel
- `meikyu_dot_16..23`: the phrase's tones, first to last along the arc
- `meikyu_text`: centred at x 240, y 157, 18 px
- `meikyu_key_*` / `meikyu_played_*`: authored parked at x 1024; the SDK lays out the keyboard at y 174

Because the ids and meanings match the current page, the handoff is artwork only: in labyrinth, replace `opxy/machines/meikyu/gen_panel.py`'s drawing with this one (or copy `panel.svg.fragment` over). `player.cpp` and `definition.json` don't change.

## How it's drawn

Grey line drawing on black. The rings, spokes and arc rim are mid grey (`#6E6E6E`), and each lamp has a static socket under it (a black disc with a dark grey rim) so an unlit step still shows where it is. The lamps themselves are the dots, filled near white (`#F0F0F0`). Lamps are 4.6 px (A), 3.8 px (B) and 5.4 px (phrase) in radius. The B lamps are the smallest thing on the page, at about 7.6 px across. There's no red anywhere.

## Checks

- Every frame and the fragment pass `lint_frame.py` with no errors.
- Device pending: lamp size on B and the socket rims are the things to photograph.
