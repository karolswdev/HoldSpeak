"""Canonical inference destinations (HS-92-07).

``RuntimeProfile`` remains the synced, version-1 storage/wire primitive.  This
module is the additive product contract over it: target identity is kept apart
from engine/model choice, and readiness is derived without contacting a
destination.  A caller can therefore render one honest ``Runs on`` picker
without discovering availability by provoking a run.
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse


TARGET_CONTRACT_VERSION = 1
PROFILE_ALIAS_VERSION = 1
THIS_MACHINE_ID = "this_machine"
PAIRED_DEVICE_ID = "paired_device"
# HS-131-08 (Sol Amendment 1): the hub-default cloud leg, as a NAMEABLE
# destination. The historical `auto` provider fell back local->cloud INSIDE one
# engine, so a receipt could claim the local revision while the cloud endpoint
# ran. Naming this destination lets the plan freeze that fallback as a real
# second entry, and a child that uses it says so.
HUB_DEFAULT_CLOUD_ID = "hub_default_cloud"
#: HS-131-10 round 2: the named refusal for a frozen ``paired_device`` revision
#: reaching the runner's engine factory. Paired execution happens on the paired
#: device, so there is nothing here to build from the revision's frozen fields —
#: and the old fallback silently re-read mutable meeting config instead.
PAIRED_DEVICE_EXECUTION_UNSUPPORTED = "inference_paired_device_execution_unsupported"
#: HS-131-13: the named refusal for a same-device revision that froze no local
#: model path. The old branch answered that case by re-reading mutable meeting
#: config, which is how an admitted child could load a model its immutable
#: revision never named. Fail closed instead: the frozen fields are the only
#: description of what a `this_machine` child is allowed to load.
LOCAL_DEPLOYMENT_MODEL_UNKNOWN = "inference_local_deployment_model_unknown"

# HS-130-01: the ONE terminal, NAMED global placement default. Placement
# inherits DOWN through the precedence tiers; when every tier is unset this is
# the explicit fallback — never `something or "this_machine"` reached by an
# accidental Python ``or``. To move the global default, change this binding.
GLOBAL_DEFAULT_TARGET_ID = THIS_MACHINE_ID

# The four placement tiers, highest precedence first (HS-130-01).
PLACEMENT_SOURCES = ("invocation", "workbench", "agent", "global")

SUPPORTED_PROFILE_KINDS = frozenset(
    {"onDevice", "openAICompatible", "desktop", "meshNode"}
)


def _private_endpoint(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower().rstrip(".")
    if not host:
        return False
    if host in {"localhost", "localhost.localdomain"} or host.endswith(
        (".local", ".internal", ".lan", ".home", ".localhost")
    ):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(address.is_private or address.is_loopback or address.is_link_local)


def _profile_key_present(profile_id: str) -> bool:
    # Readiness is true ONLY when THIS destination has its OWN key under its OWN
    # injective slot (HS-130-02) — never because a punctuation-collided sibling's
    # key happens to be present. A profile with no unique slot (blank id) is never
    # "ready"; it refuses rather than reading a shared name.
    # Import lazily: provider imports this module on some boot paths.
    from .intel.providers import profile_key_env

    try:
        env = profile_key_env(profile_id)
    except ValueError:
        return False
    return bool(os.environ.get(env, "").strip())


def _recovery(reason: str, *, alternate: str = THIS_MACHINE_ID) -> dict[str, str]:
    return {
        "reason": reason,
        "action": "choose_alternate_target",
        "alternate_target_id": alternate,
    }


@dataclass(frozen=True)
class DeploymentIdentity:
    """The ONE (destination, engine, model, node, boundary) a run is pinned to (HS-130-03).

    Computed ONCE from a resolved destination + config, then consumed unchanged by
    readiness (does THIS deployment load?), execution (load exactly it), and the
    receipt (name exactly what loaded). ``model_path`` is the concrete local
    artifact readiness checks and execution loads for a file-loading engine;
    ``model`` is the name the receipt stamps. This is a plain snapshot — Phase 131
    freezes it into an immutable, admission-captured revision. It makes the
    identity SINGULAR so 131 has one true thing to freeze.
    """

    destination_id: str
    kind: str
    engine: str
    model: str
    node: str
    boundary: str
    model_path: Optional[str] = None
    endpoint: str = ""
    secret_slot: str = ""


@dataclass(frozen=True)
class InferenceTarget:
    """One named execution destination, independent of model and engine."""

    id: str
    name: str
    kind: str
    boundary: str
    owner: str
    transport: str
    profile_id: Optional[str]
    engine: str
    model: str
    context_limit: int
    readiness_state: str = "ready"
    readiness_reason: str = ""
    requires_key: bool = False
    key_present: bool = False
    # The single deployment identity this destination resolved to (HS-130-03):
    # the thing readiness checked, execution loads, and the receipt names. Kept
    # optional so older direct constructions still build; the target's own
    # ``model``/``engine`` mirror ``deployment.model``/``deployment.engine``.
    deployment: Optional["DeploymentIdentity"] = None

    @property
    def ready(self) -> bool:
        return self.readiness_state == "ready"

    def to_dict(self) -> dict[str, Any]:
        readiness: dict[str, Any] = {
            "state": self.readiness_state,
            "available": self.ready,
            "reason": self.readiness_reason,
        }
        if not self.ready:
            readiness["recovery"] = _recovery(self.readiness_reason)
        return {
            "version": TARGET_CONTRACT_VERSION,
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "kind": self.kind,
            "boundary": self.boundary,
            "owner": self.owner,
            "transport": self.transport,
            "data_scope": {
                "sent": ["instruction", "selected_context", "grounding"],
                "returned": ["generated_output"],
            },
            # Engine/model are deliberately adjacent facts, not target identity.
            "engine": self.engine,
            "model": self.model,
            "context_limit": self.context_limit,
            "readiness": readiness,
            # Presence is safe to expose; the secret itself never enters the DTO.
            "secret": {"required": self.requires_key, "present": self.key_present},
            "profile_alias": {
                "resource": "profile",
                "version": PROFILE_ALIAS_VERSION,
                "id": self.profile_id,
            },
        }

    def placement_receipt(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        fallback_reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """The immutable actual-placement part of an attempt receipt.

        With no explicit override, the receipt names the resolved deployment
        (HS-130-03) — the same identity readiness checked and execution loaded —
        never an advertised model the run did not load.
        """
        deployment = self.deployment
        if model is None and deployment is not None:
            model = deployment.model
        actual_boundary = self.boundary
        actual_fallback = fallback_reason
        if self.kind == "paired_device" and provider == "cloud":
            actual_boundary = "paired_device_then_external_service"
            actual_fallback = (
                actual_fallback or "Paired device used its configured external engine"
            )
        return {
            "target_id": self.id,
            "target_name": self.name,
            "target_kind": self.kind,
            "boundary": actual_boundary,
            "owner": self.owner,
            "transport": self.transport,
            "data_classes": [
                "instruction",
                "selected_context",
                "grounding",
                "generated_output",
            ],
            "engine": provider or self.engine,
            "model": model or self.model,
            "fallback_reason": actual_fallback,
        }


def _this_machine_readiness() -> tuple[str, str]:
    """Readiness for the LOCAL meeting-intel model this device will actually load.

    HS-130-03: ``this_device`` execution pins ``local`` and loads the configured
    meeting-intel model (``build_intel_for_revision``), so readiness checks THAT
    file — not the dictation-runtime (transcription) model, a different subsystem
    the old check read. Ready here means *this deployment will load*.
    """
    from .intel.providers import configured_local_meeting_model_path

    model_path = configured_local_meeting_model_path()
    if model_path and Path(model_path).expanduser().exists():
        return "ready", ""
    return "unavailable", f"model file not found: {model_path}"


def this_machine_target(
    *, name: str = "This device", model: str = ""
) -> InferenceTarget:
    from .intel.providers import configured_local_meeting_model_path

    model_path = configured_local_meeting_model_path()
    state, reason = _this_machine_readiness()
    deployment_model = model or Path(model_path).expanduser().stem
    deployment = DeploymentIdentity(
        destination_id=THIS_MACHINE_ID,
        kind="this_device",
        engine="configured_local_engine",
        model=deployment_model,
        node="",
        boundary="same_device",
        model_path=model_path,
    )
    return InferenceTarget(
        id=THIS_MACHINE_ID,
        name=name,
        kind="this_device",
        boundary="same_device",
        owner="you",
        transport="in_process",
        profile_id=None,
        engine="configured_local_engine",
        model=deployment_model,
        context_limit=16_384,
        readiness_state=state,
        readiness_reason=reason,
        deployment=deployment,
    )


def hub_default_cloud_deployment(effective: Any) -> DeploymentIdentity:
    """The deployment identity of the hub-default cloud leg (HS-131-08).

    ``effective`` is an ``EffectiveEndpoint`` from ``effective_intel_cloud``: the
    resolved endpoint/model/key-slot the cloud leg would actually use. No
    credential material enters the identity — only the slot NAME.
    """
    base_url = str(getattr(effective, "base_url", "") or "")
    private = bool(base_url) and _private_endpoint(base_url)
    return DeploymentIdentity(
        destination_id=HUB_DEFAULT_CLOUD_ID,
        kind="private_endpoint" if private else "external_service",
        engine="openai_compatible",
        model=str(getattr(effective, "model", "") or ""),
        node="",
        boundary="private_network" if private else "external_service",
        model_path=None,
        endpoint=base_url,
        secret_slot=str(getattr(effective, "api_key_env", "") or ""),
    )


def paired_device_target(
    *, name: str = "Paired device", model: str = ""
) -> InferenceTarget:
    """The current hub as seen by an authenticated paired-device caller.

    Readiness reflects a REAL check of the delegated execution path
    (``build_configured_meeting_intel``): a paired target whose hub engine cannot
    load does not report ready (HS-130-03).
    """
    from .intel.providers import configured_meeting_deployment

    dep = configured_meeting_deployment()
    if dep.runnable:
        state, reason = "ready", ""
    else:
        state = "unavailable"
        reason = dep.reason or "Paired device has no runnable engine configured"
    deployment_model = model or dep.model
    deployment = DeploymentIdentity(
        destination_id=PAIRED_DEVICE_ID,
        kind="paired_device",
        engine=dep.engine,
        model=deployment_model,
        node=dep.node,
        boundary="paired_device",
        model_path=dep.model_path,
    )
    return InferenceTarget(
        id=PAIRED_DEVICE_ID,
        name=name,
        kind="paired_device",
        boundary="paired_device",
        owner="you",
        transport="paired_https",
        profile_id=None,
        engine="configured_hub_engine",
        model=deployment_model,
        context_limit=16_384,
        readiness_state=state,
        readiness_reason=reason,
        deployment=deployment,
    )


def target_from_profile(profile: Any, db: Any = None) -> InferenceTarget:
    """Adapt one version-1 ProfileRecord to the canonical target contract."""
    pid = str(getattr(profile, "id", "") or "").strip()
    name = str(getattr(profile, "name", "") or "").strip() or pid
    legacy_kind = str(getattr(profile, "kind", "") or "").strip()
    base_url = str(getattr(profile, "base_url", "") or "").strip()
    node = str(getattr(profile, "node", "") or "").strip()
    model = str(getattr(profile, "model", "") or "").strip()
    requires_key = bool(getattr(profile, "requires_key", False))
    key_present = _profile_key_present(pid) if pid else False
    state, reason = "ready", ""
    # The concrete local artifact this deployment loads, for file-loading engines
    # (HS-130-03). Set for on-device profiles so execution loads exactly the
    # model_file readiness checked; None for endpoint/mesh engines.
    deploy_model_path: Optional[str] = None

    if legacy_kind == "onDevice":
        kind, boundary, owner, transport, engine = (
            "this_device",
            "same_device",
            "you",
            "in_process",
            "local",
        )
        model_file = str(getattr(profile, "model_file", "") or "").strip()
        model = model or model_file
        deploy_model_path = model_file or None
        if not model_file:
            state = "unavailable"
            reason = f"Destination '{name}' names no on-device model file"
        elif not Path(model_file).expanduser().exists():
            state = "unavailable"
            reason = f"model file not found: {model_file}"
    elif legacy_kind == "desktop":
        kind, boundary, owner, transport, engine = (
            "paired_device",
            "paired_device",
            "you",
            "paired_https",
            "paired_runtime",
        )
        if db is not None and model:
            manifests = [m for m in db.model_manifests.list() if m.node == "desktop"]
            if manifests and not any(m.name == model for m in manifests):
                state = "stale_manifest"
                reason = f"Paired device no longer advertises model '{model}'"
    elif legacy_kind == "meshNode":
        kind, boundary, owner, transport, engine = (
            "mesh_node",
            "private_mesh",
            "you",
            "mesh_relay",
            "node_runtime",
        )
        if not node:
            state, reason = "unsupported", f"Destination '{name}' names no mesh node"
        elif db is not None:
            from .intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS

            last = db.mesh_relay.worker_last_seen(node)
            age = None if last is None else (datetime.now() - last).total_seconds()
            if age is None or age > DEFAULT_LIVENESS_WINDOW_SECONDS:
                state = "offline"
                reason = (
                    f"mesh node '{node}' is offline (no worker has ever polled)"
                    if age is None
                    else f"mesh node '{node}' is offline (last seen {int(age)}s ago)"
                )
    elif legacy_kind == "openAICompatible":
        private = _private_endpoint(base_url)
        kind = "private_endpoint" if private else "external_service"
        boundary = "private_network" if private else "external_service"
        owner = "you" if private else "service_provider"
        transport, engine = "https", "openai_compatible"
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            state, reason = (
                "unsupported",
                f"Destination '{name}' has no valid endpoint URL",
            )
        elif requires_key and not key_present:
            from .intel.providers import profile_key_env

            state = "needs_key"
            reason = f"Destination '{name}' needs a key in ${profile_key_env(pid)}"
    else:
        kind, boundary, owner, transport, engine = (
            "unsupported",
            "unknown",
            "unknown",
            "none",
            "unknown",
        )
        state, reason = (
            "unsupported",
            f"Destination '{name}' has unsupported kind '{legacy_kind or 'unknown'}'",
        )

    secret_slot = ""
    if requires_key and pid:
        from .intel.providers import profile_key_env

        secret_slot = profile_key_env(pid)
    deployment = DeploymentIdentity(
        destination_id=pid,
        kind=kind,
        engine=engine,
        model=model,
        node=node,
        boundary=boundary,
        model_path=deploy_model_path,
        endpoint=base_url,
        secret_slot=secret_slot,
    )
    return InferenceTarget(
        id=pid,
        name=name,
        kind=kind,
        boundary=boundary,
        owner=owner,
        transport=transport,
        profile_id=pid,
        engine=engine,
        model=model,
        context_limit=int(getattr(profile, "context_limit", 16_384) or 16_384),
        readiness_state=state,
        readiness_reason=reason,
        requires_key=requires_key,
        key_present=key_present,
        deployment=deployment,
    )


def list_inference_targets(db: Any) -> list[InferenceTarget]:
    return [this_machine_target()] + [
        target_from_profile(p, db) for p in db.profiles.list()
    ]


def resolve_inference_target(db: Any, target_id: Optional[str]) -> InferenceTarget:
    """Resolve an explicit id or refuse it by name; never silently retarget."""
    raw = str(target_id or THIS_MACHINE_ID).strip() or THIS_MACHINE_ID
    if raw.startswith("profile:"):
        raw = raw.split(":", 1)[1]
    if raw == THIS_MACHINE_ID:
        return this_machine_target()
    if raw == PAIRED_DEVICE_ID:
        return paired_device_target()
    profile = db.profiles.get(raw)
    if profile is None:
        return InferenceTarget(
            id=raw,
            name=raw,
            kind="unsupported",
            boundary="unknown",
            owner="unknown",
            transport="none",
            profile_id=raw,
            engine="unknown",
            model="",
            context_limit=16_384,
            readiness_state="unavailable",
            readiness_reason=f"Destination '{raw}' does not exist on this device",
        )
    return target_from_profile(profile, db)


@dataclass(frozen=True)
class PlacementResolution:
    """The outcome of precedence resolution: a target AND its provenance.

    ``source`` names the tier that WON — one of :data:`PLACEMENT_SOURCES`.
    ``effective_target_id`` is the canonical id the winning pointer resolved
    to; ``target`` is the fully-constructed destination for that id.
    """

    effective_target_id: str
    source: str
    target: InferenceTarget

    def placement_dict(self) -> dict[str, Any]:
        """The wire shape every placement API response carries (HS-130-01)."""
        return {
            "effective_target_id": self.effective_target_id,
            "source": self.source,
        }


def _placement_set(pointer: Optional[str]) -> bool:
    """A tier is SET only when it names a real pointer. ``None``/blank inherits."""
    return bool(pointer is not None and str(pointer).strip())


def resolve_placement(
    db: Any,
    *,
    invocation: Optional[str] = None,
    workbench: Optional[str] = None,
    agent: Optional[str] = None,
) -> PlacementResolution:
    """The ONE placement authority (HS-130-01).

    Turn a stored placement pointer into an effective target, carrying the
    provenance of the tier that won. Precedence, highest first:

        invocation override → Workbench override → Agent/capability default
        → global default

    ``None``/unset at every tier inherits DOWN. The global default
    (:data:`GLOBAL_DEFAULT_TARGET_ID`) is the one terminal, NAMED fallback;
    it is NEVER reached by an accidental ``pointer or "this_machine"``.

    This composes :func:`resolve_inference_target` for the winning tier — it
    does NOT reimplement target construction.
    """
    tiers = (
        ("invocation", invocation),
        ("workbench", workbench),
        ("agent", agent),
    )
    source = "global"
    pointer: Optional[str] = GLOBAL_DEFAULT_TARGET_ID
    for name, value in tiers:
        if _placement_set(value):
            source = name
            pointer = value
            break
    target = resolve_inference_target(db, pointer)
    return PlacementResolution(
        effective_target_id=target.id, source=source, target=target
    )


def target_refusal(target: InferenceTarget) -> dict[str, Any]:
    return {
        "error": target.readiness_reason
        or f"Destination '{target.name}' is unavailable",
        "code": f"inference_target_{target.readiness_state}",
        "inference_target": target.to_dict(),
        "alternate_target_id": THIS_MACHINE_ID,
    }


def target_runtime_error(target: InferenceTarget, error: Any) -> str:
    """Keep remote transport/auth failures attached to the chosen name."""
    detail = str(error)
    if target.boundary == "same_device":
        return detail
    return f"Destination '{target.name}' refused the run: {detail}"


def local_pinned_meeting_intel(
    model_path: Optional[str] = None, *, context: Any = None, revision: Any = None
) -> Any:
    """The same-device engine, built from the FROZEN revision and nothing else.

    A same-device deployment cannot silently become a cross-boundary cloud run
    (HS-131-08): the cloud leg is a separately named deployment revision and a
    separately admitted child. The local model is pinned the same way — to the
    exact path the revision froze.

    HS-131-10: an allowlisted adapter factory, so it requires the runner's dispatch
    context (or the ONE named legacy marker) before it loads anything.

    Round 2 — ``revision`` is now part of the call contract, and a real context
    without one refuses. The gate used to be ``require_dispatch_context(context)``
    with nothing to compare against, so a context genuinely minted for a REMOTE
    child was sufficient authority to build a LOCAL engine: the fence proved that
    SOME child had been admitted, not that THIS deployment was the one it was
    admitted for.

    HS-131-13 — the context gate proved WHICH child; it never proved WHAT gets
    loaded. This branch used to construct through ``configured_meeting_intel``,
    whose body re-reads ``Config.load().meeting`` and hands ``MeetingIntel`` the
    CURRENT ``intel_realtime_model``. An admitted child could therefore run model
    ``B`` while its immutable revision, its child row, and its receipt all named
    model ``A`` — the exact silent retarget Article XI.3 forbids. Construction is
    now from the revision's own fields, with no post-admission configuration read
    on this path at all.
    """
    from .kernel.dispatch_context import bind_dispatch_context, require_bound_context

    bound = require_bound_context(context, revision)
    return bind_dispatch_context(
        _local_pinned_engine(model_path, context=context, revision=revision), bound
    )


def _local_pinned_engine(
    model_path: Optional[str] = None, *, context: Any = None, revision: Any = None
) -> Any:
    """Construct the pinned same-device engine (reached only past the context gate).

    Exactly one source of truth for what loads: the frozen local model path — the
    caller's explicit one, else the revision's own. ``provider`` is pinned
    ``local`` at construction rather than corrected afterwards, so there is no
    window in which a cloud-capable adapter exists for a same-device child.
    """
    from .intel.engine import MeetingIntel
    from .kernel.model import KernelRefused

    path = str(model_path or getattr(revision, "model_path", "") or "").strip()
    if not path:
        # No frozen local model, no run. Reading the live config here is what the
        # HS-131-13 audit caught; refusing by name is the honest alternative.
        raise KernelRefused(LOCAL_DEPLOYMENT_MODEL_UNKNOWN)
    return MeetingIntel(provider="local", model_path=path)


def build_intel_for_revision(
    revision: Any, *, warrant: Any = None, context: Any = None
) -> Any:
    """The runner's engine factory: context-requiring, bound through EVERY branch.

    HS-131-10: the context is validated ONCE against this exact revision (in
    memory — no row is read), and then bound onto whatever branch constructed the
    adapter, so cloud, ``this_machine``, Whisper, and profile/mesh all carry the
    same proof of admission. Without a context this refuses by name before any
    provider object exists.
    """
    from .kernel.dispatch_context import bind_dispatch_context, require_bound_context

    bound = require_bound_context(context, revision)
    return bind_dispatch_context(
        _engine_for_revision(revision, warrant=warrant, context=context), bound
    )


def _engine_for_revision(
    revision: Any, *, warrant: Any = None, context: Any = None
) -> Any:
    """Construct from an admitted revision, never a mutable profile row.

    The established profile builder owns engine-specific behavior (notably mesh
    adapters and exact provider configuration). It receives only frozen values
    from the revision; it never receives or reads the editable profile record.

    ``this_machine`` is pinned LOCAL and the hub-default cloud leg is built from
    its own named revision, so a revision is never a lie about where the run went
    (HS-131-08, Sol Amendment 1).
    """
    from .intel.engine import MeetingIntel
    from .intel.providers import build_meeting_intel_for_profile  # NOT configured_*: see paired, below
    from .speech_session.plan import WHISPER_KIND, LocalWhisperDeployment

    if revision.kind == WHISPER_KIND:
        # On-device speech-to-text (HS-131-09). The loaded Whisper backend lives
        # in the caller's `Transcriber`, so construction here loads nothing and
        # reads no mutable config — it only carries the frozen revision.
        return LocalWhisperDeployment(revision)
    if revision.destination_id == HUB_DEFAULT_CLOUD_ID:
        return MeetingIntel(
            provider="cloud",
            cloud_model=revision.model,
            cloud_api_key_env=revision.secret_slot,
            cloud_base_url=revision.endpoint or None,
        )
    if revision.destination_id == THIS_MACHINE_ID:
        return local_pinned_meeting_intel(
            revision.model_path, context=context, revision=revision
        )

    # HS-131-10 round 2: `paired_device` is NOT in this map and has no fallback.
    # It used to map to the profile kind ``desktop``, which no branch of
    # `_profile_engine` builds, so it fell through to `configured_meeting_intel`
    # and re-read MUTABLE meeting config at dispatch time — a revision frozen with
    # model ``FROZEN-MODEL`` executed against whatever the config said just then,
    # while the receipt still named the frozen revision. There is no way to
    # construct paired execution from the revision's own fields (the work belongs
    # to the paired device), so it refuses BY NAME before any physical work,
    # rather than lying about where the run went.
    profile_kind = {
        "mesh_node": "meshNode",
        "private_endpoint": "openAICompatible",
        "external_service": "openAICompatible",
        "this_device": "onDevice",
    }.get(revision.kind)
    if profile_kind is not None and revision.destination_id:
        return build_meeting_intel_for_profile(
            kind=profile_kind,
            base_url=revision.endpoint,
            model=revision.model,
            profile_id=revision.destination_id,
            node=revision.node,
            model_file=revision.model_path or "",
            deployment_revision=revision,
            warrant=warrant,
            context=context,
        )
    if revision.kind == "paired_device":
        from .kernel.model import KernelRefused

        raise KernelRefused(PAIRED_DEVICE_EXECUTION_UNSUPPORTED)
    raise ValueError(f"unsupported admitted deployment revision {revision.id}")


# HS-131-13 deleted `build_intel_for_target(target, db)`. It was the second legacy
# uncontextual factory: it took a MUTABLE resolved target, re-read the profile row,
# and constructed an engine with no admitted child, no immutable revision, and no
# terminal receipt behind it. Its two callers (the second Decisions route seam and
# the dormant Delivery review helper) are gone, so the factory goes with them —
# NOT wrapped in a compatibility shim. `build_intel_for_revision(revision, *,
# context=...)` is the one construction path, and it validates the runner's
# dispatch context against the exact frozen revision before anything is built.
