"""Admitted meeting transcription: one door job per interval (HS-131-09).

Meeting transcription runs under the ``meeting.session`` parent the Meeting
admits, never a second parent and never a dictation session. The engine door
names the speech engine from the owner's assignment when the Meeting starts;
an interval with no live parent is dropped before Whisper.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
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

from ..logging_config import get_logger

log = get_logger("meeting_session")


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


#: The speech jobs: transcription, and the model load that serves it.
SPEECH_JOB = "speech.transcribe"
PRELOAD_JOB = "speech.preload"
TRANSCRIPTION_DEADLINE_SECONDS = 600.0

_STOP_RULES = ["success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion"]


def speech_evidence(db: Any, engine: Any) -> dict[str, Any] | None:
    """What the transcriber is built from, read from the speech engine's
    deployment revision and its profile: engine, model, language, and (MLX)
    the candidate repositories and load strategies its one preload walks.
    ``None`` when the revision or profile is not read."""
    with db._connection() as conn:
        deployment = conn.execute(
            "SELECT engine,model,artifact_id FROM deployment_revisions WHERE id=?",
            (str(engine.revision),),
        ).fetchone()
        profile = conn.execute(
            """SELECT capability_manifest_json FROM model_profile_revisions
                WHERE profile_id=? ORDER BY revision DESC LIMIT 1""",
            (str(engine.profile),),
        ).fetchone()
    if deployment is None:
        return None
    backend = str(deployment["engine"])
    identity = str(deployment["model"] or "")
    prefix = f"builtin-whisper-{backend}-"
    whisper = backend in {"mlx", "faster-whisper"} and identity.startswith(prefix)
    model = identity.removeprefix(prefix) if whisper else identity
    language = "auto"
    if whisper:
        try:
            claims = json.loads(str(profile["capability_manifest_json"]))["claims"]
            language = next(
                str(item).removeprefix("speech_language:")
                for item in claims if str(item).startswith("speech_language:")
            )
        except (KeyError, TypeError, ValueError, StopIteration):
            return None
    if backend == "mlx" and whisper:
        from ..transcribe import _model_repo_candidates

        candidates = [{"id": item, "revision": "mlx-candidate-v1"} for item in _model_repo_candidates(model)]
        strategies = ["model-holder", "silent-audio"]
    elif backend == "faster-whisper" and whisper:
        candidates = [{"id": identity, "revision": "legacy-model-config-v1"}]
        strategies = ["constructor"]
    else:
        candidates, strategies = [], ["constructor"]
    return {
        "deployment_revision_id": str(engine.revision),
        "engine": backend,
        "model": model,
        "language": language,
        "model_artifact": str(deployment["artifact_id"] or identity),
        "candidate_material": candidates,
        "strategy_sequence": strategies,
        "stop_rules": list(_STOP_RULES),
    }


@dataclass
class RoutedMeetingTranscriptionAdmission:
    """One interval on the Meeting's speech engine, through the engine door.

    Audio stays in the transcriber's closure. The door's material holds only
    its canonical-byte digest and safe interval metadata.
    """

    session: Any
    source_id: str
    interval_start: float
    interval_end: float
    final_pass: bool

    # One P=1 preload child walks the MLX candidates (the owner scope ruling).
    single_preload_sequence = True
    last_preload_receipt: Mapping[str, Any] | None = None

    def _preload_evidence(self) -> Mapping[str, Any] | None:
        """What the speech engine's transcriber is built from."""
        return getattr(self.session, "_speech_evidence", None)

    def frozen_preload_material(self) -> Mapping[str, Any]:
        """The MLX preload material the transcriber lifecycle must match."""
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
        """A loaded transcriber serves this Meeting only when its provenance
        names the same engine and the door receipt of its preload succeeded."""
        evidence = self._preload_evidence()
        provenance = getattr(impl, "_holdspeak_preload_provenance", None)
        if evidence is None or not isinstance(provenance, Mapping):
            return False
        material = self.frozen_preload_material()
        revision = str(evidence["deployment_revision_id"])
        if (
            str(provenance.get("deployment_revision_id") or "") != revision
            or str(provenance.get("engine") or "") != material.get("engine", "")
            or str(provenance.get("model") or "") != material.get("model", "")
            or str(provenance.get("language") or "auto") != str(material.get("language") or "auto")
        ):
            return False
        operation_id = str(provenance.get("operation_id") or "")
        if not operation_id:
            return False
        broker = self.session._intel_broker()
        with broker.database._connection() as conn:
            row = conn.execute(
                """SELECT o.target_ref, r.state FROM kernel_operations o
                     JOIN kernel_receipts r ON r.operation_id=o.operation_id
                    WHERE o.operation_id=?""",
                (operation_id,),
            ).fetchone()
        return bool(
            row is not None
            and str(row["state"] or "") == "succeeded"
            and str(row["target_ref"] or "").removeprefix("deployment-revision:") == revision
        )

    def record_loaded_artifact(self, impl: Any, receipt: Mapping[str, Any]) -> None:
        """Stamp provenance on the impl after a successful preload."""
        if str(receipt.get("outcome") or "") != "succeeded":
            return
        evidence = self._preload_evidence()
        if evidence is None:
            return
        impl._holdspeak_preload_provenance = {
            "deployment_revision_id": str(evidence["deployment_revision_id"]),
            "engine": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "operation_id": str(receipt.get("operation_id") or ""),
        }

    def _run_id(self, capability: str, material: Mapping[str, Any]) -> str:
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
            "material": hashlib.sha256(
                json.dumps(dict(material), sort_keys=True, separators=(",", ":"), default=str).encode()
            ).hexdigest(),
            "nonce": uuid.uuid4().hex,
        }
        digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        prefix = "meetingpreload" if capability == PRELOAD_JOB else "meetingspeech"
        return f"{prefix}_{digest[:40]}"

    def _execute(
        self,
        *,
        capability: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], Any], Any],
        reserved_output_tokens: int = 64,
    ) -> Mapping[str, Any]:
        del reserved_output_tokens
        engine = (getattr(self.session, "_live_engines", None) or {}).get(SPEECH_JOB)
        parent = getattr(self.session, "_intel_parent", None)
        if engine is None or parent is None or getattr(self.session, "_intel_closed", False):
            raise RuntimeError(TRANSCRIPTION_NOT_ADMITTED)
        if self.source_id.startswith("device:"):
            device_id = self.source_id.removeprefix("device:")
            if device_id not in set(getattr(self.session, "_requested_remote_device_ids", ()) or ()):
                self.session._transcription_refusal = "meeting_transcription_source_not_frozen"
                raise RuntimeError(self.session._transcription_refusal)
        from ..kernel.runtime import _as_principal
        from ..services import engine_door
        from ..services.inference_semantic_adapters import adapter_for

        broker = self.session._intel_broker()
        run_id = self._run_id(capability, material)
        running = self.session.__dict__.setdefault("_intel_door_runs", set())
        running.add(run_id)
        try:
            with _as_principal(self.session.intel_principal):
                answer = engine_door.run(
                    broker, self.session.intel_principal, capability, dict(material),
                    engine=engine, adapter=adapter_for(capability, call), invocation_id=run_id,
                    parent_context=parent.context, deadline=TRANSCRIPTION_DEADLINE_SECONDS,
                )
        except engine_door.EngineDoorError as exc:
            outcome = exc.outcome or "failed"
            return {"outcome": outcome, "result": None,
                    "receipt": {"outcome": outcome, "operation_id": exc.operation_id}}
        finally:
            running.discard(run_id)
        return {"outcome": "succeeded", "result": answer.result,
                "receipt": {"outcome": "succeeded", "operation_id": answer.operation_id}}

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

        routed = self._execute(capability=SPEECH_JOB, material=material, call=call)
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
            capability=PRELOAD_JOB,
            material={"stage": str(stage), **dict(material)},
            call=call,
            reserved_output_tokens=16,
        )
        evidence = self._preload_evidence()
        if str(routed["outcome"]) == "succeeded" and evidence is not None:
            try:
                from ..services.engine_door import record_ready

                record_ready(
                    self.session._intel_broker().database,
                    str(evidence["deployment_revision_id"]),
                    "loaded_under_speech_preload",
                )
            except Exception as exc:  # readiness is a record, never a gate
                log.warning("speech readiness record failed: %s", type(exc).__name__)
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
        """The handle one transcription interval runs under, or ``None``."""
        parent = self._intel_parent
        if parent is None or getattr(self, "_intel_closed", False):
            self._transcription_refusal = (
                self._transcription_refusal or TRANSCRIPTION_NOT_ADMITTED
            )
            return None
        if SPEECH_JOB in (getattr(self, "_live_engines", None) or {}):
            return RoutedMeetingTranscriptionAdmission(
                self, source_id, float(interval_start), float(interval_end), bool(final_pass)
            )
        self._transcription_refusal = TRANSCRIPTION_NOT_ADMITTED
        return None


__all__ = [
    "PRELOAD_JOB",
    "SPEECH_JOB",
    "speech_evidence",
    "TRANSCRIPTION_BUDGET_HEADROOM",
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "RoutedMeetingTranscriptionAdmission",
    "TranscribeAdmissionMixin",
    "session_child_budget",
]
