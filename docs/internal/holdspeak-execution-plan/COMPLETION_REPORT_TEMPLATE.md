# Completion report template

**Shared reference for the current [ordered plan](EXECUTION_INDEX.md). Detailed planning is authorized; this document grants no repository execution or shipping permission.**
Copy this into your task response or authorized handover. Do not manufacture a repository dossier, change `pm/roadmap/`, or add process artifacts just to satisfy the template. Maintain `pm/STATUS.md` only at the point the repository workflow/assignment authorizes.

## Identity and outcome

- Task ID and linked story/epic:
- Accepted local behavior decision and source of that decision (or pending):
- Outcome: built / already satisfied / discovery complete / partial / blocked
- Checkout, worktree and branch:
- Starting SHA and final tested SHA or uncommitted diff identity:
- Authorized scope and shipping status: no ship / held for SHIP / separately authorized action

## What changed

- Exact paths and public contract changes:
- Why this meets the task's target:
- Prerequisites checked and bounded decisions made:
- Invariants checked by ID:
- Out-of-scope files untouched; explain any approved exception:

## Proof

For each test: exact command, collected tests, exit status, collection output location, run tail location, and what boundary it exercised. Distinguish source inspection from execution.

- Focused test results:
- Actual stored-state assertions:
- Quick check result and log path; confirm the Desk sweep ran rather than skipped:
- UI shots at 1440 and 393, and narrow-window-on-wide-Desk when relevant:
- Live provider/device work: not run unless separately authorized; name any authorized target/run:
- Owner visual acceptance: obtained / not obtained / not applicable; never infer from green tests:

## Risks and handoff

- Remaining unknowns or failing baseline (named, not hidden):
- Rollback boundary and compatibility considerations:
- Follow-up task IDs unlocked:
- Decisions needing authorization or owner input:
- Push/PR/merge/deploy performed only if authorized, with actual result; otherwise say not performed:

For a blocker provide **action, target, reason, completed work, and status (denied / pending / uncertain)**. Check uncertain action outcome before retrying. Do not clean another worker's tree to clear a blocker.
