# HS-117-16 — The surface declaration

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Three separate patterns govern how a primitive appears on the desk:
(1) generic pullout card via `openPullout()`, (2) whole-page surface
registered in the SURFACES array in `SurfaceWindows.tsx`, (3) bespoke
dedicated window with its own array in the store (workbenchWindows,
roadmapWindows, repositoryWindows). No kind declares which pattern it
uses. `openPullout` is a god-method that pattern-matches by ID prefix
and item membership to guess the right pattern. Building a new kind
requires knowing which pattern applies, then manually wiring the right
files.

When this story ships, every `PrimitiveDescriptor` in `primitives.ts`
carries a `surface` field that declares how that kind opens. The
`openPullout` dispatch reads the declaration instead of guessing. Zero
new files, zero new architecture — one field on an existing registry.

**Articles served:** VI (honest construction — the surface strategy is
declared, not guessed), VIII (native-grade craft — adding a new kind
does not require reading three dispatch paths to pick the right one).

## Deliverables

### 1. Add the `surface` field to `PrimitiveDescriptor`

Extend the existing `PrimitiveDescriptor` interface in
`web/src/desk/primitives.ts`:

```typescript
interface PrimitiveDescriptor {
  // existing: label, plural, syncClass, blurb, icon, authorable
  surface:
    | { type: "pullout" }
    | { type: "window"; component: string; windowKey: string }
    | { type: "surface"; surfaceKey: string }
    | { type: "none" };
}
```

- `pullout` — opens as a card in the pullout system (most kinds).
- `window` — opens via a dedicated window array in the store.
  `windowKey` names the open method (e.g. `"RoadmapWindow"` maps to
  `openRoadmapWindow`). `component` names the component for tracing.
- `surface` — opens a whole-page surface via `openSurfaceWhenReady`.
  `surfaceKey` is the slug registered in the SURFACES array.
- `none` — no direct open (story, layout, or other kinds that never
  appear as standalone windows).

### 2. Populate `surface` for every kind in the PRIMITIVES map

Walk every entry in `PRIMITIVES` and set the correct `surface` value
by auditing the current `openPullout` dispatch and the SURFACES array:

- Kinds routed to `openRoadmapWindow`: `{ type: "window", component: "RoadmapWindow", windowKey: "RoadmapWindow" }`.
- Kinds routed to `openRepositoryWindow`: `{ type: "window", component: "RepositoryWindow", windowKey: "RepositoryWindow" }`.
- Kinds routed to `openWorkbenchWindow`: `{ type: "window", component: "WorkbenchWindow", windowKey: "WorkbenchWindow" }`.
- Kinds routed to `openSurfaceWhenReady`: `{ type: "surface", surfaceKey: "<slug>" }`.
- Kinds with no direct open behavior: `{ type: "none" }`.
- All remaining kinds: `{ type: "pullout" }`.

Every kind must have a `surface` value. TypeScript enforces this at
compile time because the field is required.

### 3. Refactor `openPullout` to read the declaration

Replace the pattern-matching logic in `openPullout` (store.ts lines
761-791) with a declaration-driven dispatch.

**Kind resolution from ID:** The current `openPullout` receives a
string `id`, not a kind. It resolves the item via `find()` across the
items arrays. Once the item is found, `item.kind` is known. The
dispatch then reads `PRIMITIVES[item.kind].surface`. This resolution
step stays — the surface declaration replaces the *routing decision*,
not the *item lookup*.

**Qualified-ref parsing:** The current code handles prefixed IDs
(`roadmap:slug`, `project:id`). This parsing runs BEFORE the surface
dispatch — it strips the prefix and resolves the kind. The surface
declaration does not eliminate qualified refs; it eliminates the
if/else chain that follows them.

```typescript
// Step 1: resolve kind from id (qualified refs parsed here)
const { kind, resolvedId } = resolveKindFromId(id, get);
if (!kind) { console.warn(`Unknown id: ${id}`); return; }

// Step 2: declaration-driven dispatch
const desc = PRIMITIVES[kind];
switch (desc.surface.type) {
  case "pullout":
    get().addPullout(resolvedId, origin);
    break;
  case "window":
    get()[`open${desc.surface.windowKey}`](resolvedId, origin);
    break;
  case "surface":
    openSurfaceWhenReady(desc.surface.surfaceKey);
    break;
  case "none":
    break;
}
```

If HS-117-02 has shipped, this dispatch lives in
`store/pulloutRoutes.ts`. If not, refactor in place in `store.ts`.
The dispatch is exhaustive — TypeScript's `never` check ensures every
surface type is handled.

### 4. Type-safe open helper for `window` kinds

Add a helper in `primitives.ts` that narrows the surface type and
returns the windowKey, so callers outside `openPullout` can also
open a kind correctly without reimplementing the dispatch:

```typescript
export function surfaceOpener(kind: PrimitiveKind): PrimitiveDescriptor["surface"] {
  return PRIMITIVES[kind].surface;
}
```

This is a one-liner accessor, not a framework. It exists so the window
factory from HS-117-02 can use the declaration to auto-generate
open/close pairs for `type: "window"` kinds.

## What NOT to do

- Do NOT create a registration framework, plugin system, or new file
  for surface declarations. This is ONE field on an EXISTING map.
- Do NOT move SURFACES entries or surface components. The declaration
  points to existing infrastructure; it does not replace it.
- Do NOT add lazy-loading, dynamic imports, or component references
  to the descriptor. `component` is a string label for tracing, not
  a React import.
- Do NOT change how any window type actually opens. The open/close
  methods stay exactly where they are. Only the dispatch decision
  moves from pattern-matching to declaration reading.
- Do NOT remove the fallback path. If `item.kind` is not in PRIMITIVES
  (should not happen, but defensive), fall through to pullout behavior
  with a `console.warn`.

## Test plan

1. `npx tsc --noEmit` — zero type errors. The required `surface` field
   on `PrimitiveDescriptor` means every kind entry compiles only if
   populated.
2. `npx vitest run` — all existing tests pass unchanged.
3. New unit tests in `web/src/desk/__tests__/surface-declaration.test.ts`:
   - Every `PrimitiveKind` has a `surface` field with a valid `type`.
   - No two `type: "window"` kinds share the same `windowKey` unless
     they intentionally share a window type.
   - Every `type: "surface"` kind's `surfaceKey` exists in the
     SURFACES array.
   - The dispatch function handles all four surface types without
     throwing.
4. `uv run pytest -q` — backend tests unaffected.
5. Playwright screenshot walk at 1440px and 393px — open one primitive
   of each surface type, verify it still opens in the correct container.

## Estimated scope

~30 lines added to `primitives.ts` (interface extension + surface
values across existing entries). ~20 lines changed in `openPullout`
(replace pattern-matching with switch on declaration). ~60 lines of
new tests. Net: ~80 lines added, ~25 lines removed. Half-day story.
