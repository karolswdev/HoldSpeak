# Evidence - HS-126-06

- **Story:** HS-126-06 - Identify owner decisions
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:01:36Z

- **Command:** `uv run pytest -q tests/unit/test_brief_collectors.py -v -k decision`
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
collected 15 items / 10 deselected / 5 selected

tests/unit/test_brief_collectors.py .....                                [100%]

======================= 5 passed, 10 deselected in 0.60s =======================
```
