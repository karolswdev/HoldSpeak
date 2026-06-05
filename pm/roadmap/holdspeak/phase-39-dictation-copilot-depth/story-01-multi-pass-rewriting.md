# HS-39-01 — Multi-pass rewriting

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-39-05
- **Owner:** unassigned

## Problem

`ProjectRewriter` is **single-pass**: `run()` makes exactly one
`runtime.rewrite(prompt, …)` call and types the result
(`holdspeak/plugins/dictation/builtin/project_rewriter.py`). For high-stakes
coding-agent prompts (`claude_code` / `codex_cli` targets) a single freeform
pass can be uneven — a draft that a second "tighten and correct" pass would
materially improve. There is no way to ask the model to refine its own output
within the latency budget.

## Scope

- In:
  - A `rewrite_passes: int = 1` field on `DictationPipelineConfig`
    (`holdspeak/config.py`). Default `1` ⇒ **byte-identical** to today.
  - A refine loop in `ProjectRewriter.run()`: pass 1 = the current draft;
    passes 2..N = a self-critique/refine call (`draft → critique → refined`)
    reusing `runtime.rewrite(...)` with the prior output + a critique
    directive in the prompt.
  - **Latency-budget awareness:** before each extra pass, check the elapsed
    pipeline budget against `max_total_latency_ms`; skip the remaining passes
    (keep the best draft so far) and emit a `StageResult` warning if a pass
    would breach it.
  - Per-pass attribution in the `StageResult.metadata` (each pass's
    `elapsed_ms` + a short label) so the dry-run surface can show it.
- Out:
  - Constrained/structured decoding for the rewrite (it stays freeform).
  - Changing the intent-router or kb-enricher stages.
  - A web UI for tuning passes (config + dry-run only this story; richer
    surfacing is HS-39-05).

## Acceptance criteria

- [x] `DictationPipelineConfig.rewrite_passes` exists, defaults to `1`, and is
      validated (`1 <= passes <= 5`); an out-of-range value raises
      `DictationConfigError` at config load. — `config.py`,
      `test_config.py::TestDictationPipelineValidation`.
- [x] With `rewrite_passes=1`, `ProjectRewriter.run()` makes exactly one
      `runtime.rewrite` call and produces output byte-identical to pre-story
      (asserted against a fixed fake runtime). —
      `test_project_rewriter_single_pass_is_byte_identical`.
- [x] With `rewrite_passes=2`, a second refine call is made with the first
      draft in the prompt; the refined text is what propagates downstream. —
      `test_project_rewriter_multi_pass_refines_prior_draft`.
- [x] When an extra pass would push elapsed time past `max_total_latency_ms`,
      the pass is skipped, the best-so-far draft is kept, and a warning is
      recorded on the `StageResult`. —
      `test_project_rewriter_skips_extra_pass_over_budget`.
- [x] `StageResult.metadata` carries per-pass timing + counts
      (`rewrite_passes_configured` / `rewrite_passes_run` / `rewrite_pass_ms` /
      `rewrite_budget_skipped`); the dry-run serializer passes stage metadata
      through verbatim (`_serialize_stage_result`), so the dry-run exposes them.
- [x] **Failure semantics (refined during implementation):** a failure on the
      first (draft) pass short-circuits to the stage input text (unchanged from
      pre-story); a failure — or empty/over-budget output — on a *refine* pass
      falls open to the **best successful draft so far**, so enabling
      multi-pass never regresses below single-pass output. —
      `test_project_rewriter_refine_failure_keeps_best_draft`,
      `test_project_rewriter_refine_empty_keeps_best_draft`.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_dictation_project_rewriter.py` —
  add cases: passes=1 byte-identical, passes=2 calls runtime twice with the
  draft threaded, budget-exceeded skip, failure short-circuit. Fake runtime
  records call count + prompts.
- Unit (config): `uv run pytest -q -k dictation_config` (or the relevant
  config test) — `rewrite_passes` default + validation.
- Integration: `uv run pytest -q tests/integration -k dictation_dry_run` —
  dry-run response includes per-pass metadata.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: optional warm run on the reference Mac to sanity-check
  2-pass latency; not a gate (no measurement gate per project posture).

## Notes / open questions

- Critique prompt: **resolved** — one generic "tighten, fix, keep intent"
  refine directive (`_default_refine_prompt_builder`) carrying the project +
  target-profile context but not the agent-reply lines; injectable via the
  `refine_prompt_builder` constructor seam.
- Budget accounting: the pipeline already tracks `elapsed_ms` per stage in
  `pipeline.py`; the rewriter needs the *running* pipeline budget, so thread
  the remaining budget (or a deadline) into the stage call rather than
  re-deriving it.
- Canon: DIR-01 §3.2 keeps each utterance independent — multi-pass refines a
  single utterance's rewrite, so it does **not** introduce cross-utterance
  state. If this story drifts toward rolling context, the DIR-01 spec wins;
  record it here.
