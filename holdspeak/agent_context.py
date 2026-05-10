"""Agent-session context registry for local coding assistants.

Claude Code and Codex hooks can report high-confidence session state
(`cwd`, `session_id`, transcript path, prompt text) that the OS cannot
reliably infer from an active terminal window. This module stores that
state in HoldSpeak's local config directory so the dictation pipeline can
prefer agent-reported project context over process/window guessing.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shlex
import shutil
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional

from .config import CONFIG_DIR

AGENT_CONTEXT_FILE = CONFIG_DIR / "agent_sessions.json"
SUPPORTED_AGENTS = {"claude", "codex"}
STATE_VERSION = 1
MAX_SESSIONS = 200
DEFAULT_RECENT_MAX_AGE_SECONDS = 30 * 60
DEFAULT_ASSISTANT_CAPTURE_MAX_CHARS = 4_096
DEFAULT_PROMPT_CAPTURE_MAX_CHARS = 4_096

HS_CONTEXT_DIR = ".hs"
HS_CONTEXT_FILES: tuple[str, ...] = (
    "instructions.md",
    "context.md",
    "memory.md",
    "workflows.md",
    "issues.md",
    "terms.md",
    "targets.md",
)
HS_CONTEXT_FILE_KEYS: dict[str, str] = {
    "instructions.md": "instructions",
    "context.md": "context",
    "memory.md": "memory",
    "workflows.md": "workflows",
    "issues.md": "issues",
    "terms.md": "terms",
    "targets.md": "targets",
}
HS_FLAT_CONTEXT_FILES: dict[str, str] = {
    ".hs_instructions": "instructions.md",
    ".hs_context": "context.md",
    ".hs_memory": "memory.md",
    ".hs_workflows": "workflows.md",
    ".hs_issues": "issues.md",
    ".hs_terms": "terms.md",
    ".hs_targets": "targets.md",
    ".hs_ignore": "ignore",
}
HS_IGNORE_FILE = "ignore"
DEFAULT_CONTEXT_MAX_BYTES = 64_000
DEFAULT_CONTEXT_PER_FILE_MAX_BYTES = 16_000
DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES = 128_000
_SECRET_CONTEXT_RE = re.compile(
    r"(api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+[a-z0-9._~+/-]{16,}|sk-[a-z0-9]{16,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AgentSession:
    """Latest known state for one Claude/Codex session."""

    agent: str
    session_id: str
    cwd: str
    updated_at: str
    hook_event_name: str
    repo_root: Optional[str] = None
    repo_anchor: Optional[str] = None
    project_name: Optional[str] = None
    transcript_path: Optional[str] = None
    model: Optional[str] = None
    last_prompt: Optional[str] = None
    last_tool_name: Optional[str] = None
    last_assistant_text: Optional[str] = None
    last_assistant_text_at: Optional[str] = None
    summary: Optional[dict[str, Any]] = None
    awaiting_response: bool = False
    capture_messages: bool = False
    created_at: Optional[str] = None
    event_count: int = 1

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "AgentSession":
        return cls(
            agent=str(raw.get("agent") or ""),
            session_id=str(raw.get("session_id") or ""),
            cwd=str(raw.get("cwd") or ""),
            updated_at=str(raw.get("updated_at") or ""),
            hook_event_name=str(raw.get("hook_event_name") or ""),
            repo_root=_optional_str(raw.get("repo_root")),
            repo_anchor=_optional_str(raw.get("repo_anchor")),
            project_name=_optional_str(raw.get("project_name")),
            transcript_path=_optional_str(raw.get("transcript_path")),
            model=_optional_str(raw.get("model")),
            last_prompt=_optional_str(raw.get("last_prompt")),
            last_tool_name=_optional_str(raw.get("last_tool_name")),
            last_assistant_text=_optional_str(raw.get("last_assistant_text")),
            last_assistant_text_at=_optional_str(raw.get("last_assistant_text_at")),
            summary=dict(raw["summary"]) if isinstance(raw.get("summary"), dict) else None,
            awaiting_response=bool(raw.get("awaiting_response")),
            capture_messages=bool(raw.get("capture_messages")),
            created_at=_optional_str(raw.get("created_at")),
            event_count=int(raw.get("event_count") or 1),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "session_id": self.session_id,
            "cwd": self.cwd,
            "updated_at": self.updated_at,
            "hook_event_name": self.hook_event_name,
            "repo_root": self.repo_root,
            "repo_anchor": self.repo_anchor,
            "project_name": self.project_name,
            "transcript_path": self.transcript_path,
            "model": self.model,
            "last_prompt": self.last_prompt,
            "last_tool_name": self.last_tool_name,
            "last_assistant_text": self.last_assistant_text,
            "last_assistant_text_at": self.last_assistant_text_at,
            "summary": dict(self.summary) if isinstance(self.summary, dict) else None,
            "awaiting_response": self.awaiting_response,
            "capture_messages": self.capture_messages,
            "created_at": self.created_at,
            "event_count": self.event_count,
        }


def ingest_agent_hook_event(
    *,
    agent: str,
    payload: Mapping[str, Any],
    state_path: Path | None = None,
    now: datetime | None = None,
    capture_messages: bool = False,
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
    state_file = state_path or AGENT_CONTEXT_FILE
    key = _session_key(normalized_agent, session_id)
    assistant_text: str | None = None
    if capture_messages and hook_event_name in {"Stop", "SubagentStop"}:
        assistant_text = extract_last_assistant_text(
            normalized_agent,
            Path(str(payload.get("transcript_path") or "")).expanduser(),
        )

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
            awaiting_response=awaiting_response,
            capture_messages=effective_capture_messages,
            created_at=_optional_str(previous.get("created_at")) or timestamp,
            event_count=event_count,
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

    normalized_project_root = _normalize_project_root(project_root)
    now = datetime.now(timezone.utc)
    candidates: list[AgentSession] = []
    for session in list_agent_sessions(state_path=state_path, agent=agent):
        if not session.awaiting_response or not session.last_assistant_text:
            continue
        if normalized_project_root and session.repo_root != normalized_project_root:
            continue
        updated = _parse_timestamp(session.updated_at)
        if updated is None or (now - updated).total_seconds() > max_age_seconds:
            continue
        candidates.append(session)
    if not candidates:
        return None
    return max(candidates, key=lambda item: _parse_timestamp(item.updated_at) or datetime.min.replace(tzinfo=timezone.utc))


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

    state_file = state_path or AGENT_CONTEXT_FILE
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

    state_file = state_path or AGENT_CONTEXT_FILE
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
    state = _read_state(state_path or AGENT_CONTEXT_FILE)
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


@dataclass(frozen=True)
class RepoRoot:
    root: Path
    anchor: str
    project_name: str


def detect_repo_root(start: Path) -> RepoRoot | None:
    """Walk upward and detect a repo/project root for agent hook state."""

    cur = start if start.is_dir() else start.parent
    try:
        cur = cur.resolve()
    except OSError:
        cur = cur.absolute()
    home = Path.home().resolve()

    while True:
        for marker, anchor in (
            (".hs", "holdspeak"),
            (".hs_context", "holdspeak-flat"),
            (".git", "git"),
            (".holdspeak", "holdspeak-legacy"),
        ):
            if (cur / marker).exists():
                return RepoRoot(root=cur, anchor=anchor, project_name=_derive_project_name(cur))
        if cur == home:
            return None
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def load_hs_project_context(
    project_root: Path,
    *,
    max_bytes: int = DEFAULT_CONTEXT_MAX_BYTES,
    per_file_max_bytes: int = DEFAULT_CONTEXT_PER_FILE_MAX_BYTES,
) -> dict[str, Any]:
    """Load repo-local HoldSpeak context using a small fixed convention."""

    root = project_root.expanduser()
    hs_dir = root / HS_CONTEXT_DIR
    payload: dict[str, Any] = {
        "root": str(root),
        "context_dir": str(hs_dir),
        "exists": hs_dir.is_dir() or any((root / name).is_file() for name in HS_FLAT_CONTEXT_FILES),
        "files": {},
        "ignore": [],
        "flat_files": {},
        "skipped": [],
        "warnings": [],
        "write_policy": {
            "canonical": ".hs/ files are editable from the web UI after user action.",
            "flat": ".hs_* files are read-only compatibility inputs; migrate edits into .hs/.",
            "automatic_writes": False,
        },
        "truncated": False,
    }
    if not payload["exists"]:
        return payload

    remaining = max(0, max_bytes)
    files: dict[str, dict[str, Any]] = {}
    flat_files: dict[str, dict[str, Any]] = {}

    for flat_name, canonical_name in HS_FLAT_CONTEXT_FILES.items():
        path = root / flat_name
        if not path.is_file():
            continue
        result = _read_context_entry(
            path,
            min(remaining, 16_000 if canonical_name == "ignore" else per_file_max_bytes),
            source="flat",
        )
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped {flat_name}: {result.get('reason')}")
            continue
        content = str(result.get("content") or "")
        remaining = max(0, remaining - len(content.encode("utf-8")))
        flat_files[flat_name] = {
            "path": str(path),
            "canonical_name": canonical_name,
            "content": content,
            "truncated": bool(result.get("truncated")),
            "read_only": True,
        }
        if canonical_name == "ignore":
            payload["ignore"] = _parse_ignore_lines(content)
            if canonical_name not in files:
                files[canonical_name] = {
                    "path": str(path),
                    "content": content,
                    "truncated": bool(result.get("truncated")),
                    "source": "flat",
                    "read_only": True,
                }
        elif canonical_name not in files:
            files[canonical_name] = {
                "path": str(path),
                "content": content,
                "truncated": bool(result.get("truncated")),
                "source": "flat",
                "read_only": True,
            }
        if result.get("truncated"):
            payload["truncated"] = True

    for name in HS_CONTEXT_FILES:
        path = hs_dir / name
        if not path.is_file():
            continue
        # Avoid letting one large file starve later canonical files. The
        # global budget still caps total prompt material.
        result = _read_context_entry(path, min(remaining, per_file_max_bytes), source="directory")
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped .hs/{name}: {result.get('reason')}")
            continue
        content = str(result.get("content") or "")
        remaining = max(0, remaining - len(content.encode("utf-8")))
        files[name] = {
            "path": str(path),
            "content": content,
            "truncated": bool(result.get("truncated")),
            "source": "directory",
            "read_only": False,
        }
        if result.get("truncated"):
            payload["truncated"] = True
    payload["files"] = files
    payload["flat_files"] = flat_files

    ignore_path = hs_dir / HS_IGNORE_FILE
    if ignore_path.is_file():
        result = _read_context_entry(ignore_path, min(remaining, 16_000), source="directory")
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped .hs/{HS_IGNORE_FILE}: {result.get('reason')}")
        else:
            content = str(result.get("content") or "")
            payload["ignore"] = _parse_ignore_lines(content)
            files[HS_IGNORE_FILE] = {
                "path": str(ignore_path),
                "content": content,
                "truncated": bool(result.get("truncated")),
                "source": "directory",
                "read_only": False,
            }
        if result.get("truncated"):
            payload["truncated"] = True

    return payload


def compact_hs_project_context(context: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a template-friendly `.hs/` context mapping for `ProjectContext`."""

    if not context.get("exists"):
        return None
    compact: dict[str, Any] = {}
    files = context.get("files")
    if isinstance(files, dict):
        for filename, key in HS_CONTEXT_FILE_KEYS.items():
            entry = files.get(filename)
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content") or "").strip()
            if content:
                compact[key] = content
    ignore = context.get("ignore")
    if isinstance(ignore, list):
        compact["ignore"] = [str(item) for item in ignore if str(item).strip()]
    rendered = render_hs_context_for_prompt(context).strip()
    if rendered:
        compact["prompt_context"] = rendered
    compact["context_dir"] = str(context.get("context_dir") or "")
    compact["truncated"] = bool(context.get("truncated"))
    return compact


