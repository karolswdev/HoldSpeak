"""Deferred-intelligence queue routes: job listing, summary, process, retry."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import _IntelProcessRequest
from ...runtime_support import error_500
from ...context import WebContext

log = get_logger("web.routes.meetings")


def build_intel_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/intel/jobs")
    async def api_list_intel_jobs(
        status: str = "all",
        limit: int = 20,
        history_limit: int = 5,
    ) -> Any:
        """List deferred intelligence jobs."""
        try:
            from ....db import get_database
            from ....config import Config

            db = get_database()
            jobs = db.intel.list_intel_jobs(status=status, limit=limit)
            retry_max_attempts = max(1, int(Config.load().meeting.intel_retry_max_attempts))
            now = datetime.now()
            bounded_history_limit = max(1, min(int(history_limit), 20))
            return JSONResponse(
                {
                    "jobs": [
                        {
                            "meeting_id": job.meeting_id,
                            "status": job.status,
                            "transcript_hash": job.transcript_hash,
                            "requested_at": job.requested_at.isoformat(),
                            "updated_at": job.updated_at.isoformat(),
                            "attempts": job.attempts,
                            "last_error": job.last_error,
                            "meeting_title": job.meeting_title,
                            "started_at": job.started_at.isoformat() if job.started_at else None,
                            "intel_status_detail": job.intel_status_detail,
                            "retry_scheduled": (
                                job.status == "queued"
                                and bool(job.last_error)
                                and job.requested_at > now
                            ),
                            "next_retry_at": (
                                job.requested_at.isoformat()
                                if (
                                    job.status == "queued"
                                    and bool(job.last_error)
                                    and job.requested_at > now
                                )
                                else None
                            ),
                            "retries_remaining": max(0, retry_max_attempts - int(job.attempts)),
                            "retry_max_attempts": retry_max_attempts,
                            "retry_history": [
                                {
                                    "attempt": event.attempt,
                                    "outcome": event.outcome,
                                    "error": event.error,
                                    "retry_at": event.retry_at.isoformat() if event.retry_at else None,
                                    "created_at": event.created_at.isoformat(),
                                }
                                for event in db.intel.list_intel_job_attempts(
                                    job.meeting_id,
                                    limit=bounded_history_limit,
                                )
                            ],
                        }
                        for job in jobs
                    ]
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to list intel jobs")

    @router.get("/api/intel/summary")
    async def api_intel_queue_summary() -> Any:
        """Return aggregate deferred-intel queue telemetry."""
        try:
            from ....db import get_database

            db = get_database()
            summary = db.intel.get_intel_queue_summary()
            return JSONResponse(
                {
                    "total_jobs": summary.total_jobs,
                    "queued_jobs": summary.queued_jobs,
                    "running_jobs": summary.running_jobs,
                    "failed_jobs": summary.failed_jobs,
                    "queued_due_jobs": summary.queued_due_jobs,
                    "scheduled_retry_jobs": summary.scheduled_retry_jobs,
                    "next_retry_at": (
                        summary.next_retry_at.isoformat() if summary.next_retry_at else None
                    ),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load intel queue summary")

    @router.post("/api/intel/process")
    async def api_process_intel_jobs(payload: Optional[_IntelProcessRequest] = None) -> Any:
        """Process queued deferred-intel jobs now."""
        try:
            from ....config import Config
            from ....intel_queue import drain_intel_queue

            cfg = Config.load().meeting
            max_jobs = payload.max_jobs if payload is not None else None
            mode = (payload.mode if payload is not None else None) or "respect_backoff"
            normalized_mode = str(mode).strip().lower()
            if normalized_mode not in {"respect_backoff", "retry_now"}:
                return JSONResponse(
                    {"success": False, "error": "mode must be respect_backoff or retry_now"},
                    status_code=400,
                )
            include_scheduled = normalized_mode == "retry_now"

            # HS-56-04: when deferred intel completes, the meeting's open
            # work becomes knowable — the presence mascot's aftercare card.
            def _on_meeting_ready(meeting_id: str) -> None:
                # Phase 72 split surfaced a latent NameError here: the handler
                # never imported get_database, so this callback crashed whenever
                # deferred intel completed (HS-56-04's aftercare_ready event
                # never fired through this path). Real bug, fixed in place.
                from ....db import get_database
                from ....meeting_aftercare import build_aftercare_ready_event

                event = build_aftercare_ready_event(get_database(), meeting_id)
                if event is not None:
                    ctx.broadcast("aftercare_ready", event)

            processed = drain_intel_queue(
                cfg.intel_realtime_model,
                on_meeting_ready=_on_meeting_ready,
                provider=cfg.intel_provider,
                cloud_model=cfg.intel_cloud_model,
                cloud_api_key_env=cfg.intel_cloud_api_key_env,
                cloud_base_url=cfg.intel_cloud_base_url,
                cloud_reasoning_effort=cfg.intel_cloud_reasoning_effort,
                cloud_store=cfg.intel_cloud_store,
                retry_base_seconds=cfg.intel_retry_base_seconds,
                retry_max_seconds=cfg.intel_retry_max_seconds,
                retry_max_attempts=cfg.intel_retry_max_attempts,
                include_scheduled=include_scheduled,
                max_jobs=max_jobs,
            )
            return JSONResponse(
                {
                    "success": True,
                    "processed": processed,
                    "mode": normalized_mode,
                }
            )
        except Exception as e:
            log.error(f"Failed to process intel jobs: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/intel/retry/{meeting_id}")
    async def api_retry_intel_job(meeting_id: str) -> Any:
        """Requeue deferred intelligence for a specific meeting."""
        try:
            from ....db import get_database

            db = get_database()
            ok = db.intel.requeue_intel_job(meeting_id, reason="Manual retry requested from web UI.")
            if not ok:
                return JSONResponse({"success": False, "error": "Meeting not found or transcript is empty"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to retry intel job: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
