# HS-48-05 — Closeout — before/after + dogfood + PR

- **Project:** holdspeak
- **Phase:** 48
- **Status:** backlog
- **Depends on:** HS-48-01, HS-48-02, HS-48-03, HS-48-04
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that the learning loop is now visible (a
digest), trustworthy (honest inline counts), and a normal ritual (one-tap
correction), captured as before/after, dogfooded end to end, and merged.

## Scope
- **In:**
  - A **before/after** capture: the old buried Memory/Journal tabs vs. the new
    "What HoldSpeak learned" digest + inline trust signals + one-tap correction
    (real screenshots via the `scripts/screenshot_*.py` pattern).
  - A **dogfood**: seed a few dictations + corrections → call the digest → show the
    honest "learned from N similar" counts → correct one in flow → digest updates.
    Provable without a mic (reuse the stub-runtime / HTTP-driven pattern from
    `scripts/dogfood_project_knowledge.py`).
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase
    status per the operating cadence; **open a PR to `main`** and merge on green CI.
- **Out:** new feature work (HS-48-01..04).

## Acceptance criteria
- [ ] Before/after captured (old vs new surfaces) + a green dogfood transcript.
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `npm run build` ✓; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; PR to
      `main` opened (and merged when CI green).

## Test plan
- Full suite + the phase dogfood; manual walk of the before/after.

## Notes / open questions
- Mirror the Phase-45/47 closeout pattern (dogfood script + before/after evidence +
  final-summary + PR). Reuse the Phase-47 dogfood/screenshot scaffolding as a model.
