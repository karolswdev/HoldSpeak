"""Calendar event projection persistence (HS-144-02).

The ICS source is authoritative.  Callers replace a complete parsed projection;
they cannot patch individual calendar rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Protocol

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
    )


class CalendarEventRepository(BaseRepository):
    """Read/replacement authority for the one configured calendar source."""

    table = "calendar_events"

    def replace_projection(
        self,
        subscription_revision: str,
        events: Iterable[CalendarEventProjection],
        *,
        seen_at: float,
    ) -> None:
        """Atomically replace the projection for the configured source.

        Old-source rows disappear before the new desired set is upserted, and
        current-source rows absent from this successful parse disappear in the
        same transaction.  A caller must not invoke this after a feed-level
        failure; that policy lives at the ingest boundary.
        """
        revision = str(subscription_revision)
        desired = tuple(events)
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM calendar_events WHERE subscription_revision != ?",
                (revision,),
            )
            for event in desired:
                conn.execute(
                    """INSERT INTO calendar_events
                       (id, uid, title, starts_at, ends_at, location, meeting_url,
                        last_seen_at, subscription_revision)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           uid=excluded.uid,
                           title=excluded.title,
                           starts_at=excluded.starts_at,
                           ends_at=excluded.ends_at,
                           location=excluded.location,
                           meeting_url=excluded.meeting_url,
                           last_seen_at=excluded.last_seen_at,
                           subscription_revision=excluded.subscription_revision""",
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
                    ),
                )
            conn.execute(
                "DELETE FROM calendar_events "
                "WHERE subscription_revision = ? AND last_seen_at != ?",
                (revision, float(seen_at)),
            )

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
