from __future__ import annotations

from holdspeak.agent_context import AgentSession
from holdspeak.agent_device import build_agent_query_response


def _session(**overrides) -> AgentSession:
    data = {
        "agent": "codex",
        "session_id": "abc",
        "cwd": "/tmp/HoldSpeak",
        "updated_at": "2026-05-24T00:00:00Z",
        "hook_event_name": "Stop",
        "repo_root": "/tmp/HoldSpeak",
        "repo_anchor": "git",
        "project_name": "HoldSpeak",
        "last_assistant_text": "The patch is ready. Should I run the focused tests?",
        "awaiting_response": True,
    }
    data.update(overrides)
    return AgentSession(**data)


def test_agent_status_query_formats_waiting_session() -> None:
    response = build_agent_query_response("agent_status", _session())

    assert response == {
        "text": "Codex waiting in HoldSpeak: The patch is ready. Should I run the focused tests?",
        "ttl_ms": 7000,
    }


def test_agent_question_query_returns_question_only() -> None:
    response = build_agent_query_response("agent_question", _session(agent="claude"))

    assert response == {
        "text": "The patch is ready. Should I run the focused tests?",
        "ttl_ms": 7000,
    }


def test_agent_query_reports_no_waiting_agent_without_fresh_capture() -> None:
    response = build_agent_query_response("agent_status", None)

    assert response == {"text": "No agent waiting", "ttl_ms": 3000}


def test_agent_query_ignores_unknown_names() -> None:
    assert build_agent_query_response("last_segment", _session()) is None


def test_agent_query_truncates_long_lcd_text() -> None:
    response = build_agent_query_response(
        "agent_question",
        _session(last_assistant_text="x" * 40),
        max_text_chars=12,
    )

    assert response == {"text": "xxxxxxxxxxx…", "ttl_ms": 7000}
