# Night Train compartment worker

DRAFT — HOLD FOR SHIP. Worker lane in `wt-night-train-20261016`, based on
`2245fc36b`. Root issued canvas GO after reading the paired composition study.
The owner judges the actual rendered scene. Tuesday: a calm, tactile place behind
Desk work, with readable passing scenery and no new controls.

## Built

The existing scene now wraps Room's renderer/composer around a metre-scale
compartment. It has walnut walls and table, curved emerald upholstery, restrained
piping/tufts, folded curtains, deep window reveals and brass trim. A 0.38 m warm
practical lamp groups with a glazed cup and partly open book below the window.
Fine rain sits close to the glass. Material bump scales match the small cabin.
No signs, recording indicators, activity signals or additional UI were added.

The window is a real Three.js Reflector with a 512 × 320 target and no MSAA,
blended with a low-alpha Fresnel shader. Its moving marker protects it from
Room batching. Local ownership follows the installed addon API:
`Reflector.dispose()` releases its render target and material; the helper then
releases its geometry. Those resources are never registered with Room.

The scene consumes the landscape lane's exact `createTrainLandscape(room)`
contract. The world and rain state are initialized at elapsed 0. The wrapper
blocks all update work while motion is off or reduced, including landscape,
rain, camera vibration and pointer parallax. It restores the responsive seated
camera after every Room update, resize and motion setting change. Disposal is
idempotent, removes the local reflection and landscape, then releases Room.

Product paths: `interiors/nightTrainScene.ts`, `nightTrainCompartment.ts`,
`nightTrainGlass.ts`; focused check: `gl/__tests__/nightTrainScene.test.ts`.
Shared Room, other scenes, host, registry, sound and landscape files are untouched
by this lane. No build, browser, staging or commit ran here.

## Actual capture refinement

Root rejected the first actual pair: the near seat hid too much of the desktop,
the window was too small, and long rain strokes looked coarse. The second pass
moves the desktop camera to `[-0.50, 1.15, 0.65]` toward
`[0.03, 1.30, -1.30]`, with a separate portrait camera at
`[-0.40, 1.15, 0.98]` toward `[0.10, 1.25, -1.30]`. The curved seat moves farther
left and outward. Table and props retain their metre dimensions.

Rain now uses a train-local shader plane with millimetre beads and rare short
trails, capped at 0.10/0.055 alpha. Its time uniform shares the wrapper's freeze.
Walnut has custom fine curved grain and pores. Lower ambient/environment/cool
fill lets the slightly stronger warm practical pool define the book and table.
The actual reflection and resource ownership remain the same.

Second-pass focused checks ran under the same locked isolated helper:

- `.tmp/night-train/compartment-v2-collect.log`: same exact file, four named
  checks collected, exit 0.
- `.tmp/night-train/compartment-v2-run.log`: `vitest run --maxWorkers=2` on that
  exact file, 1 file / 4 tests passed, 502 ms, exit 0.

The freeze check now inspects the actual droplet shader time uniform. Root's
second actual pair remains the visual authority; renderer/composer unit mocks
cannot prove the resulting pixels.

## Final bounded capture corrections

Root accepted the second pair's stronger depth/window/material direction, then
requested two final adjustments. The train-local camera far plane is now 400 m
so the oblique wide sky at z=-118 stays inside the frustum. Reflector copies that
camera far plane through its installed addon render hook. The seat shoulder
moves 0.14 m back toward the frame to `[-0.88, 0.49, 0.25]`, retaining yaw
-0.12; the cup moves inward as a group to `[0.20, 0.80, -0.54]` to improve
portrait fit without changing its size.
Root owns the final actual pair and frame performance observation.

Final focused proof, under the same shared lock and isolated HOME:

- `.tmp/night-train/compartment-final-v3-collect.log`: four checks collected,
  exit 0.
- `.tmp/night-train/compartment-final-v3-run.log`: 1 exact file / 4 tests passed,
  482 ms, exit 0. The reflection/scale check also asserts camera.far=400.

Owned product and test files are frozen after that run. No broader check, build,
browser run, stage or commit was performed by this worker.

## Checks — first pass

Root issued test GO. The supplied `.tmp/night-train/locked.py` held the shared
machine test lock and supplied an isolated HOME/native-state-off environment.

- Collection: `vitest list src/desk/gl/__tests__/nightTrainScene.test.ts` — four
  named checks, exit 0; `.tmp/night-train/compartment-collect.log`.
- Run: `vitest run --maxWorkers=2 src/desk/gl/__tests__/nightTrainScene.test.ts` —
  1 file, 4 tests passed, 523 ms, exit 0; `.tmp/night-train/compartment-run.log`.
Checks cover actual Reflector survival through the real Room batching pass,
bounded reflection target and physical table size, initialized/frozen still
state, scenery/rain/parallax/vibration pause, camera framing after resize and base
updates, and exactly-once reflection/Room disposal with no later scene work.
Renderer/composer are mocked; root owns shader compilation, material and visual
judgement, actual paired captures, previews and live Desk observations.
