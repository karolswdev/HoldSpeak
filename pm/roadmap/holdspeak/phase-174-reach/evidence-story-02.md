# Evidence - HS-174-02

- **Story:** HS-174-02 - The transport (Streamable HTTP on the hub behind scoped credentials)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T20:33:54Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_reach_wire.py tests/e2e/test_hs174_remote_settings_glass.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5a2e9eca63ce25958a6f8b09ab4758601c1b14d7

```text
RuntimeError: cannot schedule new futures after shutdown
```

### Captured run — 2026-09-05T20:35:09Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_reach_wire.py tests/e2e/test_hs174_remote_settings_glass.py 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b0625cbf228435d6d89348f5d9ada3aa09397e96

```text
40 passed in 19.76s
```
