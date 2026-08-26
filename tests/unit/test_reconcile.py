"""Tests for the declarative schema reconcile engine (HS-137-01).

Each test maps to a phase-137 invariant:

- A1 -- additive only (orphan tables/rows survive).
- A2 -- idempotent (running twice is a no-op, no ALTERs fired).
- A3 -- self-heals shape (missing tables and columns restored).
- A4 -- ALTER-safe defaults (function defaults get constant substitutes).
- A5 -- no version gate (a "newer" DB opens without error).

Plus hazard tests:
- Soft-deleted decisions survive reconcile (blocker regression).
- Clean DB reconcile skips data backfills (no perf regression).
- FTS shadow tables are not column-diffed/ALTERed.
- Shape-change open triggers backup + backfills.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from holdspeak.db.schema import SCHEMA_SQL, SCHEMA_VERSION
from holdspeak.db.reconcile import (
    reconcile_schema,
    _build_reference_schema,
    _is_function_default,
    _add_missing_columns,
)


@pytest.fixture()
def fresh_conn(tmp_path: Path):
    """A fresh SQLite connection with the full canonical schema applied."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    yield conn
    conn.close()


# ── A3: self-heals missing table ───────────────────────────────────────


def test_reconcile_recreates_dropped_table(fresh_conn: sqlite3.Connection) -> None:
    """A3 (table): dropping a table and reconciling brings it back."""
    fresh_conn.execute("DROP TABLE IF EXISTS bookmarks")
    row = fresh_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
    ).fetchone()
    assert row is None, "bookmarks should be gone before reconcile"

    reconcile_schema(fresh_conn)

    row = fresh_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
    ).fetchone()
    assert row is not None, "bookmarks should be restored after reconcile"


def test_reconcile_adds_provider_command_table_to_old_shape_without_touching_rows(tmp_path: Path) -> None:
    """S3's additive command ledger opens an old DB without data rewrites."""
    old_schema, substitutions = re.subn(
        r"\n-- HS-143-12: provider commands reserve.*?updated_at TEXT NOT NULL\n\);\n",
        "\n",
        SCHEMA_SQL,
        count=1,
        flags=re.DOTALL,
    )
    assert substitutions == 1
    conn = sqlite3.connect(str(tmp_path / "old-provider-shape.db"))
    try:
        conn.executescript(old_schema)
        conn.execute("INSERT INTO schema_version(version) VALUES (63)")
        conn.execute("INSERT INTO profiles(id,name,kind,created_at,last_modified) VALUES ('kept', 'Kept', 'onDevice', 'old', 'old')")
        conn.commit()
        assert reconcile_schema(conn) is True
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='model_library_provider_commands'"
        ).fetchone() is not None
        assert tuple(conn.execute("SELECT id,name,kind,created_at,last_modified FROM profiles WHERE id='kept'").fetchone()) == (
            "kept", "Kept", "onDevice", "old", "old",
        )
    finally:
        conn.close()


# ── A3/A4: self-heals missing column (including datetime default) ──────


def _rebuild_table_without_column(conn, table, drop_col):
    """Helper: rebuild a table without a specific column (SQLite workaround)."""
    ref_schema = _build_reference_schema()
    ref_cols = ref_schema[table]

    original_cols = [
        row[1]
        for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    ]
    assert drop_col in original_cols, f"Precondition: {drop_col} exists in {table}"

    conn.execute(f'ALTER TABLE "{table}" RENAME TO "_{table}_old"')
    keep_cols = [c for c in original_cols if c != drop_col]
    col_list = ", ".join(f'"{c}"' for c in keep_cols)

    col_defs = []
    for col in ref_cols:
        if col["name"] == drop_col:
            continue
        parts = [f'"{col["name"]}"']
        if col["type"]:
            parts.append(col["type"])
        if col["pk"]:
            parts.append("PRIMARY KEY")
        if col["dflt_value"] is not None:
            if _is_function_default(col["dflt_value"]):
                parts.append("DEFAULT ''")
            else:
                parts.append(f"DEFAULT {col['dflt_value']}")
        if col["notnull"] and not col["pk"]:
            parts.append("NOT NULL")
        col_defs.append(" ".join(parts))

    create_sql = f'CREATE TABLE "{table}" ({", ".join(col_defs)})'
    conn.execute(create_sql)
    conn.execute(
        f'INSERT INTO "{table}" ({col_list}) SELECT {col_list} FROM "_{table}_old"'
    )
    conn.execute(f'DROP TABLE "_{table}_old"')

    live_cols = {
        row[1]
        for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    }
    assert drop_col not in live_cols, f"Postcondition: {drop_col} is gone"


