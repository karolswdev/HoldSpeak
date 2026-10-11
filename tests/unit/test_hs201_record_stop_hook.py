"""The web Stop callback and the summary (PHILO-17).

HS-201-02 parked every automatic summary at Stop. The owner's setting says
"Summary after every meeting", and PHILO-17 makes it true: with a ready
summary route, the setting and the owner's consent, Stop queues the summary
through the "Run intelligence" producer (`queue_after_save`). With no engine
it still queues nothing.
"""
from datetime import datetime
from threading import Lock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.runtime.meeting_glue import MeetingGlueMixin
from holdspeak.runtime.routing_glue import RoutingGlueMixin
from tests.unit.test_hs172_loop_wire import _seed_project, _link_meeting_project, assign_meeting_engine


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
