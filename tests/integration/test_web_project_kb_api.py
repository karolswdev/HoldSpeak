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

from holdspeak import agent_context as agent_context_module
from holdspeak.agent_context import ingest_agent_hook_event
from holdspeak.agent_summarizer import AgentSummary
from holdspeak.plugins.dictation import project_root as project_root_module
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


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
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                     on_dictation_config_changed=cache_invalidator,
                 )
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


# ── Starter ──────────────────────────────────────────────────────────


class TestStarterProjectKB:
    def test_starter_creates_canonical_project_kb(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.post("/api/dictation/project-kb/starter")

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["starter"] is True
        assert body["kb"] == {"stack": None, "task_focus": None, "constraints": None}
        on_disk = yaml.safe_load((project_root_dir / ".holdspeak" / "project.yaml").read_text())
        assert on_disk == {"kb": {"stack": None, "task_focus": None, "constraints": None}}
        cache_invalidator.assert_called_once()

    def test_starter_honors_project_root_override(
        self, test_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname = "target-proj"\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        response = test_client.post(f"/api/dictation/project-kb/starter?project_root={target}")

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["detected"]["name"] == "target-proj"
        assert yaml.safe_load((target / ".holdspeak" / "project.yaml").read_text()) == {
            "kb": {"stack": None, "task_focus": None, "constraints": None}
        }

    def test_starter_refuses_to_overwrite_existing_file(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        path = _seed_kb(project_root_dir, {"stack": "python"})

        response = test_client.post("/api/dictation/project-kb/starter")

        assert response.status_code == 409
        assert yaml.safe_load(path.read_text()) == {"kb": {"stack": "python"}}
        cache_invalidator.assert_not_called()


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


# ── Project .hs context ─────────────────────────────────────────────────


class TestProjectHSContext:
    def test_get_returns_all_project_context_files(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        hs = project_root_dir / ".hs"
        hs.mkdir()
        (hs / "instructions.md").write_text("Rewrite as agent prompt.", encoding="utf-8")

        response = test_client.get("/api/dictation/project-hs")

        assert response.status_code == 200
        body = response.json()
        assert body["detected"]["name"] == "proj"
        assert body["context_dir"].endswith("/.hs")
        assert body["files"]["instructions.md"]["content"] == "Rewrite as agent prompt."
        assert "context.md" in body["files"]
        assert "targets.md" in body["files"]
        assert "ignore" in body["files"]

    def test_get_surfaces_flat_read_only_context_and_skip_warnings(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        (project_root_dir / ".hs_context").write_text("Flat repo context.", encoding="utf-8")
        (project_root_dir / ".hs_memory").write_bytes(b"abc\x00def")

        response = test_client.get("/api/dictation/project-hs")

        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is True
        assert body["context_dir_exists"] is False
        assert body["files"]["context.md"]["content"] == "Flat repo context."
        assert body["files"]["context.md"]["source"] == "flat"
        assert body["files"]["context.md"]["read_only"] is True
        assert body["files"]["context.md"]["exists"] is False
        assert body["flat_files"][".hs_context"]["canonical_name"] == "context.md"
        assert body["skipped"][0]["reason"] == "binary"
        assert "Skipped .hs_memory: binary" in body["warnings"]
        assert body["write_policy"]["automatic_writes"] is False

    def test_put_writes_selected_hs_files_and_invalidates_cache(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.put(
            "/api/dictation/project-hs",
            json={"files": {"instructions.md": "Use concise Codex tasks.", "ignore": ".env\n"}},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["exists"] is True
        assert body["files"]["instructions.md"]["content"] == "Use concise Codex tasks."
        assert (project_root_dir / ".hs" / "instructions.md").read_text() == "Use concise Codex tasks."
        assert (project_root_dir / ".hs" / "ignore").read_text() == ".env\n"
        cache_invalidator.assert_called_once()

    def test_put_creates_canonical_copy_without_modifying_flat_file(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        flat = project_root_dir / ".hs_context"
        flat.write_text("Flat context stays unchanged.", encoding="utf-8")

        response = test_client.put(
            "/api/dictation/project-hs",
            json={"files": {"context.md": "Canonical editable context."}},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert flat.read_text(encoding="utf-8") == "Flat context stays unchanged."
        assert (project_root_dir / ".hs" / "context.md").read_text() == "Canonical editable context."
        assert body["files"]["context.md"]["content"] == "Canonical editable context."
        assert body["files"]["context.md"]["source"] == "directory"
        assert body["files"]["context.md"]["read_only"] is False
        cache_invalidator.assert_called_once()

    def test_put_rejects_unknown_hs_file(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.put(
            "/api/dictation/project-hs",
            json={"files": {"secret.txt": "nope"}},
        )

        assert response.status_code == 400
        assert "unknown .hs file" in response.json()["error"]


class TestProjectDocSuggestionAPI:
    def test_apply_writes_validated_suggestion_path(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.post(
            "/api/dictation/project-doc-suggestion/apply",
            json={
                "suggestion": {
                    "target_path": ".hs/memory/retry-worker-handoff.md",
                    "rationale": "Preserves a narrow implementation note.",
                    "content": "The retry worker should expose its next scheduled run.",
                }
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["applied"] is True
        assert body["suggestion"]["target_path"] == ".hs/memory/retry-worker-handoff.md"
        assert (
            project_root_dir / ".hs" / "memory" / "retry-worker-handoff.md"
        ).read_text(encoding="utf-8") == "The retry worker should expose its next scheduled run."
        cache_invalidator.assert_called_once()

    def test_apply_rejects_unsafe_suggestion_path(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        response = test_client.post(
            "/api/dictation/project-doc-suggestion/apply",
            json={
                "suggestion": {
                    "target_path": "README.md",
                    "rationale": "Too broad.",
                    "content": "Do not write this.",
                }
            },
        )

        assert response.status_code == 400
        assert "target_path" in response.json()["error"]
        assert not (project_root_dir / "README.md").exists()
        cache_invalidator.assert_not_called()

    def test_apply_rejects_secret_like_suggestion(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.post(
            "/api/dictation/project-doc-suggestion/apply",
            json={
                "suggestion": {
                    "target_path": ".hs/memory/local-token.md",
                    "rationale": "Preserve token.",
                    "content": "access_token=abc12345678901234567890",
                }
            },
        )

        assert response.status_code == 400
        assert "secret" in response.json()["error"]
        assert not (project_root_dir / ".hs" / "memory" / "local-token.md").exists()


# ── Agent context banner API ──────────────────────────────────────────


class TestDictationAgentContext:
    def test_agent_hooks_returns_templates_and_recent_status(
        self,
        test_client: TestClient,
        project_root_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state_path = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state_path)
        ingest_agent_hook_event(
            agent="codex",
            payload={
                "session_id": "codex-1",
                "hook_event_name": "SessionStart",
                "cwd": str(project_root_dir),
            },
            state_path=state_path,
            capture_messages=True,
        )

        response = test_client.get("/api/dictation/agent-hooks?capture_messages=true")

        assert response.status_code == 200
        body = response.json()
        assert body["capture_messages"] is True
        assert body["registry_path"] == str(state_path)
        assert "--capture-messages" in body["agents"]["claude"]["template_json"]
        assert "--capture-messages" in body["agents"]["codex"]["template_json"]
        assert body["agents"]["codex"]["latest_session"]["session_id"] == "codex-1"
        assert body["summarizers"]["codex"]["command_display"] == "codex exec --sandbox read-only --ephemeral -"
        assert body["summarizers"]["claude"]["safe_default"] is True

    def test_get_returns_project_scoped_awaiting_agent_session(
        self,
        test_client: TestClient,
        project_root_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state_path = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state_path)
        transcript = tmp_path / "codex.jsonl"
        transcript.write_text(
            '{"role":"assistant","content":"Should I update the docs next?"}\n',
            encoding="utf-8",
        )
        ingest_agent_hook_event(
            agent="codex",
            payload={
                "session_id": "codex-1",
                "hook_event_name": "Stop",
                "cwd": str(project_root_dir),
                "transcript_path": str(transcript),
            },
            state_path=state_path,
            capture_messages=True,
        )

        response = test_client.get("/api/dictation/agent-context")

        assert response.status_code == 200
        body = response.json()
        assert body["awaiting_response"] is True
        assert body["session"]["agent"] == "codex"
        assert body["session"]["last_assistant_text"] == "Should I update the docs next?"

    def test_clear_removes_captured_text(
        self,
        test_client: TestClient,
        project_root_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state_path = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state_path)
        transcript = tmp_path / "claude.jsonl"
        transcript.write_text(
            '{"role":"assistant","content":"Proceed with the refactor?"}\n',
            encoding="utf-8",
        )
        ingest_agent_hook_event(
            agent="claude",
            payload={
                "session_id": "claude-1",
                "hook_event_name": "Stop",
                "cwd": str(project_root_dir),
                "transcript_path": str(transcript),
            },
            state_path=state_path,
            capture_messages=True,
        )

        clear_response = test_client.post(
            "/api/dictation/agent-context/clear",
            json={"agent": "claude", "session_id": "claude-1"},
        )
        get_response = test_client.get("/api/dictation/agent-context")

        assert clear_response.status_code == 200
        assert clear_response.json()["cleared"] is True
        assert clear_response.json()["session"]["awaiting_response"] is False
        assert get_response.status_code == 200
        assert get_response.json()["session"] is None

    def test_summarize_generates_and_persists_agent_summary(
        self,
        test_client: TestClient,
        project_root_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state_path = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state_path)
        transcript = tmp_path / "codex.jsonl"
        transcript.write_text(
            '{"role":"assistant","content":"Should I add the summarizer endpoint?"}\n',
            encoding="utf-8",
        )
        ingest_agent_hook_event(
            agent="codex",
            payload={
                "session_id": "codex-1",
                "hook_event_name": "Stop",
                "cwd": str(project_root_dir),
                "transcript_path": str(transcript),
            },
            state_path=state_path,
            capture_messages=True,
        )

        def fake_summarize(session, *, provider, timeout_seconds=20.0):
            assert session.session_id == "codex-1"
            assert provider == "codex"
            return AgentSummary(
                provider="codex",
                summary="Codex is asking whether to add the summarizer endpoint.",
                generated_at="2026-05-10T00:00:00Z",
                source_agent="codex",
                source_session_id="codex-1",
                command=("codex", "exec"),
                cwd=str(project_root_dir),
            )

        monkeypatch.setattr(
            "holdspeak.agent_summarizer.summarize_agent_session",
            fake_summarize,
        )

        response = test_client.post(
            "/api/dictation/agent-context/summarize",
            json={"provider": "codex"},
        )
        get_response = test_client.get("/api/dictation/agent-context")

        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["summary"] == "Codex is asking whether to add the summarizer endpoint."
        assert body["session"]["summary"]["provider"] == "codex"
        assert get_response.status_code == 200
        assert get_response.json()["session"]["summary"]["summary"] == body["summary"]["summary"]


# ── Round-trip ────────────────────────────────────────────────────────


def test_dictation_page_includes_project_kb_section() -> None:
    """The `/dictation` page must surface the KB editor (HS-4-03)."""
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 )
             )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    js = (Path(__file__).resolve().parents[2] / "web/src/pages/DictationPage.tsx").read_text()
    assert "Project grounding" in js
    assert "Knowledge base" in js and "Project instructions" in js
    assert "Agent hooks" in js
    assert "/api/dictation/project-kb" in js
    assert "/api/dictation/project-hs" in js
    assert "/api/dictation/agent-hooks" in js


def test_round_trip_put_then_get(test_client: TestClient, project_root_dir: Path) -> None:
    payload = {"kb": {"stack": "python", "task_focus": "HS-4-03", "owner": "karol"}}
    put_response = test_client.put("/api/dictation/project-kb", json=payload)
    assert put_response.status_code == 200
    get_response = test_client.get("/api/dictation/project-kb")
    assert get_response.status_code == 200
    assert get_response.json()["kb"] == payload["kb"]
