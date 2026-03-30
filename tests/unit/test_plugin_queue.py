from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from holdspeak.db import MeetingDatabase
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.queue import drain_plugin_run_queue, process_next_plugin_run_job


class _SuccessPlugin:
    id = "success"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {"ok": bool(context)}


class _FailPlugin:
    id = "failing"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        raise RuntimeError("boom")


def _db(tmp_path: Path) -> MeetingDatabase:
    return MeetingDatabase(tmp_path / "holdspeak.db")


def _save_meeting(db: MeetingDatabase, meeting_id: str) -> None:
    db.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=datetime(2026, 3, 29, 10, 0, 0),
            ended_at=datetime(2026, 3, 29, 11, 0, 0),
            mic_label="Me",
            remote_label="Remote",
        )
    )


def test_process_next_plugin_run_job_success(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _save_meeting(db, "m-1")

    db.enqueue_plugin_run_job(
        meeting_id="m-1",
        window_id="m-1:w-1",
        plugin_id="success",
        plugin_version="1.0.0",
        transcript_hash="h-1",
        idempotency_key="k-1",
        context={"active_intents": ["delivery"]},
    )

    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_SuccessPlugin())
    processed = process_next_plugin_run_job(host=host, db=db)
    assert processed is True

    assert db.list_plugin_run_jobs(status="all") == []
    runs = db.list_plugin_runs("m-1")
    assert len(runs) == 1
    assert runs[0].plugin_id == "success"
    assert runs[0].status == "success"
    assert runs[0].output == {"ok": True}


def test_process_next_plugin_run_job_retries_when_meeting_missing(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.enqueue_plugin_run_job(
        meeting_id="missing-meeting",
        window_id="missing-meeting:w-1",
        plugin_id="success",
        plugin_version="1.0.0",
        transcript_hash="h-missing",
        idempotency_key="k-missing",
        context={"active_intents": ["incident"]},
    )

    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_SuccessPlugin())
    processed = process_next_plugin_run_job(host=host, db=db)
    assert processed is True

    queued = db.list_plugin_run_jobs(status="queued")
    assert len(queued) == 1
    assert queued[0].attempts == 1
    assert queued[0].last_error is not None
    assert "not yet persisted" in queued[0].last_error.lower()


def test_process_next_plugin_run_job_terminal_failure_marks_failed(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _save_meeting(db, "m-2")

    db.enqueue_plugin_run_job(
        meeting_id="m-2",
        window_id="m-2:w-1",
        plugin_id="failing",
        plugin_version="1.0.0",
        transcript_hash="h-2",
        idempotency_key="k-2",
        context={"active_intents": ["incident"]},
    )

    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_FailPlugin())
    processed = process_next_plugin_run_job(host=host, db=db, retry_max_attempts=1)
    assert processed is True

    failed = db.list_plugin_run_jobs(status="failed")
    assert len(failed) == 1
    assert failed[0].attempts == 1
    assert failed[0].last_error is not None

    runs = db.list_plugin_runs("m-2")
    assert len(runs) == 1
    assert runs[0].plugin_id == "failing"
    assert runs[0].status == "error"
    assert runs[0].error is not None


def test_process_next_plugin_run_job_include_scheduled_enables_retry_now_mode(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _save_meeting(db, "m-3")

    db.enqueue_plugin_run_job(
        meeting_id="m-3",
        window_id="m-3:w-1",
        plugin_id="success",
        plugin_version="1.0.0",
        transcript_hash="h-3",
        idempotency_key="k-3",
        context={"active_intents": ["incident"]},
    )
    queued = db.list_plugin_run_jobs(status="queued")
    assert len(queued) == 1
    db.retry_plugin_run_job(
        queued[0].id,
        error="retry later",
        retry_at=datetime.now().replace(microsecond=0).replace(second=0) + timedelta(minutes=15),
    )

    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_SuccessPlugin())

    assert process_next_plugin_run_job(host=host, db=db) is False
    assert process_next_plugin_run_job(host=host, db=db, include_scheduled=True) is True

    runs = db.list_plugin_runs("m-3")
    assert len(runs) == 1
    assert runs[0].status == "success"


def test_drain_plugin_run_queue_include_scheduled_drains_future_jobs(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _save_meeting(db, "m-4")

    for idx in range(2):
        db.enqueue_plugin_run_job(
            meeting_id="m-4",
            window_id=f"m-4:w-{idx}",
            plugin_id="success",
            plugin_version="1.0.0",
            transcript_hash=f"h-4-{idx}",
            idempotency_key=f"k-4-{idx}",
            context={"active_intents": ["delivery"]},
        )

    queued = db.list_plugin_run_jobs(status="queued")
    assert len(queued) == 2
    for job in queued:
        db.retry_plugin_run_job(
            job.id,
            error="scheduled retry",
            retry_at=datetime.now().replace(microsecond=0).replace(second=0) + timedelta(minutes=30),
        )

    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_SuccessPlugin())

    assert drain_plugin_run_queue(host=host, db=db, include_scheduled=False) == 0
    assert drain_plugin_run_queue(host=host, db=db, include_scheduled=True) == 2
    assert db.list_plugin_run_jobs(status="all") == []
