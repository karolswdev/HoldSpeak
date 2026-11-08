"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/unit/test_inference_targets.py``: test_hub_default_summary_names_only_an_available_local_model, test_inference_target_api_round_trips_through_target_contract. Not collected.
"""
from __future__ import annotations
"""HS-92-07 canonical destination identities and profile alias behavior."""


from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import (
    resolve_inference_target,
    resolve_thought_placement,
    target_from_profile,
    this_machine_target,
)
from holdspeak.intel.providers import profile_key_env
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.setup_service import SetupService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router, build_setup_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "targets.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "target-test-owner")
        return await call_next(request)

    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_hub_default_summary_names_only_an_available_local_model(
    tmp_path, monkeypatch
) -> None:
    model = tmp_path / "Qwen3.5-4B-Instruct-Q4_K_M.gguf"
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(
            meeting=SimpleNamespace(intel_realtime_model=str(model))
        ),
    )
    app = FastAPI()
    app.include_router(
        build_setup_router(
            WebContext(
                get_state=lambda: {},
                setup_service=SetupService(Database(tmp_path / "setup.db")),
                inference_setup_service=InferenceSetupApplicationService(
                    Database(tmp_path / "setup.db")
                ),
            )
        )
    )
    client = TestClient(app)

    assert client.get("/api/setup/hub-default-summary").json() == {
        "engine": "",
        "model": "",
        "available": False,
    }

    model.touch()
    assert client.get("/api/setup/hub-default-summary").json() == {
        "engine": "llama.cpp",
        "model": "Qwen3.5-4B-Instruct-Q4_K_M",
        "available": True,
    }


def test_inference_target_api_round_trips_through_target_contract(rig) -> None:
    """HS-134-02: the target contract is the only read shape; profile_alias
    is deleted, endpoint/node ride the target response directly."""
    _, client = rig
    created = client.post(
        "/api/inference-targets",
        json={
            "id": "lan",
            "name": "Studio box",
            "kind": "private_endpoint",
            "endpoint": "http://10.0.0.8:8000/v1",
            "model": "Qwen",
            "contextLimit": 32768,
        },
    )
    assert created.status_code == 201, created.text
    target = created.json()["inference_target"]
    assert target["kind"] == "private_endpoint"
    # profile_alias retired (HS-134-02); endpoint/node surfaced instead.
    assert "profile_alias" not in target
    assert target["endpoint"] == "http://10.0.0.8:8000/v1"
    assert target["node"] == ""

    # The target contract carries endpoint/node — no /api/profiles read needed.
    got = client.get("/api/inference-targets/lan").json()["inference_target"]
    assert got["endpoint"] == "http://10.0.0.8:8000/v1"
    assert got["context_limit"] == 32768

    # Writes still go through the target API.
    refused = client.put("/api/profiles/lan", json={"model": "Qwen-2"})
    assert refused.status_code == 405
    updated = client.put("/api/inference-targets/lan", json={"model": "Qwen-2"})
    assert updated.status_code == 200
    assert (
        client.get("/api/inference-targets/lan").json()["inference_target"]["model"]
        == "Qwen-2"
    )
    # profile_alias block retired from list response too.
    listed = client.get("/api/inference-targets").json()
    assert "profile_alias" not in listed


