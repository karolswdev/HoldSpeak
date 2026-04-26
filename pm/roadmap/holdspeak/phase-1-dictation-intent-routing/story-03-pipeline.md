# HS-1-03 — Step 2: Pipeline executor

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-02 (contracts)
- **Unblocks:** HS-1-04 (runtime — pipeline is the consumer of `classify`), HS-1-06 (built-in stages plug into the executor), HS-1-07 (controller wiring)
- **Owner:** unassigned

## Problem

DIR-01 §6.1 declares the dictation pipeline as a **single in-process,
synchronous, ordered chain** of `Transducer` stages between
`TextProcessor.process` and `TextTyper.type_text`. The contracts
(HS-1-02) describe *what* a stage looks like; this story builds *the
thing that runs them*.

Per spec §6.1: "Failure of any stage MUST short-circuit to the original
(post-`TextProcessor`) text and emit a structured warning. The
pipeline is invoked iff `dictation.pipeline.enabled = true` in
config." Per §9.1:

- `DIR-F-001` Stages execute in declared order.
- `DIR-F-002` Pipeline is a no-op when disabled.
- `DIR-F-003` Any stage exception MUST short-circuit to the input
  text; the original utterance is always typeable.
- `DIR-F-009` Pipeline MUST capture per-stage `StageResult` for the
  most recent N utterances (default N=20).
- `DIR-F-011` Disabling the LLM runtime MUST cause `requires_llm`
  stages to be skipped (not error) and downstream stages to receive
  `IntentTag.matched=false`.

Per §9.7 (`DIR-O-001`): each pipeline run emits a structured log line
with stage IDs, elapsed_ms per stage, intent tag, and warnings.

This story lands the executor, its in-memory ring buffer, and the
unit tests covering the requirements above. It does **not** land the
LLM runtime, any concrete `Transducer`, the block loader, the
controller wiring, or the structured-log line's wire-up beyond a
documented hook (a single emitter callback the controller will pass
in HS-1-07).

## Scope

- **In:**
  - `holdspeak/plugins/dictation/pipeline.py`:
    - `PipelineRun` (frozen dataclass) — one full run's record:
      `final_text`, `stage_results: list[StageResult]`, `intent:
      IntentTag | None` (the last non-None intent set by any stage),
      `warnings: list[str]`, `total_elapsed_ms`, `short_circuited:
      bool`.
    - `DictationPipeline` — the executor.
      - Constructor:
        `DictationPipeline(stages: Sequence[Transducer], *, enabled:
        bool = True, llm_enabled: bool = True, ring_buffer_size: int =
        20, on_run: Callable[[PipelineRun], None] | None = None,
        clock: Callable[[], float] | None = None)`.
      - `run(utt: Utterance) -> PipelineRun`. Always returns a
        `PipelineRun`; never raises out to the caller.
      - When `enabled=False`: returns a `PipelineRun` with
        `final_text == utt.raw_text`, empty `stage_results`,
        `short_circuited=True`, no warnings, and does **not** call
        `on_run`. (DIR-F-002.)
      - When `llm_enabled=False`: stages with `requires_llm=True` are
        skipped silently — they do not appear in `stage_results` and
        their absence is recorded as a warning on the run, not on a
        synthesized result. Downstream stages still see the prior
        list. (DIR-F-011.)
      - On a stage exception: catch, append the exception to the
        run's warnings as a structured string
        (`"<stage_id>: <ExcType>: <msg>"`), set
        `short_circuited=True`, stop iterating, and return with
        `final_text` rolled back to `utt.raw_text` (the
        post-`TextProcessor` input). Stages that already succeeded
        before the failing one are kept in `stage_results` for
        introspection but are not allowed to influence `final_text`.
        (DIR-F-003.)
      - Per-stage timing uses the injected `clock` (defaults to
        `time.perf_counter`) so tests can assert deterministic
        `elapsed_ms` values.
      - Successful runs append to the ring buffer
        (`collections.deque(maxlen=N)`); short-circuited runs append
        too (the failure trace is itself worth introspecting). The
        public read accessor is `recent_runs() -> list[PipelineRun]`
        (newest last, copied — the deque is internal).
      - `on_run`, if provided, is called once per run with the
        finalized `PipelineRun`, and is called *after* the run is
        appended to the ring buffer. Exceptions raised by `on_run`
        are swallowed and added as a warning; the executor never
        propagates them.
  - `tests/unit/test_dictation_pipeline.py` covering
    `DIR-F-001/002/003/009/011`, the `on_run` hook, and the
    deterministic-clock contract.
