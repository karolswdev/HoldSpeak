"""Read access to pipeline observer events."""

from __future__ import annotations

import sqlite3
from typing import Any

from holdspeak.db.core import Database


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert an event row to its public representation."""
    event = dict(row)
    if "is_async" in event:
        event["is_async"] = bool(event["is_async"])
    return event


class EventQueryService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def recent(
        self,
        principal: Any,
        *,
        limit: int = 50,
        service: str | None = None,
        method: str | None = None,
        principal_kind: str | None = None,
        since: float | None = None,
        until: float | None = None,
        correlation_id: str | None = None,
        errors_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the most recent pipeline events matching the supplied filters."""
        del principal
        limit = max(0, min(limit, 1000))
        clauses: list[str] = []
        params: list[Any] = []

        for column, value in (
            ("service", service),
            ("method", method),
            ("principal_kind", principal_kind),
            ("timestamp >=", since),
            ("timestamp <=", until),
            ("correlation_id", correlation_id),
        ):
            if value is not None:
                operator = "?" if " " in column else "= ?"
                clauses.append(f"{column} {operator}")
                params.append(value)
        if errors_only:
            clauses.append("error IS NOT NULL")

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        query = f"SELECT * FROM pipeline_events{where} ORDER BY timestamp DESC LIMIT ?"
        with self._db._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_dict(row) for row in rows]

    def stats(
        self,
        principal: Any,
        *,
        since: float | None = None,
        until: float | None = None,
    ) -> dict[str, Any]:
        """Return aggregate pipeline event counts for the requested period."""
        del principal
        clauses: list[str] = []
        params: list[float] = []
        if since is not None:
            clauses.append("timestamp >= ?")
            params.append(since)
        if until is not None:
            clauses.append("timestamp <= ?")
            params.append(until)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._db._connection() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS total_events FROM pipeline_events{where}", params
            ).fetchone()["total_events"]
            by_service = conn.execute(
                "SELECT service, COUNT(*) AS count, "
                "COUNT(CASE WHEN error IS NOT NULL THEN 1 END) AS error_count, "
                "ROUND(AVG(duration_ms), 1) AS avg_ms "
                f"FROM pipeline_events{where} "
                "GROUP BY service ORDER BY count DESC",
                params,
            ).fetchall()
            by_method = conn.execute(
                "SELECT service, method, COUNT(*) AS count, "
                "COUNT(CASE WHEN error IS NOT NULL THEN 1 END) AS error_count, "
                "ROUND(AVG(duration_ms), 1) AS avg_ms "
                f"FROM pipeline_events{where} "
                "GROUP BY service, method ORDER BY count DESC LIMIT 20",
                params,
            ).fetchall()
            by_principal = conn.execute(
                "SELECT principal_kind AS kind, principal_identity AS identity, "
                "COUNT(*) AS count "
                f"FROM pipeline_events{where} "
                "GROUP BY principal_kind, principal_identity ORDER BY count DESC",
                params,
            ).fetchall()

        return {
            "total_events": total,
            "period": {"since": since, "until": until},
            "by_service": [dict(row) for row in by_service],
            "by_method": [dict(row) for row in by_method],
            "by_principal": [dict(row) for row in by_principal],
        }

    def by_correlation(
        self,
        principal: Any,
        correlation_id: str,
    ) -> list[dict[str, Any]]:
        """Return all events belonging to one correlation chain."""
        del principal
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM pipeline_events WHERE correlation_id = ? "
                "ORDER BY timestamp ASC",
                (correlation_id,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]
