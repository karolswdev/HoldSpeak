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
    # One done receipt (2026-11-08): the route answers what MCP answers, in
    # the shape /api/follow-through/complete answers (card_id, status, done_at).
    shape = ("card_id", "verb", "status")
    assert {k: mcp_result[k] for k in shape} == {
        "card_id": f"people:{mcp_commitment['id']}", "verb": "done", "status": "done"}
    assert {k: http.json()[k] for k in shape} == {
        "card_id": f"people:{http_commitment['id']}", "verb": "done", "status": "done"}
    assert set(http.json()) == set(mcp_result) == {"card_id", "verb", "status", "done_at"}
    assert http.json()["done_at"] and mcp_result["done_at"]
    assert service.get_commitment(owner, mcp_commitment["id"])["state"] == "done"
    assert service.get_commitment(owner, http_commitment["id"])["state"] == "done"


def test_philo17_owed_route_records_what_they_owe_you(tmp_path: Path) -> None:
    owner = Principal(PrincipalKind.OWNER, "route-owner")
    client = _client(tmp_path, owner)
    client.post("/api/people/setup")
    rid = client.post("/api/people/relationships", json={"display_name": "Maya Chen"}).json()["relationship"]["id"]
    owed = client.post(f"/api/people/relationships/{rid}/owed", json={"body": "Send me the API migration estimate"})
    assert owed.status_code == 201
    assert owed.json()["commitment"]["direction"] == "report_owes"
    detail = client.get(f"/api/people/relationships/{rid}").json()["relationship"]
    assert detail["commitments"] == []
    assert [item["body"] for item in detail["owed_to_you"]] == ["Send me the API migration estimate"]
    done = client.post(f"/api/people/commitments/{owed.json()['commitment']['id']}/transition", json={"verb": "done"})
    assert done.status_code == 200
    assert client.post(f"/api/people/relationships/{rid}/owed", json={"body": ""}).status_code in {400, 422}


def test_agenda_item_remove_route_takes_it_off_the_brief(tmp_path: Path) -> None:
    """PHILO-17: the owner removes an agenda item through the web route; it
    leaves the brief's open agenda (TO RAISE); a second remove is refused,
    an unknown state is refused, and a non-owner cannot write."""
    owner = Principal(PrincipalKind.OWNER, "route-owner")
    service = PeopleService(
        EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore()),
        setup_runner=lambda *, initialize, principal: initialize(),
    )
    client = _client(tmp_path, owner, service)
    assert client.post("/api/people/setup").json()["state"] == "ready"
    rid = client.post("/api/people/relationships", json={"display_name": "Agenda Sentinel"}).json()["relationship"]["id"]
    session = client.post(f"/api/people/relationships/{rid}/one-on-ones", json={}).json()["one_on_one"]["id"]
    keep = client.post(f"/api/people/one-on-ones/{session}/agenda", json={"body": "Keep this"}).json()["agenda_item"]
    drop = client.post(f"/api/people/one-on-ones/{session}/agenda", json={"body": "Drop this"}).json()["agenda_item"]

    assert client.post(f"/api/people/agenda/{drop['id']}/transition", json={"to": "archived"}).status_code == 400
    removed = client.post(f"/api/people/agenda/{drop['id']}/transition", json={"to": "removed"})
    assert removed.status_code == 200, removed.text
    assert removed.json()["agenda_item"]["state"] == "removed"

    brief = client.get(f"/api/people/relationships/{rid}/brief").json()["brief"]
    assert [item["body"] for item in brief["agenda_items"]] == ["Keep this"]
    assert client.post(f"/api/people/agenda/{drop['id']}/transition", json={"to": "removed"}).status_code == 400
    assert client.post("/api/people/agenda/nope/transition", json={"to": "removed"}).status_code == 404
    assert keep["state"] == "open"

    agent = _client(tmp_path, Principal(PrincipalKind.AGENT, "route-agent"), service)
    refused = agent.post(f"/api/people/agenda/{keep['id']}/transition", json={"to": "removed"})
    assert refused.status_code == 403


