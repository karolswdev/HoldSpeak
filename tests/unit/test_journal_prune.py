"""Dead Telegram polls leave the journal; the chain still verifies.

Until 2026-11-13 each long poll that timed out was one full egress operation
(five journal records). ``JournalStore.prune_operations`` removes them and
leaves one signed checkpoint for each run of removed records;
``scripts/prune_empty_polls.py`` is the tool that runs it with a backup.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest

import holdspeak.db.core as db_core
from holdspeak.db import Database
from holdspeak.kernel import journal_prune
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS, run_external_egress
from holdspeak.kernel.journal import JournalStore
from holdspeak.kernel.model import KernelRefused
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import telegram_reach

POLL = "telegram:getupdates:bot"


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "prune.db")
    monkeypatch.setattr(db_core, "_db", db)
    for held in (EGRESS_EXECUTIONS._plans, EGRESS_EXECUTIONS._operation_ids, EGRESS_EXECUTIONS._results):
        held.clear()
    broker = kernel_runtime._configure(db)
    monkeypatch.setattr(kernel_runtime, "_broker", broker)
    monkeypatch.setattr(kernel_runtime, "_database_id", id(db))
    return db, broker, JournalStore(db._connection)


def _dead_poll(offset: int) -> None:
    def no_answer() -> None:
        raise telegram_reach._PollFailed("no answer")

    assert telegram_reach._record_egress(POLL, "reach_update_cursor", {"offset": offset}, no_answer)


def _poll_with_updates(offset: int) -> None:
    assert telegram_reach._record_egress(POLL, "reach_update_cursor", {"offset": offset}, lambda: None)


def _send(text: str, *, fails: bool = False) -> None:
    def sender() -> dict[str, bool]:
        if fails:
            raise TimeoutError("timed out")
        return {"ok": True}

    try:
        run_external_egress(
            connector_id="reach-telegram", destination="telegram:sendmessage:chat",
            data_classes=("reach_package",), payload_material={"text": text}, sender=sender,
            allowed_destinations=("telegram:sendmessage:chat",),
        )
    except TimeoutError:
        pass


def _other_operation(broker: Any, key: str) -> str:
    parent = broker.parent_run_controller.start(
        Principal(PrincipalKind.OWNER, "owner-session"), kind="sequence",
        definition_ref=f"sequence:{key}", definition_revision="rev-1", input_snapshot={"input": "proof"},
        deadline_at=time.time() + 300, child_budget=1, idempotency_key=f"prune-parent-{key}",
    )
    return str(parent.operation_id)


def _operations(db: Any) -> list[tuple[str, str]]:
    with db._connection() as conn:
        return [(str(name), str(state)) for name, state in conn.execute(
            "SELECT name, state FROM kernel_operations ORDER BY created_at, operation_id")]


def _history(rig) -> str:
    """Dead polls at the start, in the middle (two runs) and at the end, with
    a send, another kind of operation and a poll with updates among them."""
    _db, broker, _store = rig
    _dead_poll(1)
    _dead_poll(2)
    _send("one")
    _dead_poll(3)
    other = _other_operation(broker, "one")
    _poll_with_updates(4)
    _dead_poll(5)
    _send("two", fails=True)
    _dead_poll(6)
    return other


def test_only_the_dead_polls_go_and_the_chain_verifies(rig) -> None:
    db, _broker, store = rig
    other = _history(rig)
    before = store.verify()
    kept_before = [item for item in _operations(db) if item != ("external.egress", "indeterminate")]
    dead = store.dead_poll_operation_ids()
    assert len(dead) == 5  # the failed send is indeterminate too, and is not a poll

    counts = store.prune_operations(dead)

    # The newest record of the stream is a dead poll's: that one stays.
    assert counts["operations"] == 4
    after = store.verify()
    assert after["pruned"] == counts["journal_records"] == before["records"] - after["records"]
    assert after["head"] == before["head"]
    left = _operations(db)
    assert sorted(left) == sorted([*kept_before, ("external.egress", "indeterminate"),
                                   ("external.egress", "indeterminate")])  # the failed send, the newest poll
    assert db_has(db, "kernel_operations", other)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_journal_prunes").fetchone()[0] == 3
        orphans = conn.execute(
            "SELECT COUNT(*) FROM kernel_receipts WHERE operation_id NOT IN (SELECT operation_id FROM kernel_operations)"
        ).fetchone()[0]
    assert orphans == 0
    assert store.last_receipt_for_ref("connector:reach-telegram") is not None

    # The journal goes on: a new record links to the head, and a second prune
    # joins its run to the checkpoint beside it.
    _send("three")
    _dead_poll(7)
    _send("four")
    again = store.prune_operations(store.dead_poll_operation_ids())
    assert again["operations"] == 2
    assert store.verify()["pruned"] == counts["journal_records"] + again["journal_records"]


def db_has(db: Any, table: str, operation_id: str) -> bool:
    with db._connection() as conn:
        return conn.execute(f"SELECT 1 FROM {table} WHERE operation_id=?", (operation_id,)).fetchone() is not None


@pytest.mark.parametrize("what", ["a send", "a failed send", "a poll with updates", "another operation", "no such"])
def test_what_is_not_a_dead_poll_is_refused_and_nothing_goes(rig, what: str) -> None:
    db, _broker, store = rig
    other = _history(rig)
    with db._connection() as conn:
        def egress(data_class: str, state: str) -> str:
            return str(conn.execute(
                """SELECT o.operation_id FROM kernel_operations o JOIN kernel_journal a
                     ON a.operation_id = o.operation_id AND a.event_type = 'operation.admitted'
                    WHERE o.state = ? AND a.refs_json LIKE ? LIMIT 1""",
                (state, f'%"data-class:{data_class}"%')).fetchone()[0])

        target = {
            "a send": lambda: egress("reach_package", "succeeded"),
            "a failed send": lambda: egress("reach_package", "indeterminate"),
            "a poll with updates": lambda: egress("reach_update_cursor", "succeeded"),
            "another operation": lambda: other,
            "no such": lambda: "op-that-is-not-there",
        }[what]()
    before = (_operations(db), store.verify())

    with pytest.raises(KernelRefused) as refused:
        store.prune_operations([*store.dead_poll_operation_ids(), target])
    assert refused.value.reason == "journal_prune_not_a_dead_poll"

    assert (_operations(db), store.verify()) == before
    assert before[1]["pruned"] == 0


@pytest.mark.parametrize("change", [
    "UPDATE kernel_journal_prunes SET records = records + 5, last_sequence = last_sequence + 5",
    "UPDATE kernel_journal_prunes SET class = 'anything'",
    "UPDATE kernel_journal_prunes SET pruned_at = pruned_at - 86400",
    "UPDATE kernel_journal_prunes SET previous_sha256 = 'sha256:other'",
    "DELETE FROM kernel_journal_prunes WHERE first_sequence = (SELECT MIN(first_sequence) FROM kernel_journal_prunes)",
])
def test_a_tampered_checkpoint_fails_verification(rig, change: str) -> None:
    db, _broker, store = rig
    _history(rig)
    store.prune_operations(store.dead_poll_operation_ids())
    assert store.verify()["ok"]
    with db._connection() as conn:
        conn.execute(change)
    with pytest.raises(KernelRefused) as refused:
        store.verify()
    assert refused.value.reason in ("journal_prune_checkpoint_invalid", "journal_previous_hash_mismatch")


def test_a_checkpoint_cannot_cover_a_record_that_was_not_a_dead_poll(rig) -> None:
    """Remove a send by hand and write a checkpoint for it without the
    database's secret: verification refuses it."""
    db, _broker, store = rig
    _history(rig)
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT stream_sequence, previous_sha256, record_sha256 FROM kernel_journal
                WHERE operation_id = (SELECT operation_id FROM kernel_journal
                                       WHERE refs_json LIKE '%data-class:reach_package%' LIMIT 1)
                ORDER BY stream_sequence""").fetchall()
        first, last = rows[0], rows[-1]
        forged = {"stream": "operations", "first_sequence": first[0], "last_sequence": last[0],
                  "records": len(rows), "class": journal_prune.DEAD_POLL_CLASS,
                  "previous_sha256": first[1], "last_sha256": last[2], "pruned_at": 1.0}
        conn.execute("DELETE FROM kernel_journal WHERE stream_sequence BETWEEN ? AND ?", (first[0], last[0]))
        conn.execute(
            "INSERT INTO kernel_journal_prunes VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("prune_forged", *[forged[field] for field in journal_prune._FIELDS[:5]],
             forged["previous_sha256"], forged["last_sha256"], forged["pruned_at"],
             journal_prune.checkpoint_hash("a-guessed-secret", forged)))
    with pytest.raises(KernelRefused) as refused:
        store.verify()
    assert refused.value.reason == "journal_prune_checkpoint_invalid"


# ── the tool ─────────────────────────────────────────────────────────────

def _tool():
    path = Path(__file__).resolve().parents[2] / "scripts" / "prune_empty_polls.py"
    spec = importlib.util.spec_from_file_location("prune_empty_polls", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_tool_dry_run_counts_and_changes_nothing(rig, capsys) -> None:
    db, _broker, store = rig
    _history(rig)
    before = (_operations(db), store.verify())
    assert _tool().main(["--db", str(db.db_path)]) == 0
    told = capsys.readouterr().out
    assert "kernel_operations: would remove 5 of" in told and "Dry run: nothing was changed" in told
    assert (_operations(db), store.verify()) == before


def test_the_tool_refuses_while_a_hub_owns_the_database(rig, capsys, tmp_path, monkeypatch) -> None:
    db, _broker, store = rig
    _history(rig)
    tool = _tool()
    monkeypatch.setattr(tool, "hub_owner", lambda path: 4242)
    backup = tmp_path / "parked" / "before.db"
    assert tool.main(["--db", str(db.db_path), "--apply", "--backup", str(backup)]) == 3
    assert "Stop the hub" in capsys.readouterr().out
    assert not backup.exists() and store.verify()["pruned"] == 0


def test_the_tool_backs_up_then_prunes_and_the_database_still_opens(rig, capsys, tmp_path) -> None:
    db, _broker, store = rig
    _history(rig)
    kept = [item for item in _operations(db) if item != ("external.egress", "indeterminate")]
    all_before = len(_operations(db))
    tool = _tool()
    backup = tmp_path / "parked" / "before.db"
    assert tool.hub_owner(Path(db.db_path)) is None

    assert tool.main(["--db", str(db.db_path), "--apply", "--backup", str(backup)]) == 0

    told = capsys.readouterr().out
    assert "Removed: 4 operations" in told and "Chain verified" in told
    saved = sqlite3.connect(str(backup))
    assert saved.execute("SELECT COUNT(*) FROM kernel_operations").fetchone()[0] == all_before
    saved.close()
    opened = Database(Path(db.db_path))
    assert JournalStore(opened._connection).verify()["pruned"] == 20
    assert [item for item in _operations(opened) if item != ("external.egress", "indeterminate")] == kept
    # A second run does not write over the parked backup.
    with pytest.raises(SystemExit, match="A backup is at"):
        tool.main(["--db", str(db.db_path), "--apply", "--backup", str(backup)])
