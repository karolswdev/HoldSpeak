# Evidence - HS-126-01

- **Story:** HS-126-01 - Brief window and generation model
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T00:53:15Z

- **Command:** `uv run pytest -q tests/unit/test_monday_brief_service.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 67ef15081dea0f14b7f258bf5674c6e85fa2c3f9

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 7 items

tests/unit/test_monday_brief_service.py .......                          [100%]

============================== 7 passed in 0.70s ===============================
```
