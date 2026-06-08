# HS-53-06 — Closeout: dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 53
- **Status:** not started
- **Depends on:** HS-53-01, HS-53-02, HS-53-03, HS-53-04, HS-53-05
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that the engine computes a source-cited nudge from
real activity, that dismissal sticks, that activity-off yields nothing, and that "dictate
with this" injects the record. Captured as a dogfood, and merged.

## Scope
- **In:**
  - A **dogfood** (no mic/LLM; drive the engine + context path directly): seed activity
    records + a prior meeting -> the engine returns a windowed, source-cited nudge;
    dismiss it -> it does not return; turn activity off -> no nudges; select a record ->
    the dictation context bundle contains it. Print PASS.
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase status
    per the operating cadence; flip the [backlog](../BACKLOG.md) candidate F row to
    shipped; **open a PR to `main`** and merge on green CI.
- **Out:** new feature work.

## Acceptance criteria
- [ ] A green dogfood transcript proving compute-cited-nudge / dismissal-persists /
      activity-off-empty / select-injects-context. (`dogfood-transcript.txt`, RESULT: PASS)
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `cd web && npm run build` clean; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; BACKLOG
      candidate F flipped to shipped; PR to `main` opened and merged on green CI.

## Test plan
- Full suite + the phase dogfood; manual read of the pre-briefing guide.

## Notes / open questions
- Mirror the Phase-51/52 closeout pattern (dogfood script + final-summary + PR + the
  screenshot gallery from HS-53-04 shown in the summary).
