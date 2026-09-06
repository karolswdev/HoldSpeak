# Evidence - HS-167-04

- **Story:** HS-167-04 - The faces recomposed I (the Room, the interview, the activation review, the GitHub wizard; shots)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T21:47:01Z

- **Command:** `bash -c cd web && npx vitest run src/features/project-room src/desk/surface 2>&1 | grep -E "Test Files|Tests "; cd .. && uv run python scripts/check_web_baseline.py --run 2>&1 | grep -E "VERDICT"; node web/scripts/validate-tokens.cjs 2>&1 | tail -1; HOME_REAL=$HOME; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright; export npm_config_cache=$HOME_REAL/.npm; uv run pytest -q tests/e2e/test_hs158_room_glass.py tests/e2e/test_hs159_interview_glass.py tests/e2e/test_hs161_github_glass.py -n auto -p no:cacheprovider 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 66364f54463a97d12132d47a1c784e4fd3e427f0

```text
 Test Files  35 passed (35)
      Tests  789 passed (789)
VERDICT: baseline-subset, zero branch-new
token gate: clean (12 allow-listed exceptions, all in use)
18 passed, 1 skipped in 29.57s
```
