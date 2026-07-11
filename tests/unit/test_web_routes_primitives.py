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


def _assert_run_receipt(body: dict, definition_ref: str, input_text: str) -> None:
    assert body["invocation_id"] == body["correlation_id"]
    assert body["result_ref"] == f"artifact:{body['artifact_id']}"
    invocation = body["invocation"]
    assert invocation["id"] == body["invocation_id"]
    assert invocation["definition_ref"] == definition_ref
    assert invocation["input_snapshot"]["input"] == input_text
    assert invocation["state"] == "succeeded"
    assert len(invocation["attempts"]) == 1
    assert invocation["attempts"][0]["state"] == "succeeded"


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
    resp = client.post("/api/recipes", json={
        "name": "Summarizer", "role": "assistant",
        "system_prompt": "You summarize.", "user_template": "Summarize: {input}",
        "tools": ["web"], "kb_id": "kb1",
    })
    assert resp.status_code == 201
    agent = resp.json()["recipe"]
    aid = agent["id"]
    assert agent["name"] == "Summarizer" and agent["kb_id"] == "kb1"

    assert len(client.get("/api/recipes").json()["recipes"]) == 1

    upd = client.put(f"/api/recipes/{aid}", json={"role": "expert"})
    assert upd.json()["recipe"]["role"] == "expert"
    assert upd.json()["recipe"]["system_prompt"] == "You summarize."  # unchanged

    assert client.delete(f"/api/recipes/{aid}").json() == {"success": True}
    assert client.get(f"/api/recipes/{aid}").status_code == 404


def test_agent_create_requires_name(client: TestClient) -> None:
    assert client.post("/api/recipes", json={"role": "x"}).status_code == 400


# ── Run a persona ────────────────────────────────────────────────────────────
def test_run_agent_invokes_engine(client: TestClient, monkeypatch) -> None:
    aid = client.post("/api/recipes", json={
        "name": "Echo", "system_prompt": "SYS", "user_template": "Q: {input}",
    }).json()["recipe"]["id"]

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

    resp = client.post(f"/api/recipes/{aid}/run", json={"input": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    # HS-74-01: the run persists as a run-born artifact; the id is minted.
    artifact_id = body.pop("artifact_id")
    assert artifact_id
    body["artifact_id"] = artifact_id
    _assert_run_receipt(body, f"persona:{aid}", "hello")
    assert body["recipe_id"] == aid and body["output"] == "ANSWER"
    assert body["provider"] == "local" and body["profile_id"] is None
    assert [row["source_type"] for row in body["sources"]] == [
        "recipe", "invocation", "attempt"
    ]
    # The persona's system prompt + rendered template reached the engine.
    assert captured["system_prompt"] == "SYS"
    assert captured["user_prompt"] == "Q: hello"


def test_run_agent_includes_input_source(client: TestClient, monkeypatch) -> None:
    """A caller-provided `source_ref` is recorded as an `input` lineage source."""
    aid = client.post("/api/recipes", json={
        "name": "Echo", "user_template": "{input}",
    }).json()["recipe"]["id"]

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            return "OUT"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )
    resp = client.post(
        f"/api/recipes/{aid}/run", json={"input": "x", "source_ref": "meeting_7"}
    )
    assert resp.json()["sources"][:2] == [
        {"source_type": "recipe", "source_ref": aid},
        {"source_type": "input", "source_ref": "meeting_7"},
    ]


# ── Run-response provenance: the pinned `source_type` vocabulary ─────────────
def test_run_response_source_type_vocab_is_pinned() -> None:
    """The hub is the canonical authority for run-response `source_type` values.

    Audit follow-up (Phase 22/sync): the iPad authoring port emitted "card" while
    the hub emits "input" — non-breaking but undocumented drift. The hub vocab is
    now pinned here so a future change to any literal is caught (a wire contract
    break for every surface that attaches lineage).
    """
    from holdspeak.web.routes.primitives import (
        CANONICAL_SOURCE_TYPES,
        canonical_source_type,
    )

    # The full canonical set the hub run endpoints emit.
    assert CANONICAL_SOURCE_TYPES == {
        "recipe", "input", "chain", "workflow", "invocation", "attempt"
    }

    # Canonical values pass through unchanged.
    for value in CANONICAL_SOURCE_TYPES:
        assert canonical_source_type(value) == value

    # The iPad synonym "card" folds to the canonical "input" (tolerated alias).
    assert canonical_source_type("card") == "input"
    assert canonical_source_type("CARD") == "input"  # case + strip tolerant
    assert canonical_source_type(" card ") == "input"

    # An unknown tag is NOT rejected — returned lowercased/stripped, untouched
    # (non-breaking: we never claim it canonical, but never drop it either).
    assert canonical_source_type("mystery") == "mystery"
    assert canonical_source_type("") == ""


def test_run_agent_input_source_accepts_ipad_card_alias(
    client: TestClient, monkeypatch
) -> None:
    """An iPad-supplied `source_type: "card"` folds to the canonical "input"."""
    aid = client.post("/api/recipes", json={
        "name": "Echo", "user_template": "{input}",
    }).json()["recipe"]["id"]

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            return "OUT"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )
    resp = client.post(
        f"/api/recipes/{aid}/run",
        json={"input": "x", "source_ref": "meeting_7", "source_type": "card"},
    )
    assert resp.json()["sources"][:2] == [
        {"source_type": "recipe", "source_ref": aid},
        {"source_type": "input", "source_ref": "meeting_7"},
    ]


