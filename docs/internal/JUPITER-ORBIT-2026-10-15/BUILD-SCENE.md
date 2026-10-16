# Jupiter scene — worker record

Built in `/Users/karol/dev/tools/wt-jupiter-orbit-20261015` after root's
canvas-read GO for `.tmp/jupiter-orbit/canvas/direction-1440.png` and
`direction-393.png`. HOLD FOR SHIP; no stage or commit.

## Changed files

- `web/src/desk/gl/jupiterOrbitScene.ts`: Atmosphere factory, NASA sphere map,
  procedural first paint, solar terminator, thin illuminated atmospheric limb,
  bounded stars/dust, four separate shader-surfaced moon meshes, geometric
  transit shadows, tiny pointer parallax, Pioneer/Voyager/monolith meshes.
- `web/src/desk/gl/jupiterOrbitModel.ts`: independent seeded layout RNG, moon
  trajectories, render bounds, pure rare-encounter scheduling/state helpers.
- `web/src/desk/gl/__tests__/jupiterOrbitModel.test.ts`: eight focused tests.
- `web/src/desk/gl/__tests__/jupiterOrbitScene.test.ts`: five lifecycle/resource
  tests using real Three geometry and a mocked WebGL renderer/image completion.

NASA texture, registry, host, Screen, persistence, and all other worker paths
remain root/integration owned.

## Behavior and observation hooks

`createJupiterOrbitScene(context)` follows `AtmosphereScene`. The host's elapsed
seconds drive all movement. Reduced motion freezes geometry; local image
completion still renders. A failed map retains the procedural sphere. Disposal
is idempotent, clears image callbacks/source, drops its texture image reference,
and releases each owned geometry/material/texture and renderer once. A captured
late callback checks disposal before touching the renderer.

`JUPITER_MOONS`, `jupiterMoonPosition(index, elapsed)` and
`jupiterEncounterForWindow(seed, sessionSalt, windowIndex)` support explicit
accelerated observations. `jupiterEncounterAtTime` combines the pure schedule
with its state; `jupiterEncounterState` advances an already selected event.
The live scene caches its selection once per ten-minute window and reads crypto
only at construction. Window zero is empty. The cumulative choice bands are
2% Pioneer, 1% Voyager, 0.2% monolith; each eligible window contains at most one
45–75 second pass. The reflected point is attached to the craft, never the frame.

Scene object names: `Jupiter system`, `Jupiter`, `Jupiter atmosphere`, `Io`,
`Europa`, `Ganymede`, `Callisto`, `Jupiter pioneer`, `Jupiter voyager`,
`Jupiter monolith`. Only Io is in front initially; the other three start behind
Jupiter. Orbit periods are authored 160/240/360/480 seconds. Planet/cloud rotation
is much slower. Geometry provides depth occlusion; there are no orbit lines.

## Initial focused proof

Commands ran through the root-provided helper and machine lock, with isolated
HOME. No browser, build, install, or broad suite was run by this worker.

Collection:

```text
.venv/bin/python .tmp/jupiter-orbit/locked.py scene-collect --web \
  ./node_modules/.bin/vitest list \
  src/desk/gl/__tests__/jupiterOrbitModel.test.ts \
  src/desk/gl/__tests__/jupiterOrbitScene.test.ts --maxWorkers=1
exit 0
11 tests collected across the two named files
log: .tmp/jupiter-orbit/scene-collect.log
```

Actual run:

```text
.venv/bin/python .tmp/jupiter-orbit/locked.py scene-run --web \
  ./node_modules/.bin/vitest run \
  src/desk/gl/__tests__/jupiterOrbitModel.test.ts \
  src/desk/gl/__tests__/jupiterOrbitScene.test.ts --maxWorkers=1 --reporter=verbose
Test Files  2 passed (2)
     Tests  11 passed (11)
  Duration  878ms
exit 0
log: .tmp/jupiter-orbit/scene-run.log
```

