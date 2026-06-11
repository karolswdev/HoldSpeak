"""HS-56-04 — the learning + aftercare broadcasts the presence mascot consumes.

The journal correct route now broadcasts `learning_event`, but only honestly:
only when the correction was actually taught AND has real Jaccard reach
(`similar > 0`) — a no-op teach stays silent. A wrapped meeting broadcasts
`aftercare_ready` from `MeetingSession.save()`, but only for a finished
meeting whose digest is non-empty; the deferred intel queue hands the same
moment to its host through a purely observational `on_meeting_ready` hook
(an exploding observer never breaks the audited job completion).
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

import holdspeak.intel_queue as intel_queue_module
from holdspeak.db import get_database, reset_database
from holdspeak.intel_queue import process_next_intel_job
from holdspeak.meeting_session import (
    IntelSnapshot,
    MeetingSession,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def server(db):
    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )


@pytest.fixture
def broadcasts(server, monkeypatch):
    sent: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        server, "broadcast", lambda message_type, data: sent.append((message_type, data))
    )
    return sent


@pytest.fixture
def client(server):
    return TestClient(server.app)


# ── learning_event: the correct route, honest about reach ────────────────────


def test_correct_route_broadcasts_learning_event_with_real_reach(client, db, broadcasts):
    # Two similar utterances in the journal: the taught gist reaches both.
    entry = db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about the launch", final_text="x"
    )
    db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch timing", final_text="y"
    )

    response = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "action_item"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["taught"] is True and body["similar"] > 0

    events = [d for (t, d) in broadcasts if t == "learning_event"]
    assert len(events) == 1
    data = events[0]
    assert data["kind"] == "intent"
    assert data["value"] == "action_item"
    # The broadcast's reach IS the response's reach — one matcher, one number.
    assert data["similar"] == body["similar"]
    assert data["enabled"] == body["enabled"]
    assert data["gist"].startswith("follow up with sam")


def test_no_learning_event_when_nothing_was_taught(client, db, broadcasts):
    # A secret-shaped transcript: the store refuses the teach (taught=False) —
    # the entry is still flagged corrected, but the mascot stays silent.
    entry = db.dictation_journal.record(
        source="dictation",
        transcript="set the api_key to sk-abcdefghijklmnop1234",
        final_text="x",
    )
    response = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "action_item"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["corrected"] is True
    assert body["taught"] is False

    events = [d for (t, d) in broadcasts if t == "learning_event"]
    assert events == [], "a no-op teach must never claim learning"


def test_learning_event_gist_is_truncated(client, db, broadcasts):
    long_transcript = "remind me to review the quarterly budget spreadsheet " * 6
    entry = db.dictation_journal.record(
        source="dictation", transcript=long_transcript.strip(), final_text="x"
    )
    response = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "reminder"},
    )
    assert response.status_code == 200
    events = [d for (t, d) in broadcasts if t == "learning_event"]
    assert len(events) == 1
    assert len(events[0]["gist"]) <= 121  # 120 chars + the ellipsis
    assert events[0]["gist"].endswith("…")


# ── aftercare_ready: the meeting wrap flow, quiet when empty ─────────────────


class _FakeTranscriber:
    def transcribe(self, audio) -> str:  # pragma: no cover - never called here
        _ = audio
        return ""


def _wrapped_state(meeting_id, *, action_items):
    started = datetime(2026, 6, 10, 10, 0, 0)
    return MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Wrap test",
        segments=[
            TranscriptSegment(
                text="let's divide the follow-ups", speaker="Me", start_time=0.0, end_time=5.0
            )
        ],
        intel=IntelSnapshot(timestamp=60.0, action_items=action_items),
    )


def _open_item(item_id, task, owner):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": None,
        "status": "pending",
        "review_state": "pending",
        "source_timestamp": None,
        "created_at": datetime(2026, 6, 10, 10, 30, 0).isoformat(),
    }


def test_meeting_save_broadcasts_aftercare_ready_when_work_is_open(db, tmp_path):
    sent: list[tuple[str, dict]] = []
    session = MeetingSession(
        transcriber=_FakeTranscriber(), on_broadcast=lambda t, d: sent.append((t, d))
    )
    session._state = _wrapped_state(
        "m-wrap",
        action_items=[
            _open_item("a1", "Fix the login bug", "Me"),
            _open_item("a2", "Draft the rollout note", "Sam"),
            _open_item("a3", "Book the retro", "Sam"),
        ],
    )

    result = session.save(directory=tmp_path)
    assert result.database_saved is True

    events = [d for (t, d) in sent if t == "aftercare_ready"]
    assert len(events) == 1
    data = events[0]
    assert data["meeting_id"] == "m-wrap"
    assert data["open_total"] == 3
    assert len(data["top_items"]) == 2  # capped, wire-safe
    assert all(set(item) == {"task", "owner"} for item in data["top_items"])


def test_meeting_save_is_quiet_for_an_empty_digest(db, tmp_path):
    sent: list[tuple[str, dict]] = []
    session = MeetingSession(
        transcriber=_FakeTranscriber(), on_broadcast=lambda t, d: sent.append((t, d))
    )
    session._state = _wrapped_state("m-quiet", action_items=[])

    result = session.save(directory=tmp_path)
    assert result.database_saved is True
    assert [t for (t, _d) in sent if t == "aftercare_ready"] == []


def test_meeting_save_is_quiet_for_an_unfinished_meeting(db, tmp_path):
    sent: list[tuple[str, dict]] = []
    session = MeetingSession(
        transcriber=_FakeTranscriber(), on_broadcast=lambda t, d: sent.append((t, d))
    )
    state = _wrapped_state("m-live", action_items=[_open_item("a1", "Task", "Me")])
    state.ended_at = None  # still running (an autosave mid-meeting)
    session._state = state

    session.save(directory=tmp_path)
    assert [t for (t, _d) in sent if t == "aftercare_ready"] == []


# ── the intel queue's on_meeting_ready observer ──────────────────────────────


class _FakeIntelResult:
    error = None
    topics: list = []
    action_items = [
        {
            "id": "a1",
            "task": "Ship the fix",
            "owner": "Me",
            "due": None,
            "status": "pending",
            "review_state": "pending",
            "source_timestamp": None,
            "created_at": datetime(2026, 6, 10, 10, 30, 0).isoformat(),
        }
    ]
    summary = "A meeting."


class _FakeIntel:
    def __init__(self, **_kwargs):
        pass

    def analyze(self, _transcript, stream=False):
        _ = stream
        return _FakeIntelResult()


def _queued_meeting(db, meeting_id):
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 6, 10, 10, 0, 0),
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Deferred",
        segments=[
            TranscriptSegment(
                text="we should ship the fix", speaker="Me", start_time=0.0, end_time=5.0
            )
        ],
    )
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        meeting_id, transcript_hash=state.transcript_hash(), reason="test"
    )
    return state


def test_process_next_intel_job_notifies_on_meeting_ready(db, monkeypatch):
    monkeypatch.setattr(
        intel_queue_module, "get_intel_runtime_status", lambda *a, **k: (True, "ok")
    )
    monkeypatch.setattr(intel_queue_module, "MeetingIntel", _FakeIntel)
    _queued_meeting(db, "m-intel")

    ready: list[str] = []
    assert process_next_intel_job(on_meeting_ready=ready.append) is True
    assert ready == ["m-intel"]
    assert db.meetings.get_meeting("m-intel").intel_status == "ready"


def test_exploding_on_meeting_ready_never_breaks_the_job(db, monkeypatch):
    monkeypatch.setattr(
        intel_queue_module, "get_intel_runtime_status", lambda *a, **k: (True, "ok")
    )
    monkeypatch.setattr(intel_queue_module, "MeetingIntel", _FakeIntel)
    _queued_meeting(db, "m-boom")

    def _boom(_meeting_id):
        raise RuntimeError("observer boom")

    assert process_next_intel_job(on_meeting_ready=_boom) is True
    # The job completed and the intel landed — the observer is observational.
    assert db.meetings.get_meeting("m-boom").intel_status == "ready"
    assert db.intel.claim_next_intel_job() is None
