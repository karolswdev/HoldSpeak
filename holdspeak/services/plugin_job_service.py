"""Transport-neutral deferred plugin-job operations (HS-123-07)."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import ConflictError, NotFound


class PluginJobService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _job(job: Any, full: bool = True) -> dict[str, Any]:
        now = datetime.now(); retry = job.status == "queued" and bool(job.last_error) and job.requested_at > now
        data = {"id": job.id, "meeting_id": job.meeting_id, "window_id": job.window_id, "plugin_id": job.plugin_id, "plugin_version": job.plugin_version, "status": job.status, "requested_at": job.requested_at.isoformat(), "updated_at": job.updated_at.isoformat(), "attempts": job.attempts, "last_error": job.last_error}
        if full: data.update({"transcript_hash": job.transcript_hash, "idempotency_key": job.idempotency_key, "retry_scheduled": retry, "next_retry_at": job.requested_at.isoformat() if retry else None})
        return data

    def list(self, principal: Principal, status: str, meeting_id: str | None, limit: int) -> dict[str, Any]:
        return {"jobs": [self._job(j) for j in self._db.plugins.list_plugin_run_jobs(status=status, meeting_id=meeting_id, limit=limit)]}

    def summary(self, principal: Principal) -> dict[str, Any]:
        s = self._db.plugins.get_plugin_run_job_summary()
        return {"total_jobs": s.total_jobs, "queued_jobs": s.queued_jobs, "running_jobs": s.running_jobs, "failed_jobs": s.failed_jobs, "queued_due_jobs": s.queued_due_jobs, "scheduled_retry_jobs": s.scheduled_retry_jobs, "next_retry_at": s.next_retry_at.isoformat() if s.next_retry_at else None}

    def retry(self, principal: Principal, job_id: int) -> dict[str, Any]:
        job = self._db.plugins.get_plugin_run_job(job_id)
        if job is None: raise NotFound("plugin job", str(job_id))
        if str(job.status).strip().lower() == "running": raise ConflictError("Cannot retry a running plugin job")
        self._db.plugins.retry_plugin_run_job(int(job_id), error="Manual retry requested from web UI.", retry_at=datetime.now())
        updated = self._db.plugins.get_plugin_run_job(job_id)
        return {"success": True, "job": self._job(updated, full=False) if updated else None}

    def cancel(self, principal: Principal, job_id: int) -> dict[str, Any]:
        job = self._db.plugins.get_plugin_run_job(job_id)
        if job is None: raise NotFound("plugin job", str(job_id))
        if str(job.status).strip().lower() == "running": raise ConflictError("Cannot cancel a running plugin job")
        self._db.plugins.complete_plugin_run_job(job_id)
        return {"success": True}
