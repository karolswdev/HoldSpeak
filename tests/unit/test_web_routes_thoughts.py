from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router
from holdspeak.principals import Principal, PrincipalKind


def test_thought_routes_keep_raw_out_of_normal_read_and_require_cas(tmp_path, monkeypatch):
    db = Database(tmp_path / "routes.db")
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)
    created = client.post("/api/thoughts", json={"request_id": "route-1", "raw_text": "private raw", "source": {"kind": "typed"}})
    assert created.status_code == 201
    thought = created.json()["thought"]
    fetched = client.get(f"/api/thoughts/{thought['id']}").json()["thought"]
    assert "raw_text" not in fetched
    assert client.get(f"/api/thoughts/{thought['id']}/original").json()["thought"]["raw_text"] == "private raw"
    refused = client.put(f"/api/notes/{thought['working_note']['id']}", json={"title": "no CAS"})
    assert refused.status_code == 409 and refused.json()["error"] == "thought_expected_revision_required"
    edited = client.patch(f"/api/thoughts/{thought['id']}/working", json={"expected_aggregate_revision": 1, "expected_working_revision": 1, "title": "edited"})
    assert edited.status_code == 200 and edited.json()["thought"]["working_revision"] == 2
    note = client.put(f"/api/notes/{thought['working_note']['id']}", json={"expected_aggregate_revision": 2, "expected_working_revision": 2, "body_markdown": "via note"})
    assert note.status_code == 200
    assert {"state", "aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision"} <= note.json()["note"].keys()
    deleted = client.request("DELETE", f"/api/notes/{thought['working_note']['id']}", json={"expected_aggregate_revision": 3, "expected_lifecycle_revision": 1})
    assert deleted.status_code == 200
    assert {"state", "aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision"} <= deleted.json()["note"].keys()


def test_thought_routes_deny_absent_and_agent_principals(tmp_path, monkeypatch):
    db = Database(tmp_path / "auth.db")
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    assert TestClient(app).get("/api/thoughts").status_code == 422
    agent = FastAPI()
    @agent.middleware("http")
    async def as_agent(request, call_next):
        request.state.principal = Principal(PrincipalKind.AGENT, "not-owner")
        return await call_next(request)
    agent.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    assert TestClient(agent).post("/api/thoughts", json={"request_id": "x", "raw_text": "raw"}).status_code == 422


def test_thought_product_reads_deny_node_principal(tmp_path, monkeypatch):
    db = Database(tmp_path / "node-auth.db")
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    owner = FastAPI()
    @owner.middleware("http")
    async def owner_identity(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "owner")
        return await call_next(request)
    owner.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    thought = TestClient(owner).post("/api/thoughts", json={"request_id":"node-read","raw_text":"raw"}).json()["thought"]
    node = FastAPI()
    @node.middleware("http")
    async def node_identity(request, call_next):
        request.state.principal = Principal(PrincipalKind.NODE, "peer")
        return await call_next(request)
    node.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(node)
    assert client.post("/api/thoughts", json={"request_id": "node-create", "raw_text": "no"}).status_code == 422
    assert client.post("/api/thoughts/adopt", json={"request_id": "node-adopt", "note_id": thought["working_note"]["id"], "expected_source_content_sha256": "x", "expected_source_last_modified": "x"}).status_code == 422
    assert client.get(f"/api/thoughts/{thought['id']}").status_code == 422
    assert client.get("/api/thoughts?limit=1").status_code == 422
    assert client.post(f"/api/thoughts/{thought['id']}/reconcile", json={"expected_aggregate_revision":1}).status_code == 422
    # Product commands and generic owned-Note writes are owner-only. A paired
    # sync principal may install a signed ledger, but never impersonate this UI.
    assert client.patch(f"/api/thoughts/{thought['id']}/working", json={"expected_aggregate_revision": 1, "expected_working_revision": 1, "body_markdown": "no"}).status_code == 422
    assert client.post(f"/api/thoughts/{thought['id']}/complete", json={"request_id": "node", "expected_aggregate_revision": 1, "expected_lifecycle_revision": 1}).status_code == 422
    assert client.post(f"/api/thoughts/{thought['id']}/resume", json={"expected_aggregate_revision": 1, "expected_lifecycle_revision": 1}).status_code == 422
    assert client.put(f"/api/notes/{thought['working_note']['id']}", json={"expected_aggregate_revision": 1, "expected_working_revision": 1, "body_markdown": "no"}).status_code == 422
    assert client.request("DELETE", f"/api/notes/{thought['working_note']['id']}", json={"expected_aggregate_revision": 1, "expected_lifecycle_revision": 1}).status_code == 422


def test_thought_list_is_paged_private_and_reconcile_requires_cursor(tmp_path, monkeypatch):
    db = Database(tmp_path / "page.db")
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)
    thought = client.post("/api/thoughts", json={"request_id": "page-1", "raw_text": "raw", "source": {"kind": "typed"}}).json()["thought"]
    page = client.get("/api/thoughts?limit=1")
    assert page.status_code == 200 and len(page.json()["items"]) == 1
    item = page.json()["items"][0]
    assert "body_markdown" not in item and "raw_text" not in item and "source" not in item
    assert client.get("/api/thoughts?limit=51").status_code == 422
    assert client.post(f"/api/thoughts/{thought['id']}/reconcile", json={}).status_code == 409


def test_note_adoption_routes_are_owner_only_and_return_the_same_note(tmp_path, monkeypatch):
    db = Database(tmp_path / "adopt-routes.db")
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    db.notes.upsert(note_id="n1", title="Existing", body_markdown="exact", tags=["tag"])
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)
    source = client.get("/api/thoughts/for-note/n1")
    assert source.status_code == 200 and source.json()["ownership"] == "ordinary"
    precondition = source.json()["source_precondition"]
    adopted = client.post("/api/thoughts/adopt", json={"request_id": "adopt-route", "note_id": "n1",
        "expected_source_content_sha256": precondition["content_sha256"], "expected_source_last_modified": precondition["last_modified"]})
    assert adopted.status_code == 201
    thought = adopted.json()["thought"]
    assert thought["working_note"]["id"] == "n1"
    assert client.get("/api/thoughts/for-note/n1").json()["ownership"] == "thought"
    assert client.get(f"/api/thoughts/{thought['id']}/original").json()["thought"]["raw_text"] == "exact"
