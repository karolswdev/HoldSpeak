# Station fidelity build

DRAFT — UNCHECKED — awaiting Muad'Dib. HOLD FOR SHIP.
Worktree: `/Users/karol/dev/tools/wt-night-train-fidelity-20261016`.
Design: [DESIGN.md](DESIGN.md). Root gave canvas GO before product edits and
authorized the subsequent bounded material and practical-light pass.

## Change

Only the new `web/src/desk/gl/interiors/nightTrainStation.ts` and its focused
`web/src/desk/gl/__tests__/nightTrainStation.test.ts` are this worker's product
and test paths. Landscape integration, Journey, Room, Scene and Compartment
belong to the other lanes.

The module exports the settled `createTrainStation(room,parent)` API with
`update(elapsed)` and idempotent `dispose()`. The existing group name is
`Train passing station`, at z=-6. Its x position uses the existing
`trainStationPosition` directly, including initialization at elapsed zero.
There is no timer, listener, app activity, sign, network or image dependency.

The station has an irregular shore footprint extending below the 0.30 m lake
surface. A masonry retaining wall supports the rounded platform, whose deck
is at 0.78 m. A small plaster and stone waiting room has real facade openings,
deep jambs, a pitched roof with gables, eaves, tile courses and a curved ridge
cap. The attached timber canopy has posts and diagonal braces; its slatted
bench has actual legs and back supports.

Three lantern fixtures have dark caps/bases, four metal frame members, low-alpha
glass and small amber cores (about 0.054 × 0.13 m). Two downward warm SpotLights
serve the left and center fixtures. They use full penumbra, five-metre distance,
512 × 512 shadow maps and no extra render pipeline. Relevant opaque station
meshes cast and receive shadows; glass, glowing cores and window backings do
neither. Window panes use a restrained gradient emissive map, a separate front
glass layer and a recessed dark interior rail.

Five shared construction-time canvases, at most 512 px per dimension, supply
quiet plaster/mineral variation, timber grain, roof courses and window depth.
The stone map is shared by shore, retaining blocks, foundation and platform.
Physical UV projection sets the surface scale in metres. Grain, gradients and
small bump relief are static. No textures are allocated or changed per frame.

All direct geometry is merged once into eleven shared-material meshes. The
station group and meshes are marked moving so actual Room batching leaves
their ownership intact. Temporary merge geometry is disposed during build;
the module releases final geometries, materials, textures and light shadow
targets once on teardown. Nothing is registered with `Room.mesh`.

## Focused proof

Root gave TEST GO only for the new station test file. The initial collect/run
passed four tests; logs are `.tmp/night-train-fidelity/station-collect.log` and
`station-run.log` (454 ms). The authorized material/light pass added texture
and shadow ownership checks, followed by this exact final collection and run:

```sh
.venv/bin/python .tmp/night-train-fidelity/locked.py station-polish-collect --web ./node_modules/.bin/vitest list src/desk/gl/__tests__/nightTrainStation.test.ts --maxWorkers=2
.venv/bin/python .tmp/night-train-fidelity/locked.py station-polish-run --web ./node_modules/.bin/vitest run src/desk/gl/__tests__/nightTrainStation.test.ts --maxWorkers=2 --reporter=verbose
```

Both exited 0 under the machine lock with isolated HOME and native state off.
Read both complete final logs; neither has warnings or failures. Actual final
collection output:

```text
src/desk/gl/__tests__/nightTrainStation.test.ts > Night Train lakeside station > builds a supported shore quay, open waiting-room apertures and an actual pitched roof
src/desk/gl/__tests__/nightTrainStation.test.ts > Night Train lakeside station > uses three capped framed lanterns with small amber cores and two bounded shadow spots
src/desk/gl/__tests__/nightTrainStation.test.ts > Night Train lakeside station > shares small construction-time textures at metre scales and keeps glass outside the shadow pass
src/desk/gl/__tests__/nightTrainStation.test.ts > Night Train lakeside station > preserves direct assets through actual Room batching and follows only the authored journey clock
src/desk/gl/__tests__/nightTrainStation.test.ts > Night Train lakeside station > releases its own merged resources once, leaves Room assets alive and ignores updates after disposal
```

Actual final run tail:

```text
 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  21:28:30
   Duration  492ms (transform 62ms, setup 59ms, import 73ms, tests 107ms, environment 176ms)
```

The tests inspect actual constructed Three.js geometry. Rays prove facade
apertures continue to the back wall; geometry bounds/normals prove supported
grade and roof pitch. They check fixture/core scale, light bounds, texture
sharing, actual `Room.finish` batching, unchanged vertices under travel, and
single disposal of resources including allocated shadow targets. Only canvas
painting is doubled; no WebGL renderer or hub runs in this worker lane.

Own-path `git diff --check` exited 0. No build, browser, broad suite, stage or
commit command was run. Root owns actual station frames at 160/166/172 seconds,
phone/desktop composition, shadow cost, texture quality, preview, integration,
quick check and delivery. Root supplied the first actual station crop; this
worker read `edge-v1/full-1440-166.png` and `edge-v1/station.png` before the
material pass. Unit checks cannot establish the final pixels or their beauty.

Integration note: the landscape unit fixture must supply the bounded 2D canvas
methods used by these construction-time textures. This worker changed none of
the other lanes' fixtures. HOLD FOR SHIP.
