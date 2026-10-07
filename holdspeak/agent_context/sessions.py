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
from .hooks import detect_story_claim, detect_tmux_context
from .hs_context import _normalize_project_root, detect_repo_root
from .models import (
    AgentSession,
    DEFAULT_ASSISTANT_CAPTURE_MAX_CHARS,
    DEFAULT_LIFECYCLE_DEAD_SECONDS,
    DEFAULT_LIFECYCLE_IDLE_SECONDS,
    DEFAULT_PROMPT_CAPTURE_MAX_CHARS,
    DEFAULT_RECENT_MAX_AGE_SECONDS,
    DEFAULT_STALE_AGENT_SESSION_SECONDS,
    IDLE_NOTIFICATION,
    LIFECYCLE_ENDED,
    LIFECYCLE_IDLE,
    LIFECYCLE_WAITING,
    LIFECYCLE_WORKING,
    MAX_SESSIONS,
    PERMISSION_NOTIFICATION,
    STATE_VERSION,
    SUPPORTED_AGENTS,
    is_blocked,
    is_blocking_notification,
)


# HSM-17-02: hook-event → raw lifecycle. Events that mean "the coder is
# actively doing things" are heartbeats (working); `Notification` and `Stop`
# mean the coder handed the turn to the human (waiting); `SessionEnd` is the
# tombstone. Unknown events keep the prior lifecycle (a heartbeat at most).
_WORKING_EVENTS = {
    "SessionStart",
    "CwdChanged",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PostToolUse",
    "PreCompact",
    "SubagentStop",
}
# Codex has no Notification: its approval prompt is ``PermissionRequest``.
_WAITING_EVENTS = {"Notification", "Stop", "PermissionRequest"}
_ENDED_EVENTS = {"SessionEnd"}

#: Conductor K2: a Hand-to-agent launch carries the rider hooks in its
#: ``--settings`` file, and the owner may also have them in
#: ``~/.claude/settings.json`` (K1's one-press install). Claude Code then runs
#: both for one event. The second run is the SAME event when its genuine
#: identity matches the session's last event within this window: it is
#: merged (a capturing hook's question is kept, whichever runs first) and
#: not counted again.
DUPLICATE_EVENT_WINDOW_SECONDS = 5.0
_TRANSCRIPT_TAIL_BYTES = 4096


def _transcript_mark(payload: Mapping[str, Any]) -> Optional[str]:
    """Where the session's transcript stands: its size and the hash of its
    tail. Two runs of one event see the same mark; a later event (a new
    Stop after more work) sees another."""
    import hashlib

    raw = str(payload.get("transcript_path") or "").strip()
    if not raw:
        return None
    try:
        path = Path(raw).expanduser()
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(0, size - _TRANSCRIPT_TAIL_BYTES))
            tail = handle.read()
    except OSError:
        return None
    return f"{size}:{hashlib.sha256(tail).hexdigest()}"


