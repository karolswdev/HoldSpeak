"""Primitive Framework — Note + Agent CRUD routes and the persona-run seam.

Builds a minimal app with just `build_primitives_router` over a real tmp-path
Database (the handlers do `from ...db import get_database` at call time, so we
point the singleton at a tmp DB). The persona-run endpoint is exercised with the
intel engine stubbed so no model is loaded.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield TestClient(app)
    reset_database()


# ── Notes ──────────────────────────────────────────────────────────────────
def test_note_crud_flow(client: TestClient) -> None:
    # Empty.
    assert client.get("/api/notes").json() == {"notes": []}

    # Create.
    resp = client.post("/api/notes", json={"title": "T", "body_markdown": "B", "tags": ["a"]})
    assert resp.status_code == 201
    note = resp.json()["note"]
    nid = note["id"]
    assert note["title"] == "T" and note["tags"] == ["a"] and note["deleted"] is False

    # List + get.
    assert len(client.get("/api/notes").json()["notes"]) == 1
    assert client.get(f"/api/notes/{nid}").json()["note"]["body_markdown"] == "B"

    # Update (partial).
    upd = client.put(f"/api/notes/{nid}", json={"title": "T2"})
    assert upd.status_code == 200
    assert upd.json()["note"]["title"] == "T2"
    assert upd.json()["note"]["body_markdown"] == "B"  # unchanged

    # Delete (tombstone) -> gone from list + 404 on get.
    assert client.delete(f"/api/notes/{nid}").json() == {"success": True}
    assert client.get("/api/notes").json()["notes"] == []
    assert client.get(f"/api/notes/{nid}").status_code == 404
    assert client.delete(f"/api/notes/{nid}").status_code == 404


# ── Agents ─────────────────────────────────────────────────────────────────
def test_agent_crud_flow(client: TestClient) -> None:
    resp = client.post("/api/agents", json={
        "name": "Summarizer", "role": "assistant",
        "system_prompt": "You summarize.", "user_template": "Summarize: {input}",
        "tools": ["web"], "kb_id": "kb1",
    })
    assert resp.status_code == 201
    agent = resp.json()["agent"]
    aid = agent["id"]
    assert agent["name"] == "Summarizer" and agent["kb_id"] == "kb1"

    assert len(client.get("/api/agents").json()["agents"]) == 1

    upd = client.put(f"/api/agents/{aid}", json={"role": "expert"})
    assert upd.json()["agent"]["role"] == "expert"
    assert upd.json()["agent"]["system_prompt"] == "You summarize."  # unchanged

    assert client.delete(f"/api/agents/{aid}").json() == {"success": True}
    assert client.get(f"/api/agents/{aid}").status_code == 404


def test_agent_create_requires_name(client: TestClient) -> None:
    assert client.post("/api/agents", json={"role": "x"}).status_code == 400


# ── Run a persona ────────────────────────────────────────────────────────────
def test_run_agent_invokes_engine(client: TestClient, monkeypatch) -> None:
    aid = client.post("/api/agents", json={
        "name": "Echo", "system_prompt": "SYS", "user_template": "Q: {input}",
    }).json()["agent"]["id"]

    captured = {}

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            captured["system_prompt"] = system_prompt
            captured["user_prompt"] = user_prompt
            return "ANSWER"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel",
        lambda: _FakeIntel(),
    )

    resp = client.post(f"/api/agents/{aid}/run", json={"input": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"agent_id": aid, "output": "ANSWER", "provider": "local"}
    # The persona's system prompt + rendered template reached the engine.
    assert captured["system_prompt"] == "SYS"
    assert captured["user_prompt"] == "Q: hello"


def test_run_agent_unknown_is_404(client: TestClient) -> None:
    assert client.post("/api/agents/nope/run", json={"input": "x"}).status_code == 404


def test_run_agent_engine_error_is_502(client: TestClient, monkeypatch) -> None:
    aid = client.post("/api/agents", json={
        "name": "X", "user_template": "{input}",
    }).json()["agent"]["id"]

    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = None

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _Boom()
    )
    resp = client.post(f"/api/agents/{aid}/run", json={"input": "x"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]


# ── KBs ────────────────────────────────────────────────────────────────────
def test_kb_crud_flow(client: TestClient) -> None:
    assert client.get("/api/kbs").json() == {"kbs": []}

    resp = client.post("/api/kbs", json={"name": "Specs", "member_ids": ["note_1", "note_2"]})
    assert resp.status_code == 201
    kb = resp.json()["kb"]
    kid = kb["id"]
    assert kb["name"] == "Specs"
    assert kb["member_ids"] == ["note_1", "note_2"]
    assert kb["deleted"] is False
    # Byte-for-byte contract shape: id, name, member_ids, created_at, last_modified, deleted.
    assert set(kb) == {"id", "name", "member_ids", "created_at", "last_modified", "deleted"}

    assert len(client.get("/api/kbs").json()["kbs"]) == 1
    assert client.get(f"/api/kbs/{kid}").json()["kb"]["name"] == "Specs"

    upd = client.put(f"/api/kbs/{kid}", json={"member_ids": ["note_3"]})
    assert upd.status_code == 200
    assert upd.json()["kb"]["member_ids"] == ["note_3"]
    assert upd.json()["kb"]["name"] == "Specs"  # unchanged

    assert client.delete(f"/api/kbs/{kid}").json() == {"success": True}
    assert client.get("/api/kbs").json()["kbs"] == []
    assert client.get(f"/api/kbs/{kid}").status_code == 404
    assert client.delete(f"/api/kbs/{kid}").status_code == 404


def test_kb_create_requires_name(client: TestClient) -> None:
    assert client.post("/api/kbs", json={"member_ids": []}).status_code == 400


# ── Chains ─────────────────────────────────────────────────────────────────
def test_chain_crud_flow(client: TestClient) -> None:
    assert client.get("/api/chains").json() == {"chains": []}

    resp = client.post("/api/chains", json={"name": "Triage", "steps": ["agent_a", "agent_b"]})
    assert resp.status_code == 201
    chain = resp.json()["chain"]
    cid = chain["id"]
    assert chain["name"] == "Triage"
    assert chain["steps"] == ["agent_a", "agent_b"]
    assert set(chain) == {"id", "name", "steps", "created_at", "last_modified", "deleted"}

    assert len(client.get("/api/chains").json()["chains"]) == 1
    assert client.get(f"/api/chains/{cid}").json()["chain"]["steps"] == ["agent_a", "agent_b"]

    upd = client.put(f"/api/chains/{cid}", json={"name": "Triage v2"})
    assert upd.json()["chain"]["name"] == "Triage v2"
    assert upd.json()["chain"]["steps"] == ["agent_a", "agent_b"]  # unchanged

    assert client.delete(f"/api/chains/{cid}").json() == {"success": True}
    assert client.get(f"/api/chains/{cid}").status_code == 404
    assert client.delete(f"/api/chains/{cid}").status_code == 404


def test_chain_create_requires_name(client: TestClient) -> None:
    assert client.post("/api/chains", json={"steps": []}).status_code == 400


# ── Workflows ──────────────────────────────────────────────────────────────
def test_workflow_crud_flow(client: TestClient) -> None:
    assert client.get("/api/workflows").json() == {"workflows": []}

    resp = client.post("/api/workflows", json={
        "name": "Daily", "prompt": "summarize", "graph_json": {"nodes": [1]},
    })
    assert resp.status_code == 201
    wf = resp.json()["workflow"]
    wid = wf["id"]
    assert wf["name"] == "Daily"
    assert wf["prompt"] == "summarize"
    assert wf["graph_json"] == {"nodes": [1]}
    assert set(wf) == {"id", "name", "prompt", "graph_json", "created_at", "last_modified", "deleted"}

    assert len(client.get("/api/workflows").json()["workflows"]) == 1
    assert client.get(f"/api/workflows/{wid}").json()["workflow"]["prompt"] == "summarize"

    upd = client.put(f"/api/workflows/{wid}", json={"graph_json": {"nodes": [2, 3]}})
    assert upd.json()["workflow"]["graph_json"] == {"nodes": [2, 3]}
    assert upd.json()["workflow"]["prompt"] == "summarize"  # unchanged

    assert client.delete(f"/api/workflows/{wid}").json() == {"success": True}
    assert client.get(f"/api/workflows/{wid}").status_code == 404
    assert client.delete(f"/api/workflows/{wid}").status_code == 404


def test_workflow_create_requires_name(client: TestClient) -> None:
    assert client.post("/api/workflows", json={"prompt": "x"}).status_code == 400


# ── Directories + membership ─────────────────────────────────────────────────
def test_directory_crud_flow(client: TestClient) -> None:
    assert client.get("/api/directories").json() == {"directories": []}

    # Create requires a name.
    assert client.post("/api/directories", json={}).status_code == 400

    resp = client.post("/api/directories", json={"name": "Inbox"})
    assert resp.status_code == 201
    d = resp.json()["directory"]
    did = d["id"]
    assert d["name"] == "Inbox" and d["parent_id"] is None and d["deleted"] is False

    # Nested child.
    child = client.post("/api/directories", json={"name": "Sub", "parent_id": did}).json()["directory"]
    assert child["parent_id"] == did

    # List + get (get carries members, empty here).
    assert len(client.get("/api/directories").json()["directories"]) == 2
    got = client.get(f"/api/directories/{did}").json()
    assert got["directory"]["name"] == "Inbox" and got["members"] == []

    # Update (partial).
    upd = client.put(f"/api/directories/{did}", json={"name": "Inbox 2"})
    assert upd.status_code == 200 and upd.json()["directory"]["name"] == "Inbox 2"

    # Delete (tombstone).
    assert client.delete(f"/api/directories/{did}").json() == {"success": True}
    assert client.get(f"/api/directories/{did}").status_code == 404
    assert client.delete(f"/api/directories/{did}").status_code == 404


def test_directory_membership_file_and_unfile(client: TestClient) -> None:
    did = client.post("/api/directories", json={"name": "Bag"}).json()["directory"]["id"]

    # File a primitive.
    filed = client.put(f"/api/directories/{did}/members/note_42")
    assert filed.status_code == 200
    assert filed.json()["membership"]["primitive_id"] == "note_42"
    assert filed.json()["membership"]["directory_id"] == did

    # Membership is readable both via the directory GET and the members list.
    members = client.get(f"/api/directories/{did}/members").json()["members"]
    assert [m["primitive_id"] for m in members] == ["note_42"]
    assert client.get(f"/api/directories/{did}").json()["members"][0]["primitive_id"] == "note_42"

    # Filing into an unknown directory 404s.
    assert client.put("/api/directories/nope/members/x").status_code == 404

    # Unfile (tombstone) -> gone from the list.
    assert client.delete(f"/api/directories/{did}/members/note_42").json() == {"success": True}
    assert client.get(f"/api/directories/{did}/members").json()["members"] == []
    # Unfiling again (already gone) 404s.
    assert client.delete(f"/api/directories/{did}/members/note_42").status_code == 404


def test_directory_member_listing_404_for_unknown_directory(client: TestClient) -> None:
    assert client.get("/api/directories/ghost/members").status_code == 404
