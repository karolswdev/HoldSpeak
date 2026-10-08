"""PHILO-15 B33: every "no model" word reads the summary ROUTE, not an exact pick.

Rehearsal 1B: summaries ran on the LAN box (doctor: "Meeting summary: profile
'192.168.1.43:8080'") while five faces said there was no model: the Settings
headline, the Assignments and Meetings rows, Settings › Meetings ("NO MODEL"),
Connections › Models ("Unassigned"), and doctor's hub check ("no targets
configured"). Here the Default for AI work is the only assignment: no exact
capability pick and no legacy ``meeting.intel_profile_id`` pointer.
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
