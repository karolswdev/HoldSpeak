# Evidence - HS-174-03

- **Story:** HS-174-03 - Scoped remote identity (non-OWNER principals, palette-restricted, owner-issued)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T20:34:16Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_reach_wire.py tests/e2e/test_hs174_remote_settings_glass.py -k "credential or palette or hash or expir or revoke or identity or issue or Issue" 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5a2e9eca63ce25958a6f8b09ab4758601c1b14d7

```text
19 passed, 21 deselected in 12.69s
```
