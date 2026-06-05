# HS-39-05 — Pipeline depth telemetry

- **Project:** holdspeak
- **Phase:** 39
- **Status:** backlog
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

- [ ] `GET /api/dictation/readiness` returns per-stage p50/p95 computed over
      the recent-runs buffer (empty buffer → nulls, not an error).
- [ ] Budget guidance appears when a stage's p95 approaches
      `max_total_latency_ms`; absent when comfortably under.
- [ ] Multi-pass per-pass timings (from HS-39-01) are present when
      `rewrite_passes > 1`.
- [ ] Correction-store state (enabled, size, recent gist entries) is reported,
      with no secret content.
- [ ] The readiness response remains valid when the pipeline is disabled
      (reports disabled, no crash).

## Test plan

- Unit: `tests/unit/test_dictation_pipeline.py` — quantile computation over a
  seeded ring (incl. empty + single-entry edge cases); guidance threshold
  logic.
- Integration: `tests/integration/test_web_dictation_*api.py` — readiness
  payload shape includes the new fields; disabled-pipeline path valid.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a.

## Notes / open questions

- Reuse the existing recent-runs ring buffer (DIR-F-009, default N=20) as the
  quantile sample — do not add a second buffer. Small-N quantiles are
  approximate; label them as "recent" rather than implying statistical rigor.
- This story is **after** 01/02 because it surfaces their new fields; if 01/02
  slip, ship the quantiles/guidance portion and stub the rest behind feature
  presence.
