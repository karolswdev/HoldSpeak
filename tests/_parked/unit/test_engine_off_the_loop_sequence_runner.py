"""Parked 2026-11-08 from tests/unit/test_engine_off_the_loop.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""HS-85-05 — the live walk's deadlock find, locked as a property.

A relayed run WAITS on the relay queue for a worker whose claim polls are
served by the SAME event loop that runs these routes. An engine call made
inline in an `async def` route therefore deadlocks the mesh: the hub cannot
serve the worker's claims while it waits, so the job dies at its deadline
as "never claimed" (exactly what the walk's hub rows showed, twice).

Lock the property, not the symptom: every async route that runs an engine
must execute it OFF the event loop (FastAPI's threadpool). From inside the
threadpool no running loop is observable in the calling thread, so the spy
below distinguishes the two cases deterministically.
"""
from __future__ import annotations

import asyncio
import time

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


def test_chain_runs_the_engine_off_the_loop(env, spy) -> None:
    _, client = env
    rid = client.post(
        "/api/recipes",
        json={"name": "Step", "system_prompt": "Answer.", "user_template": "Q: {input}"},
    ).json()["recipe"]["id"]
    cid = client.post(
        "/api/chains", json={"name": "Loop", "steps": [rid]}
    ).json()["chain"]["id"]

    assert client.post(f"/api/chains/{cid}/run", json={"input": "hi"}).status_code == 200
    _assert_off_loop(spy)


def test_workflow_runs_the_engine_off_the_loop(env, spy) -> None:
    _, client = env
    # The admitted Workflow runner executes its frozen graph, not the retired
    # ``recipe_ids`` convenience payload.
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
        "/api/workflows", json={"id": "wf_loop", "name": "Loop", "graph_json": graph}
    ).json()["workflow"]["id"]

    assert client.post(f"/api/workflows/{wid}/run", json={"input": "hi"}).status_code == 200
    _assert_off_loop(spy)
