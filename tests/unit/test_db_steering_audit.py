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


def test_v11_database_upgrades_to_v12_with_the_table(tmp_path) -> None:
    # A stamped v11 file (no steering_audit) must land the table on open.
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
    reset_database()
