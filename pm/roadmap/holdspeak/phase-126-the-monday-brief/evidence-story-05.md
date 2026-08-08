# Evidence - HS-126-05

- **Story:** HS-126-05 - Collect waiting work
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:00:36Z

- **Command:** `uv run pytest -q tests/unit/test_brief_collectors.py -v -k waiting`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e1c18490bf2fed976e4123130f79cbb7e5293ec2

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 4 items

tests/unit/test_brief_collectors.py FF.F                                 [100%]

=================================== FAILURES ===================================
_________________ test_waiting_collects_overdue_follow_through _________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-657/test_waiting_collects_overdue_0')

    def test_waiting_collects_overdue_follow_through(tmp_path):
        service = _service(tmp_path)
        with service._db._connection() as conn:
>           _action(
                conn,
                "action-overdue",
                "Send the revised proposal",
                owner="Ada",
                due=(date.today() - timedelta(days=1)).isoformat(),
            )

tests/unit/test_brief_collectors.py:26: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

conn = <sqlite3.Connection object at 0x108521120>, item_id = 'action-overdue'
task = 'Send the revised proposal'

    def _action(conn, item_id: str, task: str, *, owner: str | None, due: str | None) -> None:
>       conn.execute(
            """INSERT INTO action_items
               (id, task, owner, due, status, review_state, created_at)
               VALUES (?, ?, ?, ?, 'open', 'accepted', datetime('now'))""",
            (item_id, task, owner, due),
        )
E       sqlite3.IntegrityError: NOT NULL constraint failed: action_items.meeting_id

tests/unit/test_brief_collectors.py:15: IntegrityError
______________ test_waiting_collects_high_priority_cadence_loops _______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-657/test_waiting_collects_high_pri0')

    def test_waiting_collects_high_priority_cadence_loops(tmp_path):
        service = _service(tmp_path)
        with service._db._connection() as conn:
            conn.execute(
                """INSERT INTO cadence_loops
                   (id, source_type, source_id, title, status, priority)
                   VALUES ('loop-high', 'manual', 'source-1', 'Confirm launch owner', 'open', 'high')"""
            )
            conn.execute(
                """INSERT INTO cadence_loops
                   (id, source_type, source_id, title, status, priority)
                   VALUES ('loop-closed', 'manual', 'source-2', 'Already resolved', 'closed', 'urgent')"""
            )
    
        items = service._collect_waiting(None)
    
>       assert [(item.text, item.source_ref, item.priority) for item in items] == [
            ("Open loop: Confirm launch owner", "cadence_loop:loop-high", 100)
        ]
E       AssertionError: assert [('Unassigned...p-high', 200)] == [('Open loop:...p-high', 100)]
E         
E         At index 0 diff: ('Unassigned: Confirm launch owner', 'cadence_loop:loop-high', 200) != ('Open loop: Confirm launch owner', 'cadence_loop:loop-high', 100)
E         Use -v to get more diff

tests/unit/test_brief_collectors.py:58: AssertionError
_________ test_waiting_prioritizes_overdue_before_unassigned_and_loops _________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-657/test_waiting_prioritizes_overd0')

    def test_waiting_prioritizes_overdue_before_unassigned_and_loops(tmp_path):
        service = _service(tmp_path)
        with service._db._connection() as conn:
>           _action(
                conn,
                "action-overdue",
                "Escalate incident",
                owner="Ada",
                due=(date.today() - timedelta(days=1)).isoformat(),
            )

tests/unit/test_brief_collectors.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

conn = <sqlite3.Connection object at 0x109dc6020>, item_id = 'action-overdue'
task = 'Escalate incident'

    def _action(conn, item_id: str, task: str, *, owner: str | None, due: str | None) -> None:
>       conn.execute(
            """INSERT INTO action_items
               (id, task, owner, due, status, review_state, created_at)
               VALUES (?, ?, ?, ?, 'open', 'accepted', datetime('now'))""",
            (item_id, task, owner, due),
        )
E       sqlite3.IntegrityError: NOT NULL constraint failed: action_items.meeting_id

tests/unit/test_brief_collectors.py:15: IntegrityError
=========================== short test summary info ============================
FAILED tests/unit/test_brief_collectors.py::test_waiting_collects_overdue_follow_through
FAILED tests/unit/test_brief_collectors.py::test_waiting_collects_high_priority_cadence_loops
FAILED tests/unit/test_brief_collectors.py::test_waiting_prioritizes_overdue_before_unassigned_and_loops
========================= 3 failed, 1 passed in 0.53s ==========================
```

### Captured run — 2026-08-08T01:01:17Z

- **Command:** `uv run pytest -q tests/unit/test_brief_collectors.py -v -k waiting`
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
collected 9 items / 5 deselected / 4 selected

tests/unit/test_brief_collectors.py ....                                 [100%]

======================= 4 passed, 5 deselected in 0.53s ========================
```

### Captured run — 2026-08-08T01:01:54Z

- **Command:** `uv run pytest -q tests/unit/test_brief_collectors.py -v -k waiting`
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
collected 15 items / 11 deselected / 4 selected

tests/unit/test_brief_collectors.py ....                                 [100%]

======================= 4 passed, 11 deselected in 0.54s =======================
```
