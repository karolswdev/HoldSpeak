from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db.core import Database
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.inference_targets import DeploymentIdentity, InferenceTarget
from holdspeak.inference_setup_catalog import (
    PACKAGED_CATALOG_SHA256,
    applicable_presets,
    packaged_catalog_envelope_json,
    packaged_presets,
    verify_catalog_envelope,
    validate_catalog,
)
from holdspeak.mcp import resources
from holdspeak.mcp import server as mcp_server
from holdspeak.mcp.auth import MCPAuth
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_setup_service import (
    InferenceSetupApplicationService,
    _execution_support,
    _this_machine_from_config,
    inspect_local_artifacts,
    load_config_read_only,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.setup import build_setup_router
from holdspeak.services.setup_service import SetupService


OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "agent")
NOW = datetime(2026, 8, 21, 12, 30, tzinfo=timezone.utc)


def _service(tmp_path: Path, *, config: Config | None = None):
    db = Database(tmp_path / "holdspeak.db")
    cfg = config or Config()
    return db, InferenceSetupApplicationService(
        db,
        config_provider=lambda: cfg,
        home_provider=lambda: tmp_path,
        clock=lambda: NOW,
    )


def _all_strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _all_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_strings(child)
    elif isinstance(value, str):
        yield value


def test_projection_is_closed_redacted_and_preserves_v1_identity(tmp_path: Path):
    model = tmp_path / "Models" / "gguf" / "private-model.gguf"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"GGUFnot-loaded")
    cfg = Config()
    cfg.meeting.intel_realtime_model = str(model)
    db, service = _service(tmp_path, config=cfg)

    value = service.get_inference_setup(OWNER)

    assert set(value) == {
        "schema_version", "observed_at", "hardware", "runtimes", "current_routes",
        "current_thought_deployment", "artifact_detection", "detected_local_artifacts", "preset_catalog",
        "installed_model_artifacts", "acquisitions", "presets", "limitations",
    }
    assert value["schema_version"] == 1
    assert value["observed_at"] == "2026-08-21T12:30:00Z"
    current = value["current_thought_deployment"]
    assert set(current) == {"source", "configured_target_id", "target", "readiness", "execution_support", "execution_revision"}
    assert current["readiness"] == {"state": "ready", "available": True, "reason": None}
    assert current["execution_support"]["state"] in {"executable", "unsupported"}
    assert current["execution_support"]["executable"] is (
        current["execution_support"]["state"] == "executable"
    )
    assert current["execution_revision"]["schema_version"] == 1
    expected = DeploymentRevision.from_identity(
        _this_machine_from_config(cfg).deployment
    )
    assert current["execution_revision"]["id"] == expected.id
    assert value["artifact_detection"] == {"state": "complete", "reason": None}
    assert value["preset_catalog"] == {
        "schema_version": 1,
        "catalog_revision": 2,
        "generated_at": "2026-08-21T00:00:00Z",
        "expires_at": "2036-08-01T00:00:00Z",
        "signing_key_id": "holdspeak_catalog_2026_03",
        "sha256": PACKAGED_CATALOG_SHA256,
    }
    assert value["detected_local_artifacts"][0]["label"] == model.name
    assert value["detected_local_artifacts"][0]["thought_support"]["state"] == "current_v1"
    material = "\n".join(_all_strings(value))
    assert str(tmp_path) not in material
    assert "OPENAI_API_KEY" not in material


def test_first_and_repeated_reads_do_not_mutate_database_or_config(tmp_path: Path):
    config_path = tmp_path / "config.json"
    cfg = Config()
    cfg.meeting.intel_provider = "cloud"
    cfg.meeting.intel_cloud_base_url = "https://legacy.invalid/v1"
    config_path.write_text(json.dumps(asdict(cfg), sort_keys=True), encoding="utf-8")
    db = Database(tmp_path / "holdspeak.db")
    service = InferenceSetupApplicationService(
        db,
        config_provider=lambda: load_config_read_only(config_path),
        home_provider=lambda: tmp_path,
        clock=lambda: NOW,
    )
    before_config = config_path.read_bytes()
    before_stat = (config_path.stat().st_size, config_path.stat().st_mtime_ns)
    def db_files():
        return {
            path.name: (path.read_bytes(), path.stat().st_size, path.stat().st_mtime_ns)
            for path in tmp_path.glob("holdspeak.db*")
            if path.is_file()
        }
    before_db = db_files()

    first = service.get_inference_setup(OWNER)
    second = service.get_inference_setup(OWNER)

    assert first == second
    assert config_path.read_bytes() == before_config
    assert (config_path.stat().st_size, config_path.stat().st_mtime_ns) == before_stat
    assert db_files() == before_db
    assert db.profiles.list() == []


