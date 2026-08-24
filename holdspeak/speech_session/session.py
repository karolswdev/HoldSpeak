"""Admitted speech capture sessions: one finite parent per authority lifetime (HS-131-09).

A desktop hold, a configured wake capture, and a one-shot browser speak-to-fill
each open ONE finite ``dictation.session`` / ``wake.session`` parent over ONE
frozen plan, and close it when the bounded tail drains. Continuation is always a
new authenticated session, never an epoch reset.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .plan import (
    CAPABILITY_NOT_PLANNED,
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
    ENTRY_SESSION_REQUIRED,
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
    pipeline_provider_capabilities,
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

# ------------------------------------------------------- synthetic-text entries
# HS-131-15. The five entrances that run the FULL configured dictation pipeline
# over text that was never captured here: four browser routes and one command.
# Each opens its own short, credential-authenticated session; none may join an
# open-mic interval, a hold, or a wake capture.
AIM_BROWSER_REHEARSE = "browser-rehearse"
AIM_JOURNAL_REPLAY = "journal-replay"
AIM_TEMPLATE_PREVIEW = "template-preview"
AIM_REMOTE_DELIVERY = "remote-delivery"
AIM_CLI_DRY_RUN = "cli-dry-run"
ENTRY_AIMS = frozenset(
    {
        AIM_BROWSER_REHEARSE,
        AIM_JOURNAL_REPLAY,
        AIM_TEMPLATE_PREVIEW,
        AIM_REMOTE_DELIVERY,
        AIM_CLI_DRY_RUN,
    }
)
#: No audio to wait on — just the bounded classify/rewrite tail.
ENTRY_DEADLINE_SECONDS = 90.0
#: One classify plus its compatibility retry, the configured rewrite passes, and
#: the target-detection dispatch fit; an abandoned tail does not.
ENTRY_CHILD_BUDGET = 12
#: The env var that carries the hub-issued owner bearer into a separate process.
#: The same name the MCP sidecar and `holdspeak doctor` already read, so an
#: automation exports it once. It is the token the CLI POSSESSES; the hub's own
#: configured token is what it is checked against.
CLI_CREDENTIAL_ENV = "HOLDSPEAK_TOKEN"
#: The honest terminal outcome when a close/cancel could not be PERSISTED. The
#: parent's real end state is unknown, and "" (the old swallow) claimed nothing
#: went wrong.
OUTCOME_INDETERMINATE = "indeterminate"

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
        "wake-capture:configured-capture",
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
    _routed_routes: dict[str, dict[str, Any]] = None
    #: A Phase-D atomic parent/route bundle.  Historical parents deliberately
    #: retain only their v1 ``SpeechSessionPlan`` reader.
    _route_bundle: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # Eager construction is part of admission. Lazy first access let two threads
        # install different SessionFence instances: wake cancellation could cancel
        # one lock/event while transcription retained the other and still published.
        if self._fence is None:
            from .fence import SessionFence

            self._fence = SessionFence(
                broker=self.broker,
                operation_id=str(self.parent.operation_id),
                deadline_at=float(self.plan.deadline_at),
            )
        if self._routed_routes is None:
            self._routed_routes = {}

    def freeze_assigned_provider_routes(self) -> None:
        """Freeze assignment routes while this session is still admitting."""
        with self.broker.database._connection() as conn:
            active = conn.execute(
                "SELECT 1 FROM inference_assignment_migrations "
                "WHERE family='thoughts-writing-route-assignments'"
            ).fetchone() is not None
        if not active:
            return
        aliases = {
            CAPABILITY_INTENT_CLASSIFY: "speech.intent_classify",
            "rewrite": "speech.rewrite",
        }
        requested = [
            {"key": legacy, "capability_id": canonical, "invocation_id": self.plan.session_id}
            for legacy, canonical in aliases.items() if self.plan.has(legacy)
        ]
        if requested:
            self._routed_routes.update(
                self.broker.inference_adoption_service.freeze_route_set(
                    self.principal,
                    command_id=f"speechroutes-{self.plan.session_id}",
                    routes=requested,
                )
            )

    @property
    def operation_id(self) -> str:
        return str(self.parent.operation_id)

    @property
    def context(self) -> Any:
        return self.parent.context

    @property
    def fence(self) -> Any:
        """This session's admission-time immutable cancellation carrier."""
        assert self._fence is not None
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
            routed_routes=dict(self._routed_routes),
            transcription_route=self._routed_route("speech.transcribe"),
        )

    def _routed_route(self, capability_id: str) -> dict[str, Any] | None:
        if self._route_bundle is None:
            return None
        member = next(
            (
                item for item in self._route_bundle.get("members", ())
                if item.get("capability_id") == capability_id
            ),
            None,
        )
        return None if member is None else {"id": str(member["route_plan_id"])}

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
        """Close the parent with its honest terminal outcome, exactly once.

        A close that cannot be PERSISTED returns
        :data:`OUTCOME_INDETERMINATE`, not ``""`` (HS-131-15, Sol Amendment 4).
        The old empty string was indistinguishable from "nothing to do" and let a
        caller report success over a parent whose real end state is unknown.
        """
        try:
            existing = self.broker.store.receipt(self.parent.operation_id)
            if existing is not None:
                return str(existing["outcome"])
            receipt = self.broker.parent_run_controller.close(
                self.parent.context,
                outcome,
                principal=self.principal,
                publication_claim_id=self.fence.publication_claim_id,
            )
            return str(receipt.get("outcome") or outcome)
        except Exception as exc:
            log.error("speech session close failed: %s", type(exc).__name__)
            return OUTCOME_INDETERMINATE

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
            return OUTCOME_INDETERMINATE
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
            return OUTCOME_INDETERMINATE

    def transcription(
        self,
        capability: str = CAPABILITY_WHISPER_TRANSCRIBE,
        *,
        on_claim: Any = None,
        utterance_ref: str = "",
    ) -> Any:
        """The admission handle ``Transcriber`` dispatches one child under.

        A Phase-D bundle is the new-work authority; the v1 plan remains only for
        persisted historical sessions that predate the speech migration marker.
        ``on_claim`` runs inside the first claimed transcription child (the
        browser interval's lease refresh).
        """
        if self._route_bundle is not None:
            from .transcription import RoutedSpeechTranscriptionAdmission

            return RoutedSpeechTranscriptionAdmission(
                broker=self.broker,
                principal=self.principal,
                parent=self.parent,
                bundle=self._route_bundle,
                fence=self.fence,
                utterance_ref=str(utterance_ref),
                on_claim=on_claim,
                single_preload_sequence=any(
                    item.get("capability_id") == "speech.preload"
                    for item in self._route_bundle.get("members", ())
                ),
            )
        from .transcription import TranscriptionAdmission

        return TranscriptionAdmission(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            fence=self.fence,
            capability=capability,
            on_claim=on_claim,
            utterance_ref=str(utterance_ref),
        )

    def frozen_transcriber_arguments(self) -> dict[str, str] | None:
        """Return construction fields derived from this bundle's speech route.

        The derived-preload evidence is cross-bound to the source transcription
        route and deployment revision by the bundle service.  It is therefore the
        only lawful source for a new-session transcriber's backend/model/language.
        """
        if self._route_bundle is None:
            return None
        transcription = next(
            (
                item for item in self._route_bundle.get("members", ())
                if item.get("capability_id") == "speech.transcribe"
            ),
            None,
        )
        for evidence in self._route_bundle.get("derived_preloads", ()):
            if (
                transcription is not None
                and evidence.get("transcription_route_plan_id")
                == transcription.get("route_plan_id")
            ):
                return {
                    "model_name": str(evidence["model"]),
                    "backend": str(evidence["engine"]),
                    "language": str(evidence["language"]),
                }
        # A frozen transcription member remains the sole construction source if a
        # historical bundle lacks derived lifecycle evidence; never read mutable
        # Config after admission.
        if transcription is None:
            raise SpeechSessionRefused("speech_route_construction_missing")
        with self.broker.database._connection() as conn:
            row = conn.execute(
                """SELECT d.engine,d.model,p.capability_manifest_json
                     FROM inference_route_plan_entries e
                     JOIN deployment_revisions d ON d.id=e.deployment_revision_id
                     JOIN model_profile_revisions p
                       ON p.profile_id=e.profile_id AND p.revision=e.profile_revision
                    WHERE e.plan_id=? ORDER BY e.route_leg_ordinal LIMIT 1""",
                (str(transcription["route_plan_id"]),),
            ).fetchone()
        if row is None:
            raise SpeechSessionRefused("speech_route_construction_missing")
        engine, model = str(row["engine"]), str(row["model"])
        prefix = f"builtin-whisper-{engine}-"
        model = model.removeprefix(prefix)
        try:
            claims = json.loads(str(row["capability_manifest_json"]))["claims"]
            language = next(
                str(item).removeprefix("speech_language:")
                for item in claims if str(item).startswith("speech_language:")
            )
        except (KeyError, TypeError, ValueError, StopIteration) as exc:
            raise SpeechSessionRefused("speech_route_construction_missing") from exc
        return {"model_name": model, "backend": engine, "language": language}


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
    plan_defaults: bool = True,
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
    broker = _broker()
    with broker.database._connection() as conn:
        provider_routing = conn.execute(
            "SELECT 1 FROM inference_assignment_migrations "
            "WHERE family='thoughts-writing-route-assignments'"
        ).fetchone() is not None
        speech_routing = conn.execute(
            "SELECT 1 FROM inference_assignment_migrations "
            "WHERE family='speech-recognition-route-assignments'"
        ).fetchone() is not None
    # Phase-D is one coupled parent authority: speech cannot enter a bundle until
    # every configured dictation provider member can enter that same bundle.  A
    # partial migration keeps the entire established session shape; otherwise a
    # parent could mix a frozen speech child with an unbundled legacy provider
    # child and spend capacity outside its declared route authority.
    new_speech_route = (
        speech_routing
        and provider_routing
        and plan_defaults
        and principal.identity != DEVICE_SERVICE_IDENTITY
    )
    # The plan DTO survives only for a wholly legacy parent (and paired-device
    # capture, which remains outside Phase D).  A bundled parent never treats its
    # default Whisper entries as authority.
    retained_capabilities = capabilities
    retained_defaults = plan_defaults
    if new_speech_route:
        retained_capabilities = tuple(
            dict.fromkeys((*capabilities, *pipeline_provider_capabilities(config_snapshot)))
        )
        retained_defaults = False
    plan = DictationSessionPlanResolver().resolve(
        config_snapshot,
        registry_snapshot,
        principal,
        insertion_aim,
        session_id=identifier,
        deadline_at=deadline,
        child_budget=int(child_budget),
        plan_kind=plan_kind or (PLAN_WAKE if kind == PARENT_WAKE_SESSION else PLAN_DICTATION),
        capabilities=retained_capabilities,
        plan_defaults=retained_defaults,
        insertion_context=insertion_context,
        created_at=started,
    )
    parent_snapshot = plan.summary()
    if kind == PARENT_WAKE_SESSION:
        # The policy lookup is intentionally fixed.  The configured wake revision
        # rides immutable parent evidence instead of becoming a permissive
        # registry-key suffix.
        parent_snapshot["wake_capture_revision"] = wake_config_revision(
            getattr(config_snapshot, "wake_word", None)
        )

    # Phase D new work persists the capture parent and every route it can use in
    # one bundle transaction.  The old session plan remains an execution reader
    # only for parents admitted before the speech migration marker.
    if new_speech_route:
        from ..services.inference_parent_route_bundle_service import InferenceParentRouteBundleService

        aliases = {
            CAPABILITY_INTENT_CLASSIFY: "speech.intent_classify",
            "rewrite": "speech.rewrite",
        }
        routes: list[dict[str, str]] = [
            {
                "key": "transcription",
                "capability_id": "speech.transcribe",
                "invocation_id": plan.session_id,
            }
        ]
        routes.extend(
            {
                "key": legacy,
                "capability_id": canonical,
                "invocation_id": plan.session_id,
            }
            for legacy, canonical in aliases.items()
            if provider_routing and plan.has(legacy)
        )
        # The lifecycle is derived from the frozen transcription member, not an
        # assignable preload row.  OWNER capture and the closed wake SERVICE
        # policy are both lawful parents for that one P=1 member.
        derived_preload = (
            {
                "key": "preload",
                "source_key": "transcription",
                "candidate_material": [],
                "strategy_sequence": ["derive-from-frozen-transcription"],
            }
            if (
                principal.kind is PrincipalKind.OWNER
                or principal.identity == WAKE_SERVICE_IDENTITY
            )
            else None
        )
        # A capture parent is reusable: browser intervals can carry many
        # utterances, and each may consume its route policy's physical attempts.
        # Preserve the caller's full parent budget instead of treating the bundle
        # declaration's one route as a one-utterance budget.  The P=1 lifecycle
        # receives its own reserved slot; every actual capture/pipeline route
        # shares the remaining parent capacity.
        work_allocation = int(child_budget) - (1 if derived_preload is not None else 0)
        budget_groups: list[dict[str, Any]] = [
            {
                "id": "speech-capture-work",
                "allocation": work_allocation,
                "member_keys": [str(route["key"]) for route in routes],
            }
        ]
        if derived_preload is not None:
            budget_groups.append(
                {"id": "speech-capture-preload", "allocation": 1, "member_keys": ["preload"]}
            )
        try:
            started_bundle = InferenceParentRouteBundleService(
                broker, broker.inference_adoption_service
            ).start(
                principal,
                command_id=f"speech-route-bundle:{plan.session_id}",
                parent_kind=kind,
                definition_ref=f"speech:{identifier}:{insertion_aim or 'capture'}",
                definition_revision=plan.sha256,
                input_snapshot=parent_snapshot,
                deadline_at=deadline,
                routes=routes,
                budget_groups=budget_groups,
                derived_preload=derived_preload,
            )
        except Exception as exc:
            reason = str(
                getattr(exc, "code", "") or getattr(exc, "reason", "") or SESSION_NOT_ADMITTED
            )
            raise SpeechSessionRefused(reason) from None
        parent = started_bundle["parent"]
        bundle = started_bundle["bundle"]
        session = SpeechSession(broker, principal, plan, parent, kind, _route_bundle=bundle)
        for legacy, canonical in aliases.items():
            member = next(
                (item for item in bundle["members"] if item["capability_id"] == canonical),
                None,
            )
            if member is not None:
                session._routed_routes[legacy] = {"id": str(member["route_plan_id"])}
        log.info(
            "speech route bundle admitted: kind=%s parent=%s bundle=%s",
            kind, parent.operation_id, bundle["id"],
        )
        return session

    # Compatibility reader for historical parents (and the explicitly excluded
    # paired-device capture surface).  Do not make a device route policy while
    # migrating owner and wake speech.
    try:
        parent = broker.parent_run_controller.start(
            principal,
            kind=kind,
            definition_ref=f"speech:{identifier}:{insertion_aim or 'capture'}",
            definition_revision=plan.sha256,
            input_snapshot=parent_snapshot,
            deadline_at=deadline,
            child_budget=int(child_budget),
            _defer_persist=provider_routing,
        )
    except Exception as exc:
        reason = str(getattr(exc, "reason", "") or SESSION_NOT_ADMITTED)
        raise SpeechSessionRefused(reason) from None
    frozen_routes: dict[str, dict[str, Any]] = {}
    if provider_routing:
        from ..kernel.parent_run import ParentRun
        from ..services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY

        aliases = {CAPABILITY_INTENT_CLASSIFY: "speech.intent_classify", "rewrite": "speech.rewrite"}
        with broker.database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = broker.parent_run_controller._persist_parent(
                    conn, operation_id=parent.operation_id, native_id=parent.native_id,
                    kind=kind, definition_ref=f"speech:{identifier}:{insertion_aim or 'capture'}",
                    definition_revision=plan.sha256, input_snapshot=parent_snapshot,
                    deadline_at=deadline, child_budget=int(child_budget), now=started,
                )
                for ordinal, (legacy, canonical) in enumerate(aliases.items(), 1):
                    if plan.has(legacy):
                        frozen_routes[legacy] = broker.inference_adoption_service.plans.freeze_route_plan_in_transaction(
                            ROUTE_PLANNING_AUTHORITY, conn,
                            command_id=f"speechroutes-{plan.session_id}-{ordinal}",
                            capability_id=canonical, invocation_id=plan.session_id,
                            deadline_at=deadline,
                        )
                conn.commit()
            except Exception:
                conn.rollback()
                try:
                    broker.receipt(
                        parent.operation_id,
                        "refused",
                        "speech-parent:route-admission-failed",
                        broker.parent_run_controller._node,
                    )
                except Exception:
                    log.exception(
                        "failed to terminalize orphan speech parent %s",
                        parent.operation_id,
                    )
                raise
        parent = ParentRun(
            parent.operation_id, str(row["native_id"]),
            broker.parent_run_controller._context(row),
        )
    log.info(
        "speech session admitted: kind=%s parent=%s plan=%s", kind, parent.operation_id, plan.sha256
    )
    session = SpeechSession(broker, principal, plan, parent, kind)
    if provider_routing:
        session._routed_routes.update(frozen_routes)
    else:
        session.freeze_assigned_provider_routes()
    return session


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


