"""HS-4-05: integration tests for `/api/dictation/dry-run`.

Covers the browser-facing dry-run endpoint for the DIR-01 pipeline:
project-KB enrichment on a matched block, no-project execution,
LLM-unavailable fallback, disabled-pipeline behavior, and validation
of bad utterance payloads.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak import web_server as web_server_module
from holdspeak.config import Config
from holdspeak.plugins.dictation import assembly as assembly_module
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError
from holdspeak.web_server import MeetingWebServer


class _StubRuntime:
    backend = "stub"

    def __init__(self, block_id: str | None = None) -> None:
        self.block_id = block_id

    def load(self) -> None:
        pass

    def info(self) -> dict:
        return {"backend": "stub"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        block_id = self.block_id or (schema.block_ids[0] if schema.block_ids else None)
        return {
            "matched": block_id is not None,
            "block_id": block_id,
            "confidence": 0.95 if block_id is not None else 0.0,
            "extras": {},
        }


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


def _save_config(path: Path, *, enabled: bool) -> None:
    cfg = Config()
    cfg.dictation.pipeline.enabled = enabled
    cfg.save(path=path)


def _write_blocks(path: Path, *, block_id: str = "task_note", template: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "default_match_confidence": 0.6,
                "blocks": [
                    {
                        "id": block_id,
                        "description": "task note",
                        "match": {
                            "examples": ["capture a task note"],
                            "negative_examples": [],
                            "threshold": 0.5,
                        },
                        "inject": {"mode": "append", "template": template},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _seed_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "proj"
    (root / ".holdspeak").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname = "proj"\n', encoding="utf-8")
    (root / ".holdspeak" / "project.yaml").write_text(
        yaml.safe_dump({"kb": {"stack": "python"}}, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.chdir(root)
    return root


def test_dry_run_matches_block_and_enriches_with_project_kb(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=True)
    root = _seed_project(tmp_path, monkeypatch)
    _write_blocks(
        root / ".holdspeak" / "blocks.yaml",
        template="\n\nStack: {project.kb.stack}",
    )
    monkeypatch.setattr(
        assembly_module,
        "build_runtime",
        lambda **_kwargs: _StubRuntime("task_note"),
    )

    response = test_client.post(
        "/api/dictation/dry-run",
        json={"utterance": "capture this implementation note"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["project"]["name"] == "proj"
    assert body["runtime_status"] == "loaded"
    assert body["blocks_count"] == 1
    assert body["stages"][0]["stage_id"] == "intent-router"
    assert body["stages"][0]["intent"]["matched"] is True
    assert body["stages"][0]["intent"]["block_id"] == "task_note"
    assert body["stages"][1]["stage_id"] == "kb-enricher"
    assert body["stages"][1]["metadata"]["applied_block"] == "task_note"
    assert body["final_text"].endswith("Stack: python")


def test_dry_run_project_root_override_selects_project_without_relaunch(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=True)
    root = tmp_path / "target"
    (root / ".holdspeak").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
    (root / ".holdspeak" / "project.yaml").write_text(
        yaml.safe_dump({"kb": {"stack": "rust"}}, sort_keys=False),
        encoding="utf-8",
    )
    _write_blocks(
        root / ".holdspeak" / "blocks.yaml",
        template="\n\nStack: {project.kb.stack}",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        assembly_module,
        "build_runtime",
        lambda **_kwargs: _StubRuntime("task_note"),
    )

    response = test_client.post(
        "/api/dictation/dry-run",
        json={"utterance": "capture this", "project_root": str(root)},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["project"]["name"] == "target-proj"
    assert body["final_text"].endswith("Stack: rust")


def test_dry_run_no_project_still_runs_pipeline(
    test_client: TestClient,
    settings_path: Path,
    global_blocks_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        assembly_module,
        "build_runtime",
        lambda **_kwargs: _StubRuntime(),
    )

    response = test_client.post("/api/dictation/dry-run", json={"utterance": "plain text"})

    assert response.status_code == 200
    body = response.json()
    assert body["project"] is None
    assert body["runtime_status"] == "loaded"
    assert body["blocks_count"] == 0
    assert [stage["stage_id"] for stage in body["stages"]] == ["intent-router", "kb-enricher"]
    assert body["final_text"] == "plain text"


def test_dry_run_llm_unavailable_surfaces_runtime_status(
    test_client: TestClient,
    settings_path: Path,
    global_blocks_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_config(settings_path, enabled=True)
    monkeypatch.chdir(tmp_path)
    _write_blocks(global_blocks_path, template="\n\nMatched: {raw_text}")

    def _broken_runtime(**_kwargs):
        raise RuntimeUnavailableError("no model configured")

    monkeypatch.setattr(assembly_module, "build_runtime", _broken_runtime)

    response = test_client.post("/api/dictation/dry-run", json={"utterance": "task note"})

    assert response.status_code == 200
    body = response.json()
    assert body["runtime_status"] == "unavailable"
    assert "no model configured" in body["runtime_detail"]
    assert body["stages"][0]["stage_id"] == "kb-enricher"
    assert body["final_text"] == "task note"


def test_dry_run_pipeline_disabled_returns_empty_trace(
    test_client: TestClient,
    settings_path: Path,
) -> None:
    _save_config(settings_path, enabled=False)

    response = test_client.post("/api/dictation/dry-run", json={"utterance": "keep me"})

    assert response.status_code == 200
    body = response.json()
    assert body["runtime_status"] == "disabled"
    assert body["stages"] == []
    assert body["final_text"] == "keep me"
    assert body["warnings"] == ["dictation pipeline disabled"]


@pytest.mark.parametrize("payload", [{}, {"utterance": ""}, {"utterance": "   "}, {"utterance": 42}])
def test_dry_run_rejects_bad_utterance_payloads(
    test_client: TestClient,
    settings_path: Path,
    payload: dict,
) -> None:
    _save_config(settings_path, enabled=True)

    response = test_client.post("/api/dictation/dry-run", json=payload)

    assert response.status_code == 400
    assert "utterance" in response.json()["detail"]


def test_dry_run_rejects_non_string_project_root(
    test_client: TestClient,
    settings_path: Path,
) -> None:
    _save_config(settings_path, enabled=True)

    response = test_client.post(
        "/api/dictation/dry-run",
        json={"utterance": "hello", "project_root": 123},
    )

    assert response.status_code == 400
    assert "project_root" in response.json()["detail"]


def test_dictation_page_includes_dry_run_section() -> None:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    body = response.text
    assert 'data-section="dry-run"' in body
    assert "/api/dictation/dry-run" in body
    assert "Copy final text" in body
    assert "project-root-override" in body