def test_run_agent_unknown_is_404(client: TestClient) -> None:
    assert client.post("/api/recipes/nope/run", json={"input": "x"}).status_code == 404


def test_run_agent_engine_error_is_502(client: TestClient, monkeypatch) -> None:
    aid = client.post("/api/recipes", json={
        "name": "X", "user_template": "{input}",
    }).json()["recipe"]["id"]

    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = None

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _Boom()
    )
    resp = client.post(f"/api/recipes/{aid}/run", json={"input": "x"})
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
    assert set(chain) == {"id", "name", "steps", "created_at", "last_modified", "deleted", "capability"}
    assert chain["capability"]["kind"] == "sequence"
    assert chain["capability"]["readiness"]["state"] == "unavailable"

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
    return client.post("/api/recipes", json={
        "name": name, "system_prompt": f"SYS-{name}", "user_template": template,
    }).json()["recipe"]["id"]


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
    assert [s["recipe_id"] for s in body["steps"]] == [a1, a2]
    assert body["steps"][0]["output"] == "out(step1: hello)"
    assert body["steps"][0]["provider"] == "local"
    # Chain output is the last step's output.
    assert body["output"] == body["steps"][-1]["output"] == "out(step2: out(step1: hello))"
    # Top-level provider = the last step's provider (kills the "provider unknown" badge).
    assert body["provider"] == "local"
    # Provenance: the chain plus each step's agent.
    assert body["sources"][:3] == [
        {"source_type": "chain", "source_ref": cid},
        {"source_type": "recipe", "source_ref": a1},
        {"source_type": "recipe", "source_ref": a2},
    ]
    _assert_run_receipt(body, f"sequence:{cid}", "hello")


def test_run_chain_unknown_chain_is_404(client: TestClient) -> None:
    assert client.post("/api/chains/nope/run", json={"input": "x"}).status_code == 404


def test_run_chain_missing_persona_is_unavailable(client: TestClient) -> None:
    cid = client.post(
        "/api/chains", json={"name": "C", "steps": ["ghost_agent"]}
    ).json()["chain"]["id"]
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 409
    assert "ghost_agent" in resp.json()["error"]
    assert resp.json()["invocation"]["state"] == "unavailable"


def test_run_chain_empty_steps_is_unavailable(client: TestClient) -> None:
    cid = client.post("/api/chains", json={"name": "Empty", "steps": []}).json()["chain"]["id"]
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 409
    assert resp.json()["invocation"]["input_snapshot"]["input"] == "x"


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
    assert resp.json()["recipe_id"] == a1


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
    assert set(wf) == {"id", "name", "prompt", "graph_json", "created_at", "last_modified", "deleted", "capability"}
    assert wf["capability"]["readiness"]["state"] == "unavailable"

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
    # HS-74-01: the run persists as a run-born artifact; the id is minted.
    assert body.pop("artifact_id")
    body["artifact_id"] = body["result_ref"].split(":", 1)[1]
    _assert_run_receipt(body, f"workflow:{wid}", "the thing")
    assert body["workflow_id"] == wid and body["output"] == "WF-OUT"
    assert body["provider"] == "local"
    assert [row["source_type"] for row in body["sources"]] == [
        "workflow", "invocation", "attempt"
    ]
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
    assert [row["source_type"] for row in body["sources"]] == [
        "workflow", "invocation", "attempt"
    ]
    _assert_run_receipt(body, f"workflow:{wid}", "the meeting")
    assert "warning" not in body


