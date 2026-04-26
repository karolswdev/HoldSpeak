"""HS-4-03: integration tests for `/api/dictation/project-kb` (WFS-CFG-003).

Covers GET / PUT / DELETE happy paths, validation rejection of bad
keys / values / payloads, atomic-write rollback against an existing
project.yaml, and the auto-detection / no-project-detected branches.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from holdspeak.plugins.dictation import project_root as project_root_module
from holdspeak.web_server import MeetingWebServer


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


@pytest.fixture
def test_client(cache_invalidator: MagicMock) -> TestClient:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
        on_dictation_config_changed=cache_invalidator,
    )
    return TestClient(server.app)


def _seed_kb(root: Path, kb: dict) -> Path:
    path = root / ".holdspeak" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"kb": kb}, sort_keys=False), encoding="utf-8")
    return path


# ── GET ───────────────────────────────────────────────────────────────


class TestGetProjectKB:
    def test_no_project_returns_nulls(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.get("/api/dictation/project-kb")
        assert response.status_code == 200
        body = response.json()
        assert body["detected"] is None
        assert body["kb"] is None
        assert body["kb_path"] is None
        assert "no project root" in body["message"]

    def test_project_no_kb_file_returns_kb_null(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.get("/api/dictation/project-kb")
        assert response.status_code == 200
        body = response.json()
        assert body["detected"]["name"] == "proj"
        assert body["kb"] is None
        assert body["kb_path"].endswith(".holdspeak/project.yaml")

    def test_project_root_override_selects_project_without_relaunch(
        self, test_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        response = test_client.put(
            f"/api/dictation/project-kb?project_root={target}",
            json={"kb": {"stack": "python"}},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["detected"]["name"] == "target-proj"
        assert yaml.safe_load((target / ".holdspeak" / "project.yaml").read_text()) == {
            "kb": {"stack": "python"}
        }

    def test_project_with_kb_returns_dict(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        _seed_kb(project_root_dir, {"stack": "python", "task_focus": "DIR-01"})
        response = test_client.get("/api/dictation/project-kb")
        assert response.status_code == 200
        body = response.json()
        assert body["kb"] == {"stack": "python", "task_focus": "DIR-01"}

    def test_malformed_existing_file_422(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        path = project_root_dir / ".holdspeak" / "project.yaml"
        path.write_text("kb: [not a mapping]\n", encoding="utf-8")
        response = test_client.get("/api/dictation/project-kb")
        assert response.status_code == 422


# ── PUT ───────────────────────────────────────────────────────────────


class TestPutProjectKB:
    def test_put_creates_file(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.put(
            "/api/dictation/project-kb",
            json={"kb": {"stack": "python", "owner": "karol"}},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["kb"] == {"stack": "python", "owner": "karol"}
        on_disk = yaml.safe_load((project_root_dir / ".holdspeak" / "project.yaml").read_text())
        assert on_disk == {"kb": {"stack": "python", "owner": "karol"}}
        cache_invalidator.assert_called_once()

    def test_put_overwrites_existing_atomically(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        _seed_kb(project_root_dir, {"stack": "rust"})
        response = test_client.put(
            "/api/dictation/project-kb",
            json={"kb": {"stack": "python"}},
        )
        assert response.status_code == 200
        on_disk = yaml.safe_load((project_root_dir / ".holdspeak" / "project.yaml").read_text())
        assert on_disk == {"kb": {"stack": "python"}}

    def test_put_bad_key_422_and_atomic_rollback(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        path = _seed_kb(project_root_dir, {"stack": "python"})
        before = path.read_text()
        response = test_client.put(
            "/api/dictation/project-kb",
            json={"kb": {"with-dash": "no good"}},
        )
        assert response.status_code == 422
        assert path.read_text() == before, "bad write must not modify the existing file"
        cache_invalidator.assert_not_called()

    def test_put_bad_value_type_422(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.put(
            "/api/dictation/project-kb",
            json={"kb": {"stack": ["nested", "list"]}},
        )
        assert response.status_code == 422

    def test_put_null_value_allowed(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.put(
            "/api/dictation/project-kb",
            json={"kb": {"placeholder": None}},
        )
        assert response.status_code == 200
        on_disk = yaml.safe_load((project_root_dir / ".holdspeak" / "project.yaml").read_text())
        assert on_disk == {"kb": {"placeholder": None}}

    def test_put_missing_kb_key_400(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.put("/api/dictation/project-kb", json={})
        assert response.status_code == 400

    def test_put_no_project_404(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.put(
            "/api/dictation/project-kb", json={"kb": {"stack": "python"}}
        )
        assert response.status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────


class TestDeleteProjectKB:
    def test_delete_removes_file_preserves_dir(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        path = _seed_kb(project_root_dir, {"stack": "python"})
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 200
        assert not path.exists()
        assert (project_root_dir / ".holdspeak").is_dir(), (
            ".holdspeak/ must be preserved (it's also the anchor signal)"
        )
        cache_invalidator.assert_called_once()

    def test_delete_no_file_404(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 404

    def test_delete_no_project_404(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 404


# ── Round-trip ────────────────────────────────────────────────────────


def test_dictation_page_includes_project_kb_section() -> None:
    """The `/dictation` page must surface the KB editor (HS-4-03)."""
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    body = response.text
    assert "Project KB" in body
    assert "/api/dictation/project-kb" in body  # JS fetches the API


def test_round_trip_put_then_get(test_client: TestClient, project_root_dir: Path) -> None:
    payload = {"kb": {"stack": "python", "task_focus": "HS-4-03", "owner": "karol"}}
    put_response = test_client.put("/api/dictation/project-kb", json=payload)
    assert put_response.status_code == 200
    get_response = test_client.get("/api/dictation/project-kb")
    assert get_response.status_code == 200
    assert get_response.json()["kb"] == payload["kb"]
