# HS-169-05 - The walk on the owner's desk (the door in 5 clicks; the Room's first paint; the stopwatch; OWNER VERDICT — "the first one we are both proud of")

- **Project:** holdspeak
- **Phase:** 169
- **Status:** in-progress
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

## Delivered (2026-09-05)

- assets/walk-script.md (11 steps, both legs) and tests/e2e/live169_walk.py
  (HS169_WALK=1; HS169_WALK_DB=isolated|real; build-first; the face driven,
  the window shot per step at 1440 + 393; the provider wire timed; the
  viewport probe; identical consecutive shots fail; the real leg's
  finally: unattended OFF before archive, archive, and the watch rows
  READ and printed).
- Isolated leg: 2 passed; 5 clicks at both widths; door-to-Room 11.7 s.
- **The REAL leg on the owner's desk (2026-09-04 19:43 local, both widths,
  alone on the machine): 2 passed; 5 clicks; door-to-Room 24 s at 1440
  (Create itself 14.7 s — real gh + acli baselines); the Room's first paint
  showed `Nothing needs you · ON TRACK`, SOURCES 2 — `KAN · 1 DUE THIS
  WEEK`, `karolswdev/HoldSpeak · 2 OPEN PRS · 2 CHECKS FAILING`; both
  projects archived (proj-22f86af7fb2e, proj-fd894f49bbd3) with every watch
  paused and baseline established; no blank list entries.** 168's walk
  was 17 face steps.
- Found live and paid: `branch_ci` entities without an id (every default
  CI watch would have failed normalize_snapshot); the persisted-snapshot
  shape (dict entities, snake_case) unread by the derivation; the Jira
  host chip carrying the connection ref; sources duplicated per watch;
  the History phrase leaking field names; the door left open behind the
  Room; and a STALE `holdspeak` app process (running since 2026-08-31 on
  pre-169 code) whose conductor evaluated the new CI watches with the
  old dispatcher (`GitHub Watches support pull_requests`) — restarted on
  the current code; law: check the age of every `holdspeak` process
  before a real leg.
- Still to record: the owner's attended walk and his verdict, verbatim.
