from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db.core import Database
from holdspeak.deployment_revisions import resolve_deployment_revision
from holdspeak.kernel.local_runtime_lease import (
    acquire_local_runtime_lease,
    release_local_runtime_lease,
)
from holdspeak.kernel.model import KernelRefused
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.mcp.families import inference as inference_mcp
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.setup_service import SetupService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.setup import build_setup_router


OWNER = Principal(PrincipalKind.OWNER, "owner")


class _Setup:
    def get_inference_setup(self, _principal):
        return {"schema_version": 1}


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def geturl(self):
        return "http://models.test/model.gguf"


class _InterruptedResponse(_Response):
    def __init__(self, body: bytes):
        super().__init__(body[: len(body) // 2])
        self._reads = 0

    def read(self, size=-1):
        self._reads += 1
        if self._reads > 1:
            raise OSError("connection dropped")
        return super().read(size)


class _RangeResponse(_Response):
    status = 206

    def __init__(self, body: bytes, offset: int):
        super().__init__(body[offset:])
        self.headers = {
            "Content-Range": f"bytes {offset}-{len(body) - 1}/{len(body)}",
        }


def _fixture(tmp_path: Path):
    body = b"GGUF" + b"tiny-safe-model"
    digest = hashlib.sha256(body).hexdigest()
    manifest = {
        "files": [{"path": "model.gguf", "sha256": f"sha256:{digest}", "size": len(body)}]
    }
    manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    preset = {
        "kind": "local_artifact_preset",
        "activation": "download",
        "id": "preset_test_gguf",
        "experience": "quick",
        "label": "Quick test model",
        "summary": "Fast local test model.",
        "runtime_id": "llama_cpp_prompt_v1",
        "runtime_min_revision": "0.3.16",
        "format": "gguf",
        "boundary": "same_device",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {
            "repository": "test/model",
            "revision": "a" * 40,
            "filename": "model.gguf",
            "file_sha256": f"sha256:{digest}",
            "manifest_sha256": manifest_sha,
            "download_bytes": len(body),
            "installed_bytes": len(body),
            "peak_free_bytes": len(body) * 2,
            "license": "Apache-2.0",
        },
        "platforms": ["darwin_arm64"],
        "applicability": {"state": "applicable", "reason": None},
    }
    config = Config()
    db = Database(tmp_path / "holdspeak.db")
    service = InferenceAcquisitionApplicationService(
        db,
        setup_service=_Setup(),
        model_root=tmp_path / "models",
        config_provider=lambda: config,
        config_saver=lambda _config: None,
        opener=lambda *_args, **_kwargs: _Response(body),
        catalog_provider=lambda: {"catalog_revision": 7, "entries": (preset,)},
        source_url_builder=lambda _plan: "http://models.test/model.gguf",
        allowed_download_host=lambda host: host == "models.test",
        auto_recover=False,
    )
    service._submit = lambda _job_id: None
    return db, service, config, preset


def _llama_runtime_ready(monkeypatch) -> None:
    """Pin the optional local runtime for acquisition-state tests.

    The product must report a genuine absent runtime as an activation failure.
    These tests instead exercise the successful durable activation transition,
    independent of what happens to be installed on the test host.
    """
    monkeypatch.setattr(
        "holdspeak.services.inference_acquisition_service.importlib.metadata.version",
        lambda _package: "0.3.34",
    )
    monkeypatch.setattr(
        "holdspeak.services.inference_setup_service._package_available",
        lambda package: package == "llama_cpp",
    )


def test_library_download_request_has_no_route_shaped_fields(tmp_path: Path, monkeypatch):
    _llama_runtime_ready(monkeypatch)
    _db, service, _config, preset = _fixture(tmp_path)
    body = {"request_id": "library-download", "catalog_id": preset["id"], "catalog_revision": 7}
    first = service.download(OWNER, body)
    assert "setup" not in first
    service._run(first["acquisition"]["id"])
    replay = service.download(OWNER, body)
    assert replay["acquisition"]["id"] == first["acquisition"]["id"]
    with pytest.raises(Exception) as route_shaped:
        service.download(OWNER, {**body, "expected_route_revision": "forbidden"})
    assert getattr(route_shaped.value, "code", "") == "inference_acquisition_request_invalid"


def test_download_verify_adopt_activate_and_replay(tmp_path: Path, monkeypatch):
    _llama_runtime_ready(monkeypatch)
    db, service, config, preset = _fixture(tmp_path)
    original_local_model = config.meeting.intel_realtime_model
    original_thought_target = config.thoughts.inference_target_id
    body = {
        "request_id": "request-one",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }

    first = service.download_and_use(OWNER, body)
    service._run(first["acquisition"]["id"])
    complete = service.get_acquisition(OWNER, first["acquisition"]["id"])["acquisition"]

    assert complete["state"] == "ready"
    assert complete["activation_state"] == "not_requested"
    assert complete["verified_bytes"] == preset["source"]["download_bytes"]
    assert config.meeting.intel_realtime_model == original_local_model
    assert config.thoughts.inference_target_id == original_thought_target
    replay = service.download_and_use(OWNER, body)
    assert replay["acquisition"]["id"] == complete["id"]
    assert replay["acquisition"]["state"] == "ready"

    with db._connection() as conn:
        head = conn.execute(
            "SELECT execution_revision_id FROM inference_deployments WHERE artifact_id=?",
            (complete["artifact_id"],),
        ).fetchone()
    assert head is not None
    revision = db.deployment_revisions.get(head["execution_revision_id"])
    assert revision is not None
    assert revision.schema_version == 2
    assert revision.artifact_id == complete["artifact_id"]
    resolved = resolve_deployment_revision(db, revision.id)
    assert resolved is not None
    assert resolved.model_path is not None
    assert "model_path" not in resolved.to_dict()


def test_evaluation_only_candidate_cannot_enter_download_saga(tmp_path: Path):
    _db, service, config, preset = _fixture(tmp_path)
    preset["activation"] = "evaluation_only"
    with pytest.raises(Exception) as refused:
        service.download_and_use(OWNER, {
            "request_id": "hammer-evaluation-only",
            "preset_id": preset["id"],
            "catalog_revision": 7,
            "context_choice": 8192,
            "expected_route_revision": service.route_revision(config),
        })
    assert getattr(refused.value, "code", "") == "inference_preset_evaluation_only"


def test_detected_gguf_can_be_verified_selected_and_replayed(tmp_path: Path, monkeypatch):
    model = tmp_path / "Models" / "gguf" / "already-here.gguf"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"GGUF" + b"existing-model-bytes")
    config = Config()
    original_local_model = config.meeting.intel_realtime_model
    db = Database(tmp_path / "holdspeak.db")
    setup = InferenceSetupApplicationService(
        db, config_provider=lambda: config, home_provider=lambda: tmp_path,
    )
    service = InferenceAcquisitionApplicationService(
        db,
        setup_service=setup,
        model_root=tmp_path / "managed-models",
        config_provider=lambda: config,
        config_saver=lambda _config: None,
        home_provider=lambda: tmp_path,
        auto_recover=False,
    )
    service._submit = lambda _job_id: None
    _llama_runtime_ready(monkeypatch)
    projected = setup.get_inference_setup(OWNER)
    detected = next(row for row in projected["detected_local_artifacts"] if row["label"] == model.name)
    assert detected["activation"]["action"] == "use_existing"
    body = {
        "request_id": "use-existing-one",
        "detected_artifact_id": detected["id"],
        "context_choice": 8192,
        "expected_route_revision": projected["current_routes"]["thoughts"]["revision"],
    }

    started = service.use_existing(OWNER, body)["acquisition"]
    service._run(started["id"])
    complete = service.get_acquisition(OWNER, started["id"])["acquisition"]

    assert complete["state"] == "ready"
    assert complete["activation_state"] == "not_requested"
    assert complete["verified_bytes"] == model.stat().st_size
    assert config.meeting.intel_realtime_model == original_local_model
    assert service.use_existing(OWNER, body)["acquisition"]["id"] == complete["id"]
    # The service implementation remains behind Model Library composition; its
    # old HTTP/MCP public alias has no surviving receipt projection or schema.
    assert "inference.use_existing_model" not in {tool["name"] for tool in inference_mcp.TOOLS}
    with pytest.raises(LookupError):
        inference_mcp.dispatch("inference.use_existing_model", body, OWNER)
    app = FastAPI()

    @app.middleware("http")
    async def existing_owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {}, setup_service=SetupService(db),
        inference_setup_service=setup, inference_acquisition_service=service,
    )))
    client = TestClient(app)
    assert client.post("/api/inference/acquisitions/use-existing", json=body).status_code == 405
    with db._connection() as conn:
        artifact = conn.execute(
            "SELECT source_kind,local_locator FROM inference_model_artifacts WHERE artifact_id=?",
            (complete["artifact_id"],),
        ).fetchone()
    assert dict(artifact) == {
        "source_kind": "existing_local_file",
        "local_locator": str(model),
    }

    with pytest.raises(Exception) as changed:
        service.use_existing(OWNER, {**body, "expected_route_revision": "changed"})
    assert getattr(changed.value, "code", "") == "request_payload_mismatch"


