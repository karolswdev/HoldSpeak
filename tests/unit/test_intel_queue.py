"""Unit tests for deferred-intel queue worker lifecycle."""
from __future__ import annotations

import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

import holdspeak.intel_queue as intel_queue_module
from holdspeak.db.reconcile import _rebuild_legacy_intel_queue_tables, reconcile_schema
from holdspeak.db.schema import SCHEMA_SQL


def test_worker_start_and_stop(monkeypatch) -> None:
    calls = []

    def fake_drain(
        model_path=None,
        *,
        provider="local",
        # HS-200-42: the worker now forwards the finished-meeting callback.
        on_meeting_ready=None,
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url=None,
        cloud_reasoning_effort=None,
        cloud_store=False,
        retry_base_seconds=30,
        retry_max_seconds=900,
        retry_max_attempts=6,
        include_scheduled=False,
        max_jobs=None,
    ):
        _ = (
            provider,
            on_meeting_ready,
            cloud_model,
            cloud_api_key_env,
            cloud_base_url,
            cloud_reasoning_effort,
            cloud_store,
            retry_base_seconds,
            retry_max_seconds,
            retry_max_attempts,
            include_scheduled,
        )
        _ = max_jobs
        calls.append(model_path)
        return 0

    monkeypatch.setattr(intel_queue_module, "drain_intel_queue", fake_drain)
    monkeypatch.setattr(
        intel_queue_module,
        "get_database",
        # HS-200-42: the double now has the shape the REAL `Database` has —
        # the summary hangs off `.intel`. The old flat double asserted a
        # surface that never existed, so it hid the AttributeError the worker
        # raised on every failure-alert check.
        lambda: SimpleNamespace(
            intel=SimpleNamespace(
                get_intel_queue_summary=lambda: SimpleNamespace(
                    total_jobs=0,
                    queued_jobs=0,
                    running_jobs=0,
                    failed_jobs=0,
                    queued_due_jobs=0,
                    scheduled_retry_jobs=0,
                    next_retry_at=None,
                )
            )
        ),
    )

    worker = intel_queue_module.start_intel_queue_worker(model_path="model.gguf", poll_seconds=1.0)
    time.sleep(0.02)
    worker.stop(timeout=1.0)

    assert calls
    assert worker.model_path == "model.gguf"
    assert worker.poll_seconds == 5.0
    assert worker.is_alive() is False


def test_compute_retry_delay_seconds_uses_exponential_backoff() -> None:
    assert intel_queue_module._compute_retry_delay_seconds(1) == 30
    assert intel_queue_module._compute_retry_delay_seconds(2) == 60
    assert intel_queue_module._compute_retry_delay_seconds(3) == 120
    assert intel_queue_module._compute_retry_delay_seconds(20) == 900


def test_retry_or_fail_job_requeues_bound_owner_before_max_attempts() -> None:
    calls: list[tuple[object, str, object, int]] = []

    class _FakeDb:
        intel = property(lambda self: self)

        def settle_bound_execution(self, job, *, error, retry_at=None, max_attempts):
            calls.append((job, error, retry_at, max_attempts))
            return True

    job = SimpleNamespace(
        meeting_id="meeting-1",
        attempts=2,
        parent_operation_id="parent-1",
        executor_lease_token="lease-1",
        executor_lease_epoch=1,
    )
    assert intel_queue_module._retry_or_fail_job(
        _FakeDb(), job, "Deferred intel failed: timeout"
    ) is True

    assert len(calls) == 1
    settled, error, retry_at, max_attempts = calls[0]
    assert settled is job and error == "Deferred intel failed: timeout"
    assert retry_at is not None
    assert max_attempts == intel_queue_module.RETRY_MAX_ATTEMPTS


def test_retry_or_fail_job_terminalizes_bound_owner_after_max_attempts() -> None:
    calls: list[tuple[object, str, object, int]] = []

    class _FakeDb:
        intel = property(lambda self: self)

        def settle_bound_execution(self, job, *, error, retry_at=None, max_attempts):
            calls.append((job, error, retry_at, max_attempts))
            return True

    job = SimpleNamespace(
        meeting_id="meeting-1",
        attempts=intel_queue_module.RETRY_MAX_ATTEMPTS,
        parent_operation_id="parent-1",
        executor_lease_token="lease-1",
        executor_lease_epoch=1,
    )
    assert intel_queue_module._retry_or_fail_job(
        _FakeDb(), job, "Deferred intel failed: timeout"
    ) is True

    assert len(calls) == 1
    _settled, error, retry_at, max_attempts = calls[0]
    assert error == "Deferred intel failed: timeout"
    assert retry_at is None
    assert max_attempts == intel_queue_module.RETRY_MAX_ATTEMPTS


