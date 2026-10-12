"""Unit tests for MeetingSession runtime behavior."""
from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from typing import Any, Sequence
from unittest.mock import Mock

import numpy as np
import pytest

import holdspeak.db as db_module
from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.meeting_recorder import AudioChunk
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment
from holdspeak.runtime.meeting_glue import MeetingGlueMixin
from holdspeak.runtime.routing_glue import RoutingGlueMixin
from tests.unit.test_hs172_loop_wire import (
    _link_meeting_project,
    _seed_project,
    assign_meeting_engine,
)


class _FakeTranscriber:
    def transcribe(self, audio, **kwargs) -> str:
        _ = audio
        return "final transcript"


class _StubAdmission:
    """The admitted-transcription seam, reduced to running the dispatch.

    HS-131-09 makes every interval a child of the live ``meeting.session``; the
    real parent, child, and the drop-without-one are proven in
    ``test_dictation_session_admission.py``. These sessions never call
    ``start()``, so they never admitted a parent — the concern here is locking.
    """

    class _Outcome:
        outcome = "succeeded"

    def transcribe_child(self, *, material, run, seed, **kwargs):
        return self._Outcome(), run()


class _FakeRecorder:
    def stop(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        chunk = AudioChunk(
            audio=np.ones(16000, dtype=np.float32),
            timestamp=0.0,
            source="mic",
            duration=1.0,
        )
        return [chunk], []

    def get_pending_device_chunks(self) -> dict[str, list[AudioChunk]]:
        return {}


def test_stop_completes_without_deadlock_during_final_transcription_and_intel() -> None:
    """stop() should not hold the session lock across finalization work.

    HS-131-08 (Sol Amendment 2): the final analysis is no longer dispatched from
    inside ``stop()``. Stop cancels the live intelligence parent and hands the
    displaced final work to an admitted deferred job, so this session — which
    never admitted a parent — must perform NO provider work here at all. The
    deadlock proof is unchanged: final transcription still runs outside the lock.
    """
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-1",
        started_at=datetime.now(),
        title="Already titled",
    )
    session._recorder = _FakeRecorder()
    session._intel_live = True
    session._transcription_admission = lambda: _StubAdmission()  # type: ignore[method-assign]

    intel_calls: list[tuple[bool, str]] = []

    def fake_run_intel_analysis(final: bool = False) -> None:
        intel_calls.append((final, session.get_formatted_transcript()))

    session._run_intel_analysis = fake_run_intel_analysis  # type: ignore[method-assign]

    outcome: dict[str, object] = {"state": None, "error": None}

    def run_stop() -> None:
        try:
            outcome["state"] = session.stop()
        except Exception as exc:  # pragma: no cover - assertion below handles this
            outcome["error"] = exc

    thread = threading.Thread(target=run_stop, daemon=True)
    thread.start()
    thread.join(timeout=1.5)

    assert not thread.is_alive(), "MeetingSession.stop() deadlocked during finalization"
    assert outcome["error"] is None

    state = outcome["state"]
    assert isinstance(state, MeetingState)
    assert state.ended_at is not None
    assert [segment.text for segment in state.segments] == ["final transcript"]
    # No unadmitted post-close provider dispatch survives inside stop().
    assert intel_calls == []


def test_meeting_session_is_web_free_and_emits_via_on_broadcast() -> None:
    """HS-32-02: the session owns no web server; it emits live events through
    the injected ``on_broadcast`` callback (which a runtime observes)."""
    events: list[tuple[str, object]] = []

    def _spy(message_type: str, data: object) -> None:
        # Snapshot at emit time: payloads reference live state, and a real
        # observer (server.broadcast) serializes synchronously on receipt.
        snapshot = dict(data) if isinstance(data, dict) else data
        if isinstance(snapshot, dict) and isinstance(snapshot.get("tags"), list):
            snapshot["tags"] = list(snapshot["tags"])
        events.append((message_type, snapshot))

    session = MeetingSession(transcriber=_FakeTranscriber(), on_broadcast=_spy)
    session._state = MeetingState(id="m1", started_at=datetime.now())

    # The inversion is structural: no embedded web server, no web knob.
    assert not hasattr(session, "_web_server")
    assert not hasattr(session, "web_enabled")

    session.set_title("Planning Sync")
    session.add_tag("Ops")
    session.set_tags(["delivery", "qa"])

    assert events == [
        ("meeting_updated", {"title": "Planning Sync", "tags": []}),
        ("meeting_updated", {"title": "Planning Sync", "tags": ["ops"]}),
        ("meeting_updated", {"title": "Planning Sync", "tags": ["delivery", "qa"]}),
    ]


