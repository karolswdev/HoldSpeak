"""Parked 2026-11-08 from tests/unit/test_run_frames.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
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
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture()


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