def test_compute_failure_rate_percent() -> None:
    assert intel_queue_module._compute_failure_rate_percent(total_jobs=0, failed_jobs=0) == 0.0
    assert intel_queue_module._compute_failure_rate_percent(total_jobs=10, failed_jobs=3) == 30.0


def test_failure_alert_hysteresis_triggers_once_per_incident(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = None
    worker.failure_alert_webhook_header_value = None
    worker._failure_alert_above_since = None
    worker._failure_alert_sent = False

    webhook_calls = []
    monkeypatch.setattr(worker, "_post_failure_alert_webhook", lambda **kwargs: webhook_calls.append(kwargs))

    summary_high = SimpleNamespace(
        total_jobs=10,
        queued_jobs=4,
        running_jobs=0,
        failed_jobs=6,
        queued_due_jobs=2,
        scheduled_retry_jobs=2,
        next_retry_at=None,
    )
    summary_low = SimpleNamespace(
        total_jobs=10,
        queued_jobs=6,
        running_jobs=0,
        failed_jobs=1,
        queued_due_jobs=4,
        scheduled_retry_jobs=1,
        next_retry_at=None,
    )

    t0 = datetime(2026, 1, 1, 12, 0, 0)
    worker._update_failure_alert_state(summary_high, now=t0)
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=4))
    assert webhook_calls == []

    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=5))
    assert len(webhook_calls) == 1
    assert webhook_calls[0]["event"] == "triggered"

    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=8))
    assert len(webhook_calls) == 1

    worker._update_failure_alert_state(summary_low, now=t0 + timedelta(minutes=9))
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=10))
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=15))
    assert len(webhook_calls) == 3
    assert [call["event"] for call in webhook_calls] == ["triggered", "resolved", "triggered"]


