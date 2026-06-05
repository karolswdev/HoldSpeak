"""DictationCorrectionRepository — durable home for dictation corrections.

Phase 40 (HS-40-02). The dictation `CorrectionStore`
(`plugins.dictation.corrections`) is a bounded in-process ring that nudges the
router from recent user corrections — but it dies with the process. This repo
gives that learning a home on disk: a correction is written through on `record`
and the recent set is loaded back on a fresh store's construction, so the
copilot keeps what it learned across restarts.

It stores + reads only. Corrections are gist-only and secret-rejected by the
`CorrectionStore` *before* they reach this repo, so a persisted row never
carries a secret.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..logging_config import get_logger
from .base import BaseRepository
from .models import DictationCorrectionRecord

log = get_logger("db.corrections")

#: Kinds accepted for persistence (mirrors `corrections.CORRECTION_KINDS`).
VALID_CORRECTION_KINDS = frozenset({"intent", "target"})


class DictationCorrectionRepository(BaseRepository):
    """Persistence for dictation corrections (write-through + recency load)."""

    def record_correction(
        self, *, kind: str, gist: str, value: str
    ) -> DictationCorrectionRecord:
        """Persist one correction; returns the stored record.

        Raises `ValueError` for an unknown kind or an empty gist/value. The
        caller (`CorrectionStore`) has already secret-checked the gist + value.
        """
        clean_kind = str(kind or "").strip().lower()
        clean_gist = str(gist or "").strip()
        clean_value = str(value or "").strip()
        if clean_kind not in VALID_CORRECTION_KINDS:
            raise ValueError(f"unknown correction kind: {kind!r}")
        if not clean_gist:
            raise ValueError("gist is required")
        if not clean_value:
            raise ValueError("value is required")

        now = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO dictation_corrections (kind, gist, value, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (clean_kind, clean_gist, clean_value, now),
            )
            row = conn.execute(
                "SELECT * FROM dictation_corrections WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return self._row_to_record(row)

    def recent_corrections(
        self, *, limit: Optional[int] = None
    ) -> list[DictationCorrectionRecord]:
        """Stored corrections newest-first (most recent created_at/id first)."""
        with self._connection() as conn:
            if limit is not None:
                rows = conn.execute(
                    """
                    SELECT * FROM dictation_corrections
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (max(0, int(limit)),),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM dictation_corrections
                    ORDER BY created_at DESC, id DESC
                    """
                ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def delete_correction(self, correction_id: int) -> bool:
        """Delete one correction by id. Returns True if a row was removed."""
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM dictation_corrections WHERE id = ?",
                (int(correction_id),),
            )
            return bool(cursor.rowcount and cursor.rowcount > 0)

    def clear(self) -> int:
        """Delete every stored correction. Returns the number removed."""
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM dictation_corrections")
            return int(cursor.rowcount or 0)

    def _row_to_record(self, row: Any) -> DictationCorrectionRecord:
        return DictationCorrectionRecord(
            id=int(row["id"]),
            kind=row["kind"],
            gist=row["gist"],
            value=row["value"],
            created_at=row["created_at"],
        )
