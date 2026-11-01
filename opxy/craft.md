# Craft

The rules in `constraints.md` and the perceptibility floors make a screen work. They don't stop it looking childish. Toro's revision 2 passed every gate and still read like clip-art next to MNMD and labyrinth's own first Taurus chart. These are the rules I took from that comparison. A design isn't ready for review until it meets them, and the review checks them side by side with a reference.

## One drawing language

Pick the language before drawing anything, from the subject's own world: a star atlas, a patent section, an engineering schematic, an oscilloscope, a typeset diagram. Then draw every element in it.

- Name the language in the brief, with one or two references (`opxy/reference/`, `library/`).
- Every new element is drawn the way that language would draw it. A moon in an atlas is an outline with a terminator on an ephemeris track, not a flat grey disc. A meteor shower is plotted trails tracing back to a radiant, not a fan of wedges.
- No icons. If an element looks like it came from an icon set (sunbursts, cartoon moons, target rings, speech-bubble shapes), redraw it in the language or drop it.

## Line weights

Three weights, used consistently. Strokes stay the same width at any zoom or scale.

| Weight | Width | For |
| --- | --- | --- |
| Hairline | 1–1.2 px | grids, guides, figure lines, ticks |
| Line | 1.5 px | secondary outlines, contours |
| Subject | 2–2.5 px | the one thing the screen is about, when it's drawn as an outline |

A part that's scaled for motion is authored so its stroke stays inside this table at both ends of its range. If that's impossible, hide it at the far end rather than let it thicken into a wedge.

## Value and fill

- One brightest element (`#CDCDCD`): the subject, or the thing a note just hit.
- Secondary marks in the mid greys, ground at `#323232`–`#4B4B4B`.
- Outlines first. Fills only as dark bodies behind bright outlines (MNMD's operator circles, the Moon's earthshine) or as the subject's single bright mass.
- No nested bands of contrasting grey. They read as a target.
- Solid and wireframe can share a figure when they mean something different (toro: quiet parts hollow, loud parts solid; meikyu's planets: a step that plays fills in). Keep wireframes hidden-line, with a black fill so they still hide what's behind them, and keep the edge a mid grey so a solid part stays the brightest thing.

## Composition

- At least 40 % of the body stays black.
- The subject sits where the eye lands; everything else is quieter and smaller.
- Elements that move keep clear of each other through their whole range, not just at rest. Check the extremes on the contact sheet.

## Text

Small device-font text is part of the language when the subject has it: an atlas labels its stars and its page, a schematic labels its parts. Use it at 10 px in a mid grey, sparingly, and only on things that don't move (text slots go to the header). Labels make a screen look authored. An unlabelled atlas looks like a screensaver.

## Motion

Motion is small, precise and physical: a membrane ripples, a fork vibrates, a figure brightens for a beat. No bursts, bounces, expanding bullseyes or confetti. A note is answered by the subject itself before anything else.

## Think in 3D

If a screen shows depth (orbits round a sun, a drum, an isometric field, a stack seen from an angle), I build it as a 3D scene and project it. I don't draw 2D curves and nudge them until they look about right. Meikyu's orrery went through four rounds of hand-bent ellipses that never wrapped the sun properly and pinched together near it; the version that worked modelled the sun as a sphere, the orbits as evenly spaced circles round it, and put one camera on the scene. Here's what that means in practice:

- **Model, then project.** Every point comes from a world position through one camera: position, look-at point, and a projection fitted so the key object lands where the composition needs it. The picture follows from the model, so spacing, curvature and size can't drift apart from each other.
- **Space things in the world, not on the screen.** Concentric orbits stay evenly spaced all the way round because they're evenly spaced in 3D. If curves bunch up on screen, the model is wrong, not the drawing.
- **Depth decides order.** Painter's order by distance to the camera: whatever's nearer than an object is drawn after it. For spheres, compare centre distances (exact for two spheres). Split lines (orbits, rings) into runs that are nearer or further than the object they pass, so the near run crosses in front of it and the far run goes behind it. Let the occluder's own fill hide what's behind it.
- **Size from distance.** A body's drawn size is its world size times pixels-per-unit at its depth. Don't hand-tune a "depth scale".
- **Check the camera against the frame.** Search camera angle, height and distance for the one that keeps the most of the scene on screen with the key object fixed. Accept what geometry forces and say so: a ring round a point on the screen's edge is always half off-screen.
- **The device can still only translate and scale.** Projection happens in the generator (and in `display()` on the device); nodes still move by translation plus a uniform scale. Fake rotation with pre-drawn variants (a planet's meridians, a rock's tumble), not by tilting a node.

## Review: side by side

Before phase 7, put the screen's rest frame next to one reference from `opxy/reference/` or `library/`, both at 1:1, and answer:

- Is every element drawn in the named language?
- Do the line weights match the table, at every zoom?
- Is there exactly one brightest element?
- Does anything look like an icon?
- Would this sit comfortably in the same set as the reference?

Any "no" goes back to phase 5. The gates can't catch this; only looking can.
