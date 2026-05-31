# HS-26-07 — Decomposition Closeout (Size + Regression Evidence)

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-01, HS-26-02, HS-26-03, HS-26-04, HS-26-05, HS-26-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The decomposition needs a closeout that proves the monolith is gone, the API
surface is unchanged, and the suite is green — then writes the phase summary.

## Scope

### In

- Record `web_server.py` line count before/after and the new `routes/` layout.
- Produce a route-inventory diff (pre vs. post) proving identical paths/methods.
- Run `uv run pytest -q --ignore=tests/e2e/test_metal.py`; capture output.
- Re-check every phase exit criterion with evidence links.
- Write `final-summary.md`; freeze `current-phase-status.md`; flip the project
  README phase index (26 → done) and update the current pointer.

### Out

- Any further refactor work.

## Acceptance criteria

- [ ] Before/after `web_server.py` line count recorded; it is a thin assembler.
- [ ] Route-inventory diff shows zero path/method changes across the phase.
- [ ] Full suite output captured and green (or failures named with follow-ups).
- [ ] `final-summary.md` written; `current-phase-status.md` frozen; project
      README updated.

## Test plan

- Unit/integration: full suite per the command above.
- Manual: n/a.

## Notes / open questions

- Generate the route inventory programmatically from the FastAPI app
  (`app.routes`) at both ends so the diff is mechanical, not hand-written.
