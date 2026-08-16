# HS-114-02 - Ask AI is a first-class citizen

- **Project:** holdspeak
- **Phase:** 114
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-114-07
- **Owner:** unassigned

## The thesis (the bar)

Ask AI is reachable in one keystroke (Cmd+I), from the floor menu,
from the tools shelf, and from a context verb on every major
primitive type. It opens without requiring a prior lasso selection.
Article II: intelligence must be a DeskPrimitive or an affordance
on one.

## Ground (from the applicability study)

- No `go.ask` verb exists. No keyboard shortcut for Ask AI.
  (`web/src/desk/verbRegistry.ts`, `web/src/desk/keymap.ts`)
- Ask is absent from DESK_TOOLS.
  (`web/src/desk/tools.ts:6-96`)
- Floor Launch menu has Speak, Meetings, Settings — no Ask.
  (`web/src/desk/floorMenu.ts:46-51`)
- "Ask this" context verb exists only for Projects.
  (`web/src/desk/verbRegistry.ts:261-276`)
- AskPanel already IS a DeskWindowFrame; it just lacks entry points.
  (`web/src/desk/components/AskPanel.tsx:299-601`)

## Method

1. **Register `go.ask` verb** in `verbRegistry.ts` with keyboard
   `meta+i`, glyph `ask`, group `go`. Handler calls
   `useDesk.getState().openAsk()`.

2. **Add Ask to DESK_TOOLS** in `tools.ts` alongside Speak,
   Meetings, Settings.

3. **Register `object.ask` verb** for types: note, knowledge,
   recipe, meeting, artifact, workflow. Handler selects the object
   and opens Ask (same pattern as the existing Project verb).

4. **Support empty-context Ask.** `openAsk()` already works without
   selection. The AskPanel already handles empty context (no
   grounding rack, no budget meter). Verify and clean up any
   edge cases.

## Acceptance

- Cmd+I opens Ask AI from any desk state.
- Floor right-click > Launch > Ask AI opens Ask.
- Right-click a Note/Knowledge/Agent/Meeting/Artifact/Workflow >
  "Ask this" opens Ask with that object as context.
- Ask opens cleanly with no prior selection (empty context).
- All existing keymap and verb registry tests passing.

## Test plan

- `npx vitest run src/desk/__tests__/keymap.test.ts`
- `npx vitest run src/desk/__tests__/verbRegistry.test.ts`
- `npx vitest run src/desk/__tests__/floorMenu.test.ts`
- Screenshot walk: Cmd+I, floor menu, context menu on a Note.