def test_read_only_config_loader_does_not_create_missing_file(tmp_path: Path):
    path = tmp_path / "missing.json"
    cfg = load_config_read_only(path)
    assert isinstance(cfg, Config)
    assert not path.exists()


def test_empty_config_uses_exact_canonical_default_deployment_identity(tmp_path: Path):
    from holdspeak.intel.providers import configured_local_meeting_model_path
    from holdspeak.inference_targets import this_machine_target_from_model_path

    cfg = Config()
    _db, service = _service(tmp_path, config=cfg)
    projected = service.get_inference_setup(OWNER)["current_thought_deployment"]
    canonical = this_machine_target_from_model_path(
        configured_local_meeting_model_path(meeting=cfg.meeting)
    )

    assert projected["execution_revision"]["id"] == DeploymentRevision.from_identity(
        canonical.deployment
    ).id
    assert projected["target"]["model"] == canonical.model


def test_default_read_only_loader_resolves_active_config_path_at_call_time(tmp_path: Path, monkeypatch):
    active = tmp_path / "active.json"
    cfg = Config()
    cfg.thoughts.inference_target_id = "active-target"
    active.write_text(json.dumps(asdict(cfg)), encoding="utf-8")
    before = active.read_bytes()
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", active)

    loaded = load_config_read_only()

    assert loaded.thoughts.inference_target_id == "active-target"
    assert active.read_bytes() == before


def test_packaged_catalog_rejects_unknown_key_bad_signature_rollback_and_expiry():
    original = json.loads(packaged_catalog_envelope_json())
    cases = [
        ({**original, "signing_key_id": "unknown"}, "unknown"),
        ({**original, "signature": "00" * 64}, "signature"),
        ({**original, "catalog_revision": 0}, "rolled back"),
    ]
    for envelope, message in cases:
        with pytest.raises(ValueError, match=message):
            verify_catalog_envelope(json.dumps(envelope, sort_keys=True, separators=(",", ":")), now=NOW)
    with pytest.raises(ValueError, match="validity period"):
        verify_catalog_envelope(
            packaged_catalog_envelope_json(),
            now=datetime(2037, 1, 1, tzinfo=timezone.utc),
        )


def test_catalog_expiry_is_rechecked_on_every_projection(tmp_path: Path):
    current = [NOW]
    db = Database(tmp_path / "holdspeak.db")
    service = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path,
        clock=lambda: current[0],
    )
    assert service.get_inference_setup(OWNER)["preset_catalog"]["catalog_revision"] == 2
    current[0] = datetime(2037, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="validity period"):
        service.get_inference_setup(OWNER)


def test_owner_gate_and_safe_missing_path(tmp_path: Path):
    cfg = Config()
    cfg.meeting.intel_realtime_model = str(tmp_path / "private" / "gone.gguf")
    _db, service = _service(tmp_path, config=cfg)
    with pytest.raises(ServiceError, match="Owner access") as caught:
        service.get_inference_setup(AGENT)
    assert caught.value.code == "inference_setup_owner_required"

    value = service.get_inference_setup(OWNER)
    assert value["current_thought_deployment"]["readiness"] == {
        "state": "unavailable", "available": False,
        "reason": "Configured Thought model is missing.",
    }
    assert str(tmp_path) not in json.dumps(value)


def test_catalog_is_closed_and_filters_unproven_local_entries(tmp_path: Path):
    packaged = packaged_presets()
    assert len(validate_catalog(packaged)) == 4
    assert len(applicable_presets(platform_id="darwin_arm64", runtime_ids=set())) == 3
    forged = dict(packaged[0])
    forged["download_url"] = "https://mutable.invalid/latest"
    with pytest.raises(ValueError, match="invalid fields"):
        validate_catalog([forged])

    local = {
        "kind": "local_artifact_preset", "id": "local_test", "experience": "quick",
        "label": "Local test", "runtime_id": "llama_cpp_prompt_v1", "runtime_min_revision": "0.3.34", "format": "gguf",
        "boundary": "same_device", "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192}, "platforms": ["linux_x86_64"],
        "source": {"repository": "example/model", "revision": "a" * 40,
                   "filename": "model.gguf", "file_sha256": "sha256:" + "a" * 64,
                   "manifest_sha256": "sha256:" + "b" * 64,
                   "download_bytes": 10, "installed_bytes": 10,
                   "peak_free_bytes": 20, "license": "Apache-2.0"},
        "applicability": {"state": "applicable", "reason": None},
    }
    assert applicable_presets(platform_id="darwin_arm64", runtime_ids={"llama_cpp_prompt_v1"}, entries=[local]) == []
    assert len(applicable_presets(platform_id="linux_x86_64", runtime_ids={"llama_cpp_prompt_v1"}, entries=[local])) == 1

