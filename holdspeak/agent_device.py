"""Device-facing summaries of captured coding-agent state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_context import AgentSession
from .device_status import truncate_for_lcd

AGENT_STATUS_QUERY = "agent_status"
AGENT_QUESTION_QUERY = "agent_question"
AGENT_QUERY_NAMES = frozenset({AGENT_STATUS_QUERY, AGENT_QUESTION_QUERY})
AGENT_QUERY_TTL_MS = 7000
NO_AGENT_QUERY_TTL_MS = 3000


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
