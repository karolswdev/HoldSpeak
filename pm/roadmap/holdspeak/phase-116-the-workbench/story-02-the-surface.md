# HS-116-02 — The surface

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-01
- **Unblocks:** HS-116-04, HS-116-05
- **Owner:** unassigned

## The thesis (the bar)

A Workbench opens as a window on the Desk. It shows its agent
(avatar + name), its inference target (RunsOnPicker + egress lamp),
its schedule (next run + enabled toggle), and its items (ordered
list with status, priority, and inline result preview). The surface
uses the Signal Workbench material — same bevels, same keylines,
same tokens as every other desk window. When this ships, the user
can see, configure, and interact with a workbench entirely on-glass.

**Articles served:** I (the Desk is the operating surface — no
eject), II (primitive with derived UI), VII (no prose, no modals —
edit in-world), VIII (native-grade craft — same material as the OS).

## Deliverables

1. **WorkbenchWindow component.** A new desk window component
   registered in `SurfaceWindows.tsx`. Opens from the dock, from a
   desk object double-click, or from a deep link. Layout:
   - **Head:** workbench name (editable inline), agent avatar +
     name, egress lamp.
   - **Toolbar:** RunsOnPicker, schedule indicator (cron human-
     readable + next fire time), enable/disable toggle, manual
     "Run now" verb.
   - **Body:** ordered item list. Each item shows title, priority
     chip, status chip (pending/claimed/done/dismissed), and a
     collapsed result preview (expand to see full agent output +
     receipt).
   - **Footer:** item count, last run timestamp, total tokens
     consumed.

2. **Item interaction.** Click to expand. Inline edit title/body.
   Drag to reorder. Swipe/button to dismiss. Status chips are
   read-only (set by the agent run, not the user — except dismiss).

3. **Workbench object on the desk.** The workbench appears as a
   desk object (icon: the agent's avatar with a workbench badge).
   World rendering follows the existing DeskPrimitive → world
   object pipeline.

4. **Workbench in the dock.** A new dock section or shelf for
   workbenches, alongside existing Speak/Meetings/Agents/Settings
   entries.

5. **Empty state.** A new workbench shows: agent picker, target
   picker, "Add your first item" prompt, and a link to pre-built
   templates (HS-116-05). No prose. No tutorial. Just the
   affordances.

6. **Zustand store slice.** `workbenches` slice in the desk store:
   list of workbenches, selected workbench ID, item CRUD, optimistic
   updates.

## Test plan

- `npx vitest run` — WorkbenchWindow renders, item list renders,
  empty state renders, store slice round-trip.
- Visual: open a workbench window at 1440 and 393. Verify material
  (bevels, keylines, tokens), item list scrolls, agent avatar and
  egress lamp display correctly.