def test_title_and_tag_edits_are_safe_without_an_observer() -> None:
    """Default (no ``on_broadcast``): the emit is a silent no-op and the
    title/tag paths still mutate state — a meeting runs with no web server."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(id="m2", started_at=datetime.now())

    session.set_title("Solo")
    session.set_tags(["x"])

    assert session.get_title() == "Solo"
    assert session.get_tags() == ["x"]


def test_on_broadcast_callback_exception_does_not_break_the_session() -> None:
    """A misbehaving observer must not propagate into meeting bookkeeping."""

    def _boom(message_type: str, data: object) -> None:
        raise RuntimeError("observer exploded")

    session = MeetingSession(transcriber=_FakeTranscriber(), on_broadcast=_boom)
    session._state = MeetingState(id="m3", started_at=datetime.now())

    # Must not raise even though the callback does.
    session.set_title("Resilient")
    assert session.get_title() == "Resilient"


def test_save_reports_partial_failure_when_db_write_fails(tmp_path: Path) -> None:
    """save() should surface DB failure even when JSON persistence succeeds."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-2",
        started_at=datetime(2024, 1, 15, 10, 30, 0),
        ended_at=datetime(2024, 1, 15, 10, 45, 0),
    )

    original_get_database = db_module.get_database

    def broken_get_database(*args, **kwargs):
        _ = args, kwargs
        raise RuntimeError("db unavailable")

    db_module.get_database = broken_get_database
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert result.database_saved is False
    assert result.json_saved is True
    assert result.json_path == tmp_path / "meeting_meeting-2_20240115_103000.json"
    assert result.json_path is not None and result.json_path.exists()
    assert result.database_error == "RuntimeError: db unavailable"
    assert result.json_error is None


