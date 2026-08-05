# HS-117-01 — The typed primitives

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-117-05, HS-117-06
- **Owner:** unassigned

## The thesis (the bar)

The wire layer has no types. `DeskItem` is a bag with
`[key: string]: unknown`. Every `fromWire*` mapper takes `any` and
returns a bag. Every consumer needs `as JsonRecord` assertions (66 of
them) or `as any` casts (72 in the desk layer). When a field name is
misspelled in a mapper, the bug is silent.

When this story ships, every entity that crosses the wire has a
concrete TypeScript interface. The `Primitive` discriminated union is
complete (16 kinds). Every `fromWire*` mapper takes `unknown`, returns
a concrete type, and uses safe field extractors. The store holds
`TypedItems` (typed arrays per kind). `WorldObject.ref` is `Primitive`,
not `DeskItem`. Zero `any` inputs to mappers. Zero `as JsonRecord` in
the desk layer.

**Articles served:** VI (honest construction — the types must not lie),
VIII (native-grade craft — type safety is a speed multiplier).

## Deliverables

### 1. Complete the `Primitive` union in `primitives.ts`

Three interfaces are missing from the union:

```typescript
export interface Roadmap {
  kind: "roadmap";
  id: string;
  title: string;
  slug: string;
  name: string;
  phaseCount: number;
  currentPhase: number;
  currentPhaseTitle: string;
  storiesDone: number;
  storiesTotal: number;
  health: "green" | "warn" | "red";
  issues: string[];
  nextStoryId: string | null;
}

export interface Story {
  kind: "story";
  id: string;
  title: string;
  status: "backlog" | "ready" | "in-progress" | "blocked" | "done";
  hasEvidence: boolean;
  phase: number;
}

export interface Workbench {
  kind: "workbench";
  id: string;
  name: string;
  recipeId: string | null;
  profileId: string | null;
  schedule: string | null;
  scheduleEnabled: boolean;
  itemCount: number;
  pendingCount: number;
  lastRun: string | null;
  createdAt: string;
  lastModified: string | null;
}
```

Add missing fields to existing interfaces: `lastModified` on Note, KB,
Project, Repository; `profileId` and `capability` on Persona; `capability`
on Chain; `hasGraph` and `capability` on Workflow; `id` and `title` on
Coder.

Update the `Primitive` union to include all 16 variants.

### 2. Add `PrimitiveMap` and exhaustiveness helpers

```typescript
export type PrimitiveMap = {
  meeting: Meeting;
  artifact: Artifact;
  note: Note;
  decision: Decision;
  directory: Directory;
  kb: KB;
  project: Project;
  repository: Repository;
  recipe: Persona;
  chain: Chain;
  workflow: Workflow;
  coder: Coder;
  game: Game;
  layout: Layout;
  roadmap: Roadmap;
  story: Story;
  workbench: Workbench;
};
```

Use `as const satisfies Record<PrimitiveKind, ...>` on the mapper
registry so that adding a new kind without a mapper is a compile error.

Do NOT add a `narrowPrimitive()` helper function. TypeScript's native
`if (item.kind === "note")` narrowing is clearer in components and
supports exhaustive switch statements. The helper adds indirection
with no narrowing advantage. (Terra review consensus.)

### 3. Create `wireGuard.ts` — safe field extractors

Create `web/src/desk/wireGuard.ts` with typed extraction helpers:

```typescript
export function wireString(wire: unknown, key: string, fallback = ""): string;
export function wireNumber(wire: unknown, key: string, fallback = 0): number;
export function wireBool(wire: unknown, key: string, fallback = false): boolean;
export function wireArray(wire: unknown, key: string): unknown[];
export function wireStringOrNull(wire: unknown, key: string): string | null;
export function wireRaw(wire: unknown, key: string): unknown;
```

Each helper checks `typeof wire === "object"`, checks `key in wire`,
and returns the typed value or fallback. No silent coercion (`String()`,
`Number()`). Missing required identity/discriminant fields should log
a contextual warning (endpoint + payload shape), not silently default.

**Terra amendment:** Add decoder tests with malformed payloads (missing
fields, wrong types, extra fields) to catch regressions when the
Python server changes. Decoders must be open to unknown extra fields —
a new server field must never crash the frontend.

### 4. Retype all `fromWire*` mappers

Change every mapper in `desk/api.ts`:
- Input: `unknown` (not `any`)
- Output: concrete primitive type (not `DeskItem`)
- Use `wireGuard` helpers for all field access

Example:

```typescript
export const fromWireMeeting = (m: unknown): Meeting => ({
  kind: "meeting",
  id: wireString(m, "id"),
  title: wireString(m, "title", "Untitled meeting"),
  startedAt: wireString(m, "started_at"),
  endedAt: wireStringOrNull(m, "ended_at"),
  segmentCount: wireNumber(m, "segment_count"),
  actionItemCount: wireNumber(m, "action_item_count"),
  durationSeconds: wireNumber(m, "duration_seconds") || null,
  tags: wireArray(m, "tags") as string[],
  intelStatus: wireStringOrNull(m, "intel_status"),
});
```

Apply the same pattern to all 15 mappers. Each mapper returns the
EXACT interface from `primitives.ts`.

### 5. Bridge type and store migration

- Set `export type DeskItem = Primitive` as a temporary alias (add
  explicit removal acceptance check — this alias must not survive
  past HS-117-06).
- Create `TypedItems` type with typed arrays per kind.
- Change the store's `items` field from `Items` to `TypedItems`.
- Change `WorldObject.ref` from `DeskItem` to `Primitive`.
- Eliminate `fetchJson` (the `Promise<any>` helper) — call `apiFetch<T>`
  with proper types directly in `loadAll()`.

### 6. Handle unknown kinds gracefully

**Terra amendment:** An unknown `kind` from the server must not crash
the desk. Define policy:
- Unknown kind → omit from the items bucket with a console warning.
- Known kind with absent required identity field → omit with a
  contextual log.
- Extra fields on a known kind → silently ignored (decoders are open).

### 7. Fix `loadAll()` return types

`loadAll()` returns `TypedItems` instead of `Items`. The structure
stays identical — `Promise.allSettled` with per-kind error tolerance.
Only the types flowing through change.

## What NOT to do

- Do NOT add zod or valibot. The wire is owned; manual guards are
  proportionate. (Both Opus and Terra agree.)
- Do NOT rename the `kind` discriminator values. `"recipe"` stays
  `"recipe"` on the wire.
- Do NOT change `loadAll()`'s structure. Keep `Promise.allSettled`,
  keep per-kind error tolerance.
- Do NOT try to type the core page endpoints in this story. That is
  HS-117-05.

## Test plan

1. `npx tsc --noEmit` — zero type errors.
2. `npx vitest run` — all existing web tests pass.
3. New tests in `web/src/desk/__tests__/wireGuard.test.ts`:
   - Each mapper produces the correct shape from valid wire data.
   - Each mapper handles missing fields with fallbacks.
   - Each mapper handles malformed field types gracefully.
   - Unknown kinds are omitted, not crashed.
4. `uv run pytest -q` — backend tests unaffected.
5. Playwright screenshot walk at 1440px and 393px — the desk looks
   identical.

## Estimated scope

~500 lines changed across `primitives.ts`, `api.ts`, `wireGuard.ts`
(new), `world.ts`, `store.ts`, `contextual.ts`. Net line count:
slight increase (wireGuard adds ~80 lines; mapper rewrite is ~same).
