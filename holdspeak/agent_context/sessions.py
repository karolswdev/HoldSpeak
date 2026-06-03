"""Agent-session registry + state IO + assistant-text extraction (HS-34-03)."""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional

import holdspeak.agent_context as _agent_context_pkg

from ._common import _format_timestamp, _optional_str, _parse_timestamp
from .hooks import detect_tmux_context
from .hs_context import _normalize_project_root, detect_repo_root
from .models import (
    AgentSession,
    DEFAULT_ASSISTANT_CAPTURE_MAX_CHARS,
    DEFAULT_PROMPT_CAPTURE_MAX_CHARS,
    DEFAULT_RECENT_MAX_AGE_SECONDS,
    DEFAULT_STALE_AGENT_SESSION_SECONDS,
    MAX_SESSIONS,
    STATE_VERSION,
    SUPPORTED_AGENTS,
)


def _default_state_file() -> Path:
    """Resolve the default state file via the package so tests that
    monkeypatch `holdspeak.agent_context.AGENT_CONTEXT_FILE` are honored."""
    return _agent_context_pkg.AGENT_CONTEXT_FILE


def ingest_agent_hook_event(
    *,
    agent: str,
    payload: Mapping[str, Any],
    state_path: Path | None = None,
    now: datetime | None = None,
    capture_messages: bool = False,
    env: Mapping[str, str] | None = None,
) -> AgentSession:
    """Record one Claude/Codex hook event and return the normalized session."""

    normalized_agent = agent.strip().lower()
    if normalized_agent not in SUPPORTED_AGENTS:
        raise ValueError(f"agent must be one of: {', '.join(sorted(SUPPORTED_AGENTS))}")

    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        raise ValueError("hook payload is missing session_id")

    cwd = _payload_cwd(payload)
    if not cwd:
        raise ValueError("hook payload is missing cwd")
    cwd_path = Path(cwd).expanduser()
    try:
        cwd_path = cwd_path.resolve()
    except OSError:
        cwd_path = cwd_path.absolute()

    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    hook_event_name = str(payload.get("hook_event_name") or "").strip() or "unknown"
    repo = detect_repo_root(cwd_path)
    state_file = state_path or _default_state_file()
    key = _session_key(normalized_agent, session_id)
    assistant_text: str | None = None
    if capture_messages and hook_event_name in {"Stop", "SubagentStop"}:
        assistant_text = extract_last_assistant_text(
            normalized_agent,
            Path(str(payload.get("transcript_path") or "")).expanduser(),
        )
    tmux_context = detect_tmux_context(payload, env=env)

    with _state_lock(state_file):
        state = _read_state(state_file)
        sessions = state.setdefault("sessions", {})
        previous_raw = sessions.get(key) if isinstance(sessions, dict) else None
        previous = previous_raw if isinstance(previous_raw, dict) else {}
        event_count = int(previous.get("event_count") or 0) + 1
        previous_capture = bool(previous.get("capture_messages"))
        effective_capture_messages = capture_messages or previous_capture
        is_user_prompt = hook_event_name in {"UserPromptSubmit", "UserPromptExpansion"}
        last_assistant_text = _optional_str(previous.get("last_assistant_text"))
        last_assistant_text_at = _optional_str(previous.get("last_assistant_text_at"))
        summary = dict(previous["summary"]) if isinstance(previous.get("summary"), dict) else None
        awaiting_response = bool(previous.get("awaiting_response"))
        if is_user_prompt:
            last_assistant_text = None
            last_assistant_text_at = None
            summary = None
            awaiting_response = False
        elif assistant_text:
            last_assistant_text = assistant_text
            last_assistant_text_at = timestamp
            summary = None
            awaiting_response = looks_like_agent_question(assistant_text)

        session = AgentSession(
            agent=normalized_agent,
            session_id=session_id,
            cwd=str(cwd_path),
            updated_at=timestamp,
            hook_event_name=hook_event_name,
            repo_root=str(repo.root) if repo else None,
            repo_anchor=repo.anchor if repo else None,
            project_name=repo.project_name if repo else None,
            transcript_path=_optional_str(payload.get("transcript_path")) or _optional_str(previous.get("transcript_path")),
            model=_optional_str(payload.get("model")) or _optional_str(previous.get("model")),
            last_prompt=_bounded_optional_str(payload.get("prompt"), DEFAULT_PROMPT_CAPTURE_MAX_CHARS) or _optional_str(previous.get("last_prompt")),
            last_tool_name=_optional_str(payload.get("tool_name")) or _optional_str(previous.get("last_tool_name")),
            last_assistant_text=last_assistant_text,
            last_assistant_text_at=last_assistant_text_at,
            summary=summary,
            tmux_pane=tmux_context.get("tmux_pane") or _optional_str(previous.get("tmux_pane")),
            tmux_session=tmux_context.get("tmux_session") or _optional_str(previous.get("tmux_session")),
            tmux_window=tmux_context.get("tmux_window") or _optional_str(previous.get("tmux_window")),
            tmux_pane_index=tmux_context.get("tmux_pane_index") or _optional_str(previous.get("tmux_pane_index")),
            tmux_pane_current_path=tmux_context.get("tmux_pane_current_path") or _optional_str(previous.get("tmux_pane_current_path")),
            awaiting_response=awaiting_response,
            capture_messages=effective_capture_messages,
            created_at=_optional_str(previous.get("created_at")) or timestamp,
            event_count=event_count,
            pinned=bool(previous.get("pinned")),
        )
        sessions[key] = session.to_dict()
        state["version"] = STATE_VERSION
        _prune_sessions(state, max_sessions=MAX_SESSIONS)
        _write_state(state_file, state)

    return session


