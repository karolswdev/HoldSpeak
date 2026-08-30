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
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    # These route tests inject an engine; a real configured local artifact
    # supplies the canonical route's readiness evidence.
    default_model = tmp_path / "loop-default.gguf"
    default_model.touch()
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(default_model),
    )
    db.profiles.upsert(
        profile_id="loop-default", name="Loop default", kind="onDevice",
        model_file=str(default_model),
    )
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "loop-test-owner"),
        {
            "command_id": "loop-test-default-assignment",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "legacy-loop-default"}],
        },
    )
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


class _LoopSpy:
    """run_prompt records whether an event loop runs in ITS thread."""

    active_provider = "local"

    def __init__(self) -> None:
        self.on_loop: bool | None = None

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        try:
            asyncio.get_running_loop()
            self.on_loop = True
        except RuntimeError:
            self.on_loop = False
        return "RAN"


@pytest.fixture
def spy(monkeypatch) -> _LoopSpy:
    s = _LoopSpy()
    # Admitted Sequence/Workflow dispatch constructs from the immutable
    # deployment revision in InferenceRunner, not the retired configured-engine
    # route helper. Keep the production admission/runner path and replace only
    # its provider-construction boundary.
    from holdspeak.kernel.inference_runner import InferenceRunner
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_kw: s)
    # Ask and legacy Recipe surfaces still construct their provider through this
    # long-standing seam; Sequence/Workflow is deliberately covered above.
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: s)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: s)
    return s


def _assert_off_loop(spy: _LoopSpy) -> None:
    assert spy.on_loop is False, (
        "the engine ran ON the event loop — a mesh run would deadlock the "
        "worker's claim polls and die at its deadline as 'never claimed'"
    )


def test_ask_runs_the_engine_off_the_loop(env, spy) -> None:
    _, client = env
    assert client.post("/api/ask", json={"prompt": "Go"}).status_code == 200
    _assert_off_loop(spy)


def test_recipe_run_and_chat_run_the_engine_off_the_loop(env, spy) -> None:
    _, client = env
    rid = client.post(
        "/api/recipes",
        json={"name": "Loop", "system_prompt": "Answer.", "user_template": "Q: {input}"},
    ).json()["recipe"]["id"]

    assert client.post(f"/api/recipes/{rid}/run", json={"input": "hi"}).status_code == 200
    _assert_off_loop(spy)

    spy.on_loop = None
    resp = client.post(f"/api/recipes/{rid}/chat", json={"question": "hi"})
    # The thread alias returns 201 and dispatches the engine on a daemon
    # thread (the request never blocks the loop). Wait briefly for the
    # daemon to fire the spy before asserting.
    assert resp.status_code == 201
    for _ in range(100):
        if spy.on_loop is not None:
            break
        time.sleep(0.02)
    _assert_off_loop(spy)


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
