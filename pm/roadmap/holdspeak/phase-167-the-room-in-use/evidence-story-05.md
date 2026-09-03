# Evidence - HS-167-05

- **Story:** HS-167-05 - The faces recomposed II (Review, Update, Steward; shots; the beauty pass)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T22:09:47Z

- **Command:** `bash -c cd web && npx vitest run src/features/project-room 2>&1 | grep -E "Test Files|Tests "; cd .. && uv run python scripts/check_web_baseline.py --run 2>&1 | grep -E "VERDICT"; node web/scripts/validate-tokens.cjs 2>&1 | tail -1; HOME_REAL=$HOME; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright; export npm_config_cache=$HOME_REAL/.npm; uv run pytest -q tests/e2e/test_hs160_delta_glass.py tests/e2e/test_hs162_update_glass.py tests/e2e/test_hs163_steward_glass.py tests/e2e/test_hs164_unattended_glass.py -n auto -p no:cacheprovider 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e0dcd415d969b939504f7f5d4b082c2cf91801f1

```text
 Test Files  16 passed (16)
      Tests  537 passed (537)
VERDICT: baseline-subset, zero branch-new
  src/features/project-room/update/update-posture.css:60: z-index literal `z-index: 1` — use a --desk-z-* / --z-* ladder token
26 passed in 36.61s
```

### Captured run — 2026-09-03T22:12:01Z

- **Command:** `bash -c node web/scripts/validate-tokens.cjs 2>&1 | tail -1; cd web && npx vitest run src/features/project-room/update 2>&1 | grep -E "Tests "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e0dcd415d969b939504f7f5d4b082c2cf91801f1

```text
token gate: clean (12 allow-listed exceptions, all in use)
      Tests  78 passed (78)
```
