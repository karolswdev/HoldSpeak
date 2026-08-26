"""HS-143-13 S1 — closed, owner-before-body Assignment HTTP seam."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.inference_assignments import build_inference_assignments_router

OWNER = Principal(PrincipalKind.OWNER, "assignments-http-owner")
AGENT = Principal(PrincipalKind.AGENT, "assignments-http-agent")
MODEL_TURN = Principal(PrincipalKind.SERVICE, "assignments-http-turn")


def _client(tmp_path: Path) -> TestClient:
    service = InferenceAssignmentService(Database(tmp_path / "assignments-http.db"))
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        kind = request.headers.get("x-principal")
        request.state.principal = {
            "owner": OWNER, "agent": AGENT, "model-turn": MODEL_TURN, "none": None,
        }.get(kind, AGENT)
        return await call_next(request)

    app.include_router(build_inference_assignments_router(
        WebContext(get_state=lambda: {}, inference_assignment_service=service)
    ))
    # Focused transport proofs seed real profile/binding objects through the
    # exact service behind the route; never substitute browser-shaped fakes.
    app.state.assignment_test_db = service._db
    return TestClient(app)


def test_assignment_routes_are_owner_before_body_and_summary_is_closed(tmp_path: Path) -> None:
    client = _client(tmp_path)
    for principal in (None, "agent", "model-turn", "none"):
        headers = {} if principal is None else {"x-principal": principal}
        denied = client.post("/api/inference/assignments/set", headers=headers, content=b"not-json")
        assert denied.status_code == 403
        assert denied.json()["code"] == "inference_assignment_owner_required"

    response = client.get("/api/inference/assignments", headers={"x-principal": "owner"})
    assert response.status_code == 200
    projection = response.json()
    assert set(projection) == {"schema", "rows", "task_overrides", "issue_count"}
    assert len(projection["rows"]) == 7
    assert projection["rows"][0]["editor_capability_id"]


def test_editor_preview_and_commands_refuse_unknown_fields_without_echoing_them(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = {"x-principal": "owner"}
    editor = client.post(
        "/api/inference/assignments/editor", headers=headers,
        json={"scope": {"kind": "global"}, "capability_id": "ask.answer", "private_locator": "/no"},
    )
    assert editor.status_code == 400
    assert "private_locator" not in editor.json()["message"]
    preview = client.post(
        "/api/inference/assignments/preview-use-default", headers=headers,
        json={"scope": {"kind": "global"}, "capability_id": "ask.answer", "unknown": "no"},
    )
    assert preview.status_code == 400
    set_response = client.post(
        "/api/inference/assignments/set", headers=headers,
        json={"command_id": "closed-set", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [], "unknown": True},
    )
    assert set_response.status_code == 400
    assert "unknown" not in set_response.json()["message"]


def test_assignment_command_transport_preserves_cas_replay_and_same_id_refusals(
    tmp_path: Path,
) -> None:
    """The route does not weaken whole-chain CAS or command replay semantics."""
    from tests.unit.test_phase143_inference_assignments import _profile

    client = _client(tmp_path)
    _profile(client.app.state.assignment_test_db, "route-primary")
    _profile(client.app.state.assignment_test_db, "route-fallback")
    headers = {"x-principal": "owner"}
    body = {
        "command_id": "route-chain-set",
        "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "route-primary", "profile_revision": 1}],
        "retry_policy_id": None,
    }
    saved = client.post("/api/inference/assignments/set", headers=headers, json=body)
    assert saved.status_code == 200
    assert saved.json()["revision"] == 1
    assert [entry["profile_id"] for entry in saved.json()["entries"]] == ["route-primary"]

    replay = client.post("/api/inference/assignments/set", headers=headers, json=body)
    assert replay.status_code == 200
    assert replay.json() == saved.json()

    stale = client.post(
        "/api/inference/assignments/set", headers=headers,
        json={**body, "command_id": "route-stale-set", "expected_revision": 0},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "inference_assignment_revision_conflict"

    changed_payload = client.post(
        "/api/inference/assignments/set", headers=headers,
        json={
            **body,
            "entries": [{"profile_id": "route-fallback", "profile_revision": 1}],
        },
    )
    assert changed_payload.status_code == 409
    assert changed_payload.json()["code"] == "inference_assignment_command_conflict"

    preview = client.post(
        "/api/inference/assignments/preview-use-default", headers=headers,
        json={"scope": {"kind": "global"}, "capability_id": "ask.answer"},
    )
    assert preview.status_code == 200
    assert preview.json()["expected_revision"] == 1

    clear_body = {
        "command_id": "route-chain-clear",
        "expected_revision": preview.json()["expected_revision"],
        "scope": {"kind": "global"},
        "capability_id": "ask.answer",
    }
    cleared = client.post("/api/inference/assignments/clear", headers=headers, json=clear_body)
    assert cleared.status_code == 200
    assert cleared.json()["revision"] == 2
    assert client.post("/api/inference/assignments/clear", headers=headers, json=clear_body).json() == cleared.json()
    clear_changed = client.post(
        "/api/inference/assignments/clear", headers=headers,
        json={**clear_body, "expected_revision": 2},
    )
    assert clear_changed.status_code == 409
    assert clear_changed.json()["code"] == "inference_assignment_command_conflict"