def test_save_reports_success_when_both_db_and_json_succeed(tmp_path: Path) -> None:
    """save() should mark both persistence paths successful when they work."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-3",
        started_at=datetime(2024, 1, 15, 11, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 5, 0),
    )

    class _FakeDatabase:
        meetings = property(lambda self: self)
        def __init__(self) -> None:
            self.saved = []

        def save_meeting(self, state: MeetingState) -> None:
            self.saved.append(state.id)

    fake_db = _FakeDatabase()
    original_get_database = db_module.get_database
    db_module.get_database = lambda *args, **kwargs: fake_db
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert fake_db.saved == ["meeting-3"]
    assert result.database_saved is True
    assert result.json_saved is True
    assert result.database_error is None
    assert result.json_error is None
    assert result.json_path == tmp_path / "meeting_meeting-3_20240115_110000.json"


def test_save_enqueues_deferred_intel_job_when_meeting_status_is_queued(tmp_path: Path) -> None:
    """save() should enqueue deferred intel work for queued meetings."""
    session = MeetingSession(
        transcriber=_FakeTranscriber(),
        intel_enabled=True,
        intel_deferred_enabled=True,
    )
    session._state = MeetingState(
        id="meeting-4",
        started_at=datetime(2024, 1, 15, 11, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 5, 0),
        intel_status="queued",
        intel_status_detail="Queued for later processing.",
    )
    session._state.segments.append(
        TranscriptSegment(
            text="Need to follow up later.",
            speaker="Me",
            start_time=0.0,
            end_time=2.0,
        )
    )

    class _FakeDatabase:
        intel = property(lambda self: self)
        meetings = property(lambda self: self)
        def __init__(self) -> None:
            self.saved: list[str] = []
            self.enqueued: list[tuple[str, str, str | None, Sequence[str], Any | None, bool]] = []

        def save_meeting(self, state: MeetingState) -> None:
            self.saved.append(state.id)

        def enqueue_intel_job(
            self,
            meeting_id: str,
            *,
            transcript_hash: str,
            reason: str | None = None,
            displaced_work: Sequence[str] = (),
            conn: Any | None = None,
            legacy_displaced_work: bool = False,
        ) -> str:
            self.enqueued.append(
                (meeting_id, transcript_hash, reason, displaced_work, conn, legacy_displaced_work)
            )
            return "ij_fake"

    fake_db = _FakeDatabase()
    original_get_database = db_module.get_database
    db_module.get_database = lambda *args, **kwargs: fake_db
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert result.database_saved is True
    assert result.intel_job_enqueued is True
    assert fake_db.saved == ["meeting-4"]
    assert len(fake_db.enqueued) == 1
    meeting_id, transcript_hash, reason, displaced_work, conn, legacy = fake_db.enqueued[0]
    assert meeting_id == "meeting-4"
    assert transcript_hash == session._state.transcript_hash()
    assert reason == "Queued for later processing."
    assert displaced_work == () and conn is None and legacy is False


# ── from test_hs201_record_stop_hook.py: The web Stop callback and the summary (PHILO-17). ──
#
# HS-201-02 parked every automatic summary at Stop. The owner's setting says
# "Summary after every meeting", and PHILO-17 makes it true: with a ready
# summary route, the setting and the owner's consent, Stop queues the summary
# through the "Run intelligence" producer (`queue_after_save`). With no engine
# it still queues nothing.


def _stopped(tmp_path, monkeypatch, *, mode: str, linked: bool = True, engine: bool = False):
    db = Database(tmp_path / 'stop-hook.db')
    state = MeetingState(
        id='stop-hook', title='', started_at=datetime.now(), ended_at=datetime.now(),
        capture_status='finalized', segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
    )
    db.meetings.save_meeting(state)
    if linked:
        _seed_project(db, 'room-fixture')
        _link_meeting_project(db, state.id, 'room-fixture')
    if engine:
        assign_meeting_engine(db)  # the owner's own press, a local engine
    cfg = Config()
    cfg.meeting.intelligence_auto = mode
    monkeypatch.setattr(Config, 'load', lambda: cfg)
    monkeypatch.setattr('holdspeak.db.get_database', lambda: db)
    woken: list[bool] = []
    monkeypatch.setattr(
        'holdspeak.intel_queue_conductor.wake_intel_queue_conductor', lambda: woken.append(True) or True,
    )

    class Runtime(MeetingGlueMixin, RoutingGlueMixin):
        pass

    runtime = Runtime()
    runtime.state_lock = Lock()
    runtime.meeting_lock = Lock()
    runtime.runtime_status = {}
    runtime.recording_ticker = Mock()
    runtime.device_stats_cycle = {}
    runtime.voice_session = Mock()
    runtime._set_runtime_activity = Mock()
    runtime._flush_deferred_plugin_runs_to_db = lambda: {}
    runtime._persist_pending_mir_history = lambda _: {}
    runtime._synthesize_and_persist_artifacts = lambda _: {}
    runtime._associate_meeting_with_projects = lambda _: {'projects_associated': 1}
    runtime.meeting_session = SimpleNamespace(
        is_active=True, state=state, stop=lambda: state,
        save=lambda: SimpleNamespace(database_saved=True, json_saved=False, json_path=None, intel_job_enqueued=False),
    )
    result = runtime._stop_active_meeting(allow_runtime_fallback=False)
    assert result['save_error'] is None
    assert result['save']['database_saved'] is True
    return db, state, result, woken


@pytest.mark.parametrize('mode', ['every', 'room_linked'])
def test_web_stop_with_no_engine_queues_nothing_and_marks_the_meeting(tmp_path, monkeypatch, mode):
    db, state, result, woken = _stopped(tmp_path, monkeypatch, mode=mode)
    assert db.intel.get_intel_job(state.id) is None
    assert result['save']['auto_intel_enqueued'] is False
    assert result['save']['summary_deferred_no_engine'] is True  # the backlog runs it later
    assert woken == []


def test_web_stop_with_an_engine_queues_the_summary_after_every_meeting(tmp_path, monkeypatch):
    db, state, result, woken = _stopped(tmp_path, monkeypatch, mode='every', linked=False, engine=True)
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == 'queued'
    assert job.planned_route and job.planned_route.get('status') == 'ready'  # the disclosed route rides the job
    assert result['save']['auto_intel_enqueued'] is True
    assert woken == [True]
    stored = db.meetings.get_meeting(state.id)
    assert stored.intel_status == 'queued'
    assert stored.intel_status_detail == 'Queued after the meeting.'


def test_web_stop_follows_the_setting(tmp_path, monkeypatch):
    db, state, result, _ = _stopped(tmp_path, monkeypatch, mode='off', engine=True)
    assert db.intel.get_intel_job(state.id) is None and result['save']['auto_intel_enqueued'] is False


def test_web_stop_room_linked_skips_a_meeting_with_no_room(tmp_path, monkeypatch):
    db, state, result, _ = _stopped(tmp_path, monkeypatch, mode='room_linked', linked=False, engine=True)
    assert db.intel.get_intel_job(state.id) is None and result['save']['auto_intel_enqueued'] is False


def test_web_stop_room_linked_queues_a_room_meeting(tmp_path, monkeypatch):
    db, state, result, _ = _stopped(tmp_path, monkeypatch, mode='room_linked', linked=True, engine=True)
    assert db.intel.get_intel_job(state.id) is not None and result['save']['auto_intel_enqueued'] is True