The model tests cover initial occlusion positions, each full orbit/front/back
pass, deterministic layout, render bounds, ten-minute exclusion, rarity over
100,000 deterministic windows, session variation, event boundaries, and glint
duration. Lifecycle tests cover actual separate sphere geometry, absent initial
visitors, frozen load refinement, pause/resume, texture failure, and exactly-once
resource disposal including a captured late image callback.

## Limits

GPU shader compilation, visual quality at 1440/393, map orientation, live host
selection/motion behavior, all moon transits and each visitor silhouette still
need root's real renderer observations. Tests do not claim visual correctness.
Timing, scale, moon surfaces, and visitor trajectories are cinematic. The moon
surfaces are procedural visual interpretations; only Jupiter uses a NASA map.

## Owner amendment — richer universe and moving cloud streams

After seeing the original live render, the owner asked for visible stars and
slow cloud convection. Root's revised NASA-star-map canvas at 1440/393
(`.tmp/jupiter-orbit/canvas-rich-sky`) received canvas-read GO before this
amendment. Product source is now frozen and HOLD FOR SHIP again.

The sky now uses root's local `jupiter-starfield.jpg` through a spherical
direction lookup toward the galactic plane, excluding stretched atlas poles.
A diagonal Milky Way has dark dust lanes and subdued blue/gold structure.
18,000 seeded point stars add varied brightness, warm/cool color, real depth,
a concentrated galactic population, and a sparse bright tier. This replaces
the original 2,300 mostly subpixel points. Sky object names are `Jupiter stars`
and `Jupiter galactic sky`.

The planet's `uCloudTime` advances from inherited runtime elapsed seconds.
Opposing latitude jets displace NASA cloud detail at different rates. Paired
local eddies and a Great Red Spot vortex vary cloud structure within the bands.
The numeric flow constants are exported as `JUPITER_CLOUD_FLOW`; the matching
pure `jupiterZonalDisplacement(latitude, elapsed)` supports bounds checks.
Jet displacement remains bounded, storm rotation stays local, and eddy offsets
stay bounded, so hours of use cause no growing shear or abrupt timeline resets.
This is authored analytic animation, not a physical weather simulation.

Both local map loads refine a frozen frame and retain procedural scenery on
error. Both captured late callbacks are covered by disposal tests; three owned
textures are disposed once. Frame updates reuse the moon coordinate buffer and
visitor list and compute encounter progress as numbers; no new frame arrays or
state objects were added.

### Amended focused proof

The exact same two test files were collected again, then run under the machine
lock and isolated HOME:

```text
.venv/bin/python .tmp/jupiter-orbit/locked.py scene-rich-collect --web \
  ./node_modules/.bin/vitest list \
  src/desk/gl/__tests__/jupiterOrbitModel.test.ts \
  src/desk/gl/__tests__/jupiterOrbitScene.test.ts --maxWorkers=1
exit 0
13 tests collected across the two named files
log: .tmp/jupiter-orbit/scene-rich-collect.log

.venv/bin/python .tmp/jupiter-orbit/locked.py scene-rich-run-final --web \
  ./node_modules/.bin/vitest run \
  src/desk/gl/__tests__/jupiterOrbitModel.test.ts \
  src/desk/gl/__tests__/jupiterOrbitScene.test.ts --maxWorkers=1 --reporter=verbose
Test Files  2 passed (2)
     Tests  13 passed (13)
  Duration  880ms
exit 0
log: .tmp/jupiter-orbit/scene-rich-run-final.log
```

The first amended run had 12 passes and one test failure: strict `toBe(0)`
distinguished mathematical `-0` from `0` in the new jet assertion. The assertion
now compares the numeric value with `toBeCloseTo(0)`; the final run above passed.
New proof covers opposing/bounded zonal movement through 100 million elapsed
seconds, pause/resume of the actual cloud uniform, both frozen map completions,
rich star geometry/depth/bright-tier counts, both map errors, and both late
callbacks with exactly-once texture release.

Root owns new shader/visual observations, preview generation, build, production
selection/motion checks, and the quick check. The original production bundle
does not verify this amendment. This worker ran no browser/build/install or
broader suite.