def test_archive_uses_the_composed_store_off_loop_and_keeps_related_work(tmp_path, monkeypatch):
    import threading
    from holdspeak import operations

    owner = Principal(PrincipalKind.OWNER, "archive-owner")
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    service = PeopleService(store)
    relationship = service.create_relationship(owner, {"display_name": "Archive Sentinel"})
    note = service.create_note(owner, relationship["id"], {"body": "Keep this", "topic": "Context"})
    client = _client(tmp_path, owner, service)
    loop_threads, write_threads = [], []

    @client.app.get("/loop-thread")
    async def loop_thread():
        loop_threads.append(threading.get_ident())
        return {}

    original = store.archive

    def archive(record_id):
        write_threads.append(threading.get_ident())
        return original(record_id)

    monkeypatch.setattr(store, "archive", archive)
    with client:
        client.get("/loop-thread")
        for _ in range(2):  # retry is the same durable archived person
            reply = client.post(f"/api/people/relationships/{relationship['id']}/archive")
            assert reply.status_code == 200, reply.text
            assert reply.json()["relationship"]["state"] == "archived"
    assert write_threads and set(write_threads).isdisjoint(loop_threads)
    assert store.get(relationship["id"])["lifecycle"] == "archived"
    assert store.get(note["id"])["body"] == "Keep this"
    assert service.list_relationships(owner) == []
    assert service.list_relationships(owner, include_archived=True)[0]["id"] == relationship["id"]
    agent = _client(tmp_path, Principal(PrincipalKind.AGENT, "worker"), service)
    refused = agent.post(f"/api/people/relationships/{relationship['id']}/archive")
    assert refused.status_code == 403
    assert refused.json() == {"detail": "people_owner_required"}
    registry = operations.bind_available({"people_service": service})
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(Principal(PrincipalKind.AGENT, "worker"), "people.relationship.archive",
                        {"relationship_id": relationship["id"]})


@pytest.mark.parametrize("state", ["unconfigured", "locked", "key_unavailable", "no_key_store",
                                  "corrupt", "unsafe_permissions", "unavailable"])
def test_archive_names_store_readiness_refusals_without_content(tmp_path, monkeypatch, state):
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    service = PeopleService(store)
    monkeypatch.setattr(store, "readiness", lambda: state)
    client = _client(tmp_path, Principal(PrincipalKind.OWNER, "owner"), service)
    refused = client.post("/api/people/relationships/missing/archive")
    assert refused.status_code == 503
    assert refused.json() == {"detail": f"people_store_{state}"}


def test_archive_names_database_lock_and_retry_keeps_the_person(tmp_path, monkeypatch):
    import sqlite3
    from contextlib import closing

    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    owner = Principal(PrincipalKind.OWNER, "owner")
    service = PeopleService(store)
    person = service.create_relationship(owner, {"display_name": "Lock Sentinel"})
    client = _client(tmp_path, owner, service)
    connect = sqlite3.connect

    def short_wait(*args, **kwargs):
        return connect(*args, **{**kwargs, "timeout": 0.05})

    monkeypatch.setattr(sqlite3, "connect", short_wait)
    with closing(connect(store.path)) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        refused = client.post(f"/api/people/relationships/{person['id']}/archive")
        assert refused.status_code == 503
        assert refused.json() == {"detail": "people_store_busy"}
        assert store.get(person["id"])["state"] == "active"
        blocker.rollback()
    reply = client.post(f"/api/people/relationships/{person['id']}/archive")
    assert reply.status_code == 200
    assert store.get(person["id"])["state"] == "archived"


def test_people_router_cannot_mount_without_the_store_service():
    with pytest.raises(RuntimeError, match="People service is not configured"):
        build_people_router(WebContext(get_state=dict))


def test_archive_failure_diagnostics_stay_off_loop_and_hide_driver_content(tmp_path, monkeypatch):
    import threading

    owner = Principal(PrincipalKind.OWNER, "owner")
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    service = PeopleService(store)
    person = service.create_relationship(owner, {"display_name": "Private Sentinel"})
    client = _client(tmp_path, owner, service)
    loop_threads, readiness_threads = [], []
    readiness = store.readiness

    @client.app.get("/loop-thread")
    async def loop_thread():
        loop_threads.append(threading.get_ident())
        return {}

    def checked_readiness():
        readiness_threads.append(threading.get_ident())
        return readiness()

    def failed_write(record_id):
        raise RuntimeError("Private Sentinel in driver failure")

    monkeypatch.setattr(store, "readiness", checked_readiness)
    monkeypatch.setattr(store, "archive", failed_write)
    with client:
        client.get("/loop-thread")
        refused = client.post(f"/api/people/relationships/{person['id']}/archive")
    assert refused.status_code == 503
    assert readiness_threads and set(readiness_threads).isdisjoint(loop_threads)
    assert refused.json() == {"detail": "people_store_write_failed"}
    assert store.get(person["id"])["state"] == "active"
