"""The safe-by-default schema policy (HS-50-02).

`_ensure_schema` must never silently destroy a user's data on upgrade. This
pins the four-way matrix that is the forward upgrade contract:

- fresh / empty -> create at the current version
- stored == SCHEMA_VERSION -> no-op
- stored < SCHEMA_VERSION -> back up first, then apply
- stored > SCHEMA_VERSION -> refuse, leave the data untouched
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from holdspeak.db import Database, SCHEMA_VERSION, SchemaVersionError, reset_database
from holdspeak.db import core as db_core


@pytest.fixture
def db_path(tmp_path) -> Path:
    reset_database()
    yield tmp_path / "holdspeak.db"
    reset_database()


def _stamp_version(path: Path, version: int) -> None:
    """Set the stored schema version on an existing database file."""
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
    finally:
        conn.close()


def _stored_version(path: Path) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        conn.close()


def test_fresh_db_is_created_at_current_version(db_path: Path) -> None:
    assert not db_path.exists()
    Database(db_path)
    assert db_path.exists()
    assert _stored_version(db_path) == SCHEMA_VERSION


def test_at_version_is_a_noop(db_path: Path, monkeypatch) -> None:
    Database(db_path)
    # Reopening must not back up or rebuild; no .bak siblings appear.
    calls = []
    monkeypatch.setattr(db_core, "backup_database", lambda p: calls.append(p) or p)
    Database(db_path)
    assert calls == []
    backups = list(db_path.parent.glob("*.bak"))
    assert backups == []


def test_older_db_is_backed_up_then_applied(db_path: Path, monkeypatch) -> None:
    # Create a real DB at the current version and write a row.
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO meetings (id, title, started_at) VALUES ('m1', 'Kept', datetime('now'))"
    )
    conn.commit()
    conn.close()

    # Now pretend this build is newer than the database (SCHEMA_VERSION is 1, so
    # there is no representable older version yet; bumping the constant in the
    # fixture simulates the first real schema bump).
    monkeypatch.setattr(db_core, "SCHEMA_VERSION", SCHEMA_VERSION + 1)
    backups: list[Path] = []
    real_backup = db_core.backup_database
    monkeypatch.setattr(
        db_core, "backup_database", lambda p: backups.append(real_backup(p)) or backups[-1]
    )

    Database(db_path)

    # A backup was taken before the apply, and the data survived.
    assert len(backups) == 1 and backups[0].exists()
    assert _stored_version(db_path) == SCHEMA_VERSION + 1
    conn = sqlite3.connect(str(db_path))
    kept = conn.execute("SELECT title FROM meetings WHERE id = 'm1'").fetchone()
    conn.close()
    assert kept and kept[0] == "Kept"


def test_newer_db_is_refused_and_left_untouched(db_path: Path) -> None:
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO meetings (id, title, started_at) VALUES ('m1', 'Untouched', datetime('now'))"
    )
    conn.commit()
    conn.close()
    _stamp_version(db_path, SCHEMA_VERSION + 1)
    before = db_path.read_bytes()

    with pytest.raises(SchemaVersionError) as excinfo:
        Database(db_path)

    assert "newer HoldSpeak" in str(excinfo.value)
    assert "left untouched" in str(excinfo.value)
    # The file is byte-for-byte unchanged and no backup was made.
    assert db_path.read_bytes() == before
    assert list(db_path.parent.glob("*.bak")) == []


def test_backup_database_copies_to_timestamped_sibling(db_path: Path) -> None:
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO meetings (id, title, started_at) VALUES ('m1', 'Snap', datetime('now'))"
    )
    conn.commit()
    conn.close()

    backup = db_core.backup_database(db_path)
    assert backup.exists()
    assert backup.name.startswith(db_path.name)
    assert backup.name.endswith(".bak")
    # A consistent snapshot, not a byte copy: it opens and carries the data.
    conn = sqlite3.connect(str(backup))
    row = conn.execute("SELECT title FROM meetings WHERE id = 'm1'").fetchone()
    conn.close()
    assert row and row[0] == "Snap"


def test_backup_database_does_not_clobber(db_path: Path) -> None:
    Database(db_path)
    first = db_core.backup_database(db_path)
    second = db_core.backup_database(db_path)
    assert first != second
    assert first.exists() and second.exists()