def _event_identity(event: str, payload: Mapping[str, Any], *context: Any) -> Optional[str]:
    """The event's genuine identity, or ``None`` when the payload has none
    (then the event is always recorded: equal payloads are not enough).

    A tool event has its ``tool_use_id``. Any other event is identified by
    where the transcript stands plus its own message fields (a Stop by its
    transcript, a Notification by its message and type)."""
    import hashlib

    tool_use_id = str(payload.get("tool_use_id") or "").strip()
    if tool_use_id:
        basis: list[Any] = [event, "tool", tool_use_id]
    else:
        mark = _transcript_mark(payload)
        if mark is None:
            return None
        basis = [
            event, "transcript", mark,
            payload.get("message"), payload.get("notification_type"),
            payload.get("prompt"), payload.get("source"), payload.get("reason"),
        ]
    canonical = json.dumps([*basis, *context], sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lifecycle_for_event(hook_event_name: str, previous_lifecycle: str) -> str:
    if hook_event_name in _ENDED_EVENTS:
        return LIFECYCLE_ENDED
    if hook_event_name in _WAITING_EVENTS:
        return LIFECYCLE_WAITING
    if hook_event_name in _WORKING_EVENTS:
        return LIFECYCLE_WORKING
    return previous_lifecycle or LIFECYCLE_WORKING


def _notification_type(payload: Mapping[str, Any], message: str | None) -> str | None:
    """The Notification subtype: Claude Code's hook input carries
    ``notification_type`` (``permission_prompt``, ``idle_prompt``,
    ``auth_success``, ``elicitation_dialog``). An older payload without it is
    read from its message ("Claude needs your permission to use Bash",
    "Claude is waiting for your input")."""
    given = _optional_str(payload.get("notification_type"))
    if given:
        return given.strip().lower()
    text = (message or "").lower()
    if "permission" in text:
        return "permission_prompt"
    if "waiting for your input" in text:
        return "idle_prompt"
    return None


def _codex_permission_question(payload: Mapping[str, Any]) -> str | None:
    """The ask of a Codex ``PermissionRequest`` (observed on 0.159:
    ``tool_name`` plus ``tool_input.command`` and ``tool_input.description``;
    no message): its reason, else the command."""
    tool_input = payload.get("tool_input")
    raw = tool_input if isinstance(tool_input, Mapping) else {}
    tool = _optional_str(payload.get("tool_name")) or "a tool"
    reason = _optional_str(raw.get("description"))
    command = _optional_str(raw.get("command"))
    if reason:
        return f"Codex asks to use {tool}: {reason}"
    if command:
        return f"Codex asks to run: {command}"
    return f"Codex asks to use {tool}"


def _filter_question(text: str | None) -> str | None:
    """Secret-filter a captured question (HSM-17-02 acceptance: reuse the
    dictation journal's whole-field redaction so a synced question can never
    carry a token/key)."""
    if not text:
        return None
    # The light home of the journal's check: no plugin host on the hook path.
    from holdspeak.project_doc_suggestions import filter_secret

    filtered = filter_secret(str(text).strip())
    return filtered or None


def effective_state(
    session: AgentSession,
    *,
    now: datetime | None = None,
    idle_after_seconds: int = DEFAULT_LIFECYCLE_IDLE_SECONDS,
    dead_after_seconds: int = DEFAULT_LIFECYCLE_DEAD_SECONDS,
) -> str:
    """The state a consumer should render: the raw lifecycle plus decay.

    `ended` is sticky. A session whose last heartbeat is older than
    `idle_after_seconds` decays to `idle`; older than `dead_after_seconds`
    tombstones to `ended`. Computed at read time — the registry is never
    rewritten by staleness.
    """
    if session.lifecycle == LIFECYCLE_ENDED:
        return LIFECYCLE_ENDED
    updated = _parse_timestamp(session.updated_at)
    if updated is None:
        return session.lifecycle or LIFECYCLE_WORKING
    age = ((now or datetime.now(timezone.utc)) - updated).total_seconds()
    if age > dead_after_seconds:
        return LIFECYCLE_ENDED
    if age > idle_after_seconds:
        return LIFECYCLE_IDLE
    return session.lifecycle or LIFECYCLE_WORKING


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
    events_db_path: Path | None = None,
) -> AgentSession:
    """Record one Claude/Codex hook event and return the normalized session.

    PHILO-14 C0: the event is also appended to the session's event log
    (``event_log``), once per event (a duplicate from a second hook source
    is not appended again). ``events_db_path`` names the database; ``None``
    uses the hub's database when ``state_path`` is not given (a test or
    debug registry does not write the hub's log)."""

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
    # Conductor R1: Claude Code 2.1.x puts the turn's last assistant message
    # in the Stop payload itself. A question read from it needs no transcript
    # read, so a launched agent (whose rider hooks do not opt in to message
    # capture) still reaches Needs you when it asks. Only the question is kept
    # (secret-filtered), never the message. Codex's Stop is read below (R3).
    stop_text: str | None = None
    if normalized_agent != "codex" and hook_event_name == "Stop" and not assistant_text:
        stop_text = _optional_str(payload.get("last_assistant_message"))
    codex_last_message: str | None = None
    if normalized_agent == "codex" and hook_event_name == "Stop":
        text = " ".join(str(payload.get("last_assistant_message") or "").split())
        codex_last_message = text[-DEFAULT_ASSISTANT_CAPTURE_MAX_CHARS:] or None
    tmux_context = detect_tmux_context(payload, env=env)
    detected_claim = detect_story_claim(payload, env=env)
    identity = _event_identity(hook_event_name, payload, detected_claim, tmux_context)

    with _state_lock(state_file):
        state = _read_state(state_file)
        sessions = state.setdefault("sessions", {})
        previous_raw = sessions.get(key) if isinstance(sessions, dict) else None
        previous = previous_raw if isinstance(previous_raw, dict) else {}
        duplicate = False
        if identity is not None and previous.get("last_event_id") == identity:
            seen = _parse_timestamp(_optional_str(previous.get("last_event_at")) or "")
            current = _parse_timestamp(timestamp)
            duplicate = (
                seen is not None
                and current is not None
                and abs((current - seen).total_seconds()) <= DUPLICATE_EVENT_WINDOW_SECONDS
            )
        # The same event from a second hook source is merged, not counted.
        event_count = int(previous.get("event_count") or 0) + (0 if duplicate else 1)
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
        elif stop_text:
            awaiting_response = looks_like_agent_question(stop_text)

        # HSM-17-02: the raw lifecycle + the pending question. A `Notification`
        # carries the blocking ask in `message` (permission prompts, "waiting
        # for your input"); a question-shaped `Stop` reuses the captured
        # assistant text. Any working event clears the question — the coder
        # resumed. Everything captured here is secret-filtered.
        lifecycle = _lifecycle_for_event(
            hook_event_name, _optional_str(previous.get("lifecycle")) or LIFECYCLE_WORKING
        )
        question = _optional_str(previous.get("question"))
        notification_type = _optional_str(previous.get("notification_type"))
        message = _optional_str(payload.get("message")) or _optional_str(payload.get("prompt"))
        # Conductor K3: a Notification that is not a prompt (``auth_success``,
        # an unknown subtype) does not ask the owner anything. It never
        # creates or extends a wait: the session's blocked state, its event
        # name and its freshness stay as they were.
        passive = hook_event_name == "Notification" and not is_blocking_notification(
            _notification_type(payload, message)
        )
        recorded_event = hook_event_name
        updated_at = (_optional_str(previous.get("updated_at")) or timestamp) if duplicate else timestamp
        if passive:
            lifecycle = _optional_str(previous.get("lifecycle")) or LIFECYCLE_WORKING
            recorded_event = _optional_str(previous.get("hook_event_name")) or hook_event_name
            updated_at = _optional_str(previous.get("updated_at")) or timestamp
        elif lifecycle == LIFECYCLE_WORKING:
            question = None
            notification_type = None
            # The coder resumed: an earlier ask is not pending any more.
            awaiting_response = False
        elif hook_event_name == "Notification":
            notification_type = _notification_type(payload, message)
            # An idle reminder ("waiting for your input") does not replace a
            # question the agent already asked: the question is the ask.
            if not (notification_type == "idle_prompt" and question):
                question = _filter_question(message) or question
        elif hook_event_name == "PermissionRequest":
            # Codex's approval prompt: a permission wait, never answered for the owner.
            notification_type = PERMISSION_NOTIFICATION
            question = _filter_question(_codex_permission_question(payload)) or question
        elif hook_event_name == "Stop" and codex_last_message:
            # Codex: the end of a turn is its wait for input (Claude Code says
            # so with an idle_prompt Notification; Codex sends no such event).
            # The ask is the agent's last message, which the Stop payload carries.
            question = _filter_question(codex_last_message)
            notification_type = IDLE_NOTIFICATION
            awaiting_response = bool(question)
        elif hook_event_name == "Stop" and (assistant_text or stop_text) and awaiting_response:
            question = _filter_question(assistant_text or stop_text or "")
            notification_type = None

        session = AgentSession(
            agent=normalized_agent,
            session_id=session_id,
            cwd=str(cwd_path),
            updated_at=updated_at,
            hook_event_name=recorded_event,
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
            lifecycle=lifecycle,
            question=question,
            notification_type=notification_type,
        )
        # Conductor K3: the wait episode. A session that becomes blocked
        # starts a new episode (start time + id); one that stays blocked keeps
        # it (repeated reports, a restart: the registry holds it); one that
        # is not blocked has none.
        if is_blocked(session):
            if is_blocked(previous) and previous.get("wait_id"):
                session = replace(
                    session,
                    wait_started_at=_optional_str(previous.get("wait_started_at")) or timestamp,
                    wait_id=str(previous["wait_id"]),
                )
            else:
                session = replace(
                    session, wait_started_at=timestamp, wait_id=f"{timestamp}#{event_count}",
                )
        record = session.to_dict()
        # HS-94-04: additive rider-claim emission. When the hook's context
        # carries an explicit Story identity (typed payload or the launcher's
        # HOLDSPEAK_STORY_* env), the session record emits a durable claim the
        # hub resolves into an exact Work attempt. The claim is sticky across
        # heartbeats (like tmux context); claimed_at only moves when the
        # claimed Story actually changes. Sessions remain node presence —
        # attempts stay hub runtime records (the story's direction rule).
        previous_claim = (
            dict(previous["story_claim"])
            if isinstance(previous.get("story_claim"), dict)
            else None
        )
        story_claim = _merge_story_claim(
            previous_claim, detected_claim, agent=normalized_agent, timestamp=timestamp
        )
        if story_claim:
            record["story_claim"] = story_claim
        if identity is not None:
            record["last_event_id"] = identity
            record["last_event_at"] = (
                _optional_str(previous.get("last_event_at")) or timestamp
            ) if duplicate else timestamp
        sessions[key] = record
        state["version"] = STATE_VERSION
        _prune_sessions(state, max_sessions=MAX_SESSIONS)
        _write_state(state_file, state)

    if not duplicate and (events_db_path is not None or state_path is None):
        from . import event_log

        try:
            row = event_log.event_row(
                payload,
                notification_type=_notification_type(payload, message)
                if hook_event_name == "Notification" else None,
            )
            event_log.append_event(key, timestamp, row, db_path=events_db_path)
        except Exception:  # the log never fails the hook
            pass

    return session


