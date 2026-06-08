# HS-52-01 — Carve the dictation-dispatch seam out of `web_runtime` (scoped E)

- **Project:** holdspeak
- **Phase:** 52
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-52-02, HS-52-03, HS-52-04, HS-52-05, HS-52-06, HS-52-07
- **Owner:** unassigned

## Problem
After a dictation capture, the flow runs inline inside the 2,341-line `web_runtime.py`
god-object: transcription (`:1588`), text processing (`:1599`), then
`_maybe_run_dictation_pipeline` (`:1720-1825`), then typing. The voice-command dispatch
decision ("is this a configured keyword? fire the action; else dictate") needs a clean
home. Carve the seam first so the feature lands clean, not deeper in the god-object.

## Scope
- **In:**
  - Extract the dictation orchestration (roughly `web_runtime.py:1720-1825` plus its
    direct collaborators) into a dedicated, unit-testable module, e.g.
    `holdspeak/dictation_runtime.py`, with a clear entry (a function or small class).
    `web_runtime` delegates to it at the existing call site (`:1607`).
  - The module's entry is the natural place for the later dispatch branch (HS-52-04) to
    sit at the top, before the pipeline. This story only creates the seam; it adds no
    dispatch logic.
  - Behavior byte-identical: no change to what is typed, journaled, or broadcast.
- **Out:** any feature; the dispatch branch (HS-52-04); decomposing anything in
  `web_runtime` beyond the dictation path.

## Acceptance criteria
- [x] The dictation orchestration lives in its own module; `web_runtime` delegates to it;
      the god-object shrinks by the moved region. (`holdspeak/dictation_runner.py`
      `run_dictation_pipeline`; `web_runtime.py` 2341 -> 2255 lines, the method is now a
      thin delegate)
- [x] Typed output byte-identical: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      -> 2460 passed, 17 skipped (was 2454; +6 is the new unit tests, no behavioral edits).
- [x] A unit test calls the extracted entry directly and asserts the same result the
      inline path produced. (`tests/unit/test_dictation_runner.py`: disabled/no-config/
      error/not-loaded return the text unchanged, happy path returns `final_text`, and the
      `WebRuntime` method delegates)
- [x] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- Full suite (the existing dictation integration/e2e tests are the byte-identical guard)
  plus the new focused unit test on the extracted module.

## Notes / open questions
- Keep the extraction mechanical: move the logic, keep inputs/outputs, do not "improve"
  behavior here. This is the scoped-E slice; do not pull in unrelated `web_runtime`
  responsibilities (full E stays a backlog watch item).
