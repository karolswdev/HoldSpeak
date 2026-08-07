# HS-116-18 — Drop to work

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-02, HS-116-11
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

The fastest way to add work to a workbench is to DROP something on
it. Drag a note from the desk onto a workbench window → it becomes
an item with the note's content as body and the note as grounding.
Drag a meeting → it becomes an item titled with the meeting name,
grounded to that meeting's transcript. Drag an artifact → same
pattern. Lasso three objects and drag them → three items, each
grounded. Drop a file from Finder → the glass drop layer accepts
it and creates an item.

This is the interaction that makes the workbench feel like a DESK —
you pick up your work and put it where the agent can reach it. No
forms, no JSON, no "add item" → "set grounding" → "save." Just
drag and drop.

**Articles served:** I (the Desk is the operating surface — drag
and drop IS the desk interaction), VIII (native-grade craft — drag
and drop is a physics contract), VII (no modals — the drop IS the
create gesture).

**UI/UX direction:** The workbench window is a DROP TARGET. When
you drag a desk object over it, the window shows a drop affordance:
a subtle highlight on the item list area with a "Drop to add" label
in quiet mono. The drop zone covers the entire body of the window
(not just a small area). The existing `GlassDropLayer` already
handles file drops — extend it to recognize workbench windows as
targets.

## Deliverables

1. **Desk object drop.** When a desk object (note, meeting,
   artifact, decision, recipe, any DeskItem) is dragged onto an
   open workbench window:

   | Dropped kind | Item title | Item body | Grounding |
   |-------------|-----------|----------|-----------|
   | note | Note title | Note body (markdown) | note ref |
   | meeting | Meeting title | "" | meeting_id for transcript |
   | artifact | Artifact title | Artifact content preview | artifact ref |
   | decision | Decision title | Decision context | decision ref |
   | recipe | "Configure agent: {name}" | "" | none (opens agent picker) |

   The item is created via POST with the grounding refs already
   set. No intermediate form. The item appears in the list
   immediately with its grounding chips visible.

2. **Multi-object drop.** When multiple objects are selected
   (lasso'd on the desk) and dragged onto a workbench window,
   each selected object becomes its own item. A brief toast shows
   "Added 3 items" in the workbench footer.

3. **File drop.** Extend the GlassDropLayer to recognize workbench
   windows as drop targets for external files. Accepted types
   follow the existing decision table (transcripts, audio, text
   files). A dropped text file becomes an item with the file's
   content as body.

4. **Workbench object as drop target on the desk stage.** Even
   when the workbench WINDOW isn't open — if a workbench is
   visible as an object on the desk stage, dragging a note/meeting
   onto the workbench object creates an item. The workbench object
   shows a drop-ready glow when a dragged object hovers over it.

5. **Drop affordance.** When a draggable object hovers over a
   workbench window or workbench object:
   - The window/object gets a 2px accent border (the forge ember)
   - A quiet mono label appears: "Drop to add"
   - The item list scrolls to the bottom to show where the new
     item will land

6. **Drop-then-speak.** After a drop creates an item, the item
   card auto-expands and the body textarea is focused with the mic
   button pulsing — inviting the owner to say what they want done.
   The agent already has the grounding (the dropped object's
   content). The owner speaks: "summarize this and find the action
   items" → that becomes the item body. Or they just press Enter
   to accept the item as-is (title only, the agent decides what
   to do based on its system prompt). This is the
   DROP → SPEAK → RUN flow: the fastest path from "I have a thing"
   to "the agent is working on it."

7. **Reverse: drag FROM workbench.** A done item's result can be
   dragged OUT of the workbench onto the desk to create an
   artifact. This is the inverse of Keep — a physical drag gesture
   instead of clicking a verb. The dragged result carries the same
   provenance (workbench, item, run, model, egress).

## Test plan

- Visual: drag a note from the desk onto an open workbench window.
  Verify the item appears with the note's title, body, and
  grounding chip.
- Visual: lasso 3 objects, drag onto a workbench. Verify 3 items
  created.
- Visual: drag a note onto a workbench OBJECT on the desk stage
  (window not open). Verify item created, workbench object glows
  on hover.
- Visual: drag a done item's result out of the workbench onto the
  desk. Verify artifact created with provenance.