def get_recent_agent_session(
    *,
    agent: str | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
) -> AgentSession | None:
    """Return the most recently updated session, optionally by agent."""

    sessions = list_agent_sessions(state_path=state_path, agent=agent)
    if not sessions:
        return None
    recent = max(sessions, key=lambda item: _parse_timestamp(item.updated_at) or datetime.min.replace(tzinfo=timezone.utc))
    updated = _parse_timestamp(recent.updated_at)
    if updated is None:
        return None
    age = (datetime.now(timezone.utc) - updated).total_seconds()
    if age > max_age_seconds:
        return None
    return recent


def get_recent_awaiting_agent_session(
    *,
    project_root: str | Path | None = None,
    agent: str | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
) -> AgentSession | None:
    """Return the newest captured agent question awaiting a user response."""

    selected = get_selected_awaiting_agent_session(
        project_root=project_root,
        agent=agent,
        state_path=state_path,
        max_age_seconds=max_age_seconds,
    )
    if selected is not None:
        return selected
    candidates = list_recent_awaiting_agent_sessions(
        project_root=project_root,
        agent=agent,
        state_path=state_path,
        max_age_seconds=max_age_seconds,
        limit=1,
    )
    return candidates[0] if candidates else None


def get_selected_awaiting_agent_session(
    *,
    project_root: str | Path | None = None,
    agent: str | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
) -> AgentSession | None:
    """Return the user-selected awaiting session if it is still valid."""

    state = _read_state(state_path or _default_state_file())
    selected_key = _selected_response_key(state)
    if selected_key is None:
        return None
    for session in list_recent_awaiting_agent_sessions(
        project_root=project_root,
        agent=agent,
        state_path=state_path,
        max_age_seconds=max_age_seconds,
    ):
        if _session_key(session.agent, session.session_id) == selected_key:
            return session
    return None