# ------------------------------------------------- synthetic-text entry (HS-131-15)


def cli_owner_principal(config_snapshot: Any = None) -> Optional[Principal]:
    """Derive the command line's owner principal from a hub-issued credential.

    Sol Amendment 1. Three things this deliberately is NOT:

    * it does not MINT ``Principal(OWNER)`` and does not call
      :func:`hold_gesture_principal` — a command is not a physical hold gesture;
    * it does not infer authority from UID, TTY, loopback, or process location,
      and accepts no ``--principal`` flag;
    * it does not ISSUE itself a credential in order to run
      (:func:`~holdspeak.web_auth.ensure_web_token` is never called here).

    The bearer the process POSSESSES comes from ``$HOLDSPEAK_TOKEN`` — the same
    env var the MCP sidecar and ``holdspeak doctor`` already read — and is checked
    against the hub's own configured credential through
    :func:`~holdspeak.principals.derive_owner`, the SAME central authenticator the
    web edge uses. No bearer, no configured hub credential, or a mismatch all
    return ``None``, and the caller refuses by name before constructing a
    provider.
    """
    import os

    from ..principals import derive_owner

    if config_snapshot is None:
        from ..config import Config

        config_snapshot = Config.load()
    provided = str(os.environ.get(CLI_CREDENTIAL_ENV) or "").strip()
    expected = str(
        getattr(getattr(config_snapshot, "meeting", None), "web_auth_token", "") or ""
    ).strip()
    return derive_owner(provided, expected)


