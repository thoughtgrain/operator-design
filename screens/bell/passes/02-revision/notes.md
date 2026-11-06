# Bell · revision pass 02 · notes

The focus is to refine pass 01's v1 bell. Its shape is the subject, every control changes the bell or how it's struck and rings, and there's no signal or waveform anywhere. All five come from one model in `sketch.py`: a surface of revolution with a filleted shoulder (the knee) and a sound-bow, projected through one camera per variant. Every control is at its default. The frames lint with 0 errors and 0 warnings and have no text in the drawing. `design_pass_submit` returned `ready_for_pick`, with pairs differing by 9.2 to 24.4 % of the body.

- **v1 · centred hero, front elevation cutaway.** The bell is cut away on its front-right quarter, so the hatched water below the air pocket and the clapper show. The bright clapper ball is the sound source, and gain swings it out along a dashed arc.
  The language is the most complete of the five (hidden-line exterior, a hatched wall cut, inner hoops). The wall-cut hatching is only 2–3 lines thick at 1:1.
- **v2 · low horizon, top-down plan.** Seen from above, the bell is a black cut-out in a field of hatched water that sits below a low hairline. The waterline is a dashed hidden ring. Gain draws the rim in its four-node ring mode, bright, with node ticks.
  This one is the most physical answer to "how it rings". But the crown hoops seen from above sit nearly concentric, and the air pocket is only a hidden-line convention.
- **v3 · column-affine section.** The bell is cut straight through. Column 1 has a sounding line whose lead drops level with the rim. Column 2 has the pocket over hatched water, column 3 the shoulder fillet's construction, and column 4 a hammer drawn back from the bow. The struck face of the bow is the brightest thing.
  Every control reads at a glance. The sounding line and hammer sit beside the bell rather than being part of it, and the column layout leans toward a panel.
- **v4 · off-axis diagonal, three-quarter iso.** The bell sits low and right, below a diagonal surface edge, in water whose hatching closes up from 12 to 4.5 px with depth. The waterline is a dashed hidden ring, the shoulder hoop is bright, and gain scales the bell.
  Its 3D reads best. The gradient bands add four hatch densities, and gain as scale reads as "bigger" more than "louder".
- **v5 · full-bleed field, low angle.** The view looks up into the mouth from below. Inside are the water's surface (hatched) and the clapper hanging over it. The rim is bright, as depth's leading edge, and gain grows the clapper's ball.
  It's the only view where the air pocket is seen directly rather than through a cut. Gain's change is a small spot on the axis and may miss the 40 px spread floor.

## Ranking

1. v1: the closest refinement of the pick, and it shows all four controls on the bell itself.
2. v3: clearest at 1:1, but the hammer and sounding line add parts beside the bell.
3. v5: the freshest view of the bell, but gain is weak.
4. v4: strong 3D and gradient, but gain-as-scale is the weakest mapping.
5. v2: the ring mode is lovely, but the plan view hides the pocket and leans toward a target.
