"""Plugin runs, intent windows, and artifacts.

Extracted verbatim from core.py in Phase 31 (HS-31-03).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional, Any

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    IntentWindowSummary,
    PluginRunSummary,
    PluginRunJob,
    PluginRunJobQueueSummary,
    ArtifactSummary,
)

log = get_logger("db.plugins")


class PluginArtifactRepository(BaseRepository):
    """Plugin runs, intent windows, and artifacts."""

    def record_intent_window(
        self,
        *,
        meeting_id: str,
        window_id: str,
        start_seconds: float,
        end_seconds: float,
        transcript_hash: str,
        transcript_excerpt: str = "",
        profile: str = "balanced",
        threshold: float = 0.6,
        active_intents: Optional[list[str]] = None,
        intent_scores: Optional[dict[str, float]] = None,
        override_intents: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Insert or update one persisted MIR intent window."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")

        start_value = max(0.0, float(start_seconds))
        end_value = max(start_value, float(end_seconds))
        clean_profile = str(profile).strip().lower() or "balanced"
        clean_threshold = float(threshold)
        clean_hash = str(transcript_hash or "").strip()
        clean_excerpt = str(transcript_excerpt or "").strip()
        clean_active = [
            str(intent).strip().lower()
            for intent in (active_intents or [])
            if str(intent).strip()
        ]
        clean_override = [
            str(intent).strip().lower()
            for intent in (override_intents or [])
            if str(intent).strip()
        ]
        clean_tags = [
            str(tag).strip().lower()
            for tag in (tags or [])
            if str(tag).strip()
        ]
        clean_metadata = dict(metadata) if isinstance(metadata, dict) else {}
        clean_scores: dict[str, float] = {}
        if isinstance(intent_scores, dict):
            for raw_label, raw_score in intent_scores.items():
                label = str(raw_label).strip().lower()
                if not label:
                    continue
                try:
                    score_value = float(raw_score)
                except Exception:
                    continue
                clean_scores[label] = score_value

        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intent_windows (
                    meeting_id, window_id, start_seconds, end_seconds, transcript_hash,
                    transcript_excerpt, profile, threshold, active_intents_json,
                    override_intents_json, tags_json, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(meeting_id, window_id) DO UPDATE SET
                    start_seconds = excluded.start_seconds,
                    end_seconds = excluded.end_seconds,
                    transcript_hash = excluded.transcript_hash,
                    transcript_excerpt = excluded.transcript_excerpt,
                    profile = excluded.profile,
                    threshold = excluded.threshold,
                    active_intents_json = excluded.active_intents_json,
                    override_intents_json = excluded.override_intents_json,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_meeting_id,
                    clean_window_id,
                    start_value,
                    end_value,
                    clean_hash,
                    clean_excerpt,
                    clean_profile,
                    clean_threshold,
                    self._json_dumps(clean_active, fallback="[]"),
                    self._json_dumps(clean_override, fallback="[]"),
                    self._json_dumps(clean_tags, fallback="[]"),
                    self._json_dumps(clean_metadata, fallback="{}"),
                    now_iso,
                    now_iso,
                ),
            )
            conn.execute(
                """
                DELETE FROM intent_window_scores
                WHERE meeting_id = ? AND window_id = ?
                """,
                (clean_meeting_id, clean_window_id),
            )
            for intent_label, score in sorted(clean_scores.items()):
                conn.execute(
                    """
                    INSERT INTO intent_window_scores (
                        meeting_id, window_id, intent_label, score, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        intent_label,
                        float(score),
                        now_iso,
                    ),
                )

    def list_intent_windows(
        self,
        meeting_id: str,
        *,
        limit: int = 200,
    ) -> list[IntentWindowSummary]:
        """List persisted MIR intent windows for one meeting."""
        clean_meeting_id = str(meeting_id).strip()
        bounded_limit = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            window_rows = conn.execute(
                """
                SELECT *
                FROM intent_windows
                WHERE meeting_id = ?
                ORDER BY start_seconds ASC, created_at ASC
                LIMIT ?
                """,
                (clean_meeting_id, bounded_limit),
            ).fetchall()
            if not window_rows:
                return []

            score_rows = conn.execute(
                """
                SELECT meeting_id, window_id, intent_label, score
                FROM intent_window_scores
                WHERE meeting_id = ?
                ORDER BY window_id ASC, intent_label ASC
                """,
                (clean_meeting_id,),
            ).fetchall()

        scores_by_window: dict[str, dict[str, float]] = {}
        for row in score_rows:
            wid = str(row["window_id"])
            scores_by_window.setdefault(wid, {})[str(row["intent_label"])] = float(row["score"])

        windows: list[IntentWindowSummary] = []
        for row in window_rows:
            window_id = str(row["window_id"])
            windows.append(
                IntentWindowSummary(
                    meeting_id=str(row["meeting_id"]),
                    window_id=window_id,
                    start_seconds=float(row["start_seconds"]),
                    end_seconds=float(row["end_seconds"]),
                    transcript_hash=str(row["transcript_hash"] or ""),
                    transcript_excerpt=str(row["transcript_excerpt"] or ""),
                    profile=str(row["profile"] or "balanced"),
                    threshold=float(row["threshold"] if row["threshold"] is not None else 0.6),
                    active_intents=[
                        str(intent).strip().lower()
                        for intent in self._json_loads_list(row["active_intents_json"])
                        if str(intent).strip()
                    ],
                    intent_scores=scores_by_window.get(window_id, {}),
                    override_intents=[
                        str(intent).strip().lower()
                        for intent in self._json_loads_list(row["override_intents_json"])
                        if str(intent).strip()
                    ],
                    tags=[
                        str(tag).strip().lower()
                        for tag in self._json_loads_list(row["tags_json"])
                        if str(tag).strip()
                    ],
                    metadata=self._json_loads_dict(row["metadata_json"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return windows

    def record_plugin_run(
        self,
        *,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        plugin_version: str,
        status: str,
        idempotency_key: Optional[str] = None,
        duration_ms: float = 0.0,
        output: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        deduped: bool = False,
    ) -> None:
        """Persist one MIR plugin-run record."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        clean_plugin_id = str(plugin_id).strip()
        clean_status = str(status).strip().lower()
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        clean_idempotency_key = (
            str(idempotency_key).strip() if isinstance(idempotency_key, str) and idempotency_key.strip() else None
        )
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")
        if not clean_plugin_id:
            raise ValueError("plugin_id is required")
        if not clean_status:
            raise ValueError("status is required")

        now_iso = datetime.now().isoformat()
        output_json = self._json_dumps(output, fallback="null") if output is not None else None
        with self._connection() as conn:
            if clean_idempotency_key:
                conn.execute(
                    """
                    INSERT INTO plugin_runs (
                        meeting_id, window_id, plugin_id, plugin_version, status,
                        idempotency_key, duration_ms, output_json, error, deduped, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                        meeting_id = excluded.meeting_id,
                        window_id = excluded.window_id,
                        plugin_id = excluded.plugin_id,
                        plugin_version = excluded.plugin_version,
                        status = excluded.status,
                        duration_ms = excluded.duration_ms,
                        output_json = excluded.output_json,
                        error = excluded.error,
                        deduped = excluded.deduped,
                        updated_at = excluded.updated_at
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_status,
                        clean_idempotency_key,
                        float(duration_ms),
                        output_json,
                        error,
                        int(bool(deduped)),
                        now_iso,
                        now_iso,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO plugin_runs (
                        meeting_id, window_id, plugin_id, plugin_version, status,
                        idempotency_key, duration_ms, output_json, error, deduped, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_status,
                        None,
                        float(duration_ms),
                        output_json,
                        error,
                        int(bool(deduped)),
                        now_iso,
                        now_iso,
                    ),
                )

    def list_plugin_runs(
        self,
        meeting_id: str,
        *,
        window_id: Optional[str] = None,
        limit: int = 500,
    ) -> list[PluginRunSummary]:
        """List persisted MIR plugin-run history for one meeting."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip() if isinstance(window_id, str) else None
        bounded_limit = max(1, min(int(limit), 5000))

        with self._connection() as conn:
            query = """
                SELECT *
                FROM plugin_runs
                WHERE meeting_id = ?
            """
            params: list[Any] = [clean_meeting_id]
            if clean_window_id:
                query += " AND window_id = ?"
                params.append(clean_window_id)
            query += " ORDER BY created_at DESC, id DESC LIMIT ?"
            params.append(bounded_limit)
            rows = conn.execute(query, params).fetchall()

        output: list[PluginRunSummary] = []
        for row in rows:
            output_json = row["output_json"]
            parsed_output: Optional[dict[str, Any]] = None
            if isinstance(output_json, str) and output_json:
                try:
                    parsed_value = json.loads(output_json)
                except Exception:
                    parsed_value = None
                if isinstance(parsed_value, dict):
                    parsed_output = parsed_value

            output.append(
                PluginRunSummary(
                    id=int(row["id"]),
                    meeting_id=str(row["meeting_id"]),
                    window_id=str(row["window_id"]),
                    plugin_id=str(row["plugin_id"]),
                    plugin_version=str(row["plugin_version"] or "unknown"),
                    status=str(row["status"] or "unknown"),
                    idempotency_key=str(row["idempotency_key"]) if row["idempotency_key"] else None,
                    duration_ms=float(row["duration_ms"] if row["duration_ms"] is not None else 0.0),
                    output=parsed_output,
                    error=row["error"],
                    deduped=bool(row["deduped"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return output

    def _row_to_plugin_run_job(self, row: sqlite3.Row) -> PluginRunJob:
        context = self._json_loads_dict(row["context_json"])
        return PluginRunJob(
            id=int(row["id"]),
            meeting_id=str(row["meeting_id"]),
            window_id=str(row["window_id"]),
            plugin_id=str(row["plugin_id"]),
            plugin_version=str(row["plugin_version"] or "unknown"),
            transcript_hash=str(row["transcript_hash"] or ""),
            idempotency_key=str(row["idempotency_key"]),
            context=context,
            status=str(row["status"] or "queued"),
            requested_at=datetime.fromisoformat(str(row["requested_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            attempts=int(row["attempts"] or 0),
            last_error=row["last_error"],
        )

    def enqueue_plugin_run_job(
        self,
        *,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        plugin_version: str,
        transcript_hash: str,
        idempotency_key: str,
        context: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Queue one deferred MIR plugin run.

        Returns True when a new queue row was inserted, False when an existing
        idempotency key was refreshed/reused.
        """
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        clean_plugin_id = str(plugin_id).strip()
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        clean_hash = str(transcript_hash or "").strip()
        clean_key = str(idempotency_key).strip()
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")
        if not clean_plugin_id:
            raise ValueError("plugin_id is required")
        if not clean_key:
            raise ValueError("idempotency_key is required")

        now_iso = datetime.now().isoformat()
        context_json = self._json_dumps(context or {}, fallback="{}")
        with self._connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM plugin_run_jobs
                WHERE idempotency_key = ?
                """,
                (clean_key,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO plugin_run_jobs (
                        meeting_id, window_id, plugin_id, plugin_version,
                        transcript_hash, idempotency_key, context_json, status,
                        requested_at, updated_at, attempts, last_error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, 0, NULL)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_hash,
                        clean_key,
                        context_json,
                        now_iso,
                        now_iso,
                    ),
                )
                return True

            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET meeting_id = ?,
                    window_id = ?,
                    plugin_id = ?,
                    plugin_version = ?,
                    transcript_hash = ?,
                    context_json = ?,
                    status = CASE WHEN status = 'running' THEN status ELSE 'queued' END,
                    requested_at = CASE WHEN status = 'running' THEN requested_at ELSE ? END,
                    updated_at = ?,
                    last_error = NULL
                WHERE idempotency_key = ?
                """,
                (
                    clean_meeting_id,
                    clean_window_id,
                    clean_plugin_id,
                    clean_plugin_version,
                    clean_hash,
                    context_json,
                    now_iso,
                    now_iso,
                    clean_key,
                ),
            )
            return False

    def claim_next_plugin_run_job(
        self,
        *,
        include_scheduled: bool = False,
    ) -> Optional[PluginRunJob]:
        """Claim the next deferred MIR plugin run for processing."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM plugin_run_jobs
                WHERE status = 'queued'
                  AND (requested_at <= ? OR ? = 1)
                ORDER BY requested_at ASC, id ASC
                LIMIT 1
                """,
                (now_iso, 1 if include_scheduled else 0),
            ).fetchone()
            if row is None:
                return None
            job_id = int(row["id"])
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'running',
                    attempts = attempts + 1,
                    updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (now_iso, job_id),
            )
            claimed = conn.execute(
                "SELECT * FROM plugin_run_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if claimed is None:
                return None
            return self._row_to_plugin_run_job(claimed)

    def get_plugin_run_job(self, job_id: int) -> Optional[PluginRunJob]:
        """Load one deferred MIR plugin-run queue item by id."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM plugin_run_jobs WHERE id = ?",
                (int(job_id),),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_plugin_run_job(row)

    def retry_plugin_run_job(
        self,
        job_id: int,
        *,
        error: str,
        retry_at: datetime,
    ) -> None:
        """Requeue a deferred MIR plugin run for a later retry."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'queued',
                    requested_at = ?,
                    updated_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (
                    retry_at.isoformat(),
                    datetime.now().isoformat(),
                    str(error),
                    int(job_id),
                ),
            )

    def fail_plugin_run_job(self, job_id: int, *, error: str) -> None:
        """Mark a deferred MIR plugin run as permanently failed."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'failed',
                    updated_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), str(error), int(job_id)),
            )

    def complete_plugin_run_job(self, job_id: int) -> None:
        """Remove a completed deferred MIR plugin run from the queue."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM plugin_run_jobs WHERE id = ?",
                (int(job_id),),
            )

    def list_plugin_run_jobs(
        self,
        *,
        status: str = "all",
        meeting_id: Optional[str] = None,
        limit: int = 200,
    ) -> list[PluginRunJob]:
        """List deferred MIR plugin-run queue items."""
        clean_status = str(status or "all").strip().lower()
        clean_meeting_id = str(meeting_id).strip() if isinstance(meeting_id, str) and meeting_id.strip() else None
        bounded_limit = max(1, min(int(limit), 5000))

        with self._connection() as conn:
            query = "SELECT * FROM plugin_run_jobs WHERE 1=1"
            params: list[Any] = []
            if clean_status != "all":
                query += " AND status = ?"
                params.append(clean_status)
            if clean_meeting_id:
                query += " AND meeting_id = ?"
                params.append(clean_meeting_id)
            query += " ORDER BY requested_at ASC, id ASC LIMIT ?"
            params.append(bounded_limit)
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_plugin_run_job(row) for row in rows]

    def get_plugin_run_job_summary(self) -> PluginRunJobQueueSummary:
        """Return aggregate telemetry for deferred plugin-run queue state."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM plugin_run_jobs
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                """
                SELECT MIN(requested_at) AS next_retry_at
                FROM plugin_run_jobs
                WHERE status = 'queued'
                  AND requested_at > ?
                  AND last_error IS NOT NULL
                """,
                (now_iso,),
            ).fetchone()

        next_retry_at = None
        if next_row is not None and next_row["next_retry_at"]:
            next_retry_at = datetime.fromisoformat(next_row["next_retry_at"])

        return PluginRunJobQueueSummary(
            total_jobs=int(row["total_jobs"] or 0),
            queued_jobs=int(row["queued_jobs"] or 0),
            running_jobs=int(row["running_jobs"] or 0),
            failed_jobs=int(row["failed_jobs"] or 0),
            queued_due_jobs=int(row["queued_due_jobs"] or 0),
            scheduled_retry_jobs=int(row["scheduled_retry_jobs"] or 0),
            next_retry_at=next_retry_at,
        )

    def record_artifact(
        self,
        *,
        artifact_id: str,
        meeting_id: str,
        artifact_type: str,
        title: str,
        body_markdown: str = "",
        structured_json: Optional[dict[str, Any]] = None,
        confidence: float = 0.0,
        status: str = "draft",
        plugin_id: str = "unknown",
        plugin_version: str = "unknown",
        sources: Optional[list[dict[str, str]]] = None,
    ) -> None:
        """Insert or update one synthesized artifact and its lineage sources."""
        clean_artifact_id = str(artifact_id).strip()
        clean_meeting_id = str(meeting_id).strip()
        clean_type = str(artifact_type).strip().lower() or "plugin_output"
        clean_title = str(title).strip() or "Artifact"
        clean_body = str(body_markdown or "")
        clean_status = str(status).strip().lower() or "draft"
        clean_plugin_id = str(plugin_id).strip() or "unknown"
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        if not clean_artifact_id:
            raise ValueError("artifact_id is required")
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if clean_status not in {"draft", "needs_review", "accepted", "rejected"}:
            raise ValueError(f"Invalid artifact status: {clean_status!r}")

        normalized_sources: list[tuple[str, str]] = []
        for source in sources or []:
            source_type = ""
            source_ref = ""
            if isinstance(source, dict):
                source_type = str(source.get("source_type") or "").strip().lower()
                source_ref = str(source.get("source_ref") or "").strip()
            elif isinstance(source, (tuple, list)) and len(source) == 2:
                source_type = str(source[0] or "").strip().lower()
                source_ref = str(source[1] or "").strip()
            if source_type and source_ref and (source_type, source_ref) not in normalized_sources:
                normalized_sources.append((source_type, source_ref))

        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    id, meeting_id, artifact_type, title, body_markdown, structured_json,
                    confidence, status, plugin_id, plugin_version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    meeting_id = excluded.meeting_id,
                    artifact_type = excluded.artifact_type,
                    title = excluded.title,
                    body_markdown = excluded.body_markdown,
                    structured_json = excluded.structured_json,
                    confidence = excluded.confidence,
                    status = excluded.status,
                    plugin_id = excluded.plugin_id,
                    plugin_version = excluded.plugin_version,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_artifact_id,
                    clean_meeting_id,
                    clean_type,
                    clean_title,
                    clean_body,
                    self._json_dumps(structured_json or {}, fallback="{}"),
                    max(0.0, min(1.0, float(confidence))),
                    clean_status,
                    clean_plugin_id,
                    clean_plugin_version,
                    now_iso,
                    now_iso,
                ),
            )
            conn.execute(
                "DELETE FROM artifact_sources WHERE artifact_id = ?",
                (clean_artifact_id,),
            )
            for source_type, source_ref in normalized_sources:
                conn.execute(
                    """
                    INSERT INTO artifact_sources (artifact_id, source_type, source_ref, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (clean_artifact_id, source_type, source_ref, now_iso),
                )

    def list_artifacts(
        self,
        meeting_id: str,
        *,
        limit: int = 200,
    ) -> list[ArtifactSummary]:
        """List synthesized artifacts for one meeting, including lineage refs."""
        clean_meeting_id = str(meeting_id).strip()
        bounded_limit = max(1, min(int(limit), 2000))

        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM artifacts
                WHERE meeting_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (clean_meeting_id, bounded_limit),
            ).fetchall()
            if not rows:
                return []

            artifact_ids = [str(row["id"]) for row in rows]
            placeholders = ",".join("?" for _ in artifact_ids)
            source_rows = conn.execute(
                f"""
                SELECT artifact_id, source_type, source_ref
                FROM artifact_sources
                WHERE artifact_id IN ({placeholders})
                ORDER BY source_type ASC, source_ref ASC
                """,
                artifact_ids,
            ).fetchall()

        sources_by_artifact: dict[str, list[dict[str, str]]] = {}
        for row in source_rows:
            artifact_id = str(row["artifact_id"])
            sources_by_artifact.setdefault(artifact_id, []).append(
                {
                    "source_type": str(row["source_type"]),
                    "source_ref": str(row["source_ref"]),
                }
            )

        output: list[ArtifactSummary] = []
        for row in rows:
            output.append(
                ArtifactSummary(
                    id=str(row["id"]),
                    meeting_id=str(row["meeting_id"]),
                    artifact_type=str(row["artifact_type"]),
                    title=str(row["title"]),
                    body_markdown=str(row["body_markdown"] or ""),
                    structured_json=self._json_loads_dict(row["structured_json"]),
                    confidence=float(row["confidence"] if row["confidence"] is not None else 0.0),
                    status=str(row["status"] or "draft"),
                    plugin_id=str(row["plugin_id"] or "unknown"),
                    plugin_version=str(row["plugin_version"] or "unknown"),
                    sources=sources_by_artifact.get(str(row["id"]), []),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return output
