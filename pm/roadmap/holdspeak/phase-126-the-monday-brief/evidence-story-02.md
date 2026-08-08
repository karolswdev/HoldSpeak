# Evidence - HS-126-02

- **Story:** HS-126-02 - Persist the brief
- **Status:** done
- **Date:** 2026-08-07

## Proof

Persistence shipped as part of HS-126-01 — `generate()` persists, `get_latest()` loads, and items are stored with a `brief_id` foreign key.

### Captured run — 2026-08-08T00:55:59Z

- **Command:** `uv run pytest -q tests/unit/test_monday_brief_service.py -v -k persist or latest or idempotent`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 46b837f953fb96af393e3a0414504f4a612b66bc

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 7 items / 5 deselected / 2 selected

tests/unit/test_monday_brief_service.py ..                               [100%]

======================= 2 passed, 5 deselected in 0.39s ========================
```