def test_changed_request_refuses_and_route_change_still_leaves_available_model_unassigned(
    tmp_path: Path, monkeypatch
):
    _llama_runtime_ready(monkeypatch)
    _db, service, config, preset = _fixture(tmp_path)
    body = {
        "request_id": "request-two",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    result = service.download_and_use(OWNER, body)
    with pytest.raises(Exception) as changed:
        service.download_and_use(OWNER, {**body, "context_choice": 16384})
    assert getattr(changed.value, "code", "") == "request_payload_mismatch"

    config.thoughts.inference_target_id = "another-ai"
    service._run(result["acquisition"]["id"])
    current = service.get_acquisition(OWNER, result["acquisition"]["id"])["acquisition"]
    assert current["state"] == "ready"
    assert current["activation_state"] == "not_requested"
    assert current["artifact_id"]


def test_minimal_local_runtime_lease_serializes_and_releases(tmp_path: Path):
    db = Database(tmp_path / "holdspeak.db")
    first = acquire_local_runtime_lease(
        db, operation_id="op-a", deployment_revision_id="dep2-a", clock=lambda: 10.0,
    )
    with pytest.raises(KernelRefused) as busy:
        acquire_local_runtime_lease(
            db, operation_id="op-b", deployment_revision_id="dep2-b", clock=lambda: 11.0,
        )
    assert busy.value.reason == "inference_local_runtime_busy"
    with pytest.raises(KernelRefused):
        acquire_local_runtime_lease(
            db, operation_id="op-late", deployment_revision_id="dep2-late",
            clock=lambda: 100_000.0,
        )
    release_local_runtime_lease(db, first, clock=lambda: 12.0)
    second = acquire_local_runtime_lease(
        db, operation_id="op-b", deployment_revision_id="dep2-b", clock=lambda: 13.0,
    )
    assert second.operation_id == "op-b"


def test_cancel_is_idempotent_before_verification_and_cleans_staging(tmp_path: Path):
    _db, service, config, preset = _fixture(tmp_path)
    body = {
        "request_id": "request-cancel",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    started = service.download_and_use(OWNER, body)["acquisition"]
    cancel = {
        "request_id": "cancel-one",
        "expected_revision": started["revision"],
    }

    first = service.cancel(OWNER, started["id"], cancel)
    replay = service.cancel(OWNER, started["id"], cancel)
    assert replay["acquisition"]["revision"] == first["acquisition"]["revision"]
    service._run(started["id"])
    terminal = service.get_acquisition(OWNER, started["id"])["acquisition"]
    assert terminal["state"] == "cancelled"
    assert not (service._root / "staging" / started["id"]).exists()


def test_cancel_after_verification_is_typed_too_late(tmp_path: Path):
    db, service, config, preset = _fixture(tmp_path)
    body = {
        "request_id": "request-too-late",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    started = service.download_and_use(OWNER, body)["acquisition"]
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_model_acquisitions SET state='verifying' WHERE job_id=?",
            (started["id"],),
        )
    with pytest.raises(Exception) as too_late:
        service.cancel(
            OWNER,
            started["id"],
            {"request_id": "cancel-late", "expected_revision": started["revision"]},
        )
    assert getattr(too_late.value, "code", "") == "cancellation_too_late"


def test_retired_acquisition_aliases_disappear_without_replacement_receipt(tmp_path: Path):
    db, service, _config, preset = _fixture(tmp_path)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {},
        setup_service=SetupService(db),
        inference_setup_service=service._setup,
        inference_acquisition_service=service,
    )))
    body = {
        "request_id": "transport-parity",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(_config),
    }
    client = TestClient(app)
    assert client.post("/api/inference/acquisitions/download-and-use", json=body).status_code == 405
    assert client.post("/api/inference/acquisitions/use-existing", json=body).status_code == 405
    assert {
        "inference.download_and_use", "inference.use_existing_model",
    }.isdisjoint({tool["name"] for tool in inference_mcp.TOOLS})
    for name in ("inference.download_and_use", "inference.use_existing_model"):
        with pytest.raises(LookupError):
            inference_mcp.dispatch(name, body, OWNER)


