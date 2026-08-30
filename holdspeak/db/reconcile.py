"""Declarative schema reconciliation for the HoldSpeak persistence layer.

Replaces the versioned migration chain (HS-137-01).  ``reconcile_schema``
is idempotent and additive-only: it CREATEs missing tables/indexes/triggers,
ALTERs in missing columns, and runs the idempotent seeds/backfills only when
the schema shape actually changed.  It never DROPs a table, DROPs a column,
or DELETEs a row.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Optional

from ..logging_config import get_logger
from .schema import SCHEMA_SQL, SCHEMA_VERSION

log = get_logger("db.reconcile")

# ── FTS shadow-table suffixes (never column-diff or ALTER these) ───────

_FTS_SHADOW_SUFFIXES = ("_data", "_idx", "_content", "_docsize", "_config")


def _is_fts_shadow(table_name: str, fts_parents: set[str]) -> bool:
    """Return True if *table_name* is a shadow table of a known FTS virtual table."""
    for suffix in _FTS_SHADOW_SUFFIXES:
        if table_name.endswith(suffix):
            base = table_name[: -len(suffix)]
            if base in fts_parents:
                return True
    return False


def _intel_job_id(meeting_id: str, transcript_hash: str, requested_at: str) -> str:
    """Return the stable migration ID for one legacy Meeting-keyed job."""
    import hashlib

    material = "legacy-intel-job-v1\x1f".join((meeting_id, transcript_hash, requested_at))
    return "ij_" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _intel_descriptor_sha256(
    meeting_id: str, transcript_hash: str, displaced_work: str,
) -> str:
    """Hash the content-free immutable descriptor stored on a queue row."""
    import hashlib
    import json

    try:
        parsed = json.loads(displaced_work or "[]")
    except (TypeError, ValueError):
        parsed = []
    material = json.dumps(
        {
            "schema": "MeetingDeferredIntelWorkDescriptor@1",
            "meeting_id": meeting_id,
            "transcript_hash": transcript_hash,
            "displaced_work": parsed if isinstance(parsed, list) else [],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _rebuild_legacy_intel_queue_tables(conn: sqlite3.Connection) -> bool:
    """Atomically replace the pre-C Meeting-keyed queue shape when required.

    SQLite cannot alter a primary key.  Renaming both coupled tables, copying
    bytes into the new shape, and dropping only the renamed temporary tables
    keeps the old schema and rows intact if any statement raises before commit.
    """
    job_columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info('intel_jobs')")
    }
    if not job_columns or "job_id" in job_columns:
        return False
    attempt_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='intel_job_attempts'"
    ).fetchone()
    nested = conn.in_transaction
    if nested:
        conn.execute("SAVEPOINT phase143_intel_queue_rebuild")
    else:
        conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("ALTER TABLE intel_jobs RENAME TO intel_jobs__legacy_phase143")
        if attempt_exists is not None:
            conn.execute(
                "ALTER TABLE intel_job_attempts RENAME TO intel_job_attempts__legacy_phase143"
            )
        conn.execute(
            """CREATE TABLE intel_jobs (
                job_id TEXT PRIMARY KEY,
                meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                origin_job_id TEXT REFERENCES intel_jobs(job_id),
                work_descriptor_sha256 TEXT NOT NULL,
                transcript_hash TEXT NOT NULL,
                displaced_work TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'queued',
                lifecycle_posture TEXT NOT NULL DEFAULT 'queued',
                claim_id TEXT,
                parent_operation_id TEXT,
                bundle_id TEXT,
                bundle_sha256 TEXT,
                executor_lease_token TEXT,
                executor_lease_epoch INTEGER NOT NULL DEFAULT 0,
                executor_lease_expires_at REAL,
                requested_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT
            )"""
        )
        conn.execute(
            """CREATE TABLE intel_job_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                job_id TEXT REFERENCES intel_jobs(job_id),
                origin_job_id TEXT REFERENCES intel_jobs(job_id),
                claim_id TEXT,
                parent_operation_id TEXT,
                bundle_id TEXT,
                event_kind TEXT NOT NULL DEFAULT 'attempt',
                attempt INTEGER NOT NULL,
                outcome TEXT NOT NULL,
                error TEXT,
                retry_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        jobs = conn.execute(
            "SELECT meeting_id,status,transcript_hash,requested_at,updated_at,"
            "attempts,last_error,displaced_work FROM intel_jobs__legacy_phase143"
        ).fetchall()
        legacy_job_ids: dict[str, str] = {}
        for row in jobs:
            meeting_id = str(row["meeting_id"])
            transcript_hash = str(row["transcript_hash"])
            requested_at = str(row["requested_at"])
            job_id = _intel_job_id(meeting_id, transcript_hash, requested_at)
            legacy_job_ids[meeting_id] = job_id
            displaced_work = str(row["displaced_work"] or "[]")
            status = str(row["status"])
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,work_descriptor_sha256,transcript_hash,
                    displaced_work,status,lifecycle_posture,requested_at,updated_at,
                    attempts,last_error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job_id,
                    meeting_id,
                    _intel_descriptor_sha256(meeting_id, transcript_hash, displaced_work),
                    transcript_hash,
                    displaced_work,
                    status,
                    status,
                    requested_at,
                    str(row["updated_at"]),
                    int(row["attempts"]),
                    row["last_error"],
                ),
            )
        if attempt_exists is not None:
            for row in conn.execute(
                "SELECT id,meeting_id,attempt,outcome,error,retry_at,created_at "
                "FROM intel_job_attempts__legacy_phase143"
            ):
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        id,meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                    ) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        int(row["id"]),
                        str(row["meeting_id"]),
                        legacy_job_ids.get(str(row["meeting_id"])),
                        "legacy_attempt",
                        int(row["attempt"]),
                        str(row["outcome"]),
                        row["error"],
                        row["retry_at"],
                        str(row["created_at"]),
                    ),
                )
            conn.execute("DROP TABLE intel_job_attempts__legacy_phase143")
        conn.execute("DROP TABLE intel_jobs__legacy_phase143")
        if nested:
            conn.execute("RELEASE SAVEPOINT phase143_intel_queue_rebuild")
        else:
            conn.execute("COMMIT")
    except Exception:
        if nested:
            conn.execute("ROLLBACK TO SAVEPOINT phase143_intel_queue_rebuild")
            conn.execute("RELEASE SAVEPOINT phase143_intel_queue_rebuild")
        else:
            conn.execute("ROLLBACK")
        raise
    return True


