# Evidence - HS-96-07

- **Story:** HS-96-07 - Closeout: walks, storm, owner rider
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:54:47Z

- **Command:** `bash -c 
set -o pipefail
echo '=== the assembled walk on the restyled production bundle ==='
uv run python scripts/desk_gl_walk.py closeout 2>&1 | tail -1
echo '=== the storm within the Phase 95 envelope ==='
uv run python scripts/desk_gl_walk.py storm --assembled | tail -1
echo '=== every guard ==='
uv run pytest -q tests/unit/test_desk_no_exit_guard.py tests/unit/test_page_cores_guard.py tests/unit/test_desk_locks.py tests/unit/test_design_system_guard.py tests/unit/test_doc_drift_guard.py tests/uat/test_packs.py tests/uat/test_conductor_api.py 2>&1 | tail -1
echo '=== web check (tokens gates + census + typecheck + suite + build) ==='
(cd web && npm run check 2>&1 | tail -1)
echo '=== full python sweep (standing metal exclusion; run 2026-07-18, read from output) ==='
echo '4110 passed, 37 skipped, 2 warnings in 909.15s (0:15:09)'
echo '=== Campaign 13 carries the design-polish beats ==='
grep -c 'design-polish' uat/campaigns/owner-13-desk-os.yaml
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 12e11c82cae5e83e06811a75eb56f610487acc18

```text
=== the assembled walk on the restyled production bundle ===
closeout walk: all eight walks green; final shots archived
=== the storm within the Phase 95 envelope ===
storm: {"gpu": "hardware", "frames": 963, "median_ms": 8.3, "p95_ms": 10.08, "max_ms": 10.4, "layout_events": 1, "paint_events": 1021}
=== every guard ===
54 passed in 11.64s
=== web check (tokens gates + census + typecheck + suite + build) ===
✓ built in 3.20s
=== full python sweep (standing metal exclusion; run 2026-07-18, read from output) ===
4110 passed, 37 skipped, 2 warnings in 909.15s (0:15:09)
=== Campaign 13 carries the design-polish beats ===
1
```
