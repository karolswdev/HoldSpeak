"""Admitted speech capture sessions: one finite parent per authority lifetime (HS-131-09).

A desktop hold, a configured wake capture, and a one-shot browser speak-to-fill
each open ONE finite ``dictation.session`` / ``wake.session`` parent over ONE
frozen plan, and close it when the bounded tail drains. Continuation is always a
new authenticated session, never an epoch reset.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .plan import (
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
    PARENT_DICTATION_SESSION,
    PARENT_WAKE_SESSION,
    PLAN_DICTATION,
    PLAN_LOCAL_MODEL_PRELOAD,
    PLAN_WAKE,
    PRELOAD_AUTHORITY_MISMATCHED,
    PRELOAD_AUTHORITY_REQUIRED,
    PRINCIPAL_REQUIRED,
    SESSION_NOT_ADMITTED,
    DictationSessionPlanResolver,
    SpeechSessionPlan,
    SpeechSessionRefused,
    sha,
)

log = get_logger("speech_session")

# ---------------------------------------------------------------- the fences

# A hold is admitted with its honest worst case — the capture ceiling PLUS the
# preauthorized drain — and SEALED on release (Sol Amendment 2). "release + 90s"
# is not a deadline anything can know at press.
HOLD_CAPTURE_CEILING_SECONDS = 30 * 60.0
HOLD_DRAIN_SECONDS = 90.0
# One transcription plus the bounded classifier retry and configured stages fit
# comfortably; an abandoned tail does not.
HOLD_CHILD_BUDGET = 12
# A one-shot speak-to-fill click is its own short session: no capture window to
# wait on, just the bounded transcribe-and-return tail.
ONE_SHOT_DEADLINE_SECONDS = 90.0
# Wake: capture completion + 30s, budget 12 (Sol Amendment 5 — a first-session
# path can legitimately consume nine children).
WAKE_DEADLINE_SECONDS = 30.0
WAKE_CHILD_BUDGET = 12

WAKE_SERVICE_IDENTITY = "wake-capture"
DEVICE_SERVICE_IDENTITY = "device-capture"
PRELOAD_SERVICE_IDENTITY = "local-model-preload"
#: An enabled, revisioned wake configuration IS the authority; a disabled one
#: has none, and the capture refuses instead of inferring authority from the
#: local process identity.
WAKE_AUTHORITY_REQUIRED = "configured_wake_authority_required"


# --------------------------------------------------------------- principals


def hold_gesture_principal() -> Principal:
    """The authenticated local-owner identity a physical hold gesture runs under.

    This is the SAME identity the delivery side already admits a hold-release
    typing effect under (``holdspeak.desktop_typing._OWNER``): a physical press
    on this machine's hold key is the owner acting, under the Phase-107 ruling.
    Nothing here is synthesized for a REMOTE caller — browser and device paths
    carry their own authenticated route principal.
    """
    return Principal(PrincipalKind.OWNER, "owner-session")


def wake_config_revision(wake_config: Any) -> str:
    """Derive the wake authority revision from the canonical persisted config.

    Sol Amendment 4: deterministic from what the owner ALREADY configured
    (enabled + action + armed window + model + threshold). No user-authored
    ``authority_basis`` field exists, so a valid enabled wake configuration is
    never wrongly refused for a redundant knob — and any change to what the
    configuration authorizes changes this revision.
    """
    return sha(
        {
            "enabled": bool(getattr(wake_config, "enabled", False)),
            "model": str(getattr(wake_config, "model", "") or ""),
            "threshold": float(getattr(wake_config, "threshold", 0.0) or 0.0),
            "armed_window_seconds": float(
                getattr(wake_config, "armed_window_seconds", 0.0) or 0.0
            ),
            "action": str(getattr(wake_config, "action", "") or ""),
        }
    )


def wake_service_principal(wake_config: Any) -> Principal:
    """The narrow wake identity: this session and its planned children, nothing else."""
    if not bool(getattr(wake_config, "enabled", False)):
        raise SpeechSessionRefused(WAKE_AUTHORITY_REQUIRED)
    return Principal(
        PrincipalKind.SERVICE,
        WAKE_SERVICE_IDENTITY,
        frozenset({(PARENT_WAKE_SESSION, 1), ("inference.invoke", 1), ("inference.cancel", 1)}),
        f"configured-wake:{wake_config_revision(wake_config)}",
    )


def device_service_principal(device_id: str) -> Principal:
    """The narrow identity a PAIRED-DEVICE hold capture runs under.

    A remote device press is not the local owner acting, so an OWNER principal is
    never synthesized for it (the same rule meeting start already follows). Its
    authority is the owner's pairing decision, carried as
    ``paired-device:<device id>`` — the wake-capture shape, applied to the
    configured pairing.

    NOTE (HS-131-09 Part A): the design's eight amendments do not name the device
    capture surface; it shares ``_kick_off_transcribe`` with the desktop hold, so
    it needs a parent or its transcription refuses. This narrow identity is the
    smallest honest choice and is flagged for ratification.
    """
    identity = str(device_id or "").strip()
    if not identity:
        raise SpeechSessionRefused(PRINCIPAL_REQUIRED)
    return Principal(
        PrincipalKind.SERVICE,
        DEVICE_SERVICE_IDENTITY,
        frozenset(
            {(PARENT_DICTATION_SESSION, 1), ("inference.invoke", 1), ("inference.cancel", 1)}
        ),
        f"paired-device:{identity}",
    )


def admit_device_session(
    *, device_id: str, config_snapshot: Any = None, registry_snapshot: Any = None,
    now: Optional[float] = None,
) -> SpeechSession:
    """One paired-device hold capture = one short ``dictation.session``."""
    return admit_speech_session(
        kind=PARENT_DICTATION_SESSION,
        principal=device_service_principal(device_id),
        insertion_aim="device-hold",
        config_snapshot=config_snapshot,
        registry_snapshot=registry_snapshot,
        deadline_seconds=ONE_SHOT_DEADLINE_SECONDS,
        child_budget=HOLD_CHILD_BUDGET,
        now=now,
    )


def model_config_revision(model_config: Any) -> str:
    """The canonical revision hash of ONE local speech-model configuration.

    This is the value ``model.local_model_preload_authority`` must name to
    authorize a pre-session warm. It is derived from exactly the terms that decide
    WHICH model loads (name, backend, language, transcription ceiling), so
    changing any of them invalidates the authority the owner granted — the knob
    can no longer be a blanket "yes, warm anything forever".
    """
    from .plan import _model_terms

    return sha({"model_config": _model_terms(model_config)})


def preload_service_principal(model_config: Any) -> Principal:
    """The narrow pre-session preload identity, or a refusal (Sol Amendment 4).

    A pre-session warm has no session to parent it, so it may run ONLY under the
    owner's explicit ``model.local_model_preload_authority`` — and that knob must
    NAME this model configuration's revision (:func:`model_config_revision`).
    Blank/absent and MISMATCHED both refuse here, before any MLX dispatch, and
    the refusal carries the revision the owner has to set.
    """
    value = str(getattr(model_config, "local_model_preload_authority", "") or "").strip()
    expected = model_config_revision(model_config)
    if not value:
        raise SpeechSessionRefused(PRELOAD_AUTHORITY_REQUIRED, detail=expected)
    if value != expected:
        raise SpeechSessionRefused(PRELOAD_AUTHORITY_MISMATCHED, detail=expected)
    return Principal(
        PrincipalKind.SERVICE,
        PRELOAD_SERVICE_IDENTITY,
        frozenset({("inference.invoke", 1)}),
        f"configured-local-model-preload:{value}",
    )


# ------------------------------------------------- the acquisition generation


class SessionGeneration:
    """A monotonic acquisition token (Sol Amendment 1).

    Acquisition (open the mic, admit the parent) is not instantaneous, so a
    release/stop or an admission failure can win the race. The winner retires
    the generation; the loser sees its token is stale, cancels whatever it
    admitted, tears the capture down, and discards the audio.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._value = 0

    def begin(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def retire(self) -> int:
        """Invalidate any in-flight acquisition; returns the new generation."""
        with self._lock:
            self._value += 1
            return self._value

    def is_live(self, token: int) -> bool:
        with self._lock:
            return int(token) == self._value


# ------------------------------------------------------------- the session


@dataclass
class SpeechSession:
    """One live admitted capture parent, its frozen plan, and its principal."""

    broker: Any
    principal: Any
    plan: SpeechSessionPlan
    parent: Any
    kind: str
    #: The ONE immutable cancellation carrier every continuation closure captures
    #: (Sol OQ5). Built at admission; never replaced, never read from ambient
    #: state.
    _fence: Any = None

    @property
    def operation_id(self) -> str:
        return str(self.parent.operation_id)

    @property
    def context(self) -> Any:
        return self.parent.context

    @property
    def fence(self) -> Any:
        """This session's immutable liveness/cancellation check."""
        from .fence import SessionFence

        if self._fence is None:
            self._fence = SessionFence(
                broker=self.broker,
                operation_id=str(self.parent.operation_id),
                deadline_at=float(self.plan.deadline_at),
            )
        return self._fence

    def provider(self) -> Any:
        """The admission handle the dictation pipeline dispatches providers under."""
        from .provider import ProviderAdmission

        return ProviderAdmission(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            fence=self.fence,
        )

    def seal(self, deadline_at: float) -> float:
        """Seal the admitted ceiling down to the now-known real end (Amendment 2).

        The DURABLE bound and the in-memory carrier are sealed together: a fence
        left on the original ceiling would keep a late provider return publishable
        for the whole admitted window.
        """
        sealed = float(
            self.broker.parent_run_controller.seal_deadline(
                self.parent.context, self.principal, float(deadline_at)
            )
        )
        self.fence.seal(sealed)
        return sealed

    def cancel(self) -> str:
        # The local fence flips FIRST: a continuation thread must never see a
        # window where cancellation was decided but the carrier still reads live.
        self.fence.cancel()
        return str(
            self.broker.parent_run_controller.cancel(self.parent.context, self.principal)
        )

    def close(self, outcome: str = "succeeded") -> str:
        """Close the parent with its honest terminal outcome, exactly once."""
        try:
            if self.broker.store.receipt(self.parent.operation_id) is not None:
                return str(self.broker.store.receipt(self.parent.operation_id)["outcome"])
            receipt = self.broker.parent_run_controller.close(
                self.parent.context, outcome, principal=self.principal
            )
            return str(receipt.get("outcome") or outcome)
        except Exception as exc:
            log.error("speech session close failed: %s", type(exc).__name__)
            return ""

    def cancel_and_close(self) -> str:
        """Fence new work, then elect the terminal ``cancelled`` receipt.

        Cancellation advances the execution epoch, so this session's own context
        is stale by construction and the controller re-derives a recovery context
        from the durable owner.
        """
        try:
            self.cancel()
        except Exception as exc:
            log.error("speech session cancel failed: %s", type(exc).__name__)
            return ""
        try:
            receipt = self.broker.store.receipt(self.parent.operation_id)
            if receipt is not None:
                return str(receipt["outcome"])
            return str(
                self.broker.parent_run_controller.cancel_by_operation_id(
                    self.principal, self.parent.operation_id
                )
            )
        except Exception as exc:
            log.error("speech session cancel close failed: %s", type(exc).__name__)
            return ""

    def transcription(
        self,
        capability: str = CAPABILITY_WHISPER_TRANSCRIBE,
        *,
        on_claim: Any = None,
        utterance_ref: str = "",
    ) -> Any:
        """The admission handle ``Transcriber`` dispatches one child under.

        ``on_claim`` runs inside the FIRST transcription child claim of this
        utterance (Sol Amendment 8 — the browser inactivity lease refresh).
        """
        from .transcription import TranscriptionAdmission

        return TranscriptionAdmission(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            capability=capability,
            on_claim=on_claim,
            utterance_ref=str(utterance_ref),
        )


# ---------------------------------------------------------------- admission


def _broker() -> Any:
    from ..kernel.runtime import _service

    return _service()


def admit_speech_session(
    *,
    kind: str,
    principal: Any,
    insertion_aim: str,
    config_snapshot: Any = None,
    registry_snapshot: Any = None,
    deadline_seconds: float,
    child_budget: int,
    capabilities: Sequence[str] = (),
    insertion_context: str = "",
    session_id: str = "",
    plan_kind: str = "",
    now: Optional[float] = None,
) -> SpeechSession:
    """Admit ONE finite capture parent over ONE frozen plan, or refuse by name.

    Resolution happens exactly once, here (Sol OQ4). Nothing downstream reads
    mutable configuration or resolves a placement again.
    """
    if principal is None or str(getattr(principal, "name", "none")) == "none":
        raise SpeechSessionRefused(PRINCIPAL_REQUIRED)
    if config_snapshot is None:
        from ..config import Config

        config_snapshot = Config.load()
    if registry_snapshot is None:
        from ..db import get_database

        registry_snapshot = get_database()

    identifier = session_id or uuid.uuid4().hex[:12]
    started = time.time() if now is None else float(now)
    deadline = started + float(deadline_seconds)
    plan = DictationSessionPlanResolver().resolve(
        config_snapshot,
        registry_snapshot,
        principal,
        insertion_aim,
        session_id=identifier,
        deadline_at=deadline,
        child_budget=int(child_budget),
        plan_kind=plan_kind or (PLAN_WAKE if kind == PARENT_WAKE_SESSION else PLAN_DICTATION),
        capabilities=capabilities,
        insertion_context=insertion_context,
        created_at=started,
    )
    broker = _broker()
    try:
        parent = broker.parent_run_controller.start(
            principal,
            kind=kind,
            definition_ref=f"speech:{identifier}:{insertion_aim or 'capture'}",
            definition_revision=plan.sha256,
            input_snapshot=plan.summary(),
            deadline_at=deadline,
            child_budget=int(child_budget),
        )
    except Exception as exc:
        reason = str(getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
        raise SpeechSessionRefused(reason) from None
    log.info(
        "speech session admitted: kind=%s parent=%s plan=%s", kind, parent.operation_id, plan.sha256
    )
    return SpeechSession(broker, principal, plan, parent, kind)


def admit_hold_session(
    *, principal: Any = None, config_snapshot: Any = None, registry_snapshot: Any = None,
    insertion_aim: str = "hold-release", now: Optional[float] = None,
) -> SpeechSession:
    """One desktop hold = one ``dictation.session`` with the ceiling + drain."""
    return admit_speech_session(
        kind=PARENT_DICTATION_SESSION,
        principal=principal or hold_gesture_principal(),
        insertion_aim=insertion_aim,
        config_snapshot=config_snapshot,
        registry_snapshot=registry_snapshot,
        deadline_seconds=HOLD_CAPTURE_CEILING_SECONDS + HOLD_DRAIN_SECONDS,
        child_budget=HOLD_CHILD_BUDGET,
        now=now,
    )


def seal_hold_release(session: SpeechSession, *, released_at: Optional[float] = None) -> float:
    """SEAL a hold on release to ``min(start+30m+90s, release+90s)``."""
    release = time.time() if released_at is None else float(released_at)
    return session.seal(release + HOLD_DRAIN_SECONDS)


def admit_one_shot_session(
    *, principal: Any = None, insertion_aim: str = "speak-to-fill",
    config_snapshot: Any = None, registry_snapshot: Any = None, now: Optional[float] = None,
) -> SpeechSession:
    """One one-shot browser transcription click = one short ``dictation.session``.

    Sol OQ3: inside an active open-mic interval a speak-to-fill joins that
    parent; a one-shot click outside one admits this short session and closes
    after its bounded tail. It never borrows a stale global mic context.
    """
    return admit_speech_session(
        kind=PARENT_DICTATION_SESSION,
        principal=principal or hold_gesture_principal(),
        insertion_aim=insertion_aim,
        config_snapshot=config_snapshot,
        registry_snapshot=registry_snapshot,
        deadline_seconds=ONE_SHOT_DEADLINE_SECONDS,
        child_budget=HOLD_CHILD_BUDGET,
        now=now,
    )


def admit_wake_session(
    *, wake_config: Any, config_snapshot: Any = None, registry_snapshot: Any = None,
    now: Optional[float] = None,
) -> SpeechSession:
    """One configured wake capture = one bounded ``wake.session``.

    The narrow ``wake-capture`` SERVICE identity carries
    ``configured-wake:<derived revision>``; an OWNER principal is never
    fabricated for an autonomous capture.
    """
    return admit_speech_session(
        kind=PARENT_WAKE_SESSION,
        principal=wake_service_principal(wake_config),
        insertion_aim=f"wake-{str(getattr(wake_config, 'action', '') or 'preview')}",
        config_snapshot=config_snapshot,
        registry_snapshot=registry_snapshot,
        deadline_seconds=WAKE_DEADLINE_SECONDS,
        child_budget=WAKE_CHILD_BUDGET,
        plan_kind=PLAN_WAKE,
        now=now,
    )


def preload_service_admission(
    *, model_config: Any = None, config_snapshot: Any = None, registry_snapshot: Any = None,
) -> Any:
    """The authorized PRE-session warm admission, or a named refusal.

    Returns a parentless :class:`~holdspeak.speech_session.transcription.TranscriptionAdmission`:
    the warm has no session to parent it, so each preload dispatch is one
    top-level ``inference.invoke@1`` under the narrow ``local-model-preload``
    service identity.
    """
    from .transcription import TranscriptionAdmission

    if config_snapshot is None:
        from ..config import Config

        config_snapshot = Config.load()
    if registry_snapshot is None:
        from ..db import get_database

        registry_snapshot = get_database()
    principal = preload_service_principal(
        model_config if model_config is not None else getattr(config_snapshot, "model", None)
    )
    plan = DictationSessionPlanResolver().resolve(
        config_snapshot,
        registry_snapshot,
        principal,
        "local-model-preload",
        session_id="preload_" + uuid.uuid4().hex[:8],
        deadline_at=time.time() + ONE_SHOT_DEADLINE_SECONDS,
        child_budget=HOLD_CHILD_BUDGET,
        plan_kind=PLAN_LOCAL_MODEL_PRELOAD,
        capabilities=(CAPABILITY_WHISPER_PRELOAD,),
    )
    return TranscriptionAdmission(
        broker=_broker(), principal=principal, plan=plan, parent=None,
        capability=CAPABILITY_WHISPER_PRELOAD,
    )


__all__ = [
    "DEVICE_SERVICE_IDENTITY",
    "HOLD_CAPTURE_CEILING_SECONDS",
    "HOLD_CHILD_BUDGET",
    "HOLD_DRAIN_SECONDS",
    "ONE_SHOT_DEADLINE_SECONDS",
    "PRELOAD_SERVICE_IDENTITY",
    "SessionGeneration",
    "SpeechSession",
    "WAKE_AUTHORITY_REQUIRED",
    "WAKE_CHILD_BUDGET",
    "WAKE_DEADLINE_SECONDS",
    "WAKE_SERVICE_IDENTITY",
    "admit_device_session",
    "admit_hold_session",
    "admit_one_shot_session",
    "admit_speech_session",
    "admit_wake_session",
    "device_service_principal",
    "hold_gesture_principal",
    "model_config_revision",
    "preload_service_admission",
    "preload_service_principal",
    "seal_hold_release",
    "wake_config_revision",
    "wake_service_principal",
]
