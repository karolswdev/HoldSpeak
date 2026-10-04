"""The Settings hub's engine fact follows a real selection (review of #789).

After `/api/concierge/summary-selection` succeeds the summary path has an
engine. The hub read group rows only, so Settings still said
"SUMMARY · NO ENGINE". The fact is the effective assignment for the
capability, as the runner resolves it.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.settings_service import SettingsService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.concierge import build_concierge_router
from holdspeak.web.routes.system.settings import build_settings_router
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "hub-engine-owner")


class _NoSettings(SettingsService):
    def __init__(self) -> None:
        pass


class _Setup:
    def __init__(self, db: Database, home: Path) -> None:
        self._db = db
        self._home_provider = lambda: home


def test_summary_selection_turns_the_meetings_engine_fact_on(tmp_path: Path) -> None:
    db = Database(tmp_path / "hub.db")
    _profile(db, "hub-summary-profile",
             claims=("language", _result_claim("meeting.deferred_analysis")))
    ctx = WebContext(
        get_state=lambda: {},
        inference_setup_service=_Setup(db, tmp_path / "home"),
        inference_assignment_service=InferenceAssignmentService(db),
    )
    # The hub route's composition needs these two; the engine fact does not
    # read them. The assignment service and the selection route are real.
    ctx.settings_service = _NoSettings()
    ctx.credential_service = object()
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_concierge_router(ctx))
    app.include_router(build_settings_router(ctx))
    client = TestClient(app)

    before = client.get("/api/settings/hub").json()
    assert before["meetings"]["engineSet"] is False
    assert before["voice"]["engineSet"] is False

    selected = client.post("/api/concierge/summary-selection", json={
        "commandId": "hub-engine-one",
        "expectedAssignmentRevision": 0,
        "profileId": "hub-summary-profile",
        "profileRevision": 1,
    })
    assert selected.status_code == 200, selected.text
    assert selected.json()["result"]["state"] == "READY"

    after = client.get("/api/settings/hub").json()
    assert after["meetings"]["engineSet"] is True
    # The selection is for the summary capability only; speech has no engine.
    assert after["voice"]["engineSet"] is False
