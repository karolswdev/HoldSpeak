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
    db.recipes.upsert(recipe_id="a1", name="A")
    db.chains.upsert(chain_id="c1", name="C", steps=["a1"])
    db.workflows.upsert(workflow_id="w1", name="W", prompt="p")

    body = client.get("/api/sync/pull").json()
    for bucket, kind in [("notes", "note"), ("kbs", "kb"), ("recipes", "recipe"),
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
        "recipes": [{
            "meta": {"id": "a1", "kind": "recipe",
                     "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
            "value": {"name": "Persona", "system_prompt": "S", "user_template": "U"},
        }],
    }
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert resp.json()["received"]["notes"] == 1
    assert resp.json()["received"]["recipes"] == 1

    note = db.notes.get("n1")
    assert note is not None and note.title == "Pushed" and note.tags == ["t"]
    agent = db.recipes.get("a1")
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
        "recipes": [{
            "meta": {"id": "a1", "kind": "recipe", "last_modified": lm, "deleted": False},
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
    assert rcv["notes"] == 1 and rcv["recipes"] == 1 and rcv["kbs"] == 1

    # Pull brings the three primitives back with correct meta.kind + last_modified.
    pulled = client.get("/api/sync/pull").json()
    by_kind = {
        "note": pulled["notes"][0], "recipe": pulled["recipes"][0], "kb": pulled["kbs"][0],
    }
    assert by_kind["note"]["meta"]["id"] == "n1"
    assert by_kind["note"]["meta"]["kind"] == "note"
    assert by_kind["note"]["meta"]["last_modified"] == lm
    assert by_kind["note"]["meta"]["deleted"] is False
    assert by_kind["note"]["value"]["title"] == "Roundtrip"
    assert by_kind["recipe"]["meta"]["kind"] == "recipe"
    assert by_kind["recipe"]["meta"]["last_modified"] == lm
    assert by_kind["recipe"]["value"]["name"] == "Persona"
    assert by_kind["kb"]["meta"]["kind"] == "kb"
    assert by_kind["kb"]["meta"]["last_modified"] == lm
    assert by_kind["kb"]["value"]["member_ids"] == ["n1"]

    # A tombstone push (newer last_modified) removes them from a non-deleted view.
    lm2 = "2030-06-26T13:00:00Z"
    tomb = {
        "notes": [{"meta": {"id": "n1", "kind": "note", "last_modified": lm2,
                            "deleted": True}, "value": {"title": "Roundtrip"}}],
        "recipes": [{"meta": {"id": "a1", "kind": "recipe", "last_modified": lm2,
                             "deleted": True}, "value": {"name": "Persona"}}],
        "kbs": [{"meta": {"id": "kb1", "kind": "kb", "last_modified": lm2,
                          "deleted": True}, "value": {"name": "Bag"}}],
    }
    assert client.post("/api/sync/push", json=tomb).status_code == 200

    # The live store hides them; the tombstone still rides the pull (deleted=True).
    assert db.notes.get("n1") is None
    assert db.recipes.get("a1") is None
    assert db.kbs.get("kb1") is None
    repulled = client.get("/api/sync/pull").json()
    assert repulled["notes"][0]["meta"]["deleted"] is True
    assert repulled["recipes"][0]["meta"]["deleted"] is True
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


# ── Directory + membership sync ──────────────────────────────────────────────
def test_pull_includes_directories_and_memberships(env) -> None:
    db, client = env
    db.directories.upsert(directory_id="d1", name="Root")
    db.directory_memberships.upsert(primitive_id="note_1", directory_id="d1")

    body = client.get("/api/sync/pull").json()
    assert len(body["directories"]) == 1
    drec = body["directories"][0]
    assert drec["meta"]["kind"] == "directory"
    assert drec["meta"]["id"] == "d1"
    assert drec["meta"]["last_modified"].endswith("Z")
    assert drec["value"]["name"] == "Root"

    assert len(body["directory_memberships"]) == 1
    mrec = body["directory_memberships"][0]
    assert mrec["meta"]["kind"] == "directory_membership"
    # The membership's synced id is the primitive id (the map key).
    assert mrec["meta"]["id"] == "note_1"
    assert mrec["value"]["directory_id"] == "d1"


def test_directory_membership_push_pull_round_trip_and_tombstone(env) -> None:
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    changeset = {
        "directories": [{
            "meta": {"id": "d1", "kind": "directory", "last_modified": lm, "deleted": False},
            "value": {"name": "Synced", "parent_id": None},
        }],
        "directory_memberships": [{
            "meta": {"id": "note_1", "kind": "directory_membership",
                     "last_modified": lm, "deleted": False},
            "value": {"primitive_id": "note_1", "directory_id": "d1"},
        }],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200
    rcv = push.json()["received"]
    assert rcv["directories"] == 1 and rcv["directory_memberships"] == 1

    # Merged into the live store.
    assert db.directories.get("d1").name == "Synced"
    m = db.directory_memberships.get("note_1")
    assert m is not None and m.directory_id == "d1"

    # Pull brings them back with the right kind/id.
    pulled = client.get("/api/sync/pull").json()
    assert pulled["directories"][0]["meta"]["id"] == "d1"
    assert pulled["directory_memberships"][0]["meta"]["id"] == "note_1"
    assert pulled["directory_memberships"][0]["value"]["directory_id"] == "d1"

    # A tombstone push (newer last_modified) unfiles + removes the directory.
    lm2 = "2030-06-26T13:00:00Z"
    tomb = {
        "directories": [{"meta": {"id": "d1", "kind": "directory",
                                  "last_modified": lm2, "deleted": True},
                         "value": {"name": "Synced"}}],
        "directory_memberships": [{"meta": {"id": "note_1", "kind": "directory_membership",
                                            "last_modified": lm2, "deleted": True},
                                   "value": {"primitive_id": "note_1", "directory_id": "d1"}}],
    }
    assert client.post("/api/sync/push", json=tomb).status_code == 200
    assert db.directories.get("d1") is None
    assert db.directory_memberships.get("note_1") is None

    # The tombstones still ride a subsequent pull (so peers learn of the unfile).
    repulled = client.get("/api/sync/pull").json()
    assert repulled["directories"][0]["meta"]["deleted"] is True
    assert repulled["directory_memberships"][0]["meta"]["deleted"] is True


# ── Chain + workflow sync (HSM-23-04: the last two matrix rows) ──────────────
# Chain and workflow ride the generic _MERGEABLE push path; until Phase 23 they
# were the only kinds with pull-serialization coverage but no push→pull lock of
# their own. Same lock as every other kind: round-trip, LWW, tombstone.
def test_chain_and_workflow_push_pull_round_trip_and_tombstone(env) -> None:
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    # HSM-22-04: a REAL canonical graph (the shape linearize() runs), not the old
    # placeholder that only byte-survived — sync survival AND runnability are the
    # same wire now.
    graph = {
        "id": "wf-rt-1", "name": "Pipeline graph", "entry": "e1",
        "nodes": [
            {"id": "e1", "kind": {"entry": {}}},
            {"id": "n1", "kind": {"summarize": {}},
             "runs_on": "endpoint", "failure_policy": "skip"},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "e1", "name": "then"}, "to": "n1"},
            {"from": {"node": "n1", "name": "then"}, "to": "out"},
        ],
        "data_edges": [],
    }
    changeset = {
        "chains": [{
            "meta": {"id": "c1", "kind": "chain", "last_modified": lm, "deleted": False},
            "value": {"name": "Pipeline", "steps": ["a1", "a2"]},
        }],
        "workflows": [{
            "meta": {"id": "w1", "kind": "workflow", "last_modified": lm, "deleted": False},
            "value": {"name": "Blueprint", "prompt": "run it", "graph_json": graph},
        }],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200
    rcv = push.json()["received"]
    assert rcv["chains"] == 1 and rcv["workflows"] == 1

    # Merged into the live store, ordered steps + the graph intact.
    chain = db.chains.get("c1")
    assert chain is not None and chain.name == "Pipeline" and chain.steps == ["a1", "a2"]
    wf = db.workflows.get("w1")
    assert wf is not None and wf.prompt == "run it" and wf.graph_json == graph

    # Pull brings them back with the right kind/last_modified, payloads faithful —
    # the graph_json (the Phase-22 travelling graph) must survive byte-faithful.
    pulled = client.get("/api/sync/pull").json()
    crec = pulled["chains"][0]
    assert crec["meta"] == {"id": "c1", "kind": "chain", "last_modified": lm, "deleted": False}
    assert crec["value"]["steps"] == ["a1", "a2"]
    wrec = pulled["workflows"][0]
    assert wrec["meta"] == {"id": "w1", "kind": "workflow", "last_modified": lm, "deleted": False}
    assert wrec["value"]["graph_json"] == graph

    # A tombstone push (newer last_modified) hides both; the tombstones still ride
    # a subsequent pull with no payload (the §12 rule: value is null when deleted).
    lm2 = "2030-06-26T13:00:00Z"
    tomb = {
        "chains": [{"meta": {"id": "c1", "kind": "chain", "last_modified": lm2,
                             "deleted": True}, "value": None}],
        "workflows": [{"meta": {"id": "w1", "kind": "workflow", "last_modified": lm2,
                                "deleted": True}, "value": None}],
    }
    assert client.post("/api/sync/push", json=tomb).status_code == 200
    assert db.chains.get("c1") is None
    assert db.workflows.get("w1") is None
    repulled = client.get("/api/sync/pull").json()
    assert repulled["chains"][0]["meta"]["deleted"] is True
    assert repulled["chains"][0]["value"] is None
    assert repulled["workflows"][0]["meta"]["deleted"] is True
    assert repulled["workflows"][0]["value"] is None


def test_chain_and_workflow_push_last_write_wins(env) -> None:
    db, client = env
    # Stored copies are newer than the incoming push.
    db.chains.upsert(chain_id="c1", name="Newer", steps=["a9"],
                     last_modified="2031-01-01T00:00:00Z")
    db.workflows.upsert(workflow_id="w1", name="Newer", prompt="keep",
                        last_modified="2031-01-01T00:00:00Z")
    changeset = {
        "chains": [{
            "meta": {"id": "c1", "kind": "chain",
                     "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
            "value": {"name": "Older", "steps": ["a1"]},
        }],
        "workflows": [{
            "meta": {"id": "w1", "kind": "workflow",
                     "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
            "value": {"name": "Older", "prompt": "clobber"},
        }],
    }
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert resp.json()["received"]["chains"] == 0
    assert resp.json()["received"]["workflows"] == 0
    assert db.chains.get("c1").name == "Newer" and db.chains.get("c1").steps == ["a9"]
    assert db.workflows.get("w1").prompt == "keep"


def test_directory_membership_push_last_write_wins(env) -> None:
    db, client = env
    # Stored copy is newer.
    db.directory_memberships.upsert(
        primitive_id="note_1", directory_id="d_new", last_modified="2031-01-01T00:00:00Z"
    )
    changeset = {"directory_memberships": [{
        "meta": {"id": "note_1", "kind": "directory_membership",
                 "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
        "value": {"primitive_id": "note_1", "directory_id": "d_old"},
    }]}
    resp = client.post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert resp.json()["received"]["directory_memberships"] == 0
    assert db.directory_memberships.get("note_1").directory_id == "d_new"
