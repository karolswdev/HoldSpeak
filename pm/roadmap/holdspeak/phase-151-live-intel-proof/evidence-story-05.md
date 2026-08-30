# Evidence - HS-151-05

- **Story:** HS-151-05 - The record book
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T03:06:34Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8809ed2185afad4c8f63c2343117f9439db73125

```text
.................................                                        [100%]
33 passed in 1.32s
```

## Orchestrator triage — 2026-08-30

- Guards UNFILTERED, verified by my own hand (33/33 — the 150
  deselection lesson holding).
- Spot-read against shipped code: the operator runbook
  (docs/internal/OPERATOR_METAL_INTEL.md) carries the resident-
  server pin fact + do-not-touch law, the 8081 relaunch line
  verbatim from the probe record, and the never-download rule;
  MODELS.md states Me/Remote as the only reserved tokens exactly
  as parsing.py ships; USER_GUIDE's latency numbers come from
  story 03's evidence, not hope.
- Root README honestly untouched; entry points ride existing
  see-also chains.
