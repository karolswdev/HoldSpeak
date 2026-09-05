# Evidence - HS-174-07

- **Story:** HS-174-07 - The third connector (implementation: WatchSource, Door card, templates)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:20:31Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_confluence_wire.py tests/e2e/test_hs174_door_confluence_glass.py 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6d0e2495fab6267cf297ff54147d50ab9783283d

```text
33 passed in 14.91s
```
