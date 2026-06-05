# Evidence — HS-39-05 — Pipeline depth telemetry

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `holdspeak/plugins/dictation/telemetry_store.py` (**new**) —
  `DictationTelemetryStore` (bounded ring, thread-safe) + `quantile` +
  `stage_quantiles` + `latest_rewrite_pass_ms`.
- `holdspeak/dictation_telemetry.py` — `build_depth_readiness` (pure assembler:
  guidance when p95 ≥ 66% of budget; correction state passthrough).
- `holdspeak/web/context.py` — `WebContext.telemetry`.
- `holdspeak/web_server.py` — `MeetingWebServer.dictation_telemetry` + into the
  context.
- `holdspeak/web/routes/dictation/_helpers.py` — dry-run passes
  `on_run=telemetry.record_run` to `build_pipeline`.
- `holdspeak/web/routes/dictation/pipeline.py` — readiness assembles + returns
  the `depth` block; dry-run threads `ctx.telemetry`.
- `holdspeak/web_runtime.py` — live `_maybe_run_dictation_pipeline` feeds
  `self.server.dictation_telemetry` via `on_run`.
- Tests: `tests/unit/test_dictation_telemetry_store.py` (**new**, 5) + 3 in
  `tests/unit/test_dictation_telemetry.py` + 1 in
  `tests/integration/test_web_dictation_readiness_api.py`.

## Verification artifacts

- Targeted: `uv run pytest -q tests/unit/test_dictation_telemetry_store.py tests/unit/test_dictation_telemetry.py tests/integration/test_web_dictation_readiness_api.py`
  → `23 passed`.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2186 passed, 16 skipped` (was 2177/16 at HS-39-04; +9).
- **Live `.43` check** (3 real runs through the store → `build_depth_readiness`):

  ```json
  "stages": {
    "intent-router":   { "p50": 3821.7, "p95": 3985.5, "count": 3 },
    "kb-enricher":     { "p50": 0.0,    "p95": 0.0,    "count": 3 },
    "project-rewriter":{ "p50": 3553.3, "p95": 4380.5, "count": 3 }
  },
  "budget_ms": 8000.0, "guidance": [], "runs": 3
  ```

  Real per-stage quantiles: the LLM stages dominate (~3.5–4.4s), the pure
  kb-enricher is ~0ms, and p95 stays under the 8s budget so no guidance fires.

## Acceptance criteria — re-checked

- [x] `depth.stages` p50/p95 over the session store; empty → `{}` —
      `test_records_and_computes_quantiles`, `test_readiness_includes_depth_telemetry_block`.
- [x] Budget guidance at p95 ≥ 66% of budget; absent under —
      `test_depth_guidance_fires_when_p95_near_budget` (+ the under case).
- [x] `depth.rewrite_pass_ms` from the latest run with passes —
      `test_latest_rewrite_pass_ms_uses_most_recent_with_passes`.
- [x] `depth.corrections` (enabled/size/recent gists, no secrets).
- [x] Readiness valid when the pipeline is disabled.

## Deviations from plan

- The pipeline's per-instance ring buffer (DIR-F-009) resets every
  `build_pipeline` (fresh pipeline per utterance), so it never accumulates.
  Added a session-scoped `DictationTelemetryStore` fed via `on_run` from both
  paths — that's what survives across utterances. Recorded in the story Notes.
- In the live `.43` check above `rewrite_pass_ms` was empty: the short probe
  phrases exceeded the rewriter's char budget → no-op (which carries no
  per-pass metadata). The per-pass path is unit-tested with the fixture's
  longer input; the demo (HS-39-09) shows it populated.

## Follow-ups

- HS-39-06 docs should describe the `depth` readiness block.
- A future web UI could chart the quantiles; the data is on the API now.