def test_run_workflow_branching_graph_is_refused_before_run(client: TestClient, monkeypatch) -> None:
    # A branching graph + prompt remains a graph. The hub never silently lowers it.
    wid = client.post(
        "/api/workflows",
        json={"name": "G", "prompt": "fallback: {input}", "graph_json": _branching_graph()},
    ).json()["workflow"]["id"]
    fake = _stub_intel(monkeypatch)

    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "x"})
    assert resp.status_code == 409
    body = resp.json()
    assert "control-flow" in body["error"]
    assert "not lowered to a prompt" in body["error"]
    assert fake.captured == {}
    assert body["invocation"]["state"] == "unavailable"
    assert body["invocation"]["input_snapshot"]["input"] == "x"


def test_run_workflow_branching_graph_no_prompt_is_unavailable(client: TestClient, monkeypatch) -> None:
    wid = client.post(
        "/api/workflows", json={"name": "G", "graph_json": _branching_graph()}
    ).json()["workflow"]["id"]
    _stub_intel(monkeypatch)
    assert client.post(f"/api/workflows/{wid}/run", json={}).status_code == 409


def test_run_workflow_web_authored_graph_runs(client: TestClient, monkeypatch) -> None:
    """HSM-22-03 — the WEB desk builder's exact emission runs on the hub.

    This graph mirrors `web/src/desk/graph.ts buildLinearGraph` byte-shape
    (locked by its vitest, `graph.test.ts`): entry → source → summarize →
    keep_if → out, nodes WITHOUT provenance keys (absent = inherit)."""
    graph = {
        "id": "wf-web-1", "name": "Web workflow", "entry": "entry",
        "nodes": [
            {"id": "entry", "kind": {"entry": {}}},
            {"id": "source", "kind": {"source": {}}},
            {"id": "n1", "kind": {"summarize": {}}},
            {"id": "n2", "kind": {"keep_if": {"keyword": "risk"}}},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "entry", "name": "then"}, "to": "source"},
            {"from": {"node": "source", "name": "then"}, "to": "n1"},
            {"from": {"node": "n1", "name": "then"}, "to": "n2"},
            {"from": {"node": "n2", "name": "then"}, "to": "out"},
        ],
        "data_edges": [],
    }
    wid = client.post(
        "/api/workflows", json={"name": "Web workflow", "graph_json": graph}
    ).json()["workflow"]["id"]

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            return "risk: the demo\nnothing else"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )

    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "the meeting"})
    assert resp.status_code == 200
    body = resp.json()
    # The model op + the pure transform both ran, in order, no warning.
    assert [s["node_id"] for s in body["steps"]] == ["n1", "n2"]
    assert [s["kind"] for s in body["steps"]] == ["summarize", "keep_if"]
    assert body["output"] == "risk: the demo"   # keep_if kept the risk line
    assert "warning" not in body


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
    filed = client.put(f"/api/directories/{did}/members/note%3Anote_42")
    assert filed.status_code == 200
    assert filed.json()["membership"]["primitive_id"] == "note:note_42"
    assert filed.json()["membership"]["directory_id"] == did

    # Membership is readable both via the directory GET and the members list.
    members = client.get(f"/api/directories/{did}/members").json()["members"]
    assert [m["primitive_id"] for m in members] == ["note:note_42"]
    assert client.get(f"/api/directories/{did}").json()["members"][0]["primitive_id"] == "note:note_42"

    # Filing into an unknown directory 404s.
    assert client.put("/api/directories/nope/members/note%3Ax").status_code == 404

    # Unfile (tombstone) -> gone from the list.
    assert client.delete(f"/api/directories/{did}/members/note%3Anote_42").json() == {"success": True}
    assert client.get(f"/api/directories/{did}/members").json()["members"] == []
    # Unfiling again (already gone) 404s.
    assert client.delete(f"/api/directories/{did}/members/note%3Anote_42").status_code == 404


def test_directory_member_listing_404_for_unknown_directory(client: TestClient) -> None:
    assert client.get("/api/directories/ghost/members").status_code == 404


