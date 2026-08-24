"""Deferred meeting intelligence queue processing."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from typing import Optional
from urllib import request as urlrequest
from urllib.parse import urlsplit

from .db import get_database
from .kernel.external_egress import run_external_egress
from .intel import get_intel_runtime_status
from .logging_config import get_logger
from .meeting_session import IntelSnapshot

log = get_logger("intel_queue")

RETRY_BASE_SECONDS = 30
RETRY_MAX_SECONDS = 900
RETRY_MAX_ATTEMPTS = 6
RETRY_FAILURE_ALERT_PERCENT = 50.0
RETRY_FAILURE_HYSTERESIS_MINUTES = 5.0
RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS = 5.0
# Must stay materially below db.intel.BOUND_EXECUTOR_LEASE_SECONDS.
BOUND_EXECUTOR_HEARTBEAT_SECONDS = 3.0

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
            "id": f"intelq:{getattr(job, 'job_id', None) or job.meeting_id}",
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
) -> bool:
    """Settle failure, with C1 bearer fencing or preserved legacy behavior."""
    is_bound = bool(
        getattr(job, "parent_operation_id", None)
        and getattr(job, "executor_lease_token", None)
        and getattr(job, "executor_lease_epoch", 0)
    )
    if is_bound:
        retry_at = None
        if int(job.attempts) < int(max_attempts):
            delay = _compute_retry_delay_seconds(
                int(job.attempts), base_seconds=base_delay_seconds,
                max_seconds=max_delay_seconds,
            )
            retry_at = datetime.now() + timedelta(seconds=delay)
        changed = db.intel.settle_bound_execution(
            job, error=error, retry_at=retry_at, max_attempts=int(max_attempts),
        )
        if changed and retry_at is not None:
            log.warning(
                "Deferred intel failed for meeting %s (attempt %s/%s): retrying in %ss",
                job.meeting_id, job.attempts, max_attempts,
                _compute_retry_delay_seconds(int(job.attempts), base_seconds=base_delay_seconds,
                                             max_seconds=max_delay_seconds),
            )
        return changed
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
        return True

    delay = _compute_retry_delay_seconds(
        int(job.attempts), base_seconds=base_delay_seconds,
        max_seconds=max_delay_seconds,
    )
    retry_at = datetime.now() + timedelta(seconds=delay)
    db.intel.record_intel_job_attempt(
        job.meeting_id, attempt=int(job.attempts), outcome="scheduled_retry",
        error=error, retry_at=retry_at,
    )
    db.intel.retry_intel_job(
        job.meeting_id, error, retry_at=retry_at, attempt=int(job.attempts),
        max_attempts=int(max_attempts),
    )
    log.warning(
        "Deferred intel failed for meeting %s (attempt %s/%s): retrying in %ss",
        job.meeting_id, job.attempts, max_attempts, delay,
    )
    return True


def _compute_failure_rate_percent(*, total_jobs: int, failed_jobs: int) -> float:
    total = max(0, int(total_jobs))
    if total == 0:
        return 0.0
    failed = max(0, int(failed_jobs))
    return (failed / total) * 100.0


def _bound_claim(db, *, include_scheduled: bool):
    """Claim through the C1b binder without a runtime/Config preflight."""
    from .kernel.runtime import _service
    from .services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    broker = _service()
    job = db.intel.claim_next_intel_job_bound(
        MeetingDeferredQueueBinder(broker), include_scheduled=include_scheduled
    )
    return job, broker


def _bound_projection_base(job, meeting) -> dict:
    """Content-free identity carried by every bound publication stage."""
    return {
        "job_id": str(job.job_id),
        "meeting_id": str(job.meeting_id),
        "transcript_hash": str(job.transcript_hash),
        "work_descriptor_sha256": str(job.work_descriptor_sha256 or ""),
        # Opaque executor proof must arrive in the materializer transaction,
        # where it fences Meeting writes from a superseded queue worker.
        "executor_lease_token": str(job.executor_lease_token or ""),
        "executor_lease_epoch": int(job.executor_lease_epoch or 0),
    }


def _run_bound_displaced_work(db, meeting, bound, job, summary: str, *, executor_held=None) -> str:
    """Execute only stored label/title members after bound analysis publishes."""
    from .meeting_session.deferred_bound import bound_auto_title_dispatch, bound_bookmark_label_dispatch
    from .meeting_session.intel_plan import DISPLACED_AUTO_TITLE, DISPLACED_BOOKMARK_LABELS

    displaced = tuple(job.displaced_work or ())
    if DISPLACED_BOOKMARK_LABELS in displaced:
        # C1 freezes this content-free timestamp set before parent admission.
        # Do not let a mutable post-claim bookmark list create unbudgeted work.
        for bookmark_id, timestamp in tuple(job.frozen_bookmark_operations or ()):
            local_context = meeting.get_context_around(timestamp, window=10.0)
            if not local_context:
                continue
            projection, routed = bound.execute(
                capability="meeting.bookmark_label",
                operation_suffix=f"bookmark:{bookmark_id}",
                material={
                    "context_sha256": _hash_private(local_context),
                    "summary_sha256": _hash_private(summary),
                    "bookmark_id": bookmark_id,
                    "bookmark_timestamp": timestamp,
                    "template_revision": "1",
                    "context_material": local_context,
                    "summary_material": summary,
                },
                call=bound_bookmark_label_dispatch(),
                projection_kind="meeting-bound-deferred-bookmark-label",
                projection=lambda result: {
                    **_bound_projection_base(job, meeting),
                    "bookmark_id": bookmark_id,
                    "bookmark_timestamp": timestamp,
                    "label": str(result["label"]),
                },
                executor_held=executor_held,
            )
            if str(routed.get("outcome")) == "refused":
                return "displaced bookmark labels refused"
            if projection is None:
                return "displaced bookmark labels did not publish"
            if projection.get("publication") == "superseded":
                return "transcript superseded before bookmark-label publication"
    if DISPLACED_AUTO_TITLE in displaced and not str(getattr(meeting, "title", "") or "").strip():
        transcript = "\n".join(str(segment) for segment in meeting.segments)
        projection, routed = bound.execute(
            capability="meeting.auto_title",
            operation_suffix="auto-title",
            material={
                "transcript_sha256": _hash_private(transcript),
                "template_revision": "1",
                "transcript_material": transcript,
            },
            call=bound_auto_title_dispatch(),
            projection_kind="meeting-bound-deferred-auto-title",
            projection=lambda result: {
                **_bound_projection_base(job, meeting), "title": str(result["title"]),
            },
            executor_held=executor_held,
        )
        if str(routed.get("outcome")) == "refused":
            return "the displaced auto title was refused"
        if projection is None:
            return "the displaced auto title did not publish"
        if projection.get("publication") == "superseded":
            return "transcript superseded before auto-title publication"
    return ""


def _hash_private(value: object) -> str:
    """Name private material in queue evidence without retaining its bytes."""
    from .meeting_session.intel_child import sha

    return sha(value)


class _BoundExecutorLease:
    """Keep one durable queue-executor bearer live while model work runs."""

    def __init__(self, db, job) -> None:
        self._db = db
        self._job = job
        self._stop = threading.Event()
        self._lost = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if not self._db.intel.renew_bound_executor_lease(self._job):
            return False
        self._thread = threading.Thread(
            target=self._heartbeat, name=f"intel-executor-lease:{self._job.job_id}", daemon=True,
        )
        self._thread.start()
        return True

    def _heartbeat(self) -> None:
        # Renew well inside the durable expiry window. A stopped process has no
        # heartbeat; a competing worker can only take over once this expires.
        try:
            while not self._stop.wait(BOUND_EXECUTOR_HEARTBEAT_SECONDS):
                if not self._db.intel.renew_bound_executor_lease(self._job):
                    self._lost.set()
                    return
        except BaseException:  # a dead heartbeat is an ownership loss, never optimism
            self._lost.set()

    @property
    def lost(self) -> bool:
        return self._lost.is_set()

    def mark_lost(self) -> None:
        """Record a transaction-level fencing loss observed during publication."""
        self._lost.set()

    def held(self) -> bool:
        if self._lost.is_set():
            return False
        try:
            if not self._db.intel.renew_bound_executor_lease(self._job):
                self._lost.set()
                return False
        except BaseException:
            self._lost.set()
            return False
        return True

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._db.intel.release_bound_executor_lease(self._job)


def _process_bound_intel_job(
    db, job, broker, *, on_meeting_ready, retry_base_seconds: int,
    retry_max_seconds: int, retry_max_attempts: int,
) -> bool:
    """Execute a C1b-bound claim through stored parent/bundle/member IDs only."""
    from .meeting_session.deferred_admission import BoundDeferredIntelJob
    from .meeting_session.deferred_bound import bound_analysis_dispatch
    from .kernel.model import KernelRefused

    lease = _BoundExecutorLease(db, job)
    if not lease.start():
        return False
    outcome = "failed"
    bound = None
    try:
        meeting = db.meetings.get_meeting(job.meeting_id)
        if meeting is None or not meeting.segments:
            changed = db.intel.settle_bound_execution(
                job, error="Meeting has no transcript to analyze.",
                terminal_outcome="terminal_failure",
            )
            return changed
        # Preserve the deterministic fault-plane seam on the C1 bound executor:
        # this occurs before any semantic payload reaches a provider child.
        from .faults import trip as _fault_trip

        _fault_trip("intel.model_unavailable")
        bound = BoundDeferredIntelJob.reconstruct(db, job, broker=broker)
        # Fence two: this happens immediately before constructing the only payload
        # carrying transcript bytes. A mismatch supersedes rather than retargeting.
        if not lease.held():
            return False
        fresh = db.intel.supersede_bound_intel_job(
            job, reason="Transcript changed before bound material staging.",
            event_kind="staging_fence_superseded",
        )
        if fresh is not None:
            outcome = "cancelled"
            return True
        transcript = "\n".join(str(segment) for segment in meeting.segments)
        if not lease.held():
            return False
        projection, routed = bound.execute(
            capability="meeting.deferred_analysis",
            operation_suffix="analysis",
            material={
                "transcript_sha256": _hash_private(transcript),
                "template_revision": "1",
                "transcript_material": transcript,
            },
            call=bound_analysis_dispatch(),
            projection_kind="meeting-bound-deferred-analysis",
            projection=lambda result: {
                **_bound_projection_base(job, meeting),
                "summary": str(result["summary"]),
                "topics": list(result["topics"]),
                "action_items": list(result["action_items"]),
            },
            executor_held=lease.held,
        )
        # Publication's transcript fence can terminalize this job during
        # finalize. A token/epoch mismatch is stronger: this executor was fenced
        # and must perform no subsequent queue, Meeting, or parent effect.
        if projection is not None and projection.get("publication") == "lease_lost":
            lease.mark_lost()
            return False
        if projection is not None and projection.get("publication") == "superseded":
            outcome = "cancelled"
            return True
        if not lease.held():
            return False
        if str(routed.get("outcome")) == "refused":
            changed = db.intel.settle_bound_execution(
                job, error="Deferred provider refused bound execution.",
                terminal_outcome="refused",
            )
            if changed:
                outcome = "refused"
            else:
                lease.mark_lost()
            return changed
        if projection is None:
            changed = _retry_or_fail_job(
                db, job, "Deferred intel failed: bound analysis did not publish",
                max_attempts=retry_max_attempts, base_delay_seconds=retry_base_seconds,
                max_delay_seconds=retry_max_seconds,
            )
            if not changed:
                lease.mark_lost()
            return changed
        if projection.get("publication") == "superseded":
            outcome = "cancelled"
            return True
        if not lease.held():
            return False
        detail = _run_bound_displaced_work(
            db, meeting, bound, job, str(projection.get("summary") or ""),
            executor_held=lease.held,
        )
        if detail:
            if detail.startswith("transcript superseded"):
                outcome = "cancelled"
                return True
            changed = _retry_or_fail_job(
                db, job, f"Deferred intel failed: {detail}", max_attempts=retry_max_attempts,
                base_delay_seconds=retry_base_seconds, max_delay_seconds=retry_max_seconds,
            )
            if not changed:
                lease.mark_lost()
            return changed
        if not lease.held():
            return False
        if not db.intel.complete_bound_intel_job(job):
            lease.mark_lost()
            return False
        outcome = "succeeded"
        if on_meeting_ready is not None:
            try:
                on_meeting_ready(job.meeting_id)
            except Exception as exc:
                log.debug("on_meeting_ready observer failed: %s", type(exc).__name__)
        return True
    except KernelRefused as exc:
        # The provider's typed refusal is terminal, not a fallback/retry signal.
        log.warning("Bound deferred kernel refusal for meeting %s: %s", job.meeting_id, exc.reason)
        if lease.lost:
            return False
        changed = db.intel.settle_bound_execution(
            job, error="Deferred provider refused bound execution.",
            terminal_outcome="refused",
        )
        if changed:
            outcome = "refused"
        else:
            lease.mark_lost()
        return changed
    except Exception as exc:
        # FaultInjected carries the named deterministic point; retain it in the
        # durable retry evidence instead of reducing it to its exception class.
        from .faults import FaultInjected

        if lease.lost:
            return False
        reason = str(exc) if isinstance(exc, FaultInjected) else type(exc).__name__
        changed = _retry_or_fail_job(
            db, job, f"Deferred intel failed: {reason}",
            max_attempts=retry_max_attempts, base_delay_seconds=retry_base_seconds,
            max_delay_seconds=retry_max_seconds,
        )
        if not changed:
            lease.mark_lost()
            return False
        log.error("Bound deferred intel failed for meeting %s: %s: %s", job.meeting_id, type(exc).__name__, getattr(exc, "code", str(exc)))
        return True
    finally:
        # A fenced-out executor may not terminalize the shared parent after a
        # newer bearer adopted it. A normal terminal job still closes its parent
        # even though completion has already made lease renewal inapplicable.
        if bound is not None and not lease.lost:
            executor_lease = {
                "job_id": str(job.job_id), "token": str(job.executor_lease_token),
                "epoch": int(job.executor_lease_epoch),
            }
            if bound.close(outcome, executor_lease=executor_lease):
                db.intel.promote_successors_after_parent_terminal(
                    bound.parent_operation_id, executor_job=job
                )
        lease.close()


def process_next_intel_job(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    on_meeting_ready=None,
    retry_base_seconds: int = RETRY_BASE_SECONDS,
    retry_max_seconds: int = RETRY_MAX_SECONDS,
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
    include_scheduled: bool = False,
) -> bool:
    """Process a single queued intelligence job, if available.

    The cloud leg is not threaded in as bare params (HS-112-01): it resolves
    here, through the one resolver, from the assigned InferenceTarget.
    """
    # C1 bound work has no mutable runtime preflight: route election and the
    # SERVICE shell were committed with its claim, and execution must load those
    # stored IDs rather than Config, a resolver, or a fresh plan.
    db = get_database()
    # Close receipt and successor promotion are separate durable writes. Recover
    # the receipt→promotion crash interval before looking for a close still owed;
    # the scan is idempotent and lets the next drain iteration claim the survivor.
    if db.intel.promote_receipted_bound_successors():
        return True
    # A close may fail after the queue row became terminal.  Resume only the
    # old parent-close/posture transition first; its reserved successor cannot
    # bind until this durable receipt exists.
    pending_close = db.intel.get_bound_terminal_pending_close_intel_job()
    if pending_close is not None:
        from .meeting_session.deferred_admission import BoundDeferredIntelJob

        bound = BoundDeferredIntelJob.reconstruct(db, pending_close)
        outcome = (
            "succeeded" if pending_close.status == "succeeded"
            else "cancelled" if pending_close.status in {"superseded", "skipped"}
            else "failed"
        )
        if not bound.close(outcome):
            return False
        db.intel.promote_successors_after_parent_terminal(bound.parent_operation_id)
        return True
    # A post-commit crash resumes the exact stored C1 owner only after its
    # durable executor lease has expired and this worker wins takeover CAS.
    # A live bearer is another real runner, never recovery work for this caller.
    recovered_bound = db.intel.get_bound_claimed_intel_job()
    if recovered_bound is not None:
        recovered_bound = db.intel.take_over_stale_bound_executor(
            str(recovered_bound.job_id)
        )
        if recovered_bound is None:
            return False
        from .kernel.runtime import _service

        return _process_bound_intel_job(
            db, recovered_bound, _service(), on_meeting_ready=on_meeting_ready,
            retry_base_seconds=retry_base_seconds, retry_max_seconds=retry_max_seconds,
            retry_max_attempts=retry_max_attempts,
        )
    # A process can die after a pre-C1 legacy claim. Resume only that already
    # running owner; queued work never falls through to this legacy executor.
    legacy_job = db.intel.get_legacy_claimed_intel_job()
    if legacy_job is None:
        try:
            bound_job, broker = _bound_claim(db, include_scheduled=include_scheduled)
        except Exception as exc:
            # Claim refusal is progress only when the repository durably
            # terminalized it or moved it behind backoff.  Never tell an unbounded
            # drain it made progress on an unchanged immediately-due job.
            advanced = bool(getattr(exc, "_holdspeak_queue_advanced", False))
            log.warning("Bound deferred intel claim refused: %s", type(exc).__name__)
            return advanced
        if bound_job is not None:
            return _process_bound_intel_job(
                db, bound_job, broker, on_meeting_ready=on_meeting_ready,
                retry_base_seconds=retry_base_seconds, retry_max_seconds=retry_max_seconds,
                retry_max_attempts=retry_max_attempts,
            )
        return False

    # Only rows that were already claimed through the historical Meeting-keyed
    # shape reach this branch. They retain the legacy frozen-plan executor until
    # Phase F removes historical queue compatibility.
    from .config import Config
    from .config.meeting import effective_routing_profile
    from .intel.providers import effective_intel_cloud

    meeting_cfg = Config.load().meeting
    effective = effective_intel_cloud(meeting_cfg)
    runtime_kwargs = {
        "provider": provider,
        "cloud_model": effective.model,
        "cloud_api_key_env": effective.api_key_env,
        "cloud_base_url": effective.base_url,
    }
    if model_path:
        runtime_ok, runtime_reason = get_intel_runtime_status(model_path, **runtime_kwargs)
    else:
        runtime_ok, runtime_reason = get_intel_runtime_status(**runtime_kwargs)

    if not runtime_ok:
        log.debug(f"Deferred intel queue paused: {runtime_reason}")
        return False

    job = legacy_job

    meeting = db.meetings.get_meeting(job.meeting_id)
    if meeting is None:
        db.intel.fail_intel_job(job.meeting_id, "Meeting not found for deferred intelligence job.")
        return True

    if not meeting.segments:
        db.intel.fail_intel_job(job.meeting_id, "Meeting has no transcript to analyze.")
        return True

    current_hash = meeting.transcript_hash()
    if current_hash != job.transcript_hash:
        refreshed = db.intel.requeue_claimed_intel_job(
            job.meeting_id,
            transcript_hash=current_hash,
            reason="Transcript changed; refreshing queued intelligence job.",
            # A refresh must NOT forget what stop displaced onto this job.
            displaced_work=job.displaced_work,
        )
        if refreshed:
            log.info(f"Deferred intel job refreshed for meeting {job.meeting_id}")
        else:
            log.warning("Deferred intel claim disappeared before refresh: %s", job.meeting_id)
        return True

    # HS-131-08: the claimed job admits ONE short-lived
    # `meeting.deferred-intel-job` parent under the narrow queue-worker service
    # principal, over a FRESHLY frozen plan. It never joins or revives the closed
    # live `meeting.session` parent, and each retry (a new attempt) is a new
    # parent — never a reopened epoch.
    routing_enabled = bool(getattr(meeting_cfg, "intent_router_enabled", False))
    plugin_host = _routed_plugin_host(routing_enabled)
    admission = _admit_deferred_job(
        db, job, meeting_cfg=meeting_cfg, plugin_host=plugin_host, meeting=meeting
    )
    if admission is None:
        _retry_or_fail_job(
            db,
            job,
            "Deferred intel failed: meeting_deferred_intel_job_not_admitted",
            max_attempts=retry_max_attempts,
            base_delay_seconds=retry_base_seconds,
            max_delay_seconds=retry_max_seconds,
        )
        return True

    job_outcome = "failed"
    try:
        from .db.intel import ROUTED_INTEL_RETRY_REASON

        resume_routed = (
            job.last_error == ROUTED_INTEL_RETRY_REASON and meeting.intel is not None
        )
        if not resume_routed:
            # HS-93-06 fault plane: the model disappears at intelligence time.
            # Raising here takes the real deferred-intel failure path — a
            # bounded scheduled retry, never a false Ready.
            from .faults import trip as _fault_trip

            _fault_trip("intel.model_unavailable")
            transcript = "\n".join(str(segment) for segment in meeting.segments)
            # The engine is built ONLY from the plan's frozen deployment revision
            # (`build_intel_for_revision`); this seam no longer constructs a
            # provider or resolves placement of its own.
            _, projection, result = admission.analyze(transcript)
            if projection is None or result is None or getattr(result, "error", None):
                detail = str(
                    getattr(result, "error", "")
                    or "the deferred analysis child did not publish"
                )
                _retry_or_fail_job(
                    db,
                    job,
                    f"Deferred intel failed: {detail}",
                    max_attempts=retry_max_attempts,
                    base_delay_seconds=retry_base_seconds,
                    max_delay_seconds=retry_max_seconds,
                )
                job_outcome = "failed"
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
        # HS-131-08 (D3): the work stop() displaced onto this job — bookmark
        # labels and the auto title — runs HERE as admitted children, after the
        # base analysis is durable and BEFORE anything reports Ready. Their
        # outputs land through receipt-gated materializers, so the meeting is
        # re-read afterwards instead of being overwritten from a stale copy.
        displaced_detail = _run_displaced_work(db, meeting, admission, job)
        if displaced_detail:
            _retry_or_fail_job(
                db,
                job,
                f"Deferred intel failed: {displaced_detail}",
                max_attempts=retry_max_attempts,
                base_delay_seconds=retry_base_seconds,
                max_delay_seconds=retry_max_seconds,
            )
            job_outcome = "failed"
            return True
        if job.displaced_work:
            meeting = db.meetings.get_meeting(job.meeting_id) or meeting
            meeting.intel_status = "running"
            meeting.intel_completed_at = None
        # HS-80-02 — the archive gets its artifacts: after a successful base
        # analyze, run the routed plugin chain over the saved transcript (the
        # Phase-67 F-05 fix). Gated on the same knob that gates live routing.
        # Any unresolved plugin keeps the base analysis/artifacts and leaves an
        # owner-recoverable partial job; only the complete chain becomes Ready.
        artifact_count = 0
        if routing_enabled:
            try:
                from .meeting_plugins import run_meeting_plugin_chain

                # Routed plugins run ONLY under this job's parent context: each
                # executed plugin is one trusted child, and its run record and
                # artifacts are staged projections gated on that child's receipt.
                chain_summary = run_meeting_plugin_chain(
                    db,
                    meeting,
                    profile=effective_routing_profile(meeting_cfg),
                    host=plugin_host,
                    admission=admission,
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
                    # Partial is not a kernel outcome: the job as a bounded unit
                    # did not complete, so its parent closes `failed` while the
                    # queue keeps its own `partial` vocabulary for the owner.
                    job_outcome = "failed"
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
        job_outcome = "succeeded"
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
    finally:
        # One honest terminal receipt per job parent. A retry admits a NEW
        # parent; this one is never reopened.
        admission.close(job_outcome)

    return True


def _routed_plugin_host(routing_enabled: bool):
    """Build the routed plugin host BEFORE the plan freezes, or none at all.

    The frozen plan must name a deployment revision for every plugin capability
    the job may reach, so the registry that decides those capabilities has to
    exist before admission. With routing off there is no plugin capability and
    no host.
    """
    if not routing_enabled:
        return None
    try:
        from .meeting_plugins import _build_host

        return _build_host()
    except Exception as exc:
        log.warning(f"Deferred routed plugin host unavailable: {exc}")
        return None


def _routed_plugin_ids(host) -> tuple[str, ...]:
    if host is None:
        return ()
    try:
        return tuple(str(item) for item in host.list_plugins())
    except Exception:
        return ()


def _displaced_child_count(job, meeting) -> int:
    """How many displaced dispatches this job may need (one per label + a title)."""
    from .meeting_session.intel_plan import DISPLACED_AUTO_TITLE, DISPLACED_BOOKMARK_LABELS

    displaced = tuple(job.displaced_work or ())
    count = 0
    if DISPLACED_BOOKMARK_LABELS in displaced:
        count += len(getattr(meeting, "bookmarks", None) or [])
    if DISPLACED_AUTO_TITLE in displaced:
        count += 1
    return count


def _run_displaced_work(db, meeting, admission, job) -> str:
    """Run the work stop displaced onto this job, as admitted children (HS-131-08).

    Every earned output lands through its own receipt-gated materializer (the
    meeting title, the bookmark labels), so a cancelled or expired job parent
    leaves the meeting untouched. Returns "" when all displaced work settled, or
    the honest failure detail — the meeting must not reach Ready otherwise.
    """
    from .meeting_session.intel_plan import (
        DISPLACED_AUTO_TITLE,
        DISPLACED_BOOKMARK_LABELS,
        MeetingIntelRefused,
    )

    displaced = tuple(job.displaced_work or ())
    if not displaced:
        return ""
    summary = str(getattr(getattr(meeting, "intel", None), "summary", "") or "")
    try:
        if DISPLACED_BOOKMARK_LABELS in displaced:
            for bookmark in getattr(meeting, "bookmarks", None) or []:
                local_context = meeting.get_context_around(bookmark.timestamp, window=10.0)
                if not local_context:
                    continue  # no transcript near this bookmark: no model work
                _, projection, _ = admission.bookmark_label(
                    local_context=local_context,
                    meeting_summary=summary,
                    timestamp=float(bookmark.timestamp),
                )
                if projection is None:
                    return "displaced bookmark labels did not publish"
        if DISPLACED_AUTO_TITLE in displaced and not str(
            getattr(meeting, "title", "") or ""
        ).strip():
            _, projection, _ = admission.auto_title(
                "\n".join(str(segment) for segment in meeting.segments)
            )
            if projection is None:
                return "the displaced auto title did not publish"
    except MeetingIntelRefused as exc:
        return f"displaced work refused: {exc.reason}"
    return ""


def _admit_deferred_job(db, job, *, meeting_cfg, plugin_host, meeting=None):
    """Admit ONE `meeting.deferred-intel-job` parent for this claimed attempt."""
    from .meeting_session.deferred_admission import DeferredIntelJob
    from .meeting_session.intel_plan import MeetingIntelRefused

    try:
        return DeferredIntelJob.admit(
            db,
            meeting_id=job.meeting_id,
            attempt=int(job.attempts),
            transcript_hash=str(job.transcript_hash or ""),
            # A manual or scheduled requeue moves `requested_at`, so it names a
            # distinct attempt even when the attempt ordinal repeats.
            attempt_key=(
                job.requested_at.isoformat() if job.requested_at is not None else ""
            ),
            plugin_ids=_routed_plugin_ids(plugin_host),
            meeting_config=meeting_cfg,
            # The structured work stop displaced onto this job: its capabilities
            # are frozen in the plan and its dispatches are paid for by the budget.
            displaced_work=tuple(job.displaced_work or ()),
            displaced_children=(
                0 if meeting is None else _displaced_child_count(job, meeting)
            ),
        )
    except MeetingIntelRefused as exc:
        log.error(
            "Deferred intel job refused admission for meeting %s: %s",
            job.meeting_id,
            exc.reason,
        )
        return None
    except Exception as exc:
        log.error(
            "Deferred intel job admission failed for meeting %s: %s",
            job.meeting_id,
            type(exc).__name__,
        )
        return None


def drain_intel_queue(
    model_path: Optional[str] = None,
    *,
    provider: str = "local",
    on_meeting_ready=None,
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
        endpoint = urlsplit(self.failure_alert_webhook_url)
        destination = (endpoint.hostname or "invalid-webhook").lower()
        if endpoint.port:
            destination += f":{endpoint.port}"
        response = run_external_egress(
            connector_id="intel-queue-failure-alert",
            destination=destination,
            data_classes=("queue_failure_metrics",),
            payload_material=payload,
            sender=urlrequest.urlopen,
            args=(req,),
            kwargs={"timeout": RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS},
            allowed_destinations=(destination,),
        )
        with response:
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
        retry_base_seconds=retry_base_seconds,
        retry_max_seconds=retry_max_seconds,
        retry_max_attempts=retry_max_attempts,
        failure_alert_percent=failure_alert_percent,
        failure_alert_hysteresis_minutes=failure_alert_hysteresis_minutes,
        failure_alert_webhook_url=failure_alert_webhook_url,
        failure_alert_webhook_header_name=failure_alert_webhook_header_name,
        failure_alert_webhook_header_value=failure_alert_webhook_header_value,
    )