def _parent_kind_set(sql: str) -> set[str]:
    """Extract the closed parent-kind vocabulary from one table DDL string."""
    match = re.search(
        r"\bkind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*kind\s+IN\s*\(([^)]*)\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        raise RuntimeError("kernel_parent_runs kind constraint is missing")
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _canonical_parent_runs_ddl() -> tuple[str, set[str], list[str]]:
    """Return canonical parent DDL and its ordered columns from SCHEMA_SQL."""
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_SQL)
        row = reference.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='kernel_parent_runs'"
        ).fetchone()
        if row is None or not isinstance(row[0], str):
            raise RuntimeError("canonical kernel_parent_runs table is missing")
        ddl = str(row[0])
        columns = [
            str(item[1])
            for item in reference.execute("PRAGMA table_info('kernel_parent_runs')")
        ]
        return ddl, _parent_kind_set(ddl), columns
    finally:
        reference.close()


def _quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _rebuild_kernel_parent_runs_for_kind_drift(conn: sqlite3.Connection) -> bool:
    """Widen a historical parent-kind CHECK without dropping durable rows.

    SQLite cannot ALTER a CHECK constraint.  We copy the canonical table shape
    into a replacement under a savepoint, swap it in, and recreate every stored
    index/trigger owned by the table.  The trigger condition is semantic: any
    future canonical parent kind absent from the stored DDL heals in this same
    path, while a current database is a strict no-op.
    """
    live = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='kernel_parent_runs'"
    ).fetchone()
    if live is None or not isinstance(live[0], str):
        return False
    canonical_ddl, canonical_kinds, canonical_columns = _canonical_parent_runs_ddl()
    if canonical_kinds <= _parent_kind_set(str(live[0])):
        return False

    # A trigger owned by another table can still name this parent table in its
    # body. SQLite reparses those during RENAME, so preserve and temporarily
    # remove them too; otherwise the short DROP→RENAME swap is rejected.
    dependents = conn.execute(
        """SELECT type,name,sql FROM sqlite_master
             WHERE (
                    (tbl_name='kernel_parent_runs' AND type IN ('index','trigger'))
                 OR (type='trigger' AND sql LIKE '%kernel_parent_runs%')
             ) AND sql IS NOT NULL
             ORDER BY CASE type WHEN 'index' THEN 0 ELSE 1 END, name"""
    ).fetchall()
    live_columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info('kernel_parent_runs')")
    }
    columns = [column for column in canonical_columns if column in live_columns]
    if not columns:
        raise RuntimeError("kernel_parent_runs has no copyable columns")
    replacement = "kernel_parent_runs__reconcile_replacement"
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (replacement,)
    ).fetchone() is not None:
        raise RuntimeError("kernel_parent_runs replacement table already exists")
    replacement_ddl, substitutions = re.subn(
        r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"kernel_parent_runs\"|kernel_parent_runs)",
        f"CREATE TABLE {_quoted(replacement)}",
        canonical_ddl,
        count=1,
        flags=re.IGNORECASE,
    )
    if substitutions != 1:
        raise RuntimeError("canonical kernel_parent_runs DDL cannot be renamed")

    nested = conn.in_transaction
    foreign_keys = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    # FK enforcement cannot be toggled under a surrounding transaction.  The
    # normal reconciler entry is top-level; a nested caller still receives the
    # SAVEPOINT + deferred-constraint form rather than an implicit commit.
    if not nested and foreign_keys:
        conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("SAVEPOINT kernel_parent_runs_kind_rebuild")
    try:
        conn.execute(replacement_ddl)
        copied = ", ".join(_quoted(column) for column in columns)
        conn.execute(
            f"INSERT INTO {_quoted(replacement)} ({copied}) "
            f"SELECT {copied} FROM {_quoted('kernel_parent_runs')}"
        )
        for kind, name, _sql in dependents:
            if str(kind) == "trigger":
                conn.execute(f"DROP TRIGGER {_quoted(str(name))}")
        conn.execute("DROP TABLE kernel_parent_runs")
        conn.execute(
            f"ALTER TABLE {_quoted(replacement)} RENAME TO kernel_parent_runs"
        )
        for _kind, _name, sql in dependents:
            conn.execute(str(sql))
        conn.execute("RELEASE SAVEPOINT kernel_parent_runs_kind_rebuild")
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT kernel_parent_runs_kind_rebuild")
        conn.execute("RELEASE SAVEPOINT kernel_parent_runs_kind_rebuild")
        raise
    finally:
        if not nested and foreign_keys:
            conn.execute("PRAGMA foreign_keys=ON")
    return True


