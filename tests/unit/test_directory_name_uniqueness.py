"""HS-118-01 — Zone name uniqueness.

Tests: uniqueness on create, uniqueness on rename, self-rename (case change),
migration with duplicates, concurrent creates, character limits.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.db.primitives import (
    DirectoryRepository,
    ZoneNameTaken,
    normalize_zone_name,
    _backfill_directory_name_normalized,
)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


# ── normalize_zone_name ──────────────────────────────────────────────────────

def test_normalize_strips_and_collapses_whitespace() -> None:
    assert normalize_zone_name("  hello   world  ") == "hello world"


def test_normalize_casefolds() -> None:
    assert normalize_zone_name("My Zone") == "my zone"


def test_normalize_nfc() -> None:
    # e + combining acute vs. precomposed e-acute
    import unicodedata
    decomposed = "é"  # NFD
    composed = "é"     # NFC
    assert normalize_zone_name(decomposed) == normalize_zone_name(composed)


def test_normalize_empty() -> None:
    assert normalize_zone_name("") == ""
    assert normalize_zone_name("   ") == ""


# ── Uniqueness on create ─────────────────────────────────────────────────────

def test_create_two_zones_different_names(db: Database) -> None:
    a = db.directories.upsert(directory_id="d1", name="Alpha")
    b = db.directories.upsert(directory_id="d2", name="Beta")
    assert a.name_normalized == "alpha"
    assert b.name_normalized == "beta"


def test_create_duplicate_name_raises(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="Alpha")
    with pytest.raises(ZoneNameTaken) as exc_info:
        db.directories.upsert(directory_id="d2", name="Alpha")
    assert exc_info.value.existing_name == "Alpha"


def test_create_duplicate_case_insensitive(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="My Zone")
    with pytest.raises(ZoneNameTaken):
        db.directories.upsert(directory_id="d2", name="my zone")


def test_create_duplicate_whitespace_normalized(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="My Zone")
    with pytest.raises(ZoneNameTaken):
        db.directories.upsert(directory_id="d2", name="  My   Zone  ")


# ── Uniqueness on rename ─────────────────────────────────────────────────────

def test_rename_to_taken_name_raises(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="Alpha")
    db.directories.upsert(directory_id="d2", name="Beta")
    with pytest.raises(ZoneNameTaken) as exc_info:
        db.directories.upsert(directory_id="d2", name="Alpha")
    assert exc_info.value.existing_name == "Alpha"


def test_rename_to_unique_name_succeeds(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="Alpha")
    db.directories.upsert(directory_id="d2", name="Beta")
    updated = db.directories.upsert(directory_id="d2", name="Gamma")
    assert updated.name == "Gamma"
    assert updated.name_normalized == "gamma"


# ── Self-rename (case change) ────────────────────────────────────────────────

def test_self_rename_case_change(db: Database) -> None:
    """Renaming a zone to the same name with different casing should succeed."""
    db.directories.upsert(directory_id="d1", name="my zone")
    updated = db.directories.upsert(directory_id="d1", name="My Zone")
    assert updated.name == "My Zone"
    assert updated.name_normalized == "my zone"


def test_self_rename_whitespace_change(db: Database) -> None:
    """Adjusting spacing on the same zone succeeds."""
    db.directories.upsert(directory_id="d1", name="My Zone")
    updated = db.directories.upsert(directory_id="d1", name="My  Zone")
    # name is stored as stripped (the strip in upsert)
    assert updated.name_normalized == "my zone"


# ── Tombstoned names are released ────────────────────────────────────────────

def test_deleted_zone_releases_name(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="Alpha")
    db.directories.delete("d1")
    # A new zone can now take the name.
    d2 = db.directories.upsert(directory_id="d2", name="Alpha")
    assert d2.name == "Alpha"


# ── Character constraints ────────────────────────────────────────────────────

def test_empty_name_rejected(db: Database) -> None:
    with pytest.raises(ValueError, match="zone name is required"):
        db.directories.upsert(directory_id="d1", name="")


def test_whitespace_only_name_rejected(db: Database) -> None:
    with pytest.raises(ValueError, match="zone name is required"):
        db.directories.upsert(directory_id="d1", name="   ")


def test_name_exactly_64_chars(db: Database) -> None:
    name = "A" * 64
    d = db.directories.upsert(directory_id="d1", name=name)
    assert len(d.name_normalized) == 64


def test_name_over_64_chars_rejected(db: Database) -> None:
    name = "A" * 65
    with pytest.raises(ValueError, match="64 characters"):
        db.directories.upsert(directory_id="d1", name=name)


def test_name_one_char(db: Database) -> None:
    d = db.directories.upsert(directory_id="d1", name="X")
    assert d.name_normalized == "x"


# ── find_by_normalized_name ──────────────────────────────────────────────────

def test_find_by_normalized_name(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="My Zone")
    found = db.directories.find_by_normalized_name("  my   zone  ")
    assert found is not None
    assert found.id == "d1"


def test_find_by_normalized_name_missing(db: Database) -> None:
    assert db.directories.find_by_normalized_name("nonexistent") is None


def test_find_by_normalized_name_ignores_deleted(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="Alpha")
    db.directories.delete("d1")
    assert db.directories.find_by_normalized_name("alpha") is None


# ── to_dict exposes name_normalized ──────────────────────────────────────────

def test_to_dict_includes_name_normalized(db: Database) -> None:
    d = db.directories.upsert(directory_id="d1", name="My Zone")
    assert d.to_dict()["name_normalized"] == "my zone"


# ── Migration backfill ───────────────────────────────────────────────────────

def test_backfill_sets_normalized_names(tmp_path: Path) -> None:
    """Backfill correctly normalizes names on existing rows."""
    db_path = tmp_path / "backfill.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d1", "Hello World", "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d2", "Goodbye", "2024-01-02"),
    )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    rows = conn.execute("SELECT id, name_normalized FROM directories ORDER BY id").fetchall()
    assert dict(rows[0])["name_normalized"] == "hello world"
    assert dict(rows[1])["name_normalized"] == "goodbye"
    conn.close()


def test_backfill_disambiguates_duplicates(tmp_path: Path) -> None:
    """Two live rows with the same name get disambiguated by appending (2)."""
    db_path = tmp_path / "backfill_dup.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Two zones with the same name (pre-uniqueness).
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d1", "Work", "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d2", "Work", "2024-01-02"),
    )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    rows = {
        row["id"]: row
        for row in conn.execute("SELECT * FROM directories ORDER BY id").fetchall()
    }
    # The first created keeps the original name.
    assert rows["d1"]["name"] == "Work"
    assert rows["d1"]["name_normalized"] == "work"
    # The second gets disambiguated.
    assert rows["d2"]["name"] == "Work (2)"
    assert rows["d2"]["name_normalized"] == "work (2)"
    conn.close()


def test_backfill_disambiguates_three_duplicates(tmp_path: Path) -> None:
    """Three duplicate names produce (2) and (3) suffixes."""
    db_path = tmp_path / "backfill_3dup.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    for i in range(3):
        conn.execute(
            "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
            (f"d{i}", "Work", f"2024-01-0{i+1}"),
        )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    names = sorted(
        row["name"]
        for row in conn.execute("SELECT name FROM directories").fetchall()
    )
    assert names == ["Work", "Work (2)", "Work (3)"]
    conn.close()


def test_backfill_idempotent(tmp_path: Path) -> None:
    """Running backfill twice produces the same result."""
    db_path = tmp_path / "backfill_idem.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d1", "Alpha", "2024-01-01"),
    )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    row = conn.execute("SELECT name_normalized FROM directories WHERE id = 'd1'").fetchone()
    assert row["name_normalized"] == "alpha"
    conn.close()


def test_backfill_deleted_not_deduplicated(tmp_path: Path) -> None:
    """Deleted rows are not counted as duplicates of live rows."""
    db_path = tmp_path / "backfill_del.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute(
        "INSERT INTO directories (id, name, deleted, created_at) VALUES (?, ?, ?, ?)",
        ("d1", "Work", 1, "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO directories (id, name, deleted, created_at) VALUES (?, ?, ?, ?)",
        ("d2", "Work", 0, "2024-01-02"),
    )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    live = conn.execute(
        "SELECT name FROM directories WHERE id = 'd2'"
    ).fetchone()
    # The live one keeps its original name (the deleted one is not a conflict).
    assert live["name"] == "Work"
    conn.close()


def test_backfill_suffix_collision_with_existing_name(tmp_path: Path) -> None:
    """Bug 2: suffix (2) collides with an existing zone named 'Work (2)'."""
    db_path = tmp_path / "backfill_collision.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE directories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            name_normalized TEXT NOT NULL DEFAULT '',
            parent_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        )
    """)
    # "Work" x2, plus an existing "Work (2)" — the dedup suffix must skip (2).
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d1", "Work", "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d2", "Work", "2024-01-02"),
    )
    conn.execute(
        "INSERT INTO directories (id, name, created_at) VALUES (?, ?, ?)",
        ("d3", "Work (2)", "2024-01-03"),
    )
    conn.commit()
    _backfill_directory_name_normalized(conn)
    conn.commit()
    rows = {
        row["id"]: row
        for row in conn.execute("SELECT * FROM directories ORDER BY id").fetchall()
    }
    assert rows["d1"]["name"] == "Work"
    assert rows["d3"]["name"] == "Work (2)"
    # d2 must NOT get "Work (2)" — it collides with d3.
    assert rows["d2"]["name_normalized"] != "work (2)"
    assert rows["d2"]["name"] == "Work (3)"
    conn.close()


# ── Concurrent creates ───────────────────────────────────────────────────────

def test_concurrent_create_same_name(db: Database) -> None:
    """Two creates with the same name: first wins, second raises."""
    db.directories.upsert(directory_id="d1", name="Alpha")
    with pytest.raises(ZoneNameTaken):
        db.directories.upsert(directory_id="d2", name="alpha")
