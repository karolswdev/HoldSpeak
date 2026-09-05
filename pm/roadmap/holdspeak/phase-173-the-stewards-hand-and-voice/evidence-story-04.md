# Evidence - HS-173-04

- **Story:** HS-173-04 - The reviewer nudge (the first bounded external effect behind the policy gate)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T19:15:13Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs173_nudge_wire.py tests/e2e/test_hs173_health_glass.py tests/e2e/test_hs173_policy_glass.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 308935b826471d389d499156b7a204ef9e2293c5

```text
27 passed in 49.07s
```
