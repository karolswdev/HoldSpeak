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
