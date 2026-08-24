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
import hashlib


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()

from .intel_plan import (
    CAPABILITY_AUTO_TITLE,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_DEFERRED_ANALYSIS,
    CAPABILITY_LIVE_ANALYSIS,
    TRANSCRIPTION_CAPABILITIES,
    DISPLACED_AUTO_TITLE,
    DISPLACED_BOOKMARK_LABELS,
    DISPLACED_FINAL_ANALYSIS,
    DISPLACED_LABELS,
    MeetingIntelRefused,
    PRINCIPAL_REQUIRED,
    SESSION_CAPABILITIES,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
)
from .transcribe_admission import (
    TRANSCRIPTION_INTERVAL_SECONDS,
    TRANSCRIPTION_NOT_ADMITTED,
    TranscribeAdmissionMixin,
    session_child_budget,
)

log = get_logger("meeting_session")

from .intel_routed_children import (
    CONTRACT_AUTO_TITLE,
    CONTRACT_BOOKMARK_LABEL,
    CONTRACT_LIVE_ANALYSIS,
    IntelRoutedChildMixin,
    LABEL_DEADLINE_SECONDS,
    PROJECTION_AUTO_TITLE,
    PROJECTION_BOOKMARK_LABEL,
    PROJECTION_LIVE_WINDOW,
    ROUTE_AUTO_TITLE,
    ROUTE_BOOKMARK_LABEL,
    ROUTE_LIVE_ANALYSIS,
    WINDOW_DEADLINE_SECONDS,
    WINDOW_SUPERSEDED,
)

# The parent lifetime remains owned by the admission/lifecycle mixin. Child
# deadlines and route identifiers live with the extracted routed-child mixin.
SESSION_DEADLINE_SECONDS = 12 * 60 * 60
SESSION_CHILD_BUDGET = 4096
CANCEL_DRAIN_SECONDS = 15.0


