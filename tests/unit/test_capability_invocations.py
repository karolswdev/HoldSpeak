"""HS-92-06 durable run envelopes, failure retention, and receipt reads."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_repository_round_trips_invocation_attempt_and_result(rig) -> None:
    db, _ = rig
    begun = db.capability_invocations.begin(
        invocation_id="inv_1", definition_ref="persona:scout",
        grounding_refs=["meeting:m1"], requested_placement="profile:local",
        input_snapshot={"input": "find risks"},
    )
    assert begun.state == "running" and begun.attempts == []
    db.capability_invocations.start_attempt(
        invocation_id="inv_1", attempt_id="try_1", destination="profile:local",
    )
    db.capability_invocations.finish_attempt(
        "try_1", state="succeeded", provider="local", result_ref="artifact:a1",
    )
    done = db.capability_invocations.finish(
        "inv_1", state="succeeded", result_ref="artifact:a1",
    )
    assert done.correlation_id == "inv_1"
    assert done.input_snapshot == {"input": "find risks"}
    assert done.grounding_refs == ["meeting:m1"]
    assert done.attempts[0].provider == "local"


def test_failed_run_keeps_input_and_grounding_for_retry(rig, monkeypatch) -> None:
    db, client = rig
    recipe = db.recipes.upsert(
        recipe_id="scout", name="Scout", user_template="{input}",
    )

    from holdspeak.intel.models import MeetingIntelError

    class Broken:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("model offline")

    # This test owns the engine failure path; model-file readiness is covered by
    # inference-target tests and must not short-circuit the injected engine.
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: Broken())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: Broken()
    )
    request = {"input": "keep this wording", "grounding_refs": ["note:n1"]}
    response = client.post(f"/api/recipes/{recipe.id}/run", json=request)
    assert response.status_code == 502
    failed = response.json()
    assert "model offline" in failed["error"]

    # Admission now owns the durable receipt instead of the retired capability
    # invocation projection. Retrying the unchanged user request reaches a new
    # admitted run once the destination recovers.
    class Recovered:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            return "retried"

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: Recovered())
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: Recovered()
    )
    retried = client.post(f"/api/recipes/{recipe.id}/run", json=request)
    assert retried.status_code == 200
    assert retried.json()["output"] == "retried"


def test_capability_readiness_refuses_unsupported_graph_before_engine(rig, monkeypatch) -> None:
    db, client = rig
    graph = {
        "entry": "e",
        "nodes": [
            {"id": "e", "kind": {"entry": {}}},
            {"id": "b", "kind": {"branch": {}}},
        ],
        "exec_edges": [{"from": {"node": "e", "name": "then"}, "to": "b"}],
    }
    db.workflows.upsert(workflow_id="branchy", name="Branchy", prompt="fallback", graph_json=graph)
    row = client.get("/api/workflows/branchy").json()["workflow"]
    assert row["capability"]["readiness"]["state"] == "unavailable"
    assert row["capability"]["support"] == "unsupported_graph"

    called = False

    def engine():
        nonlocal called
        called = True
        raise AssertionError("engine must not be constructed")

    # Both construction seams must stay untouched: the refusal happens before any
    # engine exists, so either one firing is the defect this test names.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: engine())
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", engine)
    response = client.post("/api/workflows/branchy/run", json={"input": "retained"})
    assert response.status_code == 409
    refused = response.json()
    # HS-131-04 replaces the legacy invocation envelope with an admitted native
    # parent. Unsupported control flow is typed, receipt-closed as refused, and
    # admits no child or provider construction.
    assert refused["support"] == "unsupported_graph"
    parent_id = refused["parent_operation_id"]
    with db._connection() as conn:
        parent = conn.execute("SELECT state FROM kernel_operations WHERE operation_id=?", (parent_id,)).fetchone()
        receipt = conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (parent_id,)).fetchone()
        children = conn.execute("SELECT count(*) FROM kernel_operations WHERE parent_operation_id=?", (parent_id,)).fetchone()[0]
    assert parent[0] == "refused" and receipt[0] == "refused" and children == 0
    assert called is False
