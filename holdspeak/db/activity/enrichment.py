"""Enrichment connectors and their run ledger.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Any

from ..models import ActivityEnrichmentConnectorState, ConnectorRun


class ActivityEnrichmentMixin:
    def upsert_activity_enrichment_connector(
        self,
        *,
        connector_id: str,
        enabled: Optional[bool] = None,
        settings: Optional[dict[str, Any]] = None,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Create or update persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            raise ValueError("connector_id is required")
        current = self.get_activity_enrichment_connector(clean_id)
        next_enabled = bool(enabled) if enabled is not None else (current.enabled if current else False)
        next_settings = settings if settings is not None else (current.settings if current else {})
        now_iso = datetime.now().isoformat()
        last_run_iso = (
            last_run_at.isoformat()
            if isinstance(last_run_at, datetime)
            else (current.last_run_at.isoformat() if current and current.last_run_at else None)
        )
        clean_error = (
            str(last_error)
            if last_error not in (None, "")
            else (current.last_error if current and last_error is None else None)
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_enrichment_connectors (
                    id, enabled, settings_json, last_run_at, last_error,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    settings_json = excluded.settings_json,
                    last_run_at = excluded.last_run_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_id,
                    int(next_enabled),
                    self._json_dumps(next_settings or {}, fallback="{}"),
                    last_run_iso,
                    clean_error,
                    now_iso,
                    now_iso,
                ),
            )
        state = self.get_activity_enrichment_connector(clean_id)
        if state is None:
            raise RuntimeError("activity enrichment connector was not created")
        return state

    def get_activity_enrichment_connector(
        self,
        connector_id: str,
    ) -> Optional[ActivityEnrichmentConnectorState]:
        """Load persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                WHERE id = ?
                """,
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_enrichment_connector(row)

    def list_activity_enrichment_connectors(self) -> list[ActivityEnrichmentConnectorState]:
        """List persisted enrichment connector states."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                ORDER BY id ASC
                """
            ).fetchall()
            return [self._row_to_activity_enrichment_connector(row) for row in rows]

    def record_activity_enrichment_run(
        self,
        *,
        connector_id: str,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Persist the latest run result for one enrichment connector."""
        state = self.get_activity_enrichment_connector(connector_id)
        return self.upsert_activity_enrichment_connector(
            connector_id=connector_id,
            enabled=state.enabled if state else False,
            settings=state.settings if state else {},
            last_run_at=last_run_at or datetime.now(),
            last_error=last_error if last_error is not None else "",
        )

    def record_connector_run(
        self,
        *,
        connector_id: str,
        started_at: datetime,
        finished_at: datetime,
        succeeded: bool,
        error: Optional[str] = None,
        output_bytes: int = 0,
        annotation_count: int = 0,
        candidate_count: int = 0,
        command_count: int = 0,
    ) -> ConnectorRun:
        """Persist one row to `connector_runs`. HS-13-05.

        Every code path that exercises a pack — gh / jira CLI
        runs, calendar previews on enable, extension event
        ingestion — calls this at completion (success *or*
        failure). The single-row `last_run_at` / `last_error`
        on `activity_enrichment_connectors` remains the
        "what happened most recently" fast-path; this table
        is the over-time signal.
        """
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            raise ValueError("connector_id is required")
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO connector_runs (
                    connector_id, started_at, finished_at,
                    succeeded, error, output_bytes,
                    annotation_count, candidate_count, command_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    started_at.isoformat(),
                    finished_at.isoformat(),
                    1 if succeeded else 0,
                    (error or None),
                    int(output_bytes),
                    int(annotation_count),
                    int(candidate_count),
                    int(command_count),
                ),
            )
            row_id = int(cursor.lastrowid or 0)
        return ConnectorRun(
            id=row_id,
            connector_id=clean_id,
            started_at=started_at,
            finished_at=finished_at,
            succeeded=bool(succeeded),
            error=(error or None),
            output_bytes=int(output_bytes),
            annotation_count=int(annotation_count),
            candidate_count=int(candidate_count),
            command_count=int(command_count),
        )

    def list_connector_runs(
        self,
        *,
        connector_id: str,
        limit: int = 10,
    ) -> list[ConnectorRun]:
        """Return the N most recent runs for one connector."""
        clean_id = str(connector_id or "").strip()
        capped = max(1, min(int(limit), 200))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, connector_id, started_at, finished_at,
                       succeeded, error, output_bytes,
                       annotation_count, candidate_count, command_count
                FROM connector_runs
                WHERE connector_id = ?
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (clean_id, capped),
            ).fetchall()
        return [self._row_to_connector_run(row) for row in rows]

    def delete_connector_runs(self, *, connector_id: str) -> int:
        """Drop every run row for one connector. Returns the row
        count deleted. Called by the per-pack "Clear annotations" /
        "Clear candidates" surfaces — run history is part of the
        connector's output."""
        clean_id = str(connector_id or "").strip()
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM connector_runs WHERE connector_id = ?",
                (clean_id,),
            )
            return int(cursor.rowcount or 0)

    def _row_to_connector_run(self, row: Any) -> ConnectorRun:
        return ConnectorRun(
            id=int(row[0]),
            connector_id=str(row[1]),
            started_at=datetime.fromisoformat(str(row[2])),
            finished_at=datetime.fromisoformat(str(row[3])),
            succeeded=bool(row[4]),
            error=(str(row[5]) if row[5] is not None else None),
            output_bytes=int(row[6] or 0),
            annotation_count=int(row[7] or 0),
            candidate_count=int(row[8] or 0),
            command_count=int(row[9] or 0),
        )

    def _row_to_activity_enrichment_connector(
        self,
        row: sqlite3.Row,
    ) -> ActivityEnrichmentConnectorState:
        return ActivityEnrichmentConnectorState(
            id=str(row["id"]),
            enabled=bool(row["enabled"]),
            settings=self._json_loads_dict(row["settings_json"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
            last_error=row["last_error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

