# Live background build

HOLD FOR SHIP — root verification pending. Base bea522beb; worktree
wt-desk-drawers-live-20261015. Owner reversal: 2026-10-15, “then change them?”
Tenets 3/5/6; Constitution Articles I/II/VIII. Tuesday: choose a live place,
pause it from Wallpaper settings, and keep using Desk objects.

## Result

The current Screen mounts the existing registered Atmosphere before its
content. The selected still remains during load or failure; a successful
runtime mount and first render remove the still. Quiet Desk mounts no host,
canvas, scene or activity observer. The Screen callback is stable for each
place; cancelled lazy imports cannot announce readiness for a later place.

The host reports loading, ready or failed in `data-atmosphere-state`, releases
its activity observer immediately on import or mount failure, and releases it
once on subsequent unmount. Place and motion changes reset readiness in a
layout effect before paint and use a new canvas after the old renderer is
disposed. The shared scene runtime and individual scene modules are unchanged.

Scoped Screen CSS keeps the scene fixed to the Screen's inherited work-area
insets, below the icons in the Screen's stacking context. It stays transparent
until ready and has no pointer ownership. `object-fit: cover` retains the
existing viewport scene aspect ratio when filling the smaller work area.

Wallpaper now exposes the existing Motion preference through GadgetRow and
CheckGadget after its choice grid. Its accessible name is “Wallpaper motion”.
The preference persists in the existing key. Sound remains opt-in with no new
sound control or microphone access.

## Focused proof

All commands used root's isolated-HOME wrapper and machine test lock:

```text
.venv/bin/python .tmp/desk-drawers-live/locked.py LABEL --web \
  ./node_modules/.bin/vitest list|run --maxWorkers=2 \
  src/desk/gl/__tests__/Atmosphere.test.tsx \
  src/desk/gl/__tests__/atmosphereRuntime.test.ts \
  src/desk/gl/__tests__/atmosphereRegistry.test.ts \
  src/desk/screen/__tests__/screenAtmosphere.test.tsx \
  src/pages/cores/__tests__/settingsWallpaper.test.tsx
```

Read collection: `.tmp/desk-drawers-live/background-collect-red-five.log`,
25 tests listed. Read baseline run:
`.tmp/desk-drawers-live/background-red.log`, 13 failed / 12 passed in five
files. Missing live host, readiness state and Motion checkbox reproduced.
The initial rapid-selection test helper only wrote storage; the final test
presses the real Settings radio, which emits the existing same-tab event.

Read first green run: `.tmp/desk-drawers-live/background-green.log`, 25 passed.
Root's type check then caught an overloaded `getContext` return type in the
test measurement stub. The stub now has the canvas method's overloaded type
and answers only 2D measurement requests. Read final exact-scope rerun:
`.tmp/desk-drawers-live/background-green-types.log`:

```text
Test Files  5 passed (5)
     Tests  25 passed (25)
  Duration  2.38s
```

Coverage includes selected-only lazy loading on both compact modes, one
canvas, no host for Quiet, selection changes from real Wallpaper radios,
still retention on import and mount failure, activity cleanup once, late
import cancellation, Motion checkbox to runtime remount, object selection
and clear, system reduced motion, passive pointer registration, visibility
suspension and frozen-scene activity updates. Default sound allocates no
AudioContext. Screen tests mock runtime and passive activity; the canvas
measurement stub is for DeskIcon text measurement, not a GPU claim.

`git diff --check` was clean after these changes. No build, browser, install,
stage or commit was run by this lane. The folder lane owns the old still-only
Screen test and was sent the new readiness contract.

## Limits and debt

Root owns actual moving pixels, registered-scene checks, 1440/393 shots,
real pointer ownership and visual comparison. These are not proved by this
lane's jsdom tests.

Existing runtime limitation: if an authored scene throws during resize or
first render after runtime listeners are registered, `mountAtmosphereScene`
cannot return its cleanup. The host now releases its own activity observer;
cleanup inside a partially mounted runtime is unchanged and was reported to
root. The mocked WebGL failure proves the host fallback and observer cleanup,
not disposal of a partially constructed real Three.js renderer.
