"""The three HTTP run gestures carry the same disclosed selection."""
from datetime import datetime

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.intel import build_intel_router
from tests.unit.test_hs201_route_contract import OWNER, assign_summary, summary_profile


@pytest.mark.parametrize('path', [
    '/api/meetings/http-route/intelligence/run',
    '/api/intel/retry/http-route',
    '/api/meetings/http-route/intel-recovery/retry',
])
def test_http_route_refusal_and_repair_use_disclosed_selection(tmp_path, monkeypatch, path):
    db = Database(tmp_path / 'route-http.db')
    db.meetings.save_meeting(MeetingState(
        id='http-route', title='HTTP route', started_at=datetime.now(),
        ended_at=datetime.now(), capture_status='finalized',
        segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
    ))
    summary_profile(db, 'http-summary')
    assign_summary(db, ['http-summary'])
    service = MeetingIntelService(db)
    monkeypatch.setattr('holdspeak.intel_queue_conductor.wake_intel_queue_conductor', lambda: False)
    app = FastAPI()

    @app.middleware('http')
    async def principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_intel_router(WebContext(
        get_state=lambda: {}, meeting_intel_service=service,
    )))
    with TestClient(app) as client:
        for body in ({}, {'expected_selection_hash': 'stale-selection'}):
            refused = client.post(path, json=body)
            assert refused.status_code == 409, refused.text
            receipt = client.get('/api/meetings/http-route/intel-recovery').json()['run_receipt']
            assert receipt['outcome'] == 'refused' and receipt['attempts'] == []
        read = client.get('/api/meetings/http-route/intel-recovery').json()
        assert read['planned_route']['status'] == 'ready'
        old_hash = read['planned_route']['selection_hash']
        summary_profile(db, 'http-repaired')
        assign_summary(db, ['http-repaired'], expected_revision=1, command='http-repair')
        repaired = client.get('/api/meetings/http-route/intel-recovery').json()['planned_route']
        assert repaired['selection_hash'] != old_hash
        accepted = client.post(path, json={'expected_selection_hash': repaired['selection_hash']})
        assert accepted.status_code == 200, accepted.text
        job = db.intel.get_intel_job('http-route')
        assert job.status == 'queued'
        assert job.planned_route == repaired
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0
