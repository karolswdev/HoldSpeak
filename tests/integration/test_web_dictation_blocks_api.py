"""HS-4-02: integration tests for `/api/dictation/blocks` (WFS-CFG-001 + -002).

Covers CRUD on both `scope=global` and `scope=project`, validation
parity with `BlockConfigError`, atomic-write rollback semantics
(`WFS-CFG-006`), and project-detection 404 handling.
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
from holdspeak.plugins.dictation import project_root as project_root_module
from holdspeak.web_server import MeetingWebServer


class _StubRuntime:
    backend = "stub"

    def load(self) -> None:
        pass

    def info(self) -> dict:
        return {"backend": "stub"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        block_id = schema.block_ids[0] if schema.block_ids else None
        return {
            "matched": block_id is not None,
            "block_id": block_id,
            "confidence": 0.96 if block_id is not None else 0.0,
            "extras": {},
        }


def _block(block_id: str = "b1", template: str = "{raw_text}\n") -> dict:
    return {
        "id": block_id,
        "description": "test block",
        "match": {
            "examples": ["do the thing"],
            "negative_examples": [],
            "threshold": 0.7,
        },
        "inject": {"mode": "append", "template": template},
    }


def _seed_global(path: Path, *blocks: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {"version": 1, "default_match_confidence": 0.6, "blocks": list(blocks)},
            sort_keys=False,
        ),
        encoding="utf-8",
    )


@pytest.fixture
def global_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config" / "holdspeak" / "blocks.yaml"
    monkeypatch.setattr(web_server_module, "_GLOBAL_BLOCKS_PATH", target)
    return target


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def project_root_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "proj"
    (root / ".holdspeak").mkdir(parents=True)

    def fake_detect(start: Path | None = None) -> dict:
        return {"name": "proj", "root": str(root), "anchor": "holdspeak"}

    monkeypatch.setattr(project_root_module, "detect_project_for_cwd", fake_detect)
    return root


@pytest.fixture
def no_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_root_module, "detect_project_for_cwd", lambda start=None: None)


@pytest.fixture
def cache_invalidator() -> MagicMock:
    return MagicMock()


def test_dictation_page_route_serves_html() -> None:
    """`/dictation` returns the static editor page with the expected anchors."""
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "Dictation Blocks" in body
    assert "/api/dictation/blocks" in body  # JS fetches the API
    assert "/api/dictation/block-templates" in body
    assert "/api/dictation/project-context" in body
    assert "Starter templates" in body
    assert "Create + dry-run" in body
    assert "project-root-recent" in body


@pytest.fixture
def test_client(cache_invalidator: MagicMock) -> TestClient:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
        on_dictation_config_changed=cache_invalidator,
    )
    return TestClient(server.app)


# ── GET ───────────────────────────────────────────────────────────────


class TestProjectContext:
    def test_project_context_validates_manual_root(
        self, test_client: TestClient, tmp_path: Path
    ) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")

        response = test_client.get(f"/api/dictation/project-context?project_root={target}")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["project"]["name"] == "target-proj"
        assert body["project"]["root"] == str(target)
        assert body["paths"]["blocks"] == str(target / ".holdspeak" / "blocks.yaml")
        assert body["paths"]["project_kb"] == str(target / ".holdspeak" / "project.yaml")

    def test_project_context_rejects_missing_manual_root(
        self, test_client: TestClient
    ) -> None:
        response = test_client.get("/api/dictation/project-context?project_root=/not/a/real/path")

        assert response.status_code == 400
        assert "project_root" in response.json()["error"]

    def test_project_context_reports_no_cwd_project(
        self, test_client: TestClient, no_project: None
    ) -> None:
        response = test_client.get("/api/dictation/project-context")

        assert response.status_code == 404
        assert "no project" in response.json()["error"]


class TestGetBlocks:
    def test_global_missing_returns_empty_default(self, test_client: TestClient, global_path: Path) -> None:
        response = test_client.get("/api/dictation/blocks?scope=global")
        assert response.status_code == 200
        body = response.json()
        assert body["scope"] == "global"
        assert body["exists"] is False
        assert body["document"] == {"version": 1, "default_match_confidence": 0.6, "blocks": []}
        assert body["project"] is None

    def test_global_present_returns_document(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"))
        response = test_client.get("/api/dictation/blocks?scope=global")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is True
        assert [b["id"] for b in body["document"]["blocks"]] == ["alpha"]

    def test_project_returns_project_context(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.get("/api/dictation/blocks?scope=project")
        assert response.status_code == 200
        body = response.json()
        assert body["scope"] == "project"
        assert body["project"]["name"] == "proj"
        assert body["path"].endswith(".holdspeak/blocks.yaml")

    def test_project_root_override_selects_project_without_relaunch(
        self, test_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "target"
        (target / ".holdspeak").mkdir(parents=True)
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        response = test_client.get(
            f"/api/dictation/blocks?scope=project&project_root={target}"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["project"]["name"] == "target-proj"
        assert body["path"] == str(target / ".holdspeak" / "blocks.yaml")

    def test_project_404_when_no_project_detected(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.get("/api/dictation/blocks?scope=project")
        assert response.status_code == 404
        assert "no project" in response.json()["error"]

    def test_invalid_scope_400(self, test_client: TestClient) -> None:
        response = test_client.get("/api/dictation/blocks?scope=bogus")
        assert response.status_code == 400

    def test_malformed_existing_file_422(self, test_client: TestClient, global_path: Path) -> None:
        global_path.parent.mkdir(parents=True, exist_ok=True)
        global_path.write_text("blocks: [not-a-mapping]\nversion: 1\n", encoding="utf-8")
        response = test_client.get("/api/dictation/blocks?scope=global")
        assert response.status_code == 422


# ── POST ──────────────────────────────────────────────────────────────


class TestCreateBlock:
    def test_create_in_empty_global(
        self, test_client: TestClient, global_path: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.post(
            "/api/dictation/blocks?scope=global", json={"block": _block("alpha")}
        )
        assert response.status_code == 201
        on_disk = yaml.safe_load(global_path.read_text())
        assert [b["id"] for b in on_disk["blocks"]] == ["alpha"]
        cache_invalidator.assert_called_once()

    def test_create_appends(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"))
        response = test_client.post(
            "/api/dictation/blocks?scope=global", json={"block": _block("beta")}
        )
        assert response.status_code == 201
        on_disk = yaml.safe_load(global_path.read_text())
        assert [b["id"] for b in on_disk["blocks"]] == ["alpha", "beta"]

    def test_create_duplicate_id_409(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"))
        response = test_client.post(
            "/api/dictation/blocks?scope=global", json={"block": _block("alpha")}
        )
        assert response.status_code == 409

    def test_create_invalid_block_422_and_atomic_rollback(
        self, test_client: TestClient, global_path: Path, cache_invalidator: MagicMock
    ) -> None:
        _seed_global(global_path, _block("alpha"))
        before = global_path.read_text()
        bad = _block("beta")
        bad["match"]["examples"] = []  # rejected by `_build_match`
        response = test_client.post(
            "/api/dictation/blocks?scope=global", json={"block": bad}
        )
        assert response.status_code == 422
        assert global_path.read_text() == before, "bad write must not modify the existing file"
        cache_invalidator.assert_not_called()

    def test_create_invalid_template_422(self, test_client: TestClient, global_path: Path) -> None:
        bad = _block("alpha", template="hello {bad-name!r}")
        response = test_client.post(
            "/api/dictation/blocks?scope=global", json={"block": bad}
        )
        assert response.status_code == 422

    def test_create_in_project_scope(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.post(
            "/api/dictation/blocks?scope=project", json={"block": _block("p1")}
        )
        assert response.status_code == 201
        target = project_root_dir / ".holdspeak" / "blocks.yaml"
        assert target.exists()
        assert yaml.safe_load(target.read_text())["blocks"][0]["id"] == "p1"

    def test_create_missing_block_key_400(self, test_client: TestClient, global_path: Path) -> None:
        response = test_client.post("/api/dictation/blocks?scope=global", json={})
        assert response.status_code == 400

    def test_project_scope_no_project_404(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.post(
            "/api/dictation/blocks?scope=project", json={"block": _block()}
        )
        assert response.status_code == 404


# ── Starter templates ─────────────────────────────────────────────────


class TestStarterTemplates:
    def test_list_templates(self, test_client: TestClient) -> None:
        response = test_client.get("/api/dictation/block-templates")
        assert response.status_code == 200
        body = response.json()
        ids = {template["id"] for template in body["templates"]}
        assert {"ai_prompt_context", "action_item", "concise_note", "code_review_focus"} <= ids
        assert all("block" in template for template in body["templates"])
        assert all(template["sample_utterance"] for template in body["templates"])

    def test_create_from_template_global(
        self, test_client: TestClient, global_path: Path
    ) -> None:
        response = test_client.post(
            "/api/dictation/blocks/from-template?scope=global",
            json={"template_id": "action_item"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["block"]["id"] == "action_item"
        on_disk = yaml.safe_load(global_path.read_text())
        assert [block["id"] for block in on_disk["blocks"]] == ["action_item"]

    def test_create_from_template_uses_unique_id_when_duplicate(
        self, test_client: TestClient, global_path: Path
    ) -> None:
        _seed_global(global_path, _block("action_item"))
        response = test_client.post(
            "/api/dictation/blocks/from-template?scope=global",
            json={"template_id": "action_item"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["block"]["id"] == "action_item_2"
        on_disk = yaml.safe_load(global_path.read_text())
        assert [block["id"] for block in on_disk["blocks"]] == ["action_item", "action_item_2"]

    def test_create_from_template_project_root_override(
        self, test_client: TestClient, tmp_path: Path
    ) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
        response = test_client.post(
            f"/api/dictation/blocks/from-template?scope=project&project_root={target}",
            json={"template_id": "concise_note"},
        )
        assert response.status_code == 201, response.text
        target_file = target / ".holdspeak" / "blocks.yaml"
        assert yaml.safe_load(target_file.read_text())["blocks"][0]["id"] == "concise_note"

    def test_create_from_template_with_dry_run_global(
        self,
        test_client: TestClient,
        settings_path: Path,
        global_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cfg = Config()
        cfg.dictation.pipeline.enabled = True
        cfg.save(path=settings_path)
        monkeypatch.setattr(
            assembly_module,
            "build_runtime",
            lambda **_kwargs: _StubRuntime(),
        )

        response = test_client.post(
            "/api/dictation/blocks/from-template?scope=global",
            json={"template_id": "action_item", "dry_run": True},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["block"]["id"] == "action_item"
        assert body["dry_run"]["created_block_id"] == "action_item"
        assert body["dry_run"]["sample_utterance"] == body["template"]["sample_utterance"]
        assert body["dry_run"]["runtime_status"] == "loaded"
        assert body["dry_run"]["stages"][0]["intent"]["block_id"] == "action_item"
        assert body["dry_run"]["final_text"].startswith("Action item: follow up")

    def test_create_from_template_with_dry_run_project_root_override(
        self,
        test_client: TestClient,
        settings_path: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cfg = Config()
        cfg.dictation.pipeline.enabled = True
        cfg.save(path=settings_path)
        target = tmp_path / "target"
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            assembly_module,
            "build_runtime",
            lambda **_kwargs: _StubRuntime(),
        )

        response = test_client.post(
            f"/api/dictation/blocks/from-template?scope=project&project_root={target}",
            json={"template_id": "concise_note", "dry_run": True},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["project"]["name"] == "target-proj"
        assert body["dry_run"]["project"]["name"] == "target-proj"
        assert body["dry_run"]["created_block_id"] == "concise_note"
        assert body["dry_run"]["stages"][0]["intent"]["block_id"] == "concise_note"
        assert body["dry_run"]["final_text"].startswith("Note: the retry worker")

    def test_create_from_template_rejects_non_boolean_dry_run(
        self, test_client: TestClient
    ) -> None:
        response = test_client.post(
            "/api/dictation/blocks/from-template?scope=global",
            json={"template_id": "action_item", "dry_run": "yes"},
        )
        assert response.status_code == 400
        assert "dry_run" in response.json()["error"]

    def test_create_from_unknown_template_404(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/dictation/blocks/from-template?scope=global",
            json={"template_id": "missing"},
        )
        assert response.status_code == 404


# ── PUT ───────────────────────────────────────────────────────────────


class TestUpdateBlock:
    def test_update_replaces_in_place(
        self, test_client: TestClient, global_path: Path, cache_invalidator: MagicMock
    ) -> None:
        _seed_global(global_path, _block("alpha"), _block("beta"))
        replacement = _block("alpha", template="updated {raw_text}\n")
        response = test_client.put(
            "/api/dictation/blocks/alpha?scope=global", json={"block": replacement}
        )
        assert response.status_code == 200
        on_disk = yaml.safe_load(global_path.read_text())
        assert on_disk["blocks"][0]["inject"]["template"] == "updated {raw_text}\n"
        assert [b["id"] for b in on_disk["blocks"]] == ["alpha", "beta"]
        cache_invalidator.assert_called_once()

    def test_update_unknown_id_404(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"))
        response = test_client.put(
            "/api/dictation/blocks/missing?scope=global", json={"block": _block("missing")}
        )
        assert response.status_code == 404

    def test_update_missing_file_404(self, test_client: TestClient, global_path: Path) -> None:
        response = test_client.put(
            "/api/dictation/blocks/alpha?scope=global", json={"block": _block("alpha")}
        )
        assert response.status_code == 404

    def test_update_invalid_block_422_and_atomic_rollback(
        self, test_client: TestClient, global_path: Path
    ) -> None:
        _seed_global(global_path, _block("alpha"))
        before = global_path.read_text()
        bad = _block("alpha")
        bad["inject"]["mode"] = "blast"  # invalid InjectMode
        response = test_client.put(
            "/api/dictation/blocks/alpha?scope=global", json={"block": bad}
        )
        assert response.status_code == 422
        assert global_path.read_text() == before

    def test_update_rename_collision_409(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"), _block("beta"))
        renamed = _block("beta")  # rename alpha → beta, but beta exists
        response = test_client.put(
            "/api/dictation/blocks/alpha?scope=global", json={"block": renamed}
        )
        assert response.status_code == 409


# ── DELETE ────────────────────────────────────────────────────────────


class TestDeleteBlock:
    def test_delete_removes_block(
        self, test_client: TestClient, global_path: Path, cache_invalidator: MagicMock
    ) -> None:
        _seed_global(global_path, _block("alpha"), _block("beta"))
        response = test_client.delete("/api/dictation/blocks/alpha?scope=global")
        assert response.status_code == 200
        on_disk = yaml.safe_load(global_path.read_text())
        assert [b["id"] for b in on_disk["blocks"]] == ["beta"]
        cache_invalidator.assert_called_once()

    def test_delete_unknown_id_404(self, test_client: TestClient, global_path: Path) -> None:
        _seed_global(global_path, _block("alpha"))
        response = test_client.delete("/api/dictation/blocks/missing?scope=global")
        assert response.status_code == 404

    def test_delete_missing_file_404(self, test_client: TestClient, global_path: Path) -> None:
        response = test_client.delete("/api/dictation/blocks/alpha?scope=global")
        assert response.status_code == 404

    def test_delete_last_block_leaves_empty_list(
        self, test_client: TestClient, global_path: Path
    ) -> None:
        """Last-block delete is allowed; file remains a valid empty document.

        `resolve_blocks` already handles a `blocks: []` file by falling
        back to the empty default `LoadedBlocks`, so this is the simpler
        of the two defensible behaviors (vs. rejecting the DELETE).
        """
        _seed_global(global_path, _block("alpha"))
        response = test_client.delete("/api/dictation/blocks/alpha?scope=global")
        assert response.status_code == 200
        on_disk = yaml.safe_load(global_path.read_text())
        assert on_disk["blocks"] == []
