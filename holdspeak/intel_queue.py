"""Deferred meeting intelligence queue processing."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Optional
from urllib import request as urlrequest
from urllib.parse import urlsplit

from .db import get_database
from .kernel.external_egress import run_external_egress
from .logging_config import get_logger

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
    """Settle a C1-bound execution failure under its durable bearer."""
    if not (
        getattr(job, "parent_operation_id", None)
        and getattr(job, "executor_lease_token", None)
        and getattr(job, "executor_lease_epoch", 0)
    ):
        return False
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


def _reconcile_stop_handoffs(db, broker) -> bool:
    """Settle known-safe Stop handoffs and fresh-admit only unknown outcomes.

    The bundle primitive remains the sole settlement/activation authority.  This
    queue boundary merely revisits its durable records after restart and asks the
    adopter to append a fresh normal job for an unknown terminal; it never makes
    the old reservation claimable.
    """
    from .services.inference_parent_route_bundle_service import InferenceParentRouteBundleService

    service = InferenceParentRouteBundleService(
        broker,
        broker.inference_adoption_service,
        handoff_evidence_providers=(db.intel.stop_handoff_provider(),),
    )
    for command_id in db.intel.pending_stop_handoff_commands():
        try:
            service.reconcile_stop_handoff(command_id=command_id)
        except Exception as exc:
            # An unsettled handoff remains durable and inert; an integrity refusal
            # is not queue progress and must not open a second execution path.
            log.warning("Deferred Stop handoff reconciliation deferred: %s", type(exc).__name__)
    return bool(db.intel.admit_unknown_stop_handoff_recoveries())


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
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()


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
    from .meeting_session.deferred_bound import BoundDeferredIntelJob, bound_analysis_dispatch
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
        # C2 executes the descriptor's revision-bound installed-plugin members
        # through the same stored parent/bundle and bearer fence.  The old C1
        # descriptor has no members and remains a readable/recoverable history;
        # new claims never reach the legacy admission/Config path below.
        if tuple(getattr(job, "frozen_plugin_members", ()) or ()):
            from .meeting_plugins import run_bound_meeting_plugin_chain

            chain = run_bound_meeting_plugin_chain(
                db, meeting, bound=bound, job=job,
            )
            incomplete = sorted(
                f"{plugin_id} ({status})"
                for plugin_id, status in dict(chain.get("plugin_statuses") or {}).items()
                if str(status).strip().lower() not in RESOLVED_PLUGIN_STATUSES
            )
            if incomplete:
                detail = "Remaining routed intelligence did not finish: " + ", ".join(incomplete)
                log.warning("Bound deferred plugin chain partial for meeting %s: %s", job.meeting_id, detail)
                # Revision/host/bundle drift is an explicit refusal, not a
                # controller retry.  Other model-reaching failures retain C1's
                # bounded retry lineage and its frozen per-member budget.
                refused = any("(refused)" in item for item in incomplete)
                if refused:
                    changed = db.intel.settle_bound_execution(
                        job, error=detail, terminal_outcome="refused",
                    )
                else:
                    changed = _retry_or_fail_job(
                        db, job, detail, max_attempts=retry_max_attempts,
                        base_delay_seconds=retry_base_seconds,
                        max_delay_seconds=retry_max_seconds,
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
    # Pending Stop settlements are revisited before any claim. A known-safe
    # activation falls through into this same normal C1 claim turn; an unknown
    # terminal reports durable recovery progress and is claimed on the next turn.
    from .kernel.runtime import _service

    if _reconcile_stop_handoffs(db, _service()):
        return True
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
        from .meeting_session.deferred_bound import BoundDeferredIntelJob

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
    # Pre-C claimed/running rows lack a durable parent/bundle authority.  Their
    # provider disposition may already be unknown, so cut them over before any
    # recovery scan and never route them to an executor.
    if db.intel.cut_over_legacy_unbound_intel_jobs():
        return True
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
