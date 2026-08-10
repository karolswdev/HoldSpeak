"""Schema migrations for the HoldSpeak persistence layer.

Extracted from core.py (HS-117-10). Contains all sequential migrations
(versions 1-35) that bring an older database to the current schema.
"""

from __future__ import annotations

import sqlite3

from ..logging_config import get_logger
from .schema import SCHEMA_SQL

log = get_logger("db.migrations")


def run_migrations(conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
    """Run all needed migrations from *from_version* to *to_version*.

    Sequence:
    1. Pre-schema renames (table renames that must precede ``SCHEMA_SQL``).
    2. Apply canonical schema (idempotent ``CREATE TABLE IF NOT EXISTS``).
    3. Post-schema additive migrations (column additions, rebuilds, backfills).
    4. Seed data and version stamp.

    Called by ``Database._ensure_schema`` for both fresh and upgrade paths.
    """
    _migrate_renames(conn, from_version)
    conn.executescript(SCHEMA_SQL)
    _migrate_columns(conn, from_version)
    _apply_seeds_and_backfills(conn)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (to_version,),
    )
    log.info("Database schema created at version %d", to_version)


# ── Pre-schema renames ───────────────────────────────────────────────────


def _migrate_renames(conn: sqlite3.Connection, stored: int) -> None:
    """Non-additive migrations the canonical DDL cannot express.

    v8: the persona table ``agents`` became ``recipes`` (the owner-ratified
    Recipe rename). A plain re-apply would create an EMPTY ``recipes`` table
    beside the old data; the rename carries it. Runs after the backup, so
    the pre-rename copy is always recoverable.
    """
    if stored < 8:
        has_old = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
        ).fetchone()
        has_new = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='recipes'"
        ).fetchone()
        if has_old and not has_new:
            conn.execute("ALTER TABLE agents RENAME TO recipes")
            conn.execute("DROP INDEX IF EXISTS idx_agents_modified")

    # v11: profiles grew the ``node`` column (the meshNode kind). A column
    # ADDED to an existing table is exactly what ``CREATE TABLE IF NOT
    # EXISTS`` cannot express -- the live walk caught a v9 database
    # upgrading to a stamped v11 with the column silently missing.
    if stored < 11:
        has_profiles = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
        ).fetchone()
        if has_profiles:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(profiles)").fetchall()}
            if "node" not in cols:
                conn.execute(
                    "ALTER TABLE profiles ADD COLUMN node TEXT NOT NULL DEFAULT ''"
                )

    # v43 (HS-130-08): "Receipt" is reserved for immutable kernel evidence
    # (Constitution Art. XI). The mutable governing document's tables become
    # ``decision_record*`` and their FK column ``receipt_id`` becomes
    # ``record_id``. Rename in place BEFORE SCHEMA_SQL so the carried rows
    # survive rather than sitting beside a fresh empty table (the agents→recipes
    # pattern). Guarded so it runs exactly once and is idempotent.
    if stored < 43:
        has_old = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decision_receipts'"
        ).fetchone()
        has_new = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decision_records'"
        ).fetchone()
        if has_old and not has_new:
            conn.executescript(
                """
                DROP INDEX IF EXISTS idx_receipt_sources_receipt;
                DROP INDEX IF EXISTS idx_receipt_work_receipt;
                DROP INDEX IF EXISTS idx_receipt_revisions_receipt;
                ALTER TABLE decision_receipts RENAME TO decision_records;
                ALTER TABLE decision_receipt_sources RENAME TO decision_record_sources;
                ALTER TABLE decision_receipt_work RENAME TO decision_record_work;
                ALTER TABLE decision_receipt_revisions RENAME TO decision_record_revisions;
                ALTER TABLE decision_record_sources RENAME COLUMN receipt_id TO record_id;
                ALTER TABLE decision_record_work RENAME COLUMN receipt_id TO record_id;
                ALTER TABLE decision_record_revisions RENAME COLUMN receipt_id TO record_id;
                """
            )


# ── Post-schema additive migrations ─────────────────────────────────────


