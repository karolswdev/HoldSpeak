"""HS-175-02: Calendar event to Room (project) join table persistence.

The matcher writes links after each calendar refresh; the Door reads them
to project Room names onto upcoming event items.  Manual links are
written by the link/unlink routes and survive matcher re-runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseRepository


@dataclass(frozen=True)
class CalendarEventProject:
    calendar_event_id: str
    project_id: str
    match_source: str  # "title" | "attendee" | "manual"
    created_at: str


def _row_to_model(row: Any) -> CalendarEventProject:
    return CalendarEventProject(
        calendar_event_id=str(row["calendar_event_id"]),
        project_id=str(row["project_id"]),
        match_source=str(row["match_source"]),
        created_at=str(row["created_at"]),
    )


class CalendarEventProjectRepository(BaseRepository):
    """Read/write authority for the calendar_event_projects join table."""

    table = "calendar_event_projects"

    def link(
        self,
        calendar_event_id: str,
        project_id: str,
        match_source: str = "title",
    ) -> None:
        """Insert or replace a link (upsert on the composite PK)."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_event_projects
                   (calendar_event_id, project_id, match_source)
                   VALUES (?, ?, ?)
                   ON CONFLICT(calendar_event_id, project_id) DO UPDATE SET
                       match_source = excluded.match_source""",
                (str(calendar_event_id), str(project_id), str(match_source)),
            )

    def unlink(self, calendar_event_id: str, project_id: str) -> int:
        """Remove one link. Returns the number of rows deleted (0 or 1)."""
        with self._connection() as conn:
            cursor = conn.execute(
                """DELETE FROM calendar_event_projects
                   WHERE calendar_event_id = ? AND project_id = ?""",
                (str(calendar_event_id), str(project_id)),
            )
            return cursor.rowcount

    def unlink_event(self, calendar_event_id: str) -> int:
        """Remove all links for one event. Returns deleted count."""
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM calendar_event_projects WHERE calendar_event_id = ?",
                (str(calendar_event_id),),
            )
            return cursor.rowcount

    def list_for_event(self, calendar_event_id: str) -> list[CalendarEventProject]:
        """All Room links for one event."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM calendar_event_projects WHERE calendar_event_id = ?",
                (str(calendar_event_id),),
            ).fetchall()
        return [_row_to_model(r) for r in rows]

    def list_for_project(self, project_id: str) -> list[CalendarEventProject]:
        """All event links for one Room."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM calendar_event_projects WHERE project_id = ?",
                (str(project_id),),
            ).fetchall()
        return [_row_to_model(r) for r in rows]

    def list_manual_event_ids(self) -> set[str]:
        """Return event ids that have a manual link (immune to matcher re-runs)."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT calendar_event_id FROM calendar_event_projects WHERE match_source = 'manual'",
            ).fetchall()
        return {str(r["calendar_event_id"]) for r in rows}

    def replace_auto_links(
        self,
        links: list[tuple[str, str, str]],
    ) -> None:
        """Replace all non-manual links with the new matcher output.

        Manual links are preserved (they override the matcher).
        Each tuple is (calendar_event_id, project_id, match_source).
        """
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM calendar_event_projects WHERE match_source != 'manual'"
            )
            for event_id, project_id, source in links:
                conn.execute(
                    """INSERT INTO calendar_event_projects
                       (calendar_event_id, project_id, match_source)
                       VALUES (?, ?, ?)
                       ON CONFLICT(calendar_event_id, project_id) DO NOTHING""",
                    (str(event_id), str(project_id), str(source)),
                )

    def build_event_project_index(self) -> dict[str, tuple[str, str]]:
        """Build a dict mapping event_id -> (project_id, project_name).

        Returns the FIRST match per event (manual > title > attendee by precedence).
        project_name is resolved via the projects table.
        """
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT cep.calendar_event_id, cep.project_id, cep.match_source,
                          p.name AS project_name
                   FROM calendar_event_projects cep
                   LEFT JOIN projects p ON p.id = cep.project_id
                   ORDER BY cep.calendar_event_id,
                            CASE cep.match_source
                                WHEN 'manual' THEN 0
                                WHEN 'title' THEN 1
                                WHEN 'attendee' THEN 2
                                ELSE 3
                            END""",
            ).fetchall()
        index: dict[str, tuple[str, str]] = {}
        for r in rows:
            eid = str(r["calendar_event_id"])
            if eid not in index:
                index[eid] = (str(r["project_id"]), str(r["project_name"] or ""))
        return index
