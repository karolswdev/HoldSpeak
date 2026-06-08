# HS-52-01 — Carve the dictation-execution seam out of `web_runtime` (scoped E)

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** none
- **Unblocks:** HS-52-02, HS-52-03, HS-52-04, HS-52-05, HS-52-06, HS-52-07
- **Owner:** unassigned

## Problem
The dictation orchestration runs inline inside the 2,341-line `web_runtime.py`
god-object: `_maybe_run_dictation_pipeline` (`web_runtime.py:1720-1825`) reads config,
builds the pipeline, injects corrections, runs it, journals, and returns the text to
type. Every part of this phase (a new stage, its config, its runtime signal) would
otherwise land deeper in that object. Carve the seam first so the feature lands clean.

## Scope
- **In:**
  - Extract the dictation-execution orchestration (roughly `web_runtime.py:1720-1825`
    plus its direct collaborators) into a dedicated, unit-testable module, e.g.
    `holdspeak/dictation_runtime.py`, with a clear entry such as
    `run_dictation(text, *, runtime, config, ...) -> str` (or a small `DictationExecutor`
    class). `web_runtime` calls into it at the existing call site (`:1607`).
  - Behavior byte-identical: no change to what gets typed, journaled, or broadcast. The
    full suite passes with no test changes beyond the move.
  - A focused unit test exercising the extracted entry directly (so the seam is testable
    in isolation, which it is not today).
- **Out:** any feature (the macro stage is HS-52-03); decomposing anything in
  `web_runtime` beyond the dictation path (hotkey/device/meeting/activity stay).

## Acceptance criteria
- [ ] The dictation orchestration lives in its own module; `web_runtime` delegates to
      it; the god-object shrinks by the moved region.
- [ ] Typed output byte-identical: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green with no behavioral test edits.
- [ ] A unit test calls the extracted entry directly and asserts the same result the
      inline path produced.
- [ ] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- Full suite (the existing dictation integration/e2e tests are the byte-identical
  guard); plus the new focused unit test on the extracted module.

## Notes / open questions
- Keep the extraction mechanical: move the logic, keep the same inputs/outputs, do not
  "improve" behavior in the same story. Any cleanup beyond the move is a follow-up.
- This is the scoped-E slice. Do NOT pull in unrelated `web_runtime` responsibilities;
  full decomposition stays a backlog "watch" item.
