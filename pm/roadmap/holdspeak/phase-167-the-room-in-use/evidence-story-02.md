# Evidence - HS-167-02

- **Story:** HS-167-02 - The debts a user hits (toggles persisted; enrichment receipted; the acli file lock; the cadence write wire; the trigger route)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T20:07:27Z

- **Command:** `bash -c HOME_REAL=$HOME; export HOME=$(mktemp -d); uv run pytest -q tests/unit/test_hs167_debts.py tests/unit/test_hs166_walk_fixes.py tests/unit/test_api_surface*.py tests/unit/test_mcp_surface*.py -p no:cacheprovider 2>&1 | tail -3; cd web && npx vitest run src/features/project-room/setup src/features/project-room/steward 2>&1 | grep -E "Test Files|Tests "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d57456a182f92e8b5b2e16c7998441caac6d7f9d

```text


no tests ran in 0.00s
 Test Files  8 passed (8)
      Tests  320 passed (320)
```

### Captured run — 2026-09-03T20:07:48Z

- **Command:** `bash -c HOME_REAL=$HOME; export HOME=$(mktemp -d); uv run pytest -q tests/unit/test_hs167_debts.py tests/unit/test_hs166_walk_fixes.py tests/unit/test_api_surface.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_one_path_census.py -p no:cacheprovider 2>&1 | tail -2; cd web && npx vitest run src/features/project-room/setup src/features/project-room/steward 2>&1 | grep -E "Test Files|Tests "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d57456a182f92e8b5b2e16c7998441caac6d7f9d

```text
........................................................................ [100%]
72 passed in 80.07s (0:01:20)
 Test Files  8 passed (8)
      Tests  320 passed (320)
```
