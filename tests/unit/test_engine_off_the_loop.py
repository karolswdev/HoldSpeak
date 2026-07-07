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

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
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
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: s
    )
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
    assert client.post(f"/api/recipes/{rid}/chat", json={"question": "hi"}).status_code == 200
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
    rid = client.post(
        "/api/recipes",
        json={"id": "recipe_wf", "name": "WF", "system_prompt": "Answer."},
    ).json()["recipe"]["id"]
    wid = client.post(
        "/api/workflows", json={"id": "wf_loop", "name": "Loop", "recipe_ids": [rid]}
    ).json()["workflow"]["id"]

    assert client.post(f"/api/workflows/{wid}/run", json={"input": "hi"}).status_code == 200
    _assert_off_loop(spy)
