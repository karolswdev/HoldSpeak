"""The hands that wait for a free agent (Betterment AG5).

At the "working at once" limit (``config.agents.working_at_once``), Launch
reads **Start when one is free**: the owner's press is stored here as a
queued hand, and the hub's heartbeat starts it when an agent is free
(``start_queued``). His press is the consent; the start runs the same
``AgentHandService.hand`` as a press on Launch.

The file is ``agent_hand_queue.json`` beside the launch ledger. Each entry:
``{queue_id, kind, id, instruction, profile, project_id, queued_at}``. An
entry leaves the file when its hand starts, when the start is refused, or
when he cancels it. Nothing here deletes a launch or a worktree.

HS-S31 (the shared queue outcome contract, D18/G31): an entry that leaves
keeps one retained terminal record in the same file (``outcomes``, the
newest ``OUTCOMES_KEPT``): ``{queue_id, source_ref, outcome, code,
launch_id, at}``. ``queue_outcome`` answers an entry's outcome from that
evidence only: ``waiting`` (the live row), ``launched``, ``failed`` (the
start was refused), ``cancelled``, or ``unknown`` (no row and no record:
an absent row is never proof that nothing ran). One queue id can have zero
to many consumers (direct hands, Automation occurrences); each reads the
same answer, and a read never starts, re-queues or repeats anything. The
first record of an id wins: a replay of the same id answers the same.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("agent_hand_queue")

QUEUE_SCHEMA = 1
QUEUED = "queued"
OUTCOMES_KEPT = 500
# The terminal outcomes a queue id can have (HS-S31).
WAITING, LAUNCHED, FAILED, CANCELLED, UNKNOWN = "waiting", "launched", "failed", "cancelled", "unknown"
_LOCK = threading.Lock()


def default_queue_path() -> Path:
    """Beside the launch ledger (a test that moves the ledger moves this too)."""
    from ..delivery import factory_launch

    return Path(factory_launch.DEFAULT_LAUNCHES_PATH).with_name("agent_hand_queue.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class HandQueue:
    """The queued hands, oldest first."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else default_queue_path()

    def _read_document(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return [], []
        if not isinstance(raw, dict):
            return [], []

        def rows_of(key: str) -> list[dict[str, Any]]:
            rows = raw.get(key)
            return [dict(row) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

        return rows_of("queue"), rows_of("outcomes")

    def _read(self) -> list[dict[str, Any]]:
        return self._read_document()[0]

    def _write(self, rows: list[dict[str, Any]], outcomes: Optional[list[dict[str, Any]]] = None) -> None:
        from ..delivery.factory_launch import _write_document

        if outcomes is None:
            outcomes = self._read_document()[1]
        _write_document(self._path, {"queue_schema": QUEUE_SCHEMA, "queue": rows,
                                     "outcomes": outcomes[-OUTCOMES_KEPT:]})

    def list(self) -> list[dict[str, Any]]:
        with _LOCK:
            return self._read()

    def add(
        self, kind: str, item_id: str, *, instruction: Optional[str] = None,
        profile: Optional[str] = None, project_id: Optional[str] = None,
        review_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """Queue one hand. An item already queued keeps its one entry."""
        with _LOCK:
            rows = self._read()
            for row in rows:
                if row.get("kind") == kind and row.get("id") == item_id:
                    return dict(row)
            entry = {
                "queue_id": "queue_" + uuid.uuid4().hex[:12],
                "kind": kind,
                "id": item_id,
                "instruction": instruction,
                "profile": profile,
                "project_id": project_id,
                "review_by": review_by,
                "queued_at": _now(),
            }
            rows.append(entry)
            self._write(rows)
            return dict(entry)

    def remove(
        self, queue_id: str, *, outcome: str = CANCELLED, code: Optional[str] = None,
        launch_id: Optional[str] = None,
    ) -> bool:
        """Take one entry out and retain its terminal record (HS-S31). A
        press on Cancel is ``cancelled``; ``start_queued`` records
        ``launched`` or ``failed``. False when no live entry has that id."""
        with _LOCK:
            rows, outcomes = self._read_document()
            gone = [row for row in rows if row.get("queue_id") == queue_id]
            if not gone:
                return False
            kept = [row for row in rows if row.get("queue_id") != queue_id]
            if not any(record.get("queue_id") == queue_id for record in outcomes):
                entry = gone[0]
                outcomes.append({
                    "queue_id": queue_id,
                    "source_ref": f"{entry.get('kind') or ''}:{entry.get('id') or ''}",
                    "outcome": outcome, "code": code, "launch_id": launch_id, "at": _now(),
                })
            self._write(kept, outcomes)
            return True

    def outcome(self, queue_id: str) -> dict[str, Any]:
        """HS-S31: this id's terminal outcome from retained evidence only.
        See ``queue_outcome``."""
        with _LOCK:
            rows, outcomes = self._read_document()
        live = next((row for row in rows if row.get("queue_id") == queue_id), None)
        if live is not None:
            return {"queue_id": queue_id, "outcome": WAITING,
                    "source_ref": f"{live.get('kind') or ''}:{live.get('id') or ''}",
                    "code": None, "launch_id": None, "at": live.get("queued_at")}
        record = next((row for row in outcomes if row.get("queue_id") == queue_id), None)
        if record is None:
            return {"queue_id": queue_id, "outcome": UNKNOWN, "source_ref": None, "code": None,
                    "launch_id": None, "at": None}
        word = str(record.get("outcome") or "")
        return {"queue_id": queue_id,
                "outcome": word if word in (LAUNCHED, FAILED, CANCELLED) else UNKNOWN,
                "source_ref": record.get("source_ref"), "code": record.get("code"),
                "launch_id": record.get("launch_id"), "at": record.get("at")}


def queue_outcome(queue_id: str, queue: Optional[HandQueue] = None) -> dict[str, Any]:
    """HS-S31, the shared queue outcome contract: one queue id's outcome,
    ``waiting`` / ``launched`` / ``failed`` / ``cancelled`` / ``unknown``,
    from retained evidence only (the live row, else the retained record).
    It never counts consumers, never starts, re-queues or repeats a hand;
    ``unknown`` (no row, no record, or an unreadable file) is never read as
    failed or as safe to hand again. ``launched`` is the queue's own end
    (the hand started); an Automation occurrence's Done stays its own."""
    return (queue or HandQueue()).outcome(str(queue_id or ""))


def queued_flights(db: Any, queue: Optional[HandQueue] = None) -> list[dict[str, Any]]:
    """Each queued hand in the flight shape (``state: queued``): the Agents
    list shows it as "Waits for a free agent"."""
    from ..delivery.factory_launch import agent_of_profile
    from .agent_flights import _project_of, _title_of

    out: list[dict[str, Any]] = []
    for entry in (queue or HandQueue()).list():
        kind, item_id = str(entry.get("kind") or ""), str(entry.get("id") or "")
        ref = f"{kind}:{item_id}"
        project_id, project_name = _project_of(db, kind, item_id)
        out.append({
            "origin_ref": ref, "kind": kind, "id": item_id,
            "title": _title_of(db, ref),
            "project_id": entry.get("project_id") or project_id,
            "project_name": project_name,
            "agent": agent_of_profile(entry.get("profile") or "claude-default"),
            "state": QUEUED,
            "queue_id": entry.get("queue_id"),
            "queued_at": entry.get("queued_at"),
            "turn_end": None, "turn_id": None, "done_at": None, "new": False, "session_key": None,
            "pr": None, "close": None, "session_cleanup": None, "merged_at": None,
            "launch_id": None, "launched_at": None, "ended_at": None,
        })
    return out


def start_queued(
    service: Any, *, queue: Optional[HandQueue] = None,
    principal: Any = None,
) -> list[dict[str, Any]]:
    """Start queued hands, oldest first, while an agent is free (the hub's
    heartbeat calls this). Returns what each start answered. A start the
    hand refuses (the item is gone, the worktree exists) leaves the queue
    with its reason logged; a full desk leaves the rest queued."""
    from ..principals import Principal, PrincipalKind

    queue = queue or HandQueue()
    principal = principal or Principal(PrincipalKind.OWNER, "owner-session")
    started: list[dict[str, Any]] = []
    for entry in queue.list():
        if not service.has_free_slot():
            break
        queue_id = str(entry.get("queue_id") or "")
        try:
            answer = service.hand(
                principal, str(entry.get("kind") or ""), str(entry.get("id") or ""),
                instruction=entry.get("instruction"), profile=entry.get("profile"),
                project_id=entry.get("project_id"),
                review_by=entry.get("review_by"),
            )
        except Exception as exc:
            code = getattr(exc, "code", None) or type(exc).__name__
            if code == "launch_cap_reached":
                break   # taken meanwhile: it stays queued
            log.warning(f"queued hand {queue_id} ({entry.get('kind')}:{entry.get('id')}) refused: {code}")
            queue.remove(queue_id, outcome=FAILED, code=str(code))
            started.append({"queue_id": queue_id, "status": "refused", "code": code})
            continue
        launch_id = answer.get("launch_id") if isinstance(answer, Mapping) else None
        queue.remove(queue_id, outcome=LAUNCHED, launch_id=str(launch_id) if launch_id else None)
        started.append({"queue_id": queue_id, **answer})
    return started


__all__ = [
    "CANCELLED", "FAILED", "HandQueue", "LAUNCHED", "QUEUED", "UNKNOWN", "WAITING", "default_queue_path",
    "queue_outcome", "queued_flights", "start_queued",
]
