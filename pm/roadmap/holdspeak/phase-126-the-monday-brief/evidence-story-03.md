# Evidence - HS-126-03

- **Story:** HS-126-03 - Collect changes
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:01:08Z

- **Command:** `uv run pytest -q tests/unit/test_monday_brief_service.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e1c18490bf2fed976e4123130f79cbb7e5293ec2

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 12 items

tests/unit/test_monday_brief_service.py ............                     [100%]

============================== 12 passed in 1.17s ==============================
```

### Captured run — 2026-08-08T01:01:45Z

- **Command:** `uv run pytest -q tests/unit/test_brief_collectors.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e1c18490bf2fed976e4123130f79cbb7e5293ec2

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 15 items

tests/unit/test_brief_collectors.py ...............                      [100%]

============================== 15 passed in 1.47s ==============================
```

### Captured run — 2026-08-08T01:03:04Z

- **Command:** `uv run pytest -q tests/unit/test_monday_brief_service.py tests/unit/test_brief_collectors.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e1c18490bf2fed976e4123130f79cbb7e5293ec2

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 28 items

tests/unit/test_monday_brief_service.py .............                    [ 46%]
tests/unit/test_brief_collectors.py ...............                      [100%]

============================== 28 passed in 5.07s ==============================
```