def admit_text_entry_session(
    *,
    principal: Any,
    insertion_aim: str,
    config_snapshot: Any,
    registry_snapshot: Any = None,
    now: Optional[float] = None,
) -> SpeechSession:
    """One synthetic-text entrance = one fresh, short ``dictation.session``.

    The capabilities are exactly what THIS configuration snapshot physically
    selects (:func:`~holdspeak.speech_session.plan.pipeline_provider_capabilities`)
    and ``plan_defaults=False`` keeps Whisper transcription and preload OUT of the
    plan: there is no audio here, so no capture authority may be consumed.

    ``principal`` is never defaulted. A route passes the credential middleware's
    ``request.state.principal``; the command passes
    :func:`cli_owner_principal`. ``None`` refuses by name.
    """
    aim = str(insertion_aim or "")
    if aim not in ENTRY_AIMS:
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
    if config_snapshot is None:
        raise SpeechSessionRefused(SESSION_NOT_ADMITTED)
    return admit_speech_session(
        kind=PARENT_DICTATION_SESSION,
        principal=principal,
        insertion_aim=aim,
        config_snapshot=config_snapshot,
        registry_snapshot=registry_snapshot,
        deadline_seconds=ENTRY_DEADLINE_SECONDS,
        child_budget=ENTRY_CHILD_BUDGET,
        capabilities=pipeline_provider_capabilities(config_snapshot),
        plan_defaults=False,
        now=now,
    )


