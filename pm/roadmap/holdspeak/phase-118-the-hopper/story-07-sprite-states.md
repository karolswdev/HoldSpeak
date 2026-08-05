# HS-118-07 — Sprite states

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

Every DeskPrimitive has one static sprite. A recording meeting looks
identical to an idle one. A processing workbench looks the same as a
finished one. A draft artifact is indistinguishable from a finalized
one. The desk is a spatial OS that can't communicate state at a
glance — you have to open each object to learn what it's doing.

When this ships, every DeskPrimitive kind declares a state vocabulary
and the desk renderer maps `(kind, state)` to a sprite variant. The
system-level contract is in place: the primitive type carries a
`spriteState` field, the sprite-state registry maps kind+state to a
variant key, and the world renderer looks up the active variant when
painting. The actual pixel art assets are a follow-up concern — this
story ships the backbone so that assets can be generated to a spec.

This is not a workbench feature. It's an OS feature. Every primitive
kind benefits. The workbench is the first consumer because this phase
needs its sprites to breathe.

**Articles served:** II (DeskPrimitive contract — state is a
primitive-level concern, not a per-kind hack), VIII (native-grade
craft — the desk surface communicates visually at 60fps).

## The state model

Every DeskPrimitive gains an optional `spriteState: string` field.
The field is nullable — `null` means "default state" (backward
compatible with every existing primitive). The state vocabulary is
per-kind, declared in a central registry.

```typescript
// web/src/lib/spriteStates.ts

interface SpriteStateEntry {
  key: string;           // the variant key (e.g. "idle", "running")
  label: string;         // human-readable label for debug/tooling
  cssHint?: string;      // optional CSS class hint for non-Pixi contexts
}

type SpriteStateVocabulary = Record<string, SpriteStateEntry[]>;

const SPRITE_STATE_VOCABULARY: SpriteStateVocabulary = {
  workbench: [
    { key: "idle",    label: "Idle" },
    { key: "pending", label: "Has pending work" },
    { key: "running", label: "Processing",     cssHint: "sprite-active" },
    { key: "fresh",   label: "Just completed",  cssHint: "sprite-fresh" },
  ],
  meeting: [
    { key: "idle",      label: "No session" },
    { key: "recording", label: "Recording",    cssHint: "sprite-active" },
    { key: "paused",    label: "Paused" },
  ],
  artifact: [
    { key: "draft",           label: "Draft" },
    { key: "final",           label: "Finalized" },
    { key: "pending-review",  label: "Pending review", cssHint: "sprite-pending" },
  ],
  // Other kinds can be added incrementally.
  // Kinds not in this registry use the default (null) sprite.
};
```

The registry is a plain TypeScript object — no database, no API.
Adding states to a kind is a code change, not a data change.

## The sprite-variant registry

Maps `(kind, state)` to the asset key the renderer should use:

```typescript
// web/src/lib/spriteVariants.ts

type VariantKey = string;  // e.g. "workbench-idle", "workbench-running"

function spriteVariantKey(kind: string, state: string | null): VariantKey {
  if (!state) return kind;  // default: use the kind name as asset key
  const vocab = SPRITE_STATE_VOCABULARY[kind];
  if (!vocab?.some(e => e.key === state)) return kind;  // unknown state: default
  return `${kind}-${state}`;
}
```

The variant key is a lookup into the sprite asset registry (the
existing PixiJS texture cache or sprite sheet). If the variant key
has no loaded asset, the renderer falls back to the base kind sprite
(graceful degradation — missing assets never break the desk).

## Deliverables

1. **Extend the DeskPrimitive type.** Add `spriteState?: string |
   null` to every primitive interface in `web/src/lib/primitives.ts`.
   This is a single optional field on the base type that all kinds
   inherit. Default: `null` (no state, use default sprite).

2. **State vocabulary registry** (`web/src/lib/spriteStates.ts`).
   Declares the valid states per kind. Initial vocabularies for:
   workbench, meeting, artifact. Other kinds start with no vocabulary
   (they use the default sprite until states are declared).

3. **Sprite-variant key function** (`web/src/lib/spriteVariants.ts`).
   Pure function: `(kind, state) → variantKey`. Graceful fallback to
   base kind when state is null or unknown.

4. **World renderer integration.** The PixiJS desk renderer
   (`web/src/desk/` — the world object painting code) calls
   `spriteVariantKey(primitive.kind, primitive.spriteState)` when
   choosing which texture/sprite to display. If the variant key has
   a loaded texture, use it. If not, use the base sprite AND apply
   the CSS hint tint (opacity/transform) to the PixiJS container as
   a visual distinction. This is not a silent fallback — the
   tint/opacity change is visible even without a dedicated asset,
   satisfying Article VI (no hidden broken dependency).

5. **State derivation for workbenches.** The workbench's `spriteState`
   is derived from runtime data, not stored in the DB:

   | Condition | spriteState |
   |-----------|-------------|
   | No pending items, not running | `"idle"` |
   | Has pending items, not running | `"pending"` |
   | Run in progress (WS `workbench.run_start` received, `run_complete` not yet) | `"running"` |
   | Run completed < 5 min ago | `"fresh"` |

   This derivation lives in the desk store or a derived selector.
   It subscribes to the runtime bus for workbench events and to the
   primitive data for `pendingCount`.

   The `fresh` → `idle`/`pending` transition requires a timer.
   When `workbench.run_complete` fires, start a 5-minute
   `setTimeout`. On expiry, re-derive the state (if pending items
   exist, transition to `pending`; otherwise `idle`). The timer is
   cleared if a new `run_start` arrives before expiry. The timer
   lives in the store or a lightweight effect — no polling.

