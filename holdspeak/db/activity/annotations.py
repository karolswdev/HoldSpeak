"""Free-form activity annotations.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Any

from ..models import ActivityAnnotation


class ActivityAnnotationsMixin:
    def create_activity_annotation(
        self,
        *,
        source_connector_id: str,
        annotation_type: str,
        title: str = "",
        value: Optional[dict[str, Any]] = None,
        confidence: float = 0.0,
        activity_record_id: Optional[int] = None,
        annotation_id: Optional[str] = None,
    ) -> ActivityAnnotation:
        """Persist one local enrichment annotation."""
        clean_connector = str(source_connector_id or "").strip()
        if not clean_connector:
            raise ValueError("source_connector_id is required")
        clean_type = str(annotation_type or "").strip().lower()
        if not clean_type:
            raise ValueError("annotation_type is required")
        clean_id = str(annotation_id or f"ann-{uuid.uuid4().hex[:12]}").strip()
        record_id = int(activity_record_id) if activity_record_id is not None else None
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            if record_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM activity_records WHERE id = ?",
                    (record_id,),
                ).fetchone()
                if exists is None:
                    raise ValueError(f"activity record not found: {record_id}")
            conn.execute(
                """
                INSERT INTO activity_annotations (
                    id, activity_record_id, source_connector_id, annotation_type,
                    title, value_json, confidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    record_id,
                    clean_connector,
                    clean_type,
                    str(title or "").strip(),
                    self._json_dumps(value or {}, fallback="{}"),
                    max(0.0, min(1.0, float(confidence))),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                "SELECT * FROM activity_annotations WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_annotation(row)

    def list_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[ActivityAnnotation]:
        """List local enrichment annotations."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "SELECT * FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_annotation(row) for row in rows]

    def delete_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
    ) -> int:
        """Delete local enrichment annotations by connector, record, or type."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "DELETE FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def _row_to_activity_annotation(self, row: sqlite3.Row) -> ActivityAnnotation:
        return ActivityAnnotation(
            id=str(row["id"]),
            activity_record_id=int(row["activity_record_id"]) if row["activity_record_id"] is not None else None,
            source_connector_id=str(row["source_connector_id"]),
            annotation_type=str(row["annotation_type"]),
            title=str(row["title"] or ""),
            value=self._json_loads_dict(row["value_json"]),
            confidence=float(row["confidence"] or 0),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

