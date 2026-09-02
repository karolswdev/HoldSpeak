"""HS-162-01: Project updates schema and repo layer.

Tests:
- TST-001: a fresh DB has project_updates with correct columns/defaults/FKs/indexes.
- TST-002: lifecycle law truth table: publish sets published_at; any write to
  a published row refuses with PublishedUpdateError; supersede replaces an
  unaccepted draft (UPD-004).
- TST-003: revision pinning -- a draft records the project_revision +
  source_manifest_json at creation; the pin survives later project mutation.
- TST-004: legacy (pre-162) DB reconciles cleanly; repeated reconcile is idempotent.
- TST-005: real-DB proof -- copy the owner's DB, reconcile the copy, verify
  row counts/project IDs unchanged and new table present.
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
from holdspeak.db.updates import PublishedUpdateError, UpdatesRepository
from holdspeak.project_contracts import generate_pupd_id


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


def _build_pre162_schema() -> str:
    """Return SCHEMA_SQL with HS-162-01 additions stripped out.

    This produces a schema matching the shape before this story:
    no project_updates table.
    """
    sql = SCHEMA_SQL
    marker = "\n-- HS-162-01: Project updates"
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
                  name: str = "Alpha", revision: int = 5) -> None:
    """Insert a minimal project row for FK satisfaction."""
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, ?, "
        "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
        (project_id, name, revision),
    )
    conn.commit()


def _make_repo(tmp_path: Path):
    """Build a fresh DB + UpdatesRepository wired to it."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    _seed_project(conn)

    # Wire the repo with a minimal connection factory
    class _ConnCtx:
        def __enter__(self_):
            return conn
        def __exit__(self_, *a):
            conn.commit()

    repo = UpdatesRepository(lambda: _ConnCtx())
    return conn, repo


# -- TST-001: fresh DB has the right shape ---------------------------------

