# PHILO-3-01 - Record the decision

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** the meeting loop
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** A1

## Problem

The owner cannot record a decision on the desk: `POST /api/decisions` answers 500 because the route factory deletes `ctx` at `holdspeak/web/routes/primitives/decisions.py:20` and its `_svc` closure reads it at `:27` (since aa865f57). Both live passes, both widths. Without a decision there is no decision-backed brief.

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.route.decisions_create; state.briefs.populated (setup); J10 populated/shelf

## Acceptance criteria

- [ ] The existing decision face saves a decision from the reviewed meeting and reopens it; a create/read failure is NAMED on the face.
- [ ] A fence POSTs a decision through the real route and reads it back (id, text, source); a second fence proves the pre-fix 500.
- [ ] Closure evidence: face create → exact id/text/source read back → reopen after a reload, at 1440 and 393; the shelf is exercised separately before any claim about it.

## Effort (council estimate, not a promise)

hours for the route; up to a day for the face path

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
