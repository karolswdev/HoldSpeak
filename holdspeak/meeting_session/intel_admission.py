"""Admitted meeting intelligence: one session parent, one child per dispatch (HS-131-08).

Every ACTUAL meeting-intelligence provider dispatch during a live session runs
as one trusted ``inference.invoke@1`` child of a single authenticated
``meeting.session`` parent. Nothing here resolves placement: the frozen
:class:`~holdspeak.meeting_session.intel_plan.MeetingIntelPlan` decided that at
admission, and a capability missing from the plan is a named refusal.

Transcript, bookmark context, and prompt material ride ONLY inside the
dispatched payload. The payload is hashed into the service contract; the kernel
journal records ``{contract, revision, payload_hash}`` and nothing else.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .intel_child import (
    MeetingProviderFailure,
    discard_staged_children,
    run_admitted_capability,
    sha as _sha,
)
from .intel_plan import (
    CAPABILITY_AUTO_TITLE,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_DEFERRED_ANALYSIS,
    CAPABILITY_LIVE_ANALYSIS,
    DISPLACED_AUTO_TITLE,
    DISPLACED_BOOKMARK_LABELS,
    DISPLACED_FINAL_ANALYSIS,
    DISPLACED_LABELS,
    DISPLACED_ROUTED_INTELLIGENCE,
    MeetingIntelRefused,
    PRINCIPAL_REQUIRED,
    SESSION_CAPABILITIES,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
    freeze_meeting_intel_plan,
)

log = get_logger("meeting_session")

CONTRACT_LIVE_ANALYSIS = "holdspeak.meeting-live-analysis"
CONTRACT_BOOKMARK_LABEL = "holdspeak.meeting-bookmark-label"
CONTRACT_AUTO_TITLE = "holdspeak.meeting-auto-title"

PROJECTION_LIVE_WINDOW = "meeting-live-window"
PROJECTION_BOOKMARK_LABEL = "meeting-bookmark-label"
PROJECTION_AUTO_TITLE = "meeting-auto-title"

# A live meeting-intelligence lifetime is finite and explicit: no silent
# renewal, no epoch reset. A new window past either fence needs a new
# authenticated continuation decision (a new parent and a new plan).
SESSION_DEADLINE_SECONDS = 12 * 60 * 60
SESSION_CHILD_BUDGET = 4096
WINDOW_DEADLINE_SECONDS = 300.0
LABEL_DEADLINE_SECONDS = 120.0
# Bounded wait for an in-flight child's terminal receipt at stop. Bounded, never
# infinite: an unacknowledged provider is `indeterminate`, not a hung stop.
CANCEL_DRAIN_SECONDS = 15.0

WINDOW_SUPERSEDED = "meeting_live_window_superseded"


class IntelAdmissionMixin:
    """Session-side admission of the meeting parent and its provider children."""

    # ---------------------------------------------------------------- parent

    def _intel_broker(self) -> Any:
        from ..kernel.runtime import _service

        return _service()

    def _intel_refuse(self, reason: str, detail: str) -> None:
        """Disable intelligence with an honest named status; recording continues."""
        self._intel_refusal = reason
        self._intel_plan = None
        self._intel_parent = None
        self._intel = None
        self.intel_enabled = False
        if self._state is not None:
            self._state.intel_status = "refused"
            self._state.intel_status_detail = detail

    def _admit_intel_session(self) -> bool:
        """Admit ONE authenticated ``meeting.session`` parent over a frozen plan.

        Called immediately after ``MeetingState`` exists and before any Intel
        engine. A start with no authenticated principal admits NOTHING: the
        recording proceeds and intelligence is refused by name. Synthesizing an
        OWNER principal for a device/auto start would be authority elevation.
        """
        self._intel_refusal = ""
        self._intel_plan = None
        self._intel_parent = None
        self._intel_closed = False
        if not self.intel_enabled or self._state is None:
            return False
        principal = self.intel_principal
        if principal is None or str(getattr(principal, "name", "none")) == "none":
            self._intel_refuse(
                PRINCIPAL_REQUIRED,
                f"Meeting intelligence refused: {PRINCIPAL_REQUIRED}. Recording continues.",
            )
            log.warning("meeting intelligence refused: %s", PRINCIPAL_REQUIRED)
            return False
        try:
            from ..db import get_database

            database = get_database()
            broker = self._intel_broker()
            now = time.time()
            deadline = now + SESSION_DEADLINE_SECONDS
            plan = freeze_meeting_intel_plan(
                database,
                meeting_id=self._state.id,
                capabilities=self._intel_declared_capabilities(),
                deadline_at=deadline,
                child_budget=SESSION_CHILD_BUDGET,
                provenance=str(self._state.provenance or "desktop"),
                plugin_ids=self._intel_plugin_ids(),
                created_at=now,
            )
            parent = broker.parent_run_controller.start(
                principal,
                kind="meeting.session",
                definition_ref=f"meeting:{self._state.id}:intel",
                definition_revision=plan.sha256,
                input_snapshot=plan.summary(),
                deadline_at=deadline,
                child_budget=SESSION_CHILD_BUDGET,
                idempotency_key=f"meeting-intel-session:{self._state.id}",
            )
        except Exception as exc:
            reason = str(getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
            self._intel_refuse(
                reason,
                f"Meeting intelligence refused: {reason}. Recording continues.",
            )
            log.error("meeting intelligence admission refused: %s", reason)
            return False
        self._intel_plan = plan
        # The opaque context lives ONLY on the live session object; durable rows
        # keep the parent operation id and the content-free plan summary.
        self._intel_parent = parent
        log.info(
            "meeting intelligence admitted: parent=%s plan=%s", parent.operation_id, plan.sha256
        )
        return True

    def _intel_declared_capabilities(self) -> tuple[str, ...]:
        declared = list(SESSION_CAPABILITIES)
        if self.intel_deferred_enabled:
            declared.append(CAPABILITY_DEFERRED_ANALYSIS)
        return tuple(declared)

    def _intel_plugin_ids(self) -> tuple[str, ...]:
        host = getattr(self, "_mir_plugin_host", None)
        if host is None:
            return ()
        try:
            available = [str(item) for item in host.list_plugins()]
        except Exception:
            return ()
        disabled = {str(item) for item in (getattr(self, "_mir_disabled_plugins", None) or [])}
        return tuple(item for item in available if item not in disabled)

    def intel_session_operation_id(self) -> str:
        parent = self._intel_parent
        return "" if parent is None else str(parent.operation_id)

    def _close_intel_session(self, outcome: str = "succeeded") -> None:
        """Close the live parent with its honest terminal outcome, exactly once."""
        parent = self._intel_parent
        if parent is None:
            return
        self._intel_parent = None
        self._intel_closed = True
        try:
            broker = self._intel_broker()
            if broker.store.receipt(parent.operation_id) is None:
                broker.parent_run_controller.close(
                    parent.context, outcome, principal=self.intel_principal
                )
        except Exception as exc:
            log.error("meeting intelligence parent close failed: %s", type(exc).__name__)

    def _cancel_intel_session(self) -> str:
        """Fence new continuations: advance the epoch and cancel the active child.

        The controller attempts provider cancellation of the active child; an
        adapter that never acknowledges leaves the child ``indeterminate``,
        never a guessed success or failure.
        """
        parent = self._intel_parent
        if parent is None:
            return ""
        try:
            broker = self._intel_broker()
            disposition = str(
                broker.parent_run_controller.cancel(parent.context, self.intel_principal)
            )
        except Exception as exc:
            log.error("meeting intelligence cancel failed: %s", type(exc).__name__)
            return ""
        # The provider signal runs off-thread and needs the parent to still be
        # CANCELLING, so drain BEFORE electing the parent's terminal receipt.
        self._drain_intel_children()
        return disposition

    def _drain_intel_children(self, *, timeout: float = CANCEL_DRAIN_SECONDS) -> None:
        """Wait, bounded, for every in-flight child to reach a terminal receipt."""
        parent = self._intel_parent
        if parent is None:
            return
        from ..db import get_database

        database = get_database()
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            with database._connection() as conn:
                pending = conn.execute(
                    """SELECT COUNT(*) AS open_children FROM kernel_operations o
                       LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id
                       WHERE o.parent_operation_id=? AND r.operation_id IS NULL""",
                    (parent.operation_id,),
                ).fetchone()
            if int(pending["open_children"]) == 0:
                return
            if time.monotonic() >= deadline:
                log.warning("meeting intelligence cancellation drain timed out")
                return
            time.sleep(0.05)

    def _finish_cancelled_intel_session(self) -> str:
        """Elect the parent's terminal `cancelled` receipt after the epoch moved.

        Cancellation advanced the execution epoch, so the session's own context is
        stale by construction; the controller re-derives a recovery context from
        the durable owner instead of this object inventing one.
        """
        parent = self._intel_parent
        if parent is None:
            return ""
        self._intel_parent = None
        self._intel_closed = True
        try:
            broker = self._intel_broker()
            if broker.store.receipt(parent.operation_id) is not None:
                return str(broker.store.receipt(parent.operation_id)["outcome"])
            return str(
                broker.parent_run_controller.cancel_by_operation_id(
                    self.intel_principal, parent.operation_id
                )
            )
        except Exception as exc:
            log.error("meeting intelligence parent close failed: %s", type(exc).__name__)
            return ""

    def _discard_intel_stages(self) -> int:
        """Resolve every staged live projection; a cancelled parent discards them."""
        parent = self._intel_parent
        if parent is None:
            return 0
        try:
            from ..db import get_database

            return discard_staged_children(
                self._intel_broker(), get_database(), parent.operation_id
            )
        except Exception as exc:
            log.error("meeting intelligence stage discard failed: %s", type(exc).__name__)
            return 0

    # ----------------------------------------------------- the stop handoff

    def _handoff_intel_at_stop(self, state: Any) -> tuple[str, ...]:
        """Cancel the live parent, then durably enqueue the work stop displaced.

        Returns the names of the displaced work items, empty when nothing was
        admitted (recording without intelligence keeps its existing behavior).

        Order is load-bearing (Sol Amendment 2): cancel FIRST so no late live
        output can reach meeting state, resolve the staged snapshots so a
        cancelled parent discards them, close the parent with its honest terminal
        outcome, and only then enqueue — before ``stop()`` returns. The queue's
        own `queued` status is what keeps the meeting honestly in progress; it is
        never `ready` while the deferred job is outstanding.
        """
        if self._intel_parent is None:
            return ()
        # Sol Amendment 2 + the late-ready fence (HS-131-08 D4): the closed flag
        # is raised UNDER THE LOCK before anything else, so a child that finalized
        # a moment ago can no longer stamp meeting state, and no new live child can
        # be admitted, while stop is stamping `queued`.
        with self._lock:
            self._intel_closed = True
        disposition = self._cancel_intel_session()
        discarded = self._discard_intel_stages()
        self._finish_cancelled_intel_session()
        with self._lock:
            self._intel = None
        log.info(
            "live meeting intelligence cancelled at stop: disposition=%s discarded=%s",
            disposition or "cancelled",
            discarded,
        )
        if not state.segments:
            return ()

        displaced = [DISPLACED_FINAL_ANALYSIS]
        if state.bookmarks:
            displaced.append(DISPLACED_BOOKMARK_LABELS)
        if not state.title:
            displaced.append(DISPLACED_AUTO_TITLE)
        if self.mir_routing_enabled or self._mir_plugin_host is not None:
            displaced.append(DISPLACED_ROUTED_INTELLIGENCE)
        # The slugs are the machine contract; the sentence is for the owner.
        self._intel_displaced_work = tuple(displaced)
        detail = (
            "Meeting saved. Live intelligence stopped with the recording; "
            + ", ".join(DISPLACED_LABELS[slug] for slug in displaced)
            + " queued for deferred processing."
        )
        if self._deferred_intel_reason:
            detail += f" Earlier deferral: {self._deferred_intel_reason}"
        # The handoff's OWN stamps are the only meeting-state writes allowed once
        # the closed flag is up.

        try:
            from ..db import get_database

            get_database().intel.enqueue_intel_job(
                state.id,
                transcript_hash=state.transcript_hash(),
                reason=detail,
                displaced_work=tuple(displaced),
            )
        except Exception as exc:
            # The handoff is the only route to the displaced outputs, so a failure
            # here is an honest error, never a silent Ready.
            log.error("deferred intel handoff enqueue failed: %s", exc)
            self._set_intel_status(
                "error",
                f"Deferred intelligence could not be queued: {exc}",
                after_handoff=True,
            )
            return tuple(displaced)
        # A mid-meeting live window may have stamped `ready`; the deferred job is
        # still outstanding, so the completion stamp must go with it.
        with self._lock:
            if self._state is not None:
                self._state.intel_completed_at = None
        state.intel_completed_at = None
        self._set_intel_status("queued", detail, after_handoff=True)
        log.info("deferred intel handoff enqueued for %s: %s", state.id, ", ".join(displaced))
        return tuple(displaced)

    # ---------------------------------------------------------------- children

    def _intel_child(
        self,
        *,
        capability: str,
        contract: str,
        projection_kind: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
        encode: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
        seed: Any,
        attempt_ordinal: int = 1,
        deadline_seconds: float = WINDOW_DEADLINE_SECONDS,
    ) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """Run ONE admitted live-session provider dispatch through the one path.

        Raises :class:`MeetingIntelRefused` when the plan or the live parent
        refuses — before any provider request exists. Once the live parent is
        closed at ``stop()`` this refuses by construction: post-close work
        belongs to a separately admitted ``meeting.deferred-intel-job``.
        """
        plan, parent = self._intel_plan, self._intel_parent
        if getattr(self, "_intel_closed", False):
            # The recorded session is closing or closed. Deferred work admits its
            # OWN `meeting.deferred-intel-job` parent; nothing revives this one.
            raise MeetingIntelRefused(SESSION_CLOSED, capability)
        if plan is None or parent is None:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        return run_admitted_capability(
            broker=self._intel_broker(),
            principal=self.intel_principal,
            plan=plan,
            parent=parent,
            capability=capability,
            contract=contract,
            projection_kind=projection_kind,
            material=material,
            call=call,
            encode=encode,
            seed=seed,
            attempt_ordinal=attempt_ordinal,
            deadline_seconds=deadline_seconds,
        )

    # ----------------------------------------------------------- live window

    def _admitted_live_window(self, transcript: str, *, final: bool, analysis_id: str) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        """One actual live analysis window = one trusted child."""
        from ..kernel.model import KernelRefused

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            result = None
            for chunk in engine.analyze(payload["transcript_material"], stream=True):
                if cancellation.is_set():
                    break
                if self._current_analysis_id != analysis_id:
                    # A newer window superseded this one: no output may land.
                    raise KernelRefused(WINDOW_SUPERSEDED)
                if isinstance(chunk, str):
                    # Token broadcasts stay ephemeral and are never journaled.
                    self._emit_broadcast("intel_token", chunk)
                else:
                    result = chunk
            return result

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "transcript_sha256": payload["transcript_sha256"],
                "final": bool(payload["final"]),
                "summary": str(getattr(result, "summary", "") or ""),
                "topics": [str(topic) for topic in (getattr(result, "topics", None) or [])],
                "action_item_count": len(getattr(result, "action_items", None) or []),
                "provider_error": str(getattr(result, "error", "") or ""),
            }

        return self._intel_child(
            capability=CAPABILITY_LIVE_ANALYSIS,
            contract=CONTRACT_LIVE_ANALYSIS,
            projection_kind=PROJECTION_LIVE_WINDOW,
            material={
                "transcript_sha256": _sha(transcript),
                "window": {"start": 0.0, "end": float(self.duration), "segments": len(self._state.segments) if self._state else 0},
                "template_revision": "1",
                "limits": {"max_tokens": None},
                "final": bool(final),
                "analysis_id": analysis_id,
                "transcript_material": transcript,
            },
            call=call,
            encode=encode,
            seed=(_sha(transcript), final, analysis_id),
        )

    # ------------------------------------------------------ absorbed seams

    def _admitted_bookmark_label(self, *, local_context: str, meeting_summary: str, timestamp: float) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return engine.generate_bookmark_label_with_context(
                local_context=payload["context_material"],
                meeting_summary=payload["summary_material"],
            )

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"label": str(result or ""), "bookmark_timestamp": float(payload["bookmark_timestamp"])}

        return self._intel_child(
            capability=CAPABILITY_BOOKMARK_LABEL,
            contract=CONTRACT_BOOKMARK_LABEL,
            projection_kind=PROJECTION_BOOKMARK_LABEL,
            material={
                "context_sha256": _sha(local_context),
                "summary_sha256": _sha(meeting_summary),
                "bookmark_timestamp": float(timestamp),
                "template_revision": "1",
                "context_material": local_context,
                "summary_material": meeting_summary,
            },
            call=call,
            encode=encode,
            seed=(timestamp, _sha(local_context), _sha(meeting_summary)),
            deadline_seconds=LABEL_DEADLINE_SECONDS,
        )

    def _admitted_auto_title(self, transcript: str) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            if cancellation.is_set():
                return None
            return engine.generate_title(payload["transcript_material"])

        def encode(result: Any, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"title": str(result or ""), "transcript_sha256": payload["transcript_sha256"]}

        return self._intel_child(
            capability=CAPABILITY_AUTO_TITLE,
            contract=CONTRACT_AUTO_TITLE,
            projection_kind=PROJECTION_AUTO_TITLE,
            material={
                "transcript_sha256": _sha(transcript),
                "template_revision": "1",
                "transcript_material": transcript,
            },
            call=call,
            encode=encode,
            seed=_sha(transcript),
            deadline_seconds=LABEL_DEADLINE_SECONDS,
        )


__all__ = [
    "CONTRACT_AUTO_TITLE",
    "CONTRACT_BOOKMARK_LABEL",
    "CONTRACT_LIVE_ANALYSIS",
    "IntelAdmissionMixin",
    "MeetingProviderFailure",
    "PROJECTION_AUTO_TITLE",
    "PROJECTION_BOOKMARK_LABEL",
    "PROJECTION_LIVE_WINDOW",
    "SESSION_CHILD_BUDGET",
    "SESSION_DEADLINE_SECONDS",
    "WINDOW_SUPERSEDED",
]
