# Evidence - HS-125-06

- **Story:** HS-125-06 - Due and stall semantics
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T00:22:43Z

- **Command:** `zsh -c uv run pytest -q tests/unit/test_follow_through_service.py -v && uv run pytest -q tests/unit/test_decision_commitments.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9febc48e0fd3d6d7ac15f28a10042d832c49c148

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 16 items

tests/unit/test_follow_through_service.py ................               [100%]

============================== 16 passed in 1.30s ==============================
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 1 item

tests/unit/test_decision_commitments.py .                                [100%]

============================== 1 passed in 0.34s ===============================
```
