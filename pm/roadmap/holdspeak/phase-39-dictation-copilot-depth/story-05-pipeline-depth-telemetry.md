# HS-39-05 — Pipeline depth telemetry

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** HS-39-01, HS-39-02
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 19 added basic per-stage latency + fallback reasons to the dictation
readiness/dry-run surface. The new depth in this phase — multi-pass rewriting
(HS-39-01) and correction memory (HS-39-02) — is invisible: there's no
per-stage latency distribution, no per-pass attribution, no view of the
correction store, and no guidance when a stage is consistently slow. The depth
features need to be observable to be trustworthy and tunable.

## Scope

- In:
  - **Per-stage latency quantiles** (p50/p95) over the existing recent-runs
    ring buffer (`PipelineRun.stage_results[i].elapsed_ms` in
    `holdspeak/plugins/dictation/pipeline.py`), surfaced on
    `GET /api/dictation/readiness`.
  - **Budget guidance:** when a stage's p95 trends toward `max_total_latency_ms`,
    surface a hint (e.g. "intent-router p95 ≈ 180ms — consider a smaller model
    or lower max_tokens").
  - **Multi-pass attribution:** expose the per-pass timings HS-39-01 records.
  - **Correction-store visibility:** size / recent corrections / enabled-state
    from HS-39-02 (gist-only, no secrets).
- Out:
  - Persisting telemetry across restarts (in-memory ring only — see phase
    "Decisions deferred").
  - A new metrics backend / Prometheus exporter.
  - Charts in the web UI (data on the API; rich visualization is not required
    this story).

## Acceptance criteria

- [x] `GET /api/dictation/readiness` returns a `depth.stages` block with
      per-stage p50/p95 over the session telemetry store (empty → `{}`, not an
      error) — `build_depth_readiness` + `DictationTelemetryStore.stage_quantiles`;
      `test_readiness_includes_depth_telemetry_block`,
      `test_records_and_computes_quantiles`. **Verified live on `.43`**:
      intel-router p50 3821ms, project-rewriter p50 3553ms over 3 real runs.
- [x] Budget guidance appears when a stage's p95 ≥ 66% of
      `max_total_latency_ms`; absent when comfortably under —
      `test_depth_guidance_fires_when_p95_near_budget`,
      `test_depth_no_guidance_when_comfortably_under_budget`.
- [x] Multi-pass per-pass timings surface as `depth.rewrite_pass_ms` (from the
      most recent run that produced them) — `latest_rewrite_pass_ms`;
      `test_latest_rewrite_pass_ms_uses_most_recent_with_passes`.
- [x] Correction-store state (`enabled` / `size` / `recent` gists, no secrets)
      reported under `depth.corrections` — readiness reads `ctx.corrections.recent`.
- [x] Readiness valid when the pipeline is disabled (the `depth` block is empty
      but well-formed) — `test_readiness_includes_depth_telemetry_block`.

## Test plan

- Unit: `tests/unit/test_dictation_pipeline.py` — quantile computation over a
  seeded ring (incl. empty + single-entry edge cases); guidance threshold
  logic.
- Integration: `tests/integration/test_web_dictation_*api.py` — readiness
  payload shape includes the new fields; disabled-pipeline path valid.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a.

## Notes / open questions

- **Deviation (recorded at ship):** the pipeline's per-instance ring buffer
  (DIR-F-009) **resets every `build_pipeline`** (the dry-run + live paths build a
  fresh pipeline per utterance), so it never accumulates. I added a
  session-scoped `DictationTelemetryStore` (bounded ring, on `MeetingWebServer`
  like the correction store) fed via the pipeline `on_run` hook from both paths
  — that's what survives across utterances. Small-N quantiles are approximate
  ("recent"), not statistical rigor.
- In-memory only (no persistence across restarts), per the scope.
