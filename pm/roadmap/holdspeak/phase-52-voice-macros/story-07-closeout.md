# HS-52-07 — Closeout: dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-01, HS-52-02, HS-52-03, HS-52-04, HS-52-05, HS-52-06
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that a spoken keyword fires its configured action
through the reused executor, that a normal utterance still dictates byte-identical with
macros off, and that the carve changed no behavior. Captured as a dogfood, and merged.

## Scope
- **In:**
  - A **dogfood** (no real mic; drive the dispatch entry directly): with a configured
    `type_text` or `shell` macro (e.g. an `echo` into a temp file) and an `open_url` macro,
    speaking/feeding the keyword fires the action through `ActuatorExecutor` and records an
    audit row, while a non-keyword utterance dictates unchanged; with macros off the typed
    output is byte-identical. Use injected connectors / a temp target so the dogfood has no
    destructive side effect. Print PASS.
  - **The screenshot gallery** from HS-52-05 (the board with multiple macro kinds, the
    editor, the shell danger treatment) is part of the closeout evidence and shown in
    `final-summary.md` so the surface is reviewable from the PR.
  - Optional: a real-voice e2e behind the existing opt-in pattern (macOS `say` + Whisper,
    like `test_spoken_*`) that says a keyword and asserts the configured action fired. Keep
    it opt-in so CI does not need a mic; note it in the summary either way.
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase status
    per the operating cadence; flip the [backlog](../BACKLOG.md) candidate B row to shipped
    and record that a scoped slice of candidate E (the dispatch-seam carve) landed with it;
    **open a PR to `main`** and merge on green CI.
- **Out:** new feature work; the full `web_runtime` decomposition (candidate E stays a
  watch item).

## Acceptance criteria
- [ ] A green dogfood transcript proving keyword-fires-action (audited) and
      byte-identical-off (plus non-keyword passthrough). (`dogfood-transcript.txt`,
      RESULT: PASS)
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `cd web && npm run build` clean; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; BACKLOG
      candidate B flipped to shipped (E slice noted); PR to `main` opened and merged on
      green CI.

## Test plan
- Full suite + the phase dogfood; manual read of the Voice Commands guide.

## Notes / open questions
- Mirror the Phase-50/51 closeout pattern (dogfood script + final-summary + PR).
- The dogfood must not run a destructive command; use a temp target and/or injected
  connectors. Record in the final summary that full candidate E remains a backlog watch
  item; this phase took only the dispatch slice.
