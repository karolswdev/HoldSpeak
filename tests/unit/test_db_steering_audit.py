"""The steering_audit repository (HS-87-03) against a real temp DB."""

from __future__ import annotations

import hashlib

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.db.steering import TEXT_HEAD_CHARS


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_record_and_list_roundtrip_newest_first(db) -> None:
    first = db.steering.record(
        session_key="claude:a",
        agent="claude",
        pane_id="%5",
        text="ship it",
        grounding=["meeting:m1"],
        submit=True,
        outcome="delivered",
        operation={"effect_class": "terminal/type_text_and_keys", "destination": "%5"},
        policy_snapshot={
            "mode": "yolo", "authority_basis": "control_posture",
            "policy_version": "operation-policy/v2",
        },
    )
    second = db.steering.record(
        session_key="claude:a",
        agent="claude",
        pane_id=None,
        text="ship it again",
        outcome="unarmed",
        detail="no grant",
    )
    entries = db.steering.list()
    assert [e.id for e in entries] == [second, first]
    newest = entries[0]
    assert newest.outcome == "unarmed"
    assert newest.detail == "no grant"
    assert newest.pane_id is None
    oldest = entries[1]
    assert oldest.grounding == ["meeting:m1"]
    assert oldest.submit is True
    assert oldest.operation["destination"] == "%5"
    assert oldest.policy_snapshot["authority_basis"] == "control_posture"
    assert oldest.text_sha256 == hashlib.sha256(b"ship it").hexdigest()


def test_full_text_is_never_stored(db) -> None:
    secret_tail = "S3CRET-TAIL-" * 40
    long_text = ("x" * TEXT_HEAD_CHARS) + secret_tail
    db.steering.record(session_key="claude:a", text=long_text, outcome="delivered")
    entry = db.steering.list()[0]
    assert len(entry.text_head) == TEXT_HEAD_CHARS
    assert "S3CRET" not in entry.text_head
    assert entry.text_sha256 == hashlib.sha256(
        long_text.encode("utf-8")
    ).hexdigest()


def test_list_filters_by_session_and_clamps_limit(db) -> None:
    for i in range(5):
        db.steering.record(session_key="claude:a", text=f"a{i}", outcome="delivered")
    db.steering.record(session_key="codex:b", text="b", outcome="delivered")
    only_a = db.steering.list(session_key="claude:a")
    assert len(only_a) == 5
    assert all(e.session_key == "claude:a" for e in only_a)
    assert len(db.steering.list(limit=2)) == 2


def test_v11_database_upgrades_to_current_steering_receipt_shape(tmp_path) -> None:
    # A stamped v11 file (no steering_audit) lands the table and policy columns.
    import sqlite3

    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, "
            "applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.execute("INSERT INTO schema_version (version) VALUES (11)")
    reset_database()
    db = Database(path)
    assert db.steering.list() == []
    with db._connection() as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(steering_audit)")
        }
    assert {"operation_json", "policy_snapshot_json"}.issubset(columns)
    reset_database()


def test_v21_steering_rows_gain_empty_policy_snapshots_without_data_loss(
    tmp_path,
) -> None:
    import sqlite3

    path = tmp_path / "v21.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, "
            "applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.execute("INSERT INTO schema_version (version) VALUES (21)")
        conn.execute(
            """CREATE TABLE steering_audit (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL DEFAULT (datetime('now')),
               session_key TEXT NOT NULL, agent TEXT NOT NULL DEFAULT '',
               pane_id TEXT, text_sha256 TEXT NOT NULL,
               text_head TEXT NOT NULL DEFAULT '',
               grounding_json TEXT NOT NULL DEFAULT '[]',
               submit INTEGER NOT NULL DEFAULT 1,
               outcome TEXT NOT NULL, detail TEXT)"""
        )
        conn.execute(
            """INSERT INTO steering_audit
               (session_key,text_sha256,text_head,outcome)
               VALUES ('claude:kept','hash','kept','delivered')"""
        )
    reset_database()
    db = Database(path)
    entry = db.steering.list()[0]
    assert entry.session_key == "claude:kept"
    assert entry.operation == {}
    assert entry.policy_snapshot == {}
    reset_database()
