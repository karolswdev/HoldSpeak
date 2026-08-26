"""HS-143-12 S2 — local library additions remain availability-only."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService

OWNER = Principal(PrincipalKind.OWNER, "library-local-owner")


def _library(tmp_path: Path) -> tuple[ModelLibraryApplicationService, Path]:
    db = Database(tmp_path / "library-local.db")
    home = tmp_path / "home"
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: home)
    acquisition = InferenceAcquisitionApplicationService(db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: home)
    return ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition), home


def _wait(service: ModelLibraryApplicationService, job_id: str) -> dict[str, object]:
    for _ in range(100):
        acquisition = service._acquisition.get_acquisition(OWNER, job_id)["acquisition"]
        if acquisition["state"] in {"ready", "failed", "indeterminate"}:
            return acquisition
        time.sleep(0.02)
    raise AssertionError("local adoption did not complete")


def test_detected_gguf_add_replay_and_conflict_keep_assignment_heads(tmp_path: Path) -> None:
    library, home = _library(tmp_path)
    model = home / "Models" / "gguf" / "owner-model.gguf"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"GGUF" + b"fixture-model")
    detected = next(row for row in library.get_library(OWNER)["rows"] if row["source"] == "detected")
    before = library.assignment_heads(OWNER)
    first = library.add_to_library(OWNER, {"request_id": "detected-add", "detected_artifact_id": detected["id"].removeprefix("detected:")})
    finished = _wait(library, first["acquisition"]["id"])
    assert finished["state"] == "ready"
    assert first["receipt"]["message"] == "Added to the Model Library. Assignments are unchanged."
    assert first["receipt"]["assignments_unchanged"] is True
    assert first["receipt"]["assignments_before"] == first["receipt"]["assignments_after"] == before
    replay = library.add_to_library(OWNER, {"request_id": "detected-add", "detected_artifact_id": detected["id"].removeprefix("detected:")})
    assert replay["receipt"]["assignments_before"] == before
    # A fresh service process reads the durable request ledger and still proves
    # the same canonical assignment head, rather than repeating an add path.
    restarted, _same_home = _library(tmp_path)
    restart_replay = restarted.add_to_library(OWNER, {"request_id": "detected-add", "detected_artifact_id": detected["id"].removeprefix("detected:")})
    assert restart_replay["receipt"]["assignments_before"] == restart_replay["receipt"]["assignments_after"] == before
    with pytest.raises(ServiceError) as changed:
        library.add_to_library(OWNER, {"request_id": "detected-add", "detected_artifact_id": "detected_other"})
    assert changed.value.code == "request_payload_mismatch"
    assert library.assignment_heads(OWNER) == before


def test_hub_staged_gguf_is_ingested_without_projecting_locator(tmp_path: Path) -> None:
    library, _home = _library(tmp_path)
    staging = tmp_path / "hub-staging.gguf"
    staging.write_bytes(b"GGUF" + b"uploaded-fixture")
    before = library.assignment_heads(OWNER)
    result = library.use_model_file(OWNER, request_id="upload-add", filename="uploaded.gguf", staging_path=staging)
    assert not staging.exists()
    assert result["receipt"]["assignments_before"] == result["receipt"]["assignments_after"] == before
    assert result["receipt"]["message"] == "Added to the Model Library. Assignments are unchanged."
    rendered = json.dumps(result, sort_keys=True)
    assert str(tmp_path) not in rendered
    assert "local_locator" not in rendered
    assert "expected_route_revision" not in rendered


def test_hub_staged_mlx_is_retained_with_one_runtime_repair(tmp_path: Path) -> None:
    library, _home = _library(tmp_path)
    staging = tmp_path / "hub-staging.safetensors"
    staging.write_bytes(b"mlx-fixture")
    result = library.use_model_file(OWNER, request_id="upload-mlx", filename="model.safetensors", staging_path=staging)
    assert not staging.exists()
    assert result["acquisition"]["state"] == "ready"
    assert result["acquisition"]["activation_state"] == "failed"
    projection = library.get_library(OWNER)
    mlx_rows = [row for row in projection["rows"] if row["source"] == "installed" and row["detail"].get("format") == "mlx_safetensors"]
    assert mlx_rows
    assert all(row["repair"] == {"code": "mlx_runtime_unavailable", "label": "MLX runtime is not installed"} for row in mlx_rows)
    assert str(staging) not in json.dumps(result)
