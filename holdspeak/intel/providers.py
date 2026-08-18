"""Intel provider resolution + egress posture (HS-34-04).

`OpenAI`/`Llama` live in the package `__init__` (the optional-dependency import
head) and are read here *via the package* (`_intel_pkg.OpenAI`/`.Llama`) so tests
that monkeypatch `holdspeak.intel.OpenAI` / `holdspeak.intel.Llama` are honored.
"""

from __future__ import annotations

import hashlib
import ipaddress
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional
from urllib.parse import urlparse

import holdspeak.intel as _intel_pkg

from ..logging_config import get_logger

if TYPE_CHECKING:
    from .engine import MeetingIntel
from .models import (
    DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    DEFAULT_INTEL_CLOUD_MODEL,
    DEFAULT_INTEL_MODEL_PATH,
    DEFAULT_INTEL_PROVIDER,
    SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER,
    VALID_INTEL_PROVIDERS,
)

log = get_logger("intel")


def _normalize_provider(provider: Optional[str]) -> str:
    value = (provider or DEFAULT_INTEL_PROVIDER).strip().lower()
    if value not in VALID_INTEL_PROVIDERS:
        return DEFAULT_INTEL_PROVIDER
    return value


def _resolve_cloud_api_key(api_key_env: Optional[str]) -> Optional[str]:
    env_name = (api_key_env or DEFAULT_INTEL_CLOUD_API_KEY_ENV).strip()
    if not env_name:
        env_name = DEFAULT_INTEL_CLOUD_API_KEY_ENV
    from ..profile_key_store import ProfileKeyStoreError, resolve_profile_key

    try:
        return resolve_profile_key(env_name)
    except ProfileKeyStoreError:
        return None


def _is_self_hosted_base_url(base_url: Optional[str]) -> bool:
    """True when a custom (non-default) cloud base URL is configured."""
    return bool(base_url and base_url.strip())


def _effective_cloud_api_key(
    api_key_env: Optional[str], base_url: Optional[str]
) -> Optional[str]:
    """Resolve the key to hand the OpenAI client.

    Returns the env key when set. For a self-hosted endpoint (any custom
    ``base_url``) with no key, returns a placeholder so the SDK can connect.
    Returns ``None`` only when talking to the default OpenAI API with no key.
    """
    key = _resolve_cloud_api_key(api_key_env)
    if key:
        return key
    if _is_self_hosted_base_url(base_url):
        return SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER
    return None


