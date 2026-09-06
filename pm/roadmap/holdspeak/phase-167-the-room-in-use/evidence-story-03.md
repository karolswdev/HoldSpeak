# Evidence - HS-167-03

- **Story:** HS-167-03 - The library reform (scroll-hint + egress species promoted; the design's new species; tokens fenced; the shared glass conftest)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T20:20:42Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface 2>&1 | grep -E "Test Files|Tests "; cd .. && node web/scripts/validate-tokens.cjs 2>&1 | tail -1; HOME_REAL=$HOME; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright; export npm_config_cache=$HOME_REAL/.npm; uv run pytest -q tests/e2e/test_hs158_room_glass.py tests/e2e/test_hs159_interview_glass.py tests/e2e/test_hs160_delta_glass.py tests/e2e/test_hs161_github_glass.py tests/e2e/test_hs162_update_glass.py tests/e2e/test_hs163_steward_glass.py tests/e2e/test_hs164_unattended_glass.py tests/e2e/test_hs166_jira_glass.py -n auto -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d57456a182f92e8b5b2e16c7998441caac6d7f9d

```text
 Test Files  19 passed (19)
      Tests  252 passed (252)
token gate: clean (12 allow-listed exceptions, all in use)
FAILED tests/e2e/test_hs166_jira_glass.py::test_jira_setup_walk[1440] - playw...
2 failed, 44 passed, 1 skipped in 55.97s
```

### Captured run — 2026-09-03T20:23:46Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface 2>&1 | grep -E "Test Files|Tests "; cd .. && node web/scripts/validate-tokens.cjs 2>&1 | tail -1; HOME_REAL=$HOME; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright; export npm_config_cache=$HOME_REAL/.npm; uv run pytest -q tests/e2e/test_hs158_room_glass.py tests/e2e/test_hs159_interview_glass.py tests/e2e/test_hs160_delta_glass.py tests/e2e/test_hs161_github_glass.py tests/e2e/test_hs162_update_glass.py tests/e2e/test_hs163_steward_glass.py tests/e2e/test_hs164_unattended_glass.py tests/e2e/test_hs166_jira_glass.py -n auto -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/desk/chair/lanes/DoorBoardLane.test.tsx 2>&1 | grep -E "Tests "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d57456a182f92e8b5b2e16c7998441caac6d7f9d

```text
 Test Files  19 passed (19)
      Tests  252 passed (252)
token gate: clean (12 allow-listed exceptions, all in use)
46 passed, 1 skipped in 48.48s
      Tests  55 passed (55)
```
