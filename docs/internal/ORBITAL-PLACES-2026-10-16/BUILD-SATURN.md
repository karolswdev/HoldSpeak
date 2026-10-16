# Saturn supporting experience

DRAFT — HOLD FOR SHIP. Bounded worker lane for the owner's selected orbital
places. Design: [DESIGN.md](DESIGN.md). Tuesday: quiet space behind the Desk,
with recognizable rings and passing moons, through the existing Atmosphere host.

## Settled implementation

Warm ivory and gold oblate Saturn, procedural latitude bands with bounded
independent cloud motion, a broad tilted translucent ring plane with radial ice
layers and Cassini Division, analytic planet and ring shadows, Titan amber haze
and a distinct small ice-white Enceladus. Existing local galactic map and rich
seeded star field come from the Mars lane's `orbitalSky.ts` helper. No new UI.
Authored scale and periods are cinematic, not an ephemeris.

Own only `web/src/desk/gl/saturnOrbitScene.ts`, `saturnOrbitModel.ts`, their two
exact focused test files, and this record. Shared registry, runtime, sky, CSS,
assets and root canvas stay with their assigned lanes. No build, browser run,
stage, commit or owner-state access in this worker lane.

## Validation

Implemented the settled scene after root canvas GO. Only the bounded local sky
map loads asynchronously. Procedural planet, rings and moons need no added
assets. Rings use screen-filtered radial ice layers with transparent Cassini and
Encke gaps, depth-tested front/back arcs, an oblate-globe shadow and the same
radial density profile for the ring shadow on Saturn. The host's motion flag
freezes geometry, cloud time and pointer camera movement. Sky refinement can
render the still after a local image load; teardown rejects late callbacks.

Exact worker checks ran through `.tmp/orbital-places/locked.py`, which holds the
machine test lock and supplies an isolated HOME and native-state-off switches:

- Collection: `vitest list src/desk/gl/__tests__/saturnOrbitModel.test.ts
  src/desk/gl/__tests__/saturnOrbitScene.test.ts` — seven named checks collected,
  exit 0; `.tmp/orbital-places/saturn-collect.log`.
- Run: `vitest run` with those same two exact paths — 2 files, 7 tests passed,
  exit 0; `.tmp/orbital-places/saturn-tests.log`.
- Coverage: distinct staggered moon periods/front-back depth; desktop/phone
  camera fit; framebuffer/DPR caps; actual sphere moons and oblate globe;
  translucent depth-tested rings; geometry/cloud/parallax freeze; frozen local
  map refinement; unique-resource disposal and rejected late callbacks.

Root owns actual rendered previews, desktop and phone screenshots, shader
compilation, and graph walk. Mocked renderer unit checks cannot prove pixels or
shader compilation. No build, browser, broad suite, commit or owner-state work
ran in this worker lane.
