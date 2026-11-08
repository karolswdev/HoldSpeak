"""Parked 2026-11-08 from tests/unit/test_one_path_spine.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""HS-131-10 — the one-path fence: literal spine, every named surface.

Section 2 of DESIGN-HS-131-10.md (Sol-ratified 2026-08-11) requires that
every named product surface — FIFTEEN distinct entry forms, not the
charter's miscounted thirteen, and SIXTEEN once HS-131-13 migrated Cadence
onto the spine — reaches the SAME literal admission spine for every
physical model dispatch:

    1. InferenceRunner.invoke            (admission entry)
    2. Broker.submit_trusted_child (parent-scoped child) or Broker.submit
       (root), plus Broker._admit_authority
    3. Broker.claim
    4. InferenceRunner._dispatch
    5. ExecutorPlane._terminal            (receipt persistence)

This module monkeypatches those exact function OBJECTS (captured once, at
import time, from the kernel modules) so that a passing trace is proof the
surface really executed the imported functions — never a behaviorally
equivalent wrapper living somewhere else. Each surface driver builds the
cheapest REAL rig — a real ``Database`` in ``tmp_path`` plus the production
broker via ``holdspeak.kernel.runtime._configure`` — and fakes only the
engine/provider CONSTRUCTION seam, reusing the rigs named in the story
wherever one already exists in another test module (cross-module import of
their plain, undecorated helper functions; proven to work under this
repo's pytest configuration, since ``tests/`` has no package boundary that
would forbid it).
"""
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any, Callable

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import THIS_MACHINE_ID
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.executor import ExecutorPlane
from holdspeak.kernel.inference_runner import InferenceRunner
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

pytestmark = pytest.mark.timeout(120, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "spine-owner")

#: The principal a web route resolves to when the request carries no explicit
#: one — ``holdspeak/principals.py:179`` and the identical default in every
#: ``holdspeak/web/routes/primitives/*`` module. The HTTP-driven surfaces below
#: therefore run as THIS, not as the module's ``OWNER``; asserting the
#: difference is part of proving the kernel stamps the real authenticated
#: caller rather than whatever the test happened to have in hand.
WEB_OWNER_SESSION = Principal(PrincipalKind.OWNER, "owner-session")


# ---------------------------------------------------------------------------
# What a driver leaves behind, so the fence can read the REAL rows back
# ---------------------------------------------------------------------------


@dataclass(frozen=True)


def _http_engine_rig(tmp_path, monkeypatch, name: str):
    """The off-the-loop route rig (test_engine_off_the_loop.py), reimplemented
    as a plain function since the original is a pytest fixture and cannot be
    called directly."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / f"{name}.db")
    # Sequence/workflow now require real canonical assignment evidence rather
    # than the retired mutable this-machine selector.
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    _profile(
        db,
        f"spine-{name}",
        claims=tuple(sorted({_result_claim("sequence.step"), _result_claim("workflow.node")})),
    )
    for capability_id in ("sequence.step", "workflow.node"):
        InferenceAssignmentService(db).set_assignment(
            WEB_OWNER_SESSION,
            {
                "command_id": f"spine-{name}-{capability_id}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability_id},
                "entries": [{"profile_id": f"spine-{name}", "profile_revision": 1}],
            },
        )
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _ready_this_machine(tmp_path, monkeypatch)

    class _Engine:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            return "spine-output"

    engine = _Engine()
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    return db, TestClient(app)


def _drive_sequence(tmp_path, monkeypatch) -> SurfaceRun:
    db, client = _http_engine_rig(tmp_path, monkeypatch, "sequence")
    rid = client.post(
        "/api/recipes", json={"name": "Seq", "system_prompt": "SYS", "user_template": "{input}"},
    ).json()["recipe"]["id"]
    cid = client.post("/api/chains", json={"name": "seq", "steps": [rid]}).json()["chain"]["id"]
    response = client.post(f"/api/chains/{cid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    return SurfaceRun(
        db, WEB_OWNER_SESSION, _parent_run_operation_id(db, "sequence"), THIS_MACHINE_ID,
        parent_kind="sequence",
    )


def _drive_workflow(tmp_path, monkeypatch) -> SurfaceRun:
    db, client = _http_engine_rig(tmp_path, monkeypatch, "workflow")
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
        "/api/workflows", json={"id": "wf_spine", "name": "Spine", "graph_json": graph},
    ).json()["workflow"]["id"]
    response = client.post(f"/api/workflows/{wid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    return SurfaceRun(
        db, WEB_OWNER_SESSION, _parent_run_operation_id(db, "workflow"), THIS_MACHINE_ID,
        parent_kind="workflow",
    )
