"""Windowed, persistent generation model for the Monday Brief."""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service


_SECTIONS = ("changed", "broke", "waiting", "decisions")
_CLOSE_HOUR = 17


@dataclass
class BriefItem:
    id: str
    section: str  # changed, broke, waiting, decisions
    text: str
    detail: str | None = None
    source_ref: str | None = None
    priority: int = 0


@dataclass
class MondayBrief:
    id: str
    period_start: str
    period_end: str
    headline: str
    sections: dict[str, list[BriefItem]]
    generated_at: str
    is_empty: bool = False


@observe_service
class MondayBriefService:
    """Create one durable brief per local calendar day.

    The supplied datetime's timezone (when it has one) is retained while
    calculating the local 17:00 close. Naive datetimes retain the application's
    existing local-time convention.
    """

    def __init__(self, db: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def compute_window(
        self, now: datetime.datetime | None = None
    ) -> tuple[datetime.datetime, datetime.datetime]:
        """Compute the local brief window, from the preceding close to *now*."""
        period_end = now or datetime.datetime.now()
        weekday = period_end.weekday()
        if weekday == 0:  # Monday starts from the preceding Friday close.
            days_back = 3
        elif weekday < 5:  # Tuesday through Friday starts yesterday.
            days_back = 1
        else:  # Weekend briefs continue from Friday close.
            days_back = weekday - 4

        start_date = (period_end - datetime.timedelta(days=days_back)).date()
        period_start = datetime.datetime.combine(
            start_date,
            datetime.time(hour=_CLOSE_HOUR),
            tzinfo=period_end.tzinfo,
        )
        return period_start, period_end

    def generate(
        self, principal: Any, *, now: datetime.datetime | None = None
    ) -> MondayBrief:
        """Generate or return the existing brief for the current local date."""
        del principal
        period_start, period_end = self.compute_window(now)
        date_key = period_end.date().isoformat()

        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT * FROM monday_briefs
                   WHERE substr(period_end, 1, 10) = ?
                   ORDER BY generated_at DESC, id DESC LIMIT 1""",
                (date_key,),
            ).fetchone()
            if row is not None:
                return self._load_brief(conn, row)

            brief_id = f"brief-{uuid.uuid4().hex}"
            generated_at = period_end.isoformat()
            conn.execute(
                """INSERT INTO monday_briefs
                   (id, period_start, period_end, headline, generated_at)
                   VALUES (?, ?, ?, '', ?)""",
                (brief_id, period_start.isoformat(), period_end.isoformat(), generated_at),
            )
            row = conn.execute(
                "SELECT * FROM monday_briefs WHERE id = ?", (brief_id,)
            ).fetchone()
            assert row is not None
            return self._load_brief(conn, row)

    def get_latest(self, principal: Any) -> MondayBrief | None:
        """Return the most recently generated brief, if one exists."""
        del principal
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM monday_briefs ORDER BY generated_at DESC, id DESC LIMIT 1"
            ).fetchone()
            return self._load_brief(conn, row) if row is not None else None

    @staticmethod
    def _load_brief(conn: Any, row: Any) -> MondayBrief:
        sections: dict[str, list[BriefItem]] = {section: [] for section in _SECTIONS}
        for item in conn.execute(
            """SELECT id, section, text, detail, source_ref, priority
               FROM monday_brief_items WHERE brief_id = ?
               ORDER BY priority DESC, id ASC""",
            (row["id"],),
        ):
            section = str(item["section"])
            sections.setdefault(section, []).append(
                BriefItem(
                    id=str(item["id"]),
                    section=section,
                    text=str(item["text"]),
                    detail=item["detail"],
                    source_ref=item["source_ref"],
                    priority=int(item["priority"]),
                )
            )
        return MondayBrief(
            id=str(row["id"]),
            period_start=str(row["period_start"]),
            period_end=str(row["period_end"]),
            headline=str(row["headline"]),
            sections=sections,
            generated_at=str(row["generated_at"]),
            is_empty=not any(sections.values()),
        )