def _rebuild_action_items_for_nullable_meeting_id(conn: sqlite3.Connection) -> bool:
    """Make ``action_items.meeting_id`` nullable (HS-153-05).

    SQLite cannot ALTER a column to drop NOT NULL.  We copy the durable rows
    into the canonical table shape (which declares ``meeting_id`` without
    NOT NULL), swap it in, and recreate every stored index/trigger owned by
    the table.  The trigger condition is semantic: if the live DDL already
    omits ``NOT NULL`` on ``meeting_id``, this is a no-op.
    """
    live = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='action_items'"
    ).fetchone()
    if live is None or not isinstance(live[0], str):
        return False  # table does not exist yet; SCHEMA_SQL will create it
    live_sql = str(live[0]).upper()
    # Detect the specific pattern: MEETING_ID TEXT NOT NULL
    # If NOT NULL is absent, no rebuild needed.
    if "MEETING_ID" not in live_sql:
        return False  # unlikely; table has no meeting_id column at all
    # Heuristic: find the MEETING_ID column clause and check for NOT NULL.
    # Split the DDL into column clauses; look at the one containing MEETING_ID.
    needs_rebuild = False
    for clause in live_sql.split(","):
        if "MEETING_ID" in clause and "NOT NULL" in clause:
            needs_rebuild = True
            break
    if not needs_rebuild:
        return False

    # Build canonical DDL from SCHEMA_SQL.
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_SQL)
        canonical_row = reference.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='action_items'"
        ).fetchone()
        if canonical_row is None:
            return False
        canonical_ddl = str(canonical_row[0])
        canonical_columns = [
            str(row[1]) for row in reference.execute("PRAGMA table_info('action_items')")
        ]
    finally:
        reference.close()

    # Collect dependents (indexes, triggers that reference this table).
    dependents = conn.execute(
        """SELECT type, name, sql FROM sqlite_master
             WHERE (
                    (tbl_name='action_items' AND type IN ('index','trigger'))
                 OR (type='trigger' AND sql LIKE '%action_items%')
             ) AND sql IS NOT NULL
             ORDER BY CASE type WHEN 'index' THEN 0 ELSE 1 END, name"""
    ).fetchall()
    live_columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info('action_items')")
    }
    columns = [col for col in canonical_columns if col in live_columns]
    if not columns:
        raise RuntimeError("action_items has no copyable columns")

    replacement = "action_items__reconcile_replacement"
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (replacement,)
    ).fetchone() is not None:
        raise RuntimeError("action_items replacement table already exists")

    replacement_ddl, substitutions = re.subn(
        r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"action_items\"|action_items)",
        f"CREATE TABLE {_quoted(replacement)}",
        canonical_ddl,
        count=1,
        flags=re.IGNORECASE,
    )
    if substitutions != 1:
        raise RuntimeError("canonical action_items DDL cannot be renamed")

    nested = conn.in_transaction
    foreign_keys = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    if not nested and foreign_keys:
        conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("SAVEPOINT action_items_nullable_meeting_id")
    try:
        conn.execute(replacement_ddl)
        copied = ", ".join(_quoted(col) for col in columns)
        conn.execute(
            f"INSERT INTO {_quoted(replacement)} ({copied}) "
            f"SELECT {copied} FROM {_quoted('action_items')}"
        )
        for kind, name, _sql in dependents:
            if str(kind) == "trigger":
                conn.execute(f"DROP TRIGGER {_quoted(str(name))}")
        conn.execute("DROP TABLE action_items")
        conn.execute(
            f"ALTER TABLE {_quoted(replacement)} RENAME TO action_items"
        )
        for _kind, _name, sql in dependents:
            conn.execute(str(sql))
        conn.execute("RELEASE SAVEPOINT action_items_nullable_meeting_id")
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT action_items_nullable_meeting_id")
        conn.execute("RELEASE SAVEPOINT action_items_nullable_meeting_id")
        raise
    finally:
        if not nested and foreign_keys:
            conn.execute("PRAGMA foreign_keys=ON")
    log.info("action_items: meeting_id relaxed to nullable (HS-153-05 table rebuild)")
    return True


