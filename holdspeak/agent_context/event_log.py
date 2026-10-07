"""The agent session's event log (PHILO-14 C0).

The session record in ``agent_sessions.json`` is overwritten on each hook
event: it holds the last event only. This module keeps EVERY ingested hook
event, so the Conductor lane can show a launched agent's timeline.

Two legs, so the hook never waits on the hub (Conductor R3):

1. The rider hook SPOOLS the event: one small JSON file per event under
   ``~/.holdspeak/agent-events/`` (folder 0700, file 0600), written to a
   hidden name and renamed into place. No lock, no database, O(1).
2. The hub DRAINS the spool into ``agent_session_events`` (``db/schema.py``)
   on each lane read, each ``/api/coders/sessions`` read
   (:func:`drain_spool`), and on its own timer every 2 s while a launch is
   live (:class:`SpoolTimer`, PHILO-14 C0b). A drain is idempotent (``spool_id`` is unique), and
   a file goes only after its row is committed. When the table does not
   exist yet, the files stay until the schema reconciles.

What a row keeps (every text is secret-redacted with ``memory.defense.redact``
on the WHOLE text before it is cut):

- ``tool`` and ``head``: for Edit/Write/MultiEdit/NotebookEdit/Read the file
  path; for Bash the first 120 characters of the command; for Codex's
  ``apply_patch`` the files a ``*** Update File:`` patch names (any other
  input shape: no head; the shape is not verified on a real Codex);
  for Task the description.
- ``text``: Stop's ``last_assistant_message`` (whole, cut at 8 KB), the
  prompt of ``UserPromptSubmit`` (cut at 8 KB), a Notification's message.
- ``detail_json``: ``tool_use_id`` (the gate proposal id for a gated call),
  ``notification_type``, SessionStart's ``source``, SessionEnd's ``reason``,
  ``interrupted``.

The newest :data:`EVENT_LOG_KEEP` rows per session are kept.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

#: Rows kept per session (the oldest go first).
EVENT_LOG_KEEP = 2000
#: Characters kept of a Bash command.
COMMAND_HEAD_CHARS = 120
#: Characters kept of a path head (one path, or the paths of a patch).
PATH_HEAD_CHARS = 300
#: Bytes kept of Stop's last assistant message and of a prompt.
TEXT_MAX_BYTES = 8 * 1024
#: Files one drain takes (the rest wait for the next drain).
DRAIN_MAX_FILES = 5000
_SPOOL_SUFFIX = ".json"
_LOCK_NAME = ".drain.lock"

log = logging.getLogger(__name__)

_PATH_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "Read"}
_COMMAND_TOOLS = {"Bash", "shell", "exec_command", "local_shell"}
_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def default_spool_dir() -> Path:
    """Where the rider hook spools events for the hub to drain."""
    return Path.home() / ".holdspeak" / "agent-events"


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
        files = _PATCH_FILE_RE.findall(_redact(patch))
        # An unknown input shape claims no file: the row names the tool only.
        return ", ".join(f.strip() for f in files)[:PATH_HEAD_CHARS] or None
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
    detail = {k: _redact(v) if isinstance(v, str) else v for k, v in detail.items()}
    return {"event": event, "tool": tool, "head": head, "text": text, "detail": detail}


def spool_event(
    session_key: str, ts: str, row: Mapping[str, Any], *, spool_dir: Optional[Path] = None,
) -> bool:
    """Write one event to the spool: one file, no lock, no database.
    Returns whether it was written. Never raises: the hook must not fail
    on its log."""
    folder = Path(spool_dir) if spool_dir else default_spool_dir()
    spool_id = f"{time.time_ns():020d}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    body = json.dumps(
        {"spool_id": spool_id, "session_key": session_key, "ts": ts, "row": dict(row)},
        sort_keys=True, default=str,
    ).encode("utf-8")
    hidden = folder / f".{spool_id}.tmp"
    try:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(hidden, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, body)
        finally:
            os.close(fd)
        os.replace(hidden, folder / f"{spool_id}{_SPOOL_SUFFIX}")
        return True
    except OSError:
        return False


def drain_spool(
    connection: Callable[[], Any], *, spool_dir: Optional[Path] = None,
    keep: int = EVENT_LOG_KEEP, max_files: int = DRAIN_MAX_FILES,
) -> int:
    """Move spooled events into ``agent_session_events``; returns the files
    drained. ``connection`` is a context-manager factory that commits on a
    clean exit (``Database._connection``). One drainer at a time (a busy
    lock returns 0); a file goes only after the commit; a re-drain of the
    same file is ignored (``spool_id`` is unique). A missing table raises
    nothing and keeps every file. A file that is not an event is parked as
    ``.bad-<name>``, never read again."""
    import fcntl
    import sqlite3

    folder = Path(spool_dir) if spool_dir else default_spool_dir()
    if not folder.is_dir():
        return 0
    try:
        lock = open(folder / _LOCK_NAME, "a+")
    except OSError:
        return 0
    try:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return 0
        names = sorted(
            n for n in os.listdir(folder) if n.endswith(_SPOOL_SUFFIX) and not n.startswith(".")
        )[: max(1, int(max_files))]
        if not names:
            return 0
        entries: list[tuple[str, dict[str, Any]]] = []
        for name in names:
            try:
                doc = json.loads((folder / name).read_text(encoding="utf-8"))
                if not isinstance(doc, dict) or not doc.get("session_key") or not isinstance(doc.get("row"), dict):
                    raise ValueError("not an event")
            except (OSError, ValueError):
                try:
                    os.replace(folder / name, folder / f".bad-{name}")
                except OSError:
                    pass
                continue
            entries.append((name, doc))
        try:
            with connection() as conn:
                sessions: set[str] = set()
                for _, doc in entries:
                    row = doc["row"]
                    key = str(doc["session_key"])
                    sessions.add(key)
                    conn.execute(
                        "INSERT OR IGNORE INTO agent_session_events "
                        "(spool_id, session_key, ts, event, tool, head, text, detail_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            str(doc.get("spool_id") or ""), key, str(doc.get("ts") or ""),
                            str(row.get("event") or "unknown"), row.get("tool"), row.get("head"),
                            row.get("text"), json.dumps(dict(row.get("detail") or {}), sort_keys=True),
                        ),
                    )
                for key in sessions:
                    conn.execute(
                        "DELETE FROM agent_session_events WHERE session_key = ? AND id <= ("
                        "SELECT id FROM agent_session_events WHERE session_key = ? "
                        "ORDER BY id DESC LIMIT 1 OFFSET ?)",
                        (key, key, int(keep)),
                    )
        except sqlite3.OperationalError:
            return 0   # no table yet (the schema has not reconciled): keep the files
        for name, _ in entries:
            try:
                os.unlink(folder / name)
            except OSError:
                pass
        return len(entries)
    finally:
        lock.close()


class SpoolTimer:
    """The hub's timer leg of the drain (PHILO-14 C0b).

    The hub's ``_agent_spool_loop`` calls :meth:`tick` every
    :data:`INTERVAL` seconds (off the event loop). A tick drains only while a
    launch is live: ``live()`` (``agent_hand_service.live_launches``, a tmux
    probe per launch) is read again when the launch ledger file changes, and
    every :data:`LIVE_RECHECK` seconds while it says live (an agent whose
    tmux died leaves its ledger row as it was). With no live launch a tick is
    one ``stat`` of the ledger: no drain and no tmux probe.

    The drain is :func:`drain_spool` as the reads call it: the same
    ``flock``, so a drain in progress is never doubled (the second drainer
    gets 0), the same order and the same :data:`DRAIN_MAX_FILES` bound per
    pass. A failure is logged at most once per :data:`ERROR_LOG_EVERY`
    seconds and never raised."""

    INTERVAL = 2.0
    LIVE_RECHECK = 30.0
    ERROR_LOG_EVERY = 60.0

    def __init__(
        self,
        connection: Callable[[], Any],
        *,
        live: Callable[[], bool],
        ledger_path: Callable[[], Optional[Path]],
        spool_dir: Optional[Path] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._connection = connection
        self._live = live
        self._ledger_path = ledger_path
        self._spool_dir = spool_dir
        self._clock = clock
        self._mtime: Any = object()   # unseen: the first tick reads live()
        self._is_live = False
        self._checked = 0.0
        self._logged_at: Optional[float] = None
        self.failures = 0

    @property
    def is_live(self) -> bool:
        return self._is_live

    def _failed(self, what: str, exc: BaseException) -> None:
        self.failures += 1
        now = self._clock()
        if self._logged_at is None or now - self._logged_at >= self.ERROR_LOG_EVERY:
            self._logged_at = now
            log.warning(f"agent event spool timer: {what}: {exc}")

    def tick(self) -> int:
        """One timer pass; returns the files drained (0 when idle)."""
        now = self._clock()
        try:
            path = self._ledger_path()
            mtime = path.stat().st_mtime_ns if path is not None and path.exists() else None
        except Exception:
            mtime = None
        if mtime != self._mtime or (self._is_live and now - self._checked >= self.LIVE_RECHECK):
            self._mtime = mtime
            self._checked = now
            try:
                self._is_live = bool(self._live())
            except Exception as exc:
                self._failed("live launches not read", exc)
                self._is_live = True   # an empty drain is cheap: fail toward draining
        if not self._is_live:
            return 0
        try:
            return drain_spool(self._connection, spool_dir=self._spool_dir)
        except Exception as exc:
            self._failed("spool not drained", exc)
            return 0


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
    "SpoolTimer",
    "default_spool_dir",
    "drain_spool",
    "event_row",
    "list_events",
    "spool_event",
    "tool_head",
]
