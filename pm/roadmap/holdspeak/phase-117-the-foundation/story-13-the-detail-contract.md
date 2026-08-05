# HS-117-13 — The detail contract

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01, HS-117-15
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

`WorkbenchWindow.tsx` is a 1,444-line god-component with 21 `useState`
calls. It defines its own types inline (`WorkbenchDetail`,
`WorkbenchItem`, `WorkbenchRun`, `Skill`, `MemoryEntry` at lines
51-108), makes its own inline `apiFetch` calls with swallowed errors,
and manages its own WebSocket subscription logic. This pattern WILL
repeat for every rich primitive window. It is why the owner called the
Workbench execution "holy shit — just bad."

When this story ships, detail types are first-class citizens in the
type layer, a single `usePrimitiveDetail` hook replaces the 3-5
`useState` calls every bespoke window duplicates, and API calls live in
`api.ts` where they belong. WorkbenchWindow drops to roughly half its
current size. The pattern is concrete enough to port to RoadmapWindow
and RepositoryWindow in the same commit.

**Articles served:** VI (honest construction — inline types lie about
their importance), VIII (native-grade craft — a 1,444-line component
is not craft).

## Deliverables

### 1. Promote detail types into the type layer

Move the inline types from `WorkbenchWindow.tsx` (lines 51-108) into
`web/src/desk/detail-types.ts`:

```typescript
export interface WorkbenchDetail {
  id: string;
  name: string;
  recipeId: string | null;
  profileId: string | null;
  schedule: string | null;
  scheduleEnabled: boolean;
  skills: Skill[];
  memories: MemoryEntry[];
  constitutionalContext: string | null;
}

export interface WorkbenchItem { /* ... */ }
export interface WorkbenchRun  { /* ... */ }
export interface Skill         { /* ... */ }
export interface MemoryEntry   { /* ... */ }
```

Audit `RoadmapWindow.tsx` and `RepositoryWindow.tsx` for inline detail
types. Promote any found into the same file (e.g. `RoadmapDetail`,
`RepositoryDetail`). Each interface uses `wireGuard` field types (from
HS-117-01) — no `any`, no `as` casts.

### 2. Extract API calls into `api.ts`

Move every inline `apiFetch` call from `WorkbenchWindow.tsx` into
`web/src/desk/api.ts` as typed endpoint functions:

```typescript
export async function fetchWorkbenchDetail(id: string): Promise<WorkbenchDetail>;
export async function fetchWorkbenchItems(id: string): Promise<WorkbenchItem[]>;
export async function fetchWorkbenchRuns(id: string): Promise<WorkbenchRun[]>;
export async function updateWorkbenchSchedule(id: string, schedule: string | null, enabled: boolean): Promise<void>;
export async function runWorkbench(id: string): Promise<WorkbenchRun>;
```

Each function:
- Uses `apiFetch<T>` with a concrete return type (no `any`).
- Applies `wireGuard` extractors on the response.
- Throws a typed error on failure (no swallowed catches).

Apply the same extraction to `RoadmapWindow.tsx` and
`RepositoryWindow.tsx` if they contain inline fetches.

### 3. Create `usePrimitiveDetail<T>` hook

Create `web/src/desk/hooks/usePrimitiveDetail.ts`:

```typescript
interface PrimitiveDetailState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function usePrimitiveDetail<T>(
  kind: string,
  id: string | null,
  fetchFn: (id: string) => Promise<T>,
): PrimitiveDetailState<T>;
```

The hook handles:
- Fetch on mount and when `id` changes.
- `loading` / `error` / `data` state (replaces 3 `useState` calls).
- Refetch on window refocus (`visibilitychange`) — one event
  listener, not a cache framework. Prevents stale data when switching
  between desk windows.
- Abort on unmount / id change (no state updates after unmount).
- Stable `refresh` callback (does not cause re-render loops).

The hook does NOT handle:
- WebSocket subscriptions (stays component-side).
- Caching across components (no shared cache layer).
- Retry logic (the caller decides).

### 4. Rewire `WorkbenchWindow.tsx`

Replace the inline types, inline fetches, and detail-loading
`useState` calls with the new primitives:

```typescript
import { WorkbenchDetail, WorkbenchItem } from "../detail-types";
import { fetchWorkbenchDetail, fetchWorkbenchItems } from "../api";
import { usePrimitiveDetail } from "./usePrimitiveDetail";

// Before: 5 useState calls for detail loading
// After:
const detail = usePrimitiveDetail("workbench", id, fetchWorkbenchDetail);
const items = usePrimitiveDetail("workbench-items", id, fetchWorkbenchItems);
```

WebSocket subscription logic stays in the component. The goal is to
cut `WorkbenchWindow.tsx` by ~150-250 lines (conservative — some
useState calls are UI state like tab selection, not fetch state) and eliminate all inline
type definitions and all inline `apiFetch` calls.

### 5. Rewire `RoadmapWindow.tsx` and `RepositoryWindow.tsx`

Apply the same pattern: promote inline types, extract API calls, use
`usePrimitiveDetail`. If either window has fewer than 3 inline
`useState` calls for detail loading, the hook is optional — only adopt
it where the duplication is real.

## What NOT to do

- Do NOT create a generic data-fetching framework. No SWR, no
  react-query, no staleness timers, no background polling, no cache
  invalidation. This is a fetch-on-mount hook with a refocus trigger.
- Do NOT move WebSocket subscription logic into the hook. The hook is
  fetch-only. WebSocket stays component-side.
- Do NOT create a shared cache layer across components. Each hook
  instance owns its own state.
- Do NOT refactor the internal rendering logic of WorkbenchWindow.
  This story is about the data contract, not the JSX tree.
- Do NOT add retry/backoff logic. Failed fetches surface the error;
  the user triggers retry via `refresh`.

## Test plan

1. `npx tsc --noEmit` — zero type errors.
2. `npx vitest run` — all existing web tests pass.
3. New tests in `web/src/desk/hooks/__tests__/usePrimitiveDetail.test.ts`:
   - Fetches on mount with correct id.
   - Refetches when id changes.
   - Aborts in-flight fetch on unmount (no state-after-unmount warning).
   - Sets loading/error/data correctly on success and failure.
   - `refresh()` triggers a new fetch without clearing current data
     (stale-while-revalidate).
4. New tests in `web/src/desk/__tests__/detail-api.test.ts`:
   - Each extracted endpoint function returns the correct typed shape.
   - Each endpoint applies wireGuard extraction (malformed payloads
     produce correct fallbacks, not crashes).
5. `uv run pytest -q` — backend tests unaffected.
6. Playwright screenshot walk at 1440px and 393px — WorkbenchWindow,
   RoadmapWindow, and RepositoryWindow render identically.

## Estimated scope

~400 lines added across `detail-types.ts` (new, ~80 lines),
`api.ts` (~60 lines of new endpoints), `usePrimitiveDetail.ts`
(new, ~60 lines), plus ~200 lines of new tests. ~300 lines removed
from `WorkbenchWindow.tsx` and smaller reductions from
`RoadmapWindow.tsx` and `RepositoryWindow.tsx`. Net: ~100-line
reduction.
