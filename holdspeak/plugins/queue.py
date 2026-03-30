"""Deferred MIR plugin-run queue processing helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from ..db import MeetingDatabase, PluginRunJob
from ..logging_config import get_logger
from .host import PluginHost

log = get_logger("plugins.queue")

RETRY_BASE_SECONDS = 15
RETRY_MAX_SECONDS = 300
RETRY_MAX_ATTEMPTS = 4


def compute_retry_delay_seconds(
    attempt: int,
    *,
    base_seconds: int = RETRY_BASE_SECONDS,
    max_seconds: int = RETRY_MAX_SECONDS,
) -> int:
    """Compute exponential backoff for deferred plugin-run retries."""
    exponent = max(0, int(attempt) - 1)
    delay = int(base_seconds) * (2 ** exponent)
    return min(int(max_seconds), delay)


def _record_job_result(
    *,
    db: MeetingDatabase,
    job: PluginRunJob,
    status: str,
    plugin_version: str,
    idempotency_key: str,
    duration_ms: float,
    output: Optional[dict],
    error: Optional[str],
    deduped: bool,
) -> None:
    db.record_plugin_run(
        meeting_id=job.meeting_id,
        window_id=job.window_id,
        plugin_id=job.plugin_id,
        plugin_version=plugin_version,
        status=status,
        idempotency_key=idempotency_key,
        duration_ms=duration_ms,
        output=output,
        error=error,
        deduped=deduped,
    )


def process_next_plugin_run_job(
    *,
    host: PluginHost,
    db: MeetingDatabase,
    include_scheduled: bool = False,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
) -> bool:
    """Process one deferred MIR plugin-run queue item."""
    job = db.claim_next_plugin_run_job(include_scheduled=include_scheduled)
    if job is None:
        return False

    meeting = db.get_meeting(job.meeting_id)
    if meeting is None:
        delay_seconds = compute_retry_delay_seconds(
            job.attempts,
            base_seconds=retry_base_seconds,
            max_seconds=retry_max_seconds,
        )
        retry_at = datetime.now() + timedelta(seconds=delay_seconds)
        db.retry_plugin_run_job(
            job.id,
            error="Meeting not yet persisted; deferred plugin run will retry.",
            retry_at=retry_at,
        )
        return True

    result = host.execute(
        job.plugin_id,
        context=dict(job.context),
        meeting_id=job.meeting_id,
        window_id=job.window_id,
        transcript_hash=job.transcript_hash,
        defer_heavy=False,
    )

    if result.status in {"success", "deduped", "blocked"}:
        _record_job_result(
            db=db,
            job=job,
            status=result.status,
            plugin_version=result.plugin_version,
            idempotency_key=result.idempotency_key,
            duration_ms=result.duration_ms,
            output=result.output,
            error=result.error,
            deduped=result.deduped,
        )
        db.complete_plugin_run_job(job.id)
        return True

    if result.status in {"error", "timeout"}:
        if int(job.attempts) >= int(retry_max_attempts):
            _record_job_result(
                db=db,
                job=job,
                status=result.status,
                plugin_version=result.plugin_version,
                idempotency_key=result.idempotency_key,
                duration_ms=result.duration_ms,
                output=result.output,
                error=result.error,
                deduped=result.deduped,
            )
            db.fail_plugin_run_job(
                job.id,
                error=result.error or f"Deferred plugin run {result.status}",
            )
            return True

        delay_seconds = compute_retry_delay_seconds(
            job.attempts,
            base_seconds=retry_base_seconds,
            max_seconds=retry_max_seconds,
        )
        retry_at = datetime.now() + timedelta(seconds=delay_seconds)
        db.retry_plugin_run_job(
            job.id,
            error=result.error or f"Deferred plugin run {result.status}",
            retry_at=retry_at,
        )
        log.warning(
            "Deferred MIR plugin run failed for %s/%s (%s): retrying in %ss",
            job.meeting_id,
            job.window_id,
            job.plugin_id,
            delay_seconds,
        )
        return True

    db.fail_plugin_run_job(
        job.id,
        error=f"Unhandled deferred plugin status: {result.status}",
    )
    return True


def drain_plugin_run_queue(
    *,
    host: PluginHost,
    db: MeetingDatabase,
    max_jobs: Optional[int] = None,
    include_scheduled: bool = False,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
) -> int:
    """Drain deferred MIR plugin queue until empty or max_jobs limit."""
    processed = 0
    while max_jobs is None or processed < max_jobs:
        if not process_next_plugin_run_job(
            host=host,
            db=db,
            include_scheduled=include_scheduled,
            retry_base_seconds=retry_base_seconds,
            retry_max_seconds=retry_max_seconds,
            retry_max_attempts=retry_max_attempts,
        ):
            break
        processed += 1
    return processed
