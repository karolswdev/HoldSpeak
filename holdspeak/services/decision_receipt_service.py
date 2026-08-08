"""Durable decision receipt operations (HS-127-01)."""

from __future__ import annotations

import json
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

    def create_from_meeting(self, principal: Any, decision_id: str) -> dict[str, Any]:
        """Mint a receipt from a meeting-derived decision."""
        decision = self._db.decisions.get(decision_id)
        if decision is None:
            raise KeyError(str(decision_id or "").strip())
        existing = self._receipt_for_source("meeting", decision.id)
        if existing is not None:
            return existing

        receipt = self.create(
            principal,
            decision_text=decision.text,
            rationale=decision.rationale,
            source_type="meeting",
            source_id=decision.id,
        )
        # A segment is precision evidence, not a prerequisite for minting the
        # receipt.  Keep its absence honest when the decision's moment cannot
        # be resolved from the current transcript.
        try:
            moment = self._db.decisions.resolve_decision_moment(decision.id)
        except Exception:
            moment = None
        sources: list[tuple[str, str]] = [
            ("meeting", decision.source_meeting_id),
            ("artifact", decision.source_artifact_id),
        ]
        if moment is not None:
            sources.append(("segment", str(moment.segment_id)))
        self._add_sources(receipt["id"], tuple(sources))
        return receipt

    def create_from_desk(self, principal: Any, desk_decision_id: str) -> dict[str, Any]:
        """Mint a receipt from an authored desk decision."""
        decision = self._db.desk_decisions.get(desk_decision_id)
        if decision is None:
            raise KeyError(str(desk_decision_id or "").strip())
        existing = self._receipt_for_source("desk", decision.id)
        if existing is not None:
            return existing

        decision_text = decision.decision_markdown.strip()
        if not decision_text:
            raise ValueError("desk decision decision_markdown is required")
        rationale = self._join_text(
            decision.context_markdown, decision.consequences_markdown
        )
        alternatives = self._alternatives_text(decision.alternatives_json)
        owner = ", ".join(decider.strip() for decider in decision.deciders if decider.strip())
        return self.create(
            principal,
            decision_text=decision_text,
            rationale=rationale or None,
            alternatives=alternatives or None,
            owner=owner or None,
            source_type="desk",
            source_id=decision.id,
        )

    def get(self, principal: Any, receipt_id: str) -> dict[str, Any] | None:
        """Get a receipt by ID with its sources, work links, and revisions."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
            if row is None:
                return None
            receipt = self._receipt_dict(row)
            receipt["sources"] = [
                self._source_dict(conn, source)
                for source in conn.execute(
                    """SELECT * FROM decision_receipt_sources
                       WHERE receipt_id = ? ORDER BY created_at, id""",
                    (receipt_id,),
                ).fetchall()
            ]
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

    def _receipt_for_source(self, source_type: str, source_id: str) -> dict[str, Any] | None:
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT * FROM decision_receipts
                   WHERE source_type = ? AND source_id = ?
                   ORDER BY created_at, id LIMIT 1""",
                (source_type, source_id),
            ).fetchone()
        return self._receipt_dict(row) if row is not None else None

    def _add_sources(
        self, receipt_id: str, sources: tuple[tuple[str, str], ...]
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._db._connection() as conn:
            for source_type, source_ref in sources:
                clean_ref = str(source_ref or "").strip()
                if not clean_ref:
                    continue
                conn.execute(
                    """INSERT INTO decision_receipt_sources
                       (id, receipt_id, source_type, source_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (f"receipt-source-{uuid4().hex}", receipt_id, source_type, clean_ref, now),
                )

    @staticmethod
    def _join_text(*values: str) -> str:
        return "\n\n".join(str(value or "").strip() for value in values if str(value or "").strip())

    @staticmethod
    def _alternatives_text(value: str) -> str:
        try:
            alternatives = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return ""
        return json.dumps(alternatives, ensure_ascii=False) if alternatives else ""

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
    def _source_dict(conn: Any, row: Any) -> dict[str, Any]:
        """Enrich a receipt source with the target data needed to open it."""
        source = dict(row)
        source_type = source["source_type"]
        source_ref = source["source_ref"]
        if source_type == "segment":
            target = conn.execute(
                """SELECT id, meeting_id, text, speaker, start_time, end_time
                   FROM segments WHERE id = ?""",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = dict(target)
                source.update(details)
                source["details"] = details
        elif source_type == "meeting":
            target = conn.execute(
                "SELECT id, title, started_at FROM meetings WHERE id = ?",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = {"title": target["title"], "date": target["started_at"]}
                source.update(details)
                source["details"] = details
        elif source_type == "artifact":
            target = conn.execute(
                "SELECT id, artifact_type FROM artifacts WHERE id = ?",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = {"artifact_type": target["artifact_type"]}
                source.update(details)
                source["details"] = details
        return source

    @staticmethod
    def _rows(rows: list[Any]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]
