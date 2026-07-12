from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.config as config_module
import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_authority_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "authority-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    app = FastAPI()
    app.include_router(build_authority_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_policy_and_control_mode_are_one_future_operation_contract(rig) -> None:
    _, client = rig
    policy = client.get("/api/authority/policy")
    assert policy.status_code == 200
    assert policy.json()["control_mode"] == "neutral"
    assert policy.json()["control_mode_label"] == "Normal"
    assert policy.json()["policy_version"] == "operation-policy/v2"
    assert policy.json()["unsupported_family_behavior"] == "refused"
    assert policy.json()["applies_to"] == "future_operations_only"
    assert policy.json()["precedence"][0] == "hard_invariants"
    assert "schema_safety" in policy.json()["hard_invariants"]

    changed = client.put("/api/authority/control-mode", json={"control_mode": "Secure"})
    assert changed.status_code == 200
    assert changed.json()["control_mode_label"] == "Secure"
    assert changed.json()["applies_to"] == "future_operations_only"
    assert client.get("/api/authority/policy").json()["control_mode"] == "safe"
    assert (
        client.put(
            "/api/authority/control-mode", json={"control_mode": "wild"}
        ).status_code
        == 400
    )


def test_grants_issue_only_from_fixed_proposal_and_expose_use_receipts(rig) -> None:
    db, client = rig
    proposal = db.actuators.record_proposal(
        meeting_id=None,
        origin="desk",
        window_id="desk:1",
        plugin_id="github",
        plugin_version="1",
        idempotency_key="route-grant",
        target="github",
        action="create_issue",
        preview="Create issue",
        payload={"repo": "acme/app", "title": "Follow up"},
    )
    client.put("/api/authority/control-mode", json={"control_mode": "yolo"})
    yolo = client.post("/api/authority/grants", json={"proposal_id": proposal.id})
    assert yolo.status_code == 409
    assert "captured posture" in yolo.json()["error"]
    client.put("/api/authority/control-mode", json={"control_mode": "Normal"})
    issued = client.post(
        "/api/authority/grants",
        json={
            "proposal_id": proposal.id,
            "actor": "karol",
            "ttl_seconds": 600,
            "max_uses": 2,
        },
    )
    assert issued.status_code == 201, issued.text
    grant = issued.json()["grant"]
    assert grant["project_scope"] == "acme/app"
    assert grant["remaining_uses"] == 2

    db.actuators.consume_grant(grant["id"], operation_id=f"actuator:{proposal.id}")
    uses = client.get(f"/api/authority/grants/{grant['id']}/uses")
    assert uses.status_code == 200
    assert uses.json()["uses"][0]["operation_id"] == f"actuator:{proposal.id}"
    assert (
        client.delete(f"/api/authority/grants/{grant['id']}").json()["state"]
        == "revoked"
    )

    arbitrary = client.post(
        "/api/authority/grants",
        json={"operation": {"family": "external_write", "destination": "new.example"}},
    )
    assert arbitrary.status_code == 404
