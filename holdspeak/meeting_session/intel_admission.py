"""Admitted meeting intelligence: one session parent, one door job per call (HS-131-08).

Every model call of a live session (transcription, live analysis, bookmark
labels, the title) runs through the engine door as a trusted
``inference.invoke@1`` child of a single authenticated ``meeting.session``
parent. The door names the engine from the owner's live assignment; the
kernel receipt of each child records which engine answered.

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
    DISPLACED_LABELS,
    MeetingIntelRefused,
    PRINCIPAL_REQUIRED,
    SESSION_CAPABILITIES,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
)
from .transcribe_admission import (
    SPEECH_JOB,
    TRANSCRIPTION_INTERVAL_SECONDS,
    TRANSCRIPTION_NOT_ADMITTED,
    RoutedMeetingTranscriptionAdmission,
    TranscribeAdmissionMixin,
    session_child_budget,
    speech_evidence,
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
    LIVE_JOBS,
    displaced_work_for_stop,
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
        """Admit the OWNER Meeting parent and read the engines its jobs run on.

        The engine door names each job's engine from the owner's live
        assignment (``engine_door.engine_for``). A text job reads it again at
        each call; transcription keeps the one it started with, because the
        transcriber is built for it. Nothing is planned or frozen.
        """
        self._intel_refusal = ""
        self._transcription_refusal = ""
        self._intel_plan = None
        self._intel_parent = None
        self._live_engines = None
        self._speech_evidence = None
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
        from dataclasses import replace

        from ..services import engine_door

        broker = self._intel_broker()
        jobs = list(LIVE_JOBS) if self.intel_enabled else []
        jobs.append(SPEECH_JOB)
        engines: dict[str, Any] = {}
        for job in jobs:
            try:
                engines[job] = engine_door.engine_for(broker, job)
            except engine_door.EngineDoorError:
                continue
        if SPEECH_JOB in engines:
            # The transcriber is built for this engine: no retry on another.
            engines[SPEECH_JOB] = replace(engines[SPEECH_JOB], fallback=None)
        if not engines or (not self.intel_enabled and SPEECH_JOB not in engines):
            # Nothing this Meeting asks for has an engine.
            what = "intelligence" if self.intel_enabled else "transcription"
            self._refuse_session(
                "no_assignment",
                f"Meeting {what} refused: no_assignment. Recording continues.",
            )
            log.warning("meeting %s refused: no_assignment", what)
            return False
        interval_count = int(
            (SESSION_DEADLINE_SECONDS + TRANSCRIPTION_INTERVAL_SECONDS - 1)
            // TRANSCRIPTION_INTERVAL_SECONDS
        )
        source_count = 2 + len(self._requested_remote_device_ids)  # mic + system + remotes
        child_budget = (SESSION_CHILD_BUDGET if self.intel_enabled else 0) + (
            2 * source_count * (interval_count + 1) + 3 if SPEECH_JOB in engines else 0
        )
        try:
            deadline = time.time() + SESSION_DEADLINE_SECONDS
            self._intel_parent = broker.parent_run_controller.start(
                principal,
                kind="meeting.session",
                definition_ref=f"meeting:{self._state.id}:intel",
                definition_revision="meeting-live-door-1",
                input_snapshot={
                    "schema": "MeetingLiveSession@2",
                    "meeting_id": self._state.id,
                    "provenance": str(self._state.provenance or "desktop"),
                    "jobs": sorted(engines),
                },
                deadline_at=deadline,
                child_budget=max(1, child_budget),
                idempotency_key=f"meeting-session:{self._state.id}",
            )
        except Exception as exc:
            reason = str(getattr(exc, "code", "") or getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
            self._refuse_session(
                reason,
                f"Meeting intelligence refused: {reason}. Recording continues.",
            )
            log.error("meeting session admission refused: %s (%s)", reason, exc)
            return False
        self._live_engines = engines
        if SPEECH_JOB not in engines:
            # Raw capture continues; the degradation is visible on the meeting.
            self._record_only({
                "family": "speech-recognition-route-assignments",
                "reason_code": "transcription_no_speech_assignment",
                "repair": "repair_audio_model_lifecycle",
            })
            log.info(
                "meeting intelligence admitted (no speech engine): parent=%s transcription_status=record_only",
                self._intel_parent.operation_id,
            )
            return True
        try:
            evidence = speech_evidence(broker.database, engines[SPEECH_JOB])
        except Exception:
            evidence = None
        if evidence is None:
            self._refuse_session(
                TRANSCRIPTION_NOT_ADMITTED,
                "Meeting intelligence refused: frozen transcription evidence is missing. Recording continues.",
            )
            return False
        self._speech_evidence = evidence
        self._frozen_transcription = {
            "backend": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "deployment_revision_id": str(evidence["deployment_revision_id"]),
        }
        if self._frozen_transcription["backend"] in {"mlx", "faster-whisper"}:
            current = self.transcriber
            # A loaded instance serves this Meeting only when its preload
            # receipt names the same engine; otherwise it is rebuilt.
            if current is not None and bool(getattr(current, "loaded", False)):
                admission = RoutedMeetingTranscriptionAdmission(self, "lifecycle", 0.0, 0.0, False)
                if not admission.loaded_artifact_reusable(getattr(current, "_impl", None)):
                    self.transcriber = None
            self._resolved_transcription_backend = self._frozen_transcription["backend"]
            self._transcription_backend = self._frozen_transcription["backend"]
            self._transcription_model_name = self._frozen_transcription["model"]
        log.info("meeting intelligence admitted: parent=%s", self._intel_parent.operation_id)
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
        """Cancel the admitted parent after a capture-start failure, if one exists."""
        if self._intel_parent is None or self.intel_principal is None:
            return
        try:
            self._cancel_intel_session()
            self._finish_cancelled_intel_session()
        except Exception as exc:
            log.error("meeting parent unwind failed at %s: %s", stage, type(exc).__name__)

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
        """Stop the live jobs, end the parent cancelled, queue the deferred work.

        The final transcription pass has already completed when this method is
        entered. Each running door job is stopped (``engine_door.stop``); the
        work the Meeting still owes is one queue upsert.
        """
        # The in-memory gate closes publication and fresh Meeting-side admission
        # before the durable parent fence.  `_apply_live_window()` rechecks this
        # under the same lock, so a late elected result cannot reach a callback.
        with self._lock:
            self._intel_closed = True
            self._intel_live = False
        self._stop_door_runs()

        # A speech-only recording has no text work to hand off, including the
        # untitled-meeting auto-title path.
        displaced = displaced_work_for_stop(state, self.intel_enabled)
        self._intel_displaced_work = displaced
        detail = (
            "Meeting saved. Live intelligence stopped with the recording; "
            + ", ".join(DISPLACED_LABELS[slug] for slug in displaced)
            + " queued for deferred processing."
        ) if displaced else "Meeting saved. No deferred intelligence was requested."
        if self._deferred_intel_reason and displaced:
            detail += f" Earlier deferral: {self._deferred_intel_reason}"

        from ..db import get_database

        database = get_database()
        # The live parent ends cancelled: Stop is the owner's decision.
        if self._intel_parent is not None and self.intel_principal is not None:
            try:
                self._cancel_intel_session()
            finally:
                self._finish_cancelled_intel_session()
        if displaced:
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
                # Recovery (``recover_capture``) queues the same work again.
                database.meetings.mark_route_fence_pending(state.id, f"{type(exc).__name__}: {exc}")
                self._set_intel_status(
                    "error",
                    f"Deferred intelligence could not be queued: {exc}",
                    after_handoff=True,
                )
                return tuple(displaced)

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
