# HS-125-04 — Aftercare triage queue

- **Project:** holdspeak
- **Phase:** 125
- **Status:** backlog
- **Depends on:** HS-125-02
- **Unblocks:** HS-125-06
- **Owner:** unassigned

## The thesis (the bar)

`MeetingAftercareService.get_aftercare()` rolls up open actions,
decisions, deltas, and transcript provenance. But there is no review
gate: a meeting can close with ownerless, undated, or pending-review
actions that silently go dark. This story adds an explicit triage
queue to aftercare.

### What changes

1. `MeetingAftercareService.get_aftercare()` gains a `triage` section
   in its return value: a list of actions that are pending-review,
   ownerless, or undated.
2. Each triage item includes the action, its source (meeting segment
   if available), and the specific gap (no owner, no date, needs
   review).
3. The triage list is computed from existing `action_items` joined
   with `review_state` — no new tables.

### What this story does NOT do

- Block meeting close on triage (that's a policy decision).
- Create new action items — only surfaces existing gaps.
- Build the Desk surface (HS-125-09).

## Acceptance criteria

1. `get_aftercare()` includes a `triage` list of ownerless, undated,
   and pending-review actions.
2. An action with owner + due date + reviewed status does not appear
   in triage.
3. An ownerless action appears in triage with gap = "no_owner".
4. Triage is empty when all actions are fully specified.

## Test plan

- Unit: create a meeting with mixed actions (some ownerless, some
  undated), call `get_aftercare()`, assert triage contents.
- Unit: all actions fully specified, triage is empty.
