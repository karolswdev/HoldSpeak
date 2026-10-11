"""Runs on (the engines and the jobs they run): hub facts, no browser.

The test diet (2026-10-11): successors of browser tests whose only real
assertions were API answers. The seeds are the ones the browser tests used.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.front_door import build_front_door_router
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

LAN_ID = "lan-qwen36-35b-a3b"
LAN_GROUPS = ["thoughts_notes", "writing_dictation", "meetings", "agents_tools", "background"]


def _front_door(tmp_path: Path) -> tuple[TestClient, Database]:
    owner = Principal(PrincipalKind.OWNER, "runs-on-test-owner")
    db = Database(tmp_path / "runs-on.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    app.include_router(build_front_door_router(WebContext(get_state=lambda: {}, inference_setup_service=setup)))
    return TestClient(app), db


def _seed_like_the_glass(db: Database) -> None:
    """test_hs156_front_door_glass.py: `_seed_profile_and_assign`,
    `_seed_endpoint_profile` and `_seed_group_assignment_to`, unchanged."""
    _profile(db, "hs156-glass-local", claims=("language", _result_claim("chat.turn")))
    service = InferenceAssignmentService(db)
    service.set_assignment(OWNER, {
        "command_id": "hs156-glass-assign", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "hs156-glass-local", "profile_revision": 1}],
    })
    _profile(db, LAN_ID, claims=("language", _result_claim("chat.turn")))
    db.profiles.upsert(
        profile_id=LAN_ID, name="LAN Qwen 3.6", kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1", model="qwen3.6-35b-a3b",
    )
    for group in LAN_GROUPS:
        service.set_assignment(OWNER, {
            "command_id": f"hs156-glass-assign-{group}", "expected_revision": 0,
            "scope": {"kind": "group", "group_id": group},
            "entries": [{"profile_id": LAN_ID, "profile_revision": 1}],
        })


def test_the_topology_draws_this_mac_and_the_lan_engine_with_its_flows(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_hs156_front_door_glass.py::test_topology
    replaces: tests/e2e/test_hs156_front_door_glass.py::test_topology_add_node (its add-node clicks were conditional and asserted nothing; its one fact is this API)
    """
    client, db = _front_door(tmp_path)
    _seed_like_the_glass(db)

    response = client.get("/api/front-door/topology")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["nodes"]) >= 2, payload["nodes"]
    lan_flows = [flow for flow in payload["flows"] if flow["target_node_id"] == LAN_ID]
    assert len(lan_flows) >= 3, payload["flows"]
    # The flows are the assignments: every group the glass sent to the LAN box.
    assert {flow["group_id"] for flow in lan_flows} == set(LAN_GROUPS)
    lan = next(node for node in payload["nodes"] if node["id"] == LAN_ID)
    assert lan["base_url"] == "http://192.168.1.43:8080/v1" and lan["home"] is False


def test_the_topology_needs_the_owner(tmp_path: Path) -> None:
    """replaces: nothing (the owner rule the topology leg relied on)."""
    db = Database(tmp_path / "runs-on.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = Principal(PrincipalKind.AGENT, "runs-on-agent")
        return await call_next(request)

    app.include_router(build_front_door_router(WebContext(get_state=lambda: {}, inference_setup_service=setup)))
    assert TestClient(app).get("/api/front-door/topology").status_code == 403
