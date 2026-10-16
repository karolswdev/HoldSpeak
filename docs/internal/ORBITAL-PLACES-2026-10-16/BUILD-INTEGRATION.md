# Mars and Saturn — catalog integration

Status: built; 21 focused tests passed. HOLD FOR SHIP.

Worktree: `/Users/karol/dev/tools/wt-orbital-places-20261016`.
Design: [DESIGN.md](DESIGN.md). Root read all four paired library canvas shots
and sent GO before registration. Tuesday: the owner can choose either world in
the existing Wallpaper collection, then return to work.

## Scope

The integration uses the existing catalog, preference and host boundaries.
Mars and Saturn follow Jupiter, before Quiet Desk. The entries use
`mars-orbit` / `In Mars' orbit` / seed `0x4d415253` and `saturn-orbit` /
`In Saturn's orbit` / seed `0x53415455`, each with its local rendered preview
and lazy scene factory.

The existing generic grade element (`web/src/desk/desk.css:40`) is transparent.
Jupiter has no specific grade rule. The new orbit scenes own their lighting
and color in the same way, without an additional CSS overlay.

Focused tests cover metadata, catalog order, scenic inclusion, actual picker
selection and restore, keyboard selection and real registry lazy imports.
The picker retains Motion off and writes no Sound preference. Host coverage
checks each selected factory, seed, paused-motion mount, grade and disposal.
Scene factories, runtime and existing activity/control boundaries are doubles;
the orbit catalog entries and imports are real.

## Focused proof

Commands, run from the worktree root in this order, collected and then ran
only these three existing test files:

```sh
.venv/bin/python .tmp/orbital-places/locked.py integration-collect --web ./node_modules/.bin/vitest list src/desk/gl/__tests__/atmosphereRegistry.test.ts src/pages/cores/__tests__/settingsWallpaper.test.tsx src/desk/gl/__tests__/Atmosphere.test.tsx --maxWorkers=2
.venv/bin/python .tmp/orbital-places/locked.py integration-run --web ./node_modules/.bin/vitest run src/desk/gl/__tests__/atmosphereRegistry.test.ts src/pages/cores/__tests__/settingsWallpaper.test.tsx src/desk/gl/__tests__/Atmosphere.test.tsx --maxWorkers=2 --reporter=verbose
```

The wrapper holds the machine test lock, disables native state reads, and
sets/removes an isolated HOME. Both commands exited 0. Read both complete
logs: `.tmp/orbital-places/integration-collect.log` and
`.tmp/orbital-places/integration-run.log`. Each run waited for the machine
lock; neither log contains warnings or failures.


Actual collection output (21 tests):

```text
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > shows catalog previews and persists the live selection
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > selects 'Jupiter' from the collection and restores it on reopening
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > selects 'Mars' from the collection and restores it on reopening
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > selects 'Saturn' from the collection and restores it on reopening
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > lets the keyboard select the whole collection from one tab stop
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > pauses and resumes wallpaper motion with the stored control and keeps sound opt-in
src/pages/cores/__tests__/settingsWallpaper.test.tsx > Settings wallpaper picker > reads a motion preference changed by another settings surface
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads one registered decorative scene and releases its runtime
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > selects the quiet Desk without allocating a WebGL canvas
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads 'Jupiter' through its real registry entry only when selected
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads 'Mars' through its real registry entry only when selected
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > loads 'Saturn' through its real registry entry only when selected
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > releases the active scene when a live selection disables it
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > gives the next renderer a new canvas after disposal loses the old context
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > keeps a failed load unready and releases activity immediately
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > keeps a failed mount unready and releases activity immediately
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > cancels a pending scene when a new place wins and ignores its late completion
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > cancels a pending import on unmount without mounting or announcing readiness
src/desk/gl/__tests__/Atmosphere.test.tsx > Desk atmosphere host > remounts with the explicit motion choice and reports loading again
src/desk/gl/__tests__/atmosphereRegistry.test.ts > atmosphere registry > publishes lazy personalization metadata and a safe fallback
src/desk/gl/__tests__/atmosphereRegistry.test.ts > atmosphere registry > includes every authored world in one scenic collection
```

Actual run tail:

```text
 Test Files  3 passed (3)
      Tests  21 passed (21)
   Start at  16:56:17
   Duration  2.49s (transform 557ms, setup 176ms, import 802ms, tests 1.50s, environment 577ms)
```

Own-path `git diff --check` also exited 0.

## Limits

Worker verification covers catalog metadata, picker behavior and the host's
lazy boundary. Root owns actual rendered previews, Three.js observations,
1440/393 shots, build, quick check and deployment. No build, install, browser,
full-suite, stage or commit command was run here. HOLD FOR SHIP.
