"""HS-143-12 S3 — provider command, custody, and readiness proofs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.errors import ConflictError, NotFound, ServiceError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_key_service import ProfileKeyService
from holdspeak.services.profile_service import ProfileService

OWNER = Principal(PrincipalKind.OWNER, "library-provider-owner")


def _library(tmp_path: Path, *, store_path: Path | None = None) -> ModelLibraryApplicationService:
    db = Database(tmp_path / "library-providers.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home",
    )
    keys = ProfileKeyService(db, store=ProfileKeyStore(store_path) if store_path is not None else None)
    return ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition, profile_key_service=keys,
    )


def _draft(
    *,
    request_id: str,
    profile_id: str,
    provider_family: str,
    label: str = "Provider model",
    model: str = "provider/model",
    expected_profile_revision: int = 0,
    requires_key: bool = True,
    endpoint: str = "http://127.0.0.1:9000/v1",
) -> dict[str, object]:
    base: dict[str, object] = {
        "request_id": request_id,
        "profile_id": profile_id,
        "expected_profile_revision": expected_profile_revision,
        "label": label,
        "provider_family": provider_family,
        "model": model,
        "requires_key": requires_key,
    }
    if provider_family not in {"openrouter", "anthropic"}:
        base["endpoint"] = endpoint
    return base


def _head_bytes(service: ModelLibraryApplicationService) -> bytes:
    return json.dumps(service.assignment_heads(OWNER), sort_keys=True, separators=(",", ":")).encode()


def _row(service: ModelLibraryApplicationService, profile_id: str) -> dict[str, object]:
    return next(row for row in service.get_library(OWNER)["rows"] if row["id"] == f"profile:{profile_id}")


def test_hosted_custom_private_and_anthropic_rows_use_server_truth(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # The existing OpenAI-compatible probe's one wire call is the only fake.
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]})
    service = _library(tmp_path)
    before = _head_bytes(service)

    openrouter = service.connect_hosted_model(
        OWNER, _draft(request_id="hosted-1", profile_id="openrouter-main", provider_family="openrouter"), {"value": "openrouter-key"},
    )
    custom = service.define_endpoint(
        OWNER,
        _draft(request_id="custom-1", profile_id="custom-main", provider_family="openai_compatible"),
        {"value": "custom-key"},
    )
    private = service.define_endpoint(
        OWNER,
        _draft(
            request_id="private-1", profile_id="private-main", provider_family="private_endpoint",
            endpoint="http://192.168.1.43:8080/v1",
        ),
        {"value": "private-key"},
    )
    anthropic = service.connect_hosted_model(
        OWNER, _draft(request_id="anthropic-1", profile_id="anthropic-main", provider_family="anthropic"), {"value": "anthropic-key"},
    )

    assert _head_bytes(service) == before
    assert {payload["receipt"]["message"] for payload in (openrouter, custom, private, anthropic)} == {
        "Added to the Model Library. Assignments are unchanged."
    }
    assert _row(service, "openrouter-main")["selected_action"] == "Ready"
    assert _row(service, "custom-main")["selected_action"] == "Ready"
    assert _row(service, "private-main")["selected_action"] == "Ready"
    anthro_row = _row(service, "anthropic-main")
    assert anthro_row["status"] == "broken"
    assert anthro_row["repair"] == {
        "code": "anthropic_runtime_missing", "label": "Anthropic runtime is not installed",
    }
    assert anthro_row["selected_action"] == "Anthropic runtime is not installed"
    # Canonical v2 profile identity has no private endpoint/slot/key material.
    profile = service._profiles.get_profile(OWNER, "private-main")
    encoded = json.dumps(profile, sort_keys=True)
    assert "192.168.1.43" not in encoded
    assert "custom-key" not in encoded
    assert "secret_slot" not in encoded
    # Generated v1 target adapters are private to the aggregate: old target
    # reads retain historical targets but cannot project this endpoint side door.
    targets = ProfileService(service._db).list_inference_targets(OWNER)["targets"]
    assert all(target["id"] != "library_provider_private-main" for target in targets)
    with pytest.raises(NotFound):
        ProfileService(service._db).get_profile(OWNER, "library_provider_private-main")


def test_paired_device_row_uses_existing_liveness_truth(tmp_path: Path) -> None:
    service = _library(tmp_path)
    ProfileService(service._db).create_profile(OWNER, {
        "id": "paired-desk", "name": "Paired desk", "kind": "meshNode", "node": "offline-node", "model": "Remote model",
    })
    before = _head_bytes(service)
    result = service.connect_paired_device(OWNER, {
        "request_id": "paired-1", "profile_id": "paired-main", "expected_profile_revision": 0,
        "label": "Paired desk", "model": "Remote model", "paired_target_id": "paired-desk", "provider_family": "paired_device",
    })
    assert result["receipt"]["assignments_unchanged"] is True
    assert _head_bytes(service) == before
    row = _row(service, "paired-main")
    assert row["status"] == "broken"
    assert row["repair"] == {"code": "destination_offline", "label": "Paired device is offline"}
    assert row["selected_action"] == "Paired device is offline"


def test_provider_cas_changed_payload_replay_and_restart(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": True, "models": []})
    service = _library(tmp_path)
    draft = _draft(request_id="replay-1", profile_id="replay-main", provider_family="openai_compatible")
    before = _head_bytes(service)
    first = service.define_endpoint(OWNER, draft, {"value": "replay-key"})
    assert service.define_endpoint(OWNER, draft, {"value": "ignored-on-replay"}) == first
    assert _head_bytes(service) == before
    changed = {**draft, "label": "Changed model"}
    with pytest.raises(ConflictError) as conflict:
        service.define_endpoint(OWNER, changed, {"value": "replay-key"})
    assert conflict.value.code == "model_library_provider_request_mismatch"
    # A new request with a stale canonical profile head is a true profile CAS
    # conflict, not a library-side last-write-wins update.
    with pytest.raises(ConflictError) as profile_conflict:
        service.define_endpoint(OWNER, {**changed, "request_id": "replay-stale-2"}, {"value": "replay-key"})
    assert profile_conflict.value.code == "model_profile_revision_conflict"

    # A fresh application service over the real DB replays its nonsecret receipt.
    restarted = _library(tmp_path)
    assert restarted.define_endpoint(OWNER, draft, {"value": "another-key"}) == first
    assert _head_bytes(restarted) == before


def test_delayed_key_store_confirmation_leaves_command_retriable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": True, "models": []})
    blocked_parent = tmp_path / "blocked-parent"
    blocked_parent.write_text("not a directory")
    service = _library(tmp_path, store_path=blocked_parent / "keys.json")
    draft = _draft(request_id="delayed-1", profile_id="delayed-main", provider_family="openai_compatible")
    before = _head_bytes(service)
    with pytest.raises(ServiceError) as unavailable:
        service.define_endpoint(OWNER, draft, {"value": "retry-key"})
    assert unavailable.value.code == "profile_key_store_unavailable"
    assert _head_bytes(service) == before
    with service._db._connection() as conn:
        state = conn.execute("SELECT state,response_json FROM model_library_provider_commands WHERE request_id='delayed-1'").fetchone()
    assert tuple(state) == ("pending", None)

    blocked_parent.unlink()
    result = service.define_endpoint(OWNER, draft, {"value": "retry-key"})
    assert result["provider"]["secret"] == {"required": True, "present": True}
    assert _head_bytes(service) == before


def test_each_broken_provider_row_has_exactly_one_server_repair(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": False, "detail": "ignored private wire error"})
    service = _library(tmp_path)
    # Missing key, unreachable endpoint, and no adapter must all remain visible.
    service.define_endpoint(
        OWNER, _draft(request_id="missing-1", profile_id="missing-main", provider_family="openai_compatible"), None,
    )
    service.define_endpoint(
        OWNER, _draft(request_id="offline-1", profile_id="offline-main", provider_family="private_endpoint", requires_key=False), None,
    )
    service.connect_hosted_model(
        OWNER, _draft(request_id="anthro-1", profile_id="anthro-main", provider_family="anthropic"), {"value": "key"},
    )
    for profile_id in ("missing-main", "offline-main", "anthro-main"):
        row = _row(service, profile_id)
        assert row["status"] == "broken"
        assert isinstance(row["repair"], dict)
        assert set(row["repair"]) == {"code", "label"}
        assert row["selected_action"] == row["repair"]["label"]