- **Out:**
  - The structured log line itself (DIR-O-001) — wired in HS-1-07
    via `on_run`. This story exposes the hook; it does not write to
    `logging`.
  - `DictationPipelineConfig` in `holdspeak/config.py` — HS-1-04 lands
    config; this story takes plain constructor kwargs.
  - The LLM runtime, blocks, built-in stages, controller wiring, CLI,
    doctor checks.
  - `max_total_latency_ms` enforcement (`DIR-R-003` cold-start
    short-circuit) — that's a runtime-level concern; the pipeline
    surfaces total elapsed but does not make policy decisions about
    it in DIR-01's first executor cut. If HS-1-07 needs it, it can
    be wrapped on the controller side.

## Acceptance criteria

- [x] `holdspeak/plugins/dictation/pipeline.py` exists with
      `PipelineRun` (frozen dataclass) and `DictationPipeline` exactly
      as described in Scope.
- [x] `DictationPipeline.run` never raises out of the executor for any
      input it accepts. Stage exceptions are captured and surface as
      warnings on the returned `PipelineRun`.
- [x] Disabled pipeline (`enabled=False`) returns a no-op
      `PipelineRun` with `final_text == utt.raw_text` and empty
      `stage_results`, and does not invoke `on_run`.
- [x] LLM-disabled mode skips stages where `requires_llm=True`
      silently and records a single per-skip warning on the run.
- [x] Stages execute in the order passed to the constructor; the
      `prior` arg seen by stage *k* contains exactly the `k`
      preceding `StageResult`s in execution order.
- [x] On stage failure: subsequent stages do not run;
      `final_text == utt.raw_text`; `short_circuited=True`;
      `warnings` contains a structured `"<stage_id>:
      <ExcType>: <msg>"` entry.
- [x] `recent_runs()` is bounded by `ring_buffer_size` (default 20)
      and returns runs newest-last.
- [x] `on_run` is called exactly once per run with the final
      `PipelineRun`, after the ring-buffer append; an exception in
      `on_run` is captured as a warning and does not propagate.
- [x] `tests/unit/test_dictation_pipeline.py` exists; `uv run pytest
      -q tests/unit/test_dictation_pipeline.py` passes (11/11).
- [x] Full regression: `uv run pytest -q tests/` — 795 passed, 10
      skipped, 1 pre-existing hardware-only fail in
      `tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads`
      (Whisper model load); unrelated to this story.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_dictation_pipeline.py` —
  cases (one per acceptance criterion or DIR requirement):
  1. `test_disabled_pipeline_is_noop` (DIR-F-002).
  2. `test_stages_execute_in_declared_order_and_see_prior_results`
     (DIR-F-001).
  3. `test_text_threads_through_stages` — last stage's `text` is the
     run's `final_text` on the happy path.
  4. `test_stage_exception_short_circuits_to_input_text` (DIR-F-003).
  5. `test_stage_exception_warning_is_structured`.
  6. `test_llm_disabled_skips_requires_llm_stages` (DIR-F-011).
  7. `test_intent_propagates_to_pipeline_run` — last non-None
     `IntentTag` set by any stage surfaces on `PipelineRun.intent`.
  8. `test_recent_runs_ring_buffer_caps_at_n` (DIR-F-009).
  9. `test_on_run_callback_invoked_after_buffer_append`.
  10. `test_on_run_exception_does_not_propagate`.
  11. `test_clock_injection_makes_timings_deterministic`.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** `python -c "from holdspeak.plugins.dictation.pipeline
  import DictationPipeline, PipelineRun; print('ok')"`.

## Notes / open questions

- The `on_run` hook is the seam through which HS-1-07 will emit the
  `DIR-O-001` structured log line and HS-1-04 will hook telemetry
  counters. Keeping the executor I/O-free (no `logging` calls of its
  own) keeps the unit tests pure and lets the controller decide on
  log format/destination. This is intentional and called out so a
  future reviewer doesn't add a default logger here.
- The ring buffer captures short-circuited runs too. The introspection
  surface (DIR-F-009 / `dictation dry-run`) is more useful with
  failures visible than with them silently dropped.
- `max_total_latency_ms` (config in §9.4) is documented in spec but
  enforced policy-side, not executor-side, in DIR-01. Adding a hard
  cap here would force the executor to make a policy decision about
  what "exceeded" means (cancel? warn? disable for the session per
  `DIR-R-003`) — that decision lives at the controller. The executor
  exposes `total_elapsed_ms` so the policy layer can act.
