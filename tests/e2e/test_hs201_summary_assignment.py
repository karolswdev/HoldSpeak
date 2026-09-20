"""HS-201-05 transport fences for one summary selection gesture."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.concierge import build_concierge_router
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "hs201-summary-http-owner")
AGENT = Principal(PrincipalKind.AGENT, "hs201-summary-http-agent")


class _Setup:
    def __init__(self, db: Database, home: Path) -> None:
        self._db = db
        self._home_provider = lambda: home


def _client(tmp_path: Path) -> tuple[TestClient, Database]:
    db = Database(tmp_path / "summary-http.db")
    _profile(
        db,
        "summary-http-profile",
        claims=("language", _result_claim("meeting.deferred_analysis")),
    )
    assignments = InferenceAssignmentService(db)
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER if request.headers.get("x-owner") == "yes" else AGENT
        return await call_next(request)

    app.include_router(
        build_concierge_router(
            WebContext(
                get_state=lambda: {},
                inference_setup_service=_Setup(db, tmp_path / "home"),
                inference_assignment_service=assignments,
            )
        )
    )
    return TestClient(app), db


def test_summary_selection_is_owner_only_and_returns_one_visible_receipt(tmp_path: Path) -> None:
    client, db = _client(tmp_path)
    body = {
        "commandId": "summary-http-one",
        "expectedAssignmentRevision": 0,
        "profileId": "summary-http-profile",
        "profileRevision": 1,
    }
    denied = client.post("/api/concierge/summary-selection", json=body)
    assert denied.status_code == 403
    response = client.post(
        "/api/concierge/summary-selection",
        headers={"x-owner": "yes"},
        json=body,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["schema"] == "ConciergeSummaryAssignmentReceipt@1"
    assert result["status"] == "succeeded"
    assert result["result"]["state"] == "READY"
    assert result["receipt"]["visible"] is True
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key=?",
            ("capability:meeting.deferred_analysis",),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM kernel_receipts WHERE receipt_id=?",
            (result["receipt"]["id"],),
        ).fetchone()[0] == 1
    detected = client.get("/api/concierge/detect", headers={"x-owner": "yes"})
    assert detected.status_code == 200, detected.text
    projection = detected.json()["summaryAssignment"]
    assert projection["status"] == "assigned"
    assert projection["profileId"] == "summary-http-profile"
    assert projection["profileRevision"] == 1


def test_summary_selection_conflict_is_truthful_over_http(tmp_path: Path) -> None:
    client, _db = _client(tmp_path)
    headers = {"x-owner": "yes"}
    first = {
        "commandId": "summary-http-seed",
        "expectedAssignmentRevision": 0,
        "profileId": "summary-http-profile",
        "profileRevision": 1,
    }
    assert client.post("/api/concierge/summary-selection", headers=headers, json=first).status_code == 200
    stale = client.post(
        "/api/concierge/summary-selection",
        headers=headers,
        json={**first, "commandId": "summary-http-stale"},
    )
    assert stale.status_code == 200
    result = stale.json()
    assert result["status"] == "conflict"
    assert result["result"]["state"] == "CONFLICT"
    assert result["result"]["code"] == "inference_assignment_revision_conflict"
    assert result["result"]["expectedAssignmentRevision"] == 0
    assert result["result"]["currentAssignmentRevision"] == 1
