# Evidence - HS-174-04

- **Story:** HS-174-04 - Egress badges on remote reads (kernel receipt + badge; local stdio badgeless)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:20:03Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_reach_wire.py tests/e2e/test_hs174_receipts_glass.py 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68bd82d3df19a255a6a6c23abd317262c3ddf548

```text
53 passed in 24.88s
```
