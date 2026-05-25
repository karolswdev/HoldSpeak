# Evidence — HS-19-03 Dictation Latency and Fallback Telemetry

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-19-03](./story-03-latency-fallback-telemetry.md)

## What changed

- Added `holdspeak/dictation_telemetry.py` to normalize stage, dry-run, and readiness telemetry.
- Dry-run payloads now include:
  - per-stage `telemetry.status`
  - per-stage `telemetry.reason`
  - per-stage fallback category
  - total latency, latency budget, over-budget flag, and fallback summary
- Readiness payloads now include runtime session telemetry:
  - model/classify counters
  - classify successes
  - configured latency budget
  - cold-start cap
  - runtime/session fallback flags
- The Dictation web cockpit now shows telemetry directly in readiness cards and dry-run traces.
- Project-rewriter metadata now reports project-doc suggestion status (`suggested`, `no_suggestion`, `skipped_target`, etc.).
- Intent-router metadata now reports normalized reason values for matched/no-match/classify-failed paths.

## Validation

```bash
npm run build
```

Result: passed from `web/`.

```bash
.venv/bin/pytest -q tests/unit/test_dictation_telemetry.py tests/unit/test_dictation_intent_router.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_assembly.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py tests/integration/test_web_project_kb_api.py
```

Result: `82 passed in 3.14s`.

## Notes

- No hosted analytics or long-term telemetry storage was added.
- Readiness uses session counters rather than p50/p95 because current runtime counters are process-scoped and lightweight.
- Dry-run remains the detailed per-run latency surface.
