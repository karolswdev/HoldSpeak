"""Persistence for Watches, the typed service-event ledger, and Reactions."""
from __future__ import annotations

import json
from typing import Any

from .base import BaseRepository


class AutomationRepository(BaseRepository):
    table = "automations"

    @staticmethod
    def _payload(row: Any, *json_fields: str) -> dict[str, Any]:
        value = dict(row)
        for field in json_fields:
            raw = value.pop(f"{field}_json", None)
            try:
                value[field] = json.loads(raw) if raw else {}
            except (TypeError, json.JSONDecodeError):
                value[field] = {}
        for field in ("enabled", "auto_run"):
            if field in value:
                value[field] = bool(value[field])
        return value

    def create_watch(self, *, watch_id: str, connector_id: str, query_kind: str,
                     name: str, query: dict[str, Any], enabled: bool) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id,connector_id,query_kind,name,query_json,enabled)
                   VALUES (?,?,?,?,?,?)""",
                (watch_id, connector_id, query_kind, name,
                 json.dumps(query, sort_keys=True, separators=(",", ":")), int(enabled)),
            )
        return self.get_watch(watch_id) or {}

    def get_watch(self, watch_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM connector_watches WHERE id=?", (watch_id,)).fetchone()
        return self._payload(row, "query", "snapshot") if row else None

    def list_watches(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM connector_watches ORDER BY created_at,id").fetchall()
        return [self._payload(row, "query", "snapshot") for row in rows]

    def set_watch_enabled(self, watch_id: str, enabled: bool) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE connector_watches SET enabled=?,updated_at=datetime('now') WHERE id=?",
                (int(enabled), watch_id),
            )
        return bool(cur.rowcount)

    def record_refresh(self, watch_id: str, snapshot: dict[str, Any], events: list[dict[str, Any]]) -> None:
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for event in events:
                self._insert_event(conn, event)
            conn.execute(
                """UPDATE connector_watches SET snapshot_json=?,last_success_at=datetime('now'),
                   last_error=NULL,updated_at=datetime('now') WHERE id=?""",
                (json.dumps(snapshot, sort_keys=True, separators=(",", ":")), watch_id),
            )

    @staticmethod
    def _insert_event(conn: Any, event: dict[str, Any]) -> bool:
        cur = conn.execute(
            """INSERT OR IGNORE INTO service_events
               (id,event_type,event_version,producer,subject_ref,source_revision,
                facts_json,refs_json,principal_kind,principal_identity,
                correlation_id,causation_id,privacy_class)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (event["id"], event["event_type"], event.get("event_version", 1),
             event["producer"], event["subject_ref"], event.get("source_revision", ""),
             json.dumps(event.get("facts", {}), sort_keys=True),
             json.dumps(event.get("refs", []), sort_keys=True),
             event["principal_kind"], event["principal_identity"],
             event.get("correlation_id", ""), event.get("causation_id", ""),
             event.get("privacy_class", "private")),
        )
        return bool(cur.rowcount)

    def append_event(self, event: dict[str, Any]) -> bool:
        with self._connection() as conn:
            return self._insert_event(conn, event)

    def append_event_in_transaction(self, conn: Any, event: dict[str, Any]) -> bool:
        return self._insert_event(conn, event)

    def record_refresh_error(self, watch_id: str, error: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_error=?,updated_at=datetime('now') WHERE id=?",
                (error[:1000], watch_id),
            )

    def list_events(self, *, event_type: str | None = None, producer: str | None = None,
                    limit: int = 100) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if event_type:
            clauses.append("event_type=?")
            params.append(event_type)
        if producer:
            clauses.append("producer=?")
            params.append(producer)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, min(int(limit), 500)))
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM service_events{where} ORDER BY created_at DESC,id DESC LIMIT ?",
                params,
            ).fetchall()
        values = [self._payload(row, "facts", "refs") for row in rows]
        for value in values:
            value["event_version"] = int(value["event_version"])
        return values

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM service_events WHERE id=?", (event_id,)).fetchone()
        return self._payload(row, "facts", "refs") if row else None

    def create_reaction(self, *, reaction_id: str, name: str, watch_id: str | None,
                        event_pattern: str, workbench_id: str, title_template: str,
                        auto_run: bool, enabled: bool) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO connector_reactions
                   (id,name,watch_id,event_pattern,workbench_id,title_template,auto_run,enabled)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (reaction_id, name, watch_id, event_pattern, workbench_id,
                 title_template, int(auto_run), int(enabled)),
            )
        return self.get_reaction(reaction_id) or {}

    def get_reaction(self, reaction_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM connector_reactions WHERE id=?", (reaction_id,)).fetchone()
        return self._payload(row) if row else None

    def list_reactions(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM connector_reactions ORDER BY created_at,id").fetchall()
        return [self._payload(row) for row in rows]

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
