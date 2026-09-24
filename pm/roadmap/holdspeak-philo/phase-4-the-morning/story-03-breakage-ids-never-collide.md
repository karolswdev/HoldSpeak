# PHILO-4-03 - A failure never collides with the next brief

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** the morning in one move
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Closure finding:** Phase 3 final-summary "What he still cannot do" #2

## Problem

Breakage items get a fixed id (`brief-break-pipeline-{event_id}`, `holdspeak/services/monday_brief_service.py:546`; connectors `:575`); the next day's brief inserts the same id again (`:305`) into a table-wide primary key (`holdspeak/db/schema.py:2441`) and answers 500 (`UNIQUE constraint failed: monday_brief_items.id`, run `20260924T012420Z`). The collision needs a failure already stored in an earlier brief to be selected again (selection keeps the latest failure per source over a window from the preceding business close, `:516`, `:145`): a Wednesday-evening failure selected Wednesday evening and again Thursday morning collides; a newly encountered failure need not (Astra, closure check).

## Scope

- **In:** the result below, its fence(s) red pre-fix, the rig case at 1440 and 393.
- **Out:** everything the phase status lists as out.

## Acceptance criteria

- [ ] A lookback containing a breakage item generates the next brief with 200 and carries the breakage row (id scoped to the brief, or the insert idempotent; no schema migration).
- [ ] Fence red pre-fix: two generations across a producer-day advance with one breakage in the lookback; today's code raises IntegrityError.
- [ ] The brief's failure row still names the cause in plain words (Tenet 4).

## Effort (council-style estimate, not a promise)

0.5–1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
