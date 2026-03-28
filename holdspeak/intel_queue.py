"""Deferred meeting intelligence queue processing."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional

from .db import get_database
from .intel import MeetingIntel, get_intel_runtime_status
from .logging_config import get_logger
from .meeting_session import IntelSnapshot

log = get_logger("intel_queue")


def process_next_intel_job(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    cloud_model: str = "gpt-5-mini",
    cloud_api_key_env: str = "OPENAI_API_KEY",
    cloud_base_url: Optional[str] = None,
    cloud_reasoning_effort: Optional[str] = None,
    cloud_store: bool = False,
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
    job = db.claim_next_intel_job()
    if job is None:
        return False

    meeting = db.get_meeting(job.meeting_id)
    if meeting is None:
        db.fail_intel_job(job.meeting_id, "Meeting not found for deferred intelligence job.")
        return True

    if not meeting.segments:
        db.fail_intel_job(job.meeting_id, "Meeting has no transcript to analyze.")
        return True

    current_hash = meeting.transcript_hash()
    if current_hash != job.transcript_hash:
        db.enqueue_intel_job(
            job.meeting_id,
            transcript_hash=current_hash,
            reason="Transcript changed; refreshing queued intelligence job.",
        )
        log.info(f"Deferred intel job refreshed for meeting {job.meeting_id}")
        return True

    try:
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
            db.fail_intel_job(job.meeting_id, f"Deferred intel failed: {result.error}")
            return True

        meeting.intel = IntelSnapshot(
            timestamp=meeting.duration,
            topics=result.topics,
            action_items=result.action_items,
            summary=result.summary,
        )
        meeting.intel_status = "ready"
        meeting.intel_status_detail = "Deferred meeting intelligence processed successfully."
        meeting.intel_completed_at = datetime.now()
        db.save_meeting(meeting)
        db.complete_intel_job(job.meeting_id)
        log.info(f"Deferred intel completed for meeting {job.meeting_id}")
    except Exception as exc:
        db.fail_intel_job(job.meeting_id, f"Deferred intel failed: {exc}")
        log.error(f"Deferred intel failed for meeting {job.meeting_id}: {exc}")

    return True


def drain_intel_queue(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    cloud_model: str = "gpt-5-mini",
    cloud_api_key_env: str = "OPENAI_API_KEY",
    cloud_base_url: Optional[str] = None,
    cloud_reasoning_effort: Optional[str] = None,
    cloud_store: bool = False,
    max_jobs: Optional[int] = None,
) -> int:
    """Drain queued intelligence jobs until empty or max_jobs is reached."""
    processed = 0
    while max_jobs is None or processed < max_jobs:
        if not process_next_intel_job(
            model_path,
            provider=provider,
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
            cloud_reasoning_effort=cloud_reasoning_effort,
            cloud_store=cloud_store,
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
    ) -> None:
        self.model_path = model_path
        self.provider = provider
        self.cloud_model = cloud_model
        self.cloud_api_key_env = cloud_api_key_env
        self.cloud_base_url = cloud_base_url
        self.cloud_reasoning_effort = cloud_reasoning_effort
        self.cloud_store = cloud_store
        self.poll_seconds = max(5.0, float(poll_seconds))
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="HoldSpeakIntelQueue", daemon=True)
        self._thread.start()

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
                )
                if processed:
                    log.info(f"Processed {processed} deferred intel job(s)")
            except Exception as exc:
                log.error(f"Deferred intel worker iteration failed: {exc}")
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
    )
