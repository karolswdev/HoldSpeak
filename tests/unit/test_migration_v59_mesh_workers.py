"""HS-135-01: the hub opens its own desk -- v59 mesh_workers migration fix.

Regression test for the migration failure where a schema-59 database with the
old mesh_workers shape (only ``node`` and ``last_seen``, lacking ``node_id``
and ``credential_generation``) fails on 59->60 with:

    sqlite3.OperationalError: no such column: node_id

Root cause: SCHEMA_SQL carries ``CREATE INDEX IF NOT EXISTS
idx_mesh_workers_identity ON mesh_workers(node_id, credential_generation)``
but ``run_migrations`` calls ``conn.executescript(SCHEMA_SQL)`` BEFORE
``_migrate_columns`` (which adds the columns). A database that reached v59
without those columns -- the owner's real DB -- fails on the index creation.

Fix: ``_migrate_renames`` (pre-schema) now ensures the columns exist before
SCHEMA_SQL runs, unconditionally and idempotently.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from holdspeak.db import Database, SCHEMA_VERSION, reset_database


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    reset_database()
    yield tmp_path / "holdspeak.db"
    reset_database()


def _build_v59_db_with_old_mesh_shape(path: Path) -> None:
    """Construct a schema-59 DB with the OLD mesh_workers shape.

    The old shape (pre-v59, from git show 3b24fa48^:holdspeak/db/schema.py):

        CREATE TABLE mesh_workers (
            node TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL DEFAULT (datetime('now'))
        );

    This is what the owner's real backup looks like: stamped as v59 but
    mesh_workers lacks node_id and credential_generation.
    """
    # Create a fresh DB first, then downgrade the mesh_workers table.
    db = Database(path)
    del db
    reset_database()

    conn = sqlite3.connect(str(path))

    # Drop the correctly-shaped mesh_workers and its index, replace with old shape.
    conn.execute("DROP INDEX IF EXISTS idx_mesh_workers_identity")
    conn.execute("DROP TABLE mesh_workers")
    conn.execute(
        "CREATE TABLE mesh_workers ("
        "    node TEXT PRIMARY KEY,"
        "    last_seen TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )

    # Insert a liveness row so we can verify data survives migration.
    conn.execute(
        "INSERT INTO mesh_workers (node, last_seen) VALUES ('test-node', '2026-08-16 12:00:00')"
    )

    # Stamp as v59 (the version the owner's DB was at).
    conn.execute("DELETE FROM schema_version")
    conn.execute("INSERT INTO schema_version (version) VALUES (59)")
    conn.commit()
    conn.close()


def test_v59_db_with_old_mesh_shape_migrates_to_current(db_path: Path) -> None:
    """A v59 DB lacking mesh_workers.node_id must migrate cleanly to v60.

    This is the exact scenario from the owner's backup:
    schema_version=59, mesh_workers=(node, last_seen) only.
    """
    _build_v59_db_with_old_mesh_shape(db_path)

    # Verify the pre-migration shape: no node_id.
    conn = sqlite3.connect(str(db_path))
    cols_before = {r[1] for r in conn.execute("PRAGMA table_info(mesh_workers)").fetchall()}
    version_before = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    conn.close()

    assert "node_id" not in cols_before, "Pre-condition: mesh_workers must lack node_id"
    assert version_before == 59, "Pre-condition: schema version must be 59"

    # The migration must succeed (this was the OperationalError before the fix).
    db = Database(db_path)
    del db
    reset_database()

    # Post-migration: version is current, mesh_workers has the new columns,
    # the index exists, and the liveness row survived.
    conn = sqlite3.connect(str(db_path))
    version_after = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    cols_after = {r[1] for r in conn.execute("PRAGMA table_info(mesh_workers)").fetchall()}

    # Index exists.
    idx = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='index' AND name='idx_mesh_workers_identity'"
    ).fetchone()

    # Data survived.
    row = conn.execute(
        "SELECT node, last_seen FROM mesh_workers WHERE node='test-node'"
    ).fetchone()
    conn.close()

    assert version_after == SCHEMA_VERSION
    assert "node_id" in cols_after
    assert "credential_generation" in cols_after
    assert idx is not None, "idx_mesh_workers_identity must exist after migration"
    assert row is not None, "Liveness row must survive migration"
    assert row[0] == "test-node"
    assert row[1] == "2026-08-16 12:00:00"


def test_fresh_db_unaffected_by_mesh_guard(db_path: Path) -> None:
    """A fresh DB (no prior mesh_workers) must create normally.

    The unconditional guard in _migrate_renames must be a no-op when the
    table does not yet exist or already has the columns.
    """
    db = Database(db_path)
    del db
    reset_database()

    conn = sqlite3.connect(str(db_path))
    version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    cols = {r[1] for r in conn.execute("PRAGMA table_info(mesh_workers)").fetchall()}
    idx = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='index' AND name='idx_mesh_workers_identity'"
    ).fetchone()
    conn.close()

    assert version == SCHEMA_VERSION
    assert "node_id" in cols
    assert "credential_generation" in cols
    assert idx is not None


def test_hub_boots_on_migrated_db(db_path: Path) -> None:
    """After migration, the Database object must construct without error.

    This is the cheapest honest boot check: if the Database constructor
    completes (which opens connections, applies schema, binds repositories),
    the hub can open its own desk.
    """
    _build_v59_db_with_old_mesh_shape(db_path)

    # The boot must not raise.
    db = Database(db_path)

    # Verify the database is usable: write and read back a profile.
    db.profiles.upsert(
        profile_id="boot-test",
        name="Boot Test",
        kind="openAICompatible",
        base_url="http://localhost:8080/v1",
        model="test-model",
    )
    profile = db.profiles.get("boot-test")
    assert profile is not None
    assert profile.name == "Boot Test"

    del db
    reset_database()
