"""Executable Phase-143 C1 inventory for the evolved deferred-intel queue.

Every production reader/writer named in the Phase-C counsel amendment has a
pinned assertion here.  The behavioral probes deliberately use the real
schema/repository rather than a duplicate queue implementation.
"""
from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db.reconcile import _rebuild_legacy_intel_queue_tables, reconcile_schema
from holdspeak.db.schema import SCHEMA_SQL


ROOT = Path(__file__).resolve().parents[2]


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _legacy_queue_connection() -> sqlite3.Connection:
    """Return a complete current schema with just the two old queue tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.execute("DROP TABLE intel_job_attempts")
    conn.execute("DROP TABLE intel_jobs")
    conn.executescript(
        """
        CREATE TABLE intel_jobs (
            meeting_id TEXT PRIMARY KEY REFERENCES meetings(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'queued', transcript_hash TEXT NOT NULL,
            requested_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
            displaced_work TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE intel_job_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
            attempt INTEGER NOT NULL, outcome TEXT NOT NULL, error TEXT,
            retry_at TEXT, created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO meetings (id,started_at) VALUES (?,?)",
        ("meeting-inventory", "2026-01-01T00:00:00"),
    )
    conn.execute(
        """INSERT INTO intel_jobs VALUES
           ('meeting-inventory','queued','legacy-hash','2026-01-01T00:00:00',
            '2026-01-01T00:00:00',1,NULL,'[\"bookmark-labels\"]')"""
    )
    conn.execute(
        """INSERT INTO intel_job_attempts
           (meeting_id,attempt,outcome,created_at)
           VALUES ('meeting-inventory',1,'scheduled_retry','2026-01-01T00:00:01')"""
    )
    conn.commit()
    return conn


def test_inventory_repository_claim_enqueue_retry_release_and_ledger_are_job_keyed() -> None:
    """Pin all IntelRepository mutation/read entry points and job-keyed SQL."""
    source = _source("holdspeak/db/intel.py")
    for symbol in (
        "enqueue_intel_job", "claim_next_intel_job", "requeue_claimed_intel_job",
        "retry_intel_job", "complete_intel_job", "fail_intel_job",
        "mark_intel_job_partial", "request_intel_retry", "skip_remaining_intel",
        "record_intel_job_attempt", "get_intel_job", "list_intel_jobs",
        "get_intel_queue_summary", "list_intel_job_attempts",
    ):
        assert f"def {symbol}" in source
    assert "WHERE owner.meeting_id=j.meeting_id" in source
    assert "owner.status IN ('claimed','running')" in source
    assert "WHERE job_id=? AND status='queued'" in source
    assert "intel_job_attempts (\n                    meeting_id,job_id,event_kind" in source
    assert "status='superseded'" in source


def test_inventory_worker_and_http_recovery_use_repository_contracts() -> None:
    """Pin worker scheduling plus all Meeting queue/recovery transport readers."""
    worker = _source("holdspeak/intel_queue.py")
    service = _source("holdspeak/services/meeting_intel_service.py")
    routes = _source("holdspeak/web/routes/meetings/intel.py")
    for symbol in ("process_next_intel_job", "drain_intel_queue", "IntelQueueWorker",
                   "claim_next_intel_job", "retry_intel_job", "fail_intel_job"):
        assert symbol in worker
    for symbol in ("list_jobs", "queue_summary", "process_jobs", "retry_job",
                   "get_recovery", "retry_recovery", "skip_recovery"):
        assert f"def {symbol}" in service
    for path in ("/api/intel/jobs", "/api/intel/summary", "/api/intel/process",
                 "/api/intel/retry/{meeting_id}", "intel-recovery"):
        assert path in routes


def test_inventory_projection_dtos_session_import_and_persistence_writers_are_pinned() -> None:
    """Pin Desk/DTO ordinary readers and session, recovery, and import writers."""
    models = _source("holdspeak/db/models/__init__.py")
    projection = _source("holdspeak/db/projections.py")
    persistence = _source("holdspeak/meeting_session/persistence.py")
    admission = _source("holdspeak/meeting_session/intel_admission.py")
    imported = _source("holdspeak/meeting_import.py")
    for field in ("job_id", "origin_job_id", "work_descriptor_sha256", "claim_id",
                  "parent_operation_id", "bundle_id", "bundle_sha256", "lifecycle_posture"):
        assert field in models
    assert "newest active/claimable job" in projection
    assert "enqueue_intel_job" in persistence
    assert "enqueue_intel_job" in admission
    assert "enqueue_intel_job" in imported


def test_inventory_plugin_job_family_is_separate_and_non_colliding() -> None:
    """Pin the separately-owned plugin_run_jobs service, MCP, HTTP, and worker."""
    schema = _source("holdspeak/db/schema.py")
    plugins = _source("holdspeak/db/plugins.py")
    service = _source("holdspeak/services/plugin_job_service.py")
    mcp = _source("holdspeak/mcp/families/plugin_job.py")
    routes = _source("holdspeak/web/routes/activity/plugin_jobs.py")
    projection = _source("holdspeak/db/projections.py")
    assert "CREATE TABLE IF NOT EXISTS plugin_run_jobs" in schema
    assert "CREATE TABLE IF NOT EXISTS intel_jobs" in schema
    assert "enqueue_plugin_run_job" in plugins and "claim_next_plugin_run_job" in plugins
    assert "class PluginJobService" in service
    assert "plugin_job.list" in mcp and "plugin_job.retry" in mcp
    assert "/api/plugin-jobs" in routes
    assert '("intel_jobs", "intel_job"), ("plugin_run_jobs", "plugin_job")' in projection


def test_legacy_rows_migrate_to_deterministic_jobs_with_attempt_history_and_replay() -> None:
    """Old Meeting-keyed data survives transactional migration and restart replay."""
    conn = _legacy_queue_connection()
    assert reconcile_schema(conn) is True
    job = conn.execute("SELECT * FROM intel_jobs").fetchone()
    event = conn.execute("SELECT * FROM intel_job_attempts").fetchone()
    assert job is not None and str(job["job_id"]).startswith("ij_")
    assert job["meeting_id"] == "meeting-inventory"
    assert job["transcript_hash"] == "legacy-hash"
    assert str(job["work_descriptor_sha256"]).startswith("sha256:")
    assert event is not None and event["job_id"] == job["job_id"]
    assert event["outcome"] == "scheduled_retry" and event["event_kind"] == "legacy_attempt"
    job_id = str(job["job_id"])
    assert reconcile_schema(conn) is False
    assert conn.execute("SELECT job_id FROM intel_jobs").fetchone()[0] == job_id


def test_legacy_migration_rollback_preserves_the_old_shape_and_rows() -> None:
    """A mid-copy exception rolls the rename/rebuild back to the old table exactly."""
    raw = _legacy_queue_connection()

    class FailingConnection:
        def __init__(self, inner: sqlite3.Connection) -> None:
            self.inner = inner
            self.failed = False

        @property
        def in_transaction(self) -> bool:
            return self.inner.in_transaction

        def execute(self, sql: str, *args):  # type: ignore[no-untyped-def]
            if "INSERT INTO intel_jobs (" in sql and not self.failed:
                self.failed = True
                raise sqlite3.OperationalError("injected copy failure")
            return self.inner.execute(sql, *args)

    with pytest.raises(sqlite3.OperationalError, match="injected copy failure"):
        _rebuild_legacy_intel_queue_tables(FailingConnection(raw))
    columns = {row[1] for row in raw.execute("PRAGMA table_info('intel_jobs')")}
    assert "job_id" not in columns and "meeting_id" in columns
    assert raw.execute("SELECT transcript_hash FROM intel_jobs").fetchone()[0] == "legacy-hash"


def test_new_shape_immutability_unique_owner_and_ordinary_reader_selection(tmp_path) -> None:
    """A Meeting retains history while ordinary readers expose one live owner."""
    from holdspeak.db import Database
    from holdspeak.meeting_session import MeetingState

    db = Database(tmp_path / "inventory.db")
    meeting = MeetingState(id="meeting-current", started_at=datetime.now())
    db.meetings.save_meeting(meeting)
    first = db.intel.enqueue_intel_job(meeting.id, transcript_hash="first")
    claimed = db.intel.claim_next_intel_job()
    assert claimed is not None and claimed.job_id == first
    assert db.intel.requeue_claimed_intel_job(
        meeting.id, transcript_hash="second", reason="changed", displaced_work=(),
    )
    current = db.intel.get_intel_job(meeting.id)
    assert current is not None and current.job_id != first and current.status == "queued"
    assert [job.job_id for job in db.intel.list_intel_jobs()] == [current.job_id]
    assert [job.job_id for job in db.intel.list_intel_jobs(status="superseded")] == [first]
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE intel_jobs SET transcript_hash='retargeted' WHERE job_id=?", (current.job_id,)
            )
        assert conn.execute("SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (meeting.id,)).fetchone()[0] == 2


def _bound_claim_db(tmp_path, filename: str = "bound-claim.db"):  # type: ignore[no-untyped-def]
    from holdspeak.db import Database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    db = Database(tmp_path / filename)
    meeting = MeetingState(
        id="meeting-bound", started_at=datetime.now(),
        segments=[TranscriptSegment("durable transcript", "Me", 0.0, 1.0)],
    )
    db.meetings.save_meeting(meeting)
    db.intel.enqueue_intel_job(meeting.id, transcript_hash=meeting.transcript_hash())
    return db, meeting


def _binding(_conn, _job, ids):  # type: ignore[no-untyped-def]
    return {
        "parent_operation_id": ids["parent_command_id"],
        "bundle_id": ids["bundle_command_id"],
        "bundle_sha256": "sha256:bound-test",
    }


def test_bound_claim_rolls_back_binding_and_claim_event_on_refusal(tmp_path) -> None:
    """A binder refusal leaves no claim, parent reference, bundle, or ledger event."""
    db, meeting = _bound_claim_db(tmp_path)

    def refuse(_conn, _job, _ids):  # type: ignore[no-untyped-def]
        raise RuntimeError("route policy refused")

    with pytest.raises(RuntimeError, match="route policy refused"):
        db.intel.claim_next_intel_job_bound(refuse)
    job = db.intel.get_intel_job(meeting.id)
    assert job is not None and job.status == "queued" and job.claim_id is None
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM intel_job_attempts").fetchone()[0] == 0
        row = conn.execute("SELECT parent_operation_id,bundle_id FROM intel_jobs").fetchone()
        assert tuple(row) == (None, None)


def test_bound_claim_uses_deterministic_binding_and_competing_connections_one_owner(tmp_path) -> None:
    """Two Database services racing on one file grant exactly one bound owner."""
    db, _meeting = _bound_claim_db(tmp_path)
    from holdspeak.db import Database

    other = Database(db.db_path)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda repo: repo.intel.claim_next_intel_job_bound(_binding), (db, other)))
    claims = [item for item in results if item is not None]
    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_id and claim.parent_operation_id and claim.bundle_id
    assert claim.parent_operation_id.startswith("parent_")
    assert claim.bundle_id.startswith("bundle_")
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM intel_job_attempts WHERE event_kind='claim'").fetchone()[0] == 1