def _merge_story_claim(
    previous: Optional[dict[str, Any]],
    detected: Mapping[str, Any],
    *,
    agent: str,
    timestamp: str,
) -> Optional[dict[str, Any]]:
    """Sticky rider-claim merge (HS-94-04): a detected claim wins; an
    unchanged Story keeps its original claimed_at; no detection carries
    the previous claim forward untouched."""
    project = str(detected.get("project") or "").strip() if detected else ""
    story_id = str(detected.get("story_id") or "").strip() if detected else ""
    if project and story_id:
        claimed_at = timestamp
        if (
            previous
            and str(previous.get("project") or "") == project
            and str(previous.get("story_id") or "") == story_id
            and previous.get("claimed_at")
        ):
            claimed_at = str(previous["claimed_at"])
        return {
            "project": project,
            "story_id": story_id,
            "claimed_by": f"rider:{agent}",
            "claimed_at": claimed_at,
        }
    return previous


def list_agent_story_claims(
    *,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Every session carrying an explicit rider Story claim (HS-94-04).

    Read-only over the registry; each row pairs the claim with the
    session's presence facts the hub needs to resolve an exact Work
    attempt: the compound session key, repo root/cwd (server-side
    resolution input, never wire data), the effective lifecycle, and
    the tmux pane hint. Ordering is newest-updated first.
    """
    state = _read_state(state_path or _default_state_file())
    raw_sessions = state.get("sessions")
    if not isinstance(raw_sessions, dict):
        return []
    moment = now or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for raw in raw_sessions.values():
        if not isinstance(raw, dict):
            continue
        claim = raw.get("story_claim")
        if not isinstance(claim, dict):
            continue
        project = _optional_str(claim.get("project"))
        story_id = _optional_str(claim.get("story_id"))
        if not project or not story_id:
            continue
        session = AgentSession.from_mapping(raw)
        if not session.agent or not session.session_id:
            continue
        rows.append(
            {
                "session_key": _session_key(session.agent, session.session_id),
                "agent": session.agent,
                "session_id": session.session_id,
                "cwd": session.cwd,
                "repo_root": session.repo_root,
                "updated_at": session.updated_at,
                "lifecycle": effective_state(session, now=moment),
                "tmux_pane": session.tmux_pane,
                "story_claim": {
                    "project": project,
                    "story_id": story_id,
                    "claimed_by": _optional_str(claim.get("claimed_by"))
                    or f"rider:{session.agent}",
                    "claimed_at": _optional_str(claim.get("claimed_at")),
                },
            }
        )
    rows.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return rows


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
            wait_started_at=None,
            wait_id=None,
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
                wait_started_at=None,
                wait_id=None,
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


class AgentRegistryUnreadable(RuntimeError):
    """The session registry exists and cannot be read as a registry."""


def read_agent_sessions_strict(*, state_path: Path | None = None) -> list[AgentSession]:
    """The registry's sessions, or an error -- never a silent empty list.

    For a reader that must tell "no agents" from "could not read" (the Needs
    you coverage, Conductor K3). An absent file is a first run: no sessions.
    A file that cannot be read, is not JSON, or does not hold a registry
    raises :class:`AgentRegistryUnreadable`.
    """
    path = state_path or _default_state_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentRegistryUnreadable(f"agent registry unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise AgentRegistryUnreadable("agent registry is not an object")
    raw = data.get("sessions")
    if not isinstance(raw, dict):
        # The hooks always write ``sessions``: a registry without it (or with
        # another shape) is not one this reader understands.
        raise AgentRegistryUnreadable("agent registry has no sessions object")
    bad = [key for key, row in raw.items() if not isinstance(row, dict)]
    if bad:
        raise AgentRegistryUnreadable(f"agent registry rows are not objects: {', '.join(map(str, bad[:3]))}")
    sessions = [AgentSession.from_mapping(row) for row in raw.values()]
    return sorted(sessions, key=lambda item: item.updated_at, reverse=True)


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