def _migrate_columns(conn: sqlite3.Connection, stored: int) -> None:
    """Column additions, table rebuilds, and backfills that run after SCHEMA_SQL."""

    # v4 (Phase 24): recipe profile_id and pinned-context columns.
    recipe_cols = {row[1] for row in conn.execute("PRAGMA table_info(recipes)").fetchall()}
    if "profile_id" not in recipe_cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN profile_id TEXT")
    # v7 (Phase 77): the pinned-context columns, additive (the v4 recipe).
    if "manual_context" not in recipe_cols:
        conn.execute(
            "ALTER TABLE recipes ADD COLUMN manual_context TEXT NOT NULL DEFAULT ''"
        )
    if "use_zone_context" not in recipe_cols:
        conn.execute(
            "ALTER TABLE recipes ADD COLUMN use_zone_context INTEGER NOT NULL DEFAULT 0"
        )

    # v5 (Phase 72, HS-72-04): actuator proposals become owner-typed.
    proposal_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
    }
    if proposal_cols and "origin" not in proposal_cols:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(
            """
            CREATE TABLE actuator_proposals_v5 (
                id TEXT PRIMARY KEY,
                meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
                origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'desk')),
                window_id TEXT NOT NULL DEFAULT '',
                plugin_id TEXT NOT NULL,
                plugin_version TEXT NOT NULL DEFAULT 'unknown',
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'proposed',
                target TEXT NOT NULL,
                action TEXT NOT NULL,
                preview TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                reversible INTEGER NOT NULL DEFAULT 0,
                required_capabilities_json TEXT NOT NULL DEFAULT '[]',
                decided_by TEXT,
                result_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                decided_at TEXT,
                executed_at TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            INSERT INTO actuator_proposals_v5 (
                id, meeting_id, origin, window_id, plugin_id, plugin_version,
                idempotency_key, status, target, action, preview, payload_json,
                reversible, required_capabilities_json, decided_by, result_json,
                error, created_at, decided_at, executed_at, updated_at)
            SELECT
                id,
                CASE WHEN meeting_id = 'companion' THEN NULL ELSE meeting_id END,
                CASE WHEN meeting_id = 'companion' THEN 'desk' ELSE 'meeting' END,
                window_id, plugin_id, plugin_version, idempotency_key, status,
                target, action, preview, payload_json, reversible,
                required_capabilities_json, decided_by, result_json, error,
                created_at, decided_at, executed_at, updated_at
            FROM actuator_proposals;
            DROP TABLE actuator_proposals;
            ALTER TABLE actuator_proposals_v5 RENAME TO actuator_proposals;
            CREATE INDEX IF NOT EXISTS idx_actuator_proposals_meeting ON actuator_proposals(meeting_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_actuator_proposals_status ON actuator_proposals(status, created_at DESC);
            DELETE FROM meetings WHERE id = 'companion';
            """
        )
        conn.execute("PRAGMA foreign_keys = ON")

    # v13 (Phase 92, HS-92-02): approval binding columns.
    proposal_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
    }
    approval_binding_columns = {
        "approved_payload_hash": "TEXT",
        "approved_destination": "TEXT",
        "approved_preview_hash": "TEXT",
        "preview_renderer_version": "TEXT",
        "effect_class": "TEXT",
        "policy_version": "TEXT",
    }
    for column, sql_type in approval_binding_columns.items():
        if column not in proposal_cols:
            conn.execute(
                f"ALTER TABLE actuator_proposals ADD COLUMN {column} {sql_type}"
            )

    # v15 (Phase 92, HS-92-04): meeting capture/recovery columns.
    meeting_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(meetings)").fetchall()
    }
    capture_columns = {
        "capture_status": "TEXT NOT NULL DEFAULT 'finalized'",
        "capture_failure": "TEXT",
        "capture_checkpoint_at": "TEXT",
        "capture_checkpoint_seconds": "REAL NOT NULL DEFAULT 0",
        "provenance": "TEXT NOT NULL DEFAULT 'desktop'",
        "sync_modified_at": "TEXT",
    }
    for column, sql_type in capture_columns.items():
        if column not in meeting_cols:
            conn.execute(f"ALTER TABLE meetings ADD COLUMN {column} {sql_type}")

    # v16: preserve every existing Meeting<->Project relationship.
    conn.execute(
        """INSERT OR IGNORE INTO project_resources
           (project_id,resource_ref,relationship,source,confidence,
            created_at,last_modified,deleted)
           SELECT project_id,'meeting:' || meeting_id,'member',source,confidence,
                  detected_at,detected_at,0 FROM meeting_projects"""
    )

    # v6 (Phase 74, HS-74-01): artifacts become owner-typed.
    artifact_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()
    }
    if artifact_cols and "origin" not in artifact_cols:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(
            """
            CREATE TABLE artifacts_v6 (
                id TEXT PRIMARY KEY,
                meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
                origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'run')),
                artifact_type TEXT NOT NULL,
                title TEXT NOT NULL,
                body_markdown TEXT NOT NULL DEFAULT '',
                structured_json TEXT NOT NULL DEFAULT '{}',
                confidence REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'draft',
                plugin_id TEXT NOT NULL DEFAULT 'unknown',
                plugin_version TEXT NOT NULL DEFAULT 'unknown',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            INSERT INTO artifacts_v6 (
                id, meeting_id, origin, artifact_type, title, body_markdown,
                structured_json, confidence, status, plugin_id, plugin_version,
                created_at, updated_at)
            SELECT
                id, meeting_id, 'meeting', artifact_type, title, body_markdown,
                structured_json, confidence, status, plugin_id, plugin_version,
                created_at, updated_at
            FROM artifacts;
            DROP TABLE artifacts;
            ALTER TABLE artifacts_v6 RENAME TO artifacts;
            CREATE INDEX IF NOT EXISTS idx_artifacts_meeting ON artifacts(meeting_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type, created_at DESC);
            """
        )
        conn.execute("PRAGMA foreign_keys = ON")

    # v18 (HS-92-07): capability attempts actual placement.
    attempt_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(capability_attempts)").fetchall()
    }
    if attempt_cols and "actual_placement_json" not in attempt_cols:
        conn.execute(
            "ALTER TABLE capability_attempts "
            "ADD COLUMN actual_placement_json TEXT NOT NULL DEFAULT '{}'"
        )

    # v19 (HS-92-08): authority columns on actuator proposals.
    actuator_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
    }
    authority_columns = {
        "review_decision": "TEXT NOT NULL DEFAULT 'unreviewed'",
        "authorization_state": "TEXT NOT NULL DEFAULT 'proposed'",
        "execution_state": "TEXT NOT NULL DEFAULT 'not_started'",
        "operation_json": "TEXT NOT NULL DEFAULT '{}'",
        "policy_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
        "grant_id": "TEXT",
    }
    for column, sql_type in authority_columns.items():
        if actuator_cols and column not in actuator_cols:
            conn.execute(f"ALTER TABLE actuator_proposals ADD COLUMN {column} {sql_type}")
    if actuator_cols:
        conn.execute(
            """UPDATE actuator_proposals SET
                review_decision = 'unreviewed',
                authorization_state = CASE
                    WHEN status IN ('approved','executed','failed') THEN 'approved'
                    WHEN status = 'rejected' THEN 'rejected'
                    ELSE 'proposed' END,
                execution_state = CASE
                    WHEN status = 'executed' THEN 'succeeded'
                    WHEN status = 'failed' THEN 'failed'
                    ELSE 'not_started' END"""
        )

    # v22 (HS-93-07): steering audit receipt columns.
    steering_cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(steering_audit)").fetchall()
    }
    steering_receipt_columns = {
        "operation_json": "TEXT NOT NULL DEFAULT '{}'",
        "policy_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for column, sql_type in steering_receipt_columns.items():
        if steering_cols and column not in steering_cols:
            conn.execute(
                f"ALTER TABLE steering_audit ADD COLUMN {column} {sql_type}"
            )

    # v28 (HS-106-07): kernel operation causality + unknown state.
    operation_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(kernel_operations)").fetchall()
    }
    for column in ("parent_operation_id", "correlation_id"):
        if operation_cols and column not in operation_cols:
            conn.execute(
                f"ALTER TABLE kernel_operations ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
            )
    invocation_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='capability_invocations'"
    ).fetchone()
    if invocation_sql and "'unknown'" not in str(invocation_sql[0]):
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(
            """
            DROP INDEX IF EXISTS idx_capability_attempts_invocation;
            DROP INDEX IF EXISTS idx_capability_invocations_definition;
            DROP INDEX IF EXISTS idx_capability_invocations_state;
            CREATE TABLE capability_invocations_v28 (
                id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL UNIQUE,
                definition_ref TEXT NOT NULL, initiator TEXT NOT NULL DEFAULT 'owner',
                grounding_refs_json TEXT NOT NULL DEFAULT '[]',
                requested_placement TEXT NOT NULL DEFAULT 'this_machine',
                input_snapshot_json TEXT NOT NULL DEFAULT '{}',
                state TEXT NOT NULL DEFAULT 'running' CHECK (state IN
                    ('running','succeeded','failed','cancelled','unavailable','empty','unknown')),
                result_ref TEXT, error TEXT, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, completed_at TEXT
            );
            INSERT INTO capability_invocations_v28 SELECT * FROM capability_invocations;
            CREATE TABLE capability_attempts_v28 (
                id TEXT PRIMARY KEY,
                invocation_id TEXT NOT NULL REFERENCES capability_invocations_v28(id) ON DELETE CASCADE,
                attempt_index INTEGER NOT NULL, destination TEXT NOT NULL,
                actual_placement_json TEXT NOT NULL DEFAULT '{}', provider TEXT,
                state TEXT NOT NULL DEFAULT 'running' CHECK (state IN
                    ('running','succeeded','failed','cancelled','empty','unknown')),
                error TEXT, result_ref TEXT, started_at TEXT NOT NULL, completed_at TEXT,
                UNIQUE(invocation_id, attempt_index)
            );
            INSERT INTO capability_attempts_v28 SELECT * FROM capability_attempts;
            DROP TABLE capability_attempts;
            DROP TABLE capability_invocations;
            ALTER TABLE capability_invocations_v28 RENAME TO capability_invocations;
            ALTER TABLE capability_attempts_v28 RENAME TO capability_attempts;
            CREATE INDEX idx_capability_invocations_definition
                ON capability_invocations(definition_ref, created_at DESC);
            CREATE INDEX idx_capability_invocations_state
                ON capability_invocations(state, created_at DESC);
            CREATE INDEX idx_capability_attempts_invocation
                ON capability_attempts(invocation_id, attempt_index);
            """
        )
        conn.execute("PRAGMA foreign_keys = ON")

    # v32 (HS-109-02): decisions rebuild for transcript moments.
    stale_ddl = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='decisions'"
    ).fetchone()
    if stale_ddl and "date_basis IN ('meeting_date')" in stale_ddl[0]:
        old_cols = [
            row[1]
            for row in conn.execute("PRAGMA table_info(decisions)").fetchall()
        ]
        conn.execute("ALTER TABLE decisions RENAME TO decisions_stale_v30")
        conn.executescript(
            """
            DROP TRIGGER IF EXISTS decisions_sever_meeting_source;
            DROP TRIGGER IF EXISTS decisions_memory_ai;
            DROP TRIGGER IF EXISTS decisions_memory_ad;
            DROP TRIGGER IF EXISTS decisions_memory_au;
            CREATE TABLE decisions (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                rationale TEXT,
                decided_at TEXT NOT NULL,
                date_basis TEXT NOT NULL DEFAULT 'meeting_date',
                source_timestamp REAL,
                provenance_label TEXT
                    CHECK (provenance_label IN ('reported','anchored')),
                source_artifact_id TEXT NOT NULL,
                source_meeting_id TEXT NOT NULL,
                source_state TEXT NOT NULL DEFAULT 'linked'
                    CHECK (source_state IN ('linked','source_deleted')),
                project_key TEXT,
                lifecycle TEXT NOT NULL DEFAULT 'recorded'
                    CHECK (lifecycle IN ('recorded','accepted','superseded','rejected')),
                superseded_by TEXT REFERENCES decisions(id),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_modified TEXT NOT NULL DEFAULT (datetime('now')),
                deleted INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_decisions_project
            ON decisions(project_key, lifecycle, decided_at DESC);
            CREATE INDEX IF NOT EXISTS idx_decisions_meeting
            ON decisions(source_meeting_id, decided_at DESC);
            CREATE INDEX IF NOT EXISTS idx_decisions_lifecycle
            ON decisions(lifecycle, decided_at DESC);
            CREATE INDEX IF NOT EXISTS idx_decisions_superseded_by
            ON decisions(superseded_by);
            CREATE TRIGGER IF NOT EXISTS decisions_sever_meeting_source
            AFTER DELETE ON meetings BEGIN
                UPDATE decisions
                   SET source_state = 'source_deleted',
                       updated_at = datetime('now'),
                       last_modified = datetime('now')
                 WHERE source_meeting_id = OLD.id AND deleted = 0;
            END;
            """
        )
        conn.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS decisions_memory_ai
            AFTER INSERT ON decisions
            WHEN NEW.deleted = 0 AND NEW.source_state = 'linked' BEGIN
                INSERT INTO decisions_memory_fts(source_id,text,rationale)
                VALUES(NEW.id,NEW.text,COALESCE(NEW.rationale,''));
            END;
            CREATE TRIGGER IF NOT EXISTS decisions_memory_ad
            AFTER DELETE ON decisions BEGIN
                DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
            END;
            CREATE TRIGGER IF NOT EXISTS decisions_memory_au
            AFTER UPDATE ON decisions BEGIN
                DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
                INSERT INTO decisions_memory_fts(source_id,text,rationale)
                SELECT NEW.id,NEW.text,COALESCE(NEW.rationale,'')
                WHERE NEW.deleted=0 AND NEW.source_state='linked';
            END;
            """
        )
        carried = ",".join(c for c in old_cols if c not in
                           ("source_timestamp", "provenance_label"))
        conn.execute("DELETE FROM decisions_memory_fts")
        conn.execute(
            f"INSERT INTO decisions ({carried}) "
            f"SELECT {carried} FROM decisions_stale_v30"
        )
        conn.execute("DROP TABLE decisions_stale_v30")
    decision_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(decisions)").fetchall()
    }
    if "source_timestamp" not in decision_cols:
        conn.execute("ALTER TABLE decisions ADD COLUMN source_timestamp REAL")
    if "provenance_label" not in decision_cols:
        conn.execute(
            "ALTER TABLE decisions ADD COLUMN provenance_label TEXT "
            "CHECK (provenance_label IN ('reported','anchored'))"
        )

    # v36 (HS-118-06): output minting columns.
    artifact_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()
    }
    if "source_run_id" not in artifact_cols:
        conn.execute("ALTER TABLE artifacts ADD COLUMN source_run_id TEXT")
    if "source_item_id" not in artifact_cols:
        conn.execute("ALTER TABLE artifacts ADD COLUMN source_item_id TEXT")
    # Unique index for idempotent minting — created in SCHEMA_SQL for new DBs,
    # but for upgraded DBs the CREATE TABLE IF NOT EXISTS won't run so we ensure
    # it here as well.
    conn.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_source_run_item
           ON artifacts(source_run_id, source_item_id)
           WHERE source_run_id IS NOT NULL AND source_item_id IS NOT NULL"""
    )

    wb_item_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(workbench_items)").fetchall()
    }
    if "result_artifact_id" not in wb_item_cols:
        conn.execute("ALTER TABLE workbench_items ADD COLUMN result_artifact_id TEXT")
    if "mint_attempted" not in wb_item_cols:
        conn.execute("ALTER TABLE workbench_items ADD COLUMN mint_attempted INTEGER NOT NULL DEFAULT 0")

    # HS-118-05: resolver_profile_id on workbenches
    wb_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(workbenches)").fetchall()
    }
    if "resolver_profile_id" not in wb_cols:
        conn.execute("ALTER TABLE workbenches ADD COLUMN resolver_profile_id TEXT")

    # HS-118-06: mint_failures on workbench_runs
    wb_run_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(workbench_runs)").fetchall()
    }
    if "mint_failures" not in wb_run_cols:
        conn.execute("ALTER TABLE workbench_runs ADD COLUMN mint_failures INTEGER NOT NULL DEFAULT 0")

    # v39 (HS-125-03): decision commitments bridge accepted decisions to
    # accountable action items.  SCHEMA_SQL creates this on fresh databases;
    # keep the versioned case so v38 archives receive the table and indexes.
    if stored < 39:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_commitments (
                id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                action_item_id TEXT NOT NULL,
                owner TEXT,
                due_at TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decision_commitments_decision
                ON decision_commitments(decision_id);
            CREATE INDEX IF NOT EXISTS idx_decision_commitments_status
                ON decision_commitments(status);
            """
        )

    # v40 (HS-126-01): persist generated Monday briefs and their collector
    # output. SCHEMA_SQL creates these for fresh databases; retain the explicit
    # migration for archived v39 databases as the versioned upgrade contract.
    if stored < 40:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS monday_briefs (
                id TEXT PRIMARY KEY,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                headline TEXT NOT NULL DEFAULT '',
                generated_at TEXT NOT NULL,
                spoken INTEGER NOT NULL DEFAULT 0,
                disposition TEXT
            );
            CREATE TABLE IF NOT EXISTS monday_brief_items (
                id TEXT PRIMARY KEY,
                brief_id TEXT NOT NULL REFERENCES monday_briefs(id),
                section TEXT NOT NULL,
                text TEXT NOT NULL,
                detail TEXT,
                source_ref TEXT,
                priority INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_monday_brief_items_brief
                ON monday_brief_items(brief_id);
            """
        )

    # v41 (HS-127-01) / v43 (HS-130-08): durable decision records and traceable
    # links. SCHEMA_SQL covers fresh databases; retain this explicit upgrade leg
    # for v40 archives, now emitting the renamed decision_record* tables.
    if stored < 41:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_records (
                id TEXT PRIMARY KEY,
                decision_text TEXT NOT NULL,
                rationale TEXT,
                alternatives TEXT,
                owner TEXT,
                review_date TEXT,
                lifecycle TEXT NOT NULL DEFAULT 'active',
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS decision_record_sources (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL REFERENCES decision_records(id),
                source_type TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decision_record_sources
                ON decision_record_sources(record_id);
            CREATE TABLE IF NOT EXISTS decision_record_work (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL REFERENCES decision_records(id),
                work_type TEXT NOT NULL,
                work_ref TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decision_record_work
                ON decision_record_work(record_id);
            CREATE TABLE IF NOT EXISTS decision_record_revisions (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL REFERENCES decision_records(id),
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decision_record_revisions
                ON decision_record_revisions(record_id);
            """
        )

    # v42 (HS-127-10): decision-record tombstones make a deletion durable across
    # local-first peers without erasing its evidence chain.
    record_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(decision_records)").fetchall()
    }
    if record_cols and "deleted" not in record_cols:
        conn.execute(
            "ALTER TABLE decision_records ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0"
        )

    # v34 (HS-118-01): zone name uniqueness -- add name_normalized column
    # and backfill with dedup.
    dir_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(directories)").fetchall()
    }
    if "name_normalized" not in dir_cols:
        conn.execute(
            "ALTER TABLE directories ADD COLUMN name_normalized TEXT NOT NULL DEFAULT ''"
        )
    from .primitives import _backfill_directory_name_normalized
    _backfill_directory_name_normalized(conn)
    # On upgrade, the unique index must be created AFTER the column exists and the
    # backfill has deduped names. Fresh DBs already have it from SCHEMA_SQL.
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_directory_name_norm "
        "ON directories(name_normalized) WHERE deleted = 0"
    )

    # v45 (HS-131-02): `cancelled` is a distinct kernel terminal fact. SQLite
    # cannot alter CHECK constraints, so carry immutable operations and receipts
    # through matching tables without rewriting any row values.
    if stored < 45:
        kernel_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='kernel_operations'"
        ).fetchone()
        if kernel_sql and "'cancelled'" not in str(kernel_sql[0]):
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript(
                """
                DROP INDEX IF EXISTS idx_kernel_operations_state;
                CREATE TABLE kernel_operations_v45 (
                    operation_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    principal_kind TEXT NOT NULL,
                    principal_identity TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    placement TEXT NOT NULL,
                    envelope_sha256 TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    authority_basis TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN (
                        'admitting','awaiting_decision','awaiting_execution','claimed',
                        'succeeded','failed','refused','cancelled','indeterminate'
                    )),
                    revision INTEGER NOT NULL DEFAULT 1,
                    native_id TEXT NOT NULL,
                    parent_operation_id TEXT NOT NULL DEFAULT '',
                    correlation_id TEXT NOT NULL DEFAULT '',
                    decision TEXT,
                    warrant_json TEXT NOT NULL DEFAULT '{}',
                    warrant_revoked INTEGER NOT NULL DEFAULT 0,
                    claimed_by TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(principal_identity, idempotency_key)
                );
                CREATE TABLE kernel_receipts_v45 (
                    receipt_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations_v45(operation_id),
                    state TEXT NOT NULL CHECK (state IN (
                        'succeeded','failed','refused','cancelled','indeterminate'
                    )),
                    outcome TEXT NOT NULL,
                    result_ref TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL
                );
                INSERT INTO kernel_operations_v45 SELECT * FROM kernel_operations;
                INSERT INTO kernel_receipts_v45 SELECT * FROM kernel_receipts;
                DROP TABLE kernel_receipts;
                DROP TABLE kernel_operations;
                ALTER TABLE kernel_operations_v45 RENAME TO kernel_operations;
                ALTER TABLE kernel_receipts_v45 RENAME TO kernel_receipts;
                CREATE INDEX idx_kernel_operations_state
                    ON kernel_operations(state, created_at);
                """
            )
            conn.execute("PRAGMA foreign_keys = ON")
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError("kernel_v45_foreign_key_check_failed")
    # v46 (HS-131-03): durable runner projection staging.  This is additive so
    # stage references can be introduced one domain materializer at a time.
    if stored < 46:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kernel_projection_stages (
                stage_id TEXT PRIMARY KEY,
                invocation_id TEXT NOT NULL,
                operation_id TEXT NOT NULL REFERENCES kernel_operations(operation_id),
                kind TEXT NOT NULL,
                projection_json TEXT NOT NULL,
                projection_sha256 TEXT NOT NULL,
                result_ref TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL CHECK (state IN ('STAGED','FINALIZING','PUBLISHED','DISCARDED')),
                final_result_json TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(invocation_id, kind)
            );
            CREATE INDEX IF NOT EXISTS idx_kernel_projection_stages_recovery
            ON kernel_projection_stages(state, updated_at);
            CREATE TABLE IF NOT EXISTS ask_results (
                projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
                invocation_id TEXT NOT NULL UNIQUE,
                operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
                receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recipe_results (
                projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
                invocation_id TEXT NOT NULL UNIQUE,
                operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
                receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
                artifact_id TEXT NOT NULL UNIQUE REFERENCES artifacts(id)
            );
            CREATE TABLE IF NOT EXISTS recipe_chat_results (
                projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
                invocation_id TEXT NOT NULL UNIQUE,
                operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
                receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )

    # v47 (HS-131-04): durable native-parent controller state.  This must
    # precede v48 because the checkpoint table has a parent-run foreign key.
    if stored < 47:
        conn.execute("""CREATE TABLE IF NOT EXISTS kernel_parent_runs (
            operation_id TEXT PRIMARY KEY REFERENCES kernel_operations(operation_id),
            native_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL CHECK (kind IN ('sequence','workflow')),
            definition_ref TEXT NOT NULL, definition_revision TEXT NOT NULL,
            input_json TEXT NOT NULL, deadline_at REAL NOT NULL,
            execution_epoch INTEGER NOT NULL DEFAULT 1, planned_node TEXT NOT NULL DEFAULT '',
            active_child_invocation_id TEXT NOT NULL DEFAULT '', child_budget INTEGER NOT NULL,
            children_json TEXT NOT NULL DEFAULT '[]',
            state TEXT NOT NULL CHECK (state IN ('OPEN','CANCELLING','SUCCEEDED','FAILED','CANCELLED','REFUSED','INDETERMINATE')),
            created_at REAL NOT NULL, updated_at REAL NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kernel_parent_runs_state ON kernel_parent_runs(state, updated_at)")

    # v48 (HS-131-04): child output must be a durable receipt-gated checkpoint
    # before it can advance a Sequence/Workflow parent tuple.
    if stored < 48:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kernel_parent_checkpoints (
                stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
                parent_operation_id TEXT NOT NULL REFERENCES kernel_parent_runs(operation_id),
                child_invocation_id TEXT NOT NULL,
                execution_epoch INTEGER NOT NULL,
                planned_node TEXT NOT NULL,
                checkpoint_json TEXT NOT NULL,
                advanced INTEGER NOT NULL CHECK (advanced IN (0,1)),
                created_at REAL NOT NULL,
                UNIQUE(parent_operation_id, child_invocation_id)
            );
            CREATE INDEX IF NOT EXISTS idx_kernel_parent_checkpoints_parent
            ON kernel_parent_checkpoints(parent_operation_id, execution_epoch);
            """
        )

    # v49 (HS-131-04): a parent is abandoned only when its local execution
    # lease goes stale; warrant expiry is not a substitute for this evidence.
    if stored < 49:
        parent_columns = {row[1] for row in conn.execute("PRAGMA table_info(kernel_parent_runs)").fetchall()}
        if "lease_process_id" not in parent_columns:
            conn.execute("ALTER TABLE kernel_parent_runs ADD COLUMN lease_process_id TEXT NOT NULL DEFAULT ''")
        if "lease_heartbeat_at" not in parent_columns:
            conn.execute("ALTER TABLE kernel_parent_runs ADD COLUMN lease_heartbeat_at REAL")

    # v50 (HS-131-05): every native Workbench attempt retains resolvable
    # admitted parent/child receipt links, including cancelled attempts.
    if stored < 50:
        # SQLite cannot widen the parent-kind CHECK in place. Rebuild the tiny
        # controller table while retaining every durable parent fact.
        parent_sql = str(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='kernel_parent_runs'").fetchone()[0])
        if "'workbench'" not in parent_sql:
            conn.execute("ALTER TABLE kernel_parent_runs RENAME TO kernel_parent_runs_v49")
            conn.execute("CREATE TABLE kernel_parent_runs (operation_id TEXT PRIMARY KEY REFERENCES kernel_operations(operation_id),native_id TEXT NOT NULL UNIQUE,kind TEXT NOT NULL CHECK (kind IN ('sequence','workflow','workbench')),definition_ref TEXT NOT NULL,definition_revision TEXT NOT NULL,input_json TEXT NOT NULL,deadline_at REAL NOT NULL,execution_epoch INTEGER NOT NULL DEFAULT 1,planned_node TEXT NOT NULL DEFAULT '',active_child_invocation_id TEXT NOT NULL DEFAULT '',child_budget INTEGER NOT NULL,children_json TEXT NOT NULL DEFAULT '[]',state TEXT NOT NULL CHECK (state IN ('OPEN','CANCELLING','SUCCEEDED','FAILED','CANCELLED','REFUSED','INDETERMINATE')),lease_process_id TEXT NOT NULL DEFAULT '',lease_heartbeat_at REAL,created_at REAL NOT NULL,updated_at REAL NOT NULL)")
            conn.execute("INSERT INTO kernel_parent_runs SELECT * FROM kernel_parent_runs_v49")
            conn.execute("DROP TABLE kernel_parent_runs_v49")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kernel_parent_runs_state ON kernel_parent_runs(state, updated_at)")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(workbench_runs)").fetchall()}
        if "parent_operation_id" not in columns:
            conn.execute("ALTER TABLE workbench_runs ADD COLUMN parent_operation_id TEXT NOT NULL DEFAULT ''")
        if "parent_receipt_id" not in columns:
            conn.execute("ALTER TABLE workbench_runs ADD COLUMN parent_receipt_id TEXT NOT NULL DEFAULT ''")
        if "child_links_json" not in columns:
            conn.execute("ALTER TABLE workbench_runs ADD COLUMN child_links_json TEXT NOT NULL DEFAULT '[]'")

    # v51 (HS-131-05): cancellation and reconciliation winners are visible in
    # Workbench coordination history, rather than being misreported as running.
    if stored < 51:
        workbench_sql = str(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workbench_runs'").fetchone()[0])
        if "'cancelled'" not in workbench_sql:
            conn.execute("ALTER TABLE workbench_runs RENAME TO workbench_runs_v50")
            conn.execute("CREATE TABLE workbench_runs (id TEXT PRIMARY KEY,workbench_id TEXT NOT NULL,started_at TEXT NOT NULL,completed_at TEXT,items_attempted INTEGER NOT NULL DEFAULT 0,items_completed INTEGER NOT NULL DEFAULT 0,items_failed INTEGER NOT NULL DEFAULT 0,mint_failures INTEGER NOT NULL DEFAULT 0,total_tokens INTEGER NOT NULL DEFAULT 0,egress_boundary TEXT NOT NULL DEFAULT '',model TEXT NOT NULL DEFAULT '',constitutional_context_revision INTEGER NOT NULL DEFAULT 0,constitutional_context_hash TEXT NOT NULL DEFAULT '',skills_injected_json TEXT NOT NULL DEFAULT '[]',parent_operation_id TEXT NOT NULL DEFAULT '',parent_receipt_id TEXT NOT NULL DEFAULT '',child_links_json TEXT NOT NULL DEFAULT '[]',status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed','cancelled','indeterminate')))")
            conn.execute("INSERT INTO workbench_runs SELECT * FROM workbench_runs_v50")
            conn.execute("DROP TABLE workbench_runs_v50")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workbench_runs_workbench ON workbench_runs(workbench_id, started_at DESC)")

    # v52 (HS-131-06): local schedule revision and delegation tables are
    # additive. Existing enabled schedules intentionally receive no authority.
    if stored < 52:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(workbenches)").fetchall()}
        if "schedule_revision" not in columns:
            conn.execute("ALTER TABLE workbenches ADD COLUMN schedule_revision INTEGER NOT NULL DEFAULT 1")
        operation_columns = {row[1] for row in conn.execute("PRAGMA table_info(kernel_operations)").fetchall()}
        if "delegator_kind" not in operation_columns:
            conn.execute("ALTER TABLE kernel_operations ADD COLUMN delegator_kind TEXT NOT NULL DEFAULT ''")
        if "delegator_identity" not in operation_columns:
            conn.execute("ALTER TABLE kernel_operations ADD COLUMN delegator_identity TEXT NOT NULL DEFAULT ''")


def _apply_seeds_and_backfills(conn: sqlite3.Connection) -> None:
    """Seed data and index rebuilds that run after all migrations."""
    # Lazy imports to avoid circular dependencies at module load time.
    from .decisions import backfill_decisions
    from .memory import rebuild_memory_index

    decision_backfill = backfill_decisions(conn)
    log.info(
        "Decision backfill: "
        + ", ".join(f"{key}={value}" for key, value in decision_backfill.items())
    )
    memory_counts = rebuild_memory_index(conn)
    log.info(
        "Memory index rebuild: "
        + ", ".join(f"{key}={value}" for key, value in memory_counts.items())
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO activity_privacy_settings
            (id, enabled, retention_days, updated_at)
        VALUES (1, 1, 30, datetime('now'))
        """
    )