def test_reconcile_adds_missing_column(fresh_conn: sqlite3.Connection) -> None:
    """A3 (column): a missing column is restored by reconcile."""
    _rebuild_table_without_column(fresh_conn, "meetings", "title")

    reconcile_schema(fresh_conn)

    live_cols_after = {
        row[1]
        for row in fresh_conn.execute("PRAGMA table_info(meetings)").fetchall()
    }
    assert "title" in live_cols_after


def test_reconcile_adds_datetime_default_column_with_constant(
    fresh_conn: sqlite3.Connection,
) -> None:
    """A3+A4: a datetime('now') column gets a valid ISO sentinel default."""
    # Insert a row before the rebuild so we can verify the constant default.
    fresh_conn.execute(
        "INSERT INTO meetings (id, started_at) VALUES ('test-m', '2026-01-01')"
    )
    _rebuild_table_without_column(fresh_conn, "meetings", "created_at")

    reconcile_schema(fresh_conn)

    live_cols_after = {
        row[1]
        for row in fresh_conn.execute("PRAGMA table_info(meetings)").fetchall()
    }
    assert "created_at" in live_cols_after

    # The existing row gets the ISO sentinel, not an empty string.
    row = fresh_conn.execute(
        "SELECT created_at FROM meetings WHERE id='test-m'"
    ).fetchone()
    assert row is not None
    assert row[0] == "1970-01-01T00:00:00", (
        "Existing row gets ISO sentinel default for datetime column"
    )


# ── A2: idempotent (no ALTERs, shape stable) ──────────────────────────


def test_reconcile_is_idempotent(fresh_conn: sqlite3.Connection) -> None:
    """A2: running reconcile on a current DB twice is a no-op."""
    # First reconcile on fresh schema.
    changed = reconcile_schema(fresh_conn)
    # Fresh schema was just applied by executescript, so no shape drift.
    assert changed is False, "First reconcile on fresh DB should detect no shape change"

    # Snapshot table_info for all tables.
    tables_before = {}
    for (tbl,) in fresh_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ):
        tables_before[tbl] = fresh_conn.execute(
            f'PRAGMA table_info("{tbl}")'
        ).fetchall()

    # Second reconcile.
    changed2 = reconcile_schema(fresh_conn)
    assert changed2 is False, "Second reconcile should detect no shape change"

    # Snapshot again -- should be identical.
    tables_after = {}
    for (tbl,) in fresh_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ):
        tables_after[tbl] = fresh_conn.execute(
            f'PRAGMA table_info("{tbl}")'
        ).fetchall()

    assert tables_before == tables_after, "Second reconcile changed table shapes"


def test_reconcile_no_alter_on_current_db(fresh_conn: sqlite3.Connection) -> None:
    """A2 strengthened: on a current DB, zero ALTERs are executed."""
    alters = _add_missing_columns(fresh_conn)
    assert alters == [], f"Expected no ALTERs on current DB, got {alters}"


def test_reconcile_widens_historical_parent_kind_check_without_row_loss(tmp_path: Path) -> None:
    """A widened parent vocabulary heals an owner-era DB, not only fresh schema."""
    old_schema = SCHEMA_SQL.replace(",'rails.observer-batch','tool.turn'", "")
    assert old_schema != SCHEMA_SQL
    conn = sqlite3.connect(str(tmp_path / "old-parent-kind.db"))
    conn.row_factory = sqlite3.Row
    try:
        # Derive the exact preceding schema from canonical bytes rather than a
        # hand-written table divergence, matching the owner-DB reproducer.
        conn.executescript(old_schema)

        def operation(operation_id: str, native_id: str, name: str) -> None:
            conn.execute(
                """INSERT INTO kernel_operations
                   (operation_id,request_id,idempotency_key,name,version,principal_kind,
                    principal_identity,target_ref,placement,envelope_sha256,policy_version,
                    authority_basis,state,native_id,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    operation_id, operation_id + "-request", operation_id + "-key", name, 1,
                    "service", "migration-proof", "", "", "sha256:proof", "1",
                    "migration-proof", "claimed", native_id, 1000.0, 1000.0,
                ),
            )

        operation("old-parent", "dictation-native", "dictation.session")
        conn.execute(
            """INSERT INTO kernel_parent_runs
               (operation_id,native_id,kind,definition_ref,definition_revision,input_json,
                deadline_at,execution_epoch,planned_node,active_child_invocation_id,child_budget,
                children_json,state,lease_process_id,lease_heartbeat_at,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "old-parent", "dictation-native", "dictation.session", "dictation:legacy", "1",
                '{"source":"pre-slice"}', 9999.0, 1, "", "", 0, "[]", "OPEN", "", None,
                1000.0, 1000.0,
            ),
        )
        before = tuple(conn.execute(
            "SELECT * FROM kernel_parent_runs WHERE operation_id='old-parent'"
        ).fetchone())

        assert reconcile_schema(conn) is True
        after = tuple(conn.execute(
            "SELECT * FROM kernel_parent_runs WHERE operation_id='old-parent'"
        ).fetchone())
        assert after == before

        operation("rails-parent", "rails-native", "rails.observer-batch")
        conn.execute(
            """INSERT INTO kernel_parent_runs
               (operation_id,native_id,kind,definition_ref,definition_revision,input_json,
                deadline_at,execution_epoch,planned_node,active_child_invocation_id,child_budget,
                children_json,state,lease_process_id,lease_heartbeat_at,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "rails-parent", "rails-native", "rails.observer-batch", "rails:batch", "2",
                '{"event_batch_sha256":"sha256:proof"}', 9999.0, 1, "", "", 1, "[]", "OPEN", "", None,
                1000.0, 1000.0,
            ),
        )
        operation("tool-parent", "tool-native", "tool.turn")
        conn.execute(
            """INSERT INTO kernel_parent_runs
               (operation_id,native_id,kind,definition_ref,definition_revision,input_json,
                deadline_at,execution_epoch,planned_node,active_child_invocation_id,child_budget,
                children_json,state,lease_process_id,lease_heartbeat_at,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "tool-parent", "tool-native", "tool.turn", "tool.turn:foundation", "1",
                '{"schema":"ToolTurnParentInput@1"}', 9999.0, 1, "", "", 1, "[]", "OPEN", "", None,
                1000.0, 1000.0,
            ),
        )
        assert reconcile_schema(conn) is False
    finally:
        conn.close()