def render_hs_context_for_prompt(context: Mapping[str, Any]) -> str:
    """Render loaded `.hs/` context as compact prompt material."""

    if not context.get("exists"):
        return ""
    parts: list[str] = []
    files = context.get("files")
    if isinstance(files, dict):
        for name in HS_CONTEXT_FILES:
            entry = files.get(name)
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content") or "").strip()
            if not content:
                continue
            parts.append(f"## .hs/{name}\n{content}")
    ignore = context.get("ignore")
    if isinstance(ignore, list) and ignore:
        parts.append("## .hs/ignore\n" + "\n".join(f"- {item}" for item in ignore))
    return "\n\n".join(parts)


def claude_hook_template(*, capture_messages: bool = False) -> dict[str, Any]:
    command = _agent_hook_command("claude", capture_messages=capture_messages)
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "CwdChanged": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
        }
    }


def codex_hook_template(*, capture_messages: bool = False) -> dict[str, Any]:
    command = _agent_hook_command("codex", capture_messages=capture_messages)
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash|apply_patch|Edit|Write",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|apply_patch|Edit|Write",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
        }
    }


def _agent_hook_command(agent: str, *, capture_messages: bool = False) -> str:
    executable = shutil.which("holdspeak") or "holdspeak"
    capture = " --capture-messages" if capture_messages else ""
    return f"{shlex.quote(executable)} agent-hook ingest --agent {agent}{capture}"


