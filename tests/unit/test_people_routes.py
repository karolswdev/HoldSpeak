"""Authenticated HTTP contract for the encrypted People service."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

import holdspeak.db as db_module
from holdspeak.mcp.families import people as people_family
from holdspeak.db.core import Database, reset_database
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.people import build_people_router


def _client(
    tmp_path: Path,
    principal: Principal,
    service: PeopleService | None = None,
) -> TestClient:
    people_service = service or PeopleService(
        EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore()),
        setup_runner=lambda *, initialize, principal: initialize(),
    )
    app = FastAPI()

    @app.middleware("http")
    async def principal_state(request: Request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_people_router(WebContext(
        get_state=lambda: {},
        people_service=people_service,
    )))
    return TestClient(app)


def test_setup_and_manual_people_routes(tmp_path: Path) -> None:
    owner = Principal(PrincipalKind.OWNER, "route-owner")
    client = _client(tmp_path, owner)
    assert client.get("/api/people/readiness").json()["state"] == "unconfigured"
    assert client.post("/api/people/setup").json()["state"] == "ready"
    created = client.post("/api/people/relationships", json={"display_name": "Route Sentinel"})
    assert created.status_code == 201
    relationship_id = created.json()["relationship"]["id"]
    note = client.post(
        f"/api/people/relationships/{relationship_id}/notes",
        json={"topic": "Grounding", "body": "Durable context", "visibility": "leader_private"},
    )
    assert note.status_code == 201
    assert client.get(f"/api/people/relationships/{relationship_id}/notes").json()["notes"][0]["body"] == "Durable context"
    request = client.post(f"/api/people/relationships/{relationship_id}/requests", json={"body": "A private request"})
    assert request.status_code == 201
    accepted = client.post(f"/api/people/requests/{request.json()['request']['id']}/accept", json={})
    assert accepted.status_code == 200
    detail = client.get(f"/api/people/relationships/{relationship_id}").json()["relationship"]
    assert detail["commitments"][0]["body"] == "A private request"
    assert detail["notes"][0]["topic"] == "Grounding"


def test_people_routes_require_authenticated_owner(tmp_path: Path) -> None:
    client = _client(tmp_path, Principal(PrincipalKind.NONE, "none"))
    response = client.get("/api/people/readiness")
    assert response.status_code == 403
    assert response.json() == {"detail": "people_owner_required"}
    transition = client.post("/api/people/commitments/missing/transition", json={"verb": "done"})
    assert transition.status_code == 403
    assert transition.json() == {"detail": "people_owner_required"}


def test_commitment_can_flow_to_workbench_output_and_satisfaction_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = Principal(PrincipalKind.OWNER, "route-owner")
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(db_module, "get_database", lambda: database)
    monkeypatch.setattr(db_module, "get_observer", lambda: None)
    workbench = WorkbenchService(database).create_workbench(owner, name="Architecture work")
    project = ProjectService(database).create_project(owner, {
        "name": "Platform modernization",
        "description": "Move the platform toward a simpler architecture",
        "keywords": ["platform", "architecture"],
    })
    client = _client(tmp_path, owner)
    client.post("/api/people/setup")
    relationship = client.post(
        "/api/people/relationships",
        json={"display_name": "Relationship", "relationship_kind": "peer"},
    ).json()["relationship"]
    linked_project = client.post(
        f"/api/people/relationships/{relationship['id']}/projects/{project['id']}",
        json={},
    )
    assert linked_project.status_code == 200
    assert linked_project.json()["relationship"]["project_refs"] == [project["id"]]
    request = client.post(
        f"/api/people/relationships/{relationship['id']}/requests",
        json={"body": "Prepare the next architecture discussion"},
    ).json()["request"]
    commitment = client.post(f"/api/people/requests/{request['id']}/accept", json={}).json()["commitment"]

    sent = client.post(
        f"/api/people/commitments/{commitment['id']}/workbench",
        json={"workbench_id": workbench["id"]},
    )
    assert sent.status_code == 201
    item = sent.json()["item"]
    assert item["title"] == "Prepare the next architecture discussion"
    assert item["grounding"]["projects"][0]["name"] == "Platform modernization"
    assert item["context"]["project_ids"] == [project["id"]]
    WorkbenchService(database).update_item(
        owner,
        workbench["id"],
        item["id"],
        status="done",
        result="Architecture brief",
        completed_at="2026-08-17T04:00:00Z",
    )

    execution = client.get(f"/api/people/commitments/{commitment['id']}/execution").json()
    assert execution["items"][0]["result"] == "Architecture brief"
    satisfied = client.post(
        f"/api/people/commitments/{commitment['id']}/satisfy",
        json={"rationale": "Brief reviewed"},
    ).json()["commitment"]
    assert satisfied["state"] == "done"
    assert satisfied["history"][-1]["evidence"][0]["status"] == "done"
    history = client.get(f"/api/people/history?relationship_id={relationship['id']}").json()["history"]
    assert history["satisfied"] == 1
    assert history["with_evidence"] == 1
    reset_database()


def test_commitment_transition_http_is_a_parity_twin_of_mcp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Door's browser adapter lands through the same People service call."""
    owner = Principal(PrincipalKind.OWNER, "transition-owner")
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    service = PeopleService(store, setup_runner=lambda *, initialize, principal: initialize())
    client = _client(tmp_path, owner, service)
    assert client.post("/api/people/setup").status_code == 200
    relationship = client.post(
        "/api/people/relationships",
        json={"display_name": "Transition parity"},
    ).json()["relationship"]

    shared_request = client.post(
        f"/api/people/relationships/{relationship['id']}/requests",
        json={"body": "Finish parity proof", "visibility": "shared_intent"},
    ).json()["request"]
    http_commitment = client.post(
        f"/api/people/requests/{shared_request['id']}/accept",
        json={},
    ).json()["commitment"]
    mcp_request = service.create_request(owner, relationship["id"], {
        "body": "Finish MCP parity proof", "visibility": "shared_intent",
    })
    mcp_commitment = service.accept_request(owner, mcp_request["id"])

    monkeypatch.setattr(people_family, "build_people_service", lambda: service)
    monkeypatch.delenv(people_family.ACCESS_ENV, raising=False)
    mcp_result = people_family.dispatch(
        "people.commitment.transition",
        {"commitment_id": mcp_commitment["id"], "verb": "done"},
        owner,
    )
    http = client.post(
        f"/api/people/commitments/{http_commitment['id']}/transition",
        json={"verb": "done"},
    )

    assert http.status_code == 200
    assert mcp_result == {"card_id": f"people:{mcp_commitment['id']}", "verb": "done"}
    assert http.json() == {
        "transition": {"card_id": f"people:{http_commitment['id']}", "verb": "done"},
    }
    assert service.get_commitment(owner, mcp_commitment["id"])["state"] == "done"
    assert service.get_commitment(owner, http_commitment["id"])["state"] == "done"
