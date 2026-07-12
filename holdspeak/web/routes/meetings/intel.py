"""Deferred-intelligence queue routes: job listing, summary, process, retry."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....db.intel import MANUAL_INTEL_RETRY_REASON, ROUTED_INTEL_RETRY_REASON
from ....logging_config import get_logger
from ....web_requests import _IntelProcessRequest
from ...runtime_support import error_500
from ...context import WebContext

log = get_logger("web.routes.meetings")


def _intel_recovery_payload(db: Any, meeting_id: str) -> Optional[dict[str, Any]]:
    """Project persisted Meeting/intel work into one truthful recovery contract."""
    meeting = db.meetings.get_meeting(meeting_id)
    if meeting is None:
        return None

    job = db.intel.get_intel_job(meeting_id)
    artifacts = db.plugins.list_artifacts(meeting_id, limit=2000)
    meeting_state = str(meeting.intel_status or "disabled").strip().lower()
    job_state = str(job.status).strip().lower() if job is not None else None
    effective_state = (
        meeting_state
        if meeting_state in {"partial", "skipped"}
        else job_state or meeting_state
    )
    visible = bool(job) or meeting_state in {
        "queued",
        "running",
        "error",
        "failed",
        "partial",
        "skipped",
    }

    if effective_state == "running":
        headline = "Meeting saved · intelligence running"
    elif effective_state == "queued":
        headline = "Meeting saved · intelligence queued"
    elif meeting_state == "skipped":
        headline = "Meeting saved · intelligence skipped"
    else:
        headline = "Meeting saved · intelligence incomplete"

    segment_count = len(meeting.segments)
    completed: list[dict[str, str]] = [
        {"label": "Meeting", "detail": "Saved"},
        {
            "label": "Transcript",
            "detail": (
                f"{segment_count} saved "
                f"{'segment' if segment_count == 1 else 'segments'}"
            ),
        },
    ]
    if meeting.intel is not None:
        completed.append(
            {
                "label": "Meeting analysis",
                "detail": "Summary, topics, and action items saved",
            }
        )
    if artifacts:
        completed.append(
            {
                "label": "Artifacts",
                "detail": (
                    f"{len(artifacts)} saved "
                    f"{'artifact' if len(artifacts) == 1 else 'artifacts'}"
                ),
            }
        )

    if meeting.intel is not None and meeting_state in {"partial", "skipped"}:
        remaining_label = "Routed meeting intelligence"
    elif meeting.intel is not None:
        remaining_label = "Remaining meeting intelligence"
    else:
        remaining_label = "Summary, topics, action items, and routed artifacts"
    status_detail = (
        (job.last_error if job is not None else None)
        or meeting.intel_status_detail
        or "Meeting intelligence did not finish."
    )
    running = effective_state == "running"
    ready = meeting_state == "ready" and job is None
    retry_already_requested = effective_state == "queued" and status_detail in {
        MANUAL_INTEL_RETRY_REASON,
        ROUTED_INTEL_RETRY_REASON,
    }
    return {
        "meeting_id": meeting_id,
        "visible": visible,
        "state": effective_state,
        "headline": headline,
        "completed": completed,
        "remaining": {
            "label": remaining_label,
            "detail": str(status_detail),
        },
        "job": (
            {
                "status": job.status,
                "attempts": job.attempts,
                "requested_at": job.requested_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            }
            if job is not None
            else None
        ),
        "actions": {
            "retry": visible
            and not running
            and not ready
            and not retry_already_requested,
            "skip": visible
            and not running
            and not ready
            and meeting_state != "skipped",
        },
    }


def _broadcast_runtime_queue(ctx: WebContext, db: Any) -> None:
    """Publish queue truth after an owner recovery decision."""
    try:
        from ....intel_queue import build_runtime_queue_frame

        ctx.broadcast("runtime_queue", build_runtime_queue_frame(db))
    except Exception as exc:
        log.debug(f"runtime_queue frame dropped: {exc}")


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

            # HS-84-01: deferred jobs run where the assigned RuntimeProfile says
            # (dangling/none ⇒ the legacy intel_cloud_* shape, byte-identical).
            from ....intel.providers import effective_intel_cloud

            effective_cloud = effective_intel_cloud(cfg)

            processed = drain_intel_queue(
                cfg.intel_realtime_model,
                on_meeting_ready=_on_meeting_ready,
                provider=cfg.intel_provider,
                cloud_model=effective_cloud.model,
                cloud_api_key_env=effective_cloud.api_key_env,
                cloud_base_url=effective_cloud.base_url,
                cloud_reasoning_effort=cfg.intel_cloud_reasoning_effort,
                cloud_store=cfg.intel_cloud_store,
                retry_base_seconds=cfg.intel_retry_base_seconds,
                retry_max_seconds=cfg.intel_retry_max_seconds,
                retry_max_attempts=cfg.intel_retry_max_attempts,
                include_scheduled=include_scheduled,
                max_jobs=max_jobs,
            )

            # HS-77-02: the queue changed — broadcast the real truth.
            try:
                from ....db import get_database
                from ....intel_queue import build_runtime_queue_frame

                ctx.broadcast("runtime_queue", build_runtime_queue_frame(get_database()))
            except Exception as exc:
                log.debug(f"runtime_queue frame dropped: {exc}")
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
            outcome = db.intel.request_intel_retry(
                meeting_id,
                reason=MANUAL_INTEL_RETRY_REASON,
            )
            if outcome == "missing":
                return JSONResponse(
                    {"success": False, "error": "Meeting not found"},
                    status_code=404,
                )
            if outcome == "empty":
                return JSONResponse(
                    {"success": False, "error": "Meeting transcript is empty"},
                    status_code=409,
                )
            if outcome == "running":
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Meeting intelligence is already running",
                    },
                    status_code=409,
                )
            if outcome == "ready":
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Meeting intelligence is already ready",
                    },
                    status_code=409,
                )
            _broadcast_runtime_queue(ctx, db)
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to retry intel job: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/meetings/{meeting_id}/intel-recovery")
    async def api_get_meeting_intel_recovery(meeting_id: str) -> Any:
        """Name retained and remaining Meeting intelligence work."""
        try:
            from ....db import get_database

            recovery = _intel_recovery_payload(get_database(), meeting_id)
            if recovery is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            return JSONResponse(recovery)
        except Exception as e:
            return error_500(e, log, "Failed to load Meeting intelligence recovery")

    @router.post("/api/meetings/{meeting_id}/intel-recovery/retry")
    async def api_retry_meeting_intel_recovery(meeting_id: str) -> Any:
        """Retry only the Meeting intelligence that remains incomplete."""
        try:
            from ....db import get_database

            db = get_database()
            outcome = db.intel.request_intel_retry(
                meeting_id,
                reason=MANUAL_INTEL_RETRY_REASON,
            )
            errors = {
                "missing": (404, "Meeting not found"),
                "empty": (409, "Meeting transcript is empty; no intelligence can run"),
                "running": (409, "Meeting intelligence is already running"),
                "ready": (409, "Meeting intelligence is already ready"),
            }
            if outcome in errors:
                status_code, error = errors[outcome]
                return JSONResponse(
                    {"success": False, "error": error},
                    status_code=status_code,
                )
            _broadcast_runtime_queue(ctx, db)
            return JSONResponse(
                {
                    "success": True,
                    "recovery": _intel_recovery_payload(db, meeting_id),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to retry Meeting intelligence")

    @router.post("/api/meetings/{meeting_id}/intel-recovery/skip")
    async def api_skip_meeting_intel_recovery(meeting_id: str) -> Any:
        """Keep completed Meeting work and skip non-running remainder."""
        try:
            from ....db import get_database

            db = get_database()
            outcome = db.intel.skip_remaining_intel(meeting_id)
            errors = {
                "missing": (404, "Meeting not found"),
                "running": (
                    409,
                    "Meeting intelligence is running; wait for it to finish before skipping",
                ),
                "ready": (409, "Meeting intelligence is already ready"),
            }
            if outcome in errors:
                status_code, error = errors[outcome]
                return JSONResponse(
                    {"success": False, "error": error},
                    status_code=status_code,
                )
            _broadcast_runtime_queue(ctx, db)
            return JSONResponse(
                {
                    "success": True,
                    "recovery": _intel_recovery_payload(db, meeting_id),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to skip Meeting intelligence")

    return router
