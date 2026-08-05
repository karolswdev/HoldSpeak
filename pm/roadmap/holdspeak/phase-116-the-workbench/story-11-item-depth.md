# HS-116-11 — Item depth

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-04
- **Unblocks:** HS-116-12, HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

A workbench item is a work card, not a list row. It has visual
weight that communicates its state. Pending items look ready to
work. Running items pulse with life. Done items show their result
with an egress badge. Failed items show what went wrong. The item
surface supports editing in place, attaching grounding, reading
rendered results, and keeping results as desk artifacts. When this
ships, the item list feels like a kanban column — each card is a
self-contained unit of work with everything visible.

**Articles served:** VII (no modals — edit in place), III (egress
badge on every result), II (Keep mints a desk artifact).

**UI/UX direction:** Study DW Phase 36's board cards — story
cards with lanes, status colors, hover lift. The workbench item
cards follow the same material vocabulary: bevel on the card
surface, hairline bottom border, subtle hover elevation. State is
communicated through LEFT BORDER COLOR, not background fills
(background stays the window fill for readability):

| State | Left border | Card feel |
|-------|------------|-----------|
| pending | transparent | Ready, neutral, full opacity |
| claimed | amber, pulsing | Alive — the agent is here |
| done | green | Settled, complete, result visible |
| failed | red | Attention needed, error visible |
| dismissed | none, 50% opacity | Out of the way |

## Deliverables

1. **Item card component.** `WorkbenchItemCard` — a self-contained
   card component used by the item list. Structure:

   ```
   ┌─ left border (state color) ─────────────────────┐
   │ [P1] Fix the auth timeout            [DONE ●]   │
   │                                                   │
   │ (collapsed: 2-line result preview in quiet mono)  │
   │ (expanded ▾):                                     │
   │   ┌─ body ──────────────────────────────────────┐ │
   │   │ The session timeout is set to 30s but       │ │
   │   │ production needs 300s. Check the config...  │ │
   │   └─────────────────────────────────────────────┘ │
   │   ┌─ grounding ────────────────────────────────┐  │
   │   │ [▣ Monday standup] [▣ Auth design doc]     │  │
   │   └─────────────────────────────────────────────┘ │
   │   ┌─ result (only when done/failed) ───────────┐  │
   │   │ ## Analysis                         [LOCAL] │  │
   │   │ The timeout is configured in...             │  │
   │   │                                    [Keep ▸] │  │
   │   └─────────────────────────────────────────────┘ │
   │   [Dismiss] [Remove] [Re-run]                     │
   └───────────────────────────────────────────────────┘
   ```

2. **Inline editing.** Title: `EditInPlace` (click to edit, saves
   on blur). Body: auto-growing `<textarea>` that appears below
   the title when the card is expanded. Saves on blur via PUT.
   Both use the same mono typeface as the rest of the surface.

3. **Per-item grounding.** Each item card has its own grounding
   section (collapsed by default in the expanded view). The owner
   can attach meetings and artifacts to individual items. The
   grounding chips show as compact pills below the body.

4. **Result rendering.** Agent output renders as formatted content
   using the desk's existing text rendering (mono pre-wrap with
   basic markdown: **bold**, headers, lists). Not a full rich
   editor — that's overkill. Just readable formatted text.
   Beside the result: an egress lamp showing the actual placement
   (LOCAL green / LAN amber / CLOUD red) from `result_egress`.

5. **Keep verb.** A "Keep" chip on done items mints the result as
   a desk artifact via the existing `/api/recipes/{id}/keep` or
   `/api/ask/keep` pattern. The artifact appears on the desk with
   provenance (workbench name, item title, run ID, model, egress).

6. **Re-run verb.** A "Re-run" chip resets a done/failed item to
   pending so the next run picks it up again.

7. **Running state animation.** When an item is `claimed`, the
   left border pulses (CSS animation, `@keyframes` with opacity
   oscillation on the amber border). A `LedMeter` with `scanning`
   prop appears below the title. This is the only animation in the
   workbench — intentionally restrained.

8. **Composer body input.** The composer at the bottom gains an
   expandable body textarea. Collapsed by default (just the title
   line). A small disclosure chevron expands it. When expanded: a
   `<textarea rows="3">` below the title input. Body is optional.

## Test plan

- `npx vitest run` — card renders in all 5 states, EditInPlace
  saves, egress lamp shows correct tone, Keep calls the API.
- Visual at 1440: a workbench with items in pending, running,
  done (with result + egress badge), failed, and dismissed states.
  Verify left border colors, LedMeter on running, result
  formatting, and Keep verb.
- Visual at 393: cards stack full-width, result text wraps, verbs
  remain tappable.
