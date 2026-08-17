"""The reconcile-based schema policy (HS-137-03).

With the migration chain removed (HS-137-01), the schema contract is:

- fresh / empty -> reconcile creates the canonical shape
- current shape -> reconcile is a no-op (no ALTER, no error)
- "newer"-stamped DB -> opens WITHOUT error (no version gate)
- missing table/column -> reconcile self-heals the shape
- orphan table + its rows -> survive reconcile (additive only)
- backup is called when the shape changes and a db_path is provided

Most of these invariants are also covered in test_reconcile.py; this
file is the "policy home" that tests them through the Database() class
(the production entry point), not via reconcile_schema() directly.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from holdspeak.db import Database, SCHEMA_VERSION, reset_database
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


def test_reconcile_is_noop_on_current_db(db_path: Path, monkeypatch) -> None:
    Database(db_path)
    # Count backups after first open (the initial create may back up).
    backups_after_first = set(db_path.parent.glob("*.bak"))
    # Reopening a current DB must not call backup_database.
    calls = []
    real_backup = db_core.backup_database
    monkeypatch.setattr(db_core, "backup_database", lambda p: calls.append(p) or real_backup(p))
    reset_database()
    Database(db_path)
    assert calls == [], "backup_database called on a current DB"
    backups_after_second = set(db_path.parent.glob("*.bak"))
    assert backups_after_second == backups_after_first, "no new backups on second open"


def test_newer_stamped_db_opens_without_error(db_path: Path) -> None:
    """A5: a DB stamped with a version above the code opens without refusal."""
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO meetings (id, title, started_at) VALUES ('m1', 'Untouched', datetime('now'))"
    )
    conn.commit()
    conn.close()
    _stamp_version(db_path, SCHEMA_VERSION + 1)

    # Must NOT raise -- the old policy refused; the new one opens.
    db = Database(db_path)

    # The data is intact.
    with db._connection() as conn:
        row = conn.execute("SELECT title FROM meetings WHERE id = 'm1'").fetchone()
    assert row and row[0] == "Untouched"

    # The informational version stamp is present (never read to gate).
    conn = sqlite3.connect(str(db_path))
    versions = [r[0] for r in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    conn.close()
    assert SCHEMA_VERSION in versions


def test_missing_table_self_heals(db_path: Path) -> None:
    """A3: reconcile recreates a dropped table on reopen."""
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE IF EXISTS bookmarks")
    conn.commit()
    conn.close()

    db = Database(db_path)

    with db._connection() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
        ).fetchone()
    assert row is not None, "bookmarks should be restored after reconcile"


def test_missing_column_self_heals(db_path: Path) -> None:
    """A3: reconcile adds a missing column on reopen."""
    db = Database(db_path)
    with db._connection() as conn:
        # Verify the column exists first.
        cols = {row[1] for row in conn.execute("PRAGMA table_info(meetings)")}
        assert "title" in cols

    # Drop the column by rebuilding the table without it.
    conn = sqlite3.connect(str(db_path))
    conn.execute("ALTER TABLE meetings RENAME TO _meetings_old")
    # Create meetings without 'title'.
    conn.execute(
        "CREATE TABLE meetings (id TEXT PRIMARY KEY, started_at TEXT NOT NULL DEFAULT '')"
    )
    conn.execute("INSERT INTO meetings (id, started_at) SELECT id, started_at FROM _meetings_old")
    conn.execute("DROP TABLE _meetings_old")
    conn.commit()
    conn.close()
    reset_database()

    db = Database(db_path)
    with db._connection() as conn:
        cols_after = {row[1] for row in conn.execute("PRAGMA table_info(meetings)")}
    assert "title" in cols_after, "title column should be restored after reconcile"


def test_orphan_table_and_rows_survive(db_path: Path) -> None:
    """A1: an extra table not in SCHEMA_SQL survives reconcile with its rows."""
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS orphan_experiment ("
        "  id INTEGER PRIMARY KEY, data TEXT NOT NULL"
        ")"
    )
    conn.execute("INSERT INTO orphan_experiment (data) VALUES ('keep-me')")
    conn.execute("INSERT INTO orphan_experiment (data) VALUES ('and-me')")
    conn.commit()
    conn.close()
    reset_database()

    db = Database(db_path)

    with db._connection() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orphan_experiment'"
        ).fetchone()
        assert row is not None, "orphan table should survive reconcile"

        rows = conn.execute("SELECT data FROM orphan_experiment ORDER BY id").fetchall()
        assert [r[0] for r in rows] == ["keep-me", "and-me"]


def test_v8_db_gains_model_manifests_via_reconcile(db_path: Path) -> None:
    """The v9 regression pin (the 2026-07-06 connect saga, defect #2).

    model_manifests shipped additively WITHOUT a version bump, so a v8-stamped
    database read `stored == SCHEMA_VERSION`, never re-ran SCHEMA_SQL, and
    /api/sync/pull 500'd on the missing table. A v8 DB missing the table must
    now take the reconcile path and land it.
    """
    Database(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE model_manifests")  # what a real v8 install looks like
    conn.execute("DELETE FROM schema_version")  # the reader takes MAX(version); clear the v9 stamp
    conn.commit()
    conn.close()
    _stamp_version(db_path, 8)
    reset_database()

    db = Database(db_path)

    assert _stored_version(db_path) == SCHEMA_VERSION
    assert db.model_manifests.list() == []  # the table exists and reads clean


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
    `CREATE TABLE IF NOT EXISTS` -- a v10 database upgrading must gain
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
