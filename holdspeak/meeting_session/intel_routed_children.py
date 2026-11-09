"""The live Meeting's text jobs, each one call through the engine door."""

from __future__ import annotations

import hashlib
import threading
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()

from .intel_plan import (
    DISPLACED_AUTO_TITLE,
    DISPLACED_BOOKMARK_LABELS,
    DISPLACED_FINAL_ANALYSIS,
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


#: The live text jobs a Meeting with intelligence runs through the door.
LIVE_JOBS = (ROUTE_LIVE_ANALYSIS, ROUTE_BOOKMARK_LABEL, ROUTE_AUTO_TITLE)


def displaced_work_for_stop(state: Any, intelligence_enabled: bool) -> tuple[str, ...]:
    """Return text work to hand off only when intelligence was requested."""
    if not intelligence_enabled:
        return ()
    displaced: list[str] = []
    if state.segments:
        displaced.append(DISPLACED_FINAL_ANALYSIS)
    if state.bookmarks:
        displaced.append(DISPLACED_BOOKMARK_LABELS)
    if not state.title:
        displaced.append(DISPLACED_AUTO_TITLE)
    return tuple(displaced)

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
    """Live provider work through the engine door only."""

    def _live_job(self, capability: str) -> bool:
        """Whether the door named an engine for ``capability`` when the
        Meeting started (``_admit_intel_session``)."""
        return capability in (getattr(self, "_live_engines", None) or {})

    def _stop_door_runs(self) -> None:
        """Stop: the owner's cancel reaches every live job still running (and
        its retry on the next engine)."""
        from ..kernel.runtime import _as_principal
        from ..services import engine_door

        for run_id in list(self.__dict__.get("_intel_door_runs", ())):
            for each in (run_id, run_id + "_n2"):
                try:
                    with _as_principal(self.intel_principal):
                        engine_door.stop(self._intel_broker(), each)
                except Exception:  # a job that already ended has nothing to stop
                    continue

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
        """Run one live Meeting job through the engine door, a child of the
        live parent. The door reads the job's engine at this call."""
        if getattr(self, "_intel_closed", False):
            raise MeetingIntelRefused(SESSION_CLOSED, capability)
        parent = self._intel_parent
        if self._live_job(capability) and parent is not None:
            from types import SimpleNamespace

            from ..services import engine_door

            # One job through the engine door, a child of the live Meeting:
            # the engine the assignment names, one retry on the next engine.
            # The run id is held while it runs, so Stop reaches it (``_stop_door_runs``).
            run_id = engine_door.door_id(capability, None)
            running = self.__dict__.setdefault("_intel_door_runs", set())
            running.add(run_id)
            try:
                answer = engine_door.run(
                    self._intel_broker(), self.intel_principal, capability, dict(material),
                    adapter=_MeetingRoutedAdapter(capability, call, encode), invocation_id=run_id,
                    parent_context=parent.context, deadline=float(deadline_seconds),
                )
            except engine_door.EngineDoorError as exc:
                if exc.code == "no_engine":
                    raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability) from exc
                return SimpleNamespace(outcome=exc.outcome or "failed", error=exc.error), None, None
            finally:
                running.discard(run_id)
            value = answer.result
            return SimpleNamespace(outcome="succeeded", error=""), value if isinstance(value, Mapping) else None, value

        raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)

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
