"""HS-77-02 — a real `runtime_queue` frame for the Queue HUD.

The deferred-intel queue's truth (listable jobs + aggregate telemetry)
broadcasts on queue transitions instead of the HUD synthesizing at most
two jobs from side signals.
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="route tests drive the real app")

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.intel_queue import build_runtime_queue_frame
from holdspeak.meeting_session import MeetingState


@pytest.fixture()
def db(monkeypatch):
    reset_database()
    database = Database(Path(tempfile.mkdtemp()) / "queue-frame.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    yield database
    reset_database()


def test_frame_carries_jobs_and_summary(db) -> None:
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Planning")
    )
    db.meetings.save_meeting(
        MeetingState(id="m2", started_at=datetime.now(), title="Retro")
    )
    db.intel.enqueue_intel_job("m1", transcript_hash="h1")
    db.intel.enqueue_intel_job("m2", transcript_hash="h2")

    frame = build_runtime_queue_frame(db)
    assert frame["queued"] == 2 and frame["running"] == 0 and frame["failed"] == 0
    ids = {j["id"] for j in frame["jobs"]}
    assert ids == {"intelq:m1", "intelq:m2"}
    by_id = {j["id"]: j for j in frame["jobs"]}
    assert by_id["intelq:m1"]["label"] == "Planning"
    assert by_id["intelq:m1"]["status"] == "queued"


def test_empty_queue_is_an_honest_empty_frame(db) -> None:
    frame = build_runtime_queue_frame(db)
    assert frame == {
        "jobs": [], "queued": 0, "running": 0, "failed": 0,
        "scheduled_retries": 0, "next_retry_at": None,
    }


def test_intel_process_route_broadcasts_the_frame(db, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Planning")
    )
    db.intel.enqueue_intel_job("m1", transcript_hash="h1")

    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
    ), host="127.0.0.1")
    frames: list[tuple[str, dict]] = []
    monkeypatch.setattr(server, "broadcast", lambda t, d: frames.append((t, d)))
    # The drain itself would load a model; stub it to touch nothing.
    import holdspeak.web.routes.meetings.intel as intel_routes  # noqa: F401
    import holdspeak.intel_queue as iq
    monkeypatch.setattr(iq, "drain_intel_queue", lambda *a, **k: 0)

    client = TestClient(server.app)
    resp = client.post("/api/intel/process", json={})
    assert resp.status_code == 200, resp.text

    queue_frames = [d for (t, d) in frames if t == "runtime_queue"]
    assert len(queue_frames) == 1
    assert queue_frames[0]["queued"] == 1
    assert queue_frames[0]["jobs"][0]["id"] == "intelq:m1"
