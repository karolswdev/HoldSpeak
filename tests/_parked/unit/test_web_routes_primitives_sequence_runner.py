"""Parked 2026-11-08 from tests/unit/test_web_routes_primitives.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""Primitive Framework — Note + Agent CRUD routes and the persona-run seam.

Builds a minimal app with just `build_primitives_router` over a real tmp-path
Database (the handlers do `from ...db import get_database` at call time, so we
point the singleton at a tmp DB). The persona-run endpoint is exercised with the
intel engine stubbed so no model is loaded.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _kernel_fields import plain  # noqa: E402  (PHILO-7-02)



@pytest.fixture


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

    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _FakeIntel())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _FakeIntel()
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
    _assert_admitted_parent_run(body, 2)


def test_run_chain_unknown_chain_is_404(client: TestClient) -> None:
    assert client.post("/api/chains/nope/run", json={"input": "x"}).status_code == 404


def test_run_chain_missing_persona_is_unavailable(client: TestClient) -> None:
    cid = client.post(
        "/api/chains", json={"name": "C", "steps": ["ghost_agent"]}
    ).json()["chain"]["id"]
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 409
    assert "ghost_agent" in resp.json()["error"]
    assert resp.json()["error"]


def test_run_chain_empty_steps_is_unavailable(client: TestClient) -> None:
    cid = client.post("/api/chains", json={"name": "Empty", "steps": []}).json()["chain"]["id"]
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 409
    assert resp.json()["parent_operation_id"].startswith("op_")


def test_run_chain_engine_error_is_502(client: TestClient, monkeypatch) -> None:
    a1 = _make_agent(client, "A1", "{input}")
    cid = client.post("/api/chains", json={"name": "C", "steps": [a1]}).json()["chain"]["id"]

    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = None

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _Boom())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Boom()
    )
    resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]
    assert resp.json()["recipe_id"] == a1


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
    _assert_admitted_parent_run(body, 1)
    assert body["workflow_id"] == wid and body["output"] == "WF-OUT"
    assert body["provider"] == "local"
    assert [row["source_type"] for row in body["sources"]] == ["workflow"]
    # Workflow runs with an empty system prompt + the rendered prompt.
    assert fake.captured == {"system_prompt": "", "user_prompt": "Do: the thing"}


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

    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _FakeIntel())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _FakeIntel()
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
    assert [row["source_type"] for row in body["sources"]] == ["workflow"]
    _assert_admitted_parent_run(body, 2)
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
    assert body["error"]


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

    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _FakeIntel())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _FakeIntel()
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

    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _Boom())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Boom()
    )
    resp = client.post(f"/api/workflows/{wid}/run", json={"input": "x"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]