def _thread_parts_kind_set(sql: str) -> set[str]:
    """Extract the closed kind vocabulary from thread_message_parts DDL."""
    match = re.search(
        r"\bkind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*kind\s+IN\s*\(([^)]*)\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return set()
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _rebuild_thread_message_parts_for_kind_drift(conn: sqlite3.Connection) -> bool:
    """Widen the thread_message_parts kind CHECK to include guardrail kinds (HS-153-03).

    The pattern mirrors ``_rebuild_kernel_parent_runs_for_kind_drift``:
    detect the live kind set vs the canonical DDL, copy rows into the
    canonical shape under a SAVEPOINT, preserve indexes/triggers/FTS, log once.
    """
    live = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='thread_message_parts'"
    ).fetchone()
    if live is None or not isinstance(live[0], str):
        return False

    # Build canonical DDL from SCHEMA_SQL
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_SQL)
        canonical_row = reference.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='thread_message_parts'"
        ).fetchone()
        if canonical_row is None:
            return False
        canonical_ddl = str(canonical_row[0])
        canonical_kinds = _thread_parts_kind_set(canonical_ddl)
        canonical_columns = [
            str(row[1]) for row in reference.execute("PRAGMA table_info('thread_message_parts')")
        ]
    finally:
        reference.close()

    live_kinds = _thread_parts_kind_set(str(live[0]))
    if not live_kinds:
        return False
    if canonical_kinds <= live_kinds:
        return False  # live DDL already has all canonical kinds

    # Collect dependents (indexes, triggers, FTS triggers that reference this table)
    dependents = conn.execute(
        """SELECT type, name, sql FROM sqlite_master
             WHERE (
                    (tbl_name='thread_message_parts' AND type IN ('index','trigger'))
                 OR (type='trigger' AND sql LIKE '%thread_message_parts%')
             ) AND sql IS NOT NULL
             ORDER BY CASE type WHEN 'index' THEN 0 ELSE 1 END, name"""
    ).fetchall()
    live_columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info('thread_message_parts')")
    }
    columns = [col for col in canonical_columns if col in live_columns]
    if not columns:
        raise RuntimeError("thread_message_parts has no copyable columns")

    replacement = "thread_message_parts__reconcile_replacement"
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (replacement,)
    ).fetchone() is not None:
        raise RuntimeError("thread_message_parts replacement table already exists")

    replacement_ddl, substitutions = re.subn(
        r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"thread_message_parts\"|thread_message_parts)",
        f"CREATE TABLE {_quoted(replacement)}",
        canonical_ddl,
        count=1,
        flags=re.IGNORECASE,
    )
    if substitutions != 1:
        raise RuntimeError("canonical thread_message_parts DDL cannot be renamed")

    nested = conn.in_transaction
    foreign_keys = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    if not nested and foreign_keys:
        conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("SAVEPOINT thread_message_parts_kind_rebuild")
    try:
        conn.execute(replacement_ddl)
        copied = ", ".join(_quoted(col) for col in columns)
        conn.execute(
            f"INSERT INTO {_quoted(replacement)} ({copied}) "
            f"SELECT {copied} FROM {_quoted('thread_message_parts')}"
        )
        for kind, name, _sql in dependents:
            if str(kind) == "trigger":
                conn.execute(f"DROP TRIGGER IF EXISTS {_quoted(str(name))}")
        conn.execute("DROP TABLE thread_message_parts")
        conn.execute(
            f"ALTER TABLE {_quoted(replacement)} RENAME TO thread_message_parts"
        )
        for _kind, _name, sql in dependents:
            conn.execute(str(sql))
        conn.execute("RELEASE SAVEPOINT thread_message_parts_kind_rebuild")
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT thread_message_parts_kind_rebuild")
        conn.execute("RELEASE SAVEPOINT thread_message_parts_kind_rebuild")
        raise
    finally:
        if not nested and foreign_keys:
            conn.execute("PRAGMA foreign_keys=ON")
    log.info("thread_message_parts: kind CHECK widened for guardrail kinds (HS-153-03 table rebuild)")
    return True


