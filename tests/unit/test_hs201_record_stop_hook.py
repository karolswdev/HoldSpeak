"""The web Stop callback cannot reintroduce automatic text work."""
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
from tests.unit.test_hs172_loop_wire import _seed_project, _link_meeting_project


@pytest.mark.parametrize('mode', ['every', 'room_linked'])
def test_web_stop_never_auto_enqueues_before_summary_gesture(tmp_path, monkeypatch, mode):
    db = Database(tmp_path / 'stop-hook.db')
    state = MeetingState(
        id='stop-hook', title='', started_at=datetime.now(), ended_at=datetime.now(),
        capture_status='finalized', segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
    )
    db.meetings.save_meeting(state)
    _seed_project(db, 'room-fixture')
    _link_meeting_project(db, state.id, 'room-fixture')
    cfg = Config()
    cfg.meeting.intelligence_auto = mode
    monkeypatch.setattr(Config, 'load', lambda: cfg)
    monkeypatch.setattr('holdspeak.db.get_database', lambda: db)

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
    assert db.intel.get_intel_job(state.id) is None
    assert not result['save'].get('auto_intel_enqueued', False)
