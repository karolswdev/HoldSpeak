# Jupiter orbit — catalog integration

Status: built; 17 focused tests passed. HOLD FOR SHIP.

Worktree: `/Users/karol/dev/tools/wt-jupiter-orbit-20261015`.
Design: [DESIGN.md](DESIGN.md). Root gave canvas-read GO after reading 1440 and
393 renders. Tuesday: the owner can choose the world in the existing Wallpaper
collection, then return to work.

## Change

- `web/src/desk/gl/atmosphereRegistry.ts`: adds `jupiter-orbit` immediately
  before Quiet Desk, named `In Jupiter's orbit`, seed `0x4a555049`, local
  `desk/atmospheres/jupiter-orbit.webp` preview and lazy
  `createJupiterOrbitScene` factory. The scene owns its visual grade.
- Registry tests cover the new metadata, saved-ID recognition, preserved
  catalog order, scenic inclusion and Quiet Desk exclusion.
- The actual `WallpaperModule` test selects Jupiter, retains the stored motion
  choice, writes no sound preference, and restores Jupiter on reopening. The
  existing keyboard test reaches Jupiter immediately before Quiet Desk.
- The host test keeps the real Jupiter registry entry and lazy import. Only
  the scene factory, runtime and existing activity/control boundaries are
  doubles. It starts on Quiet Desk, proves the module has not loaded, selects
  Jupiter, checks its factory/seed/paused-motion mount and checks disposal.

No default, existing saved choice, Settings implementation, shared runtime,
Screen, motion/sound API or persistence change. The new unique grade class has
no additional CSS overlay; lighting and grading remain in the scene.

## Focused proof

Commands, run from the worktree root in this order:

```sh
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-collect --web ./node_modules/.bin/vitest list src/desk/gl/__tests__/atmosphereRegistry.test.ts src/pages/cores/__tests__/settingsWallpaper.test.tsx src/desk/gl/__tests__/Atmosphere.test.tsx --maxWorkers=2
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-run --web ./node_modules/.bin/vitest run src/desk/gl/__tests__/atmosphereRegistry.test.ts src/pages/cores/__tests__/settingsWallpaper.test.tsx src/desk/gl/__tests__/Atmosphere.test.tsx --maxWorkers=2 --reporter=verbose
```

Both exited 0. The wrapper holds the machine test lock and sets/removes an
isolated HOME. Read the complete logs after the runs:
`.tmp/jupiter-orbit/integration-collect.log` and
`.tmp/jupiter-orbit/integration-run.log`. No warnings or failures in either.

Actual collection output (17 tests):

```text
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads one registered decorative scene and releases its runtime
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > selects the quiet Desk without allocating a WebGL canvas
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads Jupiter through its real registry entry only when selected
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > releases the active scene when a live selection disables it
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > gives the next renderer a new canvas after disposal loses the old context
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > keeps a failed load unready and releases activity immediately
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > keeps a failed mount unready and releases activity immediately
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > cancels a pending scene when a new place wins and ignores its late completion
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > cancels a pending import on unmount without mounting or announcing readiness
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > remounts with the explicit motion choice and reports loading again
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > shows catalog previews and persists the live selection
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > selects Jupiter from the collection and restores it on reopening
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > lets the keyboard select the whole collection from one tab stop
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > pauses and resumes wallpaper motion with the stored control and keeps sound opt-in
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > reads a motion preference changed by another settings surface
src/desk/gl/__tests__/atmosphereRegistry.test.ts > atmosphere registry > publishes lazy personalization metadata and a safe fallback
src/desk/gl/__tests__/atmosphereRegistry.test.ts > atmosphere registry > includes every authored world in one scenic collection
```

Actual run tail:

```text
 Test Files  3 passed (3)
      Tests  17 passed (17)
   Start at  20:56:52
   Duration  1.91s (transform 575ms, setup 189ms, import 798ms, tests 926ms, environment 569ms)
```

Own-path `git diff --check` also exited 0.

## Limits

Worker verification covers catalog metadata, real picker behavior and the
host's lazy boundary. It does not exercise Three.js rendering. Root owns the
actual scene still, 1440/393 observations, build/typecheck, quick check and
deployment. No build, install, browser or full-suite command was run here.
No stage or commit. HOLD FOR SHIP.

