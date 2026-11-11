# PARKED: the retired Reaction executor has no live caller of these repository methods.
from __future__ import annotations

from typing import Any

class _ParkedBody:
    def list_enabled_legacy_watches(self) -> list[dict[str, Any]]:
        """Select enabled watches eligible for legacy refresh_due_watches.

        Excludes watches whose state is 'paused' or 'retired' (they must
        never evaluate on any timer) and watches whose project is archived
        (lifecycle = 'archived').  A watch with no project row is
        unaffected (LEFT JOIN).  Archive predicate reuses the shape from
        list_due_watches (HS-167 M-2).
        """
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT cw.* FROM connector_watches cw
                   LEFT JOIN projects p ON cw.project_id = p.id
                   WHERE cw.enabled = 1
                     AND cw.state NOT IN ('paused', 'retired')
                     AND (cw.project_id = '' OR cw.project_id IS NULL
                          OR p.lifecycle IS NULL
                          OR p.lifecycle != 'archived')
                   ORDER BY cw.created_at, cw.id""",
            ).fetchall()
        return [self._payload(row, "query", "snapshot") for row in rows]

    def set_reaction_enabled(self, reaction_id: str, enabled: bool) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE connector_reactions SET enabled=?,updated_at=datetime('now') WHERE id=?",
                (int(enabled), reaction_id),
            )
        return bool(cur.rowcount)

    def matching_reactions(self, watch_id: str | None, event_type: str) -> list[dict[str, Any]]:
        rows = self.list_reactions()
        return [row for row in rows if row["enabled"] and
                (not row["watch_id"] or row["watch_id"] == watch_id) and
                (row["event_pattern"] == event_type or
                 (row["event_pattern"].endswith(".*") and
                  event_type.startswith(row["event_pattern"][:-1])))]

    def has_projection(self, reaction_id: str, event_id: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM reaction_event_projections WHERE reaction_id=? AND event_id=?",
                (reaction_id, event_id),
            ).fetchone()
        return row is not None

    def record_projection(self, reaction_id: str, event_id: str, *, item_id: str,
                          operation_id: str | None = None,
                          receipt_id: str | None = None) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                """INSERT OR IGNORE INTO reaction_event_projections
                   (reaction_id,event_id,item_id,operation_id,receipt_id)
                   VALUES (?,?,?,?,?)""",
                (reaction_id, event_id, item_id, operation_id, receipt_id),
            )
        return bool(cur.rowcount)

    def list_reaction_projections(self, reaction_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return durable Reaction deliveries joined to their source events."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT p.reaction_id,p.event_id,p.item_id,p.operation_id,p.receipt_id,p.projected_at,
                          e.event_type,e.subject_ref,e.source_revision,e.facts_json,e.refs_json,
                          e.correlation_id,e.causation_id,e.created_at AS event_created_at
                   FROM reaction_event_projections p
                   JOIN service_events e ON e.id=p.event_id
                   WHERE p.reaction_id=?
                   ORDER BY p.projected_at DESC,p.event_id DESC LIMIT ?""",
                (reaction_id, max(1, min(int(limit), 500))),
            ).fetchall()
        return [self._payload(row, "facts", "refs") for row in rows]
