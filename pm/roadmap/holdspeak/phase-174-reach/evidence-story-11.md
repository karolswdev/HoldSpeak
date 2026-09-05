# Evidence - HS-174-11

- **Story:** HS-174-11 - The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:59:47Z

- **Command:** `bash -c .githooks/dw check holdspeak | tail -3; echo '--- suite (CI shape, -n auto)'; grep -E '^[0-9]+ failed, [0-9]+ passed' /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/full-suite-174.log; echo '--- serial re-run of the 21 non-inherited'; grep -E 'passed|failed' /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/rerun-174.log | tail -1; echo '--- fences after payment'; HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider -p no:xdist tests/integration/test_principal_separation.py tests/integration/test_web_activity_api.py tests/unit/test_db.py::TestDatabaseShape tests/unit/test_hs168_connections_service.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_project_room_read.py tests/web/test_hs168_connections_routes.py tests/unit/test_hs174_reach_wire.py 2>&1 | tail -1; echo '--- the walk'; grep -E 'Shots|Errors|Surprises|Defects|Writes' /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/walk-174.log | tail -5; echo '--- web baseline'; grep -E 'VERDICT|HEALED \(|BRANCH-NEW \(' /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/web-baseline-174.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 51ccd75e08fd705e46b94678abba377bab52f4a6

```text
ERROR pm/roadmap/holdspeak/phase-170-the-great-pass/evidence-story-03.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-174-reach/story-11-the-close.md: header status 'in-progress' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-174-reach/current-phase-status.md: broken evidence link for HS-174-11: --
--- suite (CI shape, -n auto)
27 failed, 9814 passed, 98 skipped in 1657.55s (0:27:37)
--- serial re-run of the 21 non-inherited
10 failed, 11 passed in 176.58s (0:02:56)
--- fences after payment
175 passed in 55.47s
--- the walk
  Shots:      8
  Errors:     0
  Surprises:  0
  Defects:    0
  Writes:     0
--- web baseline
HEALED (4):
BRANCH-NEW (1):
VERDICT: BRANCH-NEW FAILURES: 1
```