6. **State derivation for meetings.** Derived from the existing
   meeting session state:

   | Condition | spriteState |
   |-----------|-------------|
   | No active session | `"idle"` |
   | Recording in progress | `"recording"` |
   | Session paused | `"paused"` |

7. **State derivation for artifacts.** Directly from the artifact's
   `status` field: `"draft"`, `"final"`, `"pending-review"`. No
   runtime derivation needed — it's already stored.

8. **CSS hint classes.** For non-Pixi contexts (window title bars,
   list rows, dashboard cards), the `cssHint` from the vocabulary
   entry is applied as a class on the primitive's icon/avatar
   element. This enables CSS-driven state indication (e.g. a subtle
   pulsing border on `sprite-active`) without PixiJS. Define:

   All animations use compositor-only properties (`opacity`,
   `transform`) per Article VIII. No `box-shadow` animation.

   ```css
   .sprite-active {
     animation: sprite-pulse 1.5s ease-in-out infinite;
   }
   .sprite-fresh {
     animation: sprite-flash 500ms ease-out;
   }
   .sprite-pending {
     opacity: 0.7;
   }
   @keyframes sprite-pulse {
     0%, 100% { opacity: 1; }
     50% { opacity: 0.6; }
   }
   @keyframes sprite-flash {
     0% { opacity: 0.6; transform: scale(1.02); }
     100% { opacity: 1; transform: scale(1); }
   }
   @media (prefers-reduced-motion: reduce) {
     .sprite-active, .sprite-fresh {
       animation: none;
       opacity: 1;
     }
     .sprite-pending {
       /* static cue preserved: reduced opacity still communicates
          pending state without motion */
     }
   }
   ```

9. **Asset spec output.** Document the variant key convention so
   that a future asset generation story knows exactly what to
   produce:

   ```
   Asset naming convention:
     {kind}-{state}.png    (e.g. workbench-running.png)
     {kind}.png            (default/idle fallback)

   Required variants for Phase 118:
     workbench.png         (idle, default)
     workbench-pending.png
     workbench-running.png
     workbench-fresh.png
     meeting.png           (idle, default)
     meeting-recording.png
     meeting-paused.png
     artifact.png          (draft, default)
     artifact-final.png
     artifact-pending-review.png
   ```

   Dedicated pixel art assets are a follow-up story. The backbone
   ships with PixiJS tint/opacity fallbacks that make state visually
   distinct without dedicated art.

10. **Placeholder tints for Pixi fallback.** When no variant texture
    is loaded, the renderer applies a PixiJS-level visual cue using
    the base sprite:

    | State | Pixi fallback |
    |-------|---------------|
    | `idle` | No tint (default) |
    | `pending` | Alpha 0.7 |
    | `running` | Alpha pulse (0.6–1.0, 1.5s cycle via ticker) |
    | `fresh` | Green tint (`0x88cc88`) for 500ms, then clear |
    | `recording` | Red tint (`0xcc4444`) |
    | `pending-review` | Alpha 0.7 |

    These tints are temporary — replaced by real assets when they
    ship. But they make sprite states visually provable in the walk
    (HS-118-10) without waiting for art.

11. **Modify components that render primitive icons.** Any component
    that currently renders a primitive's sprite/icon by kind alone
    must now pass through `spriteVariantKey()` and apply the CSS
    hint class. Required renderers (exhaustive audit):
    - World objects (desk canvas sprites) — PixiJS path
    - WorkbenchWindow title bar icon
    - WorkbenchesHomeCore dashboard cards
    - ZoneWindow member list icons
    - SurfaceRow primitive glyphs (used in config panel agent
      picker, zone member lists, grounding chips)
    - DeskTray primitive icons (if applicable)

    Completion criterion: `grep -r "primitive.*icon\|sprite.*kind\|
    glyph.*kind" web/src/` returns zero unhandled call sites.

## What NOT to do

- Do NOT generate dedicated pixel art assets in this story.
  Placeholder tints on the base sprite are sufficient. Dedicated
  variant art is a follow-up story.
- Do NOT store `spriteState` in the database. It's derived from
  runtime data (workbench events, meeting session state) or from
  existing stored fields (artifact status). No new DB columns.
- Do NOT add complex Pixi animation beyond the tint fallbacks
  (alpha pulse, tint flash). Full animated sprite transitions
  (frame-by-frame, morph) are a craft concern for a later story
  after dedicated assets ship.

## Test plan

- `npx tsc --noEmit` — zero type errors.
- `npx vitest run` — new tests:
  - `spriteVariantKey("workbench", "running")` → `"workbench-running"`.
  - `spriteVariantKey("workbench", null)` → `"workbench"`.
  - `spriteVariantKey("workbench", "unknown")` → `"workbench"`.
  - `spriteVariantKey("unknownKind", "idle")` → `"unknownKind"`.
  - Workbench state derivation: pendingCount > 0 → `"pending"`.
  - Workbench state derivation: run_start event → `"running"`.
  - Workbench state derivation: run_complete event → `"fresh"`.
  - Artifact state derivation: status "pending-review" →
    `"pending-review"`.
  - CSS hint class applied to primitive icon elements.
- Visual at 1440: workbench card in WorkbenchesHomeCore shows
  `sprite-active` pulsing class when a run is in progress.
- Reduced motion: animations suppressed with
  `prefers-reduced-motion: reduce`.