def test_bound_claim_never_overlaps_legacy_running_owner_or_recovery_replay(tmp_path) -> None:
    """The legacy claim gate and bound replay both preserve one descriptor owner."""
    db, _meeting = _bound_claim_db(tmp_path)
    legacy = db.intel.claim_next_intel_job()
    assert legacy is not None and legacy.status == "running"
    assert db.intel.claim_next_intel_job_bound(_binding) is None

    second, _other = _bound_claim_db(tmp_path, "bound-claim-second.db")
    first_bound = second.intel.claim_next_intel_job_bound(_binding)
    assert first_bound is not None and first_bound.status == "claimed"
    assert second.intel.claim_next_intel_job_bound(_binding) is None
    with second._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM intel_job_attempts WHERE event_kind='claim'").fetchone()[0] == 1


def test_bound_claim_transcript_fence_supersedes_and_links_fresh_job(tmp_path) -> None:
    """Claim-time durable hash drift terminalizes the old descriptor without egress."""
    db, meeting = _bound_claim_db(tmp_path)
    with db._connection() as conn:
        conn.execute("UPDATE segments SET text='changed durable transcript' WHERE meeting_id=?", (meeting.id,))
    assert db.intel.claim_next_intel_job_bound(_binding) is None
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT status,origin_job_id,parent_operation_id,bundle_id FROM intel_jobs ORDER BY requested_at"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["status"] == "superseded"
        assert rows[0]["parent_operation_id"] is None and rows[0]["bundle_id"] is None
        assert rows[1]["status"] == "queued" and rows[1]["origin_job_id"]
