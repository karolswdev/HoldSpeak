# Night Train — a journey, seen from a seat

DRAFT — owner-requested 2026-10-16; owner judges the actual live scene. Tuesday:
a quiet, convincing place behind productive work, with depth and passing scenery.
Existing `night-train` identity, Change places selection, motion and opt-in sound.

## Composition

A seated view from the left berth, looking obliquely across a small walnut table
toward a broad window. Curved emerald upholstery frames the near left edge;
aged brass catches small warm highlights. A shaded lamp, ceramic cup and partly
open book form one close group below the window. Lamp and window center stay
close horizontally, so both survive the phone frame. Interior warmth contrasts
with readable cool blue-hour hills, a lake, forest slopes and sparse close trees.
Occasional station lights pass through the close layer. Travel has several
recognizable stages, with soft continuity and depth, not a conspicuous short loop.

Use metres consistently: compartment roughly 2.25 m wide × 2.6 m deep × 2.3 m
high; window about 1.65 × 1.0 m; table 0.78 × 0.48 m at 0.75 m height; lamp
0.38 m, cup 0.09 m, book 0.22 m. Initial camera approximately
[-0.58, 1.12, 1.37], target [0.06, 1.28, -1.26], perspective 49 degrees.
Window on z=-1.35, sill0.92/top1.92; lamp around [0.10,0.78,-0.62].
Refine exact camera/light values from actual GL shots. Portrait keeps the
window/lamp relationship, one seat edge and a useful amount of outside world.

## Material and motion

Rounded, padded seats with restrained tuft/piping; fine walnut grain, subtle
fabric weave/sheens, warm metal and glazed ceramic. Shared materials and static
batching keep detail economical. Curved curtain folds and deep window jambs
provide actual 3D shadows. One low-alpha Fresnel Reflector pane shows the actual
interior in the glass, with a bounded target around512 px maximum. Rain stays
close to the glass, fine and quiet. A warm practical lamp pools light onto the
book/table; cool window fill retains material shape. Bloom stays restrained.
Avoid the current crushed exterior, glowing horizontal stitching and huge room.

Outside: distant layered ridges, lake/water glints, wooded slopes, sparse near
vegetation and occasional passing station lights. Apparent motion differs with depth; rooted objects travel
with their ground. Use stable seeded geometry and continuous travel; initialize at
elapsed0. Tiny carriage/camera vibration only. Keep geographic claims absent.
The scene does not signal app activity; the journey is the background's subject.

## Implementation contracts and ownership

Root owns this direction canvas, records, actual GL/Desk observations, regenerated
still, final check, PR and normal delivery. Workers hold for SHIP, never stage or
commit. Product code starts only after root's canvas GO.

Landscape lane owns new `nightTrainJourney.ts`, `nightTrainLandscape.ts` and two
focused tests in `web/src/desk/gl/__tests__/`. Export
`createTrainLandscape(room: Room): { update(elapsed:number):void; dispose():void }`.
Attach world beneath `room.root` in marked moving groups (preserve animation
through Room batching). Room-created resources belong to Room; directly created
instanced geometries/materials/buffers must be explicitly owned/disposed by this
helper exactly once. Root/root builder invokes update(0) before first render.
Do not add a timer, another renderer/composer, network or async image dependency.
At most a few hundred instanced trees, a handful of terrain layers, one bounded
water/sky treatment and a coherent occasional station segment. No full world engine.

Compartment lane owns `nightTrainScene.ts`, optional train-local
`nightTrainCompartment.ts` / `nightTrainGlass.ts` and its scene lifecycle test.
Consume the exact landscape API above. Retain `Room` renderer/composer, keep
shared `sceneKit.ts` and all other scenes untouched. Construct architecture,
props, materials and window/reflection. Protect custom Reflector from Room's
batching: add via `room.moving()` and own/dispose its geometry/material/target
locally; do not double-register resources with Room. Verify addon dispose API.

Wrap `room.finish()` with explicit reduced/disposed guards: Room currently calls
ticks even while reduced. Freeze landscape, water/rain/glass time, vibration and
parallax together. Preserve static render/resize. Apply responsive camera after
base resize AND each base update, since Room resets its private target. Keep
camera motion tiny; preserve initial composition at Motion off. Dispose is
idempotent; no listener, geometry, texture or render target survives teardown.

## Composition review — 2026-10-16

Root read the existing live scene at 1440/393 before build. The old wide room,
repeating cone trees, absent glass and clipped portrait lamp informed the new
composition. The direction canvas is at `canvas/`; its second capture uses an
explicit background image after CSS suppressed the first background. Root read
both corrected direction shots before issuing implementation GO. This is a
composition decision, not owner acceptance of final appearance.

## Checks and review

Named focused files only, collected then run with the supplied locked runner,
isolated HOME/native state off. Root owns builds/browser walks. Actual captures
at1440 and393 judge composition, depth, material legibility, reflection, motion,
pause, resize and cleanup. The direction canvas is a labelled2D composition study,
not actual GL evidence. Generated picker/fallback still comes from the real scene.
Scope: one complete visual/journey rebuild, with original ID and runtime controls.

## Final execution refinements

Actual GL review moved the desktop camera to [-0.50,1.15,0.65] and portrait
to [-0.40,1.15,0.98], retaining the physical architecture and props. The near
berth frames the left edge; the view outside owns most of the composition.
Cup, book and lamp all remain in the phone view. Camera far400 prevents the
oblique landscape sky from clipping at the shared Room default. All changes
stay train-local. Root rejected the first flat terrain/oversized seat view,
then reviewed the shaded terrain, visible lake, fine glass rain and local light.

Station lights now share an actual platform above the water; trees retain fixed
height/scale and travel with their ground. The rendered picker/fallback still is
from the actual final scene at elapsed0, not the direction sketch.
