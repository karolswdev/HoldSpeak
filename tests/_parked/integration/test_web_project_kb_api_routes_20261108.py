"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_project_kb_api.py``: TestProjectDocSuggestionAPI, test_get_returns_project_scoped_awaiting_agent_session, test_a_question_ten_minutes_old_still_waits_for_an_answer, test_clear_removes_captured_text, test_summarize_generates_and_persists_agent_summary. Not collected.
"""
from __future__ import annotations
"""HS-4-03: integration tests for `/api/dictation/project-kb` (WFS-CFG-003).

Covers GET / PUT / DELETE happy paths, validation rejection of bad
keys / values / payloads, atomic-write rollback against an existing
project.yaml, and the auto-detection / no-project-detected branches.
"""


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


def _seed_kb(root: Path, kb: dict) -> Path:
    path = root / ".holdspeak" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"kb": kb}, sort_keys=False), encoding="utf-8")
    return path


# ── GET ───────────────────────────────────────────────────────────────


# ── PUT ───────────────────────────────────────────────────────────────


# ── Starter ──────────────────────────────────────────────────────────


# ── DELETE ────────────────────────────────────────────────────────────


# ── Project .hs context ─────────────────────────────────────────────────


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

    def test_a_question_ten_minutes_old_still_waits_for_an_answer(
        self,
        test_client: TestClient,
        project_root_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Conductor R5: the dictation agent-context routes use the shared
        reply window (DEFAULT_RECENT_MAX_AGE_SECONDS, 30 min), not 120 s."""
        import json as _json
        from datetime import datetime, timedelta, timezone

        from holdspeak.agent_context.models import DEFAULT_RECENT_MAX_AGE_SECONDS

        state_path = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state_path)
        transcript = tmp_path / "codex.jsonl"
        transcript.write_text(
            '{"role":"assistant","content":"Should I rebase first?"}\n',
            encoding="utf-8",
        )
        ingest_agent_hook_event(
            agent="codex",
            payload={
                "session_id": "codex-old",
                "hook_event_name": "Stop",
                "cwd": str(project_root_dir),
                "transcript_path": str(transcript),
            },
            state_path=state_path,
            capture_messages=True,
        )
        ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

        def _age(node):
            if isinstance(node, dict):
                return {k: (ten_min_ago if k == "updated_at" else _age(v)) for k, v in node.items()}
            if isinstance(node, list):
                return [_age(v) for v in node]
            return node

        state_path.write_text(
            _json.dumps(_age(_json.loads(state_path.read_text(encoding="utf-8")))),
            encoding="utf-8",
        )

        body = test_client.get("/api/dictation/agent-context").json()
        assert body["max_age_seconds"] == DEFAULT_RECENT_MAX_AGE_SECONDS
        assert body["awaiting_response"] is True
        assert body["session"]["session_id"] == "codex-old"

        cleared = test_client.post(
            "/api/dictation/agent-context/clear",
            json={"agent": "codex", "session_id": "codex-old"},
        ).json()
        assert cleared["cleared"] is True

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


