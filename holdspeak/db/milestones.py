"""MilestoneRepository — durable one-time markers for first-run state.

Phase 42 (HS-42-01). The setup surface needs to know whether the user has ever
reached a milestone (the first successful dictation) so a healthy returning user
is never sent back to setup-mode. A milestone is a single durable key recorded
once; `first_run` is true while the first-success key is absent.

It stores + reads only — keys are short, opaque strings (no payload, no secrets).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..logging_config import get_logger
from .base import BaseRepository

log = get_logger("db.milestones")

#: The user has completed a verified first dictation (set by HS-42-04).
FIRST_DICTATION_SUCCESS = "first_dictation_success"


class MilestoneRepository(BaseRepository):
    """Durable one-time markers (achieved/at), keyed by a stable string."""

    def mark(self, key: str) -> str:
        """Record a milestone as achieved (idempotent). Returns its timestamp.

        A second `mark` of the same key keeps the original `achieved_at` — the
        milestone is reached once.
        """
        clean = str(key or "").strip()
        if not clean:
            raise ValueError("milestone key is required")
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO milestones (key, achieved_at) VALUES (?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (clean, now),
            )
            row = conn.execute(
                "SELECT achieved_at FROM milestones WHERE key = ?", (clean,)
            ).fetchone()
        return row["achieved_at"] if row else now

    def is_set(self, key: str) -> bool:
        """True if the milestone has ever been achieved."""
        clean = str(key or "").strip()
        if not clean:
            return False
        with self._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM milestones WHERE key = ?", (clean,)
            ).fetchone()
        return row is not None

    def achieved_at(self, key: str) -> Optional[str]:
        """The ISO timestamp the milestone was achieved, or None."""
        clean = str(key or "").strip()
        if not clean:
            return None
        with self._connection() as conn:
            row = conn.execute(
                "SELECT achieved_at FROM milestones WHERE key = ?", (clean,)
            ).fetchone()
        return row["achieved_at"] if row else None

    def clear(self, key: str) -> bool:
        """Remove a milestone (e.g. to re-trigger first-run). True if removed."""
        clean = str(key or "").strip()
        if not clean:
            return False
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM milestones WHERE key = ?", (clean,))
            return bool(cursor.rowcount and cursor.rowcount > 0)
