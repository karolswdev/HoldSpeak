# Evidence - HS-125-07

- **Story:** HS-125-07 - Write-through completion verbs
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T00:22:31Z

- **Command:** `uv run pytest -q tests/unit/test_write_through_verbs.py tests/unit/test_follow_through_service.py tests/unit/test_decision_commitments.py -v`
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
collected 23 items

tests/unit/test_write_through_verbs.py ......                            [ 26%]
tests/unit/test_follow_through_service.py ................               [ 95%]
tests/unit/test_decision_commitments.py .                                [100%]

============================== 23 passed in 1.81s ==============================
```

### Captured run — 2026-08-08T00:23:11Z

- **Command:** `uv run pytest -q tests/unit/test_write_through_verbs.py tests/unit/test_follow_through_service.py tests/unit/test_decision_commitments.py -v`
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
collected 24 items

tests/unit/test_write_through_verbs.py .......                           [ 29%]
tests/unit/test_follow_through_service.py ................               [ 95%]
tests/unit/test_decision_commitments.py .                                [100%]

============================== 24 passed in 2.12s ==============================
```
