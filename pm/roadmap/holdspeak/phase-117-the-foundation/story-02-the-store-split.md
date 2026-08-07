# HS-117-02 — The store split

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

`store.ts` is 1,305 lines with 38 state fields and 62 methods in a
single Zustand `create()` call. Six structurally identical window-type
open/close pairs differ only in key field name and persistence. The
`openPullout` method is a god-method that knows every window type.
Every new feature that touches the store must navigate a monolith.

When this story ships, the store is composed from focused slices in a
`web/src/desk/store/` directory. Each file has a single responsibility
nameable in one phrase. A generic window factory eliminates the
open/close duplication. The `openPullout` dispatch is a data-driven
table. The public `useDesk` API is unchanged — zero consumer edits.

**Articles served:** VIII (native-grade craft — the compositor must be
legible), VI (honest construction — the store must not hide its shape).

## Deliverables

### 1. Create `store/` directory and shared types

Create `web/src/desk/store/types.ts` with: `UnitPos`, `PanelRect`,
`DeskView`, `ZoneViewPref`, `GHOST_LAYOUT_KEYS`,
`COMPACT_LIST_THRESHOLD`, `defaultViewFor`.

### 2. Build the window compositor slice

**Reconciled design (Opus + Terra):** Merge `panelSlice` and the
window-type arrays into one `compositorSlice`. Terra is right that
panel geometry, focus order, minimize/maximize, and the list of open
windows are one compositor concern — splitting them guarantees
cross-slice coordination.

The compositor slice owns:
- `panelRects`, `panelSaved`, `panelOrder`, `panelMin`, `panelMax`
- All six window arrays (pullouts, zoneWindows, infoWindows,
  roadmapWindows, repositoryWindows, workbenchWindows)
- All open/close pairs, focus/present/retire/minimize/restore/maximize
- `resetLayout()`

### 3. Generic window factory for 5 window types

Create `store/windowFactory.ts`. The factory generates open/close
methods for window types with identical structure:

```typescript
interface WindowTypeConfig {
  field: string;       // "zoneWindows"
  singular: string;    // "ZoneWindow"
  key: string;         // "id" | "slug" | "ref"
  panelPrefix: string; // "zone:"
  persistKey?: string; // "hs.desk.zone-windows"
  onOpen?: (id: string, get: () => DeskState) => void;
}
```

Five instances: zoneWindows, infoWindows, roadmapWindows,
repositoryWindows, workbenchWindows. Pullouts stay hand-written
(custom close with optional id, dispatch routing on open).

**Terra amendment:** Do NOT use a raw `Map` for open windows — it
complicates Zustand shallow equality, serialization, and devtools.
Use typed records/arrays as today.

### 4. Refactor `openPullout` to a dispatch table

Create `store/pulloutRoutes.ts`:

```typescript
interface PulloutRoute {
  match: (id: string, get: () => DeskState) => boolean;
  open: (id: string, get: () => DeskState, origin?: Origin) => void;
}

const PULLOUT_ROUTES: PulloutRoute[] = [
  { match: (id) => id.startsWith("roadmap:"),
    open: (id, get, o) => get().openRoadmapWindow(id.slice(8), o) },
  { match: (id, get) => get().items.repository.some(r => r.id === id),
    open: (id, get, o) => get().openRepositoryWindow(id, o) },
  { match: (id, get) => get().items.workbench.some(w => w.id === id),
    open: (id, get, o) => get().openWorkbenchWindow(id, o) },
  { match: (id, get) => id.startsWith("project:") ||
      get().items.project.some(p => p.id === id),
    open: (id, get) => { /* shell.openSurfaceWhenReady */ } },
];
```

The dispatch table is deterministic, ordered, and unit-tested for
ambiguity. Each route is independently testable. Adding a new window
type = adding one entry.

**Terra amendment:** Test every route, collisions, unknown IDs, stale
IDs (items not yet loaded during `refresh`), and fallback behavior.
Routes should return handled/not-handled explicitly.

### 5. Extract remaining slices

- **`dataSlice`**: items, profiles, projects, inferenceTargets, models,
  status, error, loading, updatedAt, setup + refresh, createPrimitive,
  updatePrimitive, deletePrimitive, renameZone, fileIntoDir,
  removeFromDir, fileIntoKnowledge, seedDesk, resetDesk,
  registerRepository.
- **`deskSlice`** (not "uiSlice" — Terra: avoid catch-all naming):
  positions, zoneWidths, divedZone, draggingId, newIds, editingId,
  hoverZoneId, renamingZoneId, selectedIds, askOpen, chatPersonaId,
  toolInspector, viewMode, zoneViewPrefs + all their actions +
  pullout state + openPullout dispatch + closePullout.
- **`recordingSlice`**: recording, recordingExternal, recordingStartedAt
  + 3 actions. The most isolated domain.

**Terra amendment:** Do NOT create a separate `coderSlice` for
`answerCoder`/`speakToCoder`/`runCapability`. These are command-side
effects, not durable state. Keep them in `dataSlice` as API dispatch
methods. Fix the `speakToCoder` duplication (call `answerCoder`
internally).

### 6. Compose into `store/index.ts`

The barrel composes all slices via Zustand's documented slice pattern:

```typescript
export const useDesk = create<DeskState>()((...args) => ({
  ...createCompositorSlice(...args),
  ...createDataSlice(...args),
  ...createDeskSlice(...args),
  ...createRecordingSlice(...args),
}));
```

Re-export all public types. The old `store.ts` becomes a re-export
shim (zero logic). All existing consumer imports work unchanged.

### 7. Characterization tests

**Terra amendment (critical):** Before splitting, add characterization
tests for current behavior:

- `openPullout` routing for every window type
- Panel persistence round-trip (save to localStorage, reload)
- Close/focus ordering (front-most panel, MRU)
- Recording state transitions (idle → recording → busy → idle)
- `resetDesk` sweeps all ghost layout keys
- Async stale-write guard: `refresh()` resolving after an optimistic
  `updatePrimitive` must not restore stale server data
- Timer leakage: `markNew` callbacks must not fire after `resetDesk`
- Duplicate/concurrent action idempotence (double-click open, repeated
  record start/stop)

## Migration steps

**Reconciled cadence (Opus proposed 10, Terra suggested 5):** Use 6
commits:

1. Extract types, persistence helpers, and characterization tests.
2. Extract compositor slice (panel state + window arrays + factory).
3. Extract data slice and recording slice.
4. Extract desk slice with refactored openPullout dispatch.
5. Create barrel, convert old store.ts to shim.
6. Full regression: `npx vitest run` + Playwright screenshot walk.

Each commit must pass `npx tsc --noEmit` and `npx vitest run`.

## What NOT to do

- Do NOT change any consumer imports (components, hooks, tests).
  The shim preserves all paths.
- Do NOT add Zustand middleware (persist, devtools). localStorage
  persistence stays hand-rolled, preserving exact key names and shapes.
- Do NOT use a raw Map for window state.
- Do NOT create a separate coderSlice.

## Test plan

1. All existing store tests pass unchanged.
2. New characterization tests (deliverable 7) pass.
3. New factory + dispatch table tests pass.
4. `npx tsc --noEmit` — zero errors.
5. Playwright screenshot walk at 1440px and 393px.

## Estimated scope

~1,260 lines across 8 files in `store/` (vs. 1,305 in monolith).
Net: slight reduction from deduplication. Plus ~200 lines of new tests.