def _validate_base_url(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    value = base_url.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return f"Invalid cloud base URL: {value}"
    return None


def get_local_intel_runtime_status(
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
) -> tuple[bool, Optional[str]]:
    """Return whether local meeting intelligence can run right now."""
    if _intel_pkg.Llama is None:
        return False, "llama-cpp-python is not available"

    resolved = Path(model_path).expanduser()
    if not resolved.exists():
        return False, (
            "No language model on this hub. Pick one in Settings under"
            " Intelligence."
        )

    return True, None


def get_cloud_intel_runtime_status(
    *,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Return whether cloud meeting intelligence can run right now."""
    if _intel_pkg.OpenAI is None:
        return False, "openai package is not available"

    if not (cloud_model or "").strip():
        return False, "Cloud intel model is not configured"

    base_url_error = _validate_base_url(cloud_base_url)
    if base_url_error is not None:
        return False, base_url_error

    # A custom base_url means a self-hosted server that ignores the key, so
    # only the default OpenAI endpoint actually requires one.
    if not _effective_cloud_api_key(cloud_api_key_env, cloud_base_url):
        return False, f"Missing API key in ${cloud_api_key_env}"

    return True, None


def resolve_intel_provider(
    provider: str = DEFAULT_INTEL_PROVIDER,
    *,
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the active provider for this runtime.

    Returns:
        (provider, None) on success where provider is "local" or "cloud".
        (None, reason) when unavailable.
    """
    normalized = _normalize_provider(provider)

    if normalized == "local":
        ok, reason = get_local_intel_runtime_status(model_path)
        return ("local", None) if ok else (None, reason)

    if normalized == "cloud":
        ok, reason = get_cloud_intel_runtime_status(
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
        )
        return ("cloud", None) if ok else (None, reason)

    # auto = local-first fallback to cloud
    local_ok, local_reason = get_local_intel_runtime_status(model_path)
    if local_ok:
        return "local", None

    cloud_ok, cloud_reason = get_cloud_intel_runtime_status(
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    if cloud_ok:
        return "cloud", None

    return (
        None,
        "Local intel unavailable"
        f" ({local_reason}); cloud intel unavailable ({cloud_reason})",
    )


def resolve_llm_capability(meeting_config: Any) -> bool:
    """Whether the ``"llm"`` plugin capability should be enabled.

    True iff meeting intelligence is enabled in config *and* an intel provider
    resolves (HS-16-02). The check is cheap — `resolve_intel_provider` only
    inspects config + file existence, it does not warm a model. Any failure
    (including a malformed config) is non-fatal and yields ``False`` so the host
    is still constructed; LLM-backed plugins then cleanly block at execute time.
    """
    try:
        if not bool(getattr(meeting_config, "intel_enabled", False)):
            return False
        # HS-130-05: judge the ONE placement decision (an adopted destination
        # wins over the local/auto/cloud intent), not ``intel_provider`` alone.
        placement = resolve_meeting_placement(meeting_config)
        if placement.node:
            # a mesh-adopted endpoint has no base_url for the resolver to
            # judge; the capability EXISTS (the relay provider is the engine)
            # and node liveness is a run-time question with a named refusal
            return True
        kwargs: dict[str, Any] = {
            "cloud_model": placement.model,
            "cloud_api_key_env": placement.api_key_env,
            "cloud_base_url": placement.base_url,
        }
        model_path = getattr(meeting_config, "intel_realtime_model", None)
        if model_path:
            kwargs["model_path"] = model_path
        resolved, _reason = _intel_pkg.resolve_intel_provider(placement.provider, **kwargs)
        return resolved is not None
    except Exception:
        return False


def _configured_engine() -> "MeetingIntel":
    """Construct a `MeetingIntel` from the user's saved meeting config.

    PRIVATE and dominated (HS-131-14). This was ``build_configured_meeting_intel()``
    — a public, exported, UNCONTEXTUAL factory whose signature was literally ``()``,
    which is how fourteen builtin plugins and the segment probe each built their own
    engine with no admitted child behind them. Those callers are deleted and the name
    is gone: the census keeps it in the vocabulary with zero permitted sites, so
    typing it again fails the fence.

    The only caller is :func:`configured_meeting_intel`, which refuses without the
    runner's dispatch context BEFORE this body runs — so no provider object exists
    until an admitted child has proved which deployment it is for.
    """
    from ..config import Config
    from .engine import MeetingIntel

    meeting = Config.load().meeting
    # HS-130-05: the ONE placement decision. An adopted destination (mesh or
    # openAICompatible ``intel_profile_id``) wins over the local/auto/cloud
    # intent, so a selected Meetings destination is honored instead of silently
    # ignored; otherwise ``intel_provider`` decides against the hub default.
    placement = resolve_meeting_placement(meeting)
    if placement.node:
        from .mesh_relay import MeshRelayIntel

        return MeshRelayIntel(node=placement.node, model_hint=placement.model)  # type: ignore[return-value]
    kwargs: dict[str, Any] = {
        "provider": placement.provider,
        "cloud_model": placement.model,
        "cloud_api_key_env": placement.api_key_env,
        "cloud_base_url": placement.base_url,
        "cloud_reasoning_effort": getattr(meeting, "intel_cloud_reasoning_effort", None),
        "cloud_store": bool(getattr(meeting, "intel_cloud_store", False)),
    }
    model_path = getattr(meeting, "intel_realtime_model", None)
    if model_path:
        kwargs["model_path"] = model_path
    return MeetingIntel(**kwargs)


def configured_meeting_intel(*, context: Any, revision: Any = None) -> "MeetingIntel":
    """The configured-placement engine for ONE admitted child (HS-131-10).

    The allowlisted adapter factory every migrated branch uses. It refuses BY
    NAME — before the legacy constructor above runs, so before any provider
    object exists — without the dispatch context the runner minted for the
    claimed child (or the ONE named legacy marker the census pins to its exact
    finding scopes).

    The construction itself is deliberately the module-level ``_configured_engine``
    attribute, so the long-standing injectable seam keeps working; the gate is what
    is new. HS-131-14 privatized that body and deleted its public export — this is
    now the ONE entrance to configured construction, contextual by construction.

    Round 2 — a REAL context must arrive with the exact immutable ``revision``
    it was minted for. Validating a context against nothing proved only that some
    child had been admitted somewhere, which is not authority to build THIS
    deployment's engine.
    """
    from ..kernel.dispatch_context import bind_dispatch_context, require_bound_context

    bound = require_bound_context(context, revision)
    return bind_dispatch_context(_configured_engine(), bound)


def configured_local_meeting_model_path(*, meeting: Any = None) -> str:
    """The concrete local GGUF the in-process meeting-intel engine loads (HS-130-03).

    This is the SINGLE artifact the ``this_device`` execution branch actually
    loads (``build_intel_for_revision`` pins ``this_machine`` to ``local`` and
    hands ``MeetingIntel`` this path). ``this_machine`` readiness must therefore
    check THIS file and the receipt must name it — not the dictation-runtime
    model, which is a different subsystem.

    HS-132-10: ``meeting`` may name an already-loaded meeting config (the
    settings writer describing the document it just persisted). Omitted, the
    on-disk config is loaded exactly as before.
    """
    if meeting is None:
        from ..config import Config

        meeting = Config.load().meeting
    raw = str(getattr(meeting, "intel_realtime_model", "") or "").strip()
    return raw or DEFAULT_INTEL_MODEL_PATH


@dataclass(frozen=True)
class ConfiguredMeetingDeployment:
    """What ``build_configured_meeting_intel`` will actually load right now.

    ``paired_device`` delegates its execution to ``build_configured_meeting_intel``,
    so paired readiness (``runnable``) and the paired receipt (``model``) both
    derive from this snapshot instead of hardcoding ``ready`` (HS-130-03).
    """

    engine: str  # "local" | "cloud" | "mesh"
    model: str
    model_path: Optional[str]
    node: str
    runnable: bool
    reason: Optional[str]


def configured_meeting_deployment(*, meeting: Any = None) -> ConfiguredMeetingDeployment:
    """Resolve the deployment ``build_configured_meeting_intel`` would load.

    Honors the meeting placement policy (``intel_provider`` / ``intel_profile_id``)
    exactly as ``build_configured_meeting_intel`` does — this READS that policy to
    describe runnability; it does not own or change it (that is HS-130-05).

    HS-132-10: ``meeting`` may name an already-loaded meeting config so a caller
    that HOLDS the document (the settings writer describing the placement it just
    persisted) describes THAT document instead of re-reading the disk. Omitted,
    the on-disk config is loaded exactly as before.
    """
    if meeting is None:
        from ..config import Config

        meeting = Config.load().meeting
    # HS-130-05: describe what the ONE placement decision (and therefore
    # ``build_configured_meeting_intel``) will load, not ``intel_provider``
    # alone — an adopted openAICompatible destination reports its cloud
    # deployment even under ``intel_provider="local"``, matching execution.
    placement = resolve_meeting_placement(meeting)
    if placement.node:
        # Mesh liveness is a run-time question with its own named refusal; the
        # relay provider itself exists, so the deployment is runnable here.
        return ConfiguredMeetingDeployment(
            engine="mesh", model=str(placement.model or ""), model_path=None,
            node=str(placement.node), runnable=True, reason=None,
        )
    provider = placement.provider
    model_path = configured_local_meeting_model_path(meeting=meeting)
    active, reason = resolve_intel_provider(
        provider,
        model_path=model_path,
        cloud_model=placement.model,
        cloud_api_key_env=placement.api_key_env,
        cloud_base_url=placement.base_url,
    )
    if active == "cloud":
        return ConfiguredMeetingDeployment(
            engine="cloud", model=str(placement.model or ""), model_path=None,
            node="", runnable=True, reason=None,
        )
    local_model = Path(model_path).expanduser().stem
    if active == "local":
        return ConfiguredMeetingDeployment(
            engine="local", model=local_model, model_path=model_path,
            node="", runnable=True, reason=None,
        )
    # No provider resolved: the delegated execution path cannot load.
    return ConfiguredMeetingDeployment(
        engine="local", model=local_model, model_path=model_path,
        node="", runnable=False, reason=reason,
    )


def endpoint_host(base_url: Any) -> str:
    """The bare host an endpoint egresses to (never a full URL in a badge)."""
    raw = str(base_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "//" in raw else f"//{raw}")
    return parsed.hostname or ""


# The ONE egress vocabulary (HS-130-04). Every surface that states where a run
# went reports exactly one of these four boundaries.
EGRESS_LOCAL = "local"
EGRESS_PRIVATE_NETWORK = "private_network"
EGRESS_MESH = "mesh"
EGRESS_CLOUD = "cloud"
EGRESS_BOUNDARIES = (EGRESS_LOCAL, EGRESS_PRIVATE_NETWORK, EGRESS_MESH, EGRESS_CLOUD)


def egress_boundary(
    *, cloud: bool = False, base_url: Optional[str] = None, node: Optional[str] = None
) -> str:
    """THE one egress-vocabulary classifier (HS-130-04).

    Maps the endpoint a run ACTUALLY used to one of the four egress boundaries
    ``{local, private_network, mesh, cloud}``. Every surface that states where a
    run went — the badge (`endpoint_egress`), the run egress (`run_egress`),
    doctor, and the posture string — reads its verdict HERE, so a LAN box is
    ``private_network`` everywhere and a mesh route is ``mesh`` (never
    "Local only"). No host is invented: an endpoint with no parseable host is
    classified by intent (``cloud=True`` = the default public endpoint) and is
    NEVER stamped with a fabricated host name (the old ``DEFAULT_CLOUD_HOST`` lie
    is gone).
    """
    if node and str(node).strip():
        return EGRESS_MESH
    host = endpoint_host(base_url).lower().rstrip(".")
    if not host:
        # No concrete endpoint host. ``cloud=True`` is the default public cloud
        # endpoint (contacted later, named nowhere here); otherwise the run
        # stays on THIS machine.
        return EGRESS_CLOUD if cloud else EGRESS_LOCAL
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        return EGRESS_LOCAL
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host.endswith((".local", ".internal", ".lan", ".home")):
            return EGRESS_PRIVATE_NETWORK
        return EGRESS_CLOUD
    if address.is_loopback:
        return EGRESS_LOCAL
    if address.is_private or address.is_link_local:
        return EGRESS_PRIVATE_NETWORK
    return EGRESS_CLOUD


def endpoint_egress(
    *, cloud: bool = False, base_url: Optional[str] = None,
    label: Optional[str] = None, node: Optional[str] = None
) -> dict[str, Any]:
    """The ONE egress badge constructor (HS-84-04): ``{scope, host?, label?}``.

    Every surface that states where a run went builds its badge here — routes,
    cadence, audit — so the wire shape can't drift per call site. ``scope`` is
    the boundary from :func:`egress_boundary` (HS-130-04), so a LAN endpoint
    badges ``private_network`` and a mesh route badges ``mesh`` — the flat
    three-value ``{mesh, cloud, local}`` model is gone. Badges stay REPORTED
    facts: a host is stamped only when it was actually resolved from the
    endpoint the run used, never a fabricated default.
    """
    scope = egress_boundary(cloud=cloud, base_url=base_url, node=node)
    badge: dict[str, Any] = {"scope": scope}
    if scope == EGRESS_MESH:
        badge["host"] = str(node)
    elif scope in (EGRESS_PRIVATE_NETWORK, EGRESS_CLOUD):
        host = endpoint_host(base_url)
        if host:
            badge["host"] = host
    if label:
        badge["label"] = label
    return badge


def run_egress(profile: Any, intel: Any, *, default_model: str) -> tuple[dict[str, Any], str]:
    """The ONE run-egress badge rule (HS-130-04) shared by every run surface.

    Ask (`services.ask_service`) and recipe runs (`services.support`) both call
    HERE, so "where did this run go" has a single owner instead of two drifting
    copies. The endpoint the run actually used is classified through
    :func:`egress_boundary` via :func:`endpoint_egress`, so a LAN destination
    badges ``private_network`` and a mesh route badges ``mesh`` — never the old
    flat ``cloud`` for every remote endpoint.
    """
    kind = getattr(profile, "kind", "") if profile is not None else ""
    if kind == "meshNode" and getattr(profile, "node", ""):
        return endpoint_egress(node=profile.node), str(getattr(profile, "model", "") or "")
    if kind == "openAICompatible" and getattr(profile, "base_url", ""):
        return endpoint_egress(cloud=True, base_url=profile.base_url), str(getattr(profile, "model", "") or "")
    if getattr(intel, "active_provider", "") == "mesh":
        return endpoint_egress(node=getattr(intel, "node", "")), str(getattr(intel, "model_hint", "") or "")
    if getattr(intel, "active_provider", "") == "cloud":
        from ..config import Config

        effective = effective_intel_cloud(Config.load().meeting)
        return endpoint_egress(cloud=True, base_url=effective.base_url), str(effective.model or "")
    return endpoint_egress(cloud=False), default_model


def profile_slot_id(profile_id: str) -> str:
    """Injective, deterministic, non-secret secret-slot id for a profile (HS-130-02).

    The legacy scheme mapped every non-alphanumeric char to ``_``, so ``foo-bar``,
    ``foo_bar`` and ``foo.bar`` all collapsed to one slot — a device-local
    credential could be exfiltrated by a synced/created profile whose id merely
    *shaped* like an existing one (the key belongs to the slot, not the id).

    This slot is collision-free by construction: a human-readable slug (which may
    still collide under the lossy alnum map) is disambiguated by a hex digest of
    the RAW id bytes, so two distinct ids ALWAYS land in distinct slots. The
    digest is a pure function of the raw id, so a synced profile resolves the same
    slot on every device and across process restarts. A blank id has no slot and
    REFUSES — callers must never fall back to a shared name.
    """
    raw = str(profile_id or "")
    if not raw.strip():
        raise ValueError("cannot derive a secret slot from a blank profile id")
    slug = "".join(ch if ch.isalnum() else "_" for ch in raw.upper())[:48]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
    return f"{slug}_{digest}"


def profile_key_env(profile_id: str) -> str:
    """The hub env var that holds a runtime profile's API key (Phase 24). The key lives in
    the hub's SECRETS (env), never on the synced profile shape or in the payload.

    The env name is derived from the injective secret-slot id (HS-130-02), so two
    profile ids that differ only in punctuation NEVER read each other's key. A
    blank id raises rather than resolving to a shared ``HOLDSPEAK_PROFILE__KEY``.
    """
    return f"HOLDSPEAK_PROFILE_{profile_slot_id(profile_id)}_KEY"


@dataclass(frozen=True)
class EffectiveEndpoint:
    """A pipeline's effective LLM endpoint shape (HS-84-01/02).

    ``profile_id``/``profile_name`` are set only when an assigned RuntimeProfile
    was actually adopted. ``reason`` is set only when a profile was assigned but
    NOT used (dangling id, non-endpoint kind, lookup unavailable) — it is the
    honest sentence doctor/status surfaces later; the shape itself has already
    fallen back to the pipeline's legacy config fields.
    """

    model: str
    api_key_env: str
    base_url: Optional[str]
    profile_id: Optional[str] = None
    profile_name: Optional[str] = None
    reason: Optional[str] = None
    node: Optional[str] = None  # meshNode adoption (HS-85-02): the executing mesh node


def _lookup_profile_record(profile_id: str) -> Any:
    """Best-effort RuntimeProfile lookup for config resolution.

    The pipelines are constructed on CLI and early-boot paths too, so a missing
    or unopenable DB must degrade to the legacy config shape, never raise."""
    from ..db import get_database

    return get_database().profiles.get(profile_id)


def _apply_runtime_profile(
    legacy: EffectiveEndpoint,
    profile_id: str,
    get_profile: Optional[Callable[[str], Any]],
) -> EffectiveEndpoint:
    """The ONE profile-adoption rule shared by every hub pipeline (HS-84-01).

    A valid assigned ``openAICompatible`` profile shapes the endpoint (key env =
    ``HOLDSPEAK_PROFILE_<ID>_KEY`` when set, else the legacy env, matching
    ``build_meeting_intel_for_profile``); anything else falls back to ``legacy``
    with a named ``reason`` — never a crash.
    """
    if not profile_id:
        return legacy

    try:
        prof = (get_profile or _lookup_profile_record)(profile_id)
    except Exception as exc:
        return replace(legacy, reason=f"profile lookup unavailable ({exc.__class__.__name__}): {profile_id}")
    if prof is None or bool(getattr(prof, "deleted", False)):
        return replace(legacy, reason=f"assigned profile missing: {profile_id}")
    kind = str(getattr(prof, "kind", "") or "")
    base_url = str(getattr(prof, "base_url", "") or "").strip()
    if kind == "meshNode":
        node = str(getattr(prof, "node", "") or "").strip()
        if not node:
            return replace(legacy, reason=f"assigned meshNode profile names no node: {profile_id}")
        return EffectiveEndpoint(
            model=str(getattr(prof, "model", "") or "").strip() or legacy.model,
            api_key_env=legacy.api_key_env,
            base_url=None,
            profile_id=profile_id,
            profile_name=str(getattr(prof, "name", "") or "").strip() or profile_id,
            node=node,
        )
    if kind != "openAICompatible" or not base_url:
        return replace(
            legacy,
            reason=f"assigned profile is {kind or 'unknown'}-kind; running on the hub engine",
        )
    env = profile_key_env(profile_id)
    return EffectiveEndpoint(
        model=str(getattr(prof, "model", "") or "").strip() or legacy.model,
        # A destination may use only its own key slot. Borrowing the legacy
        # endpoint's key would be a silent credential/placement change.
        api_key_env=env,
        base_url=base_url,
        profile_id=profile_id,
        profile_name=str(getattr(prof, "name", "") or "").strip() or profile_id,
    )


def effective_intel_cloud(
    meeting_cfg: Any,
    *,
    get_profile: Optional[Callable[[str], Any]] = None,
) -> EffectiveEndpoint:
    """Resolve where the meeting-intel cloud leg runs (HS-112-01).

    The ONLY source is the ``intel_profile_id`` pointer into the profiles
    table. No pointer = the hub default shape (the default cloud endpoint,
    the default key env). ``intel_provider`` semantics (local / auto / cloud)
    are untouched — this shapes only the cloud leg.
    """
    default = EffectiveEndpoint(
        model=DEFAULT_INTEL_CLOUD_MODEL,
        api_key_env=DEFAULT_INTEL_CLOUD_API_KEY_ENV,
        base_url=None,
    )
    profile_id = str(getattr(meeting_cfg, "intel_profile_id", "") or "").strip()
    return _apply_runtime_profile(default, profile_id, get_profile)


# Placement sources (HS-130-05): why the meeting run landed where it did. A
# surface states exactly one of these so the effective placement is never silent.
PLACEMENT_DESTINATION = "destination"  # an adopted intel_profile_id destination won
PLACEMENT_PROVIDER = "provider"        # no destination adopted; intel_provider decided
PLACEMENT_PROVIDER_OVERRIDDEN = "provider-selection-ignored"  # a pointer was set but not usable


@dataclass(frozen=True)
class MeetingPlacement:
    """The ONE meeting-intel placement decision (HS-130-05).

    Meeting intelligence had two owners with no stated precedence: the
    ``intel_provider`` intent (local/auto/cloud) and the ``intel_profile_id``
    destination pointer. With ``intel_provider`` defaulting to ``"local"``,
    ``build_configured_meeting_intel`` passed ``provider="local"`` and the
    resolved destination was ignored — selecting a Meetings destination did
    nothing (a silent no-op), except a ``meshNode`` pointer which silently won.

    This composes both into ONE decision with an explicit precedence:

      1. An **adopted destination wins** — a live ``meshNode`` or
         ``openAICompatible`` ``intel_profile_id`` places the run there
         regardless of the local/auto/cloud intent (mesh already behaved this
         way; an ``openAICompatible`` destination now does too, ending the
         no-op). The destination is USED, and every describer states its real
         ``boundary`` — so the placement is surfaced, never silent.
      2. **Otherwise** ``intel_provider`` decides (local / auto / cloud) against
         the hub-default endpoint. A pointer that was set but is not usable
         (dangling / deleted / non-endpoint kind) does NOT silently win: it
         falls back to the provider intent and its ``reason`` rides ``source``
         so the surface can say why the selection was overridden.

    ``build_configured_meeting_intel`` (the selection) and the describers
    (``configured_egress_boundary``, ``configured_meeting_deployment``) all
    resolve through here, so "where does the meeting run go" has one owner.
    """

    node: Optional[str]      # truthy => mesh relay to this node
    provider: str            # what MeetingIntel is handed: "local" | "cloud" | "auto"
    model: str
    base_url: Optional[str]
    api_key_env: str
    boundary: str            # HS-130-04 vocabulary: local|private_network|mesh|cloud
    source: str              # PLACEMENT_* — why the run landed here
    profile_id: Optional[str] = None
    profile_name: Optional[str] = None
    reason: Optional[str] = None  # set when a pointer was set but not usable


def resolve_meeting_placement(
    meeting_cfg: Any,
    *,
    get_profile: Optional[Callable[[str], Any]] = None,
) -> MeetingPlacement:
    """Resolve the ONE meeting-intel placement (HS-130-05). See ``MeetingPlacement``."""
    effective = effective_intel_cloud(meeting_cfg, get_profile=get_profile)
    provider_intent = _normalize_provider(getattr(meeting_cfg, "intel_provider", None))

    # (1a) An adopted mesh destination places the run on the relay, regardless
    # of intel_provider (the pointer already won here; now it is also surfaced
    # as `mesh`, never "Local only").
    if effective.node:
        return MeetingPlacement(
            node=effective.node,
            provider="cloud",  # unused by the relay path; a non-local marker
            model=str(effective.model or ""),
            base_url=None,
            api_key_env=effective.api_key_env,
            boundary=EGRESS_MESH,
            source=PLACEMENT_DESTINATION,
            profile_id=effective.profile_id,
            profile_name=effective.profile_name,
        )

    # (1b) An adopted openAICompatible destination places the run on that
    # endpoint, regardless of the local/auto/cloud intent. THIS is the fix for
    # the silent no-op: a selected Meetings destination now takes effect.
    if effective.profile_id and effective.base_url:
        return MeetingPlacement(
            node=None,
            provider="cloud",
            model=str(effective.model or ""),
            base_url=effective.base_url,
            api_key_env=effective.api_key_env,
            boundary=egress_boundary(cloud=True, base_url=effective.base_url),
            source=PLACEMENT_DESTINATION,
            profile_id=effective.profile_id,
            profile_name=effective.profile_name,
        )

    # (2) No destination adopted: intel_provider decides against the hub default.
    # A pointer that was set but is not usable degrades to the provider intent
    # with its reason surfaced (never a silent override).
    source = PLACEMENT_PROVIDER_OVERRIDDEN if effective.reason else PLACEMENT_PROVIDER
    if provider_intent == "local":
        boundary = EGRESS_LOCAL
    else:
        boundary = egress_boundary(cloud=True, base_url=effective.base_url)
    return MeetingPlacement(
        node=None,
        provider=provider_intent,
        model=str(effective.model or ""),
        base_url=effective.base_url,
        api_key_env=effective.api_key_env,
        boundary=boundary,
        source=source,
        profile_id=None,
        profile_name=None,
        reason=effective.reason,
    )


def effective_dictation_llm(
    runtime_cfg: Any,
    *,
    get_profile: Optional[Callable[[str], Any]] = None,
) -> EffectiveEndpoint:
    """Resolve where the DIR-01 dictation LLM leg runs (HS-112-01).

    The ONLY source is the ``profile_id`` pointer into the profiles table.
    An ADOPTED profile also means the dictation backend runs
    ``openai_compatible`` (the assignment is the user's explicit "run it
    there"); no pointer leaves the configured local backend untouched.
    """
    default = EffectiveEndpoint(
        model="",
        api_key_env=DEFAULT_INTEL_CLOUD_API_KEY_ENV,
        base_url=None,
    )
    profile_id = str(getattr(runtime_cfg, "profile_id", "") or "").strip()
    # meshNode adopts here too (owner call, 2026-07-07): DIR's endpoint leg is
    # already advisory-constrained (ask for JSON, validate, retry), so the
    # relay rides the same posture — a far edge degrades under the pipeline's
    # existing latency budget, exactly like a slow endpoint.
    return _apply_runtime_profile(default, profile_id, get_profile)


def build_meeting_intel_for_profile(
    *, kind: str, base_url: Optional[str], model: Optional[str], profile_id: str,
    node: str = "", model_file: str = "", deployment_revision: Any = None,
    warrant: Optional[dict[str, Any]] = None, context: Any = None,
) -> "MeetingIntel":
    """Build a `MeetingIntel` for a specific RuntimeProfile (Phase 24).

    An ``openAICompatible`` profile runs on its endpoint, with only its own
    per-profile secret name (``HOLDSPEAK_PROFILE_<ID>_KEY``). A key from an
    unrelated default destination is never borrowed. ``onDevice`` is
    local-only, so the legacy ``auto`` setting cannot silently cross a boundary.

    ``onDevice`` loads THIS profile's ``model_file`` — the exact local model that
    made the destination ready — never the global meeting model (HS-130-03).

    HS-131-10: an allowlisted adapter factory. It refuses BY NAME — before any
    provider object exists — without the runner's dispatch context for the exact
    revision being built (or the ONE named legacy marker, carried today only by the
    mesh receiver, which is itself a blocking finding).

    Round 2 — ``deployment_revision=None`` with a REAL context now refuses. The
    old gate passed ``None`` straight into the validator, which then compared
    nothing at all, so any genuine context built any profile.
    """
    from ..kernel.dispatch_context import bind_dispatch_context, require_bound_context
    from .engine import MeetingIntel

    bound = require_bound_context(context, deployment_revision)
    return bind_dispatch_context(
        _profile_engine(
            kind=kind, base_url=base_url, model=model, profile_id=profile_id,
            node=node, model_file=model_file, deployment_revision=deployment_revision,
            warrant=warrant, context=context,
        ),
        bound,
    )


def _profile_engine(
    *, kind: str, base_url: Optional[str], model: Optional[str], profile_id: str,
    node: str = "", model_file: str = "", deployment_revision: Any = None,
    warrant: Optional[dict[str, Any]] = None, context: Any = None,
) -> "MeetingIntel":
    """Construct the profile-shaped engine (reached only with a validated context).

    ``context`` is carried, not re-validated: the caller above already refused a
    missing or mismatched one. It travels so the configured-placement fallbacks
    below stay on the same admitted path instead of dropping to the legacy
    uncontextual constructor.
    """
    from .engine import MeetingIntel

    if kind == "meshNode" and str(node or "").strip():
        from .mesh_relay import MeshRelayIntel

        return MeshRelayIntel(
            node=str(node).strip(), model_hint=str(model or ""),
            deployment_revision=deployment_revision, warrant=warrant,
        )  # type: ignore[return-value]
    if kind == "openAICompatible" and str(base_url or "").strip():
        # Refuse on ambiguity: a blank profile id has no unique secret slot, and
        # borrowing a shared env name would let an unidentified destination read
        # another's key (HS-130-02). Fall back to the configured local engine
        # rather than send a transcript out under a collided credential.
        if not str(profile_id or "").strip():
            return configured_meeting_intel(
                context=context, revision=deployment_revision
            )
        env = profile_key_env(profile_id)
        return MeetingIntel(
            provider="cloud",
            cloud_model=(model or DEFAULT_INTEL_CLOUD_MODEL),
            cloud_base_url=str(base_url).strip(),
            cloud_api_key_env=env,
        )
    if kind == "onDevice":
        # HS-132-09: the profile's own model_file is the WHOLE deployment. The
        # old fallback to `configured_local_meeting_model_path()` is the same
        # shape HS-131-13 closed on the `this_machine` branch — a post-admission
        # read of MUTABLE meeting config, which lets an admitted child load a
        # model its frozen revision never named while the receipt keeps the
        # revision's name. A blank `model_file` refuses BY NAME instead.
        model_path = str(model_file or "").strip()
        if not model_path:
            from ..inference_targets import LOCAL_DEPLOYMENT_MODEL_UNKNOWN
            from ..kernel.model import KernelRefused

            raise KernelRefused(LOCAL_DEPLOYMENT_MODEL_UNKNOWN)
        return MeetingIntel(provider="local", model_path=model_path)
    return configured_meeting_intel(context=context, revision=deployment_revision)


def configured_egress_boundary(meeting_cfg: Any) -> str:
    """The egress boundary the CONFIGURED meeting-intel run will actually cross.

    Reads the RESOLVED endpoint (`effective_intel_cloud` honors the
    ``intel_profile_id`` pointer — mesh node / private endpoint / default cloud),
    NOT ``intel_provider`` alone. A ``meshNode`` pointer therefore reports
    ``mesh`` even when ``intel_provider`` still says ``local`` — matching what
    `build_configured_meeting_intel` actually loads (the relay wins regardless of
    provider). This DESCRIBES the chosen route; it does not own the selection —
    that is the meeting placement policy (`resolve_meeting_placement`,
    HS-130-05), which this delegates to so the described boundary always equals
    the run's actual boundary. An adopted ``openAICompatible`` destination
    therefore reports its endpoint's boundary even when ``intel_provider`` still
    says ``local`` (the selection wins), exactly matching what
    `build_configured_meeting_intel` loads — the "Local only" string can no
    longer describe an off-machine run. The four-value verdict itself still
    comes from `egress_boundary` (HS-130-04), which the placement policy calls.
    """
    return resolve_meeting_placement(meeting_cfg).boundary


# Boundary → (can_transmit_offmachine, human description). The ONE mapping the
# posture string and doctor/web status read (HS-130-04).
_EGRESS_POSTURE: dict[str, tuple[bool, str]] = {
    EGRESS_LOCAL: (False, "Local only — transcripts never leave this machine."),
    EGRESS_PRIVATE_NETWORK: (
        True,
        "Private network — transcripts are sent to a device on your local network.",
    ),
    EGRESS_MESH: (
        True,
        "Private mesh — transcripts are relayed to your configured mesh node.",
    ),
    EGRESS_CLOUD: (
        True,
        "Cloud — transcripts are sent to the configured cloud endpoint.",
    ),
}


def _provider_only_boundary(provider: Optional[str]) -> str:
    """Boundary from a bare provider string with no profile pointer (legacy)."""
    normalized = _normalize_provider(provider)
    if normalized == "local":
        return EGRESS_LOCAL
    # cloud / auto with no resolved endpoint = the default public cloud endpoint.
    return EGRESS_CLOUD


def intel_egress_posture(
    provider: str = DEFAULT_INTEL_PROVIDER, *, meeting_cfg: Any = None
) -> tuple[bool, str]:
    """Describe the egress boundary the configured meeting-intel run will cross.

    The single source of truth for the egress posture surfaced in
    ``holdspeak doctor`` and the web runtime status (HS-25-01). When
    ``meeting_cfg`` is given the verdict derives from the RESOLVED endpoint
    (`configured_egress_boundary`), so a ``meshNode`` route reports mesh and a
    LAN endpoint reports the private network — the "Local only" string can no
    longer appear for an off-machine route (HS-130-04). With only a bare
    ``provider`` string (legacy callers), the boundary is derived from the
    provider alone.

    Returns ``(can_transmit_offmachine, human_description)``.
    """
    if meeting_cfg is not None:
        boundary = configured_egress_boundary(meeting_cfg)
    else:
        boundary = _provider_only_boundary(provider)
    return _EGRESS_POSTURE[boundary]


def get_intel_runtime_status(
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
    *,
    provider: str = DEFAULT_INTEL_PROVIDER,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Return whether the configured meeting-intel mode can run right now."""
    active, reason = resolve_intel_provider(
        provider,
        model_path=model_path,
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    if active is None:
        return False, reason
    return True, None
