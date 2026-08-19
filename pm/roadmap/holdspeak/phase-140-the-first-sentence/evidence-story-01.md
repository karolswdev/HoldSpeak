# HS-140-01 evidence — One obvious door

**Date:** 2026-08-18
**Result:** done; Terra final verdict RATIFY

## Shipped behavior

- `DeskApp` holds a neutral, retryable no-chrome state until setup status is
  known. A rejected request or settled `setup === null` cannot fall through to
  the normal Chair.
- `arrival_required` forces the Chair even when a stale browser preference says
  Floor, and suppresses DeskChrome, lanes, dock, launchers, pullouts, and
  advanced windows.
- `ChairHome` mounts the existing `FirstWords`; there is no second capture or
  onboarding implementation.
- `SurfaceWindows` recovery mode clears stale persisted windows and registers
  only Setup. Normal window state cannot leak into first value.
- Healthy idle/success states expose no Setup or model-routing action. Setup
  appears only for a failure contract that requires it.
- Continue later cannot locally reveal the Chair; refreshed server setup state
  is the only exit authority.

## Local verification

From `web/` with Node 22.21.0:

```text
npx vitest run src/desk/components/FirstWords.test.tsx src/desk/chair/ChairHome.test.tsx src/desk/DeskApp.test.tsx src/desk/__tests__/surface-windows.test.tsx --maxWorkers=2

Test Files  4 passed (4)
Tests       24 passed (24)
```

`npm run build` passed after 1,479 modules transformed. Vite emitted only the
existing dynamic/static-import and large-chunk warnings. `git diff --check`
passed.

## Fresh-HOME visual acceptance

The worker launched `holdspeak web --no-open` under a new `mktemp -d` HOME and
captured the real loopback runtime with Puppeteer. At both widths the heading
and speak control are above fold; there is no DeskChrome, dock, Chair lane,
hero, advanced window, horizontal overflow, console error, or page error.

- [1440×900](./assets/story-01/first-value-chair-1440x900.png)
- [393×900](./assets/story-01/first-value-chair-393x900.png)

The orchestrator visually inspected both captures.

## Counsel trail

The initial implementation was amended until all named issues closed:

1. no full-Chair first-paint before setup resolution;
2. no healthy Setup or post-success Models escape;
3. no local `continued` race before server refresh;
4. stale advanced windows cleared from state and local storage;
5. setup refresh failures and `setup === null` remain quiet and retryable.

Final read-only Terra verdict: **RATIFY**.
