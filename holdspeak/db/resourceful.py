"""Persistence for intrinsic resourceful-when-idle policies."""
from __future__ import annotations

import json
from typing import Any

from .base import BaseRepository


class ResourcefulRepository(BaseRepository):
    table = "resourceful_policies"

    @staticmethod
    def _policy(row: Any) -> dict[str, Any]:
        value = dict(row)
        try:
            value["routines"] = json.loads(value.pop("routines_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            value["routines"] = []
        value["enabled"] = bool(value["enabled"])
        value["night_only"] = bool(value["night_only"])
        return value

    def get(self, workbench_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM resourceful_policies WHERE workbench_id=?",
                (workbench_id,),
            ).fetchone()
        return self._policy(row) if row else None

    def list_enabled(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM resourceful_policies WHERE enabled=1 ORDER BY workbench_id"
            ).fetchall()
        return [self._policy(row) for row in rows]

    def upsert(
        self,
        *,
        workbench_id: str,
        enabled: bool,
        idle_after_minutes: int = 30,
        cooldown_hours: int = 6,
        nightly_target: int = 2,
        night_only: bool = True,
        night_start_hour: int = 22,
        night_end_hour: int = 7,
        routines: list[str] | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO resourceful_policies
                   (workbench_id,enabled,idle_after_minutes,cooldown_hours,
                    nightly_target,night_only,night_start_hour,night_end_hour,routines_json)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(workbench_id) DO UPDATE SET
                     enabled=excluded.enabled,
                     idle_after_minutes=excluded.idle_after_minutes,
                     cooldown_hours=excluded.cooldown_hours,
                     nightly_target=excluded.nightly_target,
                     night_only=excluded.night_only,
                     night_start_hour=excluded.night_start_hour,
                     night_end_hour=excluded.night_end_hour,
                     routines_json=excluded.routines_json,
                     idle_since=CASE WHEN excluded.enabled=0 THEN NULL ELSE idle_since END,
                     updated_at=datetime('now')""",
                (
                    workbench_id,
                    int(enabled),
                    int(idle_after_minutes),
                    int(cooldown_hours),
                    int(nightly_target),
                    int(night_only),
                    int(night_start_hour),
                    int(night_end_hour),
                    json.dumps(routines or ["loose_ideas", "failed_work"]),
                ),
            )
        return self.get(workbench_id) or {}

    def begin_idle(self, workbench_id: str, *, idle_since: str) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """UPDATE resourceful_policies
                   SET idle_since=?,idle_epoch=idle_epoch+1,last_outcome='idle',
                       last_error=NULL,updated_at=datetime('now')
                   WHERE workbench_id=? AND idle_since IS NULL""",
                (idle_since, workbench_id),
            )
        return self.get(workbench_id) or {}

    def mark_busy(self, workbench_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                """UPDATE resourceful_policies
                   SET idle_since=NULL,last_outcome='busy',updated_at=datetime('now')
                   WHERE workbench_id=?""",
                (workbench_id,),
            )

    def mark_checked(
        self,
        workbench_id: str,
        *,
        at: str,
        night_key: str,
        outcome: str,
        fired: bool = False,
        error: str | None = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """UPDATE resourceful_policies SET
                     last_checked_at=?,
                     last_fired_at=CASE WHEN ? THEN ? ELSE last_fired_at END,
                     night_key=?,
                     nightly_count=CASE
                       WHEN night_key != ? THEN CASE WHEN ? THEN 1 ELSE 0 END
                       WHEN ? THEN nightly_count+1 ELSE nightly_count END,
                     last_outcome=?,last_error=?,updated_at=datetime('now')
                   WHERE workbench_id=?""",
                (
                    at,
                    int(fired),
                    at,
                    night_key,
                    night_key,
                    int(fired),
                    int(fired),
                    outcome,
                    error[:1000] if error else None,
                    workbench_id,
                ),
            )

    def was_dispatched(self, workbench_id: str, candidate_key: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                """SELECT 1 FROM resourceful_dispatches
                   WHERE workbench_id=? AND candidate_key=?""",
                (workbench_id, candidate_key),
            ).fetchone()
        return row is not None

    def record_dispatch(
        self,
        *,
        workbench_id: str,
        candidate_key: str,
        routine: str,
        source_ref: str,
        event_id: str,
        item_id: str,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO resourceful_dispatches
                   (workbench_id,candidate_key,routine,source_ref,event_id,item_id)
                   VALUES (?,?,?,?,?,?)""",
                (workbench_id, candidate_key, routine, source_ref, event_id, item_id),
            )

    def complete_dispatch(
        self,
        workbench_id: str,
        candidate_key: str,
        *,
        outcome: str,
        operation_id: str | None = None,
        receipt_id: str | None = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """UPDATE resourceful_dispatches
                   SET outcome=?,operation_id=?,receipt_id=?,completed_at=datetime('now')
                   WHERE workbench_id=? AND candidate_key=?""",
                (outcome, operation_id, receipt_id, workbench_id, candidate_key),
            )

    def list_dispatches(self, workbench_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM resourceful_dispatches WHERE workbench_id=?
                   ORDER BY created_at DESC,candidate_key DESC LIMIT ?""",
                (workbench_id, max(1, min(int(limit), 200))),
            ).fetchall()
        return [dict(row) for row in rows]
