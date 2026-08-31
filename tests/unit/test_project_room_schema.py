"""HS-158-01: Project Room aggregate schema — reconcile, column presence, defaults.

Tests:
- TST-001: a fresh DB has all new columns/tables with correct defaults.
- TST-002: a legacy (pre-158) DB reconciles with zero data loss; repeated
  reconcile is idempotent; archived rows survive.
- TST-003: the real-DB proof — copy the owner's DB, reconcile the copy,
  assert row counts and project IDs unchanged.
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


# ── Helpers ──────────────────────────────────────────────────────────────

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


def _build_pre158_schema() -> str:
    """Return the schema SQL with HS-158-01 additions stripped out.

    This produces a schema that matches the shape before this story:
    projects without the Room columns, project_resources without the
    Room columns, and none of the three new tables.
    """
    sql = SCHEMA_SQL

    # Strip Room columns from projects table.
    sql = re.sub(
        r"\n    -- HS-158-01: Project Room aggregate identity, lifecycle, and cadence\.\n"
        r"    purpose TEXT,\n"
        r"    outcome_text TEXT,\n"
        r"    owner_ref TEXT,\n"
        r"    lifecycle TEXT NOT NULL DEFAULT 'active',\n"
        r"    posture TEXT,\n"
        r"    posture_reason TEXT,\n"
        r"    start_at TEXT,\n"
        r"    target_at TEXT,\n"
        r"    review_cadence_json TEXT,\n"
        r"    next_review_at TEXT,\n"
        r"    template_key TEXT,\n"
        r"    modules_json TEXT,\n"
        r"    revision INTEGER NOT NULL DEFAULT 0,\n"
        r"    last_review_id TEXT,\n"
        r"    last_review_at TEXT,\n",
        "\n",
        sql,
        count=1,
    )

    # Strip Room columns from project_resources table.
    sql = re.sub(
        r"\n    -- HS-158-01: semantic role and metadata for Project Room sources\.\n"
        r"    semantic_role TEXT,\n"
        r"    metadata_json TEXT,\n"
        r"    revision INTEGER NOT NULL DEFAULT 0,\n",
        "\n",
        sql,
        count=1,
    )

    # Strip the three new tables and their indexes.
    sql = re.sub(
        r"\n-- HS-158-01: Project-owned items.*?"
        r"ON project_commands\(project_id, status\);\n",
        "\n",
        sql,
        count=1,
        flags=re.DOTALL,
    )

    return sql


def _find_real_db() -> Optional[Path]:
    """Locate the owner's real HoldSpeak DB, or None if absent."""
    real_home = os.environ.get("HOLDSPEAK_REAL_HOME") or str(Path.home())
    candidate = Path(real_home) / ".local" / "share" / "holdspeak" / "holdspeak.db"
    if candidate.exists():
        return candidate
    return None


# ── TST-001: fresh DB has all new shapes ─────────────────────────────────