def test_artifact_inspection_rejects_junk_and_symlinks_and_reports_execution_truth(tmp_path: Path):
    root = tmp_path / "Models" / "gguf"
    root.mkdir(parents=True)
    junk = root / "junk.gguf"
    junk.write_bytes(b"not a model")
    real = tmp_path / "outside.gguf"
    real.write_bytes(b"GGUFvalid")
    (root / "dangling.gguf").symlink_to(tmp_path / "missing.gguf")
    (root / "linked.gguf").symlink_to(real)
    cfg = Config()
    cfg.meeting.intel_realtime_model = str(junk)
    _db, service = _service(tmp_path, config=cfg)

    value = service.get_inference_setup(OWNER)

    assert value["artifact_detection"] == {"state": "complete", "reason": None}
    assert value["detected_local_artifacts"] == []
    assert value["current_thought_deployment"]["readiness"]["available"] is True
    assert value["current_thought_deployment"]["execution_support"] == {
        "state": "unavailable",
        "executable": False,
        "reason": "Configured local model is not a valid GGUF artifact.",
    }


def test_custom_on_device_target_does_not_become_executable_from_readiness_alone(tmp_path: Path):
    junk = tmp_path / "custom.gguf"
    junk.write_bytes(b"junk")
    deployment = DeploymentIdentity(
        destination_id="custom", kind="this_device", engine="local", model="custom",
        node="", boundary="same_device", model_path=str(junk),
    )
    target = InferenceTarget(
        id="custom", name="Custom", kind="this_device", boundary="same_device",
        owner="you", transport="in_process", profile_id="custom", engine="local",
        model="custom", context_limit=4096, readiness_state="ready", deployment=deployment,
    )

    assert _execution_support(target, [], []) == {
        "state": "unavailable", "executable": False,
        "reason": "Configured local model is not a valid GGUF artifact.",
    }


def test_scan_caps_before_collection_marks_partial_and_prioritizes_configured(tmp_path: Path, monkeypatch):
    import holdspeak.services.inference_setup_service as module

    root = tmp_path / "Models" / "gguf"
    root.mkdir(parents=True)
    configured = root / "z-configured.gguf"
    configured.write_bytes(b"GGUFconfigured")
    for name in ("a.gguf", "b.gguf", "c.gguf"):
        (root / name).write_bytes(b"GGUFcandidate")
    cfg = Config()
    cfg.meeting.intel_realtime_model = str(configured)
    target = _this_machine_from_config(cfg)
    monkeypatch.setattr(module, "_MAX_DIRECTORY_ENTRIES", 2)
    monkeypatch.setattr(module, "_MAX_DETECTED", 1)

    rows, detection = inspect_local_artifacts(home=tmp_path, current_target=target)

    assert rows[0]["label"] == configured.name
    assert rows[0]["configured_for_thoughts"] is True
    assert detection["state"] == "partial"


def test_detected_ids_do_not_depend_on_absolute_home(tmp_path: Path):
    ids = []
    for name in ("home-a", "home-b"):
        home = tmp_path / name
        model = home / "Models" / "gguf" / "same.gguf"
        model.parent.mkdir(parents=True)
        model.write_bytes(b"GGUFsame")
        cfg = Config()
        cfg.meeting.intel_realtime_model = str(model)
        _db, service = _service(home, config=cfg)
        ids.append(service.get_inference_setup(OWNER)["detected_local_artifacts"][0]["id"])
    assert ids[0] == ids[1]


