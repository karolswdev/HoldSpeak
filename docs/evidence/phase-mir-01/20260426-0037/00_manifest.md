# Phase MIR-01 evidence bundle — manifest

**Captured:** 2026-04-26 00:37 UTC
**Git:** c603638 (HS-2-10: MIR doctor checks + failure-isolation integration test)
**Branch:** main
**Bundle path:** `docs/evidence/phase-mir-01/20260426-0037/`
**Phase:** 2 (HoldSpeak roadmap) — MIR-01 (Multi-Intent Routing)
**Spec:** `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md`
**Story:** HS-2-11 (Definition of Done sweep)

## Files

Per spec §8.2:

| File | Purpose | Status |
|---|---|---|
| `00_manifest.md` | This document | ✓ |
| `01_env.txt` | OS / Python / git environment capture | ✓ |
| `02_git_status.txt` | Working-tree state + recent commits | ✓ |
| `03_traceability.md` | MIR-* requirement → evidence artifact matrix | ✓ |
| `10_ut_router.log` | Unit tests for router/scoring/contracts/dispatch/persistence/pipeline/observability (51 cases) | ✓ |
| `10_ut_security.log` | Unit tests for capability gates + actuator block (2 cases) | ✓ |
| `20_it_routing.log` | Integration tests for routing pipeline + stop-path + config bridge (9 cases) | ✓ |
| `20_it_synthesis.log` | Integration + unit tests for synthesis pass + persistence (11 cases) | ✓ |
| `20_it_fallback.log` | MIR-R-004 + MIR-F-012 graceful-degrade tests (3 cases) | ✓ |
| `30_db_checks.txt` | DB schema check + MIR-D-001..D-004/D-006 round-trip tests (14 cases + DDL extract) | ✓ |
| `31_migration_checks.txt` | MIR-D-005 idempotent migration check | ✓ |
| `40_api_checks.log` | Web API integration tests (timeline + controls; 14 cases) | ✓ |
| `41_cli_checks.log` | `holdspeak intel` MIR-route command tests (7 cases + --help) | ✓ |
| `50_perf.txt` | MIR-R-001 routing-per-window timing sample (n=100) | ✓ |
| `60_logs_sample.txt` | MIR-O-001 + MIR-S-003 structured-log + secret-redaction sample | ✓ |
| `61_metrics_sample.txt` | MIR-O-002 + MIR-O-003 router + host counter sample | ✓ |
| `99_phase_summary.md` | Phase summary, scope outcome, follow-ups | ✓ |

All 17 spec §8.2 files present. No deletions or omissions.

## Validity (spec §8.3)

1. ✓ Logs include the command line used (each file leads with `# Command: ...`).
2. ✓ Logs include timestamp + git commit hash (each file leads with `# Captured:` and `# Git:`).
3. ✓ Failing checks are preserved + annotated. **No checks failed in this bundle.** The metal-tagged hardware-only baseline (carried since HS-1-03) is excluded from the regression sweep per the project's standing memory; this is documented in `99_phase_summary.md`.
4. ✓ All required files exist; phase is eligible for completion.

## Reproducibility

```
git checkout c603638
uv sync
# regenerate any individual log:
uv run pytest tests/unit/test_intent_router.py tests/unit/test_intent_scoring.py \
              tests/unit/test_intent_contracts.py tests/unit/test_intent_dispatch.py \
              tests/unit/test_intent_persistence.py tests/unit/test_intent_pipeline.py \
              tests/unit/test_intent_signals.py tests/unit/test_intent_timeline.py \
              tests/unit/test_intent_observability.py -v
# (and so on per file headers)
```
