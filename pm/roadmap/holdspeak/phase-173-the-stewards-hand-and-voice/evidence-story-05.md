# Evidence - HS-173-05

- **Story:** HS-173-05 - The release-readiness scorecard (the Room token row)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T19:15:12Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs173_health_wire.py tests/e2e/test_hs173_health_glass.py -k readiness_or_release_or_ready_or_health 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 308935b826471d389d499156b7a204ef9e2293c5

```text
49 deselected in 0.13s
```

### Captured run — 2026-09-05T19:16:58Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs173_health_wire.py tests/e2e/test_hs173_health_glass.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7db6a24d79b37fa68fea7a52d0913194f2942c5f

```text
49 passed in 59.69s
```
