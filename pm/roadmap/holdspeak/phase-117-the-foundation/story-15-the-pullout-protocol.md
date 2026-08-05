# HS-117-15 — The pullout protocol

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Pullout.tsx is 900+ lines of `if/else` branches on `o.kind`. Every
kind gets a bespoke JSX block inline. InlineEditor.tsx has the same
pattern. Adding a new kind means finding the right spot in a long
conditional chain, pasting a block, and hoping. There is no
compile-time enforcement that every kind is handled, no isolation
between kind renderers, and no way to test one kind's pullout content
without mounting the entire god-dispatcher.

When this story ships, Pullout.tsx is a thin chrome shell (~100 lines)
that renders header, close button, and toolbar, then delegates body
content to a kind-keyed component map. Each kind's pullout content
lives in its own file under `desk/pullouts/`. InlineEditor.tsx follows
the same extraction. Adding a new kind means creating one file and
adding one line to the map — the `satisfies Record<PrimitiveKind, ...>`
gate (from HS-117-14) makes a missing entry a compile error. Each
extracted component is independently renderable and testable.

**Articles served:** VI (honest construction — the dispatcher must not
hide its routing), VIII (native-grade craft — isolation is a speed
multiplier for future kind work).

## Deliverables

### 0. Audit shared state and sub-components

Before extracting, audit Pullout.tsx for:
- **Shared state** between kind branches (editing mode, dirty tracking,
  save handlers, selection state). Document which state is pullout-level
  (stays in the chrome shell) vs. kind-level (moves into the per-kind
  component).
- **Shared sub-components** used by multiple kinds (tags panel, related
  items widget, action bar patterns). These go in
  `desk/pullouts/shared/` — not duplicated into each kind component.
- **Shared hooks/selectors** — store selectors used by 3+ branches
  become shared utilities in `desk/pullouts/shared/`.

This audit determines the `PulloutContentProps` interface in
deliverable 1. Do not design the interface speculatively — derive it
from what the current branches actually use.

### 1. Define the `PulloutContent` component interface

Create `web/src/desk/pullouts/types.ts`:

```typescript
import type { Primitive } from "../primitives";

export interface PulloutContentProps {
  object: WorldObject;
  onClose: () => void;
  isCompact: boolean;
  // add whatever shared props Pullout currently threads to branches
}

export type PulloutContent = React.FC<PulloutContentProps>;
```

Audit Pullout.tsx for every prop threaded into branches (store
selectors, callbacks, flags). Capture them all in the interface. Do
not add props speculatively — only props the current branches use.

### 2. Extract per-kind pullout components

Create one file per kind under `web/src/desk/pullouts/`:

- `MeetingPullout.tsx` — the largest branch (meeting intel, action
  items, playback controls, segment list)
- `NotePullout.tsx`
- `DecisionPullout.tsx`
- `DirectoryPullout.tsx`
- `KBPullout.tsx`
- `ProjectPullout.tsx`
- `RepositoryPullout.tsx`
- `PersonaPullout.tsx` (kind = `recipe`)
- `ChainPullout.tsx`
- `WorkflowPullout.tsx`
- `CoderPullout.tsx`
- `GamePullout.tsx`
- `LayoutPullout.tsx`
- `RoadmapPullout.tsx`
- `StoryPullout.tsx`
- `WorkbenchPullout.tsx`
- `ArtifactPullout.tsx`

Each component receives `PulloutContentProps` and contains exactly
the JSX + hooks that its branch currently has in Pullout.tsx.
Move, do not rewrite — preserve behavior line-for-line.

### 3. Build the kind-keyed component map

Create `web/src/desk/pullouts/registry.ts`:

```typescript
import type { PrimitiveKind } from "../primitives";
import type { PulloutContent } from "./types";

export const PULLOUT_CONTENT: Record<PrimitiveKind, PulloutContent | null> = {
  meeting: MeetingPullout,
  note: NotePullout,
  decision: DecisionPullout,
  // ... all 16 kinds
} satisfies Record<PrimitiveKind, PulloutContent | null>;
```

Kinds that genuinely have no pullout body use `null`. The shell
renders a "no detail view" fallback for `null` entries.

### 4. Reduce Pullout.tsx to a chrome shell

Pullout.tsx keeps: the outer card chrome (panel frame, header bar
with title + kind icon, close button, toolbar/action bar), sizing
logic, drag/resize hooks. The body is:

```tsx
const Content = PULLOUT_CONTENT[o.kind];
return Content
  ? <Content object={o} onClose={onClose} isCompact={isCompact} />
  : <FallbackPullout kind={o.kind} />;
```

Target: ~100 lines. The `if/else` chain is gone entirely.

### 5. Apply the same extraction to InlineEditor.tsx

Define `InlineEditorContent` interface. Extract per-kind editor
components to `web/src/desk/editors/` (or colocate with pullouts if
the branch is small). Build a `INLINE_EDITOR` registry with the same
`satisfies Record<PrimitiveKind, ...>` gate.

### 6. Barrel exports

Create `web/src/desk/pullouts/index.ts` exporting `PULLOUT_CONTENT`,
`PulloutContentProps`, and the individual components. Same for
editors if separated.

## What NOT to do

- Do NOT rewrite branch logic during extraction. This is a structural
  move, not a behavior change. Preserve the JSX line-for-line.
- Do NOT merge multiple kinds into a single "generic" component. Each
  kind gets its own file even if the body is five lines. The point is
  isolation and the compile-time map, not DRY.
- Do NOT add new features to any pullout during this story. Refactor
  only.
- Do NOT change WorldStage.tsx or how it mounts `<Pullout>`. The shell
  boundary is inside Pullout.tsx, not above it.
- Do NOT create a dynamic `import()` / lazy-load scheme. Static
  imports keep the map simple and the `satisfies` gate working.

## Test plan

1. `npx tsc --noEmit` — zero type errors. The `satisfies` gate
   catches any missing kind in the map.
2. `npx vitest run` — all existing tests pass unchanged.
3. New tests in `web/src/desk/pullouts/__tests__/`:
   - Each extracted component renders without crashing given a
     well-typed `WorldObject` of its kind.
   - The registry covers every `PrimitiveKind` (programmatic check).
   - `null` entries render the fallback component.
4. New tests in `web/src/desk/editors/__tests__/`:
   - Each extracted editor component renders for its kind.
   - The editor registry covers every `PrimitiveKind`.
5. Playwright screenshot walk at 1440px and 393px — every kind's
   pullout looks identical to before the extraction.

## Estimated scope

~18 new files (16 pullout components + types + registry), plus
editor equivalents. Net line count: slight increase from file
boilerplate; Pullout.tsx drops ~800 lines, InlineEditor.tsx drops
proportionally. Total churn ~1,200 lines moved, ~100 lines new
(registry, types, tests).
