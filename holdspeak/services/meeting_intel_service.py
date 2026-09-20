"""Transport-neutral deferred meeting-intelligence operations."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from datetime import datetime
from typing import Any, Callable
from ..config import Config
from ..db.core import Database
from ..db.intel import MANUAL_INTEL_RETRY_REASON, ROUTED_INTEL_RETRY_REASON
from ..intel_queue import build_runtime_queue_frame, drain_intel_queue
from ..meeting_aftercare import build_aftercare_ready_event
from ..principals import Principal
from .errors import ConflictError, NotFound, ValidationError
from .meeting_route_projection import project_route, require_expected_selection

@observe_service
class MeetingIntelService:
    def __init__(self, db: Database, notify: Callable[[str, Any], None] | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db, self._notify = db, notify
        self._observer = observer or NullObserver()
    def _broadcast_queue(self) -> None:
        if self._notify: self._notify("runtime_queue", build_runtime_queue_frame(self._db))

    def _conflict(
        self,
        meeting_id: str,
        detail: str,
        *,
        code: str,
        run_receipt: dict[str, Any] | None = None,
        planned_route: dict[str, Any] | None = None,
    ) -> ConflictError:
        """Build a conflict with the same read model used by all transports."""
        if planned_route is None:
            planned_route = project_route(
                self._db, invocation_id=f"meeting:{meeting_id}:conflict"
            )
        if run_receipt is None:
            run_receipt = self._db.intel.get_run_receipt(meeting_id)
        exc = ConflictError(detail, code=code)
        exc.context.update(
            {
                "planned_route": planned_route,
                "current_planned_route": planned_route,
                "run_receipt": run_receipt,
            }
        )
        return exc

    def _guard_gesture_state(self, meeting_id: str, expected_selection_hash: str | None = None) -> str:
        """Refuse protected work before resolving or recording a route fence."""
        state = self._db.intel.get_gesture_state(meeting_id)
        details = {
            "reserved": "Meeting intelligence is awaiting Stop settlement",
            "running": "Meeting intelligence is already running",
            "queued": "Meeting intelligence is already queued",
            "ready": "Meeting intelligence is already ready",
        }
        # An existing queued owner may still be retried with the currently
        # disclosed hash.  A missing hash must stop before route resolution;
        # a supplied stale hash proceeds to the route fence, whose writer
        # epoch preserves the queued owner without adding a refusal leaf.
        if state == "queued" and str(expected_selection_hash or "").strip():
            return state
        if state in details:
            raise self._conflict(meeting_id, details[state], code=state)
        return state
    def list_jobs(self, principal: Principal, filters: dict[str, Any]) -> dict[str, Any]:
        status, limit = filters.get("status", "all"), filters.get("limit", 20)
        history_limit = max(1, min(int(filters.get("history_limit", 5)), 20))
        retry_max = max(1, int(Config.load().meeting.intel_retry_max_attempts)); now = datetime.now()
        jobs = self._db.intel.list_intel_jobs(status=status, limit=limit)
        return {"jobs": [{"job_id": j.job_id, "origin_job_id": j.origin_job_id, "work_descriptor_sha256": j.work_descriptor_sha256, "claim_id": j.claim_id, "parent_operation_id": j.parent_operation_id, "bundle_id": j.bundle_id, "bundle_sha256": j.bundle_sha256, "lifecycle_posture": j.lifecycle_posture, "meeting_id": j.meeting_id, "status": j.status, "transcript_hash": j.transcript_hash, "requested_at": j.requested_at.isoformat(), "updated_at": j.updated_at.isoformat(), "attempts": j.attempts, "last_error": j.last_error, "planned_route": j.planned_route, "run_receipt": j.run_receipt, "meeting_title": j.meeting_title, "started_at": j.started_at.isoformat() if j.started_at else None, "intel_status_detail": j.intel_status_detail, "retry_scheduled": j.status == "queued" and bool(j.last_error) and j.requested_at > now, "next_retry_at": j.requested_at.isoformat() if j.status == "queued" and bool(j.last_error) and j.requested_at > now else None, "retries_remaining": max(0, retry_max - int(j.attempts)), "retry_max_attempts": retry_max, "retry_history": [{"job_id": e.job_id, "event_kind": e.event_kind, "attempt": e.attempt, "outcome": e.outcome, "error": e.error, "retry_at": e.retry_at.isoformat() if e.retry_at else None, "created_at": e.created_at.isoformat()} for e in self._db.intel.list_intel_job_attempts(j.meeting_id, limit=history_limit)]} for j in jobs]}
    def queue_summary(self, principal: Principal) -> dict[str, Any]:
        s = self._db.intel.get_intel_queue_summary()
        return {"total_jobs": s.total_jobs, "queued_jobs": s.queued_jobs, "running_jobs": s.running_jobs, "failed_jobs": s.failed_jobs, "queued_due_jobs": s.queued_due_jobs, "scheduled_retry_jobs": s.scheduled_retry_jobs, "next_retry_at": s.next_retry_at.isoformat() if s.next_retry_at else None}
    def process_jobs(self, principal: Principal, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}; mode = str(payload.get("mode") or "respect_backoff").strip().lower()
        if mode not in {"respect_backoff", "retry_now"}: raise ValidationError("mode must be respect_backoff or retry_now")
        cfg = Config.load().meeting
        def ready(meeting_id: str) -> None:
            event = build_aftercare_ready_event(self._db, meeting_id)
            if event and self._notify: self._notify("aftercare_ready", event)
        processed = drain_intel_queue(cfg.intel_realtime_model, on_meeting_ready=ready, provider=cfg.intel_provider, retry_base_seconds=cfg.intel_retry_base_seconds, retry_max_seconds=cfg.intel_retry_max_seconds, retry_max_attempts=cfg.intel_retry_max_attempts, include_scheduled=mode == "retry_now", max_jobs=payload.get("max_jobs"))
        self._broadcast_queue(); return {"success": True, "processed": processed, "mode": mode}
    def _route_for_gesture(self, meeting_id: str, expected_selection_hash: str | None) -> dict[str, Any]:
        route = project_route(self._db, invocation_id=f"meeting:{meeting_id}")
        try:
            require_expected_selection(route, expected_selection_hash)
        except ConflictError as exc:
            receipt = self._db.intel.record_route_refusal(
                meeting_id,
                planned_route=route,
                expected_selection_hash=expected_selection_hash,
                reason=str(exc),
            )
            raise self._conflict(
                meeting_id,
                str(exc),
                code=exc.code,
                run_receipt=receipt,
                planned_route=route,
            ) from exc
        return route

    def _retry(self, meeting_id: str, *, recovery: bool, expected_selection_hash: str | None) -> dict[str, Any]:
        # Preserve the settled no-assignment/no-transcript refusal before route
        # disclosure checks.  This keeps the named recording refusal owned by 02
        # while every actual run with transcript bytes binds a disclosed route.
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        state = self._guard_gesture_state(meeting_id, expected_selection_hash)
        if state == "empty":
            outcome = self._db.intel.request_intel_retry(meeting_id, reason=MANUAL_INTEL_RETRY_REASON)
        else:
            route = self._route_for_gesture(meeting_id, expected_selection_hash)
            outcome = self._db.intel.request_intel_retry(
                meeting_id, reason=MANUAL_INTEL_RETRY_REASON, planned_route=route,
            )
        errors = {"missing": "Meeting not found", "empty": "Meeting transcript is empty; no intelligence can run" if recovery else "Meeting transcript is empty", "reserved": "Meeting intelligence is awaiting Stop settlement", "running": "Meeting intelligence is already running", "ready": "Meeting intelligence is already ready"}
        if outcome in errors:
            if outcome == "missing": raise NotFound("meeting", meeting_id)
            if outcome == "empty":
                meeting = self._db.meetings.get_meeting(meeting_id)
                detail = getattr(meeting, "transcription_status_detail", None) if meeting else None
                reason = str(detail.get("reason_code") or "").strip() if isinstance(detail, dict) else ""
                if reason:
                    raise self._conflict(
                        meeting_id,
                        f"Meeting transcription is not available: {reason.replace('_', ' ')}.",
                        code=reason,
                    )
            raise self._conflict(meeting_id, errors[outcome], code=outcome)
        self._broadcast_queue(); return {"success": True, **({"recovery": self.get_recovery(None, meeting_id)} if recovery else {})}
    def retry_job(self, principal: Principal, meeting_id: str, *, expected_selection_hash: str | None = None) -> dict[str, Any]: return self._retry(meeting_id, recovery=False, expected_selection_hash=expected_selection_hash)

    def run_intelligence(self, principal: Principal, meeting_id: str, *, expected_selection_hash: str | None = None) -> dict[str, Any]:
        """HS-170-04: enqueue a fresh intelligence job for a meeting.

        Named verb for the face's 'Run intelligence' button. Returns
        ``{jobId, state, host, drainer, expectedWithinSeconds}`` where host is
        the assigned model's egress host at the point of decision (Article III).

        HS-200-42: the verb enqueues, and until the hub grew a drainer nothing
        executed what it enqueued (audit 2026-09-13 §3.1) — so this returned
        ``queued`` while the queue was never drained. It now wakes the hub's
        drainer and reports honestly whether one exists: ``drainer`` is
        ``"running"`` or ``"absent"``, and ``expectedWithinSeconds`` is 0 when
        a woken drainer will pick the job up immediately and ``None`` when
        nothing will.
        """
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        route = None
        state = self._guard_gesture_state(meeting_id, expected_selection_hash)
        if state != "empty":
            route = self._route_for_gesture(meeting_id, expected_selection_hash)
        outcome = self._db.intel.request_intel_retry(
            meeting_id, reason="Run intelligence", planned_route=route,
        )
        errors = {
            "missing": "Meeting not found",
            "empty": "Meeting has no transcript",
            "reserved": "Meeting intelligence is awaiting Stop settlement",
            "running": "Meeting intelligence is already running",
            "ready": "Meeting intelligence is already ready",
        }
        if outcome in errors:
            if outcome == "missing":
                raise NotFound("meeting", meeting_id)
            if outcome == "empty":
                detail = getattr(meeting, "transcription_status_detail", None)
                reason = str(detail.get("reason_code") or "").strip() if isinstance(detail, dict) else ""
                if reason:
                    raise self._conflict(
                        meeting_id,
                        f"Meeting transcription is not available: {reason.replace('_', ' ')}.",
                        code=reason,
                    )
            raise self._conflict(meeting_id, errors[outcome], code=outcome)
        self._broadcast_queue()
        host = (route or {}).get("legs", [{}])[0].get("host") if route else None
        job = self._db.intel.get_intel_job(meeting_id)
        # Wake the hub drainer so the job runs now rather than at the next
        # poll. `woken` is False when there is no drainer in this process.
        try:
            from ..intel_queue_conductor import (
                drainer_state,
                wake_intel_queue_conductor,
            )

            woken = wake_intel_queue_conductor()
            drainer = drainer_state()
        except Exception:
            woken, drainer = False, "absent"
        return {
            "jobId": job.job_id if job else meeting_id,
            "state": "queued",
            "host": host,
            "drainer": drainer,
            "expectedWithinSeconds": 0 if (woken and drainer == "running") else None,
            "planned_route": job.planned_route if job and job.planned_route is not None else route,
            "run_receipt": job.run_receipt if job else self._db.intel.get_run_receipt(meeting_id),
        }
    def get_recovery(self, principal: Principal | None, meeting_id: str) -> dict[str, Any]:
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None: raise NotFound("meeting", meeting_id)
        job = self._db.intel.get_intel_job(meeting_id); artifacts = self._db.plugins.list_artifacts(meeting_id, limit=2000)
        meeting_state = str(meeting.intel_status or "disabled").strip().lower(); job_state = str(job.status).strip().lower() if job else None
        reserved_handoff = (
            self._db.intel.has_unsettled_stop_reservation(meeting_id)
            or self._db.intel.has_compatibility_cutover_reservation(meeting_id)
        )
        state = meeting_state if meeting_state in {"partial", "skipped"} else job_state or meeting_state; visible = bool(job) or meeting_state in {"queued","running","error","failed","partial","skipped"}
        headline = "Meeting saved · intelligence running" if state == "running" else "Meeting saved · intelligence queued" if state == "queued" else "Meeting saved · intelligence skipped" if meeting_state == "skipped" else "Meeting saved · intelligence incomplete"
        completed = [{"label":"Meeting","detail":"Saved"},{"label":"Transcript","detail":f"{len(meeting.segments)} saved {'segment' if len(meeting.segments)==1 else 'segments'}"}]
        if meeting.intel is not None: completed.append({"label":"Meeting analysis","detail":"Summary, topics, and action items saved"})
        if artifacts: completed.append({"label":"Artifacts","detail":f"{len(artifacts)} saved {'artifact' if len(artifacts)==1 else 'artifacts'}"})
        detail = (job.last_error if job else None) or meeting.intel_status_detail or "Meeting intelligence did not finish."
        retry_requested = state == "queued" and detail in {MANUAL_INTEL_RETRY_REASON, ROUTED_INTEL_RETRY_REASON}
        return {"meeting_id":meeting_id,"visible":visible,"state":state,"headline":headline,"completed":completed,"planned_route":project_route(self._db, invocation_id=f"meeting:{meeting_id}"),"run_receipt":self._db.intel.get_run_receipt(meeting_id),"remaining":{"label":"Routed meeting intelligence" if meeting.intel is not None and meeting_state in {"partial","skipped"} else "Remaining meeting intelligence" if meeting.intel is not None else "Summary, topics, action items, and routed artifacts","detail":str(detail)},"job":{"status":job.status,"attempts":job.attempts,"requested_at":job.requested_at.isoformat(),"updated_at":job.updated_at.isoformat(),"planned_route":job.planned_route,"run_receipt":job.run_receipt} if job else None,"actions":{"retry":not reserved_handoff and visible and state != "running" and not (meeting_state == "ready" and job is None) and not retry_requested,"skip":not reserved_handoff and visible and state != "running" and not (meeting_state == "ready" and job is None) and meeting_state != "skipped"}}
    def retry_recovery(self, principal: Principal, meeting_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]: return self._retry(meeting_id, recovery=True, expected_selection_hash=(payload or {}).get("expected_selection_hash"))
    def skip_recovery(self, principal: Principal, meeting_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        outcome = self._db.intel.skip_remaining_intel(meeting_id)
        errors = {"missing":"Meeting not found", "reserved":"Meeting intelligence is awaiting Stop settlement", "running":"Meeting intelligence is running; wait for it to finish before skipping", "ready":"Meeting intelligence is already ready"}
        if outcome in errors:
            if outcome == "missing": raise NotFound("meeting", meeting_id)
            raise ConflictError(errors[outcome], code=outcome)
        self._broadcast_queue(); return {"success":True,"recovery":self.get_recovery(principal, meeting_id)}
