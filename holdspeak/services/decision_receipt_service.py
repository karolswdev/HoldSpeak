"""Durable decision receipt operations (HS-127-01)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service


_SOURCE_TYPES = frozenset({"meeting", "desk"})


@observe_service
class DecisionReceiptService:
    """Create and retrieve the durable canon for a decision."""

    def __init__(self, db: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def create(
        self,
        principal: Any,
        *,
        decision_text: str,
        rationale: str | None = None,
        alternatives: str | None = None,
        owner: str | None = None,
        review_date: str | None = None,
        source_type: str,
        source_id: str,
    ) -> dict[str, Any]:
        """Create a new decision receipt."""
        text = self._required("decision_text", decision_text)
        source_kind = self._required("source_type", source_type)
        if source_kind not in _SOURCE_TYPES:
            raise ValueError("source_type must be 'meeting' or 'desk'")
        source = self._required("source_id", source_id)
        receipt_id = f"receipt-{uuid4().hex}"
        now = datetime.now(UTC).isoformat()

        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO decision_receipts
                   (id, decision_text, rationale, alternatives, owner, review_date,
                    source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    receipt_id,
                    text,
                    rationale,
                    alternatives,
                    owner,
                    review_date,
                    source_kind,
                    source,
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM decision_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
        assert row is not None
        return self._receipt_dict(row)

    def get(self, principal: Any, receipt_id: str) -> dict[str, Any] | None:
        """Get a receipt by ID with its sources, work links, and revisions."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
            if row is None:
                return None
            receipt = self._receipt_dict(row)
            receipt["sources"] = self._rows(
                conn.execute(
                    """SELECT * FROM decision_receipt_sources
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            )
            receipt["work"] = self._rows(
                conn.execute(
                    """SELECT * FROM decision_receipt_work
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            )
            receipt["revisions"] = self._rows(
                conn.execute(
                    """SELECT * FROM decision_receipt_revisions
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            )
            return receipt

    def list_receipts(
        self, principal: Any, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List receipts, newest first."""
        bounded_limit = max(1, min(int(limit), 500))
        bounded_offset = max(0, int(offset))
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM decision_receipts
                   ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?""",
                (bounded_limit, bounded_offset),
            ).fetchall()
        return [self._receipt_dict(row) for row in rows]

    @staticmethod
    def _required(name: str, value: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError(f"{name} is required")
        return clean

    @staticmethod
    def _receipt_dict(row: Any) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _rows(rows: list[Any]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]