# ── A1: additive only (orphan tables survive) ──────────────────────────


def test_reconcile_preserves_orphan_table(fresh_conn: sqlite3.Connection) -> None:
    """A1: an extra table not in SCHEMA_SQL survives reconcile with its rows."""
    fresh_conn.execute(
        "CREATE TABLE IF NOT EXISTS orphan_experiment ("
        "  id INTEGER PRIMARY KEY, data TEXT NOT NULL"
        ")"
    )
    fresh_conn.execute("INSERT INTO orphan_experiment (data) VALUES ('keep-me')")
    fresh_conn.execute("INSERT INTO orphan_experiment (data) VALUES ('and-me')")

    reconcile_schema(fresh_conn)

    row = fresh_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='orphan_experiment'"
    ).fetchone()
    assert row is not None, "Orphan table should survive reconcile"

    rows = fresh_conn.execute("SELECT data FROM orphan_experiment ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["keep-me", "and-me"]


# ── A5: no version gate ────────────────────────────────────────────────


def test_newer_db_opens_without_error(tmp_path: Path) -> None:
    """A5: a DB stamped with a version far above the code opens without error."""
    db_path = tmp_path / "newer.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION + 100,),
    )
    conn.commit()

    reconcile_schema(conn)

    row = conn.execute(
        "SELECT version FROM schema_version WHERE version = ?",
        (SCHEMA_VERSION,),
    ).fetchone()
    assert row is not None, "Current version stamp must be present"
    conn.close()


def test_newer_db_opens_via_database_class(tmp_path: Path) -> None:
    """A5: Database() opens a newer-versioned DB without raising."""
    db_path = tmp_path / "newer2.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION + 50,),
    )
    conn.commit()
    conn.close()

    from holdspeak.db.core import Database
    db = Database(db_path)
    db.close()


# ── Reference schema builder ──────────────────────────────────────────


def test_reference_schema_contains_canonical_tables() -> None:
    """The in-memory reference DB has the expected table count."""
    ref = _build_reference_schema()
    assert len(ref) >= 100, f"Expected many tables, got {len(ref)}"
    assert "meetings" in ref
    assert "schema_version" in ref
    assert "decisions" in ref


# ── _is_function_default ──────────────────────────────────────────────


def test_is_function_default_detects_datetime() -> None:
    assert _is_function_default("datetime('now')") is True
    assert _is_function_default("(datetime('now'))") is True
    assert _is_function_default("'hello'") is False
    assert _is_function_default("0") is False
    assert _is_function_default(None) is False


# ── HAZARD: soft-deleted decisions survive reconcile (blocker) ─────────


