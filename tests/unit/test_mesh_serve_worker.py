"""HS-85-03 — `holdspeak mesh serve`, the edge worker.

The loop is factored into testable steps (claim / execute / report): against
an in-process hub app the worker claims a queued job, executes it via an
injected engine, and the hub row completes with the result verbatim; a
raising engine posts `fail` verbatim; an unreachable hub backs off without
crashing; claims stamp liveness end to end.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.commands.mesh_serve import MeshServeWorker
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes.mesh import build_mesh_router


@pytest.fixture
def db(tmp_path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def hub(db, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_mesh_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def _http_via(client: TestClient):
    """Adapt the worker's http_post seam onto the in-process test hub."""

    def post(url: str, payload: dict[str, Any], *, token: str, timeout: float) -> dict[str, Any]:
        path = url.split("http://test-hub", 1)[1]
        resp = client.post(path, json=payload)
        if resp.status_code >= 400:
            raise ValueError(f"{resp.status_code}: {resp.text}")
        return resp.json()

    return post


class _Engine:
    def __init__(self, reply: str = "answered on the edge") -> None:
        self.reply = reply
        self.calls: list[dict[str, Any]] = []

    def run_prompt(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        return self.reply


def _worker(hub, engine=None, **kw) -> MeshServeWorker:
    return MeshServeWorker(
        hub_url="http://test-hub", node="walk-edge", token="t",
        http_post=_http_via(hub), engine_factory=(lambda: engine) if engine else None,
        sleep=lambda s: None, **kw,
    )


def test_once_claims_executes_and_completes_verbatim(db, hub) -> None:
    job = db.mesh_relay.enqueue(
        node="walk-edge", system_prompt="Be brief.", user_prompt="What is dictation?",
        temperature=0.2, max_tokens=64,
    )
    engine = _Engine()
    assert _worker(hub, engine).run_once() == 0

    assert engine.calls == [{
        "system_prompt": "Be brief.", "user_prompt": "What is dictation?",
        "temperature": 0.2, "max_tokens": 64,
    }]
    done = db.mesh_relay.get(job.id)
    assert done.status == "completed" and done.result == "answered on the edge"


def test_once_with_no_work_exits_clean(db, hub) -> None:
    assert _worker(hub, _Engine()).run_once() == 0
    # the empty poll still stamped liveness — the whole point of claim-as-heartbeat
    assert db.mesh_relay.worker_last_seen("walk-edge") is not None


def test_engine_failure_posts_fail_verbatim(db, hub) -> None:
    job = db.mesh_relay.enqueue(node="walk-edge", user_prompt="x")

    class _Boom:
        def run_prompt(self, **kwargs: Any) -> str:
            raise RuntimeError("llama exploded: OOM")

    worker = MeshServeWorker(
        hub_url="http://test-hub", node="walk-edge",
        http_post=_http_via(hub), engine_factory=lambda: _Boom(),
        sleep=lambda s: None,
    )
    assert worker.run_once() == 1
    failed = db.mesh_relay.get(job.id)
    assert failed.status == "failed" and "llama exploded: OOM" in failed.error


def test_unreachable_hub_backs_off_without_crashing() -> None:
    slept: list[float] = []

    def dead_post(url, payload, *, token, timeout):
        raise ValueError("connection refused")

    worker = MeshServeWorker(
        hub_url="http://test-hub", node="walk-edge",
        http_post=dead_post, sleep=slept.append,
    )
    assert worker.poll_step() is False
    assert worker.poll_step() is False
    assert worker.poll_step() is False
    # exponential: 1, 2, 4 — capped later
    assert slept == [1.0, 2.0, 4.0]
    assert worker.run_once() == 1  # once-mode reports the outage honestly


def test_run_forever_stops_on_stop_and_does_work(db, hub) -> None:
    db.mesh_relay.enqueue(node="walk-edge", user_prompt="one")
    engine = _Engine()
    worker = _worker(hub, engine)

    ticks = {"n": 0}
    original = worker.poll_step

    def counting_step() -> bool:
        ticks["n"] += 1
        if ticks["n"] >= 3:
            worker.stop()
        return original()

    worker.poll_step = counting_step  # type: ignore[method-assign]
    assert worker.run_forever() == 0
    assert len(engine.calls) == 1  # the queued job ran exactly once


def test_cli_wiring_parses() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "holdspeak.main", "mesh", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0
    assert "serve" in proc.stdout
