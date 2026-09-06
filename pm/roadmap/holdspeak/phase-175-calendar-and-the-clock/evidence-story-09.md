# Evidence - HS-175-09

- **Story:** HS-175-09 - The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-06T02:05:49Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_api_surface.py tests/unit/test_doc_drift_guard.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_db.py -k "not project_room" -p no:cacheprovider 2>&1 | tail -1 && uv run python scripts/check_web_baseline.py --run 2>&1 | tail -1 && echo "final-summary: $(head -1 pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/final-summary.md)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 76dc4943aef3f12761cf0006da7383309d5b045a

```text
115 passed in 21.80s
VERDICT: baseline-subset, zero branch-new
final-summary: # Phase 175 — Calendar and the Clock — final summary (DRAFT: his attended walk and the close still open)
```

### Captured run — 2026-09-06T02:06:59Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_api_surface.py tests/unit/test_doc_drift_guard.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_db.py -k "not project_room" -p no:cacheprovider 2>&1 | tail -1 && uv run python scripts/check_web_baseline.py --run 2>&1 | tail -1 && echo "final-summary: $(head -1 pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/final-summary.md)" && grep -c "COMPLETE 9/9" pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/current-phase-status.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 76dc4943aef3f12761cf0006da7383309d5b045a

```text
115 passed in 21.71s
VERDICT: baseline-subset, zero branch-new
final-summary: # Phase 175 — Calendar and the Clock — final summary
2
```
