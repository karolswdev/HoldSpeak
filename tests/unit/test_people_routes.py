"""Authenticated HTTP contract for the encrypted People service."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.people import build_people_router


def _client(tmp_path: Path, principal: Principal) -> TestClient:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    app = FastAPI()

    @app.middleware("http")
    async def principal_state(request: Request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_people_router(WebContext(
        get_state=lambda: {},
        people_service=PeopleService(store, setup_runner=lambda *, initialize, principal: initialize()),
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
    request = client.post(f"/api/people/relationships/{relationship_id}/requests", json={"body": "A private request"})
    assert request.status_code == 201
    accepted = client.post(f"/api/people/requests/{request.json()['request']['id']}/accept", json={})
    assert accepted.status_code == 200
    detail = client.get(f"/api/people/relationships/{relationship_id}").json()["relationship"]
    assert detail["commitments"][0]["body"] == "A private request"


def test_people_routes_require_authenticated_owner(tmp_path: Path) -> None:
    client = _client(tmp_path, Principal(PrincipalKind.NONE, "none"))
    response = client.get("/api/people/readiness")
    assert response.status_code == 403
    assert response.json() == {"detail": "people_owner_required"}