def test_soft_deleted_decision_survives_reconcile(tmp_path: Path) -> None:
    """BLOCKER regression: a soft-deleted decision must stay deleted after reconcile."""
    db_path = tmp_path / "decisions.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    # Seed a meeting and a decisions artifact.
    conn.execute(
        "INSERT INTO meetings (id, started_at) VALUES ('m1', '2026-01-01')"
    )
    conn.execute(
        """INSERT INTO artifacts (id, meeting_id, artifact_type, title,
                body_markdown, structured_json, plugin_id)
           VALUES ('a1', 'm1', 'decisions', 'Test',
                '## Decisions\n- Decision: test decision (reason: test)',
                '{"decisions": [{"decision": "test decision", "reason": "test"}]}',
                'core')"""
    )

    # Run backfill to create the decision row.
    from holdspeak.db.decisions import backfill_decisions
    result = backfill_decisions(conn)
    assert result["inserted"] >= 1, "Precondition: decision was inserted"

    # Find the decision and soft-delete it.
    decision = conn.execute("SELECT id FROM decisions LIMIT 1").fetchone()
    assert decision is not None
    conn.execute(
        "UPDATE decisions SET deleted=1 WHERE id=?", (decision["id"],)
    )

    # Verify it's deleted.
    row = conn.execute(
        "SELECT deleted FROM decisions WHERE id=?", (decision["id"],)
    ).fetchone()
    assert row["deleted"] == 1, "Precondition: decision is soft-deleted"

    # Run backfill again (simulating what reconcile does on shape change).
    backfill_decisions(conn)

    # The decision must STILL be deleted.
    row = conn.execute(
        "SELECT deleted FROM decisions WHERE id=?", (decision["id"],)
    ).fetchone()
    assert row["deleted"] == 1, "Soft-deleted decision must survive backfill"
    conn.close()


# ── HAZARD: clean DB skips data backfills ──────────────────────────────


def test_clean_db_reconcile_skips_backfills(fresh_conn: sqlite3.Connection) -> None:
    """On a clean already-current DB, reconcile runs no data backfills."""
    with patch("holdspeak.db.reconcile._apply_data_backfills") as mock_backfill:
        changed = reconcile_schema(fresh_conn)
        assert changed is False, "No shape change on a current DB"
        mock_backfill.assert_not_called()


# ── HAZARD: shape-change open triggers backup + backfills ──────────────


def test_shape_change_triggers_backup_and_backfills(tmp_path: Path) -> None:
    """When reconcile detects a shape change, it backs up and runs backfills."""
    db_path = tmp_path / "shape.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)

    # Drop a table to force a shape change.
    conn.execute("DROP TABLE IF EXISTS bookmarks")

    with patch("holdspeak.db.reconcile._apply_data_backfills") as mock_backfill:
        with patch("holdspeak.db.core.backup_database") as mock_backup:
            mock_backup.return_value = tmp_path / "backup.bak"
            changed = reconcile_schema(conn, db_path=db_path)
            assert changed is True, "Shape change should be detected"
            mock_backup.assert_called_once_with(db_path)
            mock_backfill.assert_called_once()

    conn.close()


def test_fresh_creation_does_not_back_up(tmp_path: Path) -> None:
    """A brand-new empty DB creates every table (shape_changed=True) but has
    nothing to protect, so the reconcile must NOT take a backup on creation."""
    db_path = tmp_path / "fresh.db"
    conn = sqlite3.connect(str(db_path))  # empty file, zero tables

    with patch("holdspeak.db.core.backup_database") as mock_backup:
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True, "Fresh creation does change the shape"
        mock_backup.assert_not_called()

    conn.close()


# ── HAZARD: FTS shadow tables are not column-diffed ────────────────────


def test_fts_shadow_tables_excluded_from_reference() -> None:
    """FTS5 shadow tables must not appear in the reference schema."""
    ref = _build_reference_schema()
    fts_shadow_suffixes = ("_data", "_idx", "_content", "_docsize", "_config")

    # Verify no FTS shadow table is in the reference.
    for table in ref:
        for suffix in fts_shadow_suffixes:
            if table.endswith(suffix):
                # Double-check: this table name could be a legitimate table
                # that happens to end in _data. But we know the FTS parents.
                base = table[: -len(suffix)]
                # If the base is a known FTS table name, this is a shadow.
                assert base not in (
                    "decisions_memory_fts",
                    "artifacts_memory_fts",
                    "notes_memory_fts",
                    "segments_fts",
                ), f"FTS shadow table {table} should be excluded from reference"

    # Also verify the FTS virtual tables themselves are excluded.
    for fts_name in (
        "decisions_memory_fts",
        "artifacts_memory_fts",
        "notes_memory_fts",
        "segments_fts",
    ):
        assert fts_name not in ref, f"FTS virtual table {fts_name} should be excluded"


def test_fts_shadow_tables_not_altered(fresh_conn: sqlite3.Connection) -> None:
    """ALTERing an FTS shadow table would corrupt the index. Verify none are touched."""
    alters = _add_missing_columns(fresh_conn)
    fts_fragments = ("_fts_data", "_fts_idx", "_fts_content", "_fts_docsize", "_fts_config")
    for stmt in alters:
        for frag in fts_fragments:
            assert frag not in stmt, f"ALTER touched FTS shadow table: {stmt}"