class IntelAdmissionMixin(IntelRoutedChildMixin, TranscribeAdmissionMixin):
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
        self._intel_live = False
        self.intel_enabled = False
        if self._state is not None:
            self._state.intel_status = "refused"
            self._state.intel_status_detail = detail

    def _admit_intel_session(self) -> bool:
        """Atomically admit the OWNER Meeting parent and complete live bundle."""
        self._intel_refusal = ""
        self._transcription_refusal = ""
        self._intel_plan = None  # v1 reader only; production sessions use the bundle.
        self._intel_parent = None
        self._route_bundle = None
        self._intel_closed = False
        self._intel_live = False
        if self._state is None:
            return False
        principal = self.intel_principal
        if principal is None or str(getattr(principal, "name", "none")) == "none":
            self._refuse_session(
                PRINCIPAL_REQUIRED,
                f"Meeting intelligence refused: {PRINCIPAL_REQUIRED}. Recording continues.",
            )
            log.warning("meeting session refused: %s", PRINCIPAL_REQUIRED)
            return False
        requested = tuple(self._requested_remote_device_ids)
        interval_count = int(
            (SESSION_DEADLINE_SECONDS + TRANSCRIPTION_INTERVAL_SECONDS - 1)
            // TRANSCRIPTION_INTERVAL_SECONDS
        )
        source_count = 2 + len(requested)  # mic + system + frozen requested remotes
        transcription_budget = 2 * source_count * (interval_count + 1) + 2
        # The caller's mutable ModelConfig may establish the migration input but
        # is never execution authority.  Candidate/model/language material is
        # derived inside bundle admission from the frozen speech deployment.
        # Reserve the one bounded lifecycle child up front; a matching already
        # warm instance simply leaves that capacity unused.
        preload_budget = 1
        preload_declaration = {
            "key": "preload",
            "source_key": "transcription",
            "candidate_material": [],
            "strategy_sequence": ["derive-from-frozen-transcription"],
        }
        budget_groups = (
            {
                "id": "meeting-intelligence",
                "allocation": SESSION_CHILD_BUDGET,
                "member_keys": ["live-analysis", "bookmark-label", "auto-title"],
            },
            {
                "id": "meeting-transcription",
                "allocation": transcription_budget,
                "member_keys": ["transcription"],
            },
            {
                "id": "meeting-preload",
                "allocation": preload_budget,
                "member_keys": ["preload"],
            },
        )
        try:
            from ..services.inference_parent_route_bundle_service import InferenceParentRouteBundleService

            broker = self._intel_broker()
            deadline = time.time() + SESSION_DEADLINE_SECONDS
            started = InferenceParentRouteBundleService(
                broker, broker.inference_adoption_service
            ).start(
                principal,
                command_id=f"meeting-route-bundle:{self._state.id}",
                parent_kind="meeting.session",
                definition_ref=f"meeting:{self._state.id}:intel",
                definition_revision="meeting-live-bundle-1",
                input_snapshot={
                    "schema": "MeetingLiveBundleInput@1",
                    "meeting_id": self._state.id,
                    "provenance": str(self._state.provenance or "desktop"),
                    "deadline_at": deadline,
                    "budget_groups": [
                        {"id": group["id"], "allocation": group["allocation"]}
                        for group in budget_groups
                    ],
                },
                deadline_at=deadline,
                routes=(
                    {"key": "live-analysis", "capability_id": ROUTE_LIVE_ANALYSIS, "invocation_id": self._state.id},
                    {"key": "bookmark-label", "capability_id": ROUTE_BOOKMARK_LABEL, "invocation_id": self._state.id},
                    {"key": "auto-title", "capability_id": ROUTE_AUTO_TITLE, "invocation_id": self._state.id},
                    {"key": "transcription", "capability_id": "speech.transcribe", "invocation_id": self._state.id},
                ),
                budget_groups=budget_groups,
                derived_preload=preload_declaration,
                requested_remote_device_ids=requested,
            )
        except Exception as exc:
            reason = str(getattr(exc, "code", "") or getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
            self._refuse_session(
                reason,
                f"Meeting intelligence refused: {reason}. Recording continues.",
            )
            log.error("meeting session admission refused: %s (%s)", reason, exc)
            return False
        self._intel_parent = started["parent"]
        self._route_bundle = started["bundle"]
        evidence = next(iter(self._route_bundle.get("derived_preloads", ())), None)
        if not isinstance(evidence, Mapping):
            self._refuse_session(
                TRANSCRIPTION_NOT_ADMITTED,
                "Meeting intelligence refused: frozen transcription evidence is missing. Recording continues.",
            )
            return False
        self._frozen_transcription = {
            "backend": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "deployment_revision_id": str(evidence["deployment_revision_id"]),
        }
        if self._frozen_transcription["backend"] in {"mlx", "faster-whisper"}:
            current = self.transcriber
            # An unloaded instance has not yet been reused: it is the candidate
            # that this newly admitted Meeting will warm under its own P=1 route.
            # Only an already loaded artifact needs receipt-gated reuse proof.
            if current is not None and bool(getattr(current, "loaded", False)):
                from ..speech_session.transcription import _durable_preload_provenance_matches

                reusable = _durable_preload_provenance_matches(
                    broker,
                    getattr(getattr(current, "_impl", None), "_holdspeak_preload_provenance", {}),
                    deployment_revision_id=self._frozen_transcription["deployment_revision_id"],
                    engine=self._frozen_transcription["backend"],
                    model=self._frozen_transcription["model"],
                    language=self._frozen_transcription["language"],
                )
                if not reusable:
                    # Construction strings alone are not reuse authority.  A
                    # matching deployment revision and durable successful
                    # preload/load receipt are both required; faster-whisper has
                    # no such separable receipt, so it reconstructs after route
                    # admission.
                    self.transcriber = None
            self._resolved_transcription_backend = self._frozen_transcription["backend"]
            self._transcription_backend = self._frozen_transcription["backend"]
            self._transcription_model_name = self._frozen_transcription["model"]
        # A fresh bundle-backed Meeting never reconstructs a legacy speech plan.
        # The bundle's transcription member is the only execution authority;
        # `SpeechSessionPlan` remains readable solely for pre-cutover history.
        log.info(
            "meeting intelligence bundle admitted: parent=%s bundle=%s",
            self._intel_parent.operation_id,
            self._route_bundle["id"],
        )
        return True

    def _record_only(self, issue: Mapping[str, Any]) -> None:
        """Stamp content-free transcription repair state while raw capture continues."""
        if self._state is None:
            return
        self._transcription_refusal = str(issue.get("reason_code") or SESSION_NOT_ADMITTED)
        self._state.transcription_status = "record_only"
        self._state.transcription_status_detail = {
            "family": str(issue.get("family") or "speech-recognition-route-assignments"),
            "reason_code": self._transcription_refusal,
            "repair": str(issue.get("repair") or "repair_meeting_route_assignment"),
        }

    def _refuse_session(self, reason: str, detail: str) -> None:
        """Record the refusal on every face the session has.

        With intelligence enabled that is the named intel status; with
        intelligence disabled there is no intel face to stamp — only transcription
        was refused, and the recording keeps its honest ``disabled`` intel status.
        """
        self._transcription_refusal = reason
        if self._state is not None:
            self._state.transcription_status = "record_only"
            self._state.transcription_status_detail = {
                "family": "meeting-route-assignments",
                "reason_code": str(reason),
                "repair": "repair_meeting_route_assignment",
            }
        if self.intel_enabled:
            self._intel_refuse(reason, detail)
            return
        self._intel_plan = None
        self._intel_parent = None
        self._intel_live = False

    def _intel_declared_capabilities(self) -> tuple[str, ...]:
        # HS-131-09: a recorded session always transcribes; the intelligence
        # capabilities are declared only when intelligence is actually enabled.
        declared = list(TRANSCRIPTION_CAPABILITIES)
        if not self.intel_enabled:
            return tuple(declared)
        declared.extend(SESSION_CAPABILITIES)
        if self.intel_deferred_enabled:
            declared.append(CAPABILITY_DEFERRED_ANALYSIS)
        return tuple(declared)

    def intel_session_operation_id(self) -> str:
        parent = self._intel_parent
        return "" if parent is None else str(parent.operation_id)

    def _unwind_started_bundle(self, stage: str) -> None:
        """Fence a Phase-B bundle after a capture-start failure, if one exists."""
        bundle = getattr(self, "_route_bundle", None)
        if bundle is None or self.intel_principal is None or self._state is None:
            return
        try:
            from ..services.inference_parent_route_bundle_service import InferenceParentRouteBundleService

            broker = self._intel_broker()
            InferenceParentRouteBundleService(
                broker, broker.inference_adoption_service
            ).fence_cancel(
                self.intel_principal,
                command_id=f"meeting-start-abort:{self._state.id}:{stage}",
                bundle_id=str(bundle["id"]),
            )
        except Exception as exc:
            log.error("meeting bundle unwind failed at %s: %s", stage, type(exc).__name__)

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
            return self._intel_broker().projection_stager.finalize_parent_stages(
                parent.operation_id
            )
        except Exception as exc:
            log.error("meeting intelligence stage discard failed: %s", type(exc).__name__)
            return 0

    # ----------------------------------------------------- the Stop fence

    def _handoff_intel_at_stop(self, state: Any) -> tuple[str, ...]:
        """Fence live bundle work and reserve its deferred handoff atomically.

        The final transcription pass has already completed when this method is
        entered.  It needs the still-open frozen transcription route, so this is
        the first point at which the shared live-admission fence can close it.
        A record-only Meeting has no bundle, but its pre-cutover deferred-work
        predicate and Meeting-keyed legacy queue upsert remain exactly available.
        """
        # The in-memory gate closes publication and fresh Meeting-side admission
        # before the durable parent fence.  `_apply_live_window()` rechecks this
        # under the same lock, so a late elected result cannot reach a callback.
        with self._lock:
            self._intel_closed = True
            self._intel_live = False

        # Preserve the pre-cutover product predicate independently of live route
        # admission: segments request final analysis, bookmarks request labels,
        # and an untitled Meeting requests an auto-title.  In particular, a
        # record-only Meeting has no bundle yet still owns aftercare.
        displaced: list[str] = []
        if state.segments:
            displaced.append(DISPLACED_FINAL_ANALYSIS)
        if state.bookmarks:
            displaced.append(DISPLACED_BOOKMARK_LABELS)
        if not state.title:
            displaced.append(DISPLACED_AUTO_TITLE)
        self._intel_displaced_work = tuple(displaced)
        detail = (
            "Meeting saved. Live intelligence stopped with the recording; "
            + ", ".join(DISPLACED_LABELS[slug] for slug in displaced)
            + " queued for deferred processing."
        ) if displaced else "Meeting saved. No deferred intelligence was requested."
        if self._deferred_intel_reason and displaced:
            detail += f" Earlier deferral: {self._deferred_intel_reason}"

        from ..db import get_database

        database = get_database()

        bundle = self._route_bundle
        fenced = bundle is None or self.intel_principal is None
        if bundle is not None and self.intel_principal is not None:
            from ..services.inference_parent_route_bundle_service import InferenceParentRouteBundleService

            broker = self._intel_broker()
            provider = database.intel.stop_handoff_provider(
                meeting_id=state.id,
                transcript_hash=state.transcript_hash(),
                displaced_work=tuple(displaced),
                reason=detail,
            ) if displaced else None
            service = InferenceParentRouteBundleService(
                broker,
                broker.inference_adoption_service,
                handoff_evidence_providers=(provider,) if provider is not None else (),
            )
            fence_error: Exception | None = None
            for attempt in (1, 2):
                try:
                    if provider is None:
                        effect = service.fence_cancel(
                            self.intel_principal,
                            command_id=f"meeting-stop:{state.id}",
                            bundle_id=str(bundle["id"]),
                        )
                    else:
                        effect = service.request_stop_handoff(
                            self.intel_principal,
                            command_id=f"meeting-stop:{state.id}",
                            bundle_id=str(bundle["id"]),
                            evidence_provider_id=provider.id,
                            planning_reference=database.intel.stop_handoff_planning_reference(state.id),
                        )
                    log.info(
                        "live meeting bundle stop handed off: bundle=%s routes=%s",
                        effect["bundle_id"],
                        len(effect["route_stops"]),
                    )
                    fenced = True
                    break
                except Exception as exc:
                    fence_error = exc
                    log.warning(
                        "live meeting bundle handoff attempt %s failed: %s",
                        attempt,
                        type(exc).__name__,
                    )
            if not fenced:
                assert fence_error is not None
                # Unlike the B-era fallback, a failed C3 handoff must not write a
                # separately runnable legacy row.  Recovery repeats this exact
                # atomic request, which either creates the inert reservation with
                # the fence or leaves neither durable effect behind.
                database.meetings.mark_route_fence_pending(
                    state.id, f"{type(fence_error).__name__}: {fence_error}"
                )
        elif displaced:
            try:
                database.intel.enqueue_intel_job(
                    state.id,
                    transcript_hash=state.transcript_hash(),
                    reason=detail,
                    displaced_work=tuple(displaced),
                    legacy_displaced_work=True,
                )
            except Exception as exc:
                log.error("deferred intel handoff enqueue failed: %s", exc)
                self._set_intel_status(
                    "error",
                    f"Deferred intelligence could not be queued: {exc}",
                    after_handoff=True,
                )
                return tuple(displaced)

        # The old parent close/cancel path is intentionally not used for a bundle:
        # the handoff primitive derives and fences the complete route set in one
        # durable transaction, then performs best-effort physical child cancellation.
        self._intel_parent = None
        self._intel_closed = True
        if not displaced:
            return ()
        # A mid-meeting live window may have stamped `ready`; the deferred job is
        # still outstanding, so the completion stamp must go with it.
        with self._lock:
            if self._state is not None:
                self._state.intel_completed_at = None
        state.intel_completed_at = None
        self._set_intel_status("queued", detail, after_handoff=True)
        log.info("deferred intel handoff enqueued for %s: %s", state.id, ", ".join(displaced))
        return tuple(displaced)



__all__ = [
    "CONTRACT_AUTO_TITLE",
    "CONTRACT_BOOKMARK_LABEL",
    "CONTRACT_LIVE_ANALYSIS",
    "IntelAdmissionMixin",
    "PROJECTION_AUTO_TITLE",
    "PROJECTION_BOOKMARK_LABEL",
    "PROJECTION_LIVE_WINDOW",
    "SESSION_CHILD_BUDGET",
    "SESSION_DEADLINE_SECONDS",
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "WINDOW_SUPERSEDED",
    "session_child_budget",
]