def select_next_awaiting_agent_session(
    *,
    project_root: str | Path | None = None,
    agent: str | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
    now: datetime | None = None,
) -> AgentSession | None:
    """Advance the selected awaiting session and return the new target."""

    state_file = state_path or _default_state_file()
    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    with _state_lock(state_file):
        state = _read_state(state_file)
        sessions = _recent_awaiting_sessions_from_state(
            state,
            project_root=project_root,
            agent=agent,
            max_age_seconds=max_age_seconds,
            now=now or datetime.now(timezone.utc),
        )
        if not sessions:
            state.pop("selected_agent_response", None)
            state["version"] = STATE_VERSION
            _write_state(state_file, state)
            return None

        selected_key = _selected_response_key(state)
        selected_index = 0
        if selected_key is not None:
            for index, session in enumerate(sessions):
                if _session_key(session.agent, session.session_id) == selected_key:
                    selected_index = index
                    # A pinned selection is sticky: refuse to auto-cycle away
                    # from it. The user must unpin (or select another) to move.
                    if session.pinned:
                        return session
                    break
        next_index = (selected_index + 1) % len(sessions)
        selected = sessions[next_index]
        state["selected_agent_response"] = {
            "agent": selected.agent,
            "session_id": selected.session_id,
            "selected_at": timestamp,
        }
        state["version"] = STATE_VERSION
        _write_state(state_file, state)
        return selected


def list_recent_awaiting_agent_sessions(
    *,
    project_root: str | Path | None = None,
    agent: str | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
    limit: int | None = None,
) -> list[AgentSession]:
    """Return recent captured agent questions awaiting user responses."""

    return _recent_awaiting_sessions_from_state(
        _read_state(state_path or _default_state_file()),
        project_root=project_root,
        agent=agent,
        max_age_seconds=max_age_seconds,
        limit=limit,
        now=datetime.now(timezone.utc),
    )


