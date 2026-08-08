# HS-125-06 — Due and stall semantics

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-02, HS-125-04, HS-125-05
- **Unblocks:** HS-125-07
- **Owner:** unassigned

## The thesis (the bar)

Overdue state must be deterministic from `action_items.due` and
`cadence_loops.due_at`, distinguishing late, unassigned, snoozed, and
closed. Currently, `needs_review` from meeting extraction and genuine
overdue are conflated. Low-confidence extracted items should not be
flagged as overdue until reviewed.

### What changes

1. `FollowThroughService.board()` computes card state from a clear
   precedence:
   - `closed` / `done` → terminal, no lane
   - `snoozed` → excluded from active lanes until snooze expires
   - `needs_review` → Unassigned lane (triage), never Overdue
   - `due < today` and `status=open` and reviewed → Overdue
   - `due <= today + 2d` → Now
   - `due > today + 2d` or no due → Waiting

2. Advancing the clock (in tests) changes only the correct cards.

3. No new tables — this is logic over existing columns.

### What this story does NOT do

- Modify cadence staleness scoring (that has its own semantics).
- Add notification or nudge triggers (future phase).

## Acceptance criteria

1. A `needs_review` action appears in Unassigned, never Overdue.
2. An overdue action with `status=open` and reviewed appears in Overdue.
3. A snoozed action does not appear in active lanes.
4. Advancing time from "due in 3 days" to "due yesterday" moves a
   card from Waiting → Now → Overdue.

## Test plan

- Unit: seed actions with each state, call `board()`, assert lane.
- Unit: time-travel test — advance clock, verify lane transitions.
- Unit: snoozed item excluded from active lanes.
