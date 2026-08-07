# HS-116-04 — The composer

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-02
- **Unblocks:** HS-116-05
- **Owner:** unassigned

## The thesis (the bar)

Items arrive on a workbench through the same input affordances the
Desk already has: voice (mic button), text (inline composer),
grounding (lasso meetings, artifacts, resources), and drag-and-drop
(glass drop layer). The composer lives inside the workbench window —
no modal, no separate screen. When this ships, adding a grounded
work item to a workbench is faster than typing a Jira ticket.

**Articles served:** IV (voice is first-class — the mic is an
affordance of the OS), VII (no modals — compose in-world), II
(grounding uses existing primitives, not a new system).

## Deliverables

1. **Inline composer.** A composer strip at the bottom of the
   workbench window body (above the footer). Text input + mic
   button + grounding picker + "Add" verb. Same interaction pattern
   as the PersonaChat composer, adapted for item creation instead
   of chat turns.

2. **Voice input.** The mic button opens the existing mic session
   (openMic / micSession infrastructure). Transcribed text populates
   the composer. Same VAD, same audio floor, same one-mic-authority
   rule (Article IV.3).

3. **Grounding picker.** The existing grounding picker component
   (meetings, artifacts, resources) attaches context to the item
   being composed. Grounding is stored on the WorkbenchItemRecord
   as JSON, same shape as chat grounding.

4. **Glass drop.** Drag a file onto the workbench window to create
   an item. The glass drop layer (GlassDropLayer) recognizes the
   workbench window as a drop target. Accepted types follow the
   existing decision table (transcripts, audio, text).

5. **Conversational refinement.** After an item is added, the user
   can talk to it — expand the item, use the inline chat affordance
   to refine the title, body, or grounding with the workbench's
   assigned agent. This is a single-turn ask (AskPanel pattern),
   not a persistent thread. The agent sees the item + its grounding
   + constitutional context.

6. **Priority.** Items have a priority (1-5). Default is 3. The
   composer has a priority picker (cycle gadget, not a dropdown).
   Drag-to-reorder in the item list also sets effective priority.

## Test plan

- `npx vitest run` — composer renders inside workbench, item
  creation round-trip, grounding attachment, glass drop acceptance.
- Visual: add an item via text, via voice, via drag-and-drop. Attach
  a meeting as grounding. Verify the item appears with its context.