def require_entry_admission(admission: Any, fence: Any) -> Any:
    """Prove this really IS a live, fresh, synthetic-text admission, or refuse.

    The shared pipeline helper never mints a session; it is HANDED one. That is
    only safe if it can tell a genuine entry admission from the four things a
    caller might hand it instead, so this refuses by name on:

    * a missing or duck-typed ``admission``/``fence`` (a stub with a ``.child``
      would otherwise dispatch);
    * a fence belonging to a DIFFERENT session than the admission;
    * an open-mic interval, hold, wake, or device parent being borrowed — caught
      by the entry aim and by the presence of Whisper capabilities no
      synthetic-text plan may hold;
    * a session that is already ended, expired, revoked, or cancelled;
    * a capability this configuration requires that the plan could not resolve.

    Returns the frozen plan. Called BEFORE any runtime construction.
    """
    from .fence import SessionFence
    from .provider import ProviderAdmission

    if not isinstance(admission, ProviderAdmission) or not isinstance(fence, SessionFence):
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
    parent = getattr(admission, "parent", None)
    parent_operation_id = str(getattr(parent, "operation_id", "") or "")
    parent_context_id = str(
        getattr(getattr(parent, "context", None), "operation_id", "") or ""
    )
    if (
        admission.fence is not fence
        or admission.broker is not fence.broker
        or parent_operation_id != str(fence.operation_id)
        or parent_context_id != parent_operation_id
    ):
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
    plan = admission.plan
    if plan is None or str(getattr(plan, "insertion_aim", "")) not in ENTRY_AIMS:
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)

    # Bind the plan and principal to the durable parent too. Object identity among
    # the provider/fence/parent carriers does not prove that a caller did not swap
    # in another live session's frozen plan, which would retarget child revisions
    # and egress while receipts still named this parent.
    try:
        with admission.broker.store._connection() as conn:
            row = conn.execute(
                "SELECT p.definition_revision,p.input_json,"
                "o.principal_kind,o.principal_identity "
                "FROM kernel_parent_runs p JOIN kernel_operations o "
                "ON o.operation_id=p.operation_id WHERE p.operation_id=?",
                (parent_operation_id,),
            ).fetchone()
        parent_input = json.loads(str(row["input_json"] or "{}")) if row else {}
    except Exception:
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED) from None
    principal = admission.principal
    plan_sha = str(getattr(plan, "sha256", "") or "")
    if (
        row is None
        or not plan_sha
        or str(row["definition_revision"] or "") != plan_sha
        or str(parent_input.get("plan_sha256") or "") != plan_sha
        or str(parent_input.get("session_id") or "")
        != str(getattr(plan, "session_id", "") or "")
        or str(parent_input.get("insertion_aim") or "")
        != str(getattr(plan, "insertion_aim", "") or "")
        or str(getattr(principal, "name", "") or "")
        != str(row["principal_kind"] or "")
        or str(getattr(principal, "identity", "") or "")
        != str(row["principal_identity"] or "")
    ):
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
    if plan.has(CAPABILITY_WHISPER_TRANSCRIBE) or plan.has(CAPABILITY_WHISPER_PRELOAD):
        raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
    # An UNRESOLVED capability is a capability this configuration needs and this
    # plan could not freeze a revision for. Refusing here — before construction —
    # is what stops it from surfacing later as a "runtime unavailable" limitation.
    for capability in plan.unresolved:
        raise SpeechSessionRefused(CAPABILITY_NOT_PLANNED, str(capability))
    reason = fence.reason()
    if reason:
        raise SpeechSessionRefused(reason)
    return plan


