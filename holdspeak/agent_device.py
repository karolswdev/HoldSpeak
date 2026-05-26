"""Device-facing summaries of captured coding-agent state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_context import AgentSession
from .device_status import truncate_for_lcd

AGENT_STATUS_QUERY = "agent_status"
AGENT_QUESTION_QUERY = "agent_question"
AGENT_NEXT_QUERY = "agent_next"
AGENT_QUERY_NAMES = frozenset({AGENT_STATUS_QUERY, AGENT_QUESTION_QUERY, AGENT_NEXT_QUERY})
AGENT_QUERY_TTL_MS = 7000
NO_AGENT_QUERY_TTL_MS = 3000
IDENTITY_LABEL_MAX_CHARS = 48
IDENTITY_PART_MAX_CHARS = 18


def build_agent_query_response(
    name: str,
    session: AgentSession | None,
    *,
    max_text_chars: int = 500,
) -> dict[str, Any] | None:
    """Return a status-frame payload for a device-originated agent query."""

    query = str(name or "").strip()
    if query not in AGENT_QUERY_NAMES:
        return None
    if session is None or not session.awaiting_response or not session.last_assistant_text:
        return {"text": "No agent waiting", "ttl_ms": NO_AGENT_QUERY_TTL_MS}

    question = _compact(session.last_assistant_text)
    if query == AGENT_QUESTION_QUERY:
        text = question or "Agent waiting"
    else:
        label = _agent_label(session.agent)
        project = _project_label(session)
        prefix = f"{label} waiting"
        if project:
            prefix = f"{prefix} in {project}"
        text = f"{prefix}: {question}" if question else prefix
    return {
        "text": truncate_for_lcd(text, max_text_chars),
        "ttl_ms": AGENT_QUERY_TTL_MS,
    }


def target_profile_override_for_agent(session: AgentSession | None) -> str | None:
    """Return the dictation target override for a captured agent session."""

    if session is None:
        return None
    normalized = str(session.agent or "").strip().lower()
    if normalized == "codex":
        return "codex_cli"
    if normalized == "claude":
        return "claude_code"
    return None


def build_agent_identity_payload(
    session: AgentSession | None,
    *,
    text_injection_enabled: bool | None = None,
) -> dict[str, Any] | None:
    """Return display and routing confidence for an agent reply target."""

    if session is None:
        return None

    agent_label = _shorten_label(_agent_label(session.agent), IDENTITY_PART_MAX_CHARS)
    project_label = _shorten_label(_project_label(session), IDENTITY_PART_MAX_CHARS)
    tmux_label = _tmux_label(session)
    target_transport, target_confidence, confidence_reason = _target_confidence(
        session,
        text_injection_enabled=text_injection_enabled,
    )

    compact_parts = [agent_label]
    if project_label:
        compact_parts.append(project_label)
    compact_parts.append(tmux_label or "no tmux")
    compact_label = _shorten_label(" | ".join(compact_parts), IDENTITY_LABEL_MAX_CHARS)

    return {
        "agent_label": agent_label,
        "project_label": project_label or None,
        "tmux_label": tmux_label or None,
        "compact_label": compact_label,
        "target_transport": target_transport,
        "target_confidence": target_confidence,
        "confidence_reason": confidence_reason,
        "session_id": session.session_id,
        "cwd": session.cwd,
        "repo_root": session.repo_root,
    }


def _agent_label(agent: str) -> str:
    normalized = str(agent or "").strip().lower()
    if normalized == "codex":
        return "Codex"
    if normalized == "claude":
        return "Claude"
    return "Agent"


def _project_label(session: AgentSession) -> str:
    if session.project_name:
        return session.project_name
    if session.repo_root:
        return Path(session.repo_root).name
    if session.cwd:
        return Path(session.cwd).name
    return ""


def _compact(text: str) -> str:
    return " ".join(str(text or "").split())


def _tmux_label(session: AgentSession) -> str:
    tmux_session = _compact(session.tmux_session or "")
    tmux_window = _compact(session.tmux_window or "")
    tmux_pane_index = _compact(session.tmux_pane_index or "")
    if tmux_session and tmux_window and tmux_pane_index:
        return _shorten_label(
            f"{tmux_session}:{tmux_window}.{tmux_pane_index}",
            IDENTITY_PART_MAX_CHARS,
        )
    pane = _compact(session.tmux_pane or "")
    return _shorten_label(pane, IDENTITY_PART_MAX_CHARS) if pane else ""


def _target_confidence(
    session: AgentSession,
    *,
    text_injection_enabled: bool | None,
) -> tuple[str, str, str]:
    if _compact(session.tmux_pane or ""):
        return (
            "tmux",
            "high",
            "agent hook reported a tmux pane reply target",
        )
    if text_injection_enabled is True:
        return (
            "text_injection",
            "medium",
            "runtime can inject text but no tmux pane was reported",
        )
    if text_injection_enabled is False:
        return (
            "unavailable",
            "low",
            "no tmux pane was reported and text injection is unavailable",
        )
    return (
        "unknown",
        "low",
        "no tmux pane was reported and text injection status is unknown",
    )


def _shorten_label(text: str, max_chars: int) -> str:
    compacted = _compact(text)
    if len(compacted) <= max_chars:
        return compacted
    if max_chars <= 1:
        return compacted[:max_chars]
    return f"{compacted[: max_chars - 1]}>"
