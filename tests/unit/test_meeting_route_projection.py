"""The meeting summary route: the words every face reads from the route, and the
HTTP run gestures that carry the disclosed selection (moved together by service, the fast diet 2026-10-12).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_route_projection import summary_engine_fact
from holdspeak.services.settings_service import SettingsService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.settings import build_settings_router
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from datetime import datetime
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.web.routes.meetings.intel import build_intel_router
from tests.unit.test_hs201_route_contract import OWNER as OWNER_HTTP, assign_summary, summary_profile


# ── from tests/unit/test_philo15_18_engine_words.py (moved whole by the fast diet, 2026-10-12) ──
# PHILO-15 B33: every "no model" word reads the summary ROUTE, not an exact pick.
#
# Rehearsal 1B: summaries ran on the LAN box (doctor: "Meeting summary: profile
# '192.168.1.43:8080'") while five faces said there was no model: the Settings
# headline, the Assignments and Meetings rows, Settings › Meetings ("NO MODEL"),
# Connections › Models ("Unassigned"), and doctor's hub check ("no targets
# configured"). Here the Default for AI work is the only assignment: no exact
# capability pick and no legacy ``meeting.intel_profile_id`` pointer.

OWNER = Principal(PrincipalKind.OWNER, "b33-owner")
SUMMARY = "meeting.deferred_analysis"


class _NoSettings(SettingsService):
    def __init__(self) -> None:
        pass


class _Setup:
    def __init__(self, db: Database, home: Path) -> None:
        self._db = db
        self._home_provider = lambda: home


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "b33.db")
    _profile(database, "lan-box", claims=("language", "structured_output", _result_claim(SUMMARY)),
             modalities=("language", "text"))
    return database


def _default(db: Database) -> None:
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "b33-default", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "lan-box", "profile_revision": 1}],
    })


def _hub(db: Database, tmp_path: Path) -> dict[str, Any]:
    ctx = WebContext(
        get_state=lambda: {},
        inference_setup_service=_Setup(db, tmp_path / "home"),
        inference_assignment_service=InferenceAssignmentService(db),
    )
    ctx.settings_service = _NoSettings()
    ctx.credential_service = object()
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_settings_router(ctx))
    return TestClient(app).get("/api/settings/hub").json()


def test_the_route_fact_follows_the_default(db: Database) -> None:
    assert summary_engine_fact(db)["engine_set"] is False
    _default(db)
    fact = summary_engine_fact(db)
    assert fact["engine_set"] is True and fact["host"] == "local" and fact["off"] is False


def test_settings_hub_meetings_reads_the_route(db: Database, tmp_path: Path) -> None:
    before = _hub(db, tmp_path)
    assert before["meetings"]["engineSet"] is False
    _default(db)
    after = _hub(db, tmp_path)
    # Main: the exact capability check said False here ("SUMMARY · NO ENGINE")
    # and the host came from the legacy config pointer only ("NO MODEL").
    assert after["meetings"]["engineSet"] is True
    assert after["meetings"]["host"] == "local"
    assert after["meetings"]["summariesOff"] is False


def test_settings_hub_says_summaries_off_not_no_engine(db: Database, tmp_path: Path) -> None:
    _default(db)
    InferenceAssignmentService(db).set_capability_off(OWNER, capability_id=SUMMARY)
    hub = _hub(db, tmp_path)
    assert hub["meetings"]["engineSet"] is False and hub["meetings"]["summariesOff"] is True


def test_connections_models_row_names_the_summary_route(db: Database, monkeypatch) -> None:
    from holdspeak.services.connections_service import ConnectionsService

    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    service = ConnectionsService(inference_assignment_service=InferenceAssignmentService(db))
    _default(db)
    models = service.list_tools(OWNER)["tools"][-1]
    assert models["provider_id"] == "models"
    assert models["state"] == "connected" and models["account"]["summary_host"] == "local"


def test_doctor_hub_check_reads_the_route_when_no_legacy_target(db: Database, monkeypatch) -> None:
    import holdspeak.doctor as doctor

    monkeypatch.setattr(doctor, "_get_json", lambda *a, **k: (200, {"targets": []}))
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    assert doctor._check_inference("http://hub", "tok").status == "SKIP"
    _default(db)
    result = doctor._check_inference("http://hub", "tok")
    assert result.status == "PASS" and "summary route" in result.detail, result


# ── from tests/unit/test_hs201_route_http.py (moved whole by the fast diet, 2026-10-12) ──
# The three HTTP run gestures carry the same disclosed selection.

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
        request.state.principal = OWNER_HTTP
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
