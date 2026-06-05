# Evidence — HS-39-01 — Multi-pass rewriting

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `holdspeak/config.py` — added `rewrite_passes: int = 1` to
  `DictationPipelineConfig` + `_MAX_REWRITE_PASSES = 5`; `__post_init__`
  rejects out-of-range values with `DictationConfigError`.
- `holdspeak/plugins/dictation/builtin/project_rewriter.py` — added
  `_default_refine_prompt_builder`, `_invalid_draft_reason`, and
  `_INVALID_DRAFT_WARNINGS`; `ProjectRewriter.__init__` gained
  `rewrite_passes` / `refine_prompt_builder` / `latency_budget_ms` / `clock`;
  `run()` is now a draft→critique→refine loop with a latency-budget gate,
  fail-open-to-best-draft on a refine failure, and new per-pass metadata.
  `_noop` uses the injected clock.
- `holdspeak/plugins/dictation/assembly.py` — `build_pipeline` constructs
  `ProjectRewriter` with `rewrite_passes=cfg.pipeline.rewrite_passes` and
  `latency_budget_ms=float(cfg.pipeline.max_total_latency_ms)`.
- `tests/unit/test_dictation_project_rewriter.py` — 5 new tests
  (single-pass byte-identical, multi-pass refines prior draft, budget-skip,
  refine-failure-keeps-best, refine-empty-keeps-best) + `_DraftThenFailRuntime`
  / `_FakeClock` helpers.
- `tests/unit/test_config.py` — 4 new `TestDictationPipelineValidation` cases
  (default 1, in-range accepted, below-1 rejected, above-cap rejected).

## Verification artifacts

- Targeted (rewriter + assembly + config validation):
  `uv run pytest -q tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_assembly.py tests/unit/test_config.py::TestDictationPipelineValidation`
  → `24 passed in 0.09s`.
- Dictation unit suite: `uv run pytest -q tests/unit -k dictation`
  → `169 passed, 1 skipped, 1581 deselected` (skip = `llama_cpp` not installed).
- Dictation integration: `uv run pytest -q tests/integration -k dictation`
  → `71 passed, 1 skipped, 301 deselected` (skip = local GGUF model absent).
- Ruff (touched files):
  `uv run ruff check holdspeak/config.py holdspeak/plugins/dictation/builtin/project_rewriter.py holdspeak/plugins/dictation/assembly.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_config.py`
  → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2132 passed, 15 skipped in 61.84s` (was 2123/15 at Phase 38 close; +9).

## Acceptance criteria — re-checked

- [x] `rewrite_passes` exists, defaults to 1, validated 1–5; out-of-range →
      `DictationConfigError` — `TestDictationPipelineValidation` (4 cases).
- [x] `rewrite_passes=1` ⇒ exactly one rewrite call, output byte-identical —
      `test_project_rewriter_single_pass_is_byte_identical`.
- [x] `rewrite_passes=2` ⇒ a refine call with the prior draft in the prompt;
      the refined text propagates — `test_project_rewriter_multi_pass_refines_prior_draft`.
- [x] An extra pass that would breach `max_total_latency_ms` is skipped, the
      best draft is kept, a warning is recorded —
      `test_project_rewriter_skips_extra_pass_over_budget`.
- [x] Per-pass metadata (`rewrite_passes_configured`/`rewrite_passes_run`/
      `rewrite_pass_ms`/`rewrite_budget_skipped`) is on `StageResult.metadata`;
      `_serialize_stage_result` passes stage metadata through verbatim, so the
      dry-run exposes it.
- [x] Draft-pass failure short-circuits to input (unchanged); refine-pass
      failure / empty / over-budget falls open to the best draft —
      `test_project_rewriter_refine_failure_keeps_best_draft`,
      `test_project_rewriter_refine_empty_keeps_best_draft`.
- [x] Default suite green; pipeline-disabled path untouched; no real
      LLM/network call (all rewriter tests use injected fake runtimes).

## Deviations from plan

- The original acceptance criterion "any rewrite failure on any pass
  short-circuits to the input text" was **refined during implementation** to
  "draft-pass failure → input; refine-pass failure → best draft so far." This
  is strictly safer: enabling multi-pass can no longer make a given utterance's
  output worse than single-pass. Recorded in the phase "Decisions made".

## Follow-ups

- HS-39-05 (depth telemetry) will surface the new per-pass metadata as p50/p95
  + budget guidance on `/api/dictation/readiness`. No change needed here; the
  data is already on the `StageResult`.
- A real `.43`-endpoint warm 2-pass latency check is deferred to the HS-39-07
  dogfood (no measurement gate this story, per project posture).
