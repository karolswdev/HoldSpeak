"""Per-meeting MIR insight reads: intent timeline, plugin runs, artifacts."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...runtime_support import error_500
from ...context import WebContext

log = get_logger("web.routes.meetings")


def build_insights_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/meetings/{meeting_id}/intent-timeline")
    async def api_get_meeting_intent_timeline(
        meeting_id: str,
        limit: int = 200,
    ) -> Any:
        """Get persisted MIR intent timeline for one meeting."""
        try:
            from ....db import get_database
            from ....intent_timeline import detect_intent_transitions

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            windows = db.plugins.list_intent_windows(meeting_id, limit=limit)
            transitions = detect_intent_transitions(
                [(window.window_id, list(window.active_intents)) for window in windows]
            )
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "windows": [
                        {
                            "meeting_id": window.meeting_id,
                            "window_id": window.window_id,
                            "start_seconds": window.start_seconds,
                            "end_seconds": window.end_seconds,
                            "transcript_hash": window.transcript_hash,
                            "transcript_excerpt": window.transcript_excerpt,
                            "profile": window.profile,
                            "threshold": window.threshold,
                            "active_intents": window.active_intents,
                            "intent_scores": window.intent_scores,
                            "override_intents": window.override_intents,
                            "tags": window.tags,
                            "metadata": window.metadata,
                            "created_at": window.created_at.isoformat(),
                            "updated_at": window.updated_at.isoformat(),
                        }
                        for window in windows
                    ],
                    "transitions": transitions,
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting intent timeline")

    @router.get("/api/meetings/{meeting_id}/plugin-runs")
    async def api_get_meeting_plugin_runs(
        meeting_id: str,
        limit: int = 500,
        window_id: Optional[str] = None,
    ) -> Any:
        """Get persisted MIR plugin-run history for one meeting."""
        try:
            from ....db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            runs = db.plugins.list_plugin_runs(meeting_id, window_id=window_id, limit=limit)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "window_id": window_id,
                    "runs": [
                        {
                            "id": run.id,
                            "meeting_id": run.meeting_id,
                            "window_id": run.window_id,
                            "plugin_id": run.plugin_id,
                            "plugin_version": run.plugin_version,
                            "status": run.status,
                            "idempotency_key": run.idempotency_key,
                            "duration_ms": run.duration_ms,
                            "output": run.output,
                            "error": run.error,
                            "deduped": run.deduped,
                            "created_at": run.created_at.isoformat(),
                            "updated_at": run.updated_at.isoformat(),
                        }
                        for run in runs
                    ],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting plugin runs")

    @router.get("/api/meetings/{meeting_id}/artifacts")
    async def api_get_meeting_artifacts(
        meeting_id: str,
        limit: int = 200,
    ) -> Any:
        """Get synthesized artifacts and lineage for one meeting."""
        try:
            from ....db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            artifacts = db.plugins.list_artifacts(meeting_id, limit=limit)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "artifacts": [
                        {
                            "id": artifact.id,
                            "meeting_id": artifact.meeting_id,
                            "artifact_type": artifact.artifact_type,
                            "title": artifact.title,
                            "body_markdown": artifact.body_markdown,
                            "structured_json": artifact.structured_json,
                            "confidence": artifact.confidence,
                            "status": artifact.status,
                            "plugin_id": artifact.plugin_id,
                            "plugin_version": artifact.plugin_version,
                            "sources": artifact.sources,
                            "created_at": artifact.created_at.isoformat(),
                            "updated_at": artifact.updated_at.isoformat(),
                        }
                        for artifact in artifacts
                    ],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting artifacts")

    return router
