"""Admitted meeting transcription: one child per interval (HS-131-09).

Meeting transcription runs under the EXISTING ``meeting.session`` parent
HS-131-08 already admits — never a second parent and never a dictation session.
The plan's transcription capability names the LOCAL WHISPER deployment, so a
transcription child can never be mistaken for the leg the analysis prompt runs
on, and an interval with no live parent is dropped before Whisper.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Mapping

from .intel_plan import (
    CAPABILITY_NOT_PLANNED,
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
)

# Sol Amendment 6: a transcription-bearing session spends ONE child per
# transcription interval, so the advertised 12-hour session would
# deterministically exhaust a 4096 allocation (4320 intervals) before any intel
# child ran. Transcription therefore buys its own headroom explicitly.
TRANSCRIPTION_INTERVAL_SECONDS = 10.0
TRANSCRIPTION_BUDGET_HEADROOM = 2
#: The named refusal a dropped transcription interval reports.
TRANSCRIPTION_NOT_ADMITTED = "meeting_transcription_not_admitted"


def session_child_budget(
    *,
    transcription: bool,
    session_seconds: float,
    interval_seconds: float = TRANSCRIPTION_INTERVAL_SECONDS,
    intelligence_budget: int,
) -> int:
    """The frozen child allocation for one live meeting session.

    Sol Amendment 6, verbatim: a transcription-bearing plan adds
    ``ceil(session_max_duration / TRANSCRIBE_INTERVAL) + 2`` children to the 4096
    intelligence allocation — 8418 at 10 s over 12 h.
    """
    if not transcription:
        return int(intelligence_budget)
    intervals = math.ceil(max(0.0, float(session_seconds)) / max(0.001, float(interval_seconds)))
    return int(intelligence_budget) + int(intervals) + TRANSCRIPTION_BUDGET_HEADROOM


@dataclass
class RoutedMeetingTranscriptionAdmission:
    """One interval on the Meeting's already-frozen transcription route.

    Audio stays in the transcriber's closure.  The routed material contains only
    its canonical-byte digest and safe interval metadata; the controller owns
    every provider attempt and durable winner election.
    """

    session: Any
    source_id: str
    interval_start: float
    interval_end: float
    final_pass: bool

    # Design note §Orchestrator amendment (2026-08-22): P=1 trims the prior
    # per-candidate ceremony under the owner scope ruling.
    single_preload_sequence = True

    def _member(self, capability: str) -> Mapping[str, Any] | None:
        bundle = getattr(self.session, "_route_bundle", None) or {}
        return next(
            (item for item in bundle.get("members", ()) if item["capability_id"] == capability),
            None,
        )

    def _operation_id(self, capability: str, material: Mapping[str, Any]) -> str:
        state = self.session._state
        if state is None:
            raise RuntimeError(TRANSCRIPTION_NOT_ADMITTED)
        identity = {
            "meeting_id": state.id,
            "source_id": self.source_id,
            "interval_start": self.interval_start,
            "interval_end": self.interval_end,
            "final_pass": bool(self.final_pass),
            "capability": capability,
            **(
                {"audio_sha256": str(material["audio_sha256"])}
                if capability == "speech.transcribe"
                else {"lifecycle_material_sha256": hashlib.sha256(
                    json.dumps(dict(material), sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()}
            ),
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return f"meeting:{state.id}:{capability}:{digest}"

    def _execute(
        self,
        *,
        capability: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], Any], Any],
        reserved_output_tokens: int = 64,
    ) -> Mapping[str, Any]:
        member = self._member(capability)
        parent = getattr(self.session, "_intel_parent", None)
        if member is None or parent is None or getattr(self.session, "_intel_closed", False):
            raise RuntimeError(TRANSCRIPTION_NOT_ADMITTED)
        if self.source_id.startswith("device:"):
            device_id = self.source_id.removeprefix("device:")
            requested = set((getattr(self.session, "_route_bundle", None) or {}).get(
                "requested_remote_device_ids", ()
            ))
            if device_id not in requested:
                self.session._transcription_refusal = "meeting_transcription_source_not_frozen"
                raise RuntimeError(self.session._transcription_refusal)
        operation_id = self._operation_id(capability, material)
        coordinator = self.session._intel_broker().inference_adoption_service
        admitted = coordinator.admit_on_frozen_route(
            self.session.intel_principal,
            command_id="meeting-route-operation:" + operation_id,
            route_plan_id=str(member["route_plan_id"]),
            capability_id=capability,
            operation_id=operation_id,
            payload=dict(material),
            reserved_output_tokens=reserved_output_tokens,
        )
        from ..services.inference_semantic_adapters import adapter_for

        return coordinator.execute(
            self.session.intel_principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter_for(capability, call),
            parent_context=parent.context,
        )

    def transcribe_child(
        self,
        *,
        material: Mapping[str, Any],
        run: Callable[[], str],
        seed: Any,
        **_kwargs: Any,
    ) -> tuple[Any, Any]:
        """Run one canonical-audio interval under ``speech.transcribe``."""
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import ProviderIndeterminate
        from ..transcribe import TranscriberTimeoutError

        del seed  # identity is the ruled interval tuple, never caller material.

        def call(_engine: Any, _payload: Mapping[str, Any], cancellation: Any) -> str:
            if cancellation.is_set():
                raise KernelRefused(TRANSCRIPTION_NOT_ADMITTED)
            try:
                return run()
            except TranscriberTimeoutError as exc:
                # The native worker remains live after this timeout.  Its physical
                # outcome is unknowable, so the frozen policy must not advance.
                raise ProviderIndeterminate() from exc

        routed = self._execute(
            capability="speech.transcribe", material=material, call=call
        )
        result = routed.get("result")
        return SimpleNamespace(outcome=str(routed["outcome"])), (
            None if not isinstance(result, Mapping) else result.get("text")
        )

    def preload_sequence(
        self,
        *,
        material: Mapping[str, Any],
        run: Callable[[], Any],
    ) -> tuple[Any, Any]:
        """Receipt one frozen MLX candidate walk as the Meeting's P=1 child."""
        return self.preload_child(
            stage="mlx-warmup", material=material, run=run, attempt_ordinal=1
        )

    def preload_child(
        self,
        *,
        stage: str,
        material: Mapping[str, Any],
        run: Callable[[], Any],
        attempt_ordinal: int,
        **_kwargs: Any,
    ) -> tuple[Any, Any]:
        """Keep MLX warmup as a derived lifecycle child, never a fallback."""
        del attempt_ordinal

        def call(_engine: Any, _payload: Mapping[str, Any], _cancellation: Any) -> Mapping[str, str]:
            return {"state": str(run() or stage)}

        routed = self._execute(
            capability="speech.preload",
            material={"stage": str(stage), **dict(material)},
            call=call,
            reserved_output_tokens=16,
        )
        if str(routed["outcome"]) == "succeeded":
            member = self._member("speech.preload")
            bundle = getattr(self.session, "_route_bundle", None) or {}
            evidence = next(
                (
                    item for item in bundle.get("derived_preloads", ())
                    if member is not None
                    and item.get("preload_route_plan_id") == member.get("route_plan_id")
                ),
                None,
            )
            if evidence is not None:
                coordinator = self.session._intel_broker().inference_adoption_service
                coordinator.record_local_speech_readiness_after_load(
                    self.session.intel_principal,
                    deployment_revision_id=str(evidence["deployment_revision_id"]),
                )
        return SimpleNamespace(outcome=str(routed["outcome"])), routed.get("result")


