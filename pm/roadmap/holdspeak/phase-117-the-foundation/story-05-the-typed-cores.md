# HS-117-05 — The typed cores

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01
- **Unblocks:** HS-117-07
- **Owner:** unassigned

## The thesis (the bar)

The 16 core page components under `web/src/pages/cores/` are the
full-page surfaces that open inside desk windows (Settings, History,
Dictation, Workbenches, etc.). They share one prop type (`CoreProps`
in ActivityCore.tsx) but each defines its own local types
(`ContextState`, `WbSummary`, `SetupStatus`, `Macro`, etc.) and
fetches data through untyped `useResource<JsonRecord>` or raw
`apiFetch<any>` calls. There is no shared core types file — adding a
new core means copy-pasting the same patterns from an existing one.

When this story ships, every core's endpoint types, local interfaces,
and data-fetching calls are properly typed. `CoreProps` lives in its
own shared file. A `CoreEndpoints` map gives each core's API surface
compile-time structure. Zero `JsonRecord` reads without field
extraction. Zero `apiFetch<any>`.

**Articles served:** VI (honest construction — endpoint contracts must
not be bags), VIII (native-grade craft — typed cores catch field
renames at compile time).

## Deliverables

### 1. Extract `CoreProps` into `core-types.ts`

Create `web/src/pages/cores/core-types.ts`:

```typescript
import type { ReactNode } from "react";

export interface CoreProps {
  hero?: (actions: ReactNode) => ReactNode;
  scope?: string;
  scopeLabel?: string;
}
```

Update all 16 cores to import from `core-types.ts` instead of
`ActivityCore`. Remove the `CoreProps` export from `ActivityCore.tsx`.

### 2. Promote core-local interfaces into `core-types.ts`

Move locally-defined types that are already well-structured:
`ContextState`/`HistoryEntry` (ConstitutionalContextCore),
`WbSummary`/`RunSummary` (WorkbenchesHomeCore),
`SetupStatus` (SetupCore), `Macro` (CommandsCore),
`SecretState` (SettingsCore). `ProjectTimelineEntry`
(ProjectMemoryCore) stays in place but re-exports from the barrel.

### 3. Type the `useResource` calls

Replace every `useResource<JsonRecord>` with a concrete response
type. Apply across: ActivityCore (5 endpoints), CadenceCore (3),
CommandsCore (1), CompanionCore (2), DictationCore (multiple),
HistoryCore (multiple), LiveCore (5), SettingsCore (2), SetupCore (1).
Each response interface lives in `core-types.ts` or alongside its
core if truly single-use.

### 4. Eliminate `apiFetch<any>` in cores

ConstitutionalContextCore and WorkbenchesHomeCore bypass `useResource`
and call `apiFetch<any>` directly. Replace with typed generics
(`apiFetch<WbSummary[]>`, etc.). Mutation calls get typed responses
or `void`.

### 5. Add barrel export

Create `web/src/pages/cores/index.ts` re-exporting `CoreProps` and
the promoted shared types.

## What NOT to do

- Do NOT refactor cores' internal rendering. This story types the
  data layer, not the JSX tree. That is HS-117-07.
- Do NOT replace `useResource` with a different hook. It works; it
  just needs proper type parameters.
- Do NOT touch `DictationCore.tsx` (1,803 lines) or `HistoryCore.tsx`
  (1,319 lines) beyond typing their `useResource` calls. Their
  decomposition is HS-117-08 and HS-117-09.
- Do NOT move core files into subdirectories.

## Test plan

1. `npx tsc --noEmit` — zero type errors.
2. `npx vitest run` — all existing web tests pass, including
   `cores/__tests__/cores.test.tsx` and
   `cores/__tests__/projectMemoryCore.test.tsx`.
3. Verify no `JsonRecord` imports remain in `cores/`:
   `grep -rn "JsonRecord" web/src/pages/cores/` returns zero hits
   (excluding test fixtures if any).
4. Verify no `apiFetch<any>` remains in `cores/`:
   `grep -rn "apiFetch<any>" web/src/pages/cores/` returns zero hits.
5. `uv run pytest -q` — backend tests unaffected.
6. Playwright screenshot walk at 1440px and 393px — every core
   surface renders identically.

## Estimated scope

~300 lines added (response interfaces in `core-types.ts` + barrel).
~50 lines removed (inline type definitions consolidated). Net: ~250
lines added. 16 files touched (every core) plus 2 new files
(`core-types.ts`, `index.ts`).
