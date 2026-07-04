"""Constants + the `AgentSession` model for `agent_context` (HS-34-03).

`AGENT_CONTEXT_FILE` lives here and is re-exported by the package `__init__`;
`sessions.py` reads it *via the package* so tests that monkeypatch
`holdspeak.agent_context.AGENT_CONTEXT_FILE` are honored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from ..config import CONFIG_DIR
from ._common import _optional_str


AGENT_CONTEXT_FILE = CONFIG_DIR / "agent_sessions.json"


SUPPORTED_AGENTS = {"claude", "codex"}


STATE_VERSION = 1


MAX_SESSIONS = 200


DEFAULT_RECENT_MAX_AGE_SECONDS = 30 * 60


DEFAULT_STALE_AGENT_SESSION_SECONDS = 120


# HSM-17-02: the live-session lifecycle. `lifecycle` is the RAW state written
# by the last hook event (working | waiting | ended); the *effective* state a
# consumer sees (`effective_state`) additionally decays a session with no
# heartbeat to `idle`, and a dead one to `ended`, at read time — no background
# job ever rewrites the registry.
LIFECYCLE_WORKING = "working"
LIFECYCLE_WAITING = "waiting"
LIFECYCLE_IDLE = "idle"
LIFECYCLE_ENDED = "ended"

DEFAULT_LIFECYCLE_IDLE_SECONDS = 30 * 60

DEFAULT_LIFECYCLE_DEAD_SECONDS = 4 * 60 * 60


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
    tmux_pane: Optional[str] = None
    tmux_session: Optional[str] = None
    tmux_window: Optional[str] = None
    tmux_pane_index: Optional[str] = None
    tmux_pane_current_path: Optional[str] = None
    awaiting_response: bool = False
    capture_messages: bool = False
    created_at: Optional[str] = None
    event_count: int = 1
    pinned: bool = False
    # HSM-17-02: the raw lifecycle from the last hook event and the pending
    # question (secret-filtered at ingest) when the coder blocks on the human.
    lifecycle: str = LIFECYCLE_WORKING
    question: Optional[str] = None

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
            tmux_pane=_optional_str(raw.get("tmux_pane")),
            tmux_session=_optional_str(raw.get("tmux_session")),
            tmux_window=_optional_str(raw.get("tmux_window")),
            tmux_pane_index=_optional_str(raw.get("tmux_pane_index")),
            tmux_pane_current_path=_optional_str(raw.get("tmux_pane_current_path")),
            awaiting_response=bool(raw.get("awaiting_response")),
            capture_messages=bool(raw.get("capture_messages")),
            created_at=_optional_str(raw.get("created_at")),
            event_count=int(raw.get("event_count") or 1),
            pinned=bool(raw.get("pinned")),
            lifecycle=_optional_str(raw.get("lifecycle")) or LIFECYCLE_WORKING,
            question=_optional_str(raw.get("question")),
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
            "tmux_pane": self.tmux_pane,
            "tmux_session": self.tmux_session,
            "tmux_window": self.tmux_window,
            "tmux_pane_index": self.tmux_pane_index,
            "tmux_pane_current_path": self.tmux_pane_current_path,
            "awaiting_response": self.awaiting_response,
            "capture_messages": self.capture_messages,
            "created_at": self.created_at,
            "event_count": self.event_count,
            "pinned": self.pinned,
            "lifecycle": self.lifecycle,
            "question": self.question,
        }
