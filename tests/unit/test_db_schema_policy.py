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

    # Now pretend this build is newer than the database by bumping the constant in
    # the fixture, exercising the backup-then-apply path that a real schema bump
    # (e.g. v1 -> v2, the Primitive Framework tables) takes for an older DB.
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


def test_v8_db_gains_model_manifests_via_the_bump(db_path: Path) -> None:
    """The v9 regression pin (the 2026-07-06 connect saga, defect #2).

    model_manifests shipped additively WITHOUT a version bump, so a v8-stamped
    database read `stored == SCHEMA_VERSION`, never re-ran SCHEMA_SQL, and
    /api/sync/pull 500'd on the missing table. A v8 DB missing the table must
    now take the backup-then-apply path and land it.
    """
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE model_manifests")  # what a real v8 install looks like
    conn.execute("DELETE FROM schema_version")  # the reader takes MAX(version); clear the v9 stamp
    conn.commit()
    conn.close()
    _stamp_version(db_path, 8)

    db = Database(db_path)

    assert _stored_version(db_path) == SCHEMA_VERSION
    assert db.model_manifests.list() == []  # the table exists and reads clean
    backups = list(db_path.parent.glob("*.bak"))
    assert len(backups) == 1  # safe-by-default: backed up before the apply


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


def test_upgrade_adds_the_profiles_node_column(tmp_path):
    """The live-walk find: a column ADDED to an existing table is invisible to
    `CREATE TABLE IF NOT EXISTS` — a v10 database upgrading must gain
    `profiles.node` (with existing rows preserved), not a stamped version over
    a stale shape."""
    import sqlite3

    from holdspeak.db import Database

    path = tmp_path / "old.db"
    db = Database(path)
    db.profiles.upsert(profile_id="p-keep", name="Kept", kind="openAICompatible",
                       base_url="http://x.example/v1", model="m")
    del db

    conn = sqlite3.connect(str(path))
    conn.execute("ALTER TABLE profiles DROP COLUMN node")
    conn.execute("DELETE FROM schema_version")
    conn.execute("INSERT INTO schema_version (version) VALUES (10)")
    conn.commit()
    conn.close()

    upgraded = Database(path)
    kept = upgraded.profiles.get("p-keep")
    assert kept is not None and kept.name == "Kept" and kept.node == ""
    upgraded.profiles.upsert(profile_id="p-mesh", name="Edge", kind="meshNode",
                             node="walk-edge")
    assert upgraded.profiles.get("p-mesh").node == "walk-edge"