def test_directory_reads_include_member_ids(client: TestClient) -> None:
    did = client.post("/api/directories", json={"name": "Folder"}).json()["directory"]["id"]

    # Empty to start: both the list item and the detail carry member_ids: [].
    assert client.get("/api/directories").json()["directories"][0]["member_ids"] == []
    assert client.get(f"/api/directories/{did}").json()["member_ids"] == []

    # File two primitives.
    client.put(f"/api/directories/{did}/members/note%3Anote_1")
    client.put(f"/api/directories/{did}/members/persona%3Aagent_2")

    # The list item now carries the filed ids.
    item = client.get("/api/directories").json()["directories"][0]
    assert sorted(item["member_ids"]) == ["note:note_1", "persona:agent_2"]

    # The detail response carries member_ids AND keeps the full members bucket.
    detail = client.get(f"/api/directories/{did}").json()
    assert sorted(detail["member_ids"]) == ["note:note_1", "persona:agent_2"]
    assert sorted(m["primitive_id"] for m in detail["members"]) == ["note:note_1", "persona:agent_2"]

    # Unfiling drops the id from member_ids (tombstone excluded).
    client.delete(f"/api/directories/{did}/members/note%3Anote_1")
    assert client.get(f"/api/directories/{did}").json()["member_ids"] == ["persona:agent_2"]
    assert client.get("/api/directories").json()["directories"][0]["member_ids"] == ["persona:agent_2"]


def test_profile_crud_roundtrip(client: TestClient) -> None:
    """Phase 24 — profiles CRUD over the API (shape only; no key field)."""
    created = client.post("/api/profiles", json={
        "name": "Claude", "kind": "openAICompatible",
        "base_url": "https://api.anthropic.com/v1", "model": "claude-3.5-sonnet",
        "context_limit": 200000, "requires_key": True,
    })
    assert created.status_code == 201, created.text
    pid = created.json()["profile"]["id"]
    assert "api_key" not in created.json()["profile"] and "apiKey" not in created.json()["profile"]

    assert client.get("/api/profiles").json()["profiles"][0]["id"] == pid
    got = client.get(f"/api/profiles/{pid}").json()["profile"]
    assert got["kind"] == "openAICompatible" and got["context_limit"] == 200000

    upd = client.put(f"/api/profiles/{pid}", json={"name": "Claude 3.7", "context_limit": 128000})
    assert upd.status_code == 200 and upd.json()["profile"]["name"] == "Claude 3.7"
    assert upd.json()["profile"]["context_limit"] == 128000

    assert client.delete(f"/api/profiles/{pid}").status_code == 200
    assert client.get(f"/api/profiles/{pid}").status_code == 404


def test_run_agent_resolves_assigned_profile(client: TestClient, monkeypatch) -> None:
    """An agent assigned a profile runs on THAT profile (the per-profile builder is used),
    and the run reports the resolved profile_id."""
    pid = client.post("/api/profiles", json={
        "name": "OpenRouter", "kind": "openAICompatible",
        "base_url": "https://openrouter.ai/api/v1", "model": "x", "requires_key": True,
    }).json()["profile"]["id"]
    aid = client.post("/api/recipes", json={
        "name": "Scout", "system_prompt": "S", "user_template": "{input}", "profile_id": pid,
    }).json()["recipe"]["id"]
    assert client.get(f"/api/recipes/{aid}").json()["recipe"]["profile_id"] == pid

    seen = {}

    class _FakeIntel:
        active_provider = "cloud"
        def run_prompt(self, **kwargs):
            return "OUT"

    def _for_profile(*, kind, base_url, model, profile_id, node=""):
        seen.update(kind=kind, base_url=base_url, profile_id=profile_id)
        return _FakeIntel()

    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", _for_profile)
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel",
        lambda: (_ for _ in ()).throw(AssertionError("default builder must NOT be used when a profile is assigned")),
    )
    resp = client.post(f"/api/recipes/{aid}/run", json={"input": "hi"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["profile_id"] == pid
    assert seen == {"kind": "openAICompatible", "base_url": "https://openrouter.ai/api/v1", "profile_id": pid}


def test_run_agent_falls_back_when_profile_missing(client: TestClient, monkeypatch) -> None:
    """A dangling profile_id (e.g. deleted) falls back to the hub default, reporting profile_id=None."""
    aid = client.post("/api/recipes", json={
        "name": "Ghost", "system_prompt": "S", "user_template": "{input}", "profile_id": "gone",
    }).json()["recipe"]["id"]

    class _FakeIntel:
        active_provider = "local"
        def run_prompt(self, **kwargs):
            return "OUT"

    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel())
    resp = client.post(f"/api/recipes/{aid}/run", json={"input": "hi"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["profile_id"] is None