def test_v2_context_ceiling_reaches_the_existing_local_engine_adapter(monkeypatch):
    observed = {}

    class _Intel:
        def __init__(self, **kwargs):
            observed.update(kwargs)

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", _Intel)
    from holdspeak.inference_targets import _local_pinned_engine

    _local_pinned_engine(
        "/owned/model.gguf",
        revision=SimpleNamespace(context_ceiling=8192, model_path=""),
    )

    assert observed == {
        "provider": "local",
        "model_path": "/owned/model.gguf",
        "n_ctx": 8192,
    }


def test_one_active_claim_and_range_resume_converge_on_one_artifact(
    tmp_path: Path, monkeypatch
):
    _llama_runtime_ready(monkeypatch)
    db, service, config, preset = _fixture(tmp_path)
    body = b"GGUF" + b"tiny-safe-model"
    first_body = {
        "request_id": "range-first",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    first = service.download_and_use(OWNER, first_body)["acquisition"]
    duplicate = service.download_and_use(
        OWNER, {**first_body, "request_id": "parallel-owner-gesture"},
    )["acquisition"]
    assert duplicate["id"] == first["id"]

    service._opener = lambda *_args, **_kwargs: _InterruptedResponse(body)
    service._run(first["id"])
    failed = service.get_acquisition(OWNER, first["id"])["acquisition"]
    assert failed["state"] == "failed"
    assert failed["resumable"] is True

    observed_range = []

    def resumed(request, **_kwargs):
        value = request.get_header("Range")
        observed_range.append(value)
        offset = int(value.removeprefix("bytes=").removesuffix("-"))
        return _RangeResponse(body, offset)

    service._opener = resumed
    retry = service.download_and_use(
        OWNER, {**first_body, "request_id": "range-retry"},
    )["acquisition"]
    service._run(retry["id"])
    complete = service.get_acquisition(OWNER, retry["id"])["acquisition"]

    assert observed_range == [f"bytes={len(body) // 2}-"]
    assert complete["state"] == "ready"
    assert complete["activation_state"] == "not_requested"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT count(*) FROM inference_model_artifacts"
        ).fetchone()[0] == 1


