"""Parked 2026-11-08 from tests/unit/test_placement_provenance.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""HS-134-04 -- every answer names its decider.

Proves that every placement-resolving execution response carries
``{"placement": {"effective_target_id": ..., "source": ...}}`` from
``PlacementResolution.placement_dict()`` -- the REAL resolution used for
that run, not a recomputation that could disagree.

Surfaces covered: Ask, Recipe run, Recipe chat, Workbench run,
Sequence, Workflow, Cadence get_loop (LLM-drafted path).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import PLACEMENT_SOURCES, THIS_MACHINE_ID
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "provenance-owner")


def test_sequence_run_placement(tmp_path, monkeypatch):
    """Sequence run carries placement block."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / "seq_prov.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _ready_local_model(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    _profile(db, "sequence-provenance", claims=(_result_claim("sequence.step"),))
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "sequence-provenance-assignment", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "sequence.step"},
            "entries": [{"profile_id": "sequence-provenance", "profile_revision": 1}],
        },
    )

    class _Engine:
        active_provider = "local"

        def run_prompt(self, **_):
            return "seq-output"

    monkeypatch.setitem(
        InferenceRunner.__init__.__kwdefaults__,
        "engine_factory",
        lambda rev, **_: _Engine(),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Engine()
    )

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)

    rid = client.post(
        "/api/recipes",
        json={"name": "Seq", "system_prompt": "SYS", "user_template": "{input}"},
    ).json()["recipe"]["id"]
    cid = client.post(
        "/api/chains", json={"name": "seq", "steps": [rid]}
    ).json()["chain"]["id"]
    response = client.post(f"/api/chains/{cid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert "placement" in result, f"placement missing from sequence: {sorted(result)}"
    # The public block projects the canonical frozen route, not a legacy target.
    assert result["placement"]["source"] == "capability"
    assert result["placement"]["effective_target_id"] == "sequence-provenance"


def test_workflow_run_placement(tmp_path, monkeypatch):
    """Workflow run carries placement block."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / "wf_prov.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _ready_local_model(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    _profile(db, "workflow-provenance", claims=(_result_claim("workflow.node"),))
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "workflow-provenance-assignment", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "workflow.node"},
            "entries": [{"profile_id": "workflow-provenance", "profile_revision": 1}],
        },
    )

    class _Engine:
        active_provider = "local"

        def run_prompt(self, **_):
            return "wf-output"

    monkeypatch.setitem(
        InferenceRunner.__init__.__kwdefaults__,
        "engine_factory",
        lambda rev, **_: _Engine(),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Engine()
    )

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)

    graph = {
        "entry": "entry",
        "nodes": [
            {"id": "entry", "kind": {"entry": {}}},
            {"id": "model", "kind": {"summarize": {}}},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "entry", "name": "then"}, "to": "model"},
            {"from": {"node": "model", "name": "then"}, "to": "out"},
        ],
    }
    wid = client.post(
        "/api/workflows",
        json={"id": "wf_prov", "name": "Prov", "graph_json": graph},
    ).json()["workflow"]["id"]
    response = client.post(f"/api/workflows/{wid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert "placement" in result, f"placement missing from workflow: {sorted(result)}"
    assert result["placement"]["source"] == "capability"
    assert result["placement"]["effective_target_id"] == "workflow-provenance"
