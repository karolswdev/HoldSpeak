"""HS-160-01: Delta evidence schema -- observations, evidence links, proposals, reviews.

Tests:
- TST-001: a fresh DB has all four tables with correct columns/defaults/FKs/indexes.
- TST-002: the observation no-op law (same deterministic inputs -> one row via
  INSERT OR IGNORE, DB-002/SS5.5).
- TST-003: proposal lifecycle values are storable (open|accepted|deferred|
  dismissed|superseded|failed).
- TST-004: review shape is complete (every SS5.8 column present).
- TST-005: a legacy (pre-160) DB reconciles cleanly with zero data loss;
  repeated reconcile is idempotent.
- TST-006: real-DB proof -- copy the owner's DB, reconcile the copy, verify
  row counts/project IDs unchanged and new tables present.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

import pytest

from holdspeak.db.schema import SCHEMA_SQL, SCHEMA_VERSION
from holdspeak.db.reconcile import reconcile_schema
from holdspeak.project_contracts import generate_pobs_id


# -- Helpers ---------------------------------------------------------------

def _get_columns(conn: sqlite3.Connection, table: str) -> dict[str, dict]:
    """Return {col_name: {type, notnull, dflt_value, pk}} for *table*."""
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {
        row[1]: {
            "type": row[2],
            "notnull": row[3],
            "dflt_value": row[4],
            "pk": row[5],
        }
        for row in rows
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,),
    ).fetchone() is not None


def _fk_tables(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of referenced table names for *table*'s FKs."""
    fk_rows = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
    return {row[2] for row in fk_rows}


def _fk_on_delete(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    """Return {referenced_table: on_delete} for *table*'s FKs."""
    fk_rows = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
    return {row[2]: row[6] for row in fk_rows}


def _build_pre160_schema() -> str:
    """Return SCHEMA_SQL with HS-160-01 additions stripped out.

    This produces a schema matching the shape before this story:
    no project_observations, project_evidence_links, project_proposals,
    or project_reviews tables.
    """
    sql = SCHEMA_SQL
    # Strip the four new tables and their indexes by removing from the
    # HS-160-01 marker to the closing triple-quote (end of SCHEMA_SQL).
    marker = "\n-- HS-160-01: Append-only normalized observations"
    idx = sql.find(marker)
    if idx >= 0:
        sql = sql[:idx] + "\n"
    return sql


def _find_real_db() -> Optional[Path]:
    """Locate the owner's real HoldSpeak DB, or None if absent."""
    real_home = os.environ.get("HOLDSPEAK_REAL_HOME") or str(Path.home())
    candidate = Path(real_home) / ".local" / "share" / "holdspeak" / "holdspeak.db"
    if candidate.exists():
        return candidate
    return None


def _seed_project(conn: sqlite3.Connection, project_id: str = "proj-1",
                  name: str = "Alpha") -> None:
    """Insert a minimal project row for FK satisfaction."""
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, "
        "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
        (project_id, name),
    )
    conn.commit()


# -- TST-001: fresh DB has all new shapes ---------------------------------

# -- TST-002: observation identity no-op law ------------------------------

class TestObservationIdentityLaw:
    """Same (adapter, source_id, source_version, fact_key) -> one row.

    DB-002/SS5.5: the deterministic pobs_ ID as PK + INSERT OR IGNORE
    means an adapter retry for the same source fact/version is a silent
    no-op.
    """

    def test_same_deterministic_id_noop(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "obs-noop.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        obs_id = generate_pobs_id(
            adapter="github",
            source_id="psrc_abc",
            source_version="sha-1234",
            fact_key="pr:42:title",
        )

        # First insert succeeds.
        cur1 = conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (obs_id, "proj-1", "psrc_abc", "pr_title", "2025-08-01T00:00:00"),
        )
        assert cur1.rowcount == 1

        # Retry with same ID is a no-op.
        cur2 = conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (obs_id, "proj-1", "psrc_abc", "pr_title", "2025-08-01T00:00:00"),
        )
        assert cur2.rowcount == 0

        # Only one row exists.
        count = conn.execute(
            "SELECT COUNT(*) FROM project_observations WHERE id = ?",
            (obs_id,),
        ).fetchone()[0]
        assert count == 1

        conn.close()

    def test_different_fact_key_creates_new_row(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "obs-diff.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        id_a = generate_pobs_id(
            adapter="github", source_id="psrc_abc",
            source_version="sha-1234", fact_key="pr:42:title",
        )
        id_b = generate_pobs_id(
            adapter="github", source_id="psrc_abc",
            source_version="sha-1234", fact_key="pr:42:body",
        )
        assert id_a != id_b

        conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_a, "proj-1", "psrc_abc", "pr_title", "2025-08-01"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_b, "proj-1", "psrc_abc", "pr_body", "2025-08-01"),
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM project_observations WHERE project_id = ?",
            ("proj-1",),
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_different_source_version_creates_new_row(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "obs-ver.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        id_v1 = generate_pobs_id(
            adapter="github", source_id="psrc_abc",
            source_version="sha-1111", fact_key="pr:42:title",
        )
        id_v2 = generate_pobs_id(
            adapter="github", source_id="psrc_abc",
            source_version="sha-2222", fact_key="pr:42:title",
        )
        assert id_v1 != id_v2

        conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_v1, "proj-1", "psrc_abc", "pr_title", "2025-08-01"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO project_observations "
            "(id, project_id, source_id, observation_kind, observed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_v2, "proj-1", "psrc_abc", "pr_title", "2025-08-02"),
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM project_observations WHERE project_id = ?",
            ("proj-1",),
        ).fetchone()[0]
        assert count == 2

        conn.close()


