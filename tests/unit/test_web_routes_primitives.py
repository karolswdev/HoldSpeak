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
    assert body == {
        "agent_id": aid,
        "output": "ANSWER",
        "provider": "local",
        "sources": [{"source_type": "agent", "source_ref": aid}],
    }
    # The persona's system prompt + rendered template reached the engine.
    assert captured["system_prompt"] == "SYS"
    assert captured["user_prompt"] == "Q: hello"


def test_run_agent_includes_input_source(client: TestClient, monkeypatch) -> None:
    """A caller-provided `source_ref` is recorded as an `input` lineage source."""
    aid = client.post("/api/agents", json={
        "name": "Echo", "user_template": "{input}",
    }).json()["agent"]["id"]

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            return "OUT"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )
    resp = client.post(
        f"/api/agents/{aid}/run", json={"input": "x", "source_ref": "meeting_7"}
    )
    assert resp.json()["sources"] == [
        {"source_type": "agent", "source_ref": aid},
        {"source_type": "input", "source_ref": "meeting_7"},
    ]


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


# ── Run a chain (crew) ───────────────────────────────────────────────────────
def _make_agent(client: TestClient, name: str, template: str) -> str:
    return client.post("/api/agents", json={
        "name": name, "system_prompt": f"SYS-{name}", "user_template": template,
    }).json()["agent"]["id"]


def test_run_chain_threads_steps(client: TestClient, monkeypatch) -> None:
    a1 = _make_agent(client, "A1", "step1: {input}")
    a2 = _make_agent(client, "A2", "step2: {input}")
    cid = client.post("/api/chains", json={"name": "C", "steps": [a1, a2]}).json()["chain"]["id"]

    calls = []

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            calls.append((system_prompt, user_prompt))
            return f"out({user_prompt})"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )

    resp = client.post(f"/api/chains/{cid}/run", json={"input": "hello"})
    assert resp.status_code == 200
    body = resp.json()

    # Step 1 ran on the request input; step 2 ran on step 1's output (threaded).
    assert calls[0] == ("SYS-A1", "step1: hello")
    assert calls[1] == ("SYS-A2", "step2: out(step1: hello)")

    assert body["chain_id"] == cid
    assert [s["agent_id"] for s in body["steps"]] == [a1, a2]
    assert body["steps"][0]["output"] == "out(step1: hello)"
    assert body["steps"][0]["provider"] == "local"
    # Chain output is the last step's output.
    assert body["output"] == body["steps"][-1]["output"] == "out(step2: out(step1: hello))"
    # Top-level provider = the last step's provider (kills the "provider unknown" badge).
    assert body["provider"] == "local"
    # Provenance: the chain plus each step's agent.
    assert body["sources"] == [
        {"source_type": "chain", "source_ref": cid},
        {"source_type": "agent", "source_ref": a1},
        {"source_type": "agent", "source_ref": a2},
    ]


def test_run_chain_unknown_chain_is_404(client: TestClient) -> None:
    assert client.post("/api/chains/nope/run", json={"input": "x"}).status_code == 404


def test_run_chain_missing_agent_is_404(client: TestClient) -> None:
    cid = client.post(
        "/api/chains", json={"name": "C", "steps": ["ghost_agent"]}
    ).json()["chain"]["id"]
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 404
    assert "ghost_agent" in resp.json()["error"]


def test_run_chain_empty_steps_is_400(client: TestClient) -> None:
    cid = client.post("/api/chains", json={"name": "Empty", "steps": []}).json()["chain"]["id"]
    assert client.post(f"/api/chains/{cid}/run", json={"input": "x"}).status_code == 400


def test_run_chain_engine_error_is_502(client: TestClient, monkeypatch) -> None:
    a1 = _make_agent(client, "A1", "{input}")
    cid = client.post("/api/chains", json={"name": "C", "steps": [a1]}).json()["chain"]["id"]

    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = None

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _Boom()
    )
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]
    assert resp.json()["agent_id"] == a1


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


# ── Run a workflow ───────────────────────────────────────────────────────────
def _stub_intel(monkeypatch, output="WF-OUT", provider="local"):
    class _FakeIntel:
        active_provider = provider

        def __init__(self):
            self.captured = {}

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            self.captured["system_prompt"] = system_prompt
            self.captured["user_prompt"] = user_prompt
            return output

    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    return fake


def test_run_workflow_prompt(client: TestClient, monkeypatch) -> None:
    wid = client.post(
        "/api/workflows", json={"name": "WF", "prompt": "Do: {input}"}
    ).json()["workflow"]["id"]
    fake = _stub_intel(monkeypatch)

    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "the thing"})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "workflow_id": wid,
        "output": "WF-OUT",
        "provider": "local",
        "sources": [{"source_type": "workflow", "source_ref": wid}],
    }
    # Workflow runs with an empty system prompt + the rendered prompt.
    assert fake.captured == {"system_prompt": "", "user_prompt": "Do: the thing"}


# A real Workbench Blueprint shape: entry -> summarize -> rewrite -> output, a single
# linear chain (Swift-Codable snake_case tagged-union node kinds).
def _linear_graph() -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Summary then Exec",
        "entry": "e1",
        "nodes": [
            {"id": "e1", "kind": {"entry": {}}, "failure_policy": None},
            {"id": "sum", "kind": {"summarize": {}}, "failure_policy": None},
            {"id": "rw", "kind": {"rewrite": {"tone": "executive"}}, "failure_policy": None},
            {"id": "out", "kind": {"output": {}}, "failure_policy": None},
        ],
        "exec_edges": [
            {"from": {"node": "e1", "name": "then"}, "to": "sum"},
            {"from": {"node": "sum", "name": "then"}, "to": "rw"},
            {"from": {"node": "rw", "name": "then"}, "to": "out"},
        ],
        "data_edges": [],
    }


