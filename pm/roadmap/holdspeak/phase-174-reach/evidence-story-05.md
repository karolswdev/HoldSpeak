# Evidence - HS-174-05

- **Story:** HS-174-05 - The long-running contract (run_id + polling over HTTP)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T20:40:52Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_reach_wire.py tests/integration/test_hs174_runner_loopback.py tests/unit/test_hs174_runner.py 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 87bcb9707dd632d2eb635964ff7d6f97e6a811fa

```text
57 passed in 24.80s
```
