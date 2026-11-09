from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.config as config_module
import holdspeak.db as hsdb
from holdspeak import coder_steering
from holdspeak.db import Database, reset_database
from holdspeak.services.authority_service import AuthorityService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_authority_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    coder_steering.clear_grants()
    db = Database(tmp_path / "authority-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    from holdspeak.principals import Principal, PrincipalKind

    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "owner-session")
        return await call_next(request)

    app.include_router(
        build_authority_router(
            WebContext(get_state=lambda: {}, authority_service=AuthorityService(db))
        )
    )
    yield db, TestClient(app)
    coder_steering.clear_grants()
    reset_database()


def test_policy_and_control_mode_are_one_future_operation_contract(rig) -> None:
    _, client = rig
    policy = client.get("/api/authority/policy")
    assert policy.status_code == 200
    # HS-139-08: fresh install defaults to yolo.
    assert policy.json()["control_mode"] == "yolo"
    # Window Program W4 (the words): the owner's word for the posture.
    assert policy.json()["control_mode_label"] == "Open throttle"
    assert policy.json()["policy_version"] == "operation-policy/v2"
    assert policy.json()["unsupported_family_behavior"] == "refused"
    assert policy.json()["applies_to"] == "future_operations_only"
    assert policy.json()["precedence"][0] == "hard_invariants"
    assert "schema_safety" in policy.json()["hard_invariants"]

    coder_steering.arm(
        "claude:s1",
        "%5",
        runner=lambda argv, cwd=None: type(
            "Result", (), {"returncode": 0, "stdout": "%5\n", "stderr": ""}
        )(),
    )

    changed = client.put("/api/authority/control-mode", json={"control_mode": "Secure"})
    assert changed.status_code == 200
    assert changed.json()["control_mode_label"] == "Secure"
    assert changed.json()["revoked_coder_grants"] == 1
    assert coder_steering.active_grants() == {}
    assert changed.json()["applies_to"] == "future_operations_only"
    assert client.get("/api/authority/policy").json()["control_mode"] == "safe"
    assert (
        client.put(
            "/api/authority/control-mode", json={"control_mode": "wild"}
        ).status_code
        == 400
    )