class TranscribeAdmissionMixin:
    """The session-side handle each transcription interval dispatches under."""

    def _transcription_admission(
        self,
        *,
        source_id: str = "mic",
        interval_start: float = 0.0,
        interval_end: float = 0.0,
        final_pass: bool = False,
    ) -> Any:
        """Return the bundle route for fresh Meetings; retain v1 readers only."""
        parent = self._intel_parent
        if parent is None or getattr(self, "_intel_closed", False):
            self._transcription_refusal = (
                self._transcription_refusal or TRANSCRIPTION_NOT_ADMITTED
            )
            return None
        if getattr(self, "_route_bundle", None) is not None:
            return RoutedMeetingTranscriptionAdmission(
                self, source_id, float(interval_start), float(interval_end), bool(final_pass)
            )
        # Historical persisted sessions still reconstruct their v1 speech plan;
        # no new bundle-backed Meeting is permitted to enter this branch.
        plan = self._intel_plan
        if plan is None:
            self._transcription_refusal = TRANSCRIPTION_NOT_ADMITTED
            return None
        if not plan.has(CAPABILITY_WHISPER_TRANSCRIBE):
            self._transcription_refusal = CAPABILITY_NOT_PLANNED
            return None
        from ..speech_session.transcription import TranscriptionAdmission

        return TranscriptionAdmission(
            broker=self._intel_broker(),
            principal=self.intel_principal,
            plan=plan,
            parent=parent,
            capability=CAPABILITY_WHISPER_TRANSCRIBE,
            preload_capability=CAPABILITY_WHISPER_PRELOAD,
        )


__all__ = [
    "TRANSCRIPTION_BUDGET_HEADROOM",
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "RoutedMeetingTranscriptionAdmission",
    "TranscribeAdmissionMixin",
    "session_child_budget",
]
