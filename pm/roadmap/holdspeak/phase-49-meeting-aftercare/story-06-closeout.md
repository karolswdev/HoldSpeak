# HS-49-06 — Closeout — before/after + dogfood + PR

- **Project:** holdspeak
- **Phase:** 49
- **Status:** backlog
- **Depends on:** HS-49-01, HS-49-02, HS-49-03, HS-49-04, HS-49-05
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that the meeting result now closes loops
(open/decided/changed surfaced, the moment jump, accepted actions filed via the
human-approved actuator flow, a copyable follow-up), captured as before/after,
dogfooded end to end, and merged.

## Scope
- **In:**
  - A **before/after** capture: the old artifact-only meeting view vs. the new
    aftercare surface (open/decided/changed + the moment jump + accept-to-issue +
    follow-up draft). Real screenshots via the `scripts/screenshot_*.py` pattern
    (boot a real server over a seeded temp DB, no mic/LLM).
  - A **dogfood**: seed two meetings (prior + current) with decisions + action
    items -> call the aftercare aggregation -> show what's open / decided / changed
    -> accept an action -> create a proposal (stub connector) -> approve -> it
    executes + is audited -> generate the follow-up draft. Provable without a mic
    (reuse the HTTP-driven `TestClient` + stub-connector pattern).
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase
    status per the operating cadence; **open a PR to `main`** and merge on green CI.
- **Out:** new feature work (HS-49-01..05).

## Acceptance criteria
- [ ] Before/after captured (old vs new surfaces) + a green dogfood transcript.
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `npm run build` ✓; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated;
      the [backlog](../BACKLOG.md) row for candidate A flipped to shipped; PR to
      `main` opened (and merged when CI green).

## Test plan
- Full suite + the phase dogfood; manual walk of the before/after.

## Notes / open questions
- Mirror the Phase-45/47/48 closeout pattern (dogfood script + before/after
  evidence + final-summary + PR). Reuse the Phase-48 dogfood/screenshot scaffolding
  as a model.
- Remember to update `pm/roadmap/holdspeak/BACKLOG.md` (candidate A -> shipped) so
  the living backlog stays accurate.
