"""Deferred plugin-job queue routes — HS-34-02 split of `activity.py`.

`/api/plugin-jobs*` (list/summary/process/retry-now/cancel). This is the deferred
MIR plugin-run queue API; it lived in `activity.py` but is its own domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import _PluginJobProcessRequest
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.activity")


def build_plugin_jobs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/plugin-jobs")
    async def api_list_plugin_jobs(
        status: str = "all",
        meeting_id: Optional[str] = None,
        limit: int = 200,
    ) -> Any:
        """List deferred MIR plugin-run queue jobs."""
        try:
            from ....db import get_database

            db = get_database()
            jobs = db.plugins.list_plugin_run_jobs(status=status, meeting_id=meeting_id, limit=limit)
            now = datetime.now()
            return JSONResponse(
                {
                    "jobs": [
                        {
                            "id": job.id,
                            "meeting_id": job.meeting_id,
                            "window_id": job.window_id,
                            "plugin_id": job.plugin_id,
                            "plugin_version": job.plugin_version,
                            "transcript_hash": job.transcript_hash,
                            "idempotency_key": job.idempotency_key,
                            "status": job.status,
                            "requested_at": job.requested_at.isoformat(),
                            "updated_at": job.updated_at.isoformat(),
                            "attempts": job.attempts,
                            "last_error": job.last_error,
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
                        }
                        for job in jobs
                    ]
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to list deferred plugin jobs")

    @router.get("/api/plugin-jobs/summary")
    async def api_plugin_jobs_summary() -> Any:
        """Return aggregate telemetry for deferred MIR plugin-run queue."""
        try:
            from ....db import get_database

            db = get_database()
            summary = db.plugins.get_plugin_run_job_summary()
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
            return error_500(e, log, "Failed to load deferred plugin-job summary")

    @router.post("/api/plugin-jobs/process")
    async def api_process_plugin_jobs(payload: Optional[_PluginJobProcessRequest] = None) -> Any:
        """Process deferred plugin-run queue jobs now."""
        if ctx.on_process_plugin_jobs is None:
            return JSONResponse(
                {"success": False, "error": "Deferred plugin queue processing not supported"},
                status_code=501,
            )
        max_jobs = payload.max_jobs if payload is not None else None
        if max_jobs is not None and int(max_jobs) <= 0:
            return JSONResponse(
                {"success": False, "error": "max_jobs must be greater than 0"},
                status_code=400,
            )
        mode = (payload.mode if payload is not None else None) or "respect_backoff"
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in {"respect_backoff", "retry_now"}:
            return JSONResponse(
                {"success": False, "error": "mode must be respect_backoff or retry_now"},
                status_code=400,
            )
        include_scheduled = normalized_mode == "retry_now"
        try:
            result = ctx.on_process_plugin_jobs(
                max_jobs=max_jobs,
                include_scheduled=include_scheduled,
            )
            payload_data = dict(result) if isinstance(result, dict) else {"processed": int(result)}
            payload_data["mode"] = normalized_mode
            payload_data["success"] = True
            ctx.broadcast("plugin_jobs_processed", payload_data)
            return JSONResponse(payload_data)
        except Exception as e:
            log.error(f"Failed to process deferred plugin jobs: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/plugin-jobs/{job_id}/retry-now")
    async def api_retry_plugin_job_now(job_id: int) -> Any:
        """Reschedule one deferred MIR plugin-run job for immediate retry."""
        try:
            from ....db import get_database

            db = get_database()
            job = db.plugins.get_plugin_run_job(job_id) if hasattr(db.plugins, "get_plugin_run_job") else None
            if job is None:
                return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
            if str(job.status).strip().lower() == "running":
                return JSONResponse(
                    {"success": False, "error": "Cannot retry a running plugin job"},
                    status_code=409,
                )

            db.plugins.retry_plugin_run_job(
                int(job_id),
                error="Manual retry requested from web UI.",
                retry_at=datetime.now(),
            )
            updated = db.plugins.get_plugin_run_job(job_id) if hasattr(db.plugins, "get_plugin_run_job") else None
            return JSONResponse(
                {
                    "success": True,
                    "job": (
                        {
                            "id": updated.id,
                            "meeting_id": updated.meeting_id,
                            "window_id": updated.window_id,
                            "plugin_id": updated.plugin_id,
                            "plugin_version": updated.plugin_version,
                            "status": updated.status,
                            "requested_at": updated.requested_at.isoformat(),
                            "updated_at": updated.updated_at.isoformat(),
                            "attempts": updated.attempts,
                            "last_error": updated.last_error,
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to retry deferred plugin job {job_id}: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/plugin-jobs/{job_id}/cancel")
    async def api_cancel_plugin_job(job_id: int) -> Any:
        """Cancel one deferred MIR plugin-run job."""
        try:
            from ....db import get_database

            db = get_database()
            job = db.plugins.get_plugin_run_job(job_id) if hasattr(db.plugins, "get_plugin_run_job") else None
            if job is None:
                return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
            if str(job.status).strip().lower() == "running":
                return JSONResponse(
                    {"success": False, "error": "Cannot cancel a running plugin job"},
                    status_code=409,
                )
            db.plugins.complete_plugin_run_job(job_id)
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to cancel deferred plugin job {job_id}: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
