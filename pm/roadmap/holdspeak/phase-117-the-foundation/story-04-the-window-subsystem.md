# HS-117-04 — The window subsystem

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

`DeskWindow.tsx` is 1,766 lines containing seven distinct subsystems:
a placement engine, edge-snap geometry, a drag/resize physics hook,
a window registry with pub/sub, an expose overlay, a dock toolbar,
and the window chrome component itself. Module-level mutable Maps
(`chipEls`, `shellEls`, `windowRegistry`, `launcherRegistry`) couple
these subsystems through shared global state. Adding a new window
verb means reading the entire file.

When this story ships, `DeskWindow.tsx` is decomposed into focused
modules under `web/src/desk/components/window/`. Each module has a
single responsibility nameable in one phrase. The public API surface
(`DeskWindowFrame`, `Dock`, `useDeskWindow`) is unchanged — zero
consumer edits.

**Articles served:** VIII (native-grade craft — the window manager
must be legible), VI (honest construction — each subsystem must own
its file).

## Deliverables

### 1. Create `window/` directory and extract pure geometry

Create `web/src/desk/components/window/windowGeometry.ts` with the
pure functions that have zero React or module-state dependencies:

- `workBand()` (lines 43-57) — CSS custom property reader
- `placeWindow()` (lines 64-120) — initial placement with occlusion scoring
- `clampIntoBand()` (lines 125-138) — viewport clamping
- `snapForPointer()` (lines 143-175) — edge/corner tiling
- `resizeEdge()` (lines 180-200) — multi-edge resize math
- `clampRect()` (lines 272-281) — general rect bounding
- `exposeLayout()` (lines 241-270) — N-cell grid layout
- `mruOrder()` (lines 1479-1481) — MRU sort

~140 lines. All functions are already pure and exported. Move, add
re-exports from `DeskWindow.tsx` if any external consumer imports
them directly.

### 2. Extract the window registry

Create `web/src/desk/components/window/windowRegistry.ts`:

- Module-level Maps: `chipEls`, `shellEls`, `windowRegistry` (lines 669-931)
- Pub/sub: `publishRegistry`, `registrySnapshot`, `registryListeners`
- Hooks: `useOpenWindows()` (lines 955-963)
- Imperative functions: `announceWindow`, `retractWindow`,
  `frontWindowId`, `openWindowCount` (lines 933-984)
- Window verbs: `closeFrontWindow`, `minimizeFrontWindow`,
  `cycleWindows`, `focusOrRestoreApp` (lines 987-1021)

~120 lines. The registry owns the shared Maps; consumers import
from this module instead of reaching into DeskWindow.tsx.

### 3. Extract the launcher registry

Create `web/src/desk/components/window/launcherRegistry.ts`:

- `launcherRegistry`, `launcherSnapshot`, `launcherListeners` (lines 884-886)
- `publishLaunchers`, `announceLauncher`, `retractLauncher`,
  `activateLauncher` (lines 887-908)
- `useLaunchers()` hook (lines 909-917)

~50 lines. Fully self-contained pub/sub — no dependencies on the
window registry.

### 4. Extract overlay components and the dock

- `window/SnapGhost.tsx` (~35 lines): ghost pub/sub + component (lines 203-237).
- `window/Switcher.tsx` (~50 lines): switcher state + component (lines 686-735).
- `window/Expose.tsx` (~130 lines): expose toggle, WAAPI fan, component (lines 740-866).
- `window/VerbGlyph.tsx` (~30 lines): SVG path map (lines 1083-1112).
- `window/ShortcutSheet.tsx` (~46 lines): keyboard overlay portal (lines 1710-1766).
- `window/Dock.tsx` (~220 lines): dock toolbar (lines 1486-1708).

### 5. Slim down `DeskWindow.tsx`

After extraction, `DeskWindow.tsx` retains the `useDeskWindow` hook
(~330 lines) and `DeskWindowFrame` component (~360 lines) plus
re-exports. Target: 1,766 to ~750 lines.

## What NOT to do

- Do NOT change any public API. Zero consumer edits.
- Do NOT refactor `useDeskWindow` hook internals or extract WAAPI
  animation logic from `DeskWindowFrame` (too many local refs).
- Do NOT introduce a React context for the registries. Module-level
  Maps are faster and already work.

## Test plan

1. `npx tsc --noEmit` — zero type errors.
2. `npx vitest run` — all existing web tests pass.
3. Playwright screenshot walk at 1440px and 393px — windows open,
   drag, resize, snap, minimize, maximize, expose, dock chips, and
   shortcut sheet all render identically.
4. Verify every external import of `DeskWindow.tsx` exports still
   resolves: `grep -rn "from.*DeskWindow" web/src/`.
5. `uv run pytest -q` — backend tests unaffected.

## Estimated scope

~0 net lines (pure decomposition). 8 new files under `window/`.
`DeskWindow.tsx` drops from 1,766 to ~750 lines. Each extracted
module is independently readable and testable.
