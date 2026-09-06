# Evidence - HS-200-06

- **Story:** HS-200-06 - Separate citation, factual support, and acceptance
- **Status:** done
- **Date:** 2026-09-06

## Proof

The first attempt at this capture (21:13:35Z) pointed `PLAYWRIGHT_BROWSERS_PATH` at the throwaway HOME, so the three glass legs errored on a missing browser; it is dropped here and re-run below with the real browser cache. No product failure was hidden.

### Captured run — 2026-09-06T21:15:00Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_claim_support.py tests/integration/test_phase200_claim_support.py tests/unit/test_update_drafter.py tests/integration/test_update_routes.py tests/unit/test_project_mcp.py tests/unit/test_hs173_drafter_wire.py tests/unit/test_project_updates_schema.py tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_phase143_inference_capability_census.py -p no:cacheprovider 2>&1 | tail -2; HOME=$T PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q tests/e2e/test_hs200_claim_support_glass.py tests/e2e/test_hs162_update_glass.py tests/e2e/test_hs173_update_glass.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/features/project-room 2>&1 | grep -E "^ +Tests "; cd ..; ls pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-06-shots | wc -l | sed "s/^/shots: /"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da771ba82f9caf0627530eacd161276c6cf42b7f

```text
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
195 passed, 1 skipped in 56.57s
12 passed in 43.01s
      Tests  398 passed (398)
shots:        3
```

### Captured run — 2026-09-06T21:17:10Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run python scripts/check_web_baseline.py --run 2>&1 | tail -3; cd web && npm run check 2>&1 | grep -E "bundle gate|error TS" | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da771ba82f9caf0627530eacd161276c6cf42b7f

```text
Suite totals: 2375 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
bundle gate passed (Desk JS 1275076 B; Desk CSS 306679 B; source maps 0)
```

### Captured run — 2026-09-06T21:22:30Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_claim_support.py tests/integration/test_phase200_claim_support.py tests/unit/test_update_drafter.py tests/unit/test_project_updates_schema.py tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_db.py -k 'claim or drafter or schema or api_surface or ratchet or snapshot' -p no:cacheprovider 2>&1 | tail -1; HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_claim_support_glass.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/features/project-room/update 2>&1 | grep -E 'Tests '; cd ..; ls pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-06-shots/ | tr '\n' ' '; echo; echo 'schema 76 unchanged; api surface 669 unchanged'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da771ba82f9caf0627530eacd161276c6cf42b7f

```text
140 passed, 1 skipped, 67 deselected in 26.75s
3 passed in 12.27s
      Tests  89 passed (89)
build-claim-axes-mixed-1440.png build-claim-axes-mixed-393.png build-claim-axes-real-1440.png 
schema 76 unchanged; api surface 669 unchanged
```
