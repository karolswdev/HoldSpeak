# HS-169-05 - The walk on the owner's desk (the door in 5 clicks; the Room's first paint; the stopwatch; OWNER VERDICT — "the first one we are both proud of")

- **Project:** holdspeak
- **Phase:** 169
- **Status:** backlog
- **Depends on:** HS-169-02, HS-169-03
- **Unblocks:** HS-169-07
- **Owner:** unassigned

## Problem

The exit of the phase is the owner's word on his real desk, at both widths, with the stopwatch.

## Scope

- **In:** assets/walk-script.md + tests/e2e/live169_walk.py (HS169_WALK=1; HS169_WALK_DB=isolated|real; build-first; the provider wire timed; NEVER run beside the parallel suite): New Project → outcome → repo → Jira project → Create → the Room's first paint with counts → NEEDS YOU rows real → HISTORY; clicks and seconds recorded and compared with 168's 17 steps; the real leg archives in a finally with unattended OFF before archive and reads the watch rows it left (state, baseline_state, last_error) before calling itself green; then the owner's attended walk and his verdict verbatim.
- **Out:** steward/update legs (167/162 proved them).

## Acceptance criteria

- [ ] Connected desk: 5 clicks to a live Room; counts on first paint; both widths; the transcript in assets/story-05-walk/.
- [ ] The real leg's watch rows: baseline established, last_error empty, no blank entries in any list clause.
- [ ] The owner's verdict recorded verbatim; his PASS is the exit.

## Test plan

`HS169_WALK=1 HS169_WALK_DB=isolated uv run pytest -q tests/e2e/live169_walk.py`, then `HS169_WALK_DB=real` on his desk with the machine otherwise idle.

## Delivered

_(pending)_
