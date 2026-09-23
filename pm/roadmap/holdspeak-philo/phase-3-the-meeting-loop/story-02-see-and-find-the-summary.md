# PHILO-3-02 - See and find the summary

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** the meeting loop
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** A2

## Problem

The central meeting job has no proven completion on the rig, and by source trace the arrival never learns a summary landed: the Chair refreshes once after Run summary (`ChairHome.tsx:756`), only the Live window consumes `intel_complete`/`intel_status` (`LiveCore.tsx:177`), and the drainer emits no `desk_changed`; a retrying job shows QUEUED and FAILED under "Nothing needs you" (`ChairHome.tsx:628,1949`; `intel_queue.py:513`). Import is only ACCEPTED at capture (202, duration 0). Restart retrieval is unverified.

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.face.arrival_run_intel; edge.timer.intel_drainer; edge.cli.restart_hub; states meetings.intelligence.{queued,running,ready,failed}; J4, J5, J6, J7

## Acceptance criteria

- [ ] A COMPLETED import with its length and transcript on the row (the case waits for completion).
- [ ] One Run; the ACTUAL host and the summary text appear on the arrival without a manual refresh; a retrying or failed job reads truthfully with its cause.
- [ ] The same summary is found after a hub restart (the rig's restart step, retained evidence), and the planned host is visible at 393 with nothing covering the control.
- [ ] One synthetic architect meeting with planted decisions, owners and actions is the material; the documented install is reproduced in isolation and its result retained (the model client question, D2) before the owner touches it.
- [ ] Closure evidence: the end-to-end chain on the rig with retained observations at both widths; technical completion and owner usefulness reported separately.

## Effort (council estimate, not a promise)

2–4 days incl. proof repairs (import wait, one-trigger recipe, a lawful failure reply, retained restart evidence)

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