def test_post_failure_alert_webhook_posts_json_payload(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = "X-HoldSpeak-Token"
    worker.failure_alert_webhook_header_value = "secret-token"

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return b"ok"

    def _fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = request.data.decode("utf-8")
        captured["header"] = request.headers.get("X-holdspeak-token")
        return _Resp()

    monkeypatch.setattr(intel_queue_module.urlrequest, "urlopen", _fake_urlopen)

    summary = SimpleNamespace(
        total_jobs=3,
        queued_jobs=2,
        running_jobs=0,
        failed_jobs=1,
        queued_due_jobs=1,
        scheduled_retry_jobs=1,
        next_retry_at=datetime(2026, 1, 1, 12, 5, 0),
    )
    now = datetime(2026, 1, 1, 12, 0, 0)
    worker._post_failure_alert_webhook(summary=summary, failure_rate_percent=33.3, now=now)

    assert captured["url"] == "https://example.test/hook"
    assert captured["timeout"] == intel_queue_module.RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS
    assert captured["header"] == "secret-token"
    payload = json.loads(captured["body"])
    assert payload["type"] == "intel_queue_failure_alert"
    assert payload["event"] == "triggered"
    assert "triggered_at" in payload
    assert payload["queue"]["failed_jobs"] == 1


def test_post_failure_alert_webhook_resolved_payload(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = None
    worker.failure_alert_webhook_header_value = None

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return b"ok"

    def _fake_urlopen(request, timeout):
        _ = timeout
        captured["body"] = request.data.decode("utf-8")
        return _Resp()

    monkeypatch.setattr(intel_queue_module.urlrequest, "urlopen", _fake_urlopen)

    summary = SimpleNamespace(
        total_jobs=5,
        queued_jobs=4,
        running_jobs=0,
        failed_jobs=0,
        queued_due_jobs=2,
        scheduled_retry_jobs=1,
        next_retry_at=None,
    )
    above_since = datetime(2026, 1, 1, 12, 0, 0)
    now = datetime(2026, 1, 1, 12, 12, 0)
    worker._post_failure_alert_webhook(
        summary=summary,
        failure_rate_percent=0.0,
        now=now,
        event="resolved",
        above_since=above_since,
    )

    payload = json.loads(captured["body"])
    assert payload["type"] == "intel_queue_failure_alert"
    assert payload["event"] == "resolved"
    assert payload["resolved_at"] == now.isoformat()
    assert payload["above_since"] == above_since.isoformat()


def test_transcript_refresh_releases_its_own_claim_without_enqueue_reset(tmp_path) -> None:
    """A worker-owned refresh remains available after running-row protection."""
    from holdspeak.db import Database
    from holdspeak.meeting_session import MeetingState

    db = Database(tmp_path / "intel-queue.db")
    meeting = MeetingState(id="meeting-1", started_at=datetime.now())
    db.meetings.save_meeting(meeting)
    db.intel.enqueue_intel_job(meeting.id, transcript_hash="before")
    claimed = db.intel.claim_next_intel_job()
    assert claimed is not None and claimed.attempts == 1

    assert db.intel.requeue_claimed_intel_job(
        meeting.id,
        transcript_hash="after",
        reason="Transcript changed; refreshing queued intelligence job.",
        displaced_work=("final-analysis",),
    )
    refreshed = db.intel.get_intel_job(meeting.id)
    assert refreshed is not None
    assert refreshed.status == "queued"
    assert refreshed.transcript_hash == "after"
    assert refreshed.attempts == 1
    reclaimed = db.intel.claim_next_intel_job()
    assert reclaimed is not None and reclaimed.attempts == 2


# ── from test_phase143_intel_queue_inventory.py: Executable Phase-143 C1 inventory for the evolved deferred-intel queue. ──
#
# Every production reader/writer named in the Phase-C counsel amendment has a
# pinned assertion here.  The behavioral probes deliberately use the real
# schema/repository rather than a duplicate queue implementation.


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


def test_bound_claim_backoffs_unclassified_refusal_without_claim_or_spin(tmp_path) -> None:
    """An infrastructure refusal leaves no owner and durably moves out of due work."""
    db, meeting = _bound_claim_db(tmp_path)

    def refuse(_conn, _job, _ids):  # type: ignore[no-untyped-def]
        raise RuntimeError("route policy refused")

    with pytest.raises(RuntimeError, match="route policy refused"):
        db.intel.claim_next_intel_job_bound(refuse)
    job = db.intel.get_intel_job(meeting.id)
    assert job is not None and job.status == "queued" and job.claim_id is None and job.attempts == 1
    with db._connection() as conn:
        event = conn.execute("SELECT outcome,retry_at FROM intel_job_attempts").fetchone()
        row = conn.execute("SELECT parent_operation_id,bundle_id,requested_at FROM intel_jobs").fetchone()
        assert event is not None and event["outcome"] == "scheduled_retry" and event["retry_at"]
        assert tuple(row[:2]) == (None, None)


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


def test_staging_fence_supersedes_exact_bound_owner_and_links_fresh_job(tmp_path) -> None:
    """A post-claim transcript change cannot retarget stored bound authority."""
    db, meeting = _bound_claim_db(tmp_path, "staging-fence.db")
    claimed = db.intel.claim_next_intel_job_bound(_binding)
    assert claimed is not None and claimed.status == "claimed"
    with db._connection() as conn:
        conn.execute("UPDATE segments SET text='changed after claim' WHERE meeting_id=?", (meeting.id,))
    fresh = db.intel.supersede_bound_intel_job(
        claimed,
        reason="Transcript changed before bound material staging.",
        event_kind="staging_fence_superseded",
    )
    assert fresh is not None and fresh != claimed.job_id
    with db._connection() as conn:
        old = conn.execute("SELECT status,parent_operation_id,bundle_id FROM intel_jobs WHERE job_id=?", (claimed.job_id,)).fetchone()
        new = conn.execute("SELECT status,origin_job_id FROM intel_jobs WHERE job_id=?", (fresh,)).fetchone()
        event = conn.execute("SELECT outcome FROM intel_job_attempts WHERE job_id=? AND event_kind='staging_fence_superseded'", (claimed.job_id,)).fetchone()
    assert old is not None and old["status"] == "superseded"
    assert old["parent_operation_id"] == claimed.parent_operation_id and old["bundle_id"] == claimed.bundle_id
    assert new is not None and new["status"] == "reserved" and new["origin_job_id"] == claimed.job_id
    assert event is not None and event["outcome"] == "superseded"


def test_retry_terminalizes_old_owner_and_records_linked_fresh_job(tmp_path) -> None:
    """Queue retry is a new owner decision, never controller retry-in-place."""
    from holdspeak.intel_queue import _retry_or_fail_job

    db, meeting = _bound_claim_db(tmp_path, "retry-linkage.db")
    claimed = db.intel.claim_next_intel_job_bound(_binding)
    assert claimed is not None and claimed.status == "claimed"
    _retry_or_fail_job(db, claimed, "test failure", max_attempts=6, base_delay_seconds=1)
    with db._connection() as conn:
        old = conn.execute("SELECT status FROM intel_jobs WHERE job_id=?", (claimed.job_id,)).fetchone()
        new = conn.execute("SELECT job_id,origin_job_id,status FROM intel_jobs WHERE origin_job_id=?", (claimed.job_id,)).fetchone()
        link = conn.execute("SELECT outcome FROM intel_job_attempts WHERE job_id=? AND event_kind='retry_linkage'", (new["job_id"],)).fetchone()
    assert old is not None and old["status"] == "failed"
    assert new is not None and new["origin_job_id"] == claimed.job_id and new["status"] == "reserved"
    assert link is not None and link["outcome"] == "queued"


def test_real_service_binder_cross_binds_one_claim_parent_and_bundle(tmp_path) -> None:
    """The queue's real SERVICE binder commits its stored route set with claim."""
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import (
        InferenceAssignmentService,
    )
    from holdspeak.services.meeting_deferred_queue_binding import (
        MeetingDeferredQueueBinder,
    )
    from tests.unit.test_phase143_inference_assignments import (
        OWNER,
        _profile,
        _result_claim,
    )

    db, meeting = _bound_claim_db(tmp_path, "real-bound-claim.db")
    capabilities = (
        "meeting.deferred_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
        *(
            capability_id
            for capability_id in process_inference_capability_registry().capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    _profile(
        db,
        "queue-service-model",
        claims=(
            "language",
            "structured_output",
            "meeting_plugin",
            *(_result_claim(item) for item in capabilities),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(capabilities, 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"queue-service-assignment-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability},
                "entries": [{"profile_id": "queue-service-model", "profile_revision": 1}],
            },
        )
    broker = _configure(db)

    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))

    assert claimed is not None and claimed.status == "claimed"
    assert claimed.parent_operation_id and claimed.bundle_id and claimed.bundle_sha256
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT * FROM kernel_parent_runs WHERE operation_id=?", (claimed.parent_operation_id,)
        ).fetchone()
        bundle = conn.execute(
            "SELECT * FROM inference_parent_route_bundles WHERE id=?", (claimed.bundle_id,)
        ).fetchone()
        members = conn.execute(
            "SELECT * FROM inference_parent_route_bundle_members WHERE bundle_id=?", (claimed.bundle_id,)
        ).fetchall()
        event = conn.execute(
            "SELECT * FROM intel_job_attempts WHERE job_id=? AND event_kind='claim'",
            (claimed.job_id,),
        ).fetchone()
    assert parent is not None and str(parent["kind"]) == "meeting.deferred-intel-job"
    assert bundle is not None and str(bundle["parent_operation_id"]) == claimed.parent_operation_id
    assert {
        str(member["capability_id"])
        for member in members
    } == {
        "meeting.deferred_analysis",
        *(str(member["capability_id"]) for member in claimed.frozen_plugin_members),
    }
    assert event is not None and str(event["bundle_id"]) == claimed.bundle_id
    assert db.meetings.get_meeting(meeting.id).intel_status == "running"


def test_real_service_binder_refusal_terminalizes_job_and_records_ledger(tmp_path) -> None:
    """Missing exact SERVICE assignment visibly terminalizes with zero child."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.meeting_deferred_queue_binding import (
        MeetingDeferredQueueBinder,
    )

    db, meeting = _bound_claim_db(tmp_path, "real-bound-refusal.db")
    broker = _configure(db)

    with pytest.raises(Exception):
        db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))

    job = db.intel.get_intel_job(meeting.id)
    assert job is not None and job.status == "failed" and job.claim_id is None
    assert db.meetings.get_meeting(meeting.id).intel_status == "error"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        event = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE job_id=? AND event_kind='refusal'",
            (job.job_id,),
        ).fetchone()
    assert event is not None and event["outcome"] == "refused"


def test_real_binder_policy_flip_between_prepare_and_claim_refuses_shell(tmp_path) -> None:
    """A changed route policy cannot repurpose the pre-admitted parent budget."""
    from dataclasses import replace

    from holdspeak.inference_capabilities import (
        InferenceCapabilityRegistry,
        process_inference_capability_registry,
    )
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.errors import ConflictError
    from holdspeak.services.inference_assignment_service import (
        InferenceAssignmentService,
    )
    from holdspeak.services.inference_parent_route_bundle_service import (
        InferenceParentRouteBundleService,
    )
    from holdspeak.services.inference_route_plan_service import (
        InferenceRoutePlanService,
    )
    from holdspeak.services.meeting_deferred_queue_binding import (
        MeetingDeferredQueueBinder,
    )
    from tests.unit.test_phase143_inference_assignments import (
        OWNER,
        _profile,
        _result_claim,
    )

    db, meeting = _bound_claim_db(tmp_path, "bound-policy-race.db")
    current = process_inference_capability_registry()
    original = current.require("meeting.deferred_analysis")
    default = current.retry_policy(original.default_retry_policy_id)
    alternate = replace(
        default,
        id="retry.meeting-deferred.race",
        permitted_capability_ids=("meeting.deferred_analysis",),
        total_physical_attempts=int(default.total_physical_attempts) + 1,
        sha256="",
    )
    capability = replace(
        original,
        permitted_retry_policy_ids=(original.default_retry_policy_id, alternate.id),
        schema_sha256="",
    )
    registry = InferenceCapabilityRegistry.compose(
        capabilities=tuple(
            capability if item.id == capability.id else item
            for item in current._capabilities.values()
        ),
        retry_policies=(*current._retry_policies.values(), alternate),
    )
    capabilities = (
        "meeting.deferred_analysis",
        *(
            capability_id
            for capability_id in current.capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    _profile(
        db,
        "policy-race-model",
        claims=(
            "language",
            "structured_output",
            "meeting_plugin",
            *(_result_claim(item) for item in capabilities),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db, registry=registry)
    body = {
        "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "entries": [{"profile_id": "policy-race-model", "profile_revision": 1}],
    }
    assignments.set_assignment(
        OWNER,
        {"command_id": "policy-race-default", "expected_revision": 0, **body},
    )
    for ordinal, plugin_capability in enumerate(capabilities[1:], 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"policy-race-plugin-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": plugin_capability},
                "entries": [{"profile_id": "policy-race-model", "profile_revision": 1}],
            },
        )
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(broker, broker.inference_adoption_service)
    bundles._plans = InferenceRoutePlanService(db, registry=registry)

    class PolicyFlipBinder(MeetingDeferredQueueBinder):
        def prepare(self, job, command_ids):  # type: ignore[no-untyped-def]
            super().prepare(job, command_ids)
            assignments.set_assignment(
                OWNER,
                {
                    "command_id": "policy-race-flipped",
                    "expected_revision": 1,
                    **body,
                    "retry_policy_id": alternate.id,
                },
            )

    with pytest.raises(ConflictError) as refused:
        db.intel.claim_next_intel_job_bound(PolicyFlipBinder(broker, bundles=bundles))
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"

    job = db.intel.get_intel_job(meeting.id)
    assert job is not None and job.status == "failed" and job.claim_id is None
    assert db.meetings.get_meeting(meeting.id).intel_status == "error"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundle_members").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='claim'",
            (job.job_id,),
        ).fetchone()[0] == 0
        refusal_event = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE job_id=? AND event_kind='refusal'",
            (job.job_id,),
        ).fetchone()
        shell = conn.execute(
            """SELECT o.operation_id,o.state,r.outcome FROM kernel_operations o
               LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id
               WHERE o.principal_identity='meeting-intel-queue'
                 AND o.name='meeting.deferred-intel-job'"""
        ).fetchone()
    assert refusal_event is not None and refusal_event["outcome"] == "refused"
    assert shell is not None and shell["state"] == "refused" and shell["outcome"] == "refused"
