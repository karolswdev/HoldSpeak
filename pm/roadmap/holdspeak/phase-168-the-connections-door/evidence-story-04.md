# Evidence - HS-168-04

- **Story:** HS-168-04 - The Sources step connect-once (state on the cards; connect in place and return; the wizard asks scope only; scope carries; honest verbs; D3 settled)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-04T06:18:59Z

- **Command:** `bash -c cd web && npx vitest run src/features/project-room/setup src/desk/surface 2>&1 | grep -E 'Tests |Test Files'; cd .. && HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/integration/test_project_setup_routes.py tests/unit/test_project_setup_service.py tests/unit/test_api_surface.py tests/unit/test_web_vocabulary_guard.py 2>&1 | tail -1; HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/e2e/test_hs159_interview_glass.py tests/e2e/test_hs161_github_glass.py tests/e2e/test_hs166_jira_glass.py tests/e2e/test_hs168_sources_glass.py 2>&1 | tail -1; uv run python scripts/check_web_baseline.py --run 2>&1 | grep -E 'VERDICT|passed' | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 602dff70d0aacf98c9395d99a62752eba14d6056

```text
 Test Files  26 passed (26)
      Tests  486 passed (486)
95 passed in 22.89s
19 passed, 1 skipped in 191.07s (0:03:11)
Suite totals: 2360 passed, 0 failed, 0 skipped
VERDICT: baseline-subset, zero branch-new
```
