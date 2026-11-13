"""The latest receipt of an effect ref is one indexed read of the journal.

Setup status asks ``JournalStore.last_receipt_for_ref`` for three egress refs
on every page load. It read every admitted row of ``kernel_journal`` into
Python and parsed its JSON there: 1.7 s for the three refs on the owner's
journal of 489,000 rows (2026-11-13). The properties: the admitted rows come
from the partial covering index and the table is not scanned, on a new
database and on an old one; and the answer is the same as before.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel import journal as journal_module
from holdspeak.kernel.journal import JournalStore

INDEX = "idx_kernel_journal_admitted_refs"


def _plan(db: Database) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute(
            "EXPLAIN QUERY PLAN " + journal_module.LAST_RECEIPT_FOR_REF_SQL, ('"x"', "x")
        ).fetchall()
    return [str(row[-1]) for row in rows]


def _assert_no_scan_of_the_journal_table(db: Database) -> None:
    plan = _plan(db)
    admitted = [step for step in plan if step.startswith(("SCAN a", "SEARCH a"))]
    assert admitted and all(INDEX in step for step in admitted), plan
    receipts = [step for step in plan if step.startswith(("SCAN r", "SEARCH r"))]
    assert receipts and all(step.startswith("SEARCH r") for step in receipts), plan


def test_the_admitted_rows_come_from_the_partial_index(tmp_path: Path) -> None:
    db = Database(tmp_path / "journal.db")
    try:
        _assert_no_scan_of_the_journal_table(db)
    finally:
        db.close()


def test_an_old_database_gains_the_index_when_it_opens(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    db = Database(path)
    with db._connection() as conn:
        conn.execute(f"DROP INDEX {INDEX}")
        conn.commit()
    db.close()

    reopened = Database(path)
    try:
        _assert_no_scan_of_the_journal_table(reopened)
    finally:
        reopened.close()


def test_the_answer_is_the_newest_receipted_operation_that_names_the_ref(tmp_path: Path) -> None:
    db = Database(tmp_path / "answers.db")
    try:
        store = JournalStore(db._connection)
        # Two refs, three receipts. The newest admitted operation of
        # "egress:slack" has no receipt yet, so the one before it answers.
        store.append("operation.admitted", "op-1", refs=("egress:slack",))
        first = store.append("operation.receipt", "op-1")
        store.append("operation.admitted", "op-2", refs=("project:p", "egress:webhook"))
        store.append("operation.receipt", "op-2")
        second_webhook = store.append("operation.receipt", "op-2")
        store.append("operation.admitted", "op-3", refs=("egress:slack",))
        # A ref that only CONTAINS the asked ref's text is not the ref.
        store.append("operation.admitted", "op-4", refs=("egress:slack-archive",))
        store.append("operation.receipt", "op-4")

        assert store.last_receipt_for_ref("egress:slack") == str(first["timestamp"])
        assert store.last_receipt_for_ref("egress:webhook") == str(second_webhook["timestamp"])
        assert store.last_receipt_for_ref("egress:github") is None
        assert store.last_receipt_for_ref("slack") is None
    finally:
        db.close()
