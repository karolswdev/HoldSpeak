# Evidence - HS-127-02

- **Story:** HS-127-02 - Unify decision origins
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T01:25:37Z

- **Command:** `uv run pytest -q tests/unit/test_decision_receipt_service.py -v`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** bb0b61d7b189d9d4ce8af3c5244191eff19bcc0f

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 9 items

tests/unit/test_decision_receipt_service.py .F.F.....                    [100%]

=================================== FAILURES ===================================
________________ test_get_receipt_returns_all_fields_and_links _________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-687/test_get_receipt_returns_all_f0')

    def test_get_receipt_returns_all_fields_and_links(tmp_path):
        service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
        receipt = service.create(
            None,
            decision_text="Ship the receipt schema.",
            source_type="desk",
            source_id="adr-127",
        )
        with service._db._connection() as conn:
            conn.execute(
                """INSERT INTO decision_receipt_sources
                   (id, receipt_id, source_type, source_ref, created_at)
                   VALUES ('source-1', ?, 'artifact', 'artifact-127', '2026-08-07T00:00:00+00:00')""",
                (receipt["id"],),
            )
            conn.execute(
                """INSERT INTO decision_receipt_work
                   (id, receipt_id, work_type, work_ref, created_at)
                   VALUES ('work-1', ?, 'project', 'HS-127', '2026-08-07T00:00:00+00:00')""",
                (receipt["id"],),
            )
            conn.execute(
                """INSERT INTO decision_receipt_revisions
                   (id, receipt_id, field_name, old_value, new_value, created_at)
                   VALUES ('revision-1', ?, 'owner', NULL, 'Karol', '2026-08-07T00:00:00+00:00')""",
                (receipt["id"],),
            )
    
>       loaded = service.get(None, receipt["id"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_decision_receipt_service.py:66: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
holdspeak/services/observer.py:159: in sync_wrapper
    result = fn(self, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <holdspeak.services.decision_receipt_service.DecisionReceiptService object at 0x109b756d0>
principal = None, receipt_id = 'receipt-9fe46ac468784758a99bde0f2855a186'

    def get(self, principal: Any, receipt_id: str) -> dict[str, Any] | None:
        """Get a receipt by ID with its sources, work links, and revisions."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
            if row is None:
                return None
            receipt = self._receipt_dict(row)
            receipt["sources"] = [
>               self._source_dict(conn, source)
                ^^^^^^^^^^^^^^^^^
                for source in conn.execute(
                    """SELECT * FROM decision_receipt_sources
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            ]
E           AttributeError: 'DecisionReceiptService' object has no attribute '_source_dict'

holdspeak/services/decision_receipt_service.py:139: AttributeError
________ test_create_from_meeting_mints_idempotent_receipt_with_lineage ________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-687/test_create_from_meeting_mints0')

    def test_create_from_meeting_mints_idempotent_receipt_with_lineage(tmp_path):
        db = Database(tmp_path / "receipts.db")
        _accepted_meeting_decision(db)
        source_before = db.decisions.get("dec-127").to_dict()
        service = DecisionReceiptService(db)
    
        receipt = service.create_from_meeting(None, "dec-127")
        repeated = service.create_from_meeting(None, "dec-127")
>       loaded = service.get(None, receipt["id"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_decision_receipt_service.py:114: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
holdspeak/services/observer.py:159: in sync_wrapper
    result = fn(self, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <holdspeak.services.decision_receipt_service.DecisionReceiptService object at 0x109bd1310>
principal = None, receipt_id = 'receipt-b1bfda8f1fbe4331b6df97b94bed6e79'

    def get(self, principal: Any, receipt_id: str) -> dict[str, Any] | None:
        """Get a receipt by ID with its sources, work links, and revisions."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
            if row is None:
                return None
            receipt = self._receipt_dict(row)
            receipt["sources"] = [
>               self._source_dict(conn, source)
                ^^^^^^^^^^^^^^^^^
                for source in conn.execute(
                    """SELECT * FROM decision_receipt_sources
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            ]
E           AttributeError: 'DecisionReceiptService' object has no attribute '_source_dict'

holdspeak/services/decision_receipt_service.py:139: AttributeError
=========================== short test summary info ============================
FAILED tests/unit/test_decision_receipt_service.py::test_get_receipt_returns_all_fields_and_links
FAILED tests/unit/test_decision_receipt_service.py::test_create_from_meeting_mints_idempotent_receipt_with_lineage
========================= 2 failed, 7 passed in 0.93s ==========================
```

### Captured run — 2026-08-08T01:26:03Z

- **Command:** `uv run pytest -q tests/unit/test_decision_receipt_service.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bb0b61d7b189d9d4ce8af3c5244191eff19bcc0f

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 9 items

tests/unit/test_decision_receipt_service.py .........                    [100%]

============================== 9 passed in 0.85s ===============================
```

### Captured run — 2026-08-08T01:26:34Z

- **Command:** `uv run pytest -q tests/unit/test_decision_receipt_service.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bb0b61d7b189d9d4ce8af3c5244191eff19bcc0f

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 13 items

tests/unit/test_decision_receipt_service.py .............                [100%]

============================== 13 passed in 1.22s ==============================
```
