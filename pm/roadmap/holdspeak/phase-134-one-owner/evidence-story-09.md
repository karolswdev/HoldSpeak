# Evidence - HS-134-09

- **Story:** HS-134-09 - The docs speak destination
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T22:54:21Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_doc_drift_guard.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c7322f6884929e88c7d798e6c94f5b210b05968b

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 19 items

tests/unit/test_doc_drift_guard.py ...................                   [100%]

============================== 19 passed in 0.44s ==============================
```
