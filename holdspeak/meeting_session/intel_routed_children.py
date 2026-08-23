"""Frozen route execution children for a live meeting session."""

from __future__ import annotations

import threading
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .intel_child import MeetingProviderFailure, run_admitted_capability, sha as _sha
from .intel_plan import (
    CAPABILITY_AUTO_TITLE,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_LIVE_ANALYSIS,
    MeetingIntelRefused,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
)

log = get_logger("meeting_session")

CONTRACT_LIVE_ANALYSIS = "holdspeak.meeting-live-analysis"
CONTRACT_BOOKMARK_LABEL = "holdspeak.meeting-bookmark-label"
CONTRACT_AUTO_TITLE = "holdspeak.meeting-auto-title"

PROJECTION_LIVE_WINDOW = "meeting-live-window"
PROJECTION_BOOKMARK_LABEL = "meeting-bookmark-label"
PROJECTION_AUTO_TITLE = "meeting-auto-title"

ROUTE_LIVE_ANALYSIS = "meeting.live_analysis"
ROUTE_BOOKMARK_LABEL = "meeting.bookmark_label"
ROUTE_AUTO_TITLE = "meeting.auto_title"

WINDOW_DEADLINE_SECONDS = 300.0
LABEL_DEADLINE_SECONDS = 120.0
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
        from ..kernel.model import KernelRefused
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
        except (KernelRefused, ProviderPermanentNoGeneration):
            raise
        except (AttributeError, KeyError, TypeError, ValueError, InferenceCapabilityRegistryError):
            raise InferenceInvalidTypedOutput() from None

    def cancel(self) -> str:
        return "not_supported"




class IntelRoutedChildMixin:
    """Live provider work through frozen route-bundle members only."""

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

