# Evidence - HS-127-07

- **Story:** HS-127-07 - Supersede, never erase
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:32:32Z

- **Command:** `uv run pytest -q tests/unit/test_decision_receipt_service.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 42222ec54cb960cdde567432f12a07b16e23aee9

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 17 items

tests/unit/test_decision_receipt_service.py .................            [100%]

============================== 17 passed in 1.48s ==============================
```
