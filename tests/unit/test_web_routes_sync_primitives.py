"""Primitive Framework — the desk primitives ride /api/sync/pull|push.

Notes, KBs, Agents, Chains and Workflows sync alongside meetings/artifacts on the
same `{meta:{id, kind, last_modified, deleted}, value}` envelope. Push merges them
into the live store with last-write-wins on `last_modified` and tombstone deletes.
Uses a real tmp-path Database so the merge is real.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_sync_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_pull_includes_all_primitive_kinds(env) -> None:
    db, client = env
    db.notes.upsert(note_id="n1", title="N")
    db.kbs.upsert(kb_id="kb1", name="K")
    db.agents.upsert(agent_id="a1", name="A")
    db.chains.upsert(chain_id="c1", name="C", steps=["a1"])
    db.workflows.upsert(workflow_id="w1", name="W", prompt="p")

    body = client.get("/api/sync/pull").json()
    for bucket, kind in [("notes", "note"), ("kbs", "kb"), ("agents", "agent"),
                         ("chains", "chain"), ("workflows", "workflow")]:
        assert len(body[bucket]) == 1, bucket
        rec = body[bucket][0]
        assert rec["meta"]["kind"] == kind
        assert rec["meta"]["last_modified"].endswith("Z")
        assert rec["meta"]["deleted"] is False
        assert "value" in rec


def test_push_merges_primitives_into_store(env) -> None:
    db, client = env
    changeset = {
        "notes": [{
            "meta": {"id": "n1", "kind": "note",
                     "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
            "value": {"title": "Pushed", "body_markdown": "x", "tags": ["t"]},
        }],
        "agents": [{
            "meta": {"id": "a1", "kind": "agent",
                     "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
            "value": {"name": "Persona", "system_prompt": "S", "user_template": "U"},
        }],
    }
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert resp.json()["received"]["notes"] == 1
    assert resp.json()["received"]["agents"] == 1

    note = db.notes.get("n1")
    assert note is not None and note.title == "Pushed" and note.tags == ["t"]
    agent = db.agents.get("a1")
    assert agent is not None and agent.name == "Persona"


def test_push_last_write_wins(env) -> None:
    db, client = env
    # Stored copy is newer than the incoming push.
    db.notes.upsert(note_id="n1", title="Newer", last_modified="2031-01-01T00:00:00Z")
    changeset = {"notes": [{
        "meta": {"id": "n1", "kind": "note",
                 "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
        "value": {"title": "Older"},
    }]}
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    # Skipped: stored stays "Newer", merge count is 0.
    assert resp.json()["received"]["notes"] == 0
    assert db.notes.get("n1").title == "Newer"


def test_push_tombstone_deletes(env) -> None:
    db, client = env
    db.notes.upsert(note_id="n1", title="Alive", last_modified="2030-01-01T00:00:00Z")
    changeset = {"notes": [{
        "meta": {"id": "n1", "kind": "note",
                 "last_modified": "2031-01-01T00:00:00Z", "deleted": True},
        "value": {"title": "Alive"},
    }]}
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert db.notes.get("n1") is None  # tombstoned (hidden)
    assert db.notes.get("n1", include_deleted=True).deleted is True


def test_push_then_pull_round_trip(env) -> None:
    """The cross-device sync contract: push a note + agent + kb, pull them back
    with the right kind/last_modified, then a tombstone push removes them from a
    subsequent non-deleted pull (but the tombstone itself still propagates)."""
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    changeset = {
        "notes": [{
            "meta": {"id": "n1", "kind": "note", "last_modified": lm, "deleted": False},
            "value": {"title": "Roundtrip", "body_markdown": "B", "tags": ["x"]},
        }],
        "agents": [{
            "meta": {"id": "a1", "kind": "agent", "last_modified": lm, "deleted": False},
            "value": {"name": "Persona", "system_prompt": "S", "user_template": "U"},
        }],
        "kbs": [{
            "meta": {"id": "kb1", "kind": "kb", "last_modified": lm, "deleted": False},
            "value": {"name": "Bag", "member_ids": ["n1"]},
        }],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200
    rcv = push.json()["received"]
    assert rcv["notes"] == 1 and rcv["agents"] == 1 and rcv["kbs"] == 1

    # Pull brings the three primitives back with correct meta.kind + last_modified.
    pulled = client.get("/api/sync/pull").json()
    by_kind = {
        "note": pulled["notes"][0], "agent": pulled["agents"][0], "kb": pulled["kbs"][0],
    }
    assert by_kind["note"]["meta"]["id"] == "n1"
    assert by_kind["note"]["meta"]["kind"] == "note"
    assert by_kind["note"]["meta"]["last_modified"] == lm
    assert by_kind["note"]["meta"]["deleted"] is False
    assert by_kind["note"]["value"]["title"] == "Roundtrip"
    assert by_kind["agent"]["meta"]["kind"] == "agent"
    assert by_kind["agent"]["meta"]["last_modified"] == lm
    assert by_kind["agent"]["value"]["name"] == "Persona"
    assert by_kind["kb"]["meta"]["kind"] == "kb"
    assert by_kind["kb"]["meta"]["last_modified"] == lm
    assert by_kind["kb"]["value"]["member_ids"] == ["n1"]

    # A tombstone push (newer last_modified) removes them from a non-deleted view.
    lm2 = "2030-06-26T13:00:00Z"
    tomb = {
        "notes": [{"meta": {"id": "n1", "kind": "note", "last_modified": lm2,
                            "deleted": True}, "value": {"title": "Roundtrip"}}],
        "agents": [{"meta": {"id": "a1", "kind": "agent", "last_modified": lm2,
                             "deleted": True}, "value": {"name": "Persona"}}],
        "kbs": [{"meta": {"id": "kb1", "kind": "kb", "last_modified": lm2,
                          "deleted": True}, "value": {"name": "Bag"}}],
    }
    assert client.post("/api/sync/push", json=tomb).status_code == 200

    # The live store hides them; the tombstone still rides the pull (deleted=True).
    assert db.notes.get("n1") is None
    assert db.agents.get("a1") is None
    assert db.kbs.get("kb1") is None
    repulled = client.get("/api/sync/pull").json()
    assert repulled["notes"][0]["meta"]["deleted"] is True
    assert repulled["agents"][0]["meta"]["deleted"] is True
    assert repulled["kbs"][0]["meta"]["deleted"] is True


def test_push_rejects_unknown_kind(env) -> None:
    db, client = env
    bad = {"notes": [{
        "meta": {"id": "n1", "kind": "bogus", "last_modified": "x", "deleted": False},
        "value": {},
    }]}
    resp = client.post("/api/sync/push", json=bad)
    assert resp.status_code == 422
    assert db.notes.get("n1") is None
