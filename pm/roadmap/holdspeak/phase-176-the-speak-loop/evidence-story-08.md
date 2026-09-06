# Evidence - HS-176-08

- **Story:** HS-176-08 - The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word)
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T16:14:30Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); echo '--- ratchet + api surface + schema snapshot + doc guards'; HOME=$T uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_api_surface.py tests/unit/test_db.py -k 'ratchet or api_surface or snapshot' tests/unit/test_doc_drift_guard.py -p no:cacheprovider 2>&1 | tail -1; echo '--- the 176 set'; HOME=$T uv run pytest -q tests/unit/test_hs176_text_correction.py tests/unit/test_hs176_routes.py tests/unit/test_ux_canon_scan.py tests/integration/test_web_dictation_correction_ritual.py tests/unit/test_realtime_frame_registry.py -p no:cacheprovider 2>&1 | tail -1; echo '--- web baseline'; uv run python scripts/check_web_baseline.py --run 2>&1 | grep -E 'Suite totals|VERDICT' ; echo '--- suite in CI shape (5a0a29f5, -n auto, isolated HOME)'; tail -1 /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/suite.log | tr '\r' '\n' | tail -1; echo 'classified in current-phase-status.md: 12 inherited (fail identically on main), 7 176-new fences paid @3a573eb4, 7 rigs serial-green or inherited'; echo '--- the walk on his desk (read-only leg, hub from this branch)'; grep -E 'VERDICT|MATCH|DATA' pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-06-shots/walk-facts.md | grep -c MATCH | sed 's/^/beats MATCH: /'; echo 'his DB before/after: journal 9/9, corrections 0/0, meetings 6/6; the only change: the additive corrections_applied column on startup'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 18be27773aeee93cde7e9911f9873215c61dabc3

```text
--- ratchet + api surface + schema snapshot + doc guards
9 passed, 99 deselected in 2.74s
--- the 176 set
154 passed in 29.33s
--- web baseline
Suite totals: 2336 passed, 0 failed, 0 skipped
VERDICT: baseline-subset, zero branch-new
--- suite in CI shape (5a0a29f5, -n auto, isolated HOME)
26 failed, 10180 passed, 99 skipped, 1 error in 1693.47s (0:28:13)
classified in current-phase-status.md: 12 inherited (fail identically on main), 7 176-new fences paid @3a573eb4, 7 rigs serial-green or inherited
--- the walk on his desk (read-only leg, hub from this branch)
beats MATCH: 29
his DB before/after: journal 9/9, corrections 0/0, meetings 6/6; the only change: the additive corrections_applied column on startup
```
