"""Deferred meeting intelligence queue processing."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from typing import Optional
from urllib import request as urlrequest

from .db import get_database
from .intel import MeetingIntel, get_intel_runtime_status
from .logging_config import get_logger
from .meeting_session import IntelSnapshot

log = get_logger("intel_queue")

RETRY_BASE_SECONDS = 30
RETRY_MAX_SECONDS = 900
RETRY_MAX_ATTEMPTS = 6
RETRY_FAILURE_ALERT_PERCENT = 50.0
RETRY_FAILURE_HYSTERESIS_MINUTES = 5.0
RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS = 5.0

RESOLVED_PLUGIN_STATUSES = frozenset({"success", "proposed", "deduped", "skipped"})


def build_runtime_queue_frame(db) -> dict:
    """The REAL queue truth for the web's Queue HUD (HS-77-02).

    Composes the deferred-intel queue's listable jobs + aggregate summary
    into one `runtime_queue` frame. This is the feed the HUD's header
    comment said did not exist; live non-queue activity (a recording, a
    dictation) stays derived from `runtime_activity`/`intel_status`.
    """
    summary = db.intel.get_intel_queue_summary()
    jobs = []
    for job in db.intel.list_intel_jobs(limit=20):
        jobs.append({
            "id": f"intelq:{job.meeting_id}",
            "meeting_id": job.meeting_id,
            "label": getattr(job, "meeting_title", "") or job.meeting_id,
            "status": job.status,
            "attempts": int(getattr(job, "attempts", 0) or 0),
        })
    return {
        "jobs": jobs,
        "queued": int(summary.queued_jobs or 0),
        "running": int(summary.running_jobs or 0),
        "failed": int(summary.failed_jobs or 0),
        "scheduled_retries": int(summary.scheduled_retry_jobs or 0),
        "next_retry_at": (
            summary.next_retry_at.isoformat() if summary.next_retry_at else None
        ),
    }


def _compute_retry_delay_seconds(
    attempt: int,
    *,
    base_seconds: int = RETRY_BASE_SECONDS,
    max_seconds: int = RETRY_MAX_SECONDS,
) -> int:
    """Compute exponential backoff delay for a failed deferred-intel attempt."""
    exponent = max(0, int(attempt) - 1)
    delay = int(base_seconds) * (2 ** exponent)
    return min(int(max_seconds), delay)


def _retry_or_fail_job(
    db,
    job,
    error: str,
    *,
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay_seconds: int = RETRY_BASE_SECONDS,
    max_delay_seconds: int = RETRY_MAX_SECONDS,
) -> None:
    """Requeue a failed job with backoff, or mark it terminal after max attempts."""
    if int(job.attempts) >= int(max_attempts):
        db.intel.record_intel_job_attempt(
            job.meeting_id,
            attempt=int(job.attempts),
            outcome="terminal_failure",
            error=error,
            retry_at=None,
        )
        db.intel.fail_intel_job(
            job.meeting_id,
            f"Deferred intel failed after {job.attempts} attempt(s): {error}",
        )
        return

    delay = _compute_retry_delay_seconds(
        int(job.attempts),
        base_seconds=base_delay_seconds,
        max_seconds=max_delay_seconds,
    )
    retry_at = datetime.now() + timedelta(seconds=delay)
    db.intel.retry_intel_job(
        job.meeting_id,
        error,
        retry_at=retry_at,
        attempt=int(job.attempts),
        max_attempts=int(max_attempts),
    )
    db.intel.record_intel_job_attempt(
        job.meeting_id,
        attempt=int(job.attempts),
        outcome="scheduled_retry",
        error=error,
        retry_at=retry_at,
    )
    log.warning(
        "Deferred intel failed for meeting %s (attempt %s/%s): retrying in %ss",
        job.meeting_id,
        job.attempts,
        max_attempts,
        delay,
    )


def _compute_failure_rate_percent(*, total_jobs: int, failed_jobs: int) -> float:
    total = max(0, int(total_jobs))
    if total == 0:
        return 0.0
    failed = max(0, int(failed_jobs))
    return (failed / total) * 100.0


def process_next_intel_job(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    on_meeting_ready=None,
    cloud_model: str = "gpt-5-mini",
    cloud_api_key_env: str = "OPENAI_API_KEY",
    cloud_base_url: Optional[str] = None,
    cloud_reasoning_effort: Optional[str] = None,
    cloud_store: bool = False,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
    include_scheduled: bool = False,
) -> bool:
    """Process a single queued intelligence job, if available."""
    runtime_kwargs = {
        "provider": provider,
        "cloud_model": cloud_model,
        "cloud_api_key_env": cloud_api_key_env,
        "cloud_base_url": cloud_base_url,
    }
    if model_path:
        runtime_ok, runtime_reason = get_intel_runtime_status(model_path, **runtime_kwargs)
    else:
        runtime_ok, runtime_reason = get_intel_runtime_status(**runtime_kwargs)

    if not runtime_ok:
        log.debug(f"Deferred intel queue paused: {runtime_reason}")
        return False

    db = get_database()
    job = db.intel.claim_next_intel_job(include_scheduled=include_scheduled)
    if job is None:
        return False

    meeting = db.meetings.get_meeting(job.meeting_id)
    if meeting is None:
        db.intel.fail_intel_job(job.meeting_id, "Meeting not found for deferred intelligence job.")
        return True

    if not meeting.segments:
        db.intel.fail_intel_job(job.meeting_id, "Meeting has no transcript to analyze.")
        return True

    current_hash = meeting.transcript_hash()
    if current_hash != job.transcript_hash:
        db.intel.enqueue_intel_job(
            job.meeting_id,
            transcript_hash=current_hash,
            reason="Transcript changed; refreshing queued intelligence job.",
        )
        log.info(f"Deferred intel job refreshed for meeting {job.meeting_id}")
        return True

    try:
        from .db.intel import ROUTED_INTEL_RETRY_REASON

        resume_routed = (
            job.last_error == ROUTED_INTEL_RETRY_REASON and meeting.intel is not None
        )
        if not resume_routed:
            kwargs = {
                "provider": provider,
                "cloud_model": cloud_model,
                "cloud_api_key_env": cloud_api_key_env,
                "cloud_base_url": cloud_base_url,
                "cloud_reasoning_effort": cloud_reasoning_effort,
                "cloud_store": cloud_store,
            }
            if model_path:
                kwargs["model_path"] = model_path
            intel = MeetingIntel(**kwargs)
            transcript = "\n".join(str(segment) for segment in meeting.segments)
            result = intel.analyze(transcript, stream=False)
            if result.error:
                _retry_or_fail_job(
                    db,
                    job,
                    f"Deferred intel failed: {result.error}",
                    max_attempts=retry_max_attempts,
                    base_delay_seconds=retry_base_seconds,
                    max_delay_seconds=retry_max_seconds,
                )
                return True

            meeting.intel = IntelSnapshot(
                timestamp=meeting.duration,
                topics=result.topics,
                action_items=result.action_items,
                summary=result.summary,
            )
        else:
            log.info(
                "Deferred intel resuming routed work for meeting %s",
                job.meeting_id,
            )
        # Persist the completed base analysis before routed work starts, but do
        # not advertise Ready while the remaining chain is still unresolved.
        meeting.intel_status = "running"
        meeting.intel_status_detail = (
            "Meeting saved. Summary, topics, and action items saved. "
            "Routed intelligence running."
        )
        meeting.intel_completed_at = None
        db.meetings.save_meeting(meeting)
        # HS-80-02 — the archive gets its artifacts: after a successful base
        # analyze, run the routed plugin chain over the saved transcript (the
        # Phase-67 F-05 fix). Gated on the same knob that gates live routing.
        # Any unresolved plugin keeps the base analysis/artifacts and leaves an
        # owner-recoverable partial job; only the complete chain becomes Ready.
        from .config import Config

        meeting_cfg = Config.load().meeting
        artifact_count = 0
        if bool(getattr(meeting_cfg, "intent_router_enabled", False)):
            try:
                from .meeting_plugins import run_meeting_plugin_chain

                chain_summary = run_meeting_plugin_chain(
                    db, meeting, profile=getattr(meeting_cfg, "mir_profile", None)
                )
                artifact_count = len(
                    db.plugins.list_artifacts(job.meeting_id, limit=2000)
                )
                plugin_statuses = dict(chain_summary.get("plugin_statuses") or {})
                incomplete = sorted(
                    (str(plugin_id), str(status))
                    for plugin_id, status in plugin_statuses.items()
                    if str(status).strip().lower() not in RESOLVED_PLUGIN_STATUSES
                )
                if incomplete:
                    failed_work = ", ".join(
                        f"{plugin_id} ({status})" for plugin_id, status in incomplete
                    )
                    detail = (
                        "Meeting saved. Summary, topics, and action items retained; "
                        f"{artifact_count} routed "
                        f"{'artifact' if artifact_count == 1 else 'artifacts'} retained. "
                        f"Remaining routed intelligence did not finish: {failed_work}."
                    )
                    db.intel.mark_intel_job_partial(job.meeting_id, detail)
                    db.intel.record_intel_job_attempt(
                        job.meeting_id,
                        attempt=int(job.attempts),
                        outcome="partial_failure",
                        error=detail,
                        retry_at=None,
                    )
                    log.warning(
                        "Deferred routed intel remained partial for meeting %s: %s",
                        job.meeting_id,
                        failed_work,
                    )
                    return True
            except Exception as exc:
                log.warning(
                    f"Deferred plugin chain failed for meeting {job.meeting_id}: {exc}"
                )
                detail = (
                    "Meeting saved. Summary, topics, and action items retained. "
                    "Remaining routed intelligence did not finish: "
                    f"{type(exc).__name__}: {exc}."
                )
                db.intel.mark_intel_job_partial(job.meeting_id, detail)
                db.intel.record_intel_job_attempt(
                    job.meeting_id,
                    attempt=int(job.attempts),
                    outcome="partial_failure",
                    error=detail,
                    retry_at=None,
                )
                return True
        meeting.intel_status = "ready"
        meeting.intel_status_detail = (
            f"Meeting intelligence ready. {artifact_count} routed "
            f"{'artifact' if artifact_count == 1 else 'artifacts'} saved."
            if bool(getattr(meeting_cfg, "intent_router_enabled", False))
            else "Meeting intelligence ready."
        )
        meeting.intel_completed_at = datetime.now()
        db.meetings.save_meeting(meeting)
        db.intel.record_intel_job_attempt(
            job.meeting_id,
            attempt=int(job.attempts),
            outcome="success",
            error=None,
            retry_at=None,
        )
        db.intel.complete_intel_job(job.meeting_id)
        log.info(f"Deferred intel completed for meeting {job.meeting_id}")
        # HS-56-04: observational hand-off for hosts with a broadcast channel
        # (the presence mascot's aftercare card). Never breaks the job.
        if on_meeting_ready is not None:
            try:
                on_meeting_ready(job.meeting_id)
            except Exception as exc:
                log.debug(f"on_meeting_ready observer failed: {exc}")
    except Exception as exc:
        _retry_or_fail_job(
            db,
            job,
            f"Deferred intel failed: {exc}",
            max_attempts=retry_max_attempts,
            base_delay_seconds=retry_base_seconds,
            max_delay_seconds=retry_max_seconds,
        )
        log.error(f"Deferred intel failed for meeting {job.meeting_id}: {exc}")

    return True


def drain_intel_queue(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    on_meeting_ready=None,
    cloud_model: str = "gpt-5-mini",
    cloud_api_key_env: str = "OPENAI_API_KEY",
    cloud_base_url: Optional[str] = None,
    cloud_reasoning_effort: Optional[str] = None,
    cloud_store: bool = False,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
    include_scheduled: bool = False,
    max_jobs: Optional[int] = None,
) -> int:
    """Drain queued intelligence jobs until empty or max_jobs is reached."""
    processed = 0
    while max_jobs is None or processed < max_jobs:
        if not process_next_intel_job(
            model_path,
            provider=provider,
            on_meeting_ready=on_meeting_ready,
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
            cloud_reasoning_effort=cloud_reasoning_effort,
            cloud_store=cloud_store,
            retry_base_seconds=retry_base_seconds,
            retry_max_seconds=retry_max_seconds,
            retry_max_attempts=retry_max_attempts,
            include_scheduled=include_scheduled,
        ):
            break
        processed += 1
    return processed


class IntelQueueWorker:
    """Background deferred-intel worker with explicit shutdown control."""

    def __init__(
        self,
        model_path: Optional[str],
        poll_seconds: float,
        *,
        provider: str = "local",
        cloud_model: str = "gpt-5-mini",
        cloud_api_key_env: str = "OPENAI_API_KEY",
        cloud_base_url: Optional[str] = None,
        cloud_reasoning_effort: Optional[str] = None,
        cloud_store: bool = False,
        retry_base_seconds: int = RETRY_BASE_SECONDS,
        retry_max_seconds: int = RETRY_MAX_SECONDS,
        retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
        failure_alert_percent: float = RETRY_FAILURE_ALERT_PERCENT,
        failure_alert_hysteresis_minutes: float = RETRY_FAILURE_HYSTERESIS_MINUTES,
        failure_alert_webhook_url: Optional[str] = None,
        failure_alert_webhook_header_name: Optional[str] = None,
        failure_alert_webhook_header_value: Optional[str] = None,
    ) -> None:
        self.model_path = model_path
        self.provider = provider
        self.cloud_model = cloud_model
        self.cloud_api_key_env = cloud_api_key_env
        self.cloud_base_url = cloud_base_url
        self.cloud_reasoning_effort = cloud_reasoning_effort
        self.cloud_store = cloud_store
        self.retry_base_seconds = max(1, int(retry_base_seconds))
        self.retry_max_seconds = max(self.retry_base_seconds, int(retry_max_seconds))
        self.retry_max_attempts = max(1, int(retry_max_attempts))
        self.failure_alert_percent = max(0.0, float(failure_alert_percent))
        self.failure_alert_hysteresis_seconds = max(0.0, float(failure_alert_hysteresis_minutes) * 60.0)
        self.failure_alert_webhook_url = (failure_alert_webhook_url or "").strip() or None
        header_name = (failure_alert_webhook_header_name or "").strip() or None
        header_value = (failure_alert_webhook_header_value or "").strip() or None
        if header_name and header_value:
            self.failure_alert_webhook_header_name = header_name
            self.failure_alert_webhook_header_value = header_value
        else:
            self.failure_alert_webhook_header_name = None
            self.failure_alert_webhook_header_value = None
        self.poll_seconds = max(5.0, float(poll_seconds))
        self._failure_alert_above_since: Optional[datetime] = None
        self._failure_alert_sent = False
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="HoldSpeakIntelQueue", daemon=True)
        self._thread.start()

    def _post_failure_alert_webhook(
        self,
        *,
        summary,
        failure_rate_percent: float,
        now: datetime,
        event: str = "triggered",
        above_since: Optional[datetime] = None,
    ) -> None:
        if not self.failure_alert_webhook_url:
            return

        event_type = str(event or "triggered").strip().lower()
        if event_type not in {"triggered", "resolved"}:
            event_type = "triggered"
        payload = {
            "type": "intel_queue_failure_alert",
            "event": event_type,
            "failure_rate_percent": round(float(failure_rate_percent), 2),
            "threshold_percent": float(self.failure_alert_percent),
            "hysteresis_seconds": float(self.failure_alert_hysteresis_seconds),
            "queue": {
                "total_jobs": int(summary.total_jobs),
                "queued_jobs": int(summary.queued_jobs),
                "running_jobs": int(summary.running_jobs),
                "failed_jobs": int(summary.failed_jobs),
                "queued_due_jobs": int(summary.queued_due_jobs),
                "scheduled_retry_jobs": int(summary.scheduled_retry_jobs),
                "next_retry_at": summary.next_retry_at.isoformat() if summary.next_retry_at else None,
            },
        }
        if event_type == "triggered":
            payload["triggered_at"] = now.isoformat()
        else:
            payload["resolved_at"] = now.isoformat()
        if above_since is not None:
            payload["above_since"] = above_since.isoformat()
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.failure_alert_webhook_header_name and self.failure_alert_webhook_header_value:
            headers[self.failure_alert_webhook_header_name] = self.failure_alert_webhook_header_value
        req = urlrequest.Request(
            self.failure_alert_webhook_url,
            data=body,
            headers=headers,
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS) as response:
            _ = response.read()

    def _update_failure_alert_state(self, summary, *, now: datetime) -> None:
        failure_rate_percent = _compute_failure_rate_percent(
            total_jobs=summary.total_jobs,
            failed_jobs=summary.failed_jobs,
        )
        above_threshold = int(summary.total_jobs) > 0 and failure_rate_percent >= self.failure_alert_percent

        if not above_threshold:
            prior_above_since = self._failure_alert_above_since
            should_emit_resolved = self._failure_alert_sent
            self._failure_alert_above_since = None
            self._failure_alert_sent = False
            if should_emit_resolved:
                log.info(
                    "Deferred intel queue failure rate recovered to %.2f%% (threshold %.2f%%)",
                    failure_rate_percent,
                    self.failure_alert_percent,
                )
                try:
                    self._post_failure_alert_webhook(
                        summary=summary,
                        failure_rate_percent=failure_rate_percent,
                        now=now,
                        event="resolved",
                        above_since=prior_above_since,
                    )
                except Exception as exc:
                    log.error(f"Deferred intel recovery webhook failed: {exc}")
            return

        if self._failure_alert_above_since is None:
            self._failure_alert_above_since = now
            self._failure_alert_sent = False
            return

        elapsed_seconds = (now - self._failure_alert_above_since).total_seconds()
        if elapsed_seconds < self.failure_alert_hysteresis_seconds:
            return
        if self._failure_alert_sent:
            return

        self._failure_alert_sent = True
        log.warning(
            "Deferred intel queue failure rate %.2f%% exceeded threshold %.2f%% for %.0fs",
            failure_rate_percent,
            self.failure_alert_percent,
            elapsed_seconds,
        )
        try:
            self._post_failure_alert_webhook(
                summary=summary,
                failure_rate_percent=failure_rate_percent,
                now=now,
                event="triggered",
                above_since=self._failure_alert_above_since,
            )
        except Exception as exc:
            log.error(f"Deferred intel failure-alert webhook failed: {exc}")

    def _check_failure_alerts(self) -> None:
        try:
            summary = get_database().get_intel_queue_summary()
        except Exception as exc:
            log.error(f"Deferred intel failure-alert check failed: {exc}")
            return
        self._update_failure_alert_state(summary, now=datetime.now())

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                processed = drain_intel_queue(
                    self.model_path,
                    provider=self.provider,
                    cloud_model=self.cloud_model,
                    cloud_api_key_env=self.cloud_api_key_env,
                    cloud_base_url=self.cloud_base_url,
                    cloud_reasoning_effort=self.cloud_reasoning_effort,
                    cloud_store=self.cloud_store,
                    retry_base_seconds=self.retry_base_seconds,
                    retry_max_seconds=self.retry_max_seconds,
                    retry_max_attempts=self.retry_max_attempts,
                )
                if processed:
                    log.info(f"Processed {processed} deferred intel job(s)")
            except Exception as exc:
                log.error(f"Deferred intel worker iteration failed: {exc}")
            self._check_failure_alerts()
            self._stop_event.wait(self.poll_seconds)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread.is_alive()


def start_intel_queue_worker(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    cloud_model: str = "gpt-5-mini",
    cloud_api_key_env: str = "OPENAI_API_KEY",
    cloud_base_url: Optional[str] = None,
    cloud_reasoning_effort: Optional[str] = None,
    cloud_store: bool = False,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
    failure_alert_percent: float = RETRY_FAILURE_ALERT_PERCENT,
    failure_alert_hysteresis_minutes: float = RETRY_FAILURE_HYSTERESIS_MINUTES,
    failure_alert_webhook_url: Optional[str] = None,
    failure_alert_webhook_header_name: Optional[str] = None,
    failure_alert_webhook_header_value: Optional[str] = None,
    poll_seconds: float = 120.0,
) -> IntelQueueWorker:
    """Start a deferred-intel worker that can be stopped cleanly."""
    return IntelQueueWorker(
        model_path=model_path,
        poll_seconds=poll_seconds,
        provider=provider,
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
        cloud_reasoning_effort=cloud_reasoning_effort,
        cloud_store=cloud_store,
        retry_base_seconds=retry_base_seconds,
        retry_max_seconds=retry_max_seconds,
        retry_max_attempts=retry_max_attempts,
        failure_alert_percent=failure_alert_percent,
        failure_alert_hysteresis_minutes=failure_alert_hysteresis_minutes,
        failure_alert_webhook_url=failure_alert_webhook_url,
        failure_alert_webhook_header_name=failure_alert_webhook_header_name,
        failure_alert_webhook_header_value=failure_alert_webhook_header_value,
    )
