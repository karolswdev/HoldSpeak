# HS-52-07 — Closeout: dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-01, HS-52-02, HS-52-03, HS-52-04, HS-52-05, HS-52-06
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that a spoken command yields a deterministic
action, that normal dictation is byte-identical with macros off, and that the carve did
not change behavior. Captured as a dogfood, and merged.

## Scope
- **In:**
  - A **dogfood** proving both paths (no real mic required; drive the dictation entry
    directly): with macros off, a normal utterance types byte-identical text; with macros
    on, a built-in command (e.g. "new paragraph") yields its deterministic action and
    short-circuits the LLM, while a non-command utterance still flows through the rewrite
    unchanged. Print PASS.
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase
    status per the operating cadence; flip the [backlog](../BACKLOG.md) candidate B row to
    shipped and record that a scoped slice of candidate E (the dictation-seam carve)
    landed with it; **open a PR to `main`** and merge on green CI.
- **Out:** new feature work; the full `web_runtime` decomposition (candidate E stays a
  watch item).

## Acceptance criteria
- [ ] A green dogfood transcript proving deterministic-command-on and
      byte-identical-off (plus non-command passthrough). (`dogfood-transcript.txt`,
      RESULT: PASS)
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `cd web && npm run build` clean; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; BACKLOG
      candidate B flipped to shipped (E slice noted); PR to `main` opened and merged on
      green CI.

## Test plan
- Full suite + the phase dogfood; manual read of the Voice Macros guide.

## Notes / open questions
- Mirror the Phase-50/51 closeout pattern (dogfood script + final-summary + PR).
- Record in the final summary that full candidate E (the `web_runtime` decomposition)
  remains a backlog "watch" item; this phase took only the dictation slice.
