"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_dry_run_api.py``: test_dry_run_stores_latest_project_doc_suggestion_and_dismisses. Not collected.
"""
from __future__ import annotations
"""HS-4-05: integration tests for `/api/dictation/dry-run`.

Covers the browser-facing dry-run endpoint for the DIR-01 pipeline:
project-KB enrichment on a matched block, no-project execution,
LLM-unavailable fallback, disabled-pipeline behavior, and validation
of bad utterance payloads.
"""


from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.plugins.dictation import assembly as assembly_module
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


class _StubRuntime:
    # Backend intentionally unobservable: the explicit runtime_factory seam tests
    # route behavior, not a competing concrete loader.
    backend = ""

    def __init__(self, block_id: str | None = None, rewrite_text: str | None = None) -> None:
        self.block_id = block_id
        self.rewrite_text = rewrite_text

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

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):
        _ = prompt, max_tokens, temperature
        return self.rewrite_text or "rewritten text"


class _SequenceRewriteRuntime(_StubRuntime):
    def __init__(self, rewrites: list[str]) -> None:
        super().__init__()
        self.rewrites = list(rewrites)

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):
        _ = prompt, max_tokens, temperature
        if len(self.rewrites) > 1:
            return self.rewrites.pop(0)
        return self.rewrites[0] if self.rewrites else "rewritten text"


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def global_blocks_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "global-blocks.yaml"
    monkeypatch.setattr(assembly_module, "DEFAULT_GLOBAL_BLOCKS_PATH", target)
    return target


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


def test_dry_run_stores_latest_project_doc_suggestion_and_dismisses(
    test_client: TestClient,
    settings_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.pipeline.stages = ["project-rewriter", "kb-enricher"]
    cfg.save(path=settings_path)
    root = tmp_path / "target"
    (root / ".hs").mkdir(parents=True)
    (root / ".hs" / "instructions.md").write_text("Rewrite as coding-agent tasks.", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        assembly_module,
        "build_runtime",
        lambda **_kwargs: _SequenceRewriteRuntime(
            [
                "Document the retry worker handoff.",
                '{"target_path": ".hs/handoffs/retry-worker-next-run.md", '
                '"rationale": "Keeps the implementation handoff narrow.", '
                '"content": "Retry worker handoffs should mention the next scheduled run."}',
            ]
        ),
    )

    response = test_client.post(
        "/api/dictation/dry-run",
        json={
            "utterance": "capture the retry worker handoff",
            "target": {"app_name": "WezTerm", "window_title": "codex - HoldSpeak"},
        },
    )

    assert response.status_code == 200, response.text
    suggestion = response.json()["stages"][0]["metadata"]["project_doc_suggestion"]
    assert suggestion["target_path"] == ".hs/handoffs/retry-worker-next-run.md"

    latest = test_client.get("/api/dictation/project-doc-suggestion")
    assert latest.status_code == 200, latest.text
    assert latest.json()["suggestion"] == suggestion

    dismissed = test_client.post("/api/dictation/project-doc-suggestion/dismiss")
    assert dismissed.status_code == 200, dismissed.text
    assert dismissed.json()["dismissed"] is True
    assert not (root / ".hs" / "handoffs" / "retry-worker-next-run.md").exists()

    cleared = test_client.get("/api/dictation/project-doc-suggestion")
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["suggestion"] is None