def _recent_awaiting_sessions_from_state(
    state: Mapping[str, Any],
    *,
    project_root: str | Path | None,
    agent: str | None,
    max_age_seconds: int,
    limit: int | None = None,
    now: datetime,
) -> list[AgentSession]:
    normalized_project_root = _normalize_project_root(project_root)
    normalized_agent = agent.strip().lower() if isinstance(agent, str) and agent.strip() else None
    raw_sessions = state.get("sessions")
    if not isinstance(raw_sessions, dict):
        return []
    candidates: list[AgentSession] = []
    for raw in raw_sessions.values():
        if not isinstance(raw, dict):
            continue
        session = AgentSession.from_mapping(raw)
        if normalized_agent and session.agent != normalized_agent:
            continue
        if not session.awaiting_response or not session.last_assistant_text:
            continue
        if normalized_project_root and session.repo_root != normalized_project_root:
            continue
        updated = _parse_timestamp(session.updated_at)
        # Pinned sessions stay visible regardless of age — pin is the user's
        # explicit "keep this as the target" signal (exempt from stale aging).
        if not session.pinned and (updated is None or (now - updated).total_seconds() > max_age_seconds):
            continue
        candidates.append(session)
    candidates = sorted(
        candidates,
        key=lambda item: _parse_timestamp(item.updated_at)
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    if limit is not None:
        candidates = candidates[: max(0, limit)]
    return candidates


def clear_agent_session_response(
    *,
    agent: str | None = None,
    session_id: str | None = None,
    project_root: str | Path | None = None,
    state_path: Path | None = None,
    max_age_seconds: int = DEFAULT_RECENT_MAX_AGE_SECONDS,
    now: datetime | None = None,
) -> AgentSession | None:
    """Clear captured assistant text for a specific or recent awaiting session."""

    state_file = state_path or _default_state_file()
    normalized_agent = agent.strip().lower() if isinstance(agent, str) and agent.strip() else None
    normalized_session_id = session_id.strip() if isinstance(session_id, str) and session_id.strip() else None
    normalized_project_root = _normalize_project_root(project_root)
    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    cutoff_now = now or datetime.now(timezone.utc)

    with _state_lock(state_file):
        state = _read_state(state_file)
        raw_sessions = state.get("sessions")
        if not isinstance(raw_sessions, dict):
            return None

        selected_key: str | None = None
        selected_session: AgentSession | None = None
        if normalized_agent and normalized_session_id:
            key = _session_key(normalized_agent, normalized_session_id)
            raw = raw_sessions.get(key)
            if isinstance(raw, dict):
                selected_key = key
                selected_session = AgentSession.from_mapping(raw)
        else:
            candidates: list[tuple[str, AgentSession]] = []
            for key, raw in raw_sessions.items():
                if not isinstance(key, str) or not isinstance(raw, dict):
                    continue
                session = AgentSession.from_mapping(raw)
                if normalized_agent and session.agent != normalized_agent:
                    continue
                if normalized_session_id and session.session_id != normalized_session_id:
                    continue
                if normalized_project_root and session.repo_root != normalized_project_root:
                    continue
                if not session.awaiting_response and not session.last_assistant_text:
                    continue
                updated = _parse_timestamp(session.updated_at)
                if updated is None or (cutoff_now - updated).total_seconds() > max_age_seconds:
                    continue
                candidates.append((key, session))
            if candidates:
                selected_key, selected_session = max(
                    candidates,
                    key=lambda item: _parse_timestamp(item[1].updated_at) or datetime.min.replace(tzinfo=timezone.utc),
                )

        if selected_key is None or selected_session is None:
            return None

        cleared = replace(
            selected_session,
            updated_at=timestamp,
            hook_event_name="ManualClear",
            last_assistant_text=None,
            last_assistant_text_at=None,
            summary=None,
            awaiting_response=False,
        )
        raw_sessions[selected_key] = cleared.to_dict()
        state["version"] = STATE_VERSION
        _write_state(state_file, state)
        return cleared


def select_awaiting_agent_session(
    agent: str,
    session_id: str,
    *,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> AgentSession | None:
    """Set the selected reply target to a specific session.

    Unlike `select_next_awaiting_agent_session` (which cycles), this pins the
    selected-response key to one named session so the web companion can choose
    a target directly. Returns the selected session, or None if it is unknown.
    """

    normalized_agent = agent.strip().lower() if isinstance(agent, str) else ""
    normalized_session_id = session_id.strip() if isinstance(session_id, str) else ""
    if not normalized_agent or not normalized_session_id:
        raise ValueError("agent and session_id are required")

    state_file = state_path or _default_state_file()
    key = _session_key(normalized_agent, normalized_session_id)
    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    with _state_lock(state_file):
        state = _read_state(state_file)
        raw_sessions = state.get("sessions")
        if not isinstance(raw_sessions, dict):
            return None
        raw = raw_sessions.get(key)
        if not isinstance(raw, dict):
            return None
        state["selected_agent_response"] = {
            "agent": normalized_agent,
            "session_id": normalized_session_id,
            "selected_at": timestamp,
        }
        state["version"] = STATE_VERSION
        _write_state(state_file, state)
        return AgentSession.from_mapping(raw)


def pin_agent_session(
    agent: str,
    session_id: str,
    pinned: bool = True,
    *,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> AgentSession | None:
    """Pin (or unpin) a session as the sticky reply target.

    A pinned session stays selected, is exempt from stale pruning + the recency
    cutoff, and `select_next_awaiting_agent_session` refuses to cycle away from
    it. Pinning also selects the session. Returns the updated session, or None
    if it is unknown.
    """

    normalized_agent = agent.strip().lower() if isinstance(agent, str) else ""
    normalized_session_id = session_id.strip() if isinstance(session_id, str) else ""
    if not normalized_agent or not normalized_session_id:
        raise ValueError("agent and session_id are required")

    state_file = state_path or _default_state_file()
    key = _session_key(normalized_agent, normalized_session_id)
    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    with _state_lock(state_file):
        state = _read_state(state_file)
        raw_sessions = state.get("sessions")
        if not isinstance(raw_sessions, dict):
            return None
        raw = raw_sessions.get(key)
        if not isinstance(raw, dict):
            return None
        # Keep updated_at honest (do not refresh age on pin) so the badge still
        # reflects when the agent actually last spoke.
        updated = replace(AgentSession.from_mapping(raw), pinned=bool(pinned))
        raw_sessions[key] = updated.to_dict()
        if pinned:
            state["selected_agent_response"] = {
                "agent": normalized_agent,
                "session_id": normalized_session_id,
                "selected_at": timestamp,
            }
        state["version"] = STATE_VERSION
        _write_state(state_file, state)
        return updated


def clear_stale_agent_sessions(
    *,
    max_age_seconds: int = DEFAULT_STALE_AGENT_SESSION_SECONDS,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> int:
    """Clear captured responses for non-pinned awaiting sessions older than the
    threshold. Returns the number of sessions cleared.

    Non-destructive (mirrors `clear_agent_session_response`): the session record
    survives but its captured question/response and `awaiting_response` flag are
    cleared, so it drops out of the waiting list. Pinned sessions are skipped.
    """

    state_file = state_path or _default_state_file()
    cutoff_now = now or datetime.now(timezone.utc)
    timestamp = _format_timestamp(cutoff_now)
    cleared = 0
    with _state_lock(state_file):
        state = _read_state(state_file)
        raw_sessions = state.get("sessions")
        if not isinstance(raw_sessions, dict):
            return 0
        for key, raw in list(raw_sessions.items()):
            if not isinstance(key, str) or not isinstance(raw, dict):
                continue
            session = AgentSession.from_mapping(raw)
            if session.pinned:
                continue
            if not session.awaiting_response and not session.last_assistant_text:
                continue
            updated = _parse_timestamp(session.updated_at)
            if updated is not None and (cutoff_now - updated).total_seconds() <= max_age_seconds:
                continue
            raw_sessions[key] = replace(
                session,
                updated_at=timestamp,
                hook_event_name="ManualClear",
                last_assistant_text=None,
                last_assistant_text_at=None,
                summary=None,
                awaiting_response=False,
            ).to_dict()
            cleared += 1
        if cleared:
            state["version"] = STATE_VERSION
            _write_state(state_file, state)
    return cleared


def set_agent_session_summary(
    *,
    agent: str,
    session_id: str,
    summary: Mapping[str, Any],
    state_path: Path | None = None,
    now: datetime | None = None,
) -> AgentSession | None:
    """Persist a derived external-agent summary on an existing session."""

    normalized_agent = agent.strip().lower() if isinstance(agent, str) else ""
    normalized_session_id = session_id.strip() if isinstance(session_id, str) else ""
    if not normalized_agent or not normalized_session_id:
        raise ValueError("agent and session_id are required")
    if normalized_agent not in SUPPORTED_AGENTS:
        raise ValueError(f"agent must be one of: {', '.join(sorted(SUPPORTED_AGENTS))}")

    state_file = state_path or _default_state_file()
    key = _session_key(normalized_agent, normalized_session_id)
    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    with _state_lock(state_file):
        state = _read_state(state_file)
        raw_sessions = state.get("sessions")
        if not isinstance(raw_sessions, dict):
            return None
        raw = raw_sessions.get(key)
        if not isinstance(raw, dict):
            return None
        session = AgentSession.from_mapping(raw)
        updated = replace(
            session,
            updated_at=timestamp,
            hook_event_name="SummaryGenerated",
            summary=dict(summary),
        )
        raw_sessions[key] = updated.to_dict()
        state["version"] = STATE_VERSION
        _write_state(state_file, state)
        return updated


def list_agent_sessions(
    *,
    state_path: Path | None = None,
    agent: str | None = None,
) -> list[AgentSession]:
    state = _read_state(state_path or _default_state_file())
    raw_sessions = state.get("sessions")
    if not isinstance(raw_sessions, dict):
        return []
    normalized_agent = agent.strip().lower() if isinstance(agent, str) and agent.strip() else None
    sessions = [
        AgentSession.from_mapping(raw)
        for raw in raw_sessions.values()
        if isinstance(raw, dict)
    ]
    if normalized_agent:
        sessions = [session for session in sessions if session.agent == normalized_agent]
    return sorted(sessions, key=lambda item: item.updated_at, reverse=True)


def extract_last_assistant_text(
    agent: str,
    transcript_path: Path,
    *,
    max_chars: int = DEFAULT_ASSISTANT_CAPTURE_MAX_CHARS,
) -> str | None:
    """Extract the latest assistant text from a Claude/Codex JSONL transcript."""

    if not transcript_path.is_file():
        return None
    latest: str | None = None
    try:
        lines = transcript_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or not _is_assistant_record(obj):
            continue
        text = _extract_text_from_record(obj)
        if text:
            latest = text
    if latest is None:
        return None
    latest = " ".join(latest.split())
    if len(latest) > max_chars:
        latest = latest[-max_chars:]
    return latest


def looks_like_agent_question(text: str) -> bool:
    tail = text.strip().rstrip("`'\"*_~ ").lower()
    if not tail:
        return False
    if tail.endswith("?"):
        return True
    cues = (
        "should i",
        "shall i",
        "do you want",
        "would you like",
        "want me to",
        "let me know",
        "confirm",
        "is that ok",
        "proceed",
        "go ahead",
    )
    return any(cue in tail[-400:] for cue in cues)


def _is_assistant_record(obj: Mapping[str, Any]) -> bool:
    role = str(obj.get("role") or "").lower()
    if role == "assistant":
        return True
    record_type = str(obj.get("type") or "").lower()
    if record_type == "assistant":
        return True
    payload = obj.get("payload")
    if isinstance(payload, Mapping):
        if _is_assistant_record(payload):
            return True
        if record_type == "event_msg" and str(payload.get("type") or "").lower() == "agent_message":
            return True
    message = obj.get("message")
    if isinstance(message, Mapping):
        return str(message.get("role") or "").lower() == "assistant"
    return False


def _extract_text_from_record(obj: Mapping[str, Any]) -> str:
    candidates: list[Any] = []
    if "content" in obj:
        candidates.append(obj.get("content"))
    if "text" in obj:
        candidates.append(obj.get("text"))
    if "output_text" in obj:
        candidates.append(obj.get("output_text"))
    payload = obj.get("payload")
    if isinstance(payload, Mapping):
        candidates.extend(
            [
                payload.get("content"),
                payload.get("text"),
                payload.get("output_text"),
                payload.get("message"),
            ]
        )
    message = obj.get("message")
    if isinstance(message, Mapping):
        candidates.extend([message.get("content"), message.get("text"), message.get("output_text")])
    parts: list[str] = []
    for candidate in candidates:
        parts.extend(_extract_text_parts(candidate))
    return "\n".join(part for part in parts if part.strip()).strip()


def _extract_text_parts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        if isinstance(value.get("text"), str):
            return [value["text"]]
        if isinstance(value.get("content"), str):
            return [value["content"]]
        return []
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(_extract_text_parts(item))
        return parts
    return []


def _payload_cwd(payload: Mapping[str, Any]) -> str:
    if str(payload.get("hook_event_name") or "") == "CwdChanged":
        new_cwd = payload.get("new_cwd")
        if isinstance(new_cwd, str) and new_cwd.strip():
            return new_cwd
    cwd = payload.get("cwd")
    return cwd if isinstance(cwd, str) else ""


def _session_key(agent: str, session_id: str) -> str:
    return f"{agent}:{session_id}"


def _selected_response_key(state: Mapping[str, Any]) -> str | None:
    selected = state.get("selected_agent_response")
    if not isinstance(selected, Mapping):
        return None
    agent = _optional_str(selected.get("agent"))
    session_id = _optional_str(selected.get("session_id"))
    if not agent or not session_id:
        return None
    return _session_key(agent, session_id)


def _bounded_optional_str(value: Any, max_chars: int) -> Optional[str]:
    text = _optional_str(value)
    if text is None:
        return None
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def _read_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STATE_VERSION, "sessions": {}}
    if not isinstance(data, dict):
        return {"version": STATE_VERSION, "sessions": {}}
    if not isinstance(data.get("sessions"), dict):
        data["sessions"] = {}
    data["version"] = STATE_VERSION
    return data


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextlib.contextmanager
def _state_lock(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows fallback
            yield
            return
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _prune_sessions(state: dict[str, Any], *, max_sessions: int) -> None:
    sessions = state.get("sessions")
    if not isinstance(sessions, dict) or len(sessions) <= max_sessions:
        return
    ordered = sorted(
        sessions.items(),
        key=lambda item: str(item[1].get("updated_at") if isinstance(item[1], dict) else ""),
        reverse=True,
    )
    state["sessions"] = dict(ordered[:max_sessions])
