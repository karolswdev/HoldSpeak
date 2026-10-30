"""Programs PG21: the last usage-limit stop of each harness, read on this desk.

The screen watcher (:func:`screen_watch.tick`) reads each agent's pane; when
the pane shows a usage-limit stop (:func:`usage_limit.read_limit`, not a
share warning) this module keeps one row per harness in
``agent_limit_stops``: when the stop was first seen, the notice in its shape
(:func:`usage_limit.notice_shape`) and the reset it named. The same stop on
the next 2 s read keeps its first time.

The Engines read (:func:`notice_wire`, on each Claude Code and Codex engine
row of ``/api/concierge/detect``) says ``verified`` when a row exists, else
``documented`` with the documented line (:data:`usage_limit.DOCUMENTED`).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..logging_config import get_logger
from .usage_limit import DOCUMENTED, LimitReading, notice_shape

log = get_logger("agent_context.limit_stops")


def _iso(moment: Optional[datetime]) -> Optional[str]:
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def record(db: Any, harness: str, reading: LimitReading, now: datetime) -> bool:
    """Keep ``reading`` as ``harness``'s last stop. Returns True when it is a
    new stop (another notice or another reset than the row holds)."""
    key = str(harness or "").lower()
    if db is None or key not in DOCUMENTED or not reading.stopped:
        return False
    shape, resets = notice_shape(reading.line), _iso(reading.until)
    try:
        with db._connection() as conn:
            old = conn.execute(
                "SELECT notice, resets_at FROM agent_limit_stops WHERE harness = ?", (key,),
            ).fetchone()
            if old is not None and (old["notice"], old["resets_at"]) == (shape, resets):
                return False
            conn.execute(
                "INSERT INTO agent_limit_stops (harness, stopped_at, notice, resets_at, rule)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(harness) DO UPDATE SET stopped_at = excluded.stopped_at,"
                " notice = excluded.notice, resets_at = excluded.resets_at, rule = excluded.rule",
                (key, _iso(now), shape, resets, reading.rule),
            )
    except Exception as exc:
        log.info(f"usage-limit stop not kept: {exc}")
        return False
    return True


def notice_wire(db: Any, harness: str) -> Optional[dict[str, Any]]:
    """The Engines fact for one harness: ``verified`` with the last stop and
    its reset, or ``documented`` with the documented line; ``None`` for a
    harness whose notice is not read."""
    key = str(harness or "").lower()
    if key not in DOCUMENTED:
        return None
    row = None
    if db is not None:
        try:
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT stopped_at, notice, resets_at FROM agent_limit_stops WHERE harness = ?", (key,),
                ).fetchone()
        except Exception as exc:
            log.info(f"usage-limit stops not read: {exc}")
    if row is None:
        return {"verified": False, "notice": DOCUMENTED[key], "stoppedAt": None, "resetsAt": None}
    return {"verified": True, "notice": row["notice"], "stoppedAt": row["stopped_at"], "resetsAt": row["resets_at"]}


__all__ = ["notice_wire", "record"]
