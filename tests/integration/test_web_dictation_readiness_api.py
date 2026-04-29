"""HS-5-02: integration tests for `/api/dictation/readiness`."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak import web_server as web_server_module
from holdspeak.config import Config
from holdspeak.plugins.dictation import runtime as runtime_module
from holdspeak.web_server import MeetingWebServer


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def global_blocks_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "global-blocks.yaml"
    monkeypatch.setattr(web_server_module, "_GLOBAL_BLOCKS_PATH", target)
    return target


@pytest.fixture
def test_client(settings_path: Path, global_blocks_path: Path) -> TestClient:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    return TestClient(server.app)


def _save_config(
    path: Path,
    *,
    enabled: bool,
    model_path: Path | None = None,
    backend: str = "llama_cpp",
) -> None:
    cfg = Config()
    cfg.dictation.pipeline.enabled = enabled
    cfg.dictation.runtime.backend = backend
    if model_path is not None:
        cfg.dictation.runtime.llama_cpp_model_path = str(model_path)
    cfg.save(path=path)


def _write_project(root: Path, *, with_kb: bool = True, with_blocks: bool = True) -> None:
    (root / ".holdspeak").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text('[project]\nname = "ready-proj"\n', encoding="utf-8")
    if with_kb:
        (root / ".holdspeak" / "project.yaml").write_text(
            yaml.safe_dump({"kb": {"stack": "python"}}, sort_keys=False),
            encoding="utf-8",
        )
    if with_blocks:
        (root / ".holdspeak" / "blocks.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "default_match_confidence": 0.6,
                    "blocks": [
                        {
                            "id": "task_note",
                            "description": "task note",
                            "match": {"examples": ["task note"], "negative_examples": []},
                            "inject": {"mode": "append", "template": "{raw_text}"},
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )


def test_readiness_ready_with_project_blocks_kb_and_model(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_text("stub", encoding="utf-8")
    _save_config(settings_path, enabled=True, model_path=model_path)
    root = tmp_path / "project"
    _write_project(root)
    monkeypatch.setattr(
        runtime_module,
        "resolve_backend",
        lambda requested: ("llama_cpp", "test backend"),
    )

    response = test_client.get(f"/api/dictation/readiness?project_root={root}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ready"] is True
    assert body["project"]["name"] == "ready-proj"
    assert body["blocks"]["resolved_scope"] == "project"
    assert body["blocks"]["resolved"]["count"] == 1
    assert body["project_kb"]["keys"] == ["stack"]
    assert body["runtime"]["status"] == "available"
    assert body["warnings"] == []


def test_readiness_disabled_no_project_reports_next_actions(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=False)
    monkeypatch.chdir(tmp_path)

    response = test_client.get("/api/dictation/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is False
    assert body["runtime"]["status"] == "disabled"
    codes = {warning["code"] for warning in body["warnings"]}
    assert {"pipeline_disabled", "no_project", "no_blocks"} <= codes
    pipeline = next(w for w in body["warnings"] if w["code"] == "pipeline_disabled")
    assert pipeline["runtime_action"] == "enable_pipeline"
    assert pipeline["section"] == "runtime"
    no_blocks = next(w for w in body["warnings"] if w["code"] == "no_blocks")
    assert no_blocks["template_id"] == "action_item"
    assert no_blocks["template_action"] == "create_dry_run"
    assert no_blocks["template_scope"] == "global"


def test_readiness_no_project_blocks_recommends_project_template_scope(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
) -> None:
    _save_config(settings_path, enabled=True)
    root = tmp_path / "project"
    _write_project(root, with_blocks=False)

    response = test_client.get(f"/api/dictation/readiness?project_root={root}")

    assert response.status_code == 200
    body = response.json()
    no_blocks = next(w for w in body["warnings"] if w["code"] == "no_blocks")
    assert no_blocks["template_id"] == "action_item"
    assert no_blocks["template_action"] == "create_dry_run"
    assert no_blocks["template_scope"] == "project"


def test_readiness_missing_model_is_actionable(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_model = tmp_path / "missing.gguf"
    _save_config(settings_path, enabled=True, model_path=missing_model)
    root = tmp_path / "project"
    _write_project(root)
    monkeypatch.setattr(
        runtime_module,
        "resolve_backend",
        lambda requested: ("llama_cpp", "test backend"),
    )

    response = test_client.get(f"/api/dictation/readiness?project_root={root}")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is False
    assert body["runtime"]["status"] == "missing_model"
    warning = next(w for w in body["warnings"] if w["code"] == "runtime_model_missing")
    guidance = warning["guidance"]
    assert guidance["kind"] == "missing_model"
    assert guidance["backend"] == "llama_cpp"
    assert guidance["model_path"] == str(missing_model)
    assert str(missing_model) in guidance["next_step"]
    assert "huggingface-cli download" in guidance["command_bundle"]
    assert any(str(missing_model.parent) in item["command"] for item in guidance["commands"])


def test_readiness_runtime_unavailable_includes_install_guidance(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=True, backend="llama_cpp")
    root = tmp_path / "project"
    _write_project(root)

    def _raise_unavailable(requested: str) -> tuple[str, str]:
        raise runtime_module.RuntimeUnavailableError("llama_cpp missing")

    monkeypatch.setattr(runtime_module, "resolve_backend", _raise_unavailable)

    response = test_client.get(f"/api/dictation/readiness?project_root={root}")

    assert response.status_code == 200
    body = response.json()
    warning = next(w for w in body["warnings"] if w["code"] == "runtime_unavailable")
    guidance = warning["guidance"]
    assert guidance["kind"] == "unavailable"
    assert guidance["backend"] == "llama_cpp"
    assert guidance["model_path"] is None
    assert guidance["links"][0]["target"] == "/docs/dictation-runtime#llama-cpp"
    assert any("dictation-llama" in item["command"] for item in guidance["commands"])


def test_readiness_missing_project_kb_recommends_starter_action(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
) -> None:
    _save_config(settings_path, enabled=True)
    root = tmp_path / "project"
    _write_project(root, with_kb=False, with_blocks=True)

    response = test_client.get(f"/api/dictation/readiness?project_root={root}")

    assert response.status_code == 200
    body = response.json()
    warning = next(w for w in body["warnings"] if w["code"] == "missing_project_kb")
    assert warning["kb_action"] == "create_starter"
    assert warning["section"] == "kb"


def test_readiness_rejects_bad_project_root(test_client: TestClient, settings_path: Path) -> None:
    _save_config(settings_path, enabled=True)

    response = test_client.get("/api/dictation/readiness?project_root=/not/a/real/path")

    assert response.status_code == 400
    assert "project_root" in response.json()["error"]


def test_dictation_page_includes_readiness_panel() -> None:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)

    response = client.get("/dictation")

    assert response.status_code == 200
    body = response.text
    # Markers staying in server-rendered markup.
    assert 'data-section="readiness"' in body
    # HS-10-09: heading now sentence-case.
    assert "Dictation readiness" in body
    assert "rt-guidance" in body

    # Endpoint + handler strings + JS-rendered data attributes live
    # in the bundled chunk after the rebuild.
    import re

    match = re.search(r'src="(/_built/_astro/hoisted\.[^"]+\.js)"', body)
    assert match, "expected hoisted dictation JS chunk reference"
    js = client.get(match.group(1)).text
    assert "/api/dictation/readiness" in js
    assert "data-ready-template-id" in js
    assert "data-ready-kb-starter" in js
    assert "data-ready-runtime-action" in js
    assert "renderRuntimeGuidance" in js
    assert "data-copy-command" in js
    assert "Copy all setup commands" in js


def test_dictation_runtime_docs_route_serves_setup_page() -> None:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)

    response = client.get("/docs/dictation-runtime")

    assert response.status_code == 200
    body = response.text
    assert "Dictation Runtime Setup" in body
    assert 'id="mlx"' in body
    assert 'id="llama-cpp"' in body
    assert "dictation-mlx" in body
    assert "dictation-llama" in body
    assert "Qwen2.5-3B-Instruct-Q4_K_M.gguf" in body