# A branching Blueprint we MUST NOT linearize: entry -> branch -> {true,false}.
def _branching_graph() -> dict:
    return {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Branchy",
        "entry": "e1",
        "nodes": [
            {"id": "e1", "kind": {"entry": {}}, "failure_policy": None},
            {"id": "br", "kind": {"branch": {"condition": {"contains": {"keyword": "x"}}}},
             "failure_policy": None},
            {"id": "a", "kind": {"summarize": {}}, "failure_policy": None},
            {"id": "b", "kind": {"summarize": {}}, "failure_policy": None},
        ],
        "exec_edges": [
            {"from": {"node": "e1", "name": "then"}, "to": "br"},
            {"from": {"node": "br", "name": "true"}, "to": "a"},
            {"from": {"node": "br", "name": "false"}, "to": "b"},
        ],
        "data_edges": [],
    }


def test_run_workflow_linear_graph_runs_in_order(client: TestClient, monkeypatch) -> None:
    wid = client.post(
        "/api/workflows", json={"name": "G", "graph_json": _linear_graph()}
    ).json()["workflow"]["id"]

    calls = []

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            calls.append(user_prompt)
            return f"out{len(calls)}"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )

    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "the meeting"})
    assert resp.status_code == 200
    body = resp.json()

    # Two model ops ran in chain order: summarize first (over the input), then rewrite
    # (over summarize's output) — output threaded through, no guessed order.
    assert len(calls) == 2
    assert calls[0].startswith("Summarize the following")
    assert "the meeting" in calls[0]
    assert calls[1].startswith("Rewrite the following text in a executive tone")
    assert "out1" in calls[1]  # rewrite ran on summarize's output

    # The trail + final output + lineage are returned.
    assert [s["node_id"] for s in body["steps"]] == ["sum", "rw"]
    assert [s["kind"] for s in body["steps"]] == ["summarize", "rewrite"]
    assert body["output"] == "out2"
    assert body["provider"] == "local"
    assert body["sources"] == [{"source_type": "workflow", "source_ref": wid}]
    assert "warning" not in body


def test_run_workflow_branching_graph_falls_back_with_warning(client: TestClient, monkeypatch) -> None:
    # A branching graph + a prompt: we refuse the graph (no guessed order) and run the
    # prompt, with an honest warning naming why.
    wid = client.post(
        "/api/workflows",
        json={"name": "G", "prompt": "fallback: {input}", "graph_json": _branching_graph()},
    ).json()["workflow"]["id"]
    fake = _stub_intel(monkeypatch)

    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "x"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["output"] == "WF-OUT"
    assert "control-flow" in body["warning"] and "prompt fallback" in body["warning"]
    # It ran the PROMPT, not any graph node.
    assert fake.captured["user_prompt"] == "fallback: x"
    assert "steps" not in body


def test_run_workflow_branching_graph_no_prompt_no_input_is_400(client: TestClient, monkeypatch) -> None:
    # A branching graph, no prompt, no input: nothing safe to run -> 400 (never a guess).
    wid = client.post(
        "/api/workflows", json={"name": "G", "graph_json": _branching_graph()}
    ).json()["workflow"]["id"]
    _stub_intel(monkeypatch)
    assert client.post(f"/api/workflows/{wid}/run", json={}).status_code == 400


def test_run_workflow_unknown_is_404(client: TestClient) -> None:
    assert client.post("/api/workflows/nope/run", json={"input": "x"}).status_code == 404


def test_run_workflow_engine_error_is_502(client: TestClient, monkeypatch) -> None:
    wid = client.post(
        "/api/workflows", json={"name": "WF", "prompt": "{input}"}
    ).json()["workflow"]["id"]

    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = None

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _Boom()
    )
    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "x"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]


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


def test_directory_reads_include_member_ids(client: TestClient) -> None:
    did = client.post("/api/directories", json={"name": "Folder"}).json()["directory"]["id"]

    # Empty to start: both the list item and the detail carry member_ids: [].
    assert client.get("/api/directories").json()["directories"][0]["member_ids"] == []
    assert client.get(f"/api/directories/{did}").json()["member_ids"] == []

    # File two primitives.
    client.put(f"/api/directories/{did}/members/note_1")
    client.put(f"/api/directories/{did}/members/agent_2")

    # The list item now carries the filed ids.
    item = client.get("/api/directories").json()["directories"][0]
    assert sorted(item["member_ids"]) == ["agent_2", "note_1"]

    # The detail response carries member_ids AND keeps the full members bucket.
    detail = client.get(f"/api/directories/{did}").json()
    assert sorted(detail["member_ids"]) == ["agent_2", "note_1"]
    assert sorted(m["primitive_id"] for m in detail["members"]) == ["agent_2", "note_1"]

    # Unfiling drops the id from member_ids (tombstone excluded).
    client.delete(f"/api/directories/{did}/members/note_1")
    assert client.get(f"/api/directories/{did}").json()["member_ids"] == ["agent_2"]
    assert client.get("/api/directories").json()["directories"][0]["member_ids"] == ["agent_2"]