def test_corrected_catalog_reuses_matching_integrity_quarantine_without_network(
    tmp_path: Path, monkeypatch
):
    _llama_runtime_ready(monkeypatch)
    db, service, config, preset = _fixture(tmp_path)
    hash_calls = []
    original_hash = service._hash_file

    def tracked_hash(path):
        hash_calls.append(path)
        return original_hash(path)

    monkeypatch.setattr(service, "_hash_file", tracked_hash)
    body = b"GGUF" + b"tiny-safe-model"
    old_file_sha = "sha256:" + ("0" * 64)
    old_manifest = {
        "files": [{
            "path": preset["source"]["filename"],
            "sha256": old_file_sha,
            "size": len(body),
        }]
    }
    old_manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(old_manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    old_preset = {
        **preset,
        "source": {
            **preset["source"],
            "file_sha256": old_file_sha,
            "manifest_sha256": old_manifest_sha,
        },
    }
    service._catalog_provider = lambda: {"catalog_revision": 6, "entries": (old_preset,)}
    old_body = {
        "request_id": "old-integrity-job",
        "preset_id": preset["id"],
        "catalog_revision": 6,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    old = service.download_and_use(OWNER, old_body)["acquisition"]
    quarantine = service._root / "quarantine" / f"{old['id']}.invalid"
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    quarantine.write_bytes(body)
    with db._connection() as conn:
        conn.execute(
            """UPDATE inference_model_acquisitions
                  SET state='failed', error_code='model_download_integrity',
                      error_message='old catalog checksum', resumable=0
                WHERE job_id=?""",
            (old["id"],),
        )

    service._catalog_provider = lambda: {"catalog_revision": 7, "entries": (preset,)}
    service._opener = lambda *_args, **_kwargs: pytest.fail("recovery must not download")
    retry = service.download_and_use(
        OWNER,
        {
            **old_body,
            "request_id": "corrected-integrity-retry",
            "catalog_revision": 7,
        },
    )["acquisition"]
    assert hash_calls == []
    service._run(retry["id"])
    complete = service.get_acquisition(OWNER, retry["id"])["acquisition"]

    assert hash_calls
    assert complete["state"] == "ready"
    assert complete["verified_bytes"] == len(body)
    assert complete["artifact_id"].endswith(
        hashlib.sha256(
            json.dumps(
                {"files": [{
                    "path": preset["source"]["filename"],
                    "sha256": preset["source"]["file_sha256"],
                    "size": len(body),
                }]},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    )
    with db._connection() as conn:
        old_row = conn.execute(
            "SELECT state,error_code,source_plan_json FROM inference_model_acquisitions WHERE job_id=?",
            (old["id"],),
        ).fetchone()
    assert old_row["state"] == "failed"
    assert old_row["error_code"] == "model_download_integrity"
    assert json.loads(old_row["source_plan_json"])["sha256"] == old_file_sha
    assert not quarantine.exists()


def test_legacy_pending_plan_without_peak_bound_continues_after_restart(
    tmp_path: Path, monkeypatch
):
    _llama_runtime_ready(monkeypatch)
    db, service, config, preset = _fixture(tmp_path)
    started = service.download_and_use(OWNER, {
        "request_id": "legacy-pending-plan",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    })["acquisition"]
    with db._connection() as conn:
        row = conn.execute(
            "SELECT source_plan_json FROM inference_model_acquisitions WHERE job_id=?",
            (started["id"],),
        ).fetchone()
        legacy_plan = json.loads(row["source_plan_json"])
        legacy_plan.pop("peak_free_bytes")
        legacy_json = json.dumps(legacy_plan, sort_keys=True, separators=(",", ":"))
        legacy_sha = "sha256:" + hashlib.sha256(legacy_json.encode()).hexdigest()
        conn.execute(
            """UPDATE inference_model_acquisitions
                  SET source_plan_json=?, source_plan_sha256=?, state='requested'
                WHERE job_id=?""",
            (legacy_json, legacy_sha, started["id"]),
        )

    restarted = InferenceAcquisitionApplicationService(
        db,
        setup_service=_Setup(),
        model_root=tmp_path / "models",
        config_provider=lambda: config,
        config_saver=lambda _config: None,
        opener=lambda *_args, **_kwargs: _Response(b"GGUF" + b"tiny-safe-model"),
        catalog_provider=lambda: {"catalog_revision": 7, "entries": (preset,)},
        source_url_builder=lambda _plan: "http://models.test/model.gguf",
        allowed_download_host=lambda host: host == "models.test",
        auto_recover=False,
    )
    restarted._run(started["id"])
    complete = restarted.get_acquisition(OWNER, started["id"])["acquisition"]

    assert complete["state"] == "ready"
    assert complete["verified_bytes"] == preset["source"]["download_bytes"]
    assert complete["artifact_id"]


@pytest.mark.parametrize("case", ["wrong_bytes", "wrong_identity"])
def test_integrity_quarantine_recovery_rejects_wrong_candidate_without_network(
    tmp_path: Path, monkeypatch, case: str
):
    _llama_runtime_ready(monkeypatch)
    db, service, config, preset = _fixture(tmp_path)
    body = b"GGUF" + b"tiny-safe-model"
    free_bytes = [10_000_000_000]
    monkeypatch.setattr(
        "holdspeak.services.inference_acquisition_service.shutil.disk_usage",
        lambda *_args: SimpleNamespace(free=free_bytes[0]),
    )
    old_source = dict(preset["source"])
    if case == "wrong_bytes":
        old_source["file_sha256"] = "sha256:" + ("0" * 64)
        old_manifest = {
            "files": [{
                "path": old_source["filename"],
                "sha256": old_source["file_sha256"],
                "size": old_source["download_bytes"],
            }]
        }
        old_source["manifest_sha256"] = "sha256:" + hashlib.sha256(
            json.dumps(old_manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    else:
        old_source["repository"] = "other/model"
    old_preset = {**preset, "source": old_source}
    service._catalog_provider = lambda: {"catalog_revision": 6, "entries": (old_preset,)}
    old_body = {
        "request_id": f"old-{case}",
        "preset_id": preset["id"],
        "catalog_revision": 6,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(config),
    }
    old = service.download_and_use(OWNER, old_body)["acquisition"]
    quarantine = service._root / "quarantine" / f"{old['id']}.invalid"
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    candidate_body = body if case == "wrong_identity" else body[:-1] + b"X"
    quarantine.write_bytes(candidate_body)
    with db._connection() as conn:
        conn.execute(
            """UPDATE inference_model_acquisitions
                  SET state='failed', error_code='model_download_integrity',
                      error_message='old catalog checksum', resumable=0
                WHERE job_id=?""",
            (old["id"],),
        )

    service._catalog_provider = lambda: {"catalog_revision": 7, "entries": (preset,)}
    hash_calls = []
    original_hash = service._hash_file

    def tracked_hash(path):
        hash_calls.append(path)
        return original_hash(path)

    monkeypatch.setattr(service, "_hash_file", tracked_hash)
    retry = service.download_and_use(
        OWNER,
        {
            **old_body,
            "request_id": f"corrected-{case}",
            "catalog_revision": 7,
        },
    )["acquisition"]
    assert hash_calls == []
    free_bytes[0] = 0
    opener_called = []

    def no_network(*_args, **_kwargs):
        opener_called.append(True)
        pytest.fail("invalid quarantine must not trigger a fresh download")

    service._opener = no_network
    service._run(retry["id"])
    failed = service.get_acquisition(OWNER, retry["id"])["acquisition"]

    assert failed["state"] == "failed"
    assert failed["error"]["code"] == "model_download_disk"
    assert opener_called == []
    assert quarantine.exists()
