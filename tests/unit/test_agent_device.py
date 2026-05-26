from __future__ import annotations

from holdspeak.agent_context import AgentSession
from holdspeak.agent_device import (
    build_agent_identity_payload,
    build_agent_query_response,
    target_profile_override_for_agent,
)


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


def test_agent_next_query_returns_selected_status_text() -> None:
    response = build_agent_query_response("agent_next", _session(agent="claude"))

    assert response == {
        "text": "Claude waiting in HoldSpeak: The patch is ready. Should I run the focused tests?",
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


def test_target_profile_override_for_agent_session() -> None:
    assert target_profile_override_for_agent(_session(agent="codex")) == "codex_cli"
    assert target_profile_override_for_agent(_session(agent="claude")) == "claude_code"
    assert target_profile_override_for_agent(_session(agent="other")) is None
    assert target_profile_override_for_agent(None) is None


def test_agent_identity_payload_marks_tmux_target_high_confidence() -> None:
    payload = build_agent_identity_payload(
        _session(
            tmux_pane="%7",
            tmux_session="work",
            tmux_window="2",
            tmux_pane_index="1",
        ),
        text_injection_enabled=False,
    )

    assert payload is not None
    assert payload["compact_label"] == "Codex | HoldSpeak | work:2.1"
    assert payload["tmux_label"] == "work:2.1"
    assert payload["target_transport"] == "tmux"
    assert payload["target_confidence"] == "high"


def test_agent_identity_payload_degrades_visibly_without_tmux() -> None:
    payload = build_agent_identity_payload(
        _session(),
        text_injection_enabled=True,
    )

    assert payload is not None
    assert payload["compact_label"] == "Codex | HoldSpeak | no tmux"
    assert payload["tmux_label"] is None
    assert payload["target_transport"] == "text_injection"
    assert payload["target_confidence"] == "medium"


def test_agent_identity_payload_reports_low_confidence_when_reply_target_unknown() -> None:
    unavailable = build_agent_identity_payload(_session(), text_injection_enabled=False)
    unknown = build_agent_identity_payload(_session(), text_injection_enabled=None)

    assert unavailable is not None
    assert unavailable["compact_label"] == "Codex | HoldSpeak | no tmux"
    assert unavailable["target_transport"] == "unavailable"
    assert unavailable["target_confidence"] == "low"
    assert unknown is not None
    assert unknown["target_transport"] == "unknown"
    assert unknown["target_confidence"] == "low"
    assert build_agent_identity_payload(None) is None
