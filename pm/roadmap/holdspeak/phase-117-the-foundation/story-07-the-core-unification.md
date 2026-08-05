# HS-117-07 — The core unification

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-05
- **Unblocks:** HS-117-08, HS-117-09
- **Owner:** unassigned

## The thesis (the bar)

HS-117-05 typed every core's data layer (`useResource` generics,
`CoreProps` in `core-types.ts`, zero `apiFetch<any>`). But the 16
cores still copy-paste four structural patterns verbatim: the hero
slot ternary (9 cores), the busy/message mutation try-catch (8 cores,
~15 lines each), the wings tab setup (9 cores), and the
`SurfaceState` loading/error/empty guard (12 cores). Across ~10,600
lines of core code, roughly 800 are boilerplate duplicates.

When this story ships, four shared utilities live in
`web/src/pages/cores/core-hooks.ts` and `core-layout.tsx`. Every core
uses them. Net deletion: ~400 lines. Adding a new core means importing
the hooks, not copy-pasting from ActivityCore.

**Articles served:** VI (honest construction -- one pattern, one
source), X (sustainability -- removing gravity from the cores layer).

## Deliverables

### 1. Extract `useAction()` hook into `core-hooks.ts`

Create `web/src/pages/cores/core-hooks.ts`. The `useAction()` hook
replaces the `busy/message/setBusy/setMessage/try-catch-finally`
pattern found in ActivityCore (63-104), CadenceCore (35-67),
CommandsCore (57-93), LiveCore (70-207), HistoryCore (214-240),
SettingsCore (160-235), SetupCore (28-42), ProjectMemoryCore (multiple
handlers):

```typescript
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function run(fn: () => Promise<void>) {
    setBusy(true); setMessage("");
    try { await fn(); }
    catch (e) { setMessage(readableError(e)); }
    finally { setBusy(false); }
  }
  return { busy, message, run, setMessage };
}
```

Replace the hand-rolled pattern in all 8 cores.

### 2. Extract `useCoreWings()` hook

Add to `core-hooks.ts`. Wraps the repeated `WINGS` constant +
`useState` + `useWindowWings` triple found in ActivityCore (40-61),
CompanionCore (30-49), LiveCore (57-100), HistoryCore (819-832),
SettingsCore (121), DictationCore (1761), ProjectMemoryCore (378),
CommandsCore, CadenceCore. Returns `{ view, setView }`.

### 3. Extract `renderHeroSlot()` into `core-layout.tsx`

Create `web/src/pages/cores/core-layout.tsx`. Replace the identical
`hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>` ternary
copied across 9+ cores:

```typescript
export function renderHeroSlot(
  hero: CoreProps["hero"], verbs: ReactNode,
): ReactNode {
  return hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>;
}
```

### 4. Extract `CoreResourceGuard` component

Add to `core-layout.tsx`. Wraps the `SurfaceState` loading/error/empty
guard that 12 cores repeat with identical props:

```tsx
export function CoreResourceGuard({ resource, emptyLabel, children }) {
  return (
    <SurfaceState
      loading={resource.loading} error={resource.error}
      empty={!asRows(resource.data).length} emptyLabel={emptyLabel}
      onRetry={() => resource.reload()}
    >
      {children}
    </SurfaceState>
  );
}
```

### 5. Update the barrel

Add `core-hooks.ts` and `core-layout.tsx` exports to
`web/src/pages/cores/index.ts`.

## What NOT to do

- Do NOT decompose DictationCore or HistoryCore. That is HS-117-08
  and HS-117-09.
- Do NOT change any core's rendering logic or JSX structure. This
  story extracts shared plumbing, not UI.
- Do NOT replace `useResource` with a different data-fetching hook.
- Do NOT move core files into subdirectories.
- Do NOT touch `core-types.ts` beyond adding type imports the new
  hooks need.

## Test plan

1. `npx tsc --noEmit` -- zero type errors.
2. `npx vitest run` -- all existing web tests pass.
3. Verify the old boilerplate is gone:
   `grep -rn "setBusy(true)" web/src/pages/cores/ | grep -v core-hooks`
   returns zero hits.
4. `uv run pytest -q` -- backend tests unaffected.
5. Playwright screenshot walk at 1440px and 393px -- every core
   surface renders identically before and after.

## Estimated scope

~120 lines added (`core-hooks.ts` + `core-layout.tsx`). ~400 lines
removed (boilerplate across 16 cores). Net: ~280 lines removed.
18 files touched (16 cores + 2 new utility files).
