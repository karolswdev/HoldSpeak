# PHILO-3-04 - The thought's receipt

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** the meeting loop
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** A4 (pending the owner's D3)

## Problem

The owner's first gripe (2026-09-20): "the interface to develop a thought is completely unusable. It hides things." The graph confirms the face: typed words reach the store by autosave (`useThoughtNoteWriter.ts:204`, `PATCH /api/thoughts/{id}/working`), but the foot shows KEPT from `filing_status` and never WHEN the newest words were kept (`ThoughtWorkspaceWindow.tsx:484`); there is no Keep verb; "Kept · time" does not exist. Astra's counter-draft holds this is a real cost but not a dependency of the meeting loop (open dissent §4.3).

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.face.thought_editor_fill; edge.route.thoughts_working_patch; state.thoughts.{kept,pending,failed}; J11

## Acceptance criteria

- [ ] The Thought face shows "Kept · HH:MM" bound to the LAST SUCCESSFUL WRITE, with distinct pending and failure states; the filing state stays a separate line.
- [ ] The face is designed on the canvas first (UX-CANON: design before build) and the owner ratifies the canvas.
- [ ] Closure evidence: type → autosave → the receipt with its time on the face and the row in `GET /api/notes`, at both widths; a failed write shows its failure.

## Effort (council estimate, not a promise)

days; a checked canvas first

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
