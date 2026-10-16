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
