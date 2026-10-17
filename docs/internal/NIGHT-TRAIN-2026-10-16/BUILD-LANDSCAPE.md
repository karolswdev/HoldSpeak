# Night Train landscape build

DRAFT — UNCHECKED. HOLD FOR SHIP. 2026-10-16.

Implemented after root canvas GO in `wt-night-train-20261016`, branch
`feat/night-train-20261016`. This worker changed only the two new landscape
modules, their two focused test files, and this report. No staging or commits.

`createTrainLandscape(room: Room)` exports exactly `update(elapsed)` and
`dispose()`. Construction initializes at elapsed zero. The compartment wrapper
owns reduced motion and calls the helper only when motion is permitted; the
landscape adds no ticks, timers, renderer, composer, network or asynchronous
image work.

After reading root's actual v1 captures, the exterior was refined from flat
strips to four dense x/z heightfields, each 769 × 41 vertices. Bending ridges,
valleys and crags supply computed normals to a local directional diffuse shader,
with restrained atmospheric fade and snow only at distant high peaks. Terrain
cost is bounded at 245,760 triangles; root owns actual frame measurements.

The world-height dusk shader uses a darker cool gradient and sparse broken
cloud bands. The broad lake now sits at y=0.30 and extends from z=-3.5 to
z=-97.5, with subdued glints. Its intersection with low terrain gives irregular
shorelines and island forms; the foreground is not a continuous high wall.

208 tree instances remain bounded across distant woods, shore woods and sparse
near vegetation. Shared foliage now consists of twenty narrow asymmetric branch
sprays with sagging tips, varying azimuth and reach, rather than a few broad
stacked cones. Seeded clusters give negative space; size, width, lean, rotation
and depth vary. Tree base heights and shore masks are derived from seeded terrain once at
construction. Both woodland layers travel at the shore terrain's 0.30 m/s;
near vegetation travels at its terrain's 1.08 m/s. Height, scale, lean and
rotation remain fixed during travel. All trees recycle on the ground's 600 m
period, preserving their terrain relationship after offscreen recycling.

Five station lamps on 2.1 m posts pass as one occasional segment. A 20 × 2.2 m
platform moves with them, with its top at y=0.54 above lake y=0.30. Post bottoms
meet that top and lights sit at y=2.64. This fixes the isolated lamp that rose
from water in root's actual 180-second v2 capture. All visible geometry stays
behind the compartment's glass.

Seeded profiles, spacing and continuous motion give depth and long continuity.
Terrain contours join across a 600 m interval; recycling takes
place outside the visible world. Trees and station positions wrap far outside
the window. The helper authors scene travel, without a geographic claim.

Moving groups and custom meshes are marked through `room.moving()` so
`Room.finish()` cannot batch their mutable transforms into stationary room
architecture. The helper directly owns ten geometries, eleven materials and
five InstancedMesh buffers. Disposal removes its world and releases each once;
Room assets remain Room-owned.

## Focused proof

Only these two files were collected, then run through the supplied
`.tmp/night-train/locked.py`, with isolated HOME, native state disabled and the
machine test lock:

- `web/src/desk/gl/__tests__/nightTrainJourney.test.ts`: bounded population;
  distinct depths/speeds; smooth visible travel; distant recycling; joining
  terrain profiles and full depth relief; occasional station timing.
- `web/src/desk/gl/__tests__/nightTrainLandscape.test.ts`: initialized actual
  geometry, heightfield density/normal variation and batching protection;
  station platform above water and posts rooted in it; seeded deterministic
  explicit updates with unchanged tree matrix components except horizontal
  translation;
  geometry/material/instance disposal once while retaining Room assets.

Collection: seven named tests in `.tmp/night-train/landscape-final-v3-collect.log`, exit 0.
Final refined run: `.tmp/night-train/landscape-final-v3-run.log`, exit 0:

```text
Test Files  2 passed (2)
     Tests  7 passed (7)
  Duration  816ms
```

Two intermediate v2 runs failed an overstrict test threshold that required
low shore terrain to have the same slope variation as high mountains. The
assertion was narrowed to require substantial variation appropriate to each;
product code was unchanged during those rechecks. After root's bounded integration counsel, station platform context and stable
tree/ground flow were corrected and the exact two files passed again. Product
code is frozen after that final v3 run pending root's actual render review.

## Limits

The tests construct actual Three geometry with a lightweight Room substitute;
they do not render WebGL or judge the composition. Root owns actual 1440/393
captures, rendered depth/material review, previews and the build. No browser,
build, owner-state, staging or commit actions ran in this lane.