class SpeechEntry:
    """ONE admitted text entry and its single, non-swallowing terminal owner.

    Sol Amendment 4: once admission succeeds, exactly one ``try/finally`` owner is
    responsible for an honest terminal parent outcome — on success, named refusal,
    provider failure, cancellation, expiry, and every escaped exception. Used as a
    context manager, that owner is this object:

    * clean exit closes ``succeeded``;
    * :class:`KeyboardInterrupt` and ``asyncio.CancelledError`` CANCEL (a command
      interrupt and a browser disconnect are the same decision);
    * a named :class:`SpeechSessionRefused` closes ``refused``;
    * anything else closes ``failed``.

    The exception itself is never suppressed, and a close that cannot be persisted
    is logged as indeterminate rather than reported as a clean end.
    """

    __slots__ = ("session", "provider", "fence", "plan", "terminal", "_closed")

    def __init__(self, session: SpeechSession) -> None:
        self.session = session
        self.provider = session.provider()
        self.fence = self.provider.fence
        self.plan = session.plan
        #: The outcome actually RECORDED for this parent — not the one requested.
        #: ``""`` until closed; :data:`OUTCOME_INDETERMINATE` when the close or
        #: cancel could not be persisted.
        self.terminal = ""
        self._closed = False

    @property
    def indeterminate(self) -> bool:
        """True when this parent's real terminal state is unknown.

        Every owner reads this and SAYS SO. Logging it and returning a string
        nobody looked at was the same swallow in a different coat: the caller
        went on to report a clean success over a parent whose end state was never
        written. It is deliberately NOT an exception — a preview whose
        publication already won the election really did produce its result, and a
        remote send whose delivery already typed really did type. Turning an
        unknown *bookkeeping* outcome into a failed *effect* would be a second
        lie in the opposite direction (Sol Amendment 4).
        """
        return self.terminal == OUTCOME_INDETERMINATE

    def validate(self) -> Any:
        """Re-prove the live admission and frozen plan before construction."""
        return require_entry_admission(self.provider, self.fence)

    def close(self, outcome: str = "succeeded") -> str:
        # The terminal owner contends on the SAME election as publication and
        # cancellation. Without this lock, a disconnect watcher could set `_closed`
        # after the final response/journal callback won but before success closure,
        # then durably cancel the parent underneath the response already returning.
        with self.fence.election:
            if self._closed:
                return self.terminal
            self.terminal = self.session.close(outcome)
            self._closed = not self.indeterminate
            if self.indeterminate:
                # Unknown is not terminal ownership. Fence the in-memory carrier so
                # no new child can use a parent whose durable end is uncertain, but
                # leave the owner retryable: a later close/cancel can read an already
                # committed receipt or settle a parent that remained OPEN.
                cancel = getattr(self.fence, "cancel", None)
                if callable(cancel):
                    cancel()
                log.error(
                    "speech entry terminal state is indeterminate: parent=%s aim=%s requested=%s",
                    self.session.operation_id,
                    self.plan.insertion_aim,
                    outcome,
                )
            return self.terminal

    def cancel(self) -> str:
        # Serializes the `_closed` election too: cancellation-first closes the fence
        # and parent before publication can run; final-publication-first settles the
        # parent succeeded before a watcher can overwrite it as cancelled.
        with self.fence.election:
            if self._closed:
                return self.terminal
            self.terminal = self.session.cancel_and_close()
            self._closed = not self.indeterminate
            if self.indeterminate:
                # ``cancel_and_close`` fences first, so no work can continue even
                # when persistence is unknown. Keep terminal ownership retryable;
                # the next attempt can discover a committed receipt or finish the
                # durable cancellation rather than becoming a permanent no-op.
                cancel = getattr(self.fence, "cancel", None)
                if callable(cancel):
                    cancel()
                log.error(
                    "speech entry cancellation is indeterminate: parent=%s aim=%s",
                    self.session.operation_id,
                    self.plan.insertion_aim,
                )
            return self.terminal

    def __enter__(self) -> "SpeechEntry":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        import asyncio

        if exc is None:
            self.close("succeeded")
        elif isinstance(exc, (KeyboardInterrupt, asyncio.CancelledError)):
            self.cancel()
        elif isinstance(exc, SpeechSessionRefused):
            self.close("refused")
        else:
            self.close("failed")
        return False


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
    "AIM_BROWSER_REHEARSE",
    "AIM_CLI_DRY_RUN",
    "AIM_JOURNAL_REPLAY",
    "AIM_REMOTE_DELIVERY",
    "AIM_TEMPLATE_PREVIEW",
    "CLI_CREDENTIAL_ENV",
    "DEVICE_SERVICE_IDENTITY",
    "ENTRY_AIMS",
    "ENTRY_CHILD_BUDGET",
    "ENTRY_DEADLINE_SECONDS",
    "HOLD_CAPTURE_CEILING_SECONDS",
    "HOLD_CHILD_BUDGET",
    "HOLD_DRAIN_SECONDS",
    "ONE_SHOT_DEADLINE_SECONDS",
    "OUTCOME_INDETERMINATE",
    "PRELOAD_SERVICE_IDENTITY",
    "SessionGeneration",
    "SpeechEntry",
    "SpeechSession",
    "WAKE_AUTHORITY_REQUIRED",
    "WAKE_CHILD_BUDGET",
    "WAKE_DEADLINE_SECONDS",
    "WAKE_SERVICE_IDENTITY",
    "admit_device_session",
    "admit_hold_session",
    "admit_one_shot_session",
    "admit_speech_session",
    "admit_text_entry_session",
    "admit_wake_session",
    "cli_owner_principal",
    "device_service_principal",
    "hold_gesture_principal",
    "model_config_revision",
    "preload_service_admission",
    "preload_service_principal",
    "require_entry_admission",
    "seal_hold_release",
    "wake_config_revision",
    "wake_service_principal",
]
