# HS-117-14 — The kind exhaustiveness gate

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01
- **Unblocks:** pullout protocol story
- **Owner:** unassigned

## The thesis (the bar)

Adding a new primitive kind today requires touching 8+ files across the
codebase. Nothing enforces completeness -- you can add a kind to
`PrimitiveKind` but forget to add it to the `ORDER` array in `world.ts`,
the `EMPTY_ITEMS` in `api.ts`, the `PRIMITIVES` registry, or the
`DESK_GROUPS`. The bug is silent: the kind simply does not appear, or
appears with undefined labels.

When this story ships, every kind-keyed registry and every kind-branching
code path is compile-checked for exhaustiveness. Adding a new
`PrimitiveKind` variant without updating every registry is a type error,
not a runtime surprise. The difference between `Kind` (14 wire values)
and `PrimitiveKind` (16 values) is explicitly typed. Zero new
architecture -- ~30 lines of type-level enforcement on existing
registries.

**Articles served:** VI (honest construction -- the compiler catches
the lie), III (sovereignty of the primitive -- every kind is a
first-class citizen or an explicit exclusion).

## Deliverables

### 1. Reconcile `Kind` and `PrimitiveKind`

`api.ts` defines `Kind` (14 values); `primitives.ts` defines
`PrimitiveKind` (16 values). Make `PrimitiveKind` the single source of
truth. Define the subset explicitly:

```typescript
// api.ts
export type WireKind = Exclude<PrimitiveKind, "layout" | "workbench">;
```

**Note:** HS-117-01 adds `workbench` to `PrimitiveKind` and the
`Primitive` union. Verify the exact set of non-wire kinds at
implementation time — the `Exclude` list must match whichever kinds
lack a dedicated `/api/<kind>` endpoint in `loadAll()`. If `workbench`
does have a wire endpoint (`/api/workbenches` exists), remove it from
the exclude.

Replace every use of the old `Kind` type with `WireKind`. Remove the
duplicate `Kind` definition.

### 2. Add `satisfies Record<PrimitiveKind, ...>` on full registries

Apply `satisfies` to every registry that must cover all kinds:

- `PRIMITIVES` in `primitives.ts` -- already `Record<PrimitiveKind, PrimitiveDescriptor>`, add explicit `satisfies` if not present.
- `EMPTY_ITEMS` in `api.ts` -- currently untyped; add `satisfies Record<PrimitiveKind, ...>`.
- `DESK_GROUPS` in `primitives.ts` -- ensure every kind appears in exactly one group (type-check the flattened union).
- The mapper registry from HS-117-01 -- `as const satisfies Record<WireKind, ...>` (only wire kinds have mappers).

### 3. Add `satisfies Partial<Record<...>>` on partial registries

For registries where not every kind is valid, use `Partial<Record<...>>`:

- `posts` map in `store.ts` `createPrimitive` -- `satisfies Partial<Record<WireKind, string>>`.
- `urls` map in `store.ts` `updatePrimitive` -- `satisfies Partial<Record<WireKind, string>>`.
- `paths` map in `store.ts` `deletePrimitive` -- `satisfies Partial<Record<WireKind, string>>`.

### 4. Type-check `ORDER` in `world.ts`

Type the `ORDER` constant as `readonly PrimitiveKind[]` and add a
compile-time completeness check:

```typescript
type AssertAllKinds<T extends readonly PrimitiveKind[]> =
  Exclude<PrimitiveKind, T[number]> extends never ? T : never;

const ORDER = [
  "meeting", "artifact", /* ... all 16 ... */
] as const satisfies AssertAllKinds<typeof ORDER>;
```

A missing kind makes `AssertAllKinds` resolve to `never`, failing
`satisfies`.

### 5. Add `assertNever` exhaustive-switch helper

Create `web/src/desk/assertNever.ts`:

```typescript
export function assertNever(x: never): never {
  throw new Error(`Unhandled kind: ${x}`);
}
```

Apply it in the `default` branch of kind-switching code in:

- `Pullout.tsx` -- the `if/else` chain on `o.kind` (convert to `switch`).
- `InlineEditor.tsx` -- the `if/else` chain on `kind`.
- `verbRegistry.ts` -- the `VERBS` array builder, `EDITABLE` set, `ASKABLE` set.
- `dropMatrix.ts` -- the `DROP_MATRIX` record (add `satisfies Record<PrimitiveKind, ...>`).

### 6. Audit and close gaps

Run `npx tsc --noEmit` after all changes. Fix every new type error that
surfaces (these are the bugs the gate is designed to catch). Document
each fix as a one-line comment in the evidence file.

## What NOT to do

- Do NOT create a manifest, framework, or registration system. This is
  type-level enforcement only -- the registries stay where they are.
- Do NOT merge `WireKind` back into `PrimitiveKind`. The distinction
  is real: some kinds have no server endpoint.
- Do NOT refactor Pullout or InlineEditor beyond converting if/else to
  switch. Behavior stays identical.
- Do NOT add runtime kind validation. This story is compile-time only.
  Runtime unknown-kind handling is HS-117-01 deliverable 6.

## Test plan

1. `npx tsc --noEmit` -- zero type errors.
2. `npx vitest run` -- all existing web tests pass.
3. Prove the gate works: temporarily add `"test_phantom"` to
   `PrimitiveKind`, run `npx tsc --noEmit`, confirm errors in every
   gated registry. Revert before commit.
4. `uv run pytest -q` -- backend tests unaffected.
5. Playwright screenshot walk at 1440px and 393px -- the desk looks
   identical (no runtime changes).

## Estimated scope

~30 lines of type annotations and one 4-line utility function.
~200 lines changed across `primitives.ts`, `api.ts`, `store.ts`,
`world.ts`, `Pullout.tsx`, `InlineEditor.tsx`, `verbRegistry.ts`,
`dropMatrix.ts`, `assertNever.ts` (new). Net new code: minimal.
If/else-to-switch conversions in Pullout and InlineEditor are the
largest diffs.
