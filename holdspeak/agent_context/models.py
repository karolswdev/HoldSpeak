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
    # Conductor K3: the Notification hook's subtype (``permission_prompt``,
    # ``idle_prompt``, ...) for the current wait, and the wait EPISODE: when
    # the session began to block on the owner and a stable id for that
    # episode. Repeated reports of one wait keep both; a new wait (after the
    # owner answered or the agent worked) gets new ones.
    notification_type: Optional[str] = None
    wait_started_at: Optional[str] = None
    wait_id: Optional[str] = None

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
            notification_type=_optional_str(raw.get("notification_type")),
            wait_started_at=_optional_str(raw.get("wait_started_at")),
            wait_id=_optional_str(raw.get("wait_id")),
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
            "notification_type": self.notification_type,
            "wait_started_at": self.wait_started_at,
            "wait_id": self.wait_id,
        }


#: Notification subtypes that block on the owner (Claude Code hook input
#: ``notification_type``). Any other subtype (``auth_success``, an unknown
#: one) never creates or extends a wait. A Notification with no subtype (an
#: older payload whose message did not name it) is read as blocking.
BLOCKING_NOTIFICATIONS = frozenset({"permission_prompt", "idle_prompt", "elicitation_dialog"})

#: The Notification subtype of a permission prompt.
PERMISSION_NOTIFICATION = "permission_prompt"
#: The Notification subtype of "the agent waits for your input".
IDLE_NOTIFICATION = "idle_prompt"

#: The hook events that carry a prompt subtype: Claude Code's
#: ``Notification`` and Codex's ``PermissionRequest`` (its approval prompt;
#: Codex has no Notification event).
PROMPT_EVENTS = frozenset({"Notification", "PermissionRequest"})


def _field(session: Any, name: str) -> Any:
    if isinstance(session, Mapping):
        return session.get(name)
    return getattr(session, name, None)


def is_blocking_notification(notification_type: Any) -> bool:
    """True for a prompt subtype, or no subtype at all (an older payload)."""
    kind = str(notification_type or "").strip()
    return not kind or kind in BLOCKING_NOTIFICATIONS


def is_blocked(session: Any) -> bool:
    """THE blocked predicate (Conductor K3): the session waits on the owner.

    One rule for the Needs you membership (R5) and the hub's coder watcher.
    Not ended and a non-empty captured question; then, when the latest hook
    event is a ``Notification``, its subtype decides (a prompt blocks, a
    non-blocking subtype never does); otherwise the agent asked
    (``awaiting_response``). Working events clear the question and the flag,
    so a session that resumed is not blocked. Freshness is the reader's
    rule, not this one.
    """
    if str(_field(session, "lifecycle") or "") == LIFECYCLE_ENDED:
        return False
    if not str(_field(session, "question") or "").strip():
        return False
    if str(_field(session, "hook_event_name") or "") in PROMPT_EVENTS:
        return is_blocking_notification(_field(session, "notification_type"))
    return bool(_field(session, "awaiting_response"))


#: The words of a turn end (PHILO-15 B48): a real question waits (``asks``),
#: the agent reports its work complete (``done``), or it stopped with no
#: question (``idle``).
TURN_ASKS = "asks"
TURN_IDLE = "idle"
TURN_DONE = "done"

#: A sentence that ends in a question mark (optionally closed by a quote,
#: a bracket or markdown emphasis), at a line end or before a space. A
#: ``?`` inside a URL (``/?q=1``) is not one.
_QUESTION_RE = re.compile(r"\?[\"'\u2019\u201d)\]*_`]*(?:\s|$)")

#: An interrogative that asks the owner, wherever it stands: an inverted
#: modal or auxiliary with I/we/you ("Should I deploy", "Do you want"), or an
#: offer ("Want me to ...", "Would you like ...").
_INTERROGATIVE_RE = re.compile(
    r"\b(?:(?:should|shall|may|can|could|would|will|do|does|did|is|are)\s+(?:i|we|you)\b"
    r"|want\s+me\s+to\b|would\s+you\s+like\b|do\s+you\s+want\b)",
    re.IGNORECASE,
)


def asks_a_question(text: Any) -> bool:
    """The agent's turn end asks the owner something: a ``?`` that ends a
    sentence, or an interrogative, ANYWHERE in its words, however long the
    report around it (the ruling shared with lane 15, Astra r2 on #996 and
    #998). "Should I deploy to production? The change is done and all tests
    pass." is a question; "Done. PR #2 is open." is not.

    This is THE question predicate: Needs you, the lane's stations, the
    Conductor lamp and the responder's silence rule read it (``needsYou.ts``
    ``asksAQuestion`` mirrors it)."""
    body = str(text or "").strip()
    if not body:
        return False
    return bool(_QUESTION_RE.search(body) or _INTERROGATIVE_RE.search(body))


#: A report of a problem: a failed check, an error, a block (PHILO-15 15,
#: Astra r1 on #998: "PR #3 is open but the lint check failed" is never DONE).
_PROBLEM_RE = re.compile(
    r"\b(?:fail(?:s|ed|ing|ure)?|error(?:s|ed)?|broken|blocked|cannot|can't|couldn't|"
    r"unable|timed out|did not pass|didn't pass|not passing)\b",
    re.IGNORECASE,
)


#: A negated problem word is no problem (Astra r2 on #998: "all checks
#: passed with no errors"): these phrases are read out before the match.
_NEGATED_PROBLEM_RE = re.compile(
    r"\b(?:no|without|zero|0|did\s+not|didn't|never)\s+(?:new\s+|further\s+)?"
    r"(?:fail(?:s|ed|ing|ures?)?|errors?|problems?|blockers?)\b"
    r"|\berror[- ]free\b"
    # PHILO-15 20 (B68): the gate held the agent's own attempt and the owner
    # decided it ("the earlier /tmp write attempts were blocked, so nothing
    # landed outside"): a report of the owner's decision, not a problem.
    r"|\b(?:attempts?|writes?|calls?|commands?|tries)\s+(?:were|was|got)\s+(?:blocked|denied)\b"
    r"|\b(?:blocked|denied)\s+by\s+the\s+(?:gate|desk|owner|hook)\b",
    re.IGNORECASE,
)


def reports_a_problem(text: Any) -> bool:
    """The agent's turn end reports a problem the owner must see (a failed
    check, an error, a block), question or not; a negated one ("no errors",
    "without failures") is not. The responder reads it too (``needsYou.ts``
    ``reportsAProblem`` mirrors it)."""
    body = _NEGATED_PROBLEM_RE.sub(" ", str(text or ""))
    return bool(_PROBLEM_RE.search(body))


def turn_end(session: Any, *, work_done: bool = False) -> str:
    """How a blocked session's turn ended: ``asks`` for a permission prompt,
    a real question or a reported problem, else ``done`` when the work is
    delivered (``work_done``: the launch's PR is open) or ``idle``."""
    if wait_kind(session) == "approve":
        return TURN_ASKS
    question = _field(session, "question")
    if asks_a_question(question) or reports_a_problem(question):
        return TURN_ASKS
    return TURN_DONE if work_done else TURN_IDLE


def wait_kind(session: Any) -> str:
    """``approve`` for a permission prompt, else ``answer``."""
    if (
        str(_field(session, "hook_event_name") or "") in PROMPT_EVENTS
        and str(_field(session, "notification_type") or "") == PERMISSION_NOTIFICATION
    ):
        return "approve"
    return "answer"
