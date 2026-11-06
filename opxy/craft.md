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
- **Semi-opaque areas are hatched, not tinted.** Where a region would be see-through (a range that's off or out of reach, a ghost of where something will be, the part of a curve that's cut away), I fill it with diagonal hairlines instead of a translucent grey, the way the stock filter page hatches the band its cutoff removes. The lines run at 45°, in a mid grey over black, at least 3 px apart at 1:1 (`constraints.md`, Hatching), clipped to the region's outline. Hatching keeps the ground black between the lines, so it reads as "there but not active" without a muddy mid-tone, and it stays legible on the real screen where a 30 % grey would just look like a dimmer solid.
- Solid and wireframe can share a figure when they mean something different (toro: quiet parts hollow, loud parts solid; meikyu's planets: a step that plays fills in). Keep wireframes hidden-line, with a black fill so they still hide what's behind them, and keep the edge a mid grey so a solid part stays the brightest thing.

## Detail follows how often the subject changes

How much detail a drawing can carry depends on how often the subject itself is replaced, not on how fast notes come.

- **The subject swaps often:** keep it minimal. The stock drum machine draws a different instrument for each sound (a tambourine, then something else), so each one is a few bold, closed, double-outline shapes the eye takes in at once.
- **One subject that stays:** detail is fine. Meikyu's black hole is on screen the whole time and only what's on it changes, so a wireframe can stay, in drum mode as well.

Fast notes are a motion question (flashes, pacing, the redraw budget), not a reason to strip the drawing. I made that mistake once with meikyu's drum mode and reverted it.

## Picture, not panel

A screen's drawing represents what the parameters do; it isn't the interface. At rest a page is the header plus one drawing that every knob changes. Strips of cells, mode grids, badges and legends belong to the moment they're used (an encoder held, a mode being picked), not to the resting page. The exception is a page where the interaction is the picture: choosing notes on a keyboard, shaping a filter curve.

Use the stock header, flush with the top of the screen (y 0–20). Reserve the two-page band only when a page has more than four controls or needs the Shift row.

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
- **3D shapes can be detailed line art.** A modelled shape doesn't have to be reduced to its silhouette: I can draw it as detailed line art, with its hidden-line edges plus the structure inside them (facets, ribs, seams, panel lines, construction lines), every line projected from the same model. Outer edges take the Line weight, inner detail the Hairline weight, both in mid greys, over a black fill so the shape still hides what's behind it and the one brightest element stays brightest. How much detail it carries follows how often the subject changes (above): a shape that stays on screen can carry a lot, one that swaps often keeps to a few edges. Keep parallel detail lines at least 3 px apart at 1:1 (the hatching limit in `constraints.md`), or they merge into a grey patch, and count the lines against the node and redraw budget like any other part.
- **Nodes move in the screen's plane.** Projection happens in the generator (and in `display()` on the device); a node moves by translation, a uniform scale and a turn about its own origin (`display.md`, Frame: `turn`, `sweep`), never a tilt out of the plane. So a part spinning on the screen (a dial, an arm) can turn, but a 3D rotation that tips a part towards or away from the camera is faked with pre-drawn variants (a planet's meridians, a rock's tumble).

## Review: side by side

Before phase 7, put the screen's rest frame next to one reference from `opxy/reference/` or `library/`, both at 1:1, and answer:

- Is every element drawn in the named language?
- Do the line weights match the table, at every zoom?
- Is there exactly one brightest element?
- Does anything look like an icon?
- Would this sit comfortably in the same set as the reference?

Any "no" goes back to phase 5. The gates can't catch this; only looking can.
