"""Parked 2026-11-08 from tests/unit/test_capability_invocations.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""HS-92-06 durable run envelopes, failure retention, and receipt reads."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture


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