def test_local_preset_union_and_mlx_runtime_use_real_dependency(tmp_path: Path, monkeypatch):
    local = {
        "kind": "local_artifact_preset", "id": "local_test", "experience": "quick",
        "label": "Local test", "runtime_id": "mlx_text_v1", "runtime_min_revision": "0.1.0", "format": "mlx_safetensors",
        "boundary": "same_device", "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192}, "platforms": ["darwin_arm64"],
        "source": {"repository": "example/model", "revision": "a" * 40,
                   "filename": "model.gguf", "file_sha256": "sha256:" + "a" * 64,
                   "manifest_sha256": "sha256:" + "b" * 64,
                   "download_bytes": 10, "installed_bytes": 10,
                   "peak_free_bytes": 20, "license": "Apache-2.0"},
        "applicability": {"state": "applicable", "reason": None},
    }
    monkeypatch.setattr("holdspeak.services.inference_setup_service.platform.system", lambda: "Darwin")
    monkeypatch.setattr("holdspeak.services.inference_setup_service.platform.machine", lambda: "arm64")
    monkeypatch.setattr(
        "holdspeak.services.inference_setup_service._package_available",
        lambda module: module == "mlx_lm",
    )
    _db, service = _service(tmp_path)

    value = service.get_inference_setup(OWNER)

    assert value["runtimes"][1]["id"] == "mlx_text_v1"
    assert value["runtimes"][1]["availability"]["state"] == "available"
    assert applicable_presets(
        platform_id="darwin_arm64", runtime_ids={"mlx_text_v1"}, entries=[local]
    ) == [local]


def test_http_and_mcp_share_exact_envelope_and_agent_cannot_discover(tmp_path: Path, monkeypatch):
    db, service = _service(tmp_path)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {}, setup_service=SetupService(db), inference_setup_service=service,
    )))
    http = TestClient(app).get("/api/inference/setup")
    assert http.status_code == 200
    monkeypatch.setattr(resources, "get_database", lambda: db)
    monkeypatch.setattr(resources, "InferenceSetupApplicationService", lambda _db: service)
    content = resources.read_resource("holdspeak://inference/setup", OWNER)
    mcp = json.loads(content["contents"][0]["text"])
    assert mcp == http.json()

    owner_catalog = resources.list_resources(OWNER)
    agent_catalog = resources.list_resources(AGENT)
    assert any(row["uri"] == "holdspeak://inference/setup" for row in owner_catalog["resources"])
    assert all(row["uri"] != "holdspeak://inference/setup" for row in agent_catalog["resources"])
    with pytest.raises(ServiceError) as caught:
        monkeypatch.setattr(resources, "get_database", lambda: pytest.fail("denied read touched DB"))
        resources.read_resource("holdspeak://inference/setup", AGENT)
    assert caught.value.code == "inference_setup_owner_required"

    monkeypatch.setattr(mcp_server, "resolve_auth", lambda: MCPAuth(AGENT))
    listed = mcp_server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "resources/list"})
    assert all(
        row["uri"] != "holdspeak://inference/setup"
        for row in listed["result"]["resources"]
    )
    denied = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 2, "method": "resources/read",
        "params": {"uri": "holdspeak://inference/setup"},
    })
    assert denied["error"]["data"]["code"] == "inference_setup_owner_required"


def test_http_agent_is_denied_and_projection_performs_no_runner_or_revision_write(tmp_path: Path, monkeypatch):
    db, service = _service(tmp_path)
    monkeypatch.setattr(
        "holdspeak.deployment_revisions.capture_deployment_revision",
        lambda *_args, **_kwargs: pytest.fail("projection attempted a deployment upsert"),
    )
    app = FastAPI()

    @app.middleware("http")
    async def agent(request: Request, call_next):
        request.state.principal = AGENT
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {}, setup_service=SetupService(db), inference_setup_service=service,
    )))

    response = TestClient(app).get("/api/inference/setup")

    assert response.status_code == 403
    assert response.json()["error"] == "Owner access is required."


def test_owner_projection_never_saves_connects_or_loads_a_model(tmp_path: Path, monkeypatch):
    _db, service = _service(tmp_path)
    monkeypatch.setattr(Config, "save", lambda *_a, **_k: pytest.fail("Config write"))
    monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: pytest.fail("network"))
    monkeypatch.setattr("socket.create_connection", lambda *_a, **_k: pytest.fail("network"))
    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel.__init__",
        lambda *_a, **_k: pytest.fail("model/provider construction"),
    )
    monkeypatch.setattr(
        "holdspeak.kernel.inference_runner.InferenceRunner.invoke",
        lambda *_a, **_k: pytest.fail("inference admission"),
    )
    monkeypatch.setattr(
        "holdspeak.inference_targets.build_intel_for_revision",
        lambda *_a, **_k: pytest.fail("runtime factory"),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda *_a, **_k: pytest.fail("provider adapter"),
    )

    first = service.get_inference_setup(OWNER)
    first["presets"][0]["label"] = "caller mutation"
    second = service.get_inference_setup(OWNER)

    assert second["presets"][0]["label"] != "caller mutation"
