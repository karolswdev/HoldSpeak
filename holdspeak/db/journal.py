"""DictationJournalRepository — the durable home for the dictation journal.

Phase 45 (HS-45-01). Meetings persist; dictation didn't. This repository gives
the daily-driver dictation loop a private, local-only record: one row per
pipeline run (real dictation *and* dry-run), capturing what was said, how it
routed, what got typed, and per-stage latency — so the loop becomes reviewable
(HS-45-02), correctable after the fact (HS-45-03), and replayable (HS-45-04).

It stores + reads only. The `DictationJournalRecorder`
(`plugins.dictation.journal`) secret-filters the transcript + final text
*before* they reach this repo, so a persisted row never carries a secret, and
passes the configured `retention` so each insert prunes the table to a
last-N bound. JSON-encoded columns (`stage_ms`, `rewrite_pass_ms`, `warnings`)
use the shared `_json_*` helpers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository
from .models import DictationJournalRecord

#: Run sources accepted for persistence (mirrors the recorder's `VALID_SOURCES`).
VALID_JOURNAL_SOURCES = frozenset({"dictation", "dry_run"})


class DictationJournalRepository(BaseRepository):
    """Persistence for the dictation journal (write + read + curate + prune)."""

    def record(
        self,
        *,
        source: str,
        transcript: str,
        final_text: str,
        intent: Optional[str] = None,
        block_id: Optional[str] = None,
        target_profile: Optional[str] = None,
        project_root: Optional[str] = None,
        stage_ms: Optional[dict[str, float]] = None,
        total_ms: float = 0.0,
        rewrite_pass_ms: Optional[list[float]] = None,
        confidence: Optional[float] = None,
        warnings: Optional[list[str]] = None,
        retention: Optional[int] = None,
    ) -> DictationJournalRecord:
        """Persist one journal row; prune to `retention` (last-N); return the row.

        Raises `ValueError` for an unknown `source`. The caller (the recorder)
        has already secret-filtered `transcript` + `final_text`.
        """
        clean_source = str(source or "").strip().lower()
        if clean_source not in VALID_JOURNAL_SOURCES:
            raise ValueError(f"unknown journal source: {source!r}")

        now = datetime.now().isoformat()
        stage_json = self._json_dumps(stage_ms or {}, fallback="{}")
        passes_json = self._json_dumps(
            [float(x) for x in (rewrite_pass_ms or [])], fallback="[]"
        )
        warnings_json = self._json_dumps(
            [str(w) for w in (warnings or [])], fallback="[]"
        )
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO dictation_journal (
                    created_at, source, project_root, transcript, intent,
                    block_id, target_profile, final_text, stage_ms, total_ms,
                    rewrite_pass_ms, confidence, warnings, corrected, correction_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
                """,
                (
                    now,
                    clean_source,
                    (str(project_root) if project_root else None),
                    str(transcript or ""),
                    (str(intent) if intent else None),
                    (str(block_id) if block_id else None),
                    (str(target_profile) if target_profile else None),
                    str(final_text or ""),
                    stage_json,
                    float(total_ms or 0.0),
                    passes_json,
                    (float(confidence) if confidence is not None else None),
                    warnings_json,
                ),
            )
            new_id = cursor.lastrowid
            if retention is not None:
                self._prune(conn, int(retention))
            row = conn.execute(
                "SELECT * FROM dictation_journal WHERE id = ?", (new_id,)
            ).fetchone()
        return self._row_to_record(row)

    def recent(
        self, *, limit: Optional[int] = None, source: Optional[str] = None
    ) -> list[DictationJournalRecord]:
        """Stored entries newest-first, optionally filtered by `source`/limited."""
        clauses = []
        params: list[Any] = []
        if source is not None:
            clauses.append("source = ?")
            params.append(str(source).strip().lower())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT * FROM dictation_journal {where} "
            "ORDER BY created_at DESC, id DESC"
        )
        if limit is not None:
            sql += " LIMIT ?"
            params.append(max(0, int(limit)))
        with self._connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get(self, entry_id: int) -> Optional[DictationJournalRecord]:
        """One entry by id, or None if absent."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM dictation_journal WHERE id = ?", (int(entry_id),)
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def mark_corrected(
        self, entry_id: int, *, correction_id: Optional[int] = None
    ) -> bool:
        """Flag an entry as corrected (HS-45-03 owns calling this).

        Sets `corrected = 1` and optionally links the `dictation_corrections`
        row the in-moment fix created. Returns True if a row was updated.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE dictation_journal
                SET corrected = 1, correction_id = ?
                WHERE id = ?
                """,
                (
                    (int(correction_id) if correction_id is not None else None),
                    int(entry_id),
                ),
            )
            return bool(cursor.rowcount and cursor.rowcount > 0)

    def update_transcript(self, entry_id: int, transcript: str) -> bool:
        """HS-101 (edit in place): rewrite one entry's transcript record.

        The presented text is the record — corrections stay the separate,
        taught act (`mark_corrected`). Returns True if a row was updated.
        """
        text = str(transcript).strip()
        if not text:
            return False
        with self._connection() as conn:
            cursor = conn.execute(
                "UPDATE dictation_journal SET transcript = ? WHERE id = ?",
                (text, int(entry_id)),
            )
            return bool(cursor.rowcount and cursor.rowcount > 0)

    def delete(self, entry_id: int) -> bool:
        """Delete one entry by id. Returns True if a row was removed."""
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM dictation_journal WHERE id = ?", (int(entry_id),)
            )
            return bool(cursor.rowcount and cursor.rowcount > 0)

    def clear(self) -> int:
        """Wipe the journal. Returns the number of rows removed."""
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM dictation_journal")
            return int(cursor.rowcount or 0)

    def count(self) -> int:
        """Total stored entries."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM dictation_journal"
            ).fetchone()
        return int(row["n"]) if row is not None else 0

    def _prune(self, conn: Any, retention: int) -> None:
        """Prune to the newest `retention` rows (last-N cap)."""
        keep = max(1, int(retention))
        conn.execute(
            """
            DELETE FROM dictation_journal
            WHERE id NOT IN (
                SELECT id FROM dictation_journal
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            )
            """,
            (keep,),
        )

    def _row_to_record(self, row: Any) -> DictationJournalRecord:
        return DictationJournalRecord(
            id=int(row["id"]),
            created_at=row["created_at"],
            source=row["source"],
            transcript=row["transcript"] or "",
            final_text=row["final_text"] or "",
            project_root=row["project_root"],
            intent=row["intent"],
            block_id=row["block_id"],
            target_profile=row["target_profile"],
            stage_ms={
                str(k): float(v)
                for k, v in self._json_loads_dict(row["stage_ms"]).items()
            },
            total_ms=float(row["total_ms"] or 0.0),
            rewrite_pass_ms=[
                float(x) for x in self._json_loads_list(row["rewrite_pass_ms"])
            ],
            confidence=(
                float(row["confidence"]) if row["confidence"] is not None else None
            ),
            warnings=[str(w) for w in self._json_loads_list(row["warnings"])],
            corrected=bool(row["corrected"]),
            correction_id=(
                int(row["correction_id"])
                if row["correction_id"] is not None
                else None
            ),
        )
