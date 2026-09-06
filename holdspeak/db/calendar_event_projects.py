"""HS-175-02: Calendar event to Room (project) join table persistence.

The matcher writes links after each calendar refresh; the Door reads them
to project Room names onto upcoming event items.  Manual links are
written by the link/unlink routes and survive matcher re-runs.

Ruled R1 (2026-09-06, on the owner's deferral): a ``title`` link needs
the Room's FULL name as a contiguous whole-word phrase of the event
title, and a single generic word (``calendar_ingest_conductor.
GENERIC_MEETING_WORDS``) never links.  ``Unlink`` stays the remedy for a
wrong link; the suppression below is untouched by that ruling.

HS-175 counsel C5 / C6(c):

- An owner's ``unlink`` is durable.  It is recorded in
  ``calendar_event_link_suppressions`` keyed by the event's
  ``(source_id, uid)`` and the Room, and ``replace_auto_links`` never
  re-inserts a suppressed pair.  A later manual ``link`` clears the
  suppression (the owner's newer word wins).
- A manual link follows its event when the projection id regenerates
  (the id hashes ``starts_at``): the conductor snapshots manual links
  before a replace and ``rebind_manual_link`` moves them by ``(source_id, uid)``.
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


@dataclass(frozen=True)
class ManualLinkSnapshot:
    """A manual link captured before a projection replace (C6(c))."""

    calendar_event_id: str
    project_id: str
    uid: str
    starts_at: str


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
        """Insert or replace a link (upsert on the composite PK).

        A manual link also clears any suppression for the pair: the
        owner's newer word (link) outranks the older one (unlink).
        """
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_event_projects
                   (calendar_event_id, project_id, match_source)
                   VALUES (?, ?, ?)
                   ON CONFLICT(calendar_event_id, project_id) DO UPDATE SET
                       match_source = excluded.match_source""",
                (str(calendar_event_id), str(project_id), str(match_source)),
            )
            if str(match_source) == "manual":
                conn.execute(
                    """DELETE FROM calendar_event_link_suppressions
                       WHERE project_id = ?
                         AND (calendar_source_id, calendar_uid) IN (
                             SELECT source_id, uid FROM calendar_events WHERE id = ?
                         )""",
                    (str(project_id), str(calendar_event_id)),
                )

    def unlink(self, calendar_event_id: str, project_id: str) -> int:
        """Remove one link durably. Returns the number of live rows removed.

        C5: the pair is recorded in ``calendar_event_link_suppressions``
        (keyed by the event's source + uid) so the matcher never re-links
        it by title, and the suppression survives a time change.
        """
        with self._connection() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO calendar_event_link_suppressions
                   (calendar_source_id, calendar_uid, project_id)
                   SELECT source_id, uid, ? FROM calendar_events WHERE id = ?""",
                (str(project_id), str(calendar_event_id)),
            )
            cursor = conn.execute(
                """DELETE FROM calendar_event_projects
                   WHERE calendar_event_id = ? AND project_id = ?""",
                (str(calendar_event_id), str(project_id)),
            )
            return cursor.rowcount

    def unlink_event(self, calendar_event_id: str) -> int:
        """Remove all links for one event durably. Returns deleted count."""
        with self._connection() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO calendar_event_link_suppressions
                   (calendar_source_id, calendar_uid, project_id)
                   SELECT ce.source_id, ce.uid, cep.project_id
                   FROM calendar_event_projects cep
                   JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                   WHERE cep.calendar_event_id = ?""",
                (str(calendar_event_id),),
            )
            cursor = conn.execute(
                "DELETE FROM calendar_event_projects WHERE calendar_event_id = ?",
                (str(calendar_event_id),),
            )
            return cursor.rowcount

    def delete_link(self, calendar_event_id: str, project_id: str) -> int:
        """Delete one row WITHOUT recording a suppression (housekeeping only)."""
        with self._connection() as conn:
            cursor = conn.execute(
                """DELETE FROM calendar_event_projects
                   WHERE calendar_event_id = ? AND project_id = ?""",
                (str(calendar_event_id), str(project_id)),
            )
            return cursor.rowcount

    def list_suppressions(self) -> set[tuple[str, str, str]]:
        """Every durable unlink as ``(calendar_source_id, calendar_uid, project_id)``."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT calendar_source_id, calendar_uid, project_id "
                "FROM calendar_event_link_suppressions"
            ).fetchall()
        return {
            (str(r["calendar_source_id"]), str(r["calendar_uid"]), str(r["project_id"]))
            for r in rows
        }

    def is_suppressed(self, calendar_event_id: str, project_id: str) -> bool:
        """Whether the owner has durably unlinked this (event, Room) pair."""
        with self._connection() as conn:
            row = conn.execute(
                """SELECT 1 FROM calendar_event_link_suppressions s
                   JOIN calendar_events ce
                     ON ce.source_id = s.calendar_source_id AND ce.uid = s.calendar_uid
                   WHERE ce.id = ? AND s.project_id = ?
                   LIMIT 1""",
                (str(calendar_event_id), str(project_id)),
            ).fetchone()
        return row is not None

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

    def list_linked_event_ids(self) -> set[str]:
        """Every event id with at least one live Room link (any match_source)."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT calendar_event_id FROM calendar_event_projects"
            ).fetchall()
        return {str(r["calendar_event_id"]) for r in rows}

    def list_manual_for_source(self, source_id: str) -> list[ManualLinkSnapshot]:
        """Manual links on one source's events, with the uid + starts_at
        needed to rebind them after the projection is replaced (C6(c))."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT cep.calendar_event_id, cep.project_id, ce.uid, ce.starts_at
                   FROM calendar_event_projects cep
                   JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                   WHERE ce.source_id = ? AND cep.match_source = 'manual'""",
                (str(source_id),),
            ).fetchall()
        return [
            ManualLinkSnapshot(
                calendar_event_id=str(r["calendar_event_id"]),
                project_id=str(r["project_id"]),
                uid=str(r["uid"]),
                starts_at=str(r["starts_at"]),
            )
            for r in rows
        ]

    def rebind_manual_link(
        self, old_event_id: str, new_event_id: str, project_id: str,
    ) -> None:
        """Move a manual link from a dead projection id to its successor."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_event_projects
                   (calendar_event_id, project_id, match_source)
                   VALUES (?, ?, 'manual')
                   ON CONFLICT(calendar_event_id, project_id) DO UPDATE SET
                       match_source = 'manual'""",
                (str(new_event_id), str(project_id)),
            )
            conn.execute(
                """DELETE FROM calendar_event_projects
                   WHERE calendar_event_id = ? AND project_id = ?""",
                (str(old_event_id), str(project_id)),
            )

    def delete_orphans(self) -> int:
        """Drop links whose event no longer exists in the projection.

        Runs after every source has been refreshed and manual links
        rebound, so what remains orphaned is truly dead (a removed
        source, or a uid that left the feed).
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """DELETE FROM calendar_event_projects
                   WHERE calendar_event_id NOT IN (SELECT id FROM calendar_events)"""
            )
            return cursor.rowcount

    def replace_auto_links(
        self,
        links: list[tuple[str, str, str]],
    ) -> None:
        """Replace all non-manual links with the new matcher output.

        Manual links are preserved (they override the matcher).  A pair
        the owner unlinked (``calendar_event_link_suppressions``) is never
        re-inserted (C5).  Each tuple is
        (calendar_event_id, project_id, match_source).
        """
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM calendar_event_projects WHERE match_source != 'manual'"
            )
            suppressed = {
                (str(r["calendar_source_id"]), str(r["calendar_uid"]), str(r["project_id"]))
                for r in conn.execute(
                    "SELECT calendar_source_id, calendar_uid, project_id "
                    "FROM calendar_event_link_suppressions"
                ).fetchall()
            }
            event_keys: dict[str, tuple[str, str]] = {}
            if suppressed and links:
                for r in conn.execute(
                    "SELECT id, source_id, uid FROM calendar_events"
                ).fetchall():
                    event_keys[str(r["id"])] = (str(r["source_id"]), str(r["uid"]))
            for event_id, project_id, source in links:
                key = event_keys.get(str(event_id))
                if key is not None and (key[0], key[1], str(project_id)) in suppressed:
                    continue
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
