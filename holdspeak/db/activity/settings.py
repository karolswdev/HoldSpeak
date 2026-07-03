"""The small state tables: import checkpoints, the privacy toggle, nudge dismissals.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from ..models import ActivityImportCheckpoint


class ActivitySettingsMixin:
    def set_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
        last_visit_raw: Optional[str] = None,
        last_imported_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
        enabled: bool = True,
    ) -> ActivityImportCheckpoint:
        """Create or update a browser history import checkpoint."""
        clean_browser = str(source_browser or "").strip().lower()
        if not clean_browser:
            raise ValueError("source_browser is required")
        clean_profile = str(source_profile or "").strip()
        clean_path_hash = str(source_path_hash or "").strip()
        now_iso = datetime.now().isoformat()
        imported_iso = (
            last_imported_at.isoformat()
            if isinstance(last_imported_at, datetime)
            else now_iso
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_import_checkpoints (
                    source_browser, source_profile, source_path_hash,
                    last_visit_raw, last_imported_at, last_error, enabled,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_browser, source_profile, source_path_hash)
                DO UPDATE SET
                    last_visit_raw = excluded.last_visit_raw,
                    last_imported_at = excluded.last_imported_at,
                    last_error = excluded.last_error,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_browser,
                    clean_profile,
                    clean_path_hash,
                    str(last_visit_raw) if last_visit_raw not in (None, "") else None,
                    imported_iso,
                    str(last_error) if last_error not in (None, "") else None,
                    int(bool(enabled)),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (clean_browser, clean_profile, clean_path_hash),
            ).fetchone()
            return self._row_to_activity_checkpoint(row)

    def list_activity_import_checkpoints(self) -> list[ActivityImportCheckpoint]:
        """List all browser history import checkpoints."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                ORDER BY source_browser ASC, source_profile ASC, source_path_hash ASC
                """
            ).fetchall()
            return [self._row_to_activity_checkpoint(row) for row in rows]

    def get_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
    ) -> Optional[ActivityImportCheckpoint]:
        """Load one browser history import checkpoint."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (
                    str(source_browser or "").strip().lower(),
                    str(source_profile or "").strip(),
                    str(source_path_hash or "").strip(),
                ),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_checkpoint(row)

    def get_activity_privacy_settings(self) -> dict[str, Any]:
        """Return activity ingestion privacy settings with defaults."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT enabled, retention_days, updated_at
                FROM activity_privacy_settings
                WHERE id = 1
                """
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO activity_privacy_settings
                        (id, enabled, retention_days, updated_at)
                    VALUES (1, 1, 30, ?)
                    """,
                    (datetime.now().isoformat(),),
                )
                row = conn.execute(
                    """
                    SELECT enabled, retention_days, updated_at
                    FROM activity_privacy_settings
                    WHERE id = 1
                    """
                ).fetchone()
            return {
                "enabled": bool(row["enabled"]),
                "paused": not bool(row["enabled"]),
                "retention_days": int(row["retention_days"] or 30),
                "updated_at": str(row["updated_at"]),
            }

    def update_activity_privacy_settings(
        self,
        *,
        enabled: Optional[bool] = None,
        retention_days: Optional[int] = None,
    ) -> dict[str, Any]:
        """Update activity ingestion privacy settings."""
        current = self.get_activity_privacy_settings()
        next_enabled = current["enabled"] if enabled is None else bool(enabled)
        next_retention = current["retention_days"]
        if retention_days is not None:
            next_retention = max(1, min(int(retention_days), 3650))
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_privacy_settings
                    (id, enabled, retention_days, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    retention_days = excluded.retention_days,
                    updated_at = excluded.updated_at
                """,
                (int(next_enabled), int(next_retention), datetime.now().isoformat()),
            )
        return self.get_activity_privacy_settings()

    def list_dismissed_nudge_keys(self) -> set[str]:
        """Phase 53: persisted nudge dismissals (HS-53-01)."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT nudge_key FROM activity_nudge_dismissals"
            ).fetchall()
            return {str(row["nudge_key"]) for row in rows}

    def dismiss_nudge(self, nudge_key: str) -> None:
        """Phase 53: persist a nudge dismissal so it stays dismissed (HS-53-01)."""
        clean = str(nudge_key or "").strip()
        if not clean:
            raise ValueError("nudge_key is required")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_nudge_dismissals (nudge_key, dismissed_at)
                VALUES (?, ?)
                ON CONFLICT(nudge_key) DO UPDATE SET dismissed_at = excluded.dismissed_at
                """,
                (clean, datetime.now().isoformat()),
            )

    def _row_to_activity_checkpoint(self, row: sqlite3.Row) -> ActivityImportCheckpoint:
        return ActivityImportCheckpoint(
            source_browser=str(row["source_browser"]),
            source_profile=str(row["source_profile"] or ""),
            source_path_hash=str(row["source_path_hash"] or ""),
            last_visit_raw=row["last_visit_raw"],
            last_imported_at=(
                datetime.fromisoformat(row["last_imported_at"])
                if row["last_imported_at"]
                else None
            ),
            last_error=row["last_error"],
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