def _refresh_tool_turn_lifecycle_guards(conn: sqlite3.Connection) -> bool:
    """Upgrade A2's blanket immutability guards to the fenced A3/A4 lifecycle.

    SQLite's ``CREATE TRIGGER IF NOT EXISTS`` cannot revise a historical trigger.
    Compare the canonical trigger SQL generated from this source, then replace
    only the two guards whose frozen identity must now receive one durable
    receipt/adoption transition.
    """
    names = ("tool_turn_model_steps_no_update", "tool_turn_effect_children_no_update")
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_SQL)
        expected = {
            str(name): str(row[0])
            for name in names
            if (row := reference.execute(
                "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (name,)
            ).fetchone()) is not None
        }
    finally:
        reference.close()
    changed = False
    for name, sql in expected.items():
        row = conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (name,)).fetchone()
        if row is not None and str(row[0]) == sql:
            continue
        if row is not None:
            conn.execute(f"DROP TRIGGER {_quoted(name)}")
        conn.execute(sql)
        changed = True
    return changed


def reconcile_schema(
    conn: sqlite3.Connection,
    *,
    db_path: Optional[Path] = None,
) -> bool:
    """Bring *conn* to the canonical schema shape, idempotently.

    1. Apply ``SCHEMA_SQL`` (all ``CREATE ... IF NOT EXISTS``).
    2. For each canonical table, add any columns the live DB is missing.
    3. If the shape changed (table created or column added), optionally
       back up the DB file first, then run the data backfills.
    4. Stamp the informational ``schema_version`` row (never read to gate).

    Returns True if the schema shape was changed, False if it was already
    current (a true no-op).

    Parameters
    ----------
    db_path : Path, optional
        The on-disk path of the database, used for the conditional backup.
        When None (e.g. an in-memory DB or test), the backup step is skipped.

    Invariants
    ----------
    A1 -- additive only (never DROP / DELETE).
    A2 -- idempotent (running twice is a no-op).
    A3 -- self-heals shape (missing tables and columns are created).
    A4 -- ALTER-safe defaults (function defaults use a constant in ALTER).
    A5 -- no version gate (a "newer" DB opens without error).
    """

    # ── 1. Snapshot pre-reconcile tables ───────────────────────────────
    pre_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    # These immutable vocabulary/primary-key shape changes cannot be
    # expressed as ALTER TABLE. Rebuild before SCHEMA_SQL recreates canonical
    # indexes and triggers around their replacement tables.
    intel_queue_rebuilt = _rebuild_legacy_intel_queue_tables(conn)
    parent_kind_rebuilt = _rebuild_kernel_parent_runs_for_kind_drift(conn)
    action_items_rebuilt = _rebuild_action_items_for_nullable_meeting_id(conn)
    thread_parts_rebuilt = _rebuild_thread_message_parts_for_kind_drift(conn)

    # ── 1b. Add missing columns to EXISTING tables first (HS-152-06) ────
    # SCHEMA_SQL carries `CREATE INDEX IF NOT EXISTS` statements over
    # columns that were added to canonical tables after a database was
    # born (e.g. scheduled_recordings(calendar_event_id), Phase 136).
    # SQLite validates a new index's columns at creation, so running the
    # script before the additive column reconcile strands every older
    # database with "no such column" — the owner's real desk included.
    # HS-142-02 special-cased one such index below; this pass closes the
    # class: columns first, then the script.
    pre_columns_added = _add_missing_columns(conn, existing_only=True)
    if pre_columns_added:
        log.info("Reconcile: pre-pass added %d column(s) before SCHEMA_SQL", len(pre_columns_added))

    # ── 2. Create any missing tables / indexes / triggers ──────────────
    conn.executescript(SCHEMA_SQL)
    tool_turn_guards_refreshed = _refresh_tool_turn_lifecycle_guards(conn)

    post_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    tables_created = post_tables - pre_tables
    shape_changed = bool(tables_created) or intel_queue_rebuilt or parent_kind_rebuilt or action_items_rebuilt or tool_turn_guards_refreshed
    if pre_columns_added:
        shape_changed = True
    if tables_created:
        log.info("Reconcile: created tables %s", sorted(tables_created))

    # ── 3. Add any missing columns (inside a transaction) ──────────────
    columns_added = _add_missing_columns(conn)
    if columns_added:
        shape_changed = True

    # HS-142-02: this index depends on a column added to an existing canonical
    # table. Creating it in SCHEMA_SQL would make SQLite evaluate the index
    # before the additive column reconcile and strand every Story-01 database.
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_inference_acquisition_source
              ON inference_model_acquisitions(source_claim_sha256, state, updated_at)"""
    )

    # ── 4. Conditional backup + data backfills ─────────────────────────
    # Back up only when an EXISTING, populated database gains shape — never
    # on fresh creation (an empty new DB has nothing to protect).  A fresh
    # DB has no tables before the reconcile, so ``pre_tables`` is empty.
    if shape_changed and pre_tables and db_path is not None and db_path.exists():
        from .core import backup_database
        backup = backup_database(db_path)
        log.warning(
            "Schema shape changed; backed up to %s before applying backfills",
            backup,
        )

    if shape_changed:
        # Wrap backfills in an explicit transaction so a partial failure
        # rolls back cleanly (FIX 5).  The IF-NOT-EXISTS DDL already
        # committed via executescript, but it is safe to re-run.
        conn.execute("BEGIN")
        try:
            _apply_data_backfills(conn)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    # Always run the cheap, idempotent privacy seed.
    conn.execute(
        """
        INSERT OR IGNORE INTO activity_privacy_settings
            (id, enabled, retention_days, updated_at)
        VALUES (1, 1, 30, datetime('now'))
        """
    )

    # ── 5. Informational version stamp (never read to gate) ────────────
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    log.info(
        "Schema reconciled to version %d (changed=%s)", SCHEMA_VERSION, shape_changed
    )
    return shape_changed


# ── Column reconciliation ──────────────────────────────────────────────


def _build_reference_schema() -> dict[str, list[dict]]:
    """Create an in-memory DB from ``SCHEMA_SQL`` and return its column map.

    Excludes FTS5 shadow tables -- those are managed internally by SQLite
    and must never be column-diffed or ALTERed.

    Returns ``{table_name: [col_dict, ...]}`` where each *col_dict* has the
    keys returned by ``PRAGMA table_info``: *cid*, *name*, *type*, *notnull*,
    *dflt_value*, *pk*.
    """
    ref = sqlite3.connect(":memory:")
    try:
        ref.executescript(SCHEMA_SQL)

        # Identify FTS virtual tables by their CREATE VIRTUAL TABLE sql.
        fts_parents: set[str] = set()
        for row in ref.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table'"
        ):
            sql_text = row[1] or ""
            if sql_text.strip().upper().startswith("CREATE VIRTUAL TABLE"):
                fts_parents.add(row[0])

        tables: dict[str, list[dict]] = {}
        for (tbl,) in ref.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ):
            # Skip FTS virtual tables and their shadow tables.
            if tbl in fts_parents or _is_fts_shadow(tbl, fts_parents):
                continue
            cols = []
            for row in ref.execute(f'PRAGMA table_info("{tbl}")'):
                cols.append(
                    {
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": row[3],
                        "dflt_value": row[4],
                        "pk": row[5],
                    }
                )
            tables[tbl] = cols
        return tables
    finally:
        ref.close()


_FUNC_DEFAULT_RE = re.compile(r"^\s*\(?\s*\w+\s*\(", re.IGNORECASE)
"""Matches parenthesised/function-call defaults like ``datetime('now')``."""


def _is_function_default(dflt: str | None) -> bool:
    """Return True if *dflt* is a function expression that SQLite rejects in ALTER."""
    if dflt is None:
        return False
    return bool(_FUNC_DEFAULT_RE.match(dflt))


def _is_datetime_function_default(dflt: str | None) -> bool:
    """Return True if *dflt* is a datetime/date function expression."""
    if dflt is None:
        return False
    return bool(re.match(r"^\s*\(?\s*datetime\s*\(", dflt, re.IGNORECASE))


def _constant_default_for(col: dict) -> str:
    """Return a safe constant DEFAULT clause for an ALTER TABLE ADD COLUMN.

    SQLite rejects non-constant (function) defaults in ALTER TABLE ADD
    COLUMN.  This returns a constant substitute that is type-appropriate
    for existing rows (which legitimately have no value).  New INSERTs
    still get the function default from the CREATE TABLE definition.

    For datetime-function TEXT columns, uses an ISO sentinel instead of
    empty string to avoid ``datetime.fromisoformat('')`` crashes downstream.
    """
    typ = (col["type"] or "").upper()
    if typ in ("INTEGER", "INT"):
        return "DEFAULT 0"
    if typ in ("REAL", "FLOAT", "DOUBLE"):
        return "DEFAULT 0"
    # TEXT: datetime-function defaults get a valid ISO sentinel.
    if _is_datetime_function_default(col.get("dflt_value")):
        return "DEFAULT '1970-01-01T00:00:00'"
    # Other TEXT, BLOB, etc.
    return "DEFAULT ''"


def _alter_column_sql(table: str, col: dict) -> str:
    """Build the ``ALTER TABLE ... ADD COLUMN ...`` statement for *col*.

    Handles:
    - Function-expression defaults -> constant substitute (A4).
    - NOT NULL columns -> supplies the constant default so the ALTER succeeds.
    - Nullable columns with no default -> bare column add.
    """
    parts = [f'ALTER TABLE "{table}" ADD COLUMN "{col["name"]}"']

    if col["type"]:
        parts.append(col["type"])

    dflt = col["dflt_value"]
    notnull = col["notnull"]

    if _is_function_default(dflt):
        # A4: function default -> constant substitute.
        parts.append(_constant_default_for(col))
    elif dflt is not None:
        # Constant default from the schema -- use as-is.
        parts.append(f"DEFAULT {dflt}")
    elif notnull:
        # NOT NULL but no default: supply a typed constant so the ALTER
        # succeeds (SQLite requires a default for NOT NULL ADD COLUMN).
        parts.append(_constant_default_for(col))

    if notnull:
        parts.append("NOT NULL")

    return " ".join(parts)


def _add_missing_columns(conn: sqlite3.Connection, *, existing_only: bool = False) -> list[str]:
    """For each canonical table, ALTER-in any columns the live DB lacks.

    Returns a list of ALTER statements executed (empty if nothing changed).
    With ``existing_only`` (the pre-SCHEMA_SQL pass) a table that does not
    exist yet is simply skipped — the script creates it whole.
    """
    reference = _build_reference_schema()
    executed: list[str] = []

    for table, ref_cols in reference.items():
        # Check if the table exists in the live DB.
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if not exists:
            if existing_only:
                continue
            # Table does not exist -- step 1 should have created it.  If it
            # still doesn't exist something unusual is going on; skip rather
            # than crash.
            log.warning("Table %s missing after SCHEMA_SQL; skipping column reconcile", table)
            continue

        live_cols = {
            row[1]
            for row in conn.execute(f'PRAGMA table_info("{table}")')
        }

        for col in ref_cols:
            if col["name"] not in live_cols:
                stmt = _alter_column_sql(table, col)
                log.info("Reconcile: %s", stmt)
                conn.execute(stmt)
                executed.append(stmt)

    return executed


# ── Seeds / backfills ──────────────────────────────────────────────────


def _apply_data_backfills(conn: sqlite3.Connection) -> None:
    """Data backfills that run ONLY when the schema shape changed.

    Carried from ``migrations.py:_apply_seeds_and_backfills`` (HS-137-01)
    with imports routed to the real modules (not migrations.py).
    """
    from .decisions import backfill_decisions
    from .memory import rebuild_memory_index
    from .refinement_thoughts import RefinementThoughtRepository

    for row in conn.execute("SELECT id,attachment_revision,attachment_sha256 FROM refinement_thoughts WHERE attachment_sha256='' OR attachment_sha256 IS NULL").fetchall():
        if int(row[1]) != 0:
            raise RuntimeError(f"refinement thought {row[0]} has a nonzero attachment revision without a manifest")
        conn.execute("UPDATE refinement_thoughts SET attachment_sha256=? WHERE id=?",
                     (RefinementThoughtRepository.empty_attachment_hash(str(row[0])), str(row[0])))

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

    # ── chat-route-assignments (HS-151-02) ─────────────────────────────
    # Copy the assignment chain from recipe.chat to chat.turn. If no
    # recipe.chat chain exists, copy from ask.answer instead. Idempotent:
    # an existing chat.turn chain is never overwritten.
    _backfill_chat_route_assignments(conn)

    # ── chat-practice-assignments (HS-153-03/05) ─────────────────────
    # Copy the chat.turn chain to chat.guardrail and chat.compact so the
    # owner can independently assign a cheaper model.  Idempotent.
    _backfill_chat_practice_assignments(conn)


def _backfill_chat_route_assignments(conn: sqlite3.Connection) -> None:
    """Family ``chat-route-assignments`` (HS-151-02).

    Copies an existing global capability assignment chain to ``chat.turn``.
    Source precedence: ``recipe.chat`` first, then ``ask.answer``.
    Idempotent: a second run is a no-op; an existing ``chat.turn`` chain
    is never overwritten.
    """
    import uuid as _uuid

    TARGET_KEY = "capability:chat.turn"
    existing = conn.execute(
        "SELECT 1 FROM inference_assignment_heads WHERE assignment_key=?",
        (TARGET_KEY,),
    ).fetchone()
    if existing is not None:
        return  # chat.turn already assigned; never overwrite

    source_key: str | None = None
    for candidate in ("capability:recipe.chat", "capability:ask.answer"):
        row = conn.execute(
            "SELECT assignment_id, revision FROM inference_assignment_heads "
            "WHERE assignment_key=? AND cleared=0",
            (candidate,),
        ).fetchone()
        if row is not None:
            source_key = candidate
            break

    if source_key is None:
        return  # no source chain to copy

    src_assignment_id, src_revision = row[0], row[1]
    rev_row = conn.execute(
        "SELECT scope_kind, scope_id, subject_kind, selector_kind, "
        "capability_id, group_id, retry_policy_id, payload_json, sha256, "
        "created_at FROM inference_assignment_revisions "
        "WHERE assignment_id=? AND revision=?",
        (src_assignment_id, src_revision),
    ).fetchone()
    if rev_row is None:
        return  # orphan head; nothing to copy

    entries = conn.execute(
        "SELECT profile_id, profile_revision, profile_schema_version, ordinal "
        "FROM inference_assignments "
        "WHERE assignment_id=? AND assignment_revision=?",
        (src_assignment_id, src_revision),
    ).fetchall()
    if not entries:
        return  # empty chain

    new_id = "ia_" + _uuid.uuid4().hex
    new_revision = 1
    created_at = rev_row[9]

    conn.execute(
        """INSERT INTO inference_assignment_revisions
           (assignment_id, revision, assignment_key, scope_kind, scope_id,
            subject_kind, selector_kind, capability_id, group_id,
            retry_policy_id, payload_json, sha256, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            new_id, new_revision, TARGET_KEY,
            "global",  # scope_kind
            "",         # scope_id
            "",         # subject_kind
            "capability",  # selector_kind
            "chat.turn",   # capability_id
            "",         # group_id
            rev_row[6],  # retry_policy_id
            rev_row[7],  # payload_json
            rev_row[8],  # sha256
            created_at,
        ),
    )
    conn.execute(
        """INSERT INTO inference_assignment_heads
           (assignment_key, assignment_id, revision, cleared, updated_at)
           VALUES (?,?,?,0,?)""",
        (TARGET_KEY, new_id, new_revision, created_at),
    )
    for entry in entries:
        conn.execute(
            """INSERT INTO inference_assignments
               (id, assignment_id, assignment_revision, profile_id,
                profile_revision, profile_schema_version, ordinal)
               VALUES (?,?,?,?,?,?,?)""",
            (
                f"{new_id}:{new_revision}:{entry[3]}",
                new_id, new_revision,
                entry[0], entry[1], entry[2], entry[3],
            ),
        )
    log.info(
        "chat-route-assignments backfill: copied %s to chat.turn (%d entries)",
        source_key, len(entries),
    )


