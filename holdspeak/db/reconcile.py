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

    # The Phase-C queue primary-key change cannot be expressed as ALTER TABLE.
    # Rebuild before SCHEMA_SQL creates its job-keyed indexes and triggers.
    intel_queue_rebuilt = _rebuild_legacy_intel_queue_tables(conn)

    # ── 2. Create any missing tables / indexes / triggers ──────────────
    conn.executescript(SCHEMA_SQL)

    post_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    tables_created = post_tables - pre_tables
    shape_changed = bool(tables_created) or intel_queue_rebuilt
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


def _add_missing_columns(conn: sqlite3.Connection) -> list[str]:
    """For each canonical table, ALTER-in any columns the live DB lacks.

    Returns a list of ALTER statements executed (empty if nothing changed).
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
