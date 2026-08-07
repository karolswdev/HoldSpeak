# HS-117-06 — The component narrowing

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

HS-117-01 gave every wire entity a concrete TypeScript interface and
made `WorldObject.ref` a `Primitive` discriminated union. But 49
`as any` casts survive in the desk layer. The dominant pattern is
`const ir = o.ref as any; ir.bodyMarkdown` — accessing kind-specific
fields without narrowing on `o.ref.kind`. The proof that narrowing
works already exists at `DeskListView.tsx:95`:
`o.ref.kind === "coder" ? o.ref.agent : "claude"`. That pattern must
replace every cast.

When this story ships, zero `as any` casts remain in the desk layer
(excluding test fixtures). Every kind-specific field access is guarded
by a `kind` check. TypeScript proves at compile time that each field
access is valid for the matched kind.

**Articles served:** VI (honest construction — `as any` is a lie to
the compiler), VIII (native-grade craft — discriminated unions are a
speed multiplier for refactors).

## Deliverables

### 1. Narrow the pullout components (22 casts)

Eight pullout files each assign `const ir = o.ref as any` at the top.
Replace with a kind guard and early return:

```typescript
if (o.ref.kind !== "kb") return null;
const ir = o.ref; // TypeScript narrows to KB
```

Files: `KbPullout` (1), `RecipePullout` (1), `WorkflowPullout` (1),
`NotePullout` (1), `ArtifactPullout` (1), `ChainPullout` (1),
`CoderPullout` (1), `DecisionPullout` (2),
`shared/CapabilitySection` (3, multiple kinds), `Pullout.tsx` (1).

### 2. Narrow the editor components (13 casts)

Editor components receive `live` (a ref record) and cast to `any`.
`RecipeEditor` (8 casts), `NoteEditor` (3), `WorkflowEditor` (2).
Each editor's parent already knows the kind. Type the `live` prop as
the concrete interface (`Persona`, `Note`, `Workflow` from
`primitives.ts`) so field access needs no cast.

### 3. Narrow `infoContract.ts` (6 casts)

Lines 36-83 access `.memberIds`, `.bodyMarkdown`, `.segmentCount`,
`.meetingCount`, `.profileId` via `as any`. Replace with per-kind
`if` guards (e.g. `o.ref.kind === "directory" ? o.ref.memberIds...`).

### 4. Narrow `gl/sceneModel.ts` and `lineage.ts` (7 casts)

`sceneModel.ts` (lines 138, 223, 165): access `.agent`, `.memberIds`
via casts. The scene model already reads `ref.kind` for icon
textures — add narrowing. `lineage.ts` (lines 62-71, 5 casts):
define a `LineageSource` discriminated union for the polymorphic
source record.

### 5. Fix the remaining one-off casts (6 casts)

`PersonaChat.tsx` (2), `AskPanel.tsx` (1), `steering.ts` (1),
`store/recordingSlice.ts` (1), `store/dataSlice.ts` (1). Each needs
a concrete type or kind narrow — no structural change.

### 6. Remove the `DeskItem` alias

HS-117-01 set `export type DeskItem = Primitive` as a temporary
bridge. Remove the alias entirely. Update any remaining imports of
`DeskItem` to use `Primitive` directly. This alias was explicitly
flagged for removal in this story.

## What NOT to do

- Do NOT add a generic `narrowPrimitive()` helper function.
  TypeScript's native `if (item.kind === "note")` narrowing is
  clearer. (Terra review consensus from HS-117-01.)
- Do NOT change the `Primitive` union or add new kinds. The union is
  set by HS-117-01.
- Do NOT refactor component rendering logic. This story fixes type
  casts only — the JSX stays as-is.
- Do NOT suppress `as any` with `// eslint-disable`. Every cast must
  be replaced, not hidden.
- Do NOT touch test files. Test fixtures may legitimately use `any`
  for mock construction.

## Test plan

1. `npx tsc --noEmit` — zero type errors.
2. `npx vitest run` — all existing web tests pass.
3. Verify zero `as any` in desk production code:
   `grep -rn "as any" web/src/desk/ --include="*.ts" --include="*.tsx"
   | grep -v __tests__ | grep -v node_modules` returns zero hits.
4. Verify `DeskItem` alias is gone:
   `grep -rn "DeskItem" web/src/` returns zero hits.
5. `uv run pytest -q` — backend tests unaffected.
6. Playwright screenshot walk at 1440px and 393px — every pullout,
   editor, info window, and list view renders identically.

## Estimated scope

~200 lines changed across 20 files. Net line count: slight increase
(kind guards add ~1 line per cast site; editor prop types add ~10
lines total). Zero new files.
