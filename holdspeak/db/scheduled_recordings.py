"""Scheduled recording persistence (HS-136-01).

CRUD + state-machine transitions for owner-scheduled cron-driven captures.
"""
from __future__ import annotations

import uuid
import time
from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseRepository


@dataclass
class ScheduledRecording:
    id: str
    title: str
    cron_expr: str
    tz: str
    one_shot: bool
    duration_minutes: int
    enabled: bool
    revision: int
    created_at: float
    last_fired_at: Optional[float]
    next_fire_at: Optional[float]
    armed_at: Optional[float]
    deadline_at: Optional[float]
    state: str
    last_outcome: str
    last_receipt_id: str
    delegation_receipt_id: str
    calendar_event_id: str
    calendar_uid: str
    calendar_source_id: str


def _row_to_model(row: Any) -> ScheduledRecording:
    return ScheduledRecording(
        id=str(row["id"]),
        title=str(row["title"]),
        cron_expr=str(row["cron_expr"]),
        tz=str(row["tz"] or "UTC"),
        one_shot=bool(row["one_shot"]),
        duration_minutes=int(row["duration_minutes"]),
        enabled=bool(row["enabled"]),
        revision=int(row["revision"]),
        created_at=float(row["created_at"]),
        last_fired_at=float(row["last_fired_at"]) if row["last_fired_at"] is not None else None,
        next_fire_at=float(row["next_fire_at"]) if row["next_fire_at"] is not None else None,
        armed_at=float(row["armed_at"]) if row["armed_at"] is not None else None,
        deadline_at=float(row["deadline_at"]) if row["deadline_at"] is not None else None,
        state=str(row["state"]),
        last_outcome=str(row["last_outcome"] or ""),
        last_receipt_id=str(row["last_receipt_id"] or ""),
        delegation_receipt_id=str(row["delegation_receipt_id"] or ""),
        calendar_event_id=str(row["calendar_event_id"] or ""),
        calendar_uid=str(row["calendar_uid"] or ""),
        calendar_source_id=str(row["calendar_source_id"] or ""),
    )


