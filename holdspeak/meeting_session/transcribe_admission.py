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
    last_preload_receipt: Mapping[str, Any] | None = None

    def _preload_evidence(self) -> Mapping[str, Any] | None:
        """The derived preload evidence for the speech.preload member."""
        bundle = getattr(self.session, "_route_bundle", None) or {}
        preload = self._member("speech.preload")
        if preload is None:
            return None
        return next(
            (
                item for item in bundle.get("derived_preloads", ())
                if item.get("preload_route_plan_id") == preload.get("route_plan_id")
            ),
            None,
        )

    def frozen_preload_material(self) -> Mapping[str, Any]:
        """The frozen MLX preload evidence the transcriber lifecycle must match."""
        evidence = self._preload_evidence()
        if evidence is None:
            return {}
        return {
            "engine": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "candidate_ids": [str(item["id"]) for item in evidence["candidate_material"]],
            "strategy_sequence": [str(item) for item in evidence["strategy_sequence"]],
            "stop_rules": [str(item) for item in evidence["stop_rules"]],
        }

    def loaded_artifact_reusable(self, impl: Any) -> bool:
        """Skip reload when the impl already carries matching provenance."""
        evidence = self._preload_evidence()
        if evidence is None:
            return False
        provenance = getattr(impl, "_holdspeak_preload_provenance", None)
        if not isinstance(provenance, Mapping):
            return False
        material = self.frozen_preload_material()
        deployment_revision_id = str(evidence["deployment_revision_id"])
        if (
            str(provenance.get("deployment_revision_id") or "") != deployment_revision_id
            or str(provenance.get("engine") or "") != material.get("engine", "")
            or str(provenance.get("model") or "") != material.get("model", "")
            or str(provenance.get("language") or "auto") != str(material.get("language") or "auto")
        ):
            return False
        # The exact durable-receipt cross-check from the speech session:
        # an execution_id and route_plan_id must both be present.
        execution_id = str(provenance.get("execution_id") or "")
        route_plan_id = str(provenance.get("route_plan_id") or "")
        if not execution_id or not route_plan_id:
            return False
        broker = self.session._intel_broker()
        with broker.database._connection() as conn:
            row = conn.execute(
                """SELECT e.terminal_outcome, e.winning_attempt_id,
                          p.capability_id, r.deployment_revision_id
                     FROM inference_route_executions e
                     JOIN inference_operation_route_request_plans o
                       ON o.id = e.operation_plan_id
                     JOIN inference_route_plans p ON p.id = o.route_plan_id
                     JOIN inference_route_plan_entries r
                       ON r.plan_id = p.id
                    WHERE e.id = ? AND p.id = ?
                      AND r.route_leg_ordinal = 1""",
                (execution_id, route_plan_id),
            ).fetchone()
        return bool(
            row is not None
            and str(row["terminal_outcome"] or "") == "succeeded"
            and str(row["winning_attempt_id"] or "")
            and str(row["capability_id"] or "") == "speech.preload"
            and str(row["deployment_revision_id"] or "") == deployment_revision_id
        )

    def record_loaded_artifact(self, impl: Any, receipt: Mapping[str, Any]) -> None:
        """Stamp provenance on the impl after a successful preload."""
        if str(receipt.get("outcome") or "") != "succeeded":
            return
        evidence = self._preload_evidence()
        preload = self._member("speech.preload")
        if evidence is None or preload is None:
            return
        impl._holdspeak_preload_provenance = {
            "deployment_revision_id": str(evidence["deployment_revision_id"]),
            "engine": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "execution_id": str(receipt.get("execution_id") or ""),
            "route_plan_id": str(preload["route_plan_id"]),
        }

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
            from ..services.inference_parent_route_bundle_service import remote_device_evidence

            device_id = self.source_id.removeprefix("device:")
            requested = set((getattr(self.session, "_route_bundle", None) or {}).get(
                "requested_remote_device_ids", ()
            ))
            if remote_device_evidence(device_id) not in requested:
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
            parent_operation_id=getattr(parent, "operation_id", None),
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

        def call(_engine: Any, _payload: Mapping[str, Any], cancellation: Any) -> Mapping[str, str]:
            # Existing lifecycle callbacks remain zero-argument; the MLX sequence
            # opts into the cancellation argument and checks it between calls.
            import inspect

            parameters = inspect.signature(run).parameters
            value = run(cancellation) if parameters else run()
            return {"state": str(value or stage)}

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
        self.last_preload_receipt = routed.get("receipt")
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
        """Return the sole bundle-backed transcription execution authority."""
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
        # A persisted v1 plan remains historical display data only. It cannot
        # reconstruct a speech admission after the Meeting cutover.
        self._transcription_refusal = TRANSCRIPTION_NOT_ADMITTED
        return None


__all__ = [
    "TRANSCRIPTION_BUDGET_HEADROOM",
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "RoutedMeetingTranscriptionAdmission",
    "TranscribeAdmissionMixin",
    "session_child_budget",
]
