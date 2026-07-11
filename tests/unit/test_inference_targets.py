"""HS-92-07 canonical destination identities and profile alias behavior."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import (
    resolve_inference_target,
    target_from_profile,
)
from holdspeak.intel.providers import profile_key_env
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "targets.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_five_destination_kinds_are_independent_of_engine_and_model(rig) -> None:
    db, _ = rig
    profiles = [
        db.profiles.upsert(profile_id="local", name="This iMac", kind="onDevice", model_file="q.gguf"),
        db.profiles.upsert(profile_id="pair", name="Studio", kind="desktop", model="Qwen"),
        db.profiles.upsert(profile_id="lan", name="LAN box", kind="openAICompatible",
                           base_url="http://192.168.1.43:8000/v1", model="Qwen"),
        db.profiles.upsert(profile_id="mesh", name="Garage node", kind="meshNode", node="garage"),
        db.profiles.upsert(profile_id="svc", name="OpenRouter", kind="openAICompatible",
                           base_url="https://openrouter.ai/api/v1", model="claude"),
    ]
    kinds = [target_from_profile(profile).kind for profile in profiles]
    assert kinds == [
        "this_device", "paired_device", "private_endpoint", "mesh_node", "external_service"
    ]
    assert target_from_profile(profiles[2]).model == "Qwen"
    assert target_from_profile(profiles[2]).engine == "openai_compatible"


def test_required_key_refuses_without_leaking_or_borrowing_another_key(rig, monkeypatch) -> None:
    db, _ = rig
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-borrowed")
    monkeypatch.delenv(profile_key_env("svc"), raising=False)
    profile = db.profiles.upsert(
        profile_id="svc", name="External service", kind="openAICompatible",
        base_url="https://example.com/v1", requires_key=True,
    )
    target = target_from_profile(profile, db)
    payload = target.to_dict()
    assert target.readiness_state == "needs_key"
    assert payload["secret"] == {"required": True, "present": False}
    assert "must-not-be-borrowed" not in str(payload)
    assert profile_key_env("svc") in target.readiness_reason


def test_unknown_target_is_named_and_never_retargeted(rig) -> None:
    db, _ = rig
    target = resolve_inference_target(db, "gone")
    assert target.id == "gone"
    assert target.ready is False
    assert "gone" in target.readiness_reason


def test_inference_target_api_round_trips_through_profile_alias(rig) -> None:
    _, client = rig
    created = client.post("/api/inference-targets", json={
        "id": "lan", "name": "Studio box", "kind": "private_endpoint",
        "endpoint": "http://10.0.0.8:8000/v1", "model": "Qwen",
        "contextLimit": 32768,
    })
    assert created.status_code == 201, created.text
    target = created.json()["inference_target"]
    assert target["kind"] == "private_endpoint"
    assert target["profile_alias"] == {"resource": "profile", "version": 1, "id": "lan"}

    legacy = client.get("/api/profiles/lan").json()["profile"]
    assert legacy["kind"] == "openAICompatible"
    assert legacy["base_url"] == "http://10.0.0.8:8000/v1"
    assert legacy["context_limit"] == 32768

    updated = client.put("/api/profiles/lan", json={"model": "Qwen-2"})
    assert updated.status_code == 200
    assert client.get("/api/inference-targets/lan").json()["inference_target"]["model"] == "Qwen-2"
    alias = client.get("/api/inference-targets").json()["profile_alias"]
    assert alias["removal"] == "not_before_inference_target_v3"


def test_target_api_rejects_secret_fields(rig) -> None:
    _, client = rig
    response = client.post("/api/inference-targets", json={
        "name": "Nope", "kind": "external_service", "api_key": "sk-secret",
    })
    assert response.status_code == 400
    assert "sk-secret" not in response.text


def test_attempt_round_trips_actual_placement(rig) -> None:
    db, _ = rig
    db.capability_invocations.begin(invocation_id="run", definition_ref="persona:scout")
    placement = {
        "target_id": "lan", "target_name": "LAN box", "target_kind": "private_endpoint",
        "boundary": "private_network", "transport": "https", "engine": "openai_compatible",
        "model": "Qwen", "data_classes": ["instruction", "generated_output"],
        "fallback_reason": None,
    }
    db.capability_invocations.start_attempt(
        invocation_id="run", attempt_id="attempt", destination="lan",
        actual_placement=placement,
    )
    assert db.capability_invocations.get("run").attempts[0].actual_placement == placement


def test_doctor_names_destination_class_and_unavailable_reason(rig, monkeypatch) -> None:
    db, _ = rig
    db.profiles.upsert(
        profile_id="svc", name="Vendor", kind="openAICompatible",
        base_url="https://example.com/v1", requires_key=True,
    )
    monkeypatch.delenv(profile_key_env("svc"), raising=False)
    from holdspeak.commands.doctor import _check_inference_targets

    check = _check_inference_targets()
    assert check.status == "WARN"
    assert "Vendor: external service · external_service · unavailable" in check.detail
    assert "needs a key" in check.detail


def test_dead_endpoint_or_rejected_token_refuses_with_target_name(rig, monkeypatch) -> None:
    db, client = rig
    profile = db.profiles.upsert(
        profile_id="vendor", name="Named vendor", kind="openAICompatible",
        base_url="https://example.com/v1", requires_key=False,
    )
    from holdspeak.intel.models import MeetingIntelError

    class Rejected:
        active_provider = "cloud"

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("401 rejected token")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **kwargs: Rejected(),
    )
    response = client.post("/api/ask", json={
        "prompt": "go", "inference_target_id": profile.id,
    })
    assert response.status_code == 502
    assert response.json()["error"] == (
        "Destination 'Named vendor' refused the run: 401 rejected token"
    )
    assert response.json()["alternate_target_id"] == "this_machine"
