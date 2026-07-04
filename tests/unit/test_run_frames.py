"""HS-74-02 — the run routes broadcast honest `intel_status` frames.

`running` precedes the engine call, `ready` follows success, `error`
follows a 502 — tagged `scope: "run"` with the capability identity, so
the theater and the Queue HUD play while the meeting-scoped /live panel
ignores them. No token frames are fabricated (the engine call is
synchronous). Headless contexts (`ctx.broadcast is None`) stay silent.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="route tests drive the real app")

from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture()
def rig(monkeypatch):
    reset_database()
    database = Database(Path(tempfile.mkdtemp()) / "run-frames.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
    ), host="127.0.0.1")
    frames: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        server, "broadcast", lambda t, d: frames.append((t, d))
    )
    # The router captured ctx.broadcast at build time as a lambda over
    # self.broadcast — the monkeypatch above reaches it through self.
    yield TestClient(server.app), database, frames
    reset_database()


def _stub_engine(monkeypatch, *, fail: bool = False):
    import holdspeak.intel.providers as providers
    from holdspeak.intel.models import MeetingIntelError

    class _Stub:
        active_provider = "stub"

        def run_prompt(self, **kwargs):
            if fail:
                raise MeetingIntelError("endpoint down")
            return "out"

    monkeypatch.setattr(
        providers, "build_configured_meeting_intel", lambda: _Stub()
    )


def _run_frames(frames):
    return [d for (t, d) in frames if t == "intel_status" and d.get("scope") == "run"]


def test_agent_run_frames_running_then_ready(rig, monkeypatch) -> None:
    client, db, frames = rig
    db.recipes.upsert(recipe_id="a1", name="Owl", system_prompt="s")
    _stub_engine(monkeypatch)

    resp = client.post("/api/recipes/a1/run", json={"input": "hi"})
    assert resp.status_code == 200

    run = _run_frames(frames)
    assert [f["state"] for f in run] == ["running", "ready"]
    assert run[0]["capability"] == {"kind": "recipe", "id": "a1", "name": "Owl"}
    assert "error" not in run[0] and "error" not in run[1]


def test_agent_run_error_frame_on_502(rig, monkeypatch) -> None:
    client, db, frames = rig
    db.recipes.upsert(recipe_id="a1", name="Owl", system_prompt="s")
    _stub_engine(monkeypatch, fail=True)

    resp = client.post("/api/recipes/a1/run", json={"input": "hi"})
    assert resp.status_code == 502

    run = _run_frames(frames)
    assert [f["state"] for f in run] == ["running", "error"]
    assert run[1]["error"] == "endpoint down"


def test_chain_and_workflow_bracket_the_whole_run(rig, monkeypatch) -> None:
    client, db, frames = rig
    db.recipes.upsert(recipe_id="a1", name="Owl", system_prompt="s",
                     user_template="{input}")
    db.chains.upsert(chain_id="c1", name="Pipeline", steps=["a1"])
    db.workflows.upsert(workflow_id="w1", name="Flow", prompt="Do: {input}")
    _stub_engine(monkeypatch)

    assert client.post("/api/chains/c1/run", json={"input": "x"}).status_code == 200
    assert client.post("/api/workflows/w1/run", json={"input": "x"}).status_code == 200

    run = _run_frames(frames)
    assert [(f["capability"]["kind"], f["state"]) for f in run] == [
        ("chain", "running"), ("chain", "ready"),
        ("workflow", "running"), ("workflow", "ready"),
    ]
    # ONE bracket per chain run, not one per step (no per-step noise).
    assert len([f for f in run if f["capability"]["kind"] == "chain"]) == 2


def test_no_token_frames_ever(rig, monkeypatch) -> None:
    client, db, frames = rig
    db.recipes.upsert(recipe_id="a1", name="Owl", system_prompt="s")
    _stub_engine(monkeypatch)
    client.post("/api/recipes/a1/run", json={"input": "hi"})
    assert not [t for (t, _d) in frames if t == "intel_token"], (
        "token frames must never be fabricated for a synchronous run"
    )