# -- TST-003: proposal lifecycle values storable --------------------------

# -- TST-004: review shape complete ---------------------------------------

# -- TST-005: legacy fixture reconciles -----------------------------------

class TestLegacyReconcile:
    """A pre-160 DB reconciles cleanly; existing data survives."""

    def test_reconcile_adds_delta_tables(self, tmp_path: Path) -> None:
        pre160 = _build_pre160_schema()
        db_path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre160)

        # Seed a legacy project.
        conn.execute(
            "INSERT INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("proj-leg", "Legacy", "desc", "[]", "[]", "{}", 0.5, 0,
             "2025-01-01T00:00:00", "2025-06-01T00:00:00"),
        )
        conn.commit()

        # Pre-reconcile: new tables missing.
        assert not _table_exists(conn, "project_observations")
        assert not _table_exists(conn, "project_evidence_links")
        assert not _table_exists(conn, "project_proposals")
        assert not _table_exists(conn, "project_reviews")

        # Reconcile.
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # New tables present.
        assert _table_exists(conn, "project_observations")
        assert _table_exists(conn, "project_evidence_links")
        assert _table_exists(conn, "project_proposals")
        assert _table_exists(conn, "project_reviews")

        # Existing project data intact.
        row = conn.execute(
            "SELECT id, name FROM projects WHERE id = 'proj-leg'"
        ).fetchone()
        assert row is not None
        assert dict(row)["name"] == "Legacy"

        # New indexes present.
        assert _index_exists(conn, "idx_project_observations_source")
        assert _index_exists(conn, "idx_project_evidence_links_target")
        assert _index_exists(conn, "idx_project_proposals_window")
        assert _index_exists(conn, "idx_project_reviews_status")

        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        pre160 = _build_pre160_schema()
        db_path = tmp_path / "idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(pre160)
        conn.execute(
            "INSERT INTO projects (id, name, created_at, updated_at) "
            "VALUES ('x', 'X', '2025-01-01', '2025-01-01')"
        )
        conn.commit()

        first = reconcile_schema(conn, db_path=db_path)
        assert first is True

        second = reconcile_schema(conn, db_path=db_path)
        assert second is False  # no changes on second run

        conn.close()

    def test_archived_rows_survive_reconcile(self, tmp_path: Path) -> None:
        pre160 = _build_pre160_schema()
        db_path = tmp_path / "archive.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre160)
        conn.execute(
            "INSERT INTO projects (id, name, is_archived, created_at, updated_at) "
            "VALUES ('arc-1', 'Archived', 1, '2024-01-01', '2024-01-01')"
        )
        conn.commit()

        reconcile_schema(conn, db_path=db_path)

        row = conn.execute(
            "SELECT id, name, is_archived FROM projects WHERE id = 'arc-1'"
        ).fetchone()
        assert row is not None
        assert dict(row)["is_archived"] == 1
        assert dict(row)["name"] == "Archived"

        conn.close()


# -- TST-006: real-DB proof -----------------------------------------------

@pytest.mark.skipif(
    _find_real_db() is None,
    reason="Owner's real DB not found (CI or isolated HOME)",
)
class TestRealDbReconcile:
    """Copy the owner's real DB, reconcile the copy, verify zero data loss.

    Proves DB-001: existing project IDs and row counts survive the additive
    schema migration.  The copy is never the live file.
    """

    def test_real_db_reconcile_preserves_data(self, tmp_path: Path) -> None:
        real_db = _find_real_db()
        assert real_db is not None  # guard; skipif already checked

        copy_path = tmp_path / "real_copy.db"
        # HS-200-45 R5: the database runs in WAL now, so its committed tail can
        # live in the ``-wal`` sidecar. A bare file copy would hand this test a
        # database missing its most recent rows (or, on a fresh file, an empty
        # one) and the "preserves data" assertions would pass vacuously. The
        # sqlite backup API reads one consistent snapshot through SQLite.
        _src = sqlite3.connect(f"file:{real_db}?mode=ro", uri=True)
        try:
            _dest = sqlite3.connect(str(copy_path))
            try:
                _src.backup(_dest)
            finally:
                _dest.close()
        finally:
            _src.close()

        conn = sqlite3.connect(str(copy_path))
        conn.row_factory = sqlite3.Row

        # Snapshot BEFORE reconcile.
        before_project_count = conn.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]
        before_project_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM projects").fetchall()
        )

        # Reconcile the copy.
        reconcile_schema(conn, db_path=copy_path)

        # Snapshot AFTER reconcile.
        after_project_count = conn.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]
        after_project_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM projects").fetchall()
        )

        # Row counts unchanged.
        assert after_project_count == before_project_count, (
            f"project row count changed: {before_project_count} -> {after_project_count}"
        )
        # Project IDs unchanged.
        assert after_project_ids == before_project_ids, (
            "project IDs changed after reconcile"
        )

        # New tables exist.
        assert _table_exists(conn, "project_observations")
        assert _table_exists(conn, "project_evidence_links")
        assert _table_exists(conn, "project_proposals")
        assert _table_exists(conn, "project_reviews")

        # New indexes exist.
        assert _index_exists(conn, "idx_project_observations_source")
        assert _index_exists(conn, "idx_project_evidence_links_target")
        assert _index_exists(conn, "idx_project_proposals_window")
        assert _index_exists(conn, "idx_project_reviews_status")

        # Second reconcile is a no-op.
        changed = reconcile_schema(conn, db_path=copy_path)
        assert changed is False, "second reconcile should be a no-op"

        conn.close()