class ScheduledRecordingRepository(BaseRepository):
    table = "scheduled_recordings"

    def create(
        self,
        *,
        title: str,
        cron_expr: str,
        tz: str = "UTC",
        one_shot: bool = False,
        duration_minutes: int = 60,
        enabled: bool = False,
        next_fire_at: Optional[float] = None,
        delegation_receipt_id: str = "",
        calendar_event_id: str = "",
        calendar_uid: str = "",
        calendar_source_id: str = "",
    ) -> ScheduledRecording:
        rec_id = f"sr_{uuid.uuid4().hex[:12]}"
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO scheduled_recordings
                   (id, title, cron_expr, tz, one_shot, duration_minutes, enabled,
                    revision, created_at, next_fire_at, state,
                    delegation_receipt_id,
                    calendar_event_id, calendar_uid, calendar_source_id)
                   VALUES (?,?,?,?,?,?,?,1,?,?,'idle',?,?,?,?)""",
                (
                    rec_id,
                    str(title or "").strip(),
                    str(cron_expr).strip(),
                    str(tz or "UTC").strip(),
                    int(bool(one_shot)),
                    max(1, int(duration_minutes)),
                    int(bool(enabled)),
                    now,
                    next_fire_at,
                    delegation_receipt_id,
                    str(calendar_event_id or ""),
                    str(calendar_uid or ""),
                    str(calendar_source_id or ""),
                ),
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?", (rec_id,)
            ).fetchone()
        return _row_to_model(row)

    def get(self, rec_id: str) -> Optional[ScheduledRecording]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    def list_enabled(self) -> list[ScheduledRecording]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE enabled=1 ORDER BY next_fire_at"
            ).fetchall()
        return [_row_to_model(r) for r in rows]

    def list_all(self) -> list[ScheduledRecording]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_recordings ORDER BY created_at DESC"
            ).fetchall()
        return [_row_to_model(r) for r in rows]

    def update(
        self,
        rec_id: str,
        *,
        title: Optional[str] = None,
        cron_expr: Optional[str] = None,
        tz: Optional[str] = None,
        one_shot: Optional[bool] = None,
        duration_minutes: Optional[int] = None,
        enabled: Optional[bool] = None,
        next_fire_at: object = ...,
        delegation_receipt_id: Optional[str] = None,
    ) -> Optional[ScheduledRecording]:
        sets: list[str] = []
        params: list[Any] = []
        bump_revision = False
        if title is not None:
            sets.append("title=?")
            params.append(str(title).strip())
        if cron_expr is not None:
            sets.append("cron_expr=?")
            params.append(str(cron_expr).strip())
            bump_revision = True
        if tz is not None:
            sets.append("tz=?")
            params.append(str(tz).strip())
            bump_revision = True
        if one_shot is not None:
            sets.append("one_shot=?")
            params.append(int(bool(one_shot)))
            bump_revision = True
        if duration_minutes is not None:
            sets.append("duration_minutes=?")
            params.append(max(1, int(duration_minutes)))
            bump_revision = True
        if enabled is not None:
            sets.append("enabled=?")
            params.append(int(bool(enabled)))
        if next_fire_at is not ...:
            sets.append("next_fire_at=?")
            params.append(next_fire_at)
        if delegation_receipt_id is not None:
            sets.append("delegation_receipt_id=?")
            params.append(delegation_receipt_id)
        if bump_revision:
            sets.append("revision=revision+1")
        if not sets:
            return self.get(rec_id)
        params.append(str(rec_id))
        with self._connection() as conn:
            conn.execute(
                f"UPDATE scheduled_recordings SET {','.join(sets)} WHERE id=?",
                params,
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    def set_state(
        self,
        rec_id: str,
        state: str,
        *,
        last_fired_at: Optional[float] = None,
        next_fire_at: object = ...,
        last_outcome: Optional[str] = None,
        last_receipt_id: Optional[str] = None,
        enabled: Optional[bool] = None,
        armed_at: object = ...,
        deadline_at: object = ...,
    ) -> Optional[ScheduledRecording]:
        sets = ["state=?"]
        params: list[Any] = [state]
        if last_fired_at is not None:
            sets.append("last_fired_at=?")
            params.append(last_fired_at)
        if next_fire_at is not ...:
            sets.append("next_fire_at=?")
            params.append(next_fire_at)
        if last_outcome is not None:
            sets.append("last_outcome=?")
            params.append(last_outcome)
        if last_receipt_id is not None:
            sets.append("last_receipt_id=?")
            params.append(last_receipt_id)
        if enabled is not None:
            sets.append("enabled=?")
            params.append(int(bool(enabled)))
        if armed_at is not ...:
            sets.append("armed_at=?")
            params.append(armed_at)
        if deadline_at is not ...:
            sets.append("deadline_at=?")
            params.append(deadline_at)
        params.append(str(rec_id))
        with self._connection() as conn:
            conn.execute(
                f"UPDATE scheduled_recordings SET {','.join(sets)} WHERE id=?",
                params,
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    # ── HS-147-03: narrow reconciliation helpers ────────────────────

    def list_linked_for_source(self, source_id: str) -> list[ScheduledRecording]:
        """Return enabled, idle schedules linked to a calendar source (D3a).

        Only rows with state='idle' are eligible for reconciliation; arming
        and recording rows are excluded by X1.
        """
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM scheduled_recordings
                   WHERE calendar_source_id = ?
                     AND enabled = 1
                     AND state = 'idle'
                     AND calendar_event_id != ''""",
                (str(source_id),),
            ).fetchall()
        return [_row_to_model(r) for r in rows]

    def rebind_event(
        self,
        rec_id: str,
        *,
        calendar_event_id: str,
        next_fire_at: Optional[float],
        duration_minutes: int,
        title: str,
    ) -> Optional[ScheduledRecording]:
        """Rebind a schedule to a new event occurrence (R2).

        Updates the projection id, fire time, duration, and title in one
        atomic statement.  Returns None if the row vanished between query
        and update (conductor interleave -- harmless).
        """
        with self._connection() as conn:
            conn.execute(
                """UPDATE scheduled_recordings
                   SET calendar_event_id = ?,
                       next_fire_at = ?,
                       duration_minutes = ?,
                       title = ?
                   WHERE id = ?""",
                (
                    str(calendar_event_id),
                    next_fire_at,
                    max(1, int(duration_minutes)),
                    str(title or "").strip(),
                    str(rec_id),
                ),
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    def refresh_in_place(
        self,
        rec_id: str,
        *,
        duration_minutes: int,
        title: str,
    ) -> Optional[ScheduledRecording]:
        """Refresh duration and title in place (R1).

        The projection id is unchanged (starts_at did not move).
        """
        with self._connection() as conn:
            conn.execute(
                """UPDATE scheduled_recordings
                   SET duration_minutes = ?,
                       title = ?
                   WHERE id = ?""",
                (
                    max(1, int(duration_minutes)),
                    str(title or "").strip(),
                    str(rec_id),
                ),
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    def cancel_for_event_removed(self, rec_id: str) -> Optional[ScheduledRecording]:
        """Cancel a schedule whose linked event was removed from the feed (R3).

        Sets state='cancelled', last_outcome='event_removed', enabled=0,
        next_fire_at=NULL.  Uses only existing state vocabulary.
        """
        with self._connection() as conn:
            conn.execute(
                """UPDATE scheduled_recordings
                   SET state = 'cancelled',
                       last_outcome = 'event_removed',
                       enabled = 0,
                       next_fire_at = NULL
                   WHERE id = ?""",
                (str(rec_id),),
            )
            row = conn.execute(
                "SELECT * FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            ).fetchone()
        return _row_to_model(row) if row else None

    def delete(self, rec_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM scheduled_recordings WHERE id=?",
                (str(rec_id),),
            )
            return bool(cursor.rowcount)