def _backfill_chat_practice_assignments(conn: sqlite3.Connection) -> None:
    """Family ``chat-practice-assignments`` (HS-153-03/05).

    Copies the existing ``chat.turn`` assignment chain to ``chat.guardrail``
    and ``chat.compact`` once.  Idempotent: existing chains are never
    overwritten.  Runs after ``_backfill_chat_route_assignments`` so the
    ``chat.turn`` chain is guaranteed to exist when a source is available.
    """
    import uuid as _uuid

    SOURCE_KEY = "capability:chat.turn"
    TARGETS = ("chat.guardrail", "chat.compact")

    source_row = conn.execute(
        "SELECT assignment_id, revision FROM inference_assignment_heads "
        "WHERE assignment_key=? AND cleared=0",
        (SOURCE_KEY,),
    ).fetchone()
    if source_row is None:
        return  # no chat.turn chain to copy

    src_assignment_id, src_revision = source_row[0], source_row[1]
    rev_row = conn.execute(
        "SELECT scope_kind, scope_id, subject_kind, selector_kind, "
        "capability_id, group_id, retry_policy_id, payload_json, sha256, "
        "created_at FROM inference_assignment_revisions "
        "WHERE assignment_id=? AND revision=?",
        (src_assignment_id, src_revision),
    ).fetchone()
    if rev_row is None:
        return

    entries = conn.execute(
        "SELECT profile_id, profile_revision, profile_schema_version, ordinal "
        "FROM inference_assignments "
        "WHERE assignment_id=? AND assignment_revision=?",
        (src_assignment_id, src_revision),
    ).fetchall()
    if not entries:
        return

    for target_cap in TARGETS:
        target_key = f"capability:{target_cap}"
        existing = conn.execute(
            "SELECT 1 FROM inference_assignment_heads WHERE assignment_key=?",
            (target_key,),
        ).fetchone()
        if existing is not None:
            continue  # never overwrite

        new_id = "ia_" + _uuid.uuid4().hex
        new_revision = 1
        created_at = rev_row[9]

        conn.execute(
            """INSERT INTO inference_assignment_revisions
               (assignment_id, revision, assignment_key, scope_kind, scope_id,
                subject_kind, selector_kind, capability_id, group_id,
                retry_policy_id, payload_json, sha256, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                new_id, new_revision, target_key,
                "global", "", "", "capability", target_cap, "",
                rev_row[6], rev_row[7], rev_row[8], created_at,
            ),
        )
        conn.execute(
            """INSERT INTO inference_assignment_heads
               (assignment_key, assignment_id, revision, cleared, updated_at)
               VALUES (?,?,?,0,?)""",
            (target_key, new_id, new_revision, created_at),
        )
        for entry in entries:
            conn.execute(
                """INSERT INTO inference_assignments
                   (id, assignment_id, assignment_revision, profile_id,
                    profile_revision, profile_schema_version, ordinal)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    f"{new_id}:{new_revision}:{entry[3]}",
                    new_id, new_revision,
                    entry[0], entry[1], entry[2], entry[3],
                ),
            )
        log.info(
            "chat-practice-assignments backfill: copied chat.turn to %s (%d entries)",
            target_cap, len(entries),
        )
