"""Calendar event projection persistence (HS-144-02, HS-146-01 multi-source).

The ICS source is authoritative.  Callers replace a complete parsed projection;
they cannot patch individual calendar rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Protocol, Sequence

from .base import BaseRepository


class CalendarEventProjection(Protocol):
    """The bounded parser output required to persist one occurrence."""

    id: str
    uid: str
    title: str
    starts_at: str
    ends_at: str
    location: Optional[str]
    meeting_url: Optional[str]


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    uid: str
    title: str
    starts_at: str
    ends_at: str
    location: Optional[str]
    meeting_url: Optional[str]
    last_seen_at: float
    subscription_revision: str
    source_id: str = ""
    source_label: str = ""


def _row_to_model(row: Any) -> CalendarEvent:
    return CalendarEvent(
        id=str(row["id"]),
        uid=str(row["uid"]),
        title=str(row["title"] or ""),
        starts_at=str(row["starts_at"]),
        ends_at=str(row["ends_at"]),
        location=str(row["location"]) if row["location"] is not None else None,
        meeting_url=str(row["meeting_url"]) if row["meeting_url"] is not None else None,
        last_seen_at=float(row["last_seen_at"]),
        subscription_revision=str(row["subscription_revision"]),
        source_id=str(row["source_id"]) if "source_id" in row.keys() else "",
        source_label=str(row["source_label"]) if "source_label" in row.keys() else "",
    )


class CalendarEventRepository(BaseRepository):
    """Read/replacement authority for calendar sources."""

    table = "calendar_events"

    def replace_projection(
        self,
        subscription_revision: str,
        events: Iterable[CalendarEventProjection],
        *,
        seen_at: float,
        source_id: str = "",
        source_label: str = "",
    ) -> None:
        """Atomically replace the projection for one source.

        When ``source_id`` is set (multi-source mode), only that source's
        rows are deleted before inserting.  When empty (legacy single-source
        callers), all rows are deleted -- preserving the old behaviour.
        """
        revision = str(subscription_revision)
        sid = str(source_id)
        slabel = str(source_label)
        desired = tuple(events)
        with self._connection() as conn:
            # The source owns its whole projection. Clear its old/current rows
            # in the transaction before inserting the complete desired set,
            # rather than depending on a clock value being unique across
            # refreshes. A transaction rollback restores the prior working
            # projection if any insert fails.
            if sid:
                conn.execute(
                    "DELETE FROM calendar_events WHERE source_id = ?", (sid,)
                )
            else:
                conn.execute("DELETE FROM calendar_events")
            for event in desired:
                conn.execute(
                    """INSERT INTO calendar_events
                       (id, uid, title, starts_at, ends_at, location, meeting_url,
                        last_seen_at, subscription_revision, source_id, source_label)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           uid=excluded.uid,
                           title=excluded.title,
                           starts_at=excluded.starts_at,
                           ends_at=excluded.ends_at,
                           location=excluded.location,
                           meeting_url=excluded.meeting_url,
                           last_seen_at=excluded.last_seen_at,
                           subscription_revision=excluded.subscription_revision,
                           source_id=excluded.source_id,
                           source_label=excluded.source_label""",
                    (
                        str(event.id),
                        str(event.uid),
                        str(event.title or ""),
                        str(event.starts_at),
                        str(event.ends_at),
                        str(event.location) if event.location is not None else None,
                        str(event.meeting_url) if event.meeting_url is not None else None,
                        float(seen_at),
                        revision,
                        sid,
                        slabel,
                    ),
                )

    def delete_sources_not_in(self, enabled_ids: Sequence[str]) -> int:
        """Remove rows whose source_id is not in the enabled set.

        Returns the number of deleted rows.  Called by the conductor after
        all enabled sources have been refreshed so that disabled/removed
        sources' projections are cleaned up.
        """
        if not enabled_ids:
            with self._connection() as conn:
                cursor = conn.execute("DELETE FROM calendar_events")
                return cursor.rowcount
        placeholders = ", ".join("?" for _ in enabled_ids)
        with self._connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM calendar_events WHERE source_id NOT IN ({placeholders})",
                tuple(str(sid) for sid in enabled_ids),
            )
            return cursor.rowcount

    def list_upcoming(self, now_iso: str) -> list[CalendarEvent]:
        """Return future projected occurrences in the Door's chronological order."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM calendar_events
                   WHERE starts_at >= ?
                   ORDER BY starts_at, id""",
                (str(now_iso),),
            ).fetchall()
        return [_row_to_model(row) for row in rows]

    def list_all(self) -> list[CalendarEvent]:
        """Small read helper for projection integrity tests and conductor checks."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM calendar_events ORDER BY starts_at, id"
            ).fetchall()
        return [_row_to_model(row) for row in rows]