class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has the HS-162-01 shape."""

    def test_schema_version_is_72(self) -> None:
        assert SCHEMA_VERSION == 72

    def test_updates_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_updates")
        conn.close()

    def test_updates_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_updates")
        expected = [
            "id", "project_id", "project_revision", "review_id",
            "lifecycle", "draft_revision", "body_md", "claims_json",
            "source_manifest_json", "generator",
            "created_at", "updated_at", "published_at",
        ]
        for col in expected:
            assert col in cols, f"project_updates missing column {col}"
        conn.close()

    def test_updates_defaults(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_updates")
        assert cols["lifecycle"]["dflt_value"] == "'draft'"
        assert cols["draft_revision"]["dflt_value"] == "1"
        assert cols["body_md"]["dflt_value"] == "''"
        assert cols["claims_json"]["dflt_value"] == "'{}'"
        assert cols["source_manifest_json"]["dflt_value"] == "'{}'"
        assert cols["generator"]["dflt_value"] == "'deterministic'"
        conn.close()

    def test_updates_fk_to_projects(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "project_updates")
        assert _fk_on_delete(conn, "project_updates")["projects"] == "CASCADE"
        conn.close()

    def test_updates_indexes(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "idx_project_updates_project")
        assert _index_exists(conn, "idx_project_updates_review")
        conn.close()

    def test_published_at_nullable(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_updates")
        assert cols["published_at"]["notnull"] == 0
        conn.close()

    def test_review_id_nullable(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_updates")
        assert cols["review_id"]["notnull"] == 0
        conn.close()


# -- TST-002: lifecycle law truth table ------------------------------------

class TestLifecycleLaw:
    """Publish, refuse-on-published, supersede -- the UPD-004 truth table."""

    def test_insert_creates_draft(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
            body_md="# First draft",
        )
        row = repo.get_update(uid)
        assert row is not None
        assert row["lifecycle"] == "draft"
        assert row["published_at"] is None
        conn.close()

    def test_publish_sets_published_lifecycle_and_timestamp(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
        )
        repo.publish_update(uid)
        row = repo.get_update(uid)
        assert row["lifecycle"] == "published"
        assert row["published_at"] is not None
        conn.close()

    def test_update_draft_on_published_refuses(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
        )
        repo.publish_update(uid)
        with pytest.raises(PublishedUpdateError):
            repo.update_draft(uid, body_md="changed")
        conn.close()

    def test_republish_refuses(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
        )
        repo.publish_update(uid)
        with pytest.raises(PublishedUpdateError):
            repo.publish_update(uid)
        conn.close()

    def test_supersede_published_refuses(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
        )
        repo.publish_update(uid)
        with pytest.raises(PublishedUpdateError):
            repo.supersede_draft(
                uid,
                new_update_id=generate_pupd_id(),
                body_md="attempt",
            )
        conn.close()

    def test_supersede_unaccepted_draft(self, tmp_path: Path) -> None:
        """UPD-004: superseding marks old draft superseded, creates draft_revision+1."""
        conn, repo = _make_repo(tmp_path)
        uid1 = generate_pupd_id()
        repo.insert_update(
            update_id=uid1,
            project_id="proj-1",
            project_revision=5,
            draft_revision=1,
            body_md="draft v1",
        )

        uid2 = generate_pupd_id()
        new_draft = repo.supersede_draft(
            uid1,
            new_update_id=uid2,
            body_md="draft v2",
        )

        # Old draft is superseded
        old = repo.get_update(uid1)
        assert old["lifecycle"] == "superseded"

        # New draft has draft_revision+1
        assert new_draft["lifecycle"] == "draft"
        assert new_draft["draft_revision"] == 2
        assert new_draft["body_md"] == "draft v2"
        # Inherits the project_revision pin
        assert new_draft["project_revision"] == 5
        conn.close()

    def test_update_draft_on_superseded_refuses(self, tmp_path: Path) -> None:
        """S-1: a superseded row is immutable -- update_draft refuses."""
        conn, repo = _make_repo(tmp_path)
        uid1 = generate_pupd_id()
        repo.insert_update(
            update_id=uid1,
            project_id="proj-1",
            project_revision=5,
            body_md="original",
        )
        uid2 = generate_pupd_id()
        repo.supersede_draft(uid1, new_update_id=uid2, body_md="v2")
        with pytest.raises(PublishedUpdateError, match="superseded"):
            repo.update_draft(uid1, body_md="should fail")
        conn.close()

    def test_publish_on_superseded_refuses(self, tmp_path: Path) -> None:
        """S-1: a superseded row cannot be published."""
        conn, repo = _make_repo(tmp_path)
        uid1 = generate_pupd_id()
        repo.insert_update(
            update_id=uid1,
            project_id="proj-1",
            project_revision=5,
        )
        uid2 = generate_pupd_id()
        repo.supersede_draft(uid1, new_update_id=uid2, body_md="v2")
        with pytest.raises(PublishedUpdateError, match="superseded"):
            repo.publish_update(uid1)
        conn.close()

    def test_supersede_preserves_project_pin(self, tmp_path: Path) -> None:
        """The new draft from supersede inherits the original project_revision."""
        conn, repo = _make_repo(tmp_path)
        uid1 = generate_pupd_id()
        repo.insert_update(
            update_id=uid1,
            project_id="proj-1",
            project_revision=5,
            source_manifest_json='{"obs":["o1","o2"]}',
        )
        uid2 = generate_pupd_id()
        new_draft = repo.supersede_draft(
            uid1,
            new_update_id=uid2,
            body_md="v2",
            source_manifest_json='{"obs":["o1","o2","o3"]}',
        )
        assert new_draft["project_revision"] == 5
        conn.close()

    def test_list_by_lifecycle(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid_draft = generate_pupd_id()
        uid_pub = generate_pupd_id()
        repo.insert_update(
            update_id=uid_draft,
            project_id="proj-1",
            project_revision=5,
        )
        repo.insert_update(
            update_id=uid_pub,
            project_id="proj-1",
            project_revision=5,
        )
        repo.publish_update(uid_pub)
        drafts = repo.list_updates("proj-1", lifecycle="draft")
        published = repo.list_updates("proj-1", lifecycle="published")
        assert len(drafts) == 1
        assert drafts[0]["id"] == uid_draft
        assert len(published) == 1
        assert published[0]["id"] == uid_pub
        conn.close()

    def test_update_draft_succeeds_on_draft(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
            body_md="original",
        )
        repo.update_draft(uid, body_md="edited")
        row = repo.get_update(uid)
        assert row["body_md"] == "edited"
        conn.close()

    def test_in_transaction_variants_work(self, tmp_path: Path) -> None:
        """conn-accepting variants are functional."""
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        # Use the _in_transaction variant directly
        with repo._connection() as c:
            repo.insert_update_in_transaction(
                c,
                update_id=uid,
                project_id="proj-1",
                project_revision=5,
            )
        row = repo.get_update(uid)
        assert row is not None
        assert row["lifecycle"] == "draft"

        # Publish in transaction
        with repo._connection() as c:
            repo.publish_update_in_transaction(c, uid)
        row = repo.get_update(uid)
        assert row["lifecycle"] == "published"
        conn.close()


# -- TST-003: revision pinning --------------------------------------------

class TestRevisionPinning:
    """A draft records project_revision + source_manifest at creation;
    the pin survives later project mutation."""

    def test_pin_survives_project_mutation(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        manifest = '{"observations":["obs-1"],"caveats":[]}'
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
            source_manifest_json=manifest,
        )

        # Mutate the project (bump revision to 6)
        conn.execute(
            "UPDATE projects SET revision = 6, updated_at = '2025-07-01T00:00:00' "
            "WHERE id = 'proj-1'"
        )
        conn.commit()

        # The draft's pin is unchanged
        row = repo.get_update(uid)
        assert row["project_revision"] == 5
        assert row["source_manifest_json"] == manifest

        # Confirm the project itself moved
        proj = conn.execute(
            "SELECT revision FROM projects WHERE id = 'proj-1'"
        ).fetchone()
        assert proj[0] == 6
        conn.close()

    def test_pin_records_at_creation_time(self, tmp_path: Path) -> None:
        """The pin is stamped at INSERT, not deferred."""
        conn, repo = _make_repo(tmp_path)
        uid = generate_pupd_id()
        repo.insert_update(
            update_id=uid,
            project_id="proj-1",
            project_revision=5,
            source_manifest_json='{"src":["s1"]}',
        )
        row = repo.get_update(uid)
        assert row["project_revision"] == 5
        assert row["source_manifest_json"] == '{"src":["s1"]}'
        conn.close()

    def test_multiple_drafts_pin_different_revisions(self, tmp_path: Path) -> None:
        conn, repo = _make_repo(tmp_path)
        uid1 = generate_pupd_id()
        repo.insert_update(
            update_id=uid1,
            project_id="proj-1",
            project_revision=5,
        )
        # Bump project
        conn.execute(
            "UPDATE projects SET revision = 6 WHERE id = 'proj-1'"
        )
        conn.commit()
        uid2 = generate_pupd_id()
        repo.insert_update(
            update_id=uid2,
            project_id="proj-1",
            project_revision=6,
        )
        r1 = repo.get_update(uid1)
        r2 = repo.get_update(uid2)
        assert r1["project_revision"] == 5
        assert r2["project_revision"] == 6
        conn.close()


# -- TST-004: legacy reconcile --------------------------------------------

class TestLegacyReconcile:
    """A pre-162 DB reconciles to v70 shape without data loss."""

    def test_reconcile_adds_project_updates_table(self, tmp_path: Path) -> None:
        pre162 = _build_pre162_schema()
        db_path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre162)
        _seed_project(conn)

        assert not _table_exists(conn, "project_updates")
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True
        assert _table_exists(conn, "project_updates")
        assert _index_exists(conn, "idx_project_updates_project")
        assert _index_exists(conn, "idx_project_updates_review")
        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        pre162 = _build_pre162_schema()
        db_path = tmp_path / "idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(pre162)
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

    def test_existing_data_survives_reconcile(self, tmp_path: Path) -> None:
        pre162 = _build_pre162_schema()
        db_path = tmp_path / "data.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre162)
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


# -- TST-005: real-DB proof -----------------------------------------------

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
        assert real_db is not None

        copy_path = tmp_path / "real_copy.db"
        shutil.copy2(str(real_db), str(copy_path))

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

        # New table exists.
        assert _table_exists(conn, "project_updates")

        # New indexes exist.
        assert _index_exists(conn, "idx_project_updates_project")
        assert _index_exists(conn, "idx_project_updates_review")

        # Second reconcile is a no-op.
        changed = reconcile_schema(conn, db_path=copy_path)
        assert changed is False, "second reconcile should be a no-op"

        conn.close()


# -- ID prefix validation -------------------------------------------------

class TestIdPrefix:
    """The pupd_ prefix generator and validator work correctly."""

    def test_generate_pupd_id_has_prefix(self) -> None:
        uid = generate_pupd_id()
        assert uid.startswith("pupd_")
        assert len(uid) == len("pupd_") + 32  # prefix + 32 hex chars

    def test_two_ids_are_unique(self) -> None:
        uid1 = generate_pupd_id()
        uid2 = generate_pupd_id()
        assert uid1 != uid2

    def test_validate_pupd_id(self) -> None:
        from holdspeak.project_contracts import validate_pupd_id
        uid = generate_pupd_id()
        assert validate_pupd_id(uid) is True
        assert validate_pupd_id("pitem_" + "a" * 32) is False
        assert validate_pupd_id("invalid") is False
