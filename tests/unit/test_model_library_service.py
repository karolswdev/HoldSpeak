"""HS-143-12 S1 — ModelLibraryProjection@1 authority proofs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import MODEL_LIBRARY_SCHEMA, ModelLibraryApplicationService
from holdspeak.services.model_profile_service import ModelProfileService

OWNER = Principal(PrincipalKind.OWNER, "library-owner")
AGENT = Principal(PrincipalKind.AGENT, "library-agent")


def _manifest() -> dict[str, object]:
    import hashlib
    material = {"claims": ["language"], "revision": "library-fixture"}
    return {**material, "sha256": "sha256:" + hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def _service(tmp_path: Path) -> ModelLibraryApplicationService:
    db = Database(tmp_path / "library.db")
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path / "home",
    )
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home",
    )
    return ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition)


def test_projection_is_aggregate_owner_safe_and_action_closed(tmp_path: Path) -> None:
    service = _service(tmp_path)
    projection = service.get_library(OWNER)
    assert projection["schema"] == MODEL_LIBRARY_SCHEMA
    assert projection["rows"]
    assert set(projection["summary"]) == {"state", "label", "ready_count", "attention_count"}
    assert projection["summary"]["state"] in {"empty", "ready", "attention"}
    assert projection["summary"]["label"] in {"Add model", "Ready", "Needs attention"}
    closed = {"Download", "Add to library", "Connect", "Add model", "Ready", "Checking", "Try again"}
    assert {row["selected_action"] for row in projection["rows"]} <= closed
    assert all(row["selected_action"] == "Connect" for row in projection["rows"] if row["source"] == "catalog" and "OpenRouter" in row["label"])
    encoded = json.dumps(projection, sort_keys=True)
    for forbidden in ("Use model", "In use", "Download & use", "Connect & use", "Test", "assignment", "secret_slot"):
        assert forbidden not in encoded
    for row in projection["rows"]:
        assert set(row) == {"id", "source", "label", "status", "detail", "repair", "selected_action"}
        assert row["repair"] is None or set(row["repair"]) == {"code", "label"}
        assert "/" not in row["label"]


def test_empty_projection_invites_an_add_from_server_facts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(tmp_path)
    monkeypatch.setattr(service, "_rows", lambda *_: [])

    summary = service.get_library(OWNER)["summary"]

    assert summary == {
        "state": "empty",
        "label": "Add model",
        "ready_count": 0,
        "attention_count": 0,
    }


def test_profile_rows_keep_one_repair_and_no_locator_or_secret(tmp_path: Path) -> None:
    service = _service(tmp_path)
    ModelProfileService(service._db).create_profile(OWNER, {
        "profile_id": "library-balanced", "expected_revision": 0, "label": "Balanced",
        "provider_family": "local", "runtime_family": "llama_cpp_prompt_v1",
        "model_or_artifact_identity": "artifact-balanced", "supported_modalities": ["language"],
        "context_support": "bounded", "tokenizer_template_requirements": {},
        "capability_manifest": _manifest(), "safe_presentation": {"summary": "General"},
    })
    row = next(row for row in service.get_library(OWNER)["rows"] if row["id"] == "profile:library-balanced")
    assert row["repair"] == {"code": "binding_missing", "label": "Model needs a deployment binding"}
    assert row["selected_action"] == "Add model"
    assert "secret" not in json.dumps(row).lower()
    assert "/" not in json.dumps(row)


def test_owner_matrix_and_assignment_snapshot_are_read_only(tmp_path: Path) -> None:
    service = _service(tmp_path)
    before = service.assignment_heads(OWNER)
    assert before == {"heads": [], "sha256": before["sha256"]}
    for principal in (None, AGENT, Principal(PrincipalKind.SERVICE, "model-turn")):
        with pytest.raises(ServiceError) as refusal:
            service.get_library(principal)  # type: ignore[arg-type]
        assert refusal.value.code == "model_library_owner_required"
    assert service.assignment_heads(OWNER) == before