## Scope amendment — existing collection tests

Root authorized two additional test files after the complete quick check
reported six failures in `.tmp/jupiter-orbit/quick-final/vitest.log`:

- `web/src/design/AtmospherePreview.test.tsx`: first collection size, last
  world on wrap, Quiet Desk fallback count and unknown-link fallback count.
- `web/src/pages/cores/__tests__/ChangePlacesCore.test.tsx`: full catalog size
  and return to All places after an empty Favorites filter.

Classification (a): these tests asserted the old fixed collection count and
last item. A natural run of the unchanged two files reproduced all six reds.
The amendment changes only these two test files and appends this record.

Preview tests now compare rendered IDs/order to `SCENIC_ATMOSPHERES`, derive
the displayed total and first/last wrap from that collection, assert Jupiter
is present, and cover direct links for every scenic world, including Jupiter.
Change places compares rendered IDs/order to `ATMOSPHERES` and asserts Jupiter
both initially and after All places restores the collection. Existing checks
for explicit preference selection, no preview selection before Use, no View
on Floor action, favorites, keyboard focus, the settle flag, the sound
preference and refused storage writes remain. No product face, guard ceiling
or other test changed in this amendment.

Exact commands, in order, under the same lock and isolated-HOME helper:

```sh
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-fallout-collect-before --web ./node_modules/.bin/vitest list src/design/AtmospherePreview.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx --maxWorkers=2
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-fallout-red --web ./node_modules/.bin/vitest run src/design/AtmospherePreview.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx --maxWorkers=2 --reporter=verbose
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-fallout-collect --web ./node_modules/.bin/vitest list src/design/AtmospherePreview.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx --maxWorkers=2
.venv/bin/python .tmp/jupiter-orbit/locked.py integration-fallout-green --web ./node_modules/.bin/vitest run src/design/AtmospherePreview.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx --maxWorkers=2 --reporter=verbose
```

The first collection exited 0 and listed 15 tests. The unchanged run exited 1;
actual red tail from `.tmp/jupiter-orbit/integration-fallout-red.log`:

```text
 Test Files  2 failed (2)
      Tests  6 failed | 9 passed (15)
   Start at  21:30:41
   Duration  1.60s (transform 660ms, setup 120ms, import 930ms, tests 946ms, environment 381ms)
```

Updated collection exited 0. Full output from
`.tmp/jupiter-orbit/integration-fallout-collect.log` (21 tests):

```text
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > shows the complete catalog without changing the current work surface
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > favorites never switch the room and the filter retains keyboard entry
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > loads favorites on reopen and synchronizes a different tab
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > retains keyboard focus when removing the last filtered favorite
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > restores the complete catalog after an empty Favorites filter
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > settles without implicitly turning on motion, sound or capture
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > ignores malformed, duplicate and removed favorites
src/pages/cores/__tests__/ChangePlacesCore.test.tsx > Change places > keeps favorites usable when storage writes are refused
src/design/AtmospherePreview.test.tsx > the complete night collection > opens at the first scenic world and exposes the complete collection
src/design/AtmospherePreview.test.tsx > the complete night collection > wraps from the first scenic world to the last and back
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to rainy-city
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to lantern-garden
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to radio-station
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to midnight-archive
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to night-train
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to deep-sea
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to greenhouse
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to laundromat
src/design/AtmospherePreview.test.tsx > the complete night collection > honors a direct link to jupiter-orbit
src/design/AtmospherePreview.test.tsx > the complete night collection > falls back to the first scenic world for #quiet-desk
src/design/AtmospherePreview.test.tsx > the complete night collection > falls back to the first scenic world for #missing
```

Updated run exited 0. Actual green tail from
`.tmp/jupiter-orbit/integration-fallout-green.log`:

```text
 Test Files  2 passed (2)
      Tests  21 passed (21)
   Start at  21:31:37
   Duration  1.73s (transform 666ms, setup 128ms, import 944ms, tests 1.23s, environment 376ms)
```

Read both complete updated logs; no warnings or failures. Own-path
`git diff --check` exited 0. Root reruns the complete quick check. No build,
browser, full-suite, stage or commit command was run here. HOLD FOR SHIP.
