"""The agent session's event log (PHILO-14 C0).

The session record in ``agent_sessions.json`` is overwritten on each hook
event: it holds the last event only. This module appends EVERY ingested hook
event to the ``agent_session_events`` table (``db/schema.py``), so the
Conductor lane can show a launched agent's timeline.

The rider hook writes here. The hook must stay fast (Conductor R3), so this
module does not import ``holdspeak.db`` (about 0.9 s): it opens the hub's
database file with plain ``sqlite3`` in ``mode=rw``. A missing file or a
missing table (the hub has not reconciled the schema yet) skips the write;
the hook never creates a database and never fails on the log.

What a row keeps (every text is secret-redacted with ``memory.defense.redact``
on the WHOLE text before it is cut):

- ``tool`` and ``head``: for Edit/Write/MultiEdit/NotebookEdit/Read the file
  path; for Bash the first 120 characters of the command; for Codex's
  ``apply_patch`` the files the patch names; for Task the description.
- ``text``: Stop's ``last_assistant_message`` (whole, cut at 8 KB), the
  prompt of ``UserPromptSubmit`` (cut at 8 KB), a Notification's message.
- ``detail_json``: ``tool_use_id`` (the gate proposal id for a gated call),
  ``notification_type``, SessionStart's ``source``, SessionEnd's ``reason``.

The newest :data:`EVENT_LOG_KEEP` rows per session are kept.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Mapping, Optional

#: Rows kept per session (the oldest go first).
EVENT_LOG_KEEP = 2000
#: Characters kept of a Bash command.
COMMAND_HEAD_CHARS = 120
#: Characters kept of a path head (one path, or the paths of a patch).
PATH_HEAD_CHARS = 300
#: Bytes kept of Stop's last assistant message and of a prompt.
TEXT_MAX_BYTES = 8 * 1024
#: The hook waits at most this long for a write lock.
WRITE_BUSY_TIMEOUT_MS = 2000

_PATH_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "Read"}
_COMMAND_TOOLS = {"Bash", "shell", "exec_command", "local_shell"}
_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def default_db_path() -> Path:
    """The hub's database file (``holdspeak.db.core.DEFAULT_DB_PATH``),
    resolved without importing ``holdspeak.db``."""
    return Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"


def _redact(text: str) -> str:
    from holdspeak.memory.defense import redact

    return redact(text)


def _cut_bytes(text: str, max_bytes: int) -> str:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", errors="ignore")


def _safe_text(value: Any, max_bytes: int = TEXT_MAX_BYTES) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    return _cut_bytes(_redact(text), max_bytes) or None


def _command_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(part) for part in value)
    return str(value or "")


def tool_head(tool: str, tool_input: Any) -> Optional[str]:
    """A short, secret-redacted head of one tool call's input."""
    data = tool_input if isinstance(tool_input, Mapping) else {}
    if tool in _PATH_TOOLS:
        path = data.get("file_path") or data.get("notebook_path") or data.get("path")
        return (_redact(str(path))[:PATH_HEAD_CHARS] or None) if path else None
    if tool in _COMMAND_TOOLS:
        command = _command_text(data.get("command") or data.get("cmd"))
        folded = " ".join(_redact(command).split())
        return folded[:COMMAND_HEAD_CHARS] or None
    if tool == "apply_patch":
        patch = _command_text(data.get("command") or data.get("patch") or data.get("input"))
        files = _PATCH_FILE_RE.findall(patch)
        text = ", ".join(f.strip() for f in files) if files else " ".join(patch.split())
        return _redact(text)[:PATH_HEAD_CHARS] or None
    if tool in {"Task", "Agent"}:
        description = data.get("description") or data.get("subagent_type")
        return (_redact(str(description))[:COMMAND_HEAD_CHARS] or None) if description else None
    return None


def event_row(payload: Mapping[str, Any], *, notification_type: Optional[str] = None) -> dict[str, Any]:
    """One hook payload as an event-log row (without ``session_key``/``ts``)."""
    event = str(payload.get("hook_event_name") or "").strip() or "unknown"
    tool = str(payload.get("tool_name") or "").strip() or None
    head = tool_head(tool, payload.get("tool_input")) if tool else None
    text: Optional[str] = None
    detail: dict[str, Any] = {}
    tool_use_id = str(payload.get("tool_use_id") or "").strip()
    if tool_use_id:
        detail["tool_use_id"] = tool_use_id
    if event in {"Stop", "SubagentStop"}:
        text = _safe_text(payload.get("last_assistant_message"))
    elif event in {"UserPromptSubmit", "UserPromptExpansion"}:
        text = _safe_text(payload.get("prompt"))
    elif event == "Notification":
        text = _safe_text(payload.get("message"))
        if notification_type:
            detail["notification_type"] = notification_type
    elif event == "SessionStart" and payload.get("source"):
        detail["source"] = str(payload.get("source"))
    elif event == "SessionEnd" and payload.get("reason"):
        detail["reason"] = str(payload.get("reason"))
    response = payload.get("tool_response")
    if isinstance(response, Mapping) and isinstance(response.get("interrupted"), bool):
        detail["interrupted"] = response["interrupted"]
    return {"event": event, "tool": tool, "head": head, "text": text, "detail": detail}


def append_event(
    session_key: str, ts: str, row: Mapping[str, Any], *,
    db_path: Optional[Path] = None, keep: int = EVENT_LOG_KEEP,
) -> bool:
    """Append one row and trim the session to ``keep`` rows. Returns whether
    it was written. Never raises: the hook must not fail on its log."""
    path = Path(db_path) if db_path else default_db_path()
    if not path.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{path}?mode=rw", uri=True, timeout=WRITE_BUSY_TIMEOUT_MS / 1000)
    except sqlite3.Error:
        return False
    try:
        conn.execute(f"PRAGMA busy_timeout = {int(WRITE_BUSY_TIMEOUT_MS)}")
        with conn:
            conn.execute(
                "INSERT INTO agent_session_events (session_key, ts, event, tool, head, text, detail_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_key, ts, str(row.get("event") or "unknown"), row.get("tool"),
                    row.get("head"), row.get("text"),
                    json.dumps(dict(row.get("detail") or {}), sort_keys=True),
                ),
            )
            conn.execute(
                "DELETE FROM agent_session_events WHERE session_key = ? AND id <= ("
                "SELECT id FROM agent_session_events WHERE session_key = ? "
                "ORDER BY id DESC LIMIT 1 OFFSET ?)",
                (session_key, session_key, int(keep)),
            )
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def list_events(
    conn: Any, session_key: str, *, after: int = 0, limit: int = 200,
) -> list[dict[str, Any]]:
    """One session's events, oldest first, with ``id > after``."""
    limit = max(1, min(int(limit), 1000))
    rows = conn.execute(
        "SELECT id, ts, event, tool, head, text, detail_json FROM agent_session_events "
        "WHERE session_key = ? AND id > ? ORDER BY id ASC LIMIT ?",
        (session_key, int(after), limit),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            detail = json.loads(row[6] or "{}")
        except ValueError:
            detail = {}
        out.append({
            "id": int(row[0]), "ts": str(row[1]), "event": str(row[2]),
            "tool": row[3], "head": row[4], "text": row[5],
            "detail": detail if isinstance(detail, dict) else {},
        })
    return out


__all__ = [
    "EVENT_LOG_KEEP",
    "append_event",
    "default_db_path",
    "event_row",
    "list_events",
    "tool_head",
]
