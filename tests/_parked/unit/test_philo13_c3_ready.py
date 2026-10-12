"""PHILO-13 C3: durable, newly-ready meeting attention."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak import db as db_module
from holdspeak.intel import IntelResult
from holdspeak.meeting_session import (
    IntelSnapshot,
    MeetingSession,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.crud import build_crud_router


def _meeting(meeting_id: str, *, title: str, status: str = "ready") -> MeetingState:
    return MeetingState(
        id=meeting_id,
        title=title,
        started_at=datetime(2026, 10, 2, 12, 0),
        ended_at=datetime(2026, 10, 2, 12, 30),
        intel_status=status,
        intel_completed_at=datetime(2026, 10, 2, 12, 31),
        intel=IntelSnapshot(timestamp=1.0, summary=f"Stored summary for {meeting_id}"),
    )


def test_old_summary_is_not_unseen_but_new_ready_is_durable_and_readable(tmp_path: Path) -> None:
    db = Database(tmp_path / "c3-ready.db")
    try:
        db.meetings.save_meeting(_meeting("old", title="Old summary"))
        db.meetings.save_meeting(_meeting("old-2", title="Another old summary"))
        db.meetings.save_meeting(_meeting("new", title="New summary"))
        first_ready = db.meetings.mark_ready_unseen("new")

        assert [row["id"] for row in db.meetings.list_unread_ready()] == ["new"]

        db.meetings.mark_ready_read("new")
        assert first_ready is not None
        db.meetings.mark_ready_unseen("new", ready_at=first_ready["ready_at"])
        assert db.meetings.list_unread_ready() == []
        db.meetings.mark_ready_unseen("new", ready_at="new-completion-revision")
        assert [row["id"] for row in db.meetings.list_unread_ready()] == ["new"]
        db.meetings.mark_ready_read("new")
        reopened = Database(tmp_path / "c3-ready.db")
        try:
            assert reopened.meetings.list_unread_ready() == []
        finally:
            reopened.close()
    finally:
        db.close()


def test_ready_read_route_is_idempotent_and_survives_reload(tmp_path: Path) -> None:
    db = Database(tmp_path / "c3-ready-route.db")
    db.meetings.save_meeting(_meeting("m-route", title="Route meeting"))
    db.meetings.save_meeting(_meeting("old-open", title="Old summary"))
    db.meetings.mark_ready_unseen("m-route")
    app = FastAPI()
    app.include_router(
        build_crud_router(
            WebContext(get_state=lambda: {}, meeting_service=MeetingService(db))
        )
    )
    with TestClient(app) as client:
        listed = client.get("/api/meetings/ready")
        assert listed.status_code == 200, listed.text
        assert [row["id"] for row in listed.json()["meetings"]] == ["m-route"]
        first = client.post("/api/meetings/m-route/ready/read")
        second = client.post("/api/meetings/m-route/ready/read")
        old = client.post("/api/meetings/old-open/ready/read")
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert old.status_code == 200, old.text
        assert old.json()["ready_at"] is None
        assert first.json()["read"] is True
        assert client.get("/api/meetings/ready").json()["meetings"] == []
    db.close()


def test_real_bound_queue_completion_creates_unread_ready_marker(tmp_path: Path, monkeypatch) -> None:
    """The production queue completion, not a test-only helper, creates READY."""
    from tests.unit.test_meeting_deferred_admission import _queue_rig, _queued_meeting
    from holdspeak.intel_queue import _process_bound_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-produced-ready")
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    frames: list[str] = []

    assert _process_bound_intel_job(
        db,
        claimed,
        broker,
        on_meeting_ready=frames.append,
        retry_base_seconds=1,
        retry_max_seconds=1,
        retry_max_attempts=4,
    ) is True

    assert frames == [state.id]
    # Read the durable producer seam directly so this fence fails clearly on
    # the pre-C3 source even before repository convenience methods exist.
    with db._connection() as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'meeting_ready_reads'"
        ).fetchone()
        assert table is not None, "real completion must have a durable readiness table"
        marker = conn.execute(
            "SELECT meeting_id, ready_at, read_at FROM meeting_ready_reads WHERE meeting_id = ?",
            (state.id,),
        ).fetchone()
    assert marker is not None
    assert marker["meeting_id"] == state.id
    assert marker["ready_at"]
    assert marker["read_at"] is None
    db.close()


def test_meeting_session_save_marks_only_meaningful_aftercare_before_callback(
    tmp_path: Path, monkeypatch
) -> None:
    """Ended empty saves stay quiet; meaningful aftercare is durable first."""
    db = Database(tmp_path / "c3-session-ready.db")
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    events: list[tuple[str, object]] = []

    def on_broadcast(kind: str, payload: object) -> None:
        if kind == "aftercare_ready":
            marker = db.meetings.list_unread_ready()
            assert marker and marker[0]["id"] == "meaningful"
            events.append((kind, payload))

    empty = MeetingSession(transcriber=None, on_broadcast=on_broadcast)
    empty._state = MeetingState(
        id="empty",
        title="Empty meeting",
        started_at=datetime(2026, 10, 2, 9, 0),
        ended_at=datetime(2026, 10, 2, 9, 30),
    )
    assert empty.save(tmp_path / "empty-json").database_saved is True
    assert events == []
    assert db.meetings.list_unread_ready() == []

    meaningful = MeetingSession(transcriber=None, on_broadcast=on_broadcast)
    meaningful._state = MeetingState(
        id="meaningful",
        title="Meaningful meeting",
        started_at=datetime(2026, 10, 2, 10, 0),
        ended_at=datetime(2026, 10, 2, 10, 30),
        intel=IntelSnapshot(
            timestamp=1.0,
            action_items=[
                {"id": "action-1", "task": "Ship the fix", "owner": "Me"}
            ],
        ),
    )
    assert meaningful.save(tmp_path / "meaningful-json").database_saved is True
    assert [kind for kind, _payload in events] == ["aftercare_ready"]
    assert [row["id"] for row in db.meetings.list_unread_ready()] == ["meaningful"]
    db.close()


def test_live_summary_only_success_persists_ready_before_frame_and_reload(
    tmp_path: Path, monkeypatch
) -> None:
    """A real live analysis result is durable before its frame and callback."""
    db_path = tmp_path / "c3-live-ready.db"
    db = Database(db_path)
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    frame_markers: list[list[dict[str, object]]] = []
    callback_markers: list[list[dict[str, object]]] = []

    def on_broadcast(kind: str, _payload: object) -> None:
        if kind == "intel_complete":
            frame_markers.append(db.meetings.list_unread_ready())

    def on_intel(_snapshot: IntelSnapshot) -> None:
        callback_markers.append(db.meetings.list_unread_ready())

    session = MeetingSession(
        transcriber=None,
        intel_enabled=True,
        on_intel=on_intel,
        on_broadcast=on_broadcast,
    )
    state = MeetingState(
        id="live-summary",
        title="Live summary",
        started_at=datetime(2026, 10, 3, 9, 0),
        segments=[TranscriptSegment("Summary only", "Me", 0.0, 1.0)],
    )
    session._state = state
    session._intel_live = True
    db.meetings.save_meeting(state)
    result = IntelResult(
        topics=[],
        action_items=[],
        summary="The meeting has a concise summary.",
        raw_response="{}",
    )
    monkeypatch.setattr(
        session,
        "_admitted_live_window",
        lambda _transcript, *, final, analysis_id: (
            SimpleNamespace(outcome="succeeded"),
            {"publication": "published", "analysis_id": analysis_id, "final": final},
            result,
        ),
    )

    session._run_intel_analysis()

    assert frame_markers and frame_markers[0][0]["id"] == state.id
    assert callback_markers and callback_markers[0][0]["id"] == state.id
    reopened = Database(db_path)
    try:
        assert [row["id"] for row in reopened.meetings.list_unread_ready()] == [state.id]
    finally:
        reopened.close()
    db.close()


def test_live_provider_failure_does_not_create_ready_marker(
    tmp_path: Path, monkeypatch
) -> None:
    """A refused live provider result never creates durable READY."""
    db = Database(tmp_path / "c3-live-failed.db")
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    session = MeetingSession(
        transcriber=None,
        intel_enabled=True,
        intel_deferred_enabled=False,
    )
    state = MeetingState(
        id="live-failed",
        title="Failed live analysis",
        started_at=datetime(2026, 10, 3, 10, 0),
        segments=[TranscriptSegment("Provider fails", "Me", 0.0, 1.0)],
    )
    session._state = state
    session._intel_live = True
    db.meetings.save_meeting(state)
    monkeypatch.setattr(
        session,
        "_admitted_live_window",
        lambda _transcript, *, final, analysis_id: (
            SimpleNamespace(outcome="failed", error="provider unavailable"),
            None,
            None,
        ),
    )

    session._run_intel_analysis()

    assert db.meetings.list_unread_ready() == []
    db.close()
