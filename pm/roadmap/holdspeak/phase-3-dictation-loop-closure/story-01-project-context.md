# HS-3-01 — Project-context plumbing into `Utterance`

- **Project:** holdspeak
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HS-2-11 (MIR-01 closed; phase-3 scaffold landed)
- **Unblocks:** HS-3-02 (llama_cpp leg can verify project context flowing); the kb-enricher (HS-1-06) becoming live in dogfood
- **Owner:** unassigned

## Problem

`Utterance.project` exists in the dictation contract
(`holdspeak/plugins/dictation/contracts.py:29`) and the kb-enricher
stage (`holdspeak/plugins/dictation/builtin/kb_enricher.py`) reads
off it, but no Utterance constructor populates it: both call sites
hard-code `project=None` (`holdspeak/controller.py:265`,
`holdspeak/commands/dictation.py:89`). The kb-enricher therefore has
nothing to enrich — the entire DIR-01 block-grounded path is inert
in dogfood. This story wires `holdspeak/plugins/project_detector.py`
output into both call sites so blocks earn their keep.

## Scope

- **In:**
  - Add a `detect_project()` (or equivalent) call at both Utterance construction sites; pass the result through to `Utterance.project`.
  - Cache project-context detection across utterances when the cwd hasn't changed (cheap memoization keyed on cwd + mtime of project markers); no new module required if the existing detector is already idempotent.
  - Integration test exercising the controller path end-to-end: feed a synthetic transcript, assert the pipeline's `Utterance.project` is non-None and contains the expected detector keys.
  - Integration test for the CLI path (`holdspeak dictate ...`): same shape.
  - Doctor check (or extension of an existing one) reporting whether project context is being detected from the current cwd.
- **Out:**
  - Narrowing `ProjectContext` from `dict[str, Any]` to a dataclass — DIR-01 §6.4 explicitly leaves the loose typing for kb-enricher's benefit.
  - New project-detector heuristics. The detector is HS-1-06 territory; this story consumes it as-is.
  - Web/UI surfacing of project context.

## Acceptance criteria

- [ ] `holdspeak/controller.py` and `holdspeak/commands/dictation.py` both populate `Utterance.project` from `project_detector` output (no more hard-coded `None`).
- [ ] An integration test in `tests/integration/` constructs an Utterance via the controller path and asserts `utt.project is not None` with at least the expected detector keys present.
- [ ] An integration test for the CLI path asserts the same.
- [ ] `holdspeak doctor` reports project-context detection status for the current cwd (loaded | unavailable | error).
- [ ] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.

## Test plan

- **Unit:** any new helper (e.g., the cache wrapper) gets a unit test.
- **Integration:** the two end-to-end tests above.
- **Regression:** the documented full-suite command (metal excluded per standing memory).

## Notes / open questions

- The detection cache is a perf concern only if `detect_project` does file I/O on every utterance. Verify before adding the cache; if it's already cheap, skip the cache and document why in evidence.
- The doctor extension may be a sub-check on an existing `Project context` check (if one exists) or a new check in `holdspeak/commands/doctor.py`. Decide at implementation time.
