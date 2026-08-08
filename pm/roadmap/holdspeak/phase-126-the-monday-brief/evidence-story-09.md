# Evidence - HS-126-09

- **Story:** HS-126-09 - The walk
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:12:24Z

- **Command:** `uv run pytest -q tests/unit/test_walk_monday_brief_126.py -v`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4090848be638a19804ceda00db0893c0ffc5ddf8

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 2 items

tests/unit/test_walk_monday_brief_126.py F.                              [100%]

=================================== FAILURES ===================================
______________ test_walk_generates_and_delivers_all_four_sections ______________

db = <holdspeak.db.core.Database object at 0x10fd927b0>

    def test_walk_generates_and_delivers_all_four_sections(db: Database) -> None:
        _seed_window(db)
        service = MondayBriefService(db)
    
        brief = service.generate(OWNER, now=NOW)
    
        assert brief.sections["changed"]
        assert brief.sections["broke"]
        assert brief.sections["waiting"]
        assert brief.sections["decisions"]
>       assert brief.sections["changed"][0].text == "NoteService.create_note"
E       AssertionError: assert 'WorkflowService.run_workflow' == 'NoteService.create_note'
E         
E         - NoteService.create_note
E         + WorkflowService.run_workflow

tests/unit/test_walk_monday_brief_126.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_walk_monday_brief_126.py::test_walk_generates_and_delivers_all_four_sections
========================= 1 failed, 1 passed in 0.53s ==========================
```

### Captured run — 2026-08-08T01:12:40Z

- **Command:** `uv run pytest -q tests/unit/test_walk_monday_brief_126.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4090848be638a19804ceda00db0893c0ffc5ddf8

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 2 items

tests/unit/test_walk_monday_brief_126.py ..                              [100%]

============================== 2 passed in 0.49s ===============================
```

### Captured run — 2026-08-08T01:12:59Z

- **Command:** `uv run pytest -q tests/unit/test_walk_monday_brief_126.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4090848be638a19804ceda00db0893c0ffc5ddf8

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 2 items

tests/unit/test_walk_monday_brief_126.py ..                              [100%]

============================== 2 passed in 0.49s ===============================
```
