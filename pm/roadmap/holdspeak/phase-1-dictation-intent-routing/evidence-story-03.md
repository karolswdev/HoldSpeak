# Evidence — HS-1-03 (Pipeline executor)

**Story:** [story-03-pipeline.md](./story-03-pipeline.md)
**Date:** 2026-04-25
**Status flipped:** in-progress → done

## What shipped

- `holdspeak/plugins/dictation/pipeline.py` — `DictationPipeline`
  ordered executor + `PipelineRun` frozen dataclass. Synchronous,
  in-process, error-isolating per DIR-01 §6.1 / §9.1. The executor
  is I/O-free; the controller (HS-1-07) supplies the structured-log
  emitter via the `on_run` hook.
- `tests/unit/test_dictation_pipeline.py` — 11 cases covering
  `DIR-F-001/002/003/009/011`, `on_run` semantics, hook-exception
  isolation, and deterministic-clock injection.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-F-001` Stages execute in declared order | `test_stages_execute_in_declared_order_and_see_prior_results`, `test_text_threads_through_stages` |
| `DIR-F-002` Pipeline no-op when disabled | `test_disabled_pipeline_is_noop` |
| `DIR-F-003` Stage exception → short-circuit to input text + warning | `test_stage_exception_short_circuits_to_input_text`, `test_stage_exception_warning_is_structured` |
| `DIR-F-009` Last-N introspection ring buffer | `test_recent_runs_ring_buffer_caps_at_n` |
| `DIR-F-011` LLM-disabled skips `requires_llm` stages silently | `test_llm_disabled_skips_requires_llm_stages` |

`DIR-O-001` (structured log line) is intentionally deferred to
HS-1-07; the executor exposes the `on_run` hook the controller will
use to emit it. Documented in story-03 §"Notes / open questions".

## Test output

### Targeted (pipeline only)

```
$ uv run pytest -q tests/unit/test_dictation_pipeline.py
...........                                                              [100%]
11 passed in 0.04s
```

The eleven cases:

1. `test_disabled_pipeline_is_noop` — DIR-F-002.
2. `test_stages_execute_in_declared_order_and_see_prior_results` — DIR-F-001.
3. `test_text_threads_through_stages` — last stage's text becomes `final_text`.
4. `test_stage_exception_short_circuits_to_input_text` — DIR-F-003.
5. `test_stage_exception_warning_is_structured` — `"<stage_id>: <ExcType>: <msg>"`.
6. `test_llm_disabled_skips_requires_llm_stages` — DIR-F-011.
7. `test_intent_propagates_to_pipeline_run` — last non-None `IntentTag` surfaces.
8. `test_recent_runs_ring_buffer_caps_at_n` — DIR-F-009 (capped to N, newest-last).
9. `test_on_run_callback_invoked_after_buffer_append` — hook ordering.
10. `test_on_run_exception_does_not_propagate` — hook errors stay inside the executor.
11. `test_clock_injection_makes_timings_deterministic` — clock seam.

### Full regression

```
$ uv run pytest -q tests/ --timeout=30
...
1 failed, 795 passed, 10 skipped, 3 warnings in 17.46s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

The lone failure is in `tests/e2e/test_metal.py` (the `metal` marker
per `pyproject.toml`: "hardware tests requiring real
mic/model/keyboard"). It exercises Whisper model loading
(`AttributeError: 'Transcriber' object has no attribute
'_path_or_hf_repo'`) — a pre-existing hardware/environment failure
unrelated to the pipeline executor.

For comparison, HS-1-02's evidence sweep recorded **2** metal-class
fails (mic + Whisper); the mic test now passes. Test count delta:
`+11` new pipeline cases (783 → 795 passed; the difference of 12
splits as +11 new tests + the now-passing mic test, vs. one fewer
metal-class failure).

## Files in this commit

- `holdspeak/plugins/dictation/pipeline.py` (new)
- `tests/unit/test_dictation_pipeline.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-03-pipeline.md` (new — story authored, status flipped to done in same commit, acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-03.md` (this file)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- The story file was authored fresh in this commit (it was a stub
  row before). It moves through `backlog → in-progress → done` in a
  single commit, which is unusual but compliant — the commit ships
  the implementation, the tests, and the evidence in one atomic
  chunk per the operating cadence. PMO §6 is satisfied: status `done`
  + matching `evidence-story-03.md` are both staged.
- `max_total_latency_ms` (§9.4) is not enforced in the executor by
  design — see story §"Notes / open questions". The controller (HS-1-07)
  applies the policy; the executor exposes `total_elapsed_ms`.