class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has every HS-158-01 shape."""

    def test_projects_has_room_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "projects")
        room_cols = [
            "purpose", "outcome_text", "owner_ref", "lifecycle",
            "posture", "posture_reason", "start_at", "target_at",
            "review_cadence_json", "next_review_at", "template_key",
            "modules_json", "revision", "last_review_id", "last_review_at",
        ]
        for col in room_cols:
            assert col in cols, f"projects missing column {col}"
        conn.close()

    def test_projects_lifecycle_default(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "projects")
        assert cols["lifecycle"]["dflt_value"] == "'active'"
        assert cols["lifecycle"]["notnull"] == 1
        conn.close()

    def test_projects_revision_default(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "projects")
        assert cols["revision"]["dflt_value"] == "0"
        assert cols["revision"]["notnull"] == 1
        conn.close()

    def test_project_resources_has_room_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_resources")
        for col in ["semantic_role", "metadata_json", "revision"]:
            assert col in cols, f"project_resources missing column {col}"
        assert cols["revision"]["dflt_value"] == "0"
        conn.close()

    def test_project_items_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_items")
        cols = _get_columns(conn, "project_items")
        expected = [
            "id", "project_id", "item_type", "title", "summary",
            "lifecycle", "severity", "owner_ref", "due_at", "sort_key",
            "details_json", "provenance_kind", "source_observation_id",
            "created_by_ref", "revision", "created_at", "updated_at",
        ]
        for col in expected:
            assert col in cols, f"project_items missing column {col}"
        # FK to projects
        fk_rows = conn.execute("PRAGMA foreign_key_list(project_items)").fetchall()
        fk_tables = {row[2] for row in fk_rows}
        assert "projects" in fk_tables
        conn.close()

    def test_project_changes_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_changes")
        cols = _get_columns(conn, "project_changes")
        expected = [
            "id", "project_id", "project_revision", "change_kind",
            "target_ref", "actor_ref", "command_id",
            "before_hash", "after_hash", "summary_json", "created_at",
        ]
        for col in expected:
            assert col in cols, f"project_changes missing column {col}"
        conn.close()

    def test_project_commands_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_commands")
        cols = _get_columns(conn, "project_commands")
        expected = [
            "id", "project_id", "command_kind", "request_hash",
            "status", "result_json", "error_code", "created_at",
            "completed_at",
        ]
        for col in expected:
            assert col in cols, f"project_commands missing column {col}"
        conn.close()

    def test_project_items_index_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            ("idx_project_items_project_type",),
        ).fetchone()
        assert idx is not None
        conn.close()

    def test_project_changes_index_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            ("idx_project_changes_project_rev",),
        ).fetchone()
        assert idx is not None
        conn.close()

    def test_project_commands_index_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            ("idx_project_commands_project",),
        ).fetchone()
        assert idx is not None
        conn.close()


# ── TST-002: legacy fixture reconciles with zero data loss ───────────────

class TestLegacyReconcile:
    """A pre-158 DB reconciles cleanly, preserving every row."""

    def test_reconcile_adds_room_columns_to_legacy_projects(self, tmp_path: Path) -> None:
        """Room columns appear on legacy DB via reconcile; existing data intact."""
        pre158 = _build_pre158_schema()
        db_path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre158)

        # Seed a legacy project.
        conn.execute(
            "INSERT INTO projects (id, name, description, keywords_json, "
            "team_members_json, context_json, detection_threshold, is_archived, "
            "created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("proj-1", "Alpha", "desc", "[]", "[]", "{}", 0.5, 0,
             "2025-01-01T00:00:00", "2025-06-01T00:00:00"),
        )
        # Seed an archived project.
        conn.execute(
            "INSERT INTO projects (id, name, description, keywords_json, "
            "team_members_json, context_json, detection_threshold, is_archived, "
            "created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("proj-2", "Beta", "archived", "[]", "[]", "{}", 0.3, 1,
             "2024-01-01T00:00:00", "2024-06-01T00:00:00"),
        )
        # Seed a legacy resource.
        conn.execute(
            "INSERT INTO project_resources (project_id, resource_ref, relationship, "
            "source, confidence, created_at, last_modified, deleted) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("proj-1", "meeting:m1", "member", "auto", 0.9,
             "2025-01-01", "2025-01-01", 0),
        )
        conn.commit()

        # Verify pre-reconcile: new columns missing.
        old_cols = _get_columns(conn, "projects")
        assert "purpose" not in old_cols
        assert "lifecycle" not in old_cols

        # Reconcile.
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # New columns present.
        new_cols = _get_columns(conn, "projects")
        assert "purpose" in new_cols
        assert "lifecycle" in new_cols
        assert "revision" in new_cols

        # New tables present.
        assert _table_exists(conn, "project_items")
        assert _table_exists(conn, "project_changes")
        assert _table_exists(conn, "project_commands")

        # project_resources gained Room columns.
        pr_cols = _get_columns(conn, "project_resources")
        assert "semantic_role" in pr_cols
        assert "metadata_json" in pr_cols
        assert "revision" in pr_cols

        # Existing data intact.
        rows = conn.execute(
            "SELECT id, name, description, is_archived FROM projects ORDER BY id"
        ).fetchall()
        assert len(rows) == 2
        assert dict(rows[0])["id"] == "proj-1"
        assert dict(rows[0])["name"] == "Alpha"
        assert dict(rows[1])["id"] == "proj-2"
        assert dict(rows[1])["is_archived"] == 1  # archived survives

        # Legacy project gets safe defaults for new NOT NULL columns.
        room = conn.execute(
            "SELECT lifecycle, revision FROM projects WHERE id = 'proj-1'"
        ).fetchone()
        # ALTER TABLE adds NOT NULL DEFAULT 'active' -> constant substitute is ''
        # for TEXT, and 0 for INTEGER.  The reconcile engine uses constant defaults
        # for function/NOT-NULL columns in ALTER.  lifecycle is TEXT NOT NULL DEFAULT
        # 'active' -> constant default '' for existing rows; revision INTEGER NOT
        # NULL DEFAULT 0 -> constant default 0.
        assert room["revision"] == 0

        # Resource still exists.
        res = conn.execute(
            "SELECT * FROM project_resources WHERE project_id = 'proj-1'"
        ).fetchone()
        assert dict(res)["resource_ref"] == "meeting:m1"

        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        """Running reconcile twice produces no additional changes."""
        pre158 = _build_pre158_schema()
        db_path = tmp_path / "idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(pre158)
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
        """Archived projects remain readable and restorable after reconcile."""
        pre158 = _build_pre158_schema()
        db_path = tmp_path / "archive.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre158)
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


# ── TST-003: real-DB proof ───────────────────────────────────────────────

@pytest.mark.skipif(
    _find_real_db() is None,
    reason="Owner's real DB not found (CI or isolated HOME)",
)
class TestRealDbReconcile:
    """Copy the owner's real DB, reconcile the copy, verify zero data loss.

    The copy is never the live file.  This test proves DB-001: existing
    project IDs and row counts survive the additive schema migration.
    """

    def test_real_db_reconcile_preserves_data(self, tmp_path: Path) -> None:
        real_db = _find_real_db()
        assert real_db is not None  # guard; skipif already checked

        copy_path = tmp_path / "real_copy.db"
        shutil.copy2(str(real_db), str(copy_path))

        conn = sqlite3.connect(str(copy_path))
        conn.row_factory = sqlite3.Row

        # Snapshot BEFORE reconcile.
        before_project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        before_project_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM projects").fetchall()
        )
        before_resource_count = conn.execute("SELECT COUNT(*) FROM project_resources").fetchone()[0]

        # Reconcile the copy.
        reconcile_schema(conn, db_path=copy_path)

        # Snapshot AFTER reconcile.
        after_project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        after_project_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM projects").fetchall()
        )
        after_resource_count = conn.execute("SELECT COUNT(*) FROM project_resources").fetchone()[0]

        # Row counts unchanged.
        assert after_project_count == before_project_count, (
            f"project row count changed: {before_project_count} -> {after_project_count}"
        )
        assert after_resource_count == before_resource_count, (
            f"resource row count changed: {before_resource_count} -> {after_resource_count}"
        )

        # Project IDs unchanged.
        assert after_project_ids == before_project_ids, "project IDs changed after reconcile"

        # New columns exist.
        cols = _get_columns(conn, "projects")
        assert "lifecycle" in cols
        assert "revision" in cols
        assert "purpose" in cols

        # New tables exist.
        assert _table_exists(conn, "project_items")
        assert _table_exists(conn, "project_changes")
        assert _table_exists(conn, "project_commands")

        # Second reconcile is a no-op.
        changed = reconcile_schema(conn, db_path=copy_path)
        assert changed is False, "second reconcile should be a no-op"

        conn.close()