def _payload_cwd(payload: Mapping[str, Any]) -> str:
    if str(payload.get("hook_event_name") or "") == "CwdChanged":
        new_cwd = payload.get("new_cwd")
        if isinstance(new_cwd, str) and new_cwd.strip():
            return new_cwd
    cwd = payload.get("cwd")
    return cwd if isinstance(cwd, str) else ""


def _session_key(agent: str, session_id: str) -> str:
    return f"{agent}:{session_id}"


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bounded_optional_str(value: Any, max_chars: int) -> Optional[str]:
    text = _optional_str(value)
    if text is None:
        return None
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def _normalize_project_root(project_root: str | Path | None) -> str | None:
    if project_root is None:
        return None
    raw = str(project_root).strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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


def _derive_project_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        name = _read_toml_name(pyproject, ("project", "name"))
        if name:
            return name
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            raw = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = None
        if isinstance(raw, dict) and isinstance(raw.get("name"), str) and raw["name"].strip():
            return raw["name"].strip()
    return root.name


def _read_toml_name(path: Path, dotted: tuple[str, ...]) -> str | None:
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        return None
    try:
        with path.open("rb") as handle:
            data: Any = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    cursor: Any = data
    for key in dotted:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor.strip() if isinstance(cursor, str) and cursor.strip() else None


def _read_text_budget(path: Path, budget: int) -> tuple[str, bool]:
    if budget <= 0:
        return "", True
    try:
        raw = path.read_bytes()
    except OSError:
        return "", False
    truncated = len(raw) > budget
    if truncated:
        raw = raw[:budget]
    return raw.decode("utf-8", errors="replace"), truncated


def _read_context_entry(path: Path, budget: int, *, source: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": f"read_error:{exc.__class__.__name__}",
        }
    if len(raw) > DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "too_large",
            "size_bytes": len(raw),
            "max_bytes": DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
        }
    if b"\x00" in raw:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "binary",
            "size_bytes": len(raw),
        }
    truncated = len(raw) > budget
    if truncated:
        raw = raw[: max(0, budget)]
    content = raw.decode("utf-8", errors="replace")
    if _SECRET_CONTEXT_RE.search(content):
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "possible_secret",
            "size_bytes": len(raw),
        }
    return {
        "path": str(path),
        "source": source,
        "content": content,
        "truncated": truncated,
    }


def _parse_ignore_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
