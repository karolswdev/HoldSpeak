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

CONTRACT_LIVE_ANALYSIS = "holdspeak.meeting-live-analysis"
CONTRACT_BOOKMARK_LABEL = "holdspeak.meeting-bookmark-label"
CONTRACT_AUTO_TITLE = "holdspeak.meeting-auto-title"

PROJECTION_LIVE_WINDOW = "meeting-live-window"
PROJECTION_BOOKMARK_LABEL = "meeting-bookmark-label"
PROJECTION_AUTO_TITLE = "meeting-auto-title"

# Phase-B registry IDs.  The similarly named imports above are v1 plan keys,
# retained exclusively by the historical-reader branch in `_intel_child`.
ROUTE_LIVE_ANALYSIS = "meeting.live_analysis"
ROUTE_BOOKMARK_LABEL = "meeting.bookmark_label"
ROUTE_AUTO_TITLE = "meeting.auto_title"

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


class _MeetingRoutedAdapter:
    """One selected Meeting leg, with closed output before election."""

    connector_id = "inference-provider"

    def __init__(
        self,
        capability: str,
        call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
        encode: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
    ) -> None:
        self._capability = capability
        self._call = call
        self._encode = encode

    def dispatch(self, engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Mapping[str, Any]:
        from ..inference_capabilities import (
            InferenceCapabilityRegistryError,
            process_inference_capability_registry,
        )
        from ..kernel.dispatch_context import dispatch_context_of
        from ..kernel.provider_signals import (
            InferenceInvalidTypedOutput,
            ProviderPermanentNoGeneration,
        )

        dispatch_context_of(engine)  # Runner proved the frozen deployment revision.
        if cancellation.is_set():
            from ..kernel.model import KernelRefused

            raise KernelRefused(SESSION_CLOSED)
        try:
            raw = self._call(engine, payload, cancellation)
            if getattr(raw, "error", None):
                raise ProviderPermanentNoGeneration()
            value = dict(self._encode(raw, payload))
            process_inference_capability_registry().require(self._capability).validate_result(value)
            return value
        except ProviderPermanentNoGeneration:
            raise
        except (AttributeError, KeyError, TypeError, ValueError, InferenceCapabilityRegistryError):
            raise InferenceInvalidTypedOutput() from None

    def cancel(self) -> str:
        return "not_supported"


class IntelAdmissionMixin(TranscribeAdmissionMixin):
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
        # Resolve `auto` exactly as Transcriber does: importability only, never
        # model construction, a load, or a network call at route admission.
        resolved_backend = self._transcription_backend
        if resolved_backend == "auto":
            try:
                from ..transcribe import _resolve_backend

                resolved_backend = _resolve_backend("auto")
            except Exception:
                resolved_backend = ""
        self._resolved_transcription_backend = resolved_backend
        model_name = self._transcription_model_name or "base"
        deferred_faster_whisper = (
            self.transcriber is None
            and self._transcriber_factory is not None
            and resolved_backend == "faster-whisper"
        )
        deferred_or_unloaded_mlx = (
            resolved_backend == "mlx"
            and (
                (self.transcriber is None and self._transcriber_factory is not None)
                or (self.transcriber is not None and not bool(getattr(self.transcriber, "loaded", False)))
            )
        )
        if deferred_or_unloaded_mlx:
            from ..transcribe import _model_repo_candidates

            candidates = [
                {"id": candidate, "revision": "mlx-candidate-v1"}
                for candidate in _model_repo_candidates(model_name)
            ]
            strategies = ["model-holder", "silent-audio"]
        elif deferred_faster_whisper:
            candidates = [{
                "id": f"builtin-whisper-faster-whisper-{model_name}",
                "revision": "legacy-model-config-v1",
            }]
            strategies = ["constructor"]
        else:
            candidates = []
            strategies = ["constructor"]
        preload_budget = 1 if (deferred_faster_whisper or deferred_or_unloaded_mlx) else 0
        preload_declaration = {
            "key": "preload",
            "source_key": "transcription",
            "candidate_material": candidates,
            "strategy_sequence": strategies,
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
            self._intel_live = False
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
        # HS-131-17: the live session no longer infers routed intelligence from
        # private MIR fields — it has none. The deferred job reads the current
        # `MeetingConfig.intent_router_enabled` under its own admitted parent and
        # owns that decision end to end.
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

    def _bundle_member(self, capability: str) -> Mapping[str, Any] | None:
        bundle = self._route_bundle
        if bundle is None:
            return None
        return next(
            (member for member in bundle.get("members", ()) if member["capability_id"] == capability),
            None,
        )

    def _routed_identity(self, capability: str, material: Mapping[str, Any]) -> str:
        """Stable logical operation identity; random UI supersession stays private."""
        if self._state is None:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        if capability == ROUTE_LIVE_ANALYSIS:
            suffix = ":".join((
                str(material["transcript_sha256"]),
                str(material["window"]["start"]),
                str(material["window"]["end"]),
                str(int(bool(material["final"]))),
            ))
        elif capability == ROUTE_BOOKMARK_LABEL:
            suffix = ":".join((
                str(material["bookmark_timestamp"]),
                str(material["context_sha256"]),
                str(material["summary_sha256"]),
            ))
        elif capability == ROUTE_AUTO_TITLE:
            suffix = str(material["transcript_sha256"])
        else:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        # Hash the complete stable tuple rather than truncating it: the durable
        # command stays below the route API's identifier limit without weakening
        # replay identity.
        return f"meeting:{self._state.id}:{capability}:{_sha((capability, suffix))}"

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
        """Execute live Meeting work only through its frozen bundle member.

        Operation material is private until the coordinator validates and elects a
        result.  The legacy branch remains solely for historical-plan readers;
        production sessions set ``_route_bundle`` at start and never call the
        legacy planner or child runner.
        """
        if getattr(self, "_intel_closed", False):
            raise MeetingIntelRefused(SESSION_CLOSED, capability)
        parent = self._intel_parent
        member = self._bundle_member(capability)
        if member is not None and parent is not None:
            from types import SimpleNamespace

            operation_id = self._routed_identity(capability, material)
            command_id = "meeting-route-operation:" + operation_id
            try:
                admitted = self._intel_broker().inference_adoption_service.admit_on_frozen_route(
                    self.intel_principal,
                    command_id=command_id,
                    route_plan_id=str(member["route_plan_id"]),
                    capability_id=capability,
                    operation_id=operation_id,
                    payload=dict(material),
                    reserved_output_tokens=512,
                )
                routed = self._intel_broker().inference_adoption_service.execute(
                    self.intel_principal,
                    execution_id=str(admitted["execution"]["id"]),
                    adapter=_MeetingRoutedAdapter(capability, call, encode),
                    parent_context=parent.context,
                )
            except MeetingIntelRefused:
                raise
            except Exception as exc:
                # A route admission failure is a named pre-dispatch refusal to the
                # Meeting seam; a controller result below remains its own receipt.
                reason = str(getattr(exc, "code", "") or SESSION_NOT_ADMITTED)
                raise MeetingIntelRefused(reason, capability) from exc
            outcome = SimpleNamespace(
                outcome=str(routed["outcome"]),
                error=str(routed.get("receipt", {}).get("terminal_disposition") or ""),
            )
            value = routed.get("result")
            return outcome, value if isinstance(value, Mapping) else None, value

        # Historical v1 plans remain readable.  No new production session reaches
        # this branch after the Phase-B bundle cutover (design note §45-51).
        plan = self._intel_plan
        if plan is None or parent is None:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        legacy_capability = {
            ROUTE_LIVE_ANALYSIS: CAPABILITY_LIVE_ANALYSIS,
            ROUTE_BOOKMARK_LABEL: CAPABILITY_BOOKMARK_LABEL,
            ROUTE_AUTO_TITLE: CAPABILITY_AUTO_TITLE,
        }.get(capability, capability)
        return run_admitted_capability(
            broker=self._intel_broker(),
            principal=self.intel_principal,
            plan=plan,
            parent=parent,
            capability=legacy_capability,
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
            if cancellation.is_set() or self._current_analysis_id != analysis_id:
                # A newer window superseded this one: no output may land.
                raise KernelRefused(WINDOW_SUPERSEDED)
            # Phase-B has no elected-stream abstraction.  Keep all model output
            # private until semantic validation and controller receipt election.
            return engine.analyze(payload["transcript_material"], stream=False)

        def encode(result: Any, _payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "summary": str(getattr(result, "summary", "") or ""),
                "topics": [str(topic) for topic in (getattr(result, "topics", None) or [])],
                "action_items": [
                    {
                        "task": str(getattr(item, "task", "") or ""),
                        "owner": (
                            str(getattr(item, "owner"))
                            if getattr(item, "owner", None) is not None else None
                        ),
                        "due": (
                            str(getattr(item, "due"))
                            if getattr(item, "due", None) is not None else None
                        ),
                    }
                    for item in (getattr(result, "action_items", None) or [])
                ],
            }

        return self._intel_child(
            capability=ROUTE_LIVE_ANALYSIS,
            contract=CONTRACT_LIVE_ANALYSIS,
            projection_kind=PROJECTION_LIVE_WINDOW,
            material={
                "transcript_sha256": _sha(transcript),
                "window": {"start": 0.0, "end": float(self.duration), "segments": len(self._state.segments) if self._state else 0},
                "template_revision": "1",
                "limits": {"max_tokens": None},
                "final": bool(final),
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

        def encode(result: Any, _payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"label": str(result or "")}

        return self._intel_child(
            capability=ROUTE_BOOKMARK_LABEL,
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

        def encode(result: Any, _payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"title": str(result or "")}

        return self._intel_child(
            capability=ROUTE_AUTO_TITLE,
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
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "WINDOW_SUPERSEDED",
    "session_child_budget",
]
