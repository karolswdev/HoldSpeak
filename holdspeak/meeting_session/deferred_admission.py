"""The post-close deferred meeting-intelligence job parent (HS-131-08 Part B).

A claimed deferred-intel queue job runs AFTER the live ``meeting.session``
parent was cancelled and closed at ``stop()``. It therefore never joins, reopens
or revives that parent (Sol: a closed live parent cannot honestly authorize new
children). Instead each claim admits ONE short-lived
``meeting.deferred-intel-job`` parent, under the narrow queue-worker service
principal, over a FRESHLY frozen plan and a finite deadline/budget derived from
that job's work envelope.

Every actual provider dispatch under it is one trusted ``inference.invoke@1``
child through :func:`holdspeak.meeting_session.intel_child.run_admitted_child`:
the one base analysis (``holdspeak.meeting-deferred-analysis@1``) and each
executed routed plugin (``holdspeak.meeting-plugin:<plugin-id>@1``). Deduped,
skipped, and fault-injected plugins issue no child. Each queue RETRY is a NEW
job parent, never a reopened epoch.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Mapping, Optional, Sequence

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .intel_child import MeetingAdapter, run_admitted_capability, sha
from .intel_plan import (
    CAPABILITY_AUTO_TITLE,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_DEFERRED_ANALYSIS,
    DISPLACED_AUTO_TITLE,
    DISPLACED_BOOKMARK_LABELS,
    PLUGIN_CAPABILITY_PREFIX,
    MeetingIntelRefused,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
    freeze_meeting_intel_plan,
)

log = get_logger("intel_queue")

PARENT_KIND = "meeting.deferred-intel-job"
QUEUE_SERVICE_IDENTITY = "meeting-intel-queue"
QUEUE_AUTHORITY_BASIS = "meeting-intel-queue:deferred"

CONTRACT_DEFERRED_ANALYSIS = "holdspeak.meeting-deferred-analysis"
CONTRACT_PLUGIN_PREFIX = "holdspeak.meeting-plugin:"
# The displaced live seams keep their own contracts: the work is the same work,
# only the parent that authorizes it changed.
CONTRACT_BOOKMARK_LABEL = "holdspeak.meeting-bookmark-label"
CONTRACT_AUTO_TITLE = "holdspeak.meeting-auto-title"

PROJECTION_DEFERRED_ANALYSIS = "meeting-deferred-analysis"
PROJECTION_PLUGIN_RESULT = "meeting-plugin-result"
# Post-close displaced work has NO live session to apply it, so these two kinds
# are materialized: the meeting title and the bookmark labels are written inside
# the finalization transaction the winning child receipt permits.
PROJECTION_DEFERRED_BOOKMARK_LABEL = "meeting-deferred-bookmark-label"
PROJECTION_DEFERRED_AUTO_TITLE = "meeting-deferred-auto-title"

#: The displaced-work slug -> the plan capability it needs.
DISPLACED_CAPABILITIES = {
    DISPLACED_BOOKMARK_LABELS: CAPABILITY_BOOKMARK_LABEL,
    DISPLACED_AUTO_TITLE: CAPABILITY_AUTO_TITLE,
}

# The job's finite envelope. A deferred job is bounded work over one frozen
# transcript, not an open-ended session: it may take half an hour and no longer.
JOB_DEADLINE_SECONDS = 30 * 60
# The declared in-job retry allowance. Provider-reaching retries inside ONE job
# are distinct children, so the budget must pay for them explicitly; exhausting
# it refuses instead of silently overrunning.
JOB_RETRY_ALLOWANCE = 2
ANALYSIS_DEADLINE_SECONDS = 600.0
PLUGIN_DEADLINE_SECONDS = 300.0
# Displaced label/title work is short by construction: one bounded prompt each.
DISPLACED_DEADLINE_SECONDS = 120.0


def queue_service_principal() -> Principal:
    """The narrow queue-worker identity: admit this job, dispatch its children.

    Not an owner and not the meeting's route principal. Its authority is the
    queue's own bounded execution decision, so it can neither elevate itself nor
    bypass a refusal the live session already recorded.
    """
    return Principal(
        PrincipalKind.SERVICE,
        QUEUE_SERVICE_IDENTITY,
        frozenset({(PARENT_KIND, 1), ("inference.invoke", 1), ("inference.cancel", 1)}),
        QUEUE_AUTHORITY_BASIS,
    )


def job_child_budget(planned_plugins: int, displaced_children: int = 0) -> int:
    """1 base analysis + one per planned plugin + displaced work + the retries.

    ``displaced_children`` is the number of dispatches the stop handoff displaced
    onto this job (one per bookmark label, one auto title): admitted work must be
    paid for by the budget, never overrun it silently.
    """
    return (
        1
        + max(0, int(planned_plugins))
        + max(0, int(displaced_children))
        + JOB_RETRY_ALLOWANCE
    )


def plugin_capability(plugin_id: str) -> str:
    return f"{PLUGIN_CAPABILITY_PREFIX}{plugin_id}"


class DeferredIntelJob:
    """One admitted deferred job parent and its trusted provider children."""

    def __init__(
        self,
        broker: Any,
        principal: Principal,
        plan: Any,
        parent: Any,
        *,
        meeting_id: str,
        attempt: int,
    ) -> None:
        self._broker = broker
        self._principal = principal
        self.plan = plan
        self.parent = parent
        self.meeting_id = str(meeting_id)
        self.attempt = int(attempt)
        self._closed = False

    # ------------------------------------------------------------- admission

    @classmethod
    def admit(
        cls,
        db: Any,
        *,
        meeting_id: str,
        attempt: int,
        transcript_hash: str,
        attempt_key: str = "",
        plugin_ids: Sequence[str] = (),
        meeting_config: Any = None,
        broker: Any = None,
        displaced_work: Sequence[str] = (),
        displaced_children: int = 0,
    ) -> "DeferredIntelJob":
        """Admit ONE job parent over a freshly frozen deferred plan.

        ``displaced_work`` names the work the stop handoff moved onto this job
        (HS-131-08 D3): each named item's capability is frozen in THIS plan, so the
        displaced bookmark-label / auto-title dispatches are admitted children of
        this job. A job with no displaced work freezes nothing extra and therefore
        cannot dispatch them at all.

        Raises :class:`MeetingIntelRefused` when the kernel refuses; the caller
        takes the queue's existing retry/failure path rather than dispatching.
        """
        from ..kernel.runtime import _service

        broker = broker if broker is not None else _service()
        principal = queue_service_principal()
        planned = tuple(dict.fromkeys(str(item) for item in plugin_ids if str(item).strip()))
        displaced = tuple(dict.fromkeys(str(item) for item in displaced_work if str(item).strip()))
        capabilities = (CAPABILITY_DEFERRED_ANALYSIS,) + tuple(
            DISPLACED_CAPABILITIES[slug] for slug in displaced if slug in DISPLACED_CAPABILITIES
        )
        now = time.time()
        deadline = now + JOB_DEADLINE_SECONDS
        budget = job_child_budget(len(planned), displaced_children)
        try:
            plan = freeze_meeting_intel_plan(
                db,
                meeting_id=str(meeting_id),
                capabilities=capabilities,
                deadline_at=deadline,
                child_budget=budget,
                provenance="deferred-queue",
                meeting_config=meeting_config,
                plugin_ids=planned,
                created_at=now,
            )
            parent = broker.parent_run_controller.start(
                principal,
                kind=PARENT_KIND,
                definition_ref=f"meeting:{meeting_id}:deferred:{int(attempt)}",
                definition_revision=plan.sha256,
                input_snapshot={
                    **plan.summary(),
                    "queue_attempt": int(attempt),
                    "transcript_sha256": sha(transcript_hash),
                    "displaced_work": list(displaced),
                },
                deadline_at=deadline,
                child_budget=budget,
                # The queue job's attempt key: a replayed claim of the SAME
                # attempt replays this parent; every RETRY (a new attempt, or a
                # requeue with a new requested-at) is a new bounded execution
                # decision and therefore a NEW parent, never a reopened epoch.
                idempotency_key=(
                    f"meeting-deferred-intel:{meeting_id}:{int(attempt)}"
                    + (f":{attempt_key}" if attempt_key else "")
                ),
            )
        except MeetingIntelRefused:
            raise
        except Exception as exc:
            reason = str(getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
            raise MeetingIntelRefused(reason, CAPABILITY_DEFERRED_ANALYSIS) from None
        log.info(
            "deferred intel job admitted: meeting=%s attempt=%s parent=%s plan=%s budget=%s",
            meeting_id, attempt, parent.operation_id, plan.sha256, budget,
        )
        return cls(broker, principal, plan, parent, meeting_id=meeting_id, attempt=attempt)

    # -------------------------------------------------------------- children

    def analyze(self, transcript: str) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """The job's ONE base-analysis attempt, as a trusted child."""

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return engine.analyze(payload["transcript_material"], stream=False)

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "transcript_sha256": payload["transcript_sha256"],
                "summary": str(getattr(result, "summary", "") or ""),
                "topics": [str(topic) for topic in (getattr(result, "topics", None) or [])],
                "action_item_count": len(getattr(result, "action_items", None) or []),
                "provider_error": str(getattr(result, "error", "") or ""),
            }

        return self._child(
            capability=CAPABILITY_DEFERRED_ANALYSIS,
            contract=CONTRACT_DEFERRED_ANALYSIS,
            projection_kind=PROJECTION_DEFERRED_ANALYSIS,
            material={
                "transcript_sha256": sha(transcript),
                "template_revision": "1",
                "queue_attempt": self.attempt,
                "transcript_material": transcript,
            },
            call=call,
            encode=encode,
            seed=(sha(transcript), self.attempt),
            deadline_seconds=ANALYSIS_DEADLINE_SECONDS,
        )

    def bookmark_label(
        self, *, local_context: str, meeting_summary: str, timestamp: float
    ) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """ONE displaced bookmark-label dispatch, as a trusted child.

        The earned label is written to the bookmark row by the in-transaction
        materializer under this child's winning receipt — never by this thread.
        """

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return engine.generate_bookmark_label_with_context(
                local_context=payload["context_material"],
                meeting_summary=payload["summary_material"],
            )

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "label": str(result or ""),
                "bookmark_timestamp": float(payload["bookmark_timestamp"]),
            }

        return self._child(
            capability=CAPABILITY_BOOKMARK_LABEL,
            contract=CONTRACT_BOOKMARK_LABEL,
            projection_kind=PROJECTION_DEFERRED_BOOKMARK_LABEL,
            material={
                "context_sha256": sha(local_context),
                "summary_sha256": sha(meeting_summary),
                "bookmark_timestamp": float(timestamp),
                "template_revision": "1",
                "queue_attempt": self.attempt,
                "context_material": local_context,
                "summary_material": meeting_summary,
            },
            call=call,
            encode=encode,
            seed=(timestamp, sha(local_context), sha(meeting_summary), self.attempt),
            deadline_seconds=DISPLACED_DEADLINE_SECONDS,
        )

    def auto_title(self, transcript: str) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """ONE displaced auto-title dispatch, as a trusted child.

        The earned title is written to the meeting row by the in-transaction
        materializer under this child's winning receipt.
        """

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return engine.generate_title(payload["transcript_material"])

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "title": str(result or ""),
                "transcript_sha256": payload["transcript_sha256"],
            }

        return self._child(
            capability=CAPABILITY_AUTO_TITLE,
            contract=CONTRACT_AUTO_TITLE,
            projection_kind=PROJECTION_DEFERRED_AUTO_TITLE,
            material={
                "transcript_sha256": sha(transcript),
                "template_revision": "1",
                "queue_attempt": self.attempt,
                "transcript_material": transcript,
            },
            call=call,
            encode=encode,
            seed=(sha(transcript), self.attempt),
            deadline_seconds=DISPLACED_DEADLINE_SECONDS,
        )

    def plugin(
        self,
        plugin_id: str,
        *,
        window_id: str,
        idempotency_key: str,
        transcript_hash: str,
        execute: Callable[[Any, threading.Event], Any],
    ) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """One EXECUTED routed plugin = one trusted child + one staged result.

        ``execute`` receives the engine built from the deployment revision THIS
        child names AND that child's cancellation signal, and must run the plugin
        on the pair (HS-131-08 D2, HS-131-14): the plugin's provider work happens
        inside this dispatch, so it is inside the child's cancellation seam and its
        receipt cannot name a revision it did not use. Handing the signal down is
        what lets the plugin's dispatch handle refuse a completion that starts
        after the child was cancelled.

        The plugin's own run record and its synthesized artifacts are staged
        (``meeting-plugin-result``) and written only by the in-transaction
        materializer after this child's winning receipt.
        """

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return execute(engine, cancellation)

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            record = dict(result or {})
            return {
                "window_id": str(payload["window_id"]),
                "plugin_id": str(record.get("plugin_id") or plugin_id),
                "plugin_version": str(record.get("plugin_version") or "unknown"),
                "status": str(record.get("status") or "unknown"),
                "idempotency_key": str(record.get("idempotency_key") or payload["idempotency_key"]),
                "duration_ms": float(record.get("duration_ms") or 0.0),
                "output": record.get("output") if isinstance(record.get("output"), dict) else None,
                "error": str(record["error"]) if record.get("error") else "",
                "deduped": bool(record.get("deduped")),
            }

        return self._child(
            capability=plugin_capability(plugin_id),
            contract=f"{CONTRACT_PLUGIN_PREFIX}{plugin_id}",
            projection_kind=PROJECTION_PLUGIN_RESULT,
            material={
                "plugin_id": str(plugin_id),
                "window_id": str(window_id),
                "idempotency_key": str(idempotency_key),
                "transcript_sha256": sha(transcript_hash),
                "template_revision": "1",
            },
            call=call,
            encode=encode,
            # The exact plugin idempotency key IS the attempt identity: an exact
            # retry of the same key is the same invocation, a new key a new one.
            seed=(idempotency_key,),
            deadline_seconds=PLUGIN_DEADLINE_SECONDS,
        )

    def _child(self, **kwargs: Any) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        if self._closed:
            raise MeetingIntelRefused(SESSION_CLOSED, str(kwargs.get("capability") or ""))
        contract, call = str(kwargs["contract"]), kwargs["call"]

        def adapter_factory() -> MeetingAdapter:
            # Each frozen entry gets its OWN adapter: one adapter, one dispatch,
            # one cancellation seam.
            adapter = MeetingAdapter(contract, call)
            self.adapter = adapter
            return adapter

        return run_admitted_capability(
            broker=self._broker,
            principal=self._principal,
            plan=self.plan,
            parent=self.parent,
            adapter_factory=adapter_factory,
            **kwargs,
        )

    # ------------------------------------------------------------- lifecycle

    def cancel(self) -> str:
        try:
            return str(
                self._broker.parent_run_controller.cancel(self.parent.context, self._principal)
            )
        except Exception as exc:
            log.error("deferred intel job cancel failed: %s", type(exc).__name__)
            return ""

    def close(self, outcome: str = "succeeded") -> None:
        """Close the job parent with its honest terminal outcome, exactly once."""
        if self._closed:
            return
        self._closed = True
        try:
            if self._broker.store.receipt(self.parent.operation_id) is None:
                self._broker.parent_run_controller.close(
                    self.parent.context, outcome, principal=self._principal
                )
        except Exception as exc:
            log.error("deferred intel job close failed: %s", type(exc).__name__)

    def discard_stages(self) -> int:
        from .intel_child import discard_staged_children

        try:
            from ..db import get_database

            return discard_staged_children(
                self._broker, get_database(), self.parent.operation_id
            )
        except Exception as exc:
            log.error("deferred intel stage discard failed: %s", type(exc).__name__)
            return 0


__all__ = [
    "ANALYSIS_DEADLINE_SECONDS",
    "CONTRACT_AUTO_TITLE",
    "CONTRACT_BOOKMARK_LABEL",
    "CONTRACT_DEFERRED_ANALYSIS",
    "CONTRACT_PLUGIN_PREFIX",
    "DISPLACED_CAPABILITIES",
    "DISPLACED_DEADLINE_SECONDS",
    "PROJECTION_DEFERRED_AUTO_TITLE",
    "PROJECTION_DEFERRED_BOOKMARK_LABEL",
    "DeferredIntelJob",
    "JOB_DEADLINE_SECONDS",
    "JOB_RETRY_ALLOWANCE",
    "PARENT_KIND",
    "PLUGIN_DEADLINE_SECONDS",
    "PROJECTION_DEFERRED_ANALYSIS",
    "PROJECTION_PLUGIN_RESULT",
    "QUEUE_SERVICE_IDENTITY",
    "SESSION_CLOSED",
    "job_child_budget",
    "plugin_capability",
    "queue_service_principal",
]
