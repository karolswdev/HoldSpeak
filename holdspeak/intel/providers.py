"""Intel provider resolution + egress posture (HS-34-04).

`OpenAI`/`Llama` live in the package `__init__` (the optional-dependency import
head) and are read here *via the package* (`_intel_pkg.OpenAI`/`.Llama`) so tests
that monkeypatch `holdspeak.intel.OpenAI` / `holdspeak.intel.Llama` are honored.
"""

from __future__ import annotations

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
    value = os.environ.get(env_name)
    if value:
        return value.strip() or None
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
        return False, f"Intel model not found: {resolved}"

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
        provider = getattr(meeting_config, "intel_provider", None) or DEFAULT_INTEL_PROVIDER
        effective = effective_intel_cloud(meeting_config)
        kwargs: dict[str, Any] = {
            "cloud_model": effective.model,
            "cloud_api_key_env": effective.api_key_env,
            "cloud_base_url": effective.base_url,
        }
        model_path = getattr(meeting_config, "intel_realtime_model", None)
        if model_path:
            kwargs["model_path"] = model_path
        resolved, _reason = _intel_pkg.resolve_intel_provider(provider, **kwargs)
        return resolved is not None
    except Exception:
        return False


def build_configured_meeting_intel() -> "MeetingIntel":
    """Construct a `MeetingIntel` from the user's saved meeting config.

    Built-in plugins (`mermaid_architecture`, `action_owner_enforcer`, …) call
    this for their default intel provider so they honour the configured endpoint
    (e.g. a self-hosted `.43` cloud base URL) instead of the bare `MeetingIntel()`
    module defaults — which would otherwise ignore the user's provider entirely.
    """
    from ..config import Config
    from .engine import MeetingIntel

    meeting = Config.load().meeting
    effective = effective_intel_cloud(meeting)
    if effective.node:
        from .mesh_relay import MeshRelayIntel

        return MeshRelayIntel(node=effective.node, model_hint=effective.model)  # type: ignore[return-value]
    kwargs: dict[str, Any] = {
        "provider": getattr(meeting, "intel_provider", DEFAULT_INTEL_PROVIDER),
        "cloud_model": effective.model,
        "cloud_api_key_env": effective.api_key_env,
        "cloud_base_url": effective.base_url,
        "cloud_reasoning_effort": getattr(meeting, "intel_cloud_reasoning_effort", None),
        "cloud_store": bool(getattr(meeting, "intel_cloud_store", False)),
    }
    model_path = getattr(meeting, "intel_realtime_model", None)
    if model_path:
        kwargs["model_path"] = model_path
    return MeetingIntel(**kwargs)


def endpoint_host(base_url: Any) -> str:
    """The bare host an endpoint egresses to (never a full URL in a badge)."""
    raw = str(base_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "//" in raw else f"//{raw}")
    return parsed.hostname or ""


def endpoint_egress(
    *, cloud: bool = False, base_url: Optional[str] = None,
    label: Optional[str] = None, node: Optional[str] = None
) -> dict[str, Any]:
    """The ONE egress badge constructor (HS-84-04): ``{scope, host?, label?}``.

    Every surface that states where a run went builds its badge here — routes,
    cadence, audit — so the wire shape can't drift per call site. Badges stay
    REPORTED facts: pass the endpoint the run actually used, never a default.
    """
    if node:
        badge: dict[str, Any] = {"scope": "mesh", "host": str(node)}
    else:
        badge = {"scope": "cloud" if cloud else "local"}
        if cloud:
            badge["host"] = endpoint_host(base_url) or "api.openai.com"
    if label:
        badge["label"] = label
    return badge


def profile_key_env(profile_id: str) -> str:
    """The hub env var that holds a runtime profile's API key (Phase 24). The key lives in
    the hub's SECRETS (env), never on the synced profile shape or in the payload."""
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(profile_id or "").upper())
    return f"HOLDSPEAK_PROFILE_{safe}_KEY"


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
        api_key_env=env if os.environ.get(env) else legacy.api_key_env,
        base_url=base_url,
        profile_id=profile_id,
        profile_name=str(getattr(prof, "name", "") or "").strip() or profile_id,
    )


def effective_intel_cloud(
    meeting_cfg: Any,
    *,
    get_profile: Optional[Callable[[str], Any]] = None,
) -> EffectiveEndpoint:
    """Resolve where the meeting-intel cloud leg runs (HS-84-01).

    Resolution order: a valid assigned ``openAICompatible`` RuntimeProfile →
    the legacy ``intel_cloud_*`` config shape. ``intel_provider`` semantics
    (local / auto / cloud) are untouched — this shapes only the cloud leg.
    """
    legacy = EffectiveEndpoint(
        model=str(getattr(meeting_cfg, "intel_cloud_model", "") or "").strip()
        or DEFAULT_INTEL_CLOUD_MODEL,
        api_key_env=str(getattr(meeting_cfg, "intel_cloud_api_key_env", "") or "").strip()
        or DEFAULT_INTEL_CLOUD_API_KEY_ENV,
        base_url=getattr(meeting_cfg, "intel_cloud_base_url", None),
    )
    profile_id = str(getattr(meeting_cfg, "intel_profile_id", "") or "").strip()
    return _apply_runtime_profile(legacy, profile_id, get_profile)


def effective_dictation_llm(
    runtime_cfg: Any,
    *,
    get_profile: Optional[Callable[[str], Any]] = None,
) -> EffectiveEndpoint:
    """Resolve where the DIR-01 dictation LLM leg runs (HS-84-02).

    Resolution order: a valid assigned ``openAICompatible`` RuntimeProfile →
    the legacy ``openai_compatible_*`` config shape. An ADOPTED profile also
    means the dictation backend runs ``openai_compatible`` (the assignment is
    the user's explicit "run it there"); every fallback leaves the configured
    backend untouched.
    """
    legacy = EffectiveEndpoint(
        model=str(getattr(runtime_cfg, "openai_compatible_model", "") or "").strip(),
        api_key_env=str(getattr(runtime_cfg, "openai_compatible_api_key_env", "") or "").strip()
        or DEFAULT_INTEL_CLOUD_API_KEY_ENV,
        base_url=getattr(runtime_cfg, "openai_compatible_base_url", None),
    )
    profile_id = str(getattr(runtime_cfg, "profile_id", "") or "").strip()
    # meshNode adopts here too (owner call, 2026-07-07): DIR's endpoint leg is
    # already advisory-constrained (ask for JSON, validate, retry), so the
    # relay rides the same posture — a far edge degrades under the pipeline's
    # existing latency budget, exactly like a slow endpoint.
    return _apply_runtime_profile(legacy, profile_id, get_profile)


def build_meeting_intel_for_profile(
    *, kind: str, base_url: Optional[str], model: Optional[str], profile_id: str,
    node: str = ""
) -> "MeetingIntel":
    """Build a `MeetingIntel` for a specific RuntimeProfile (Phase 24).

    An ``openAICompatible`` profile runs on its endpoint, with the key resolved from the hub's
    secrets — a per-profile env var (``HOLDSPEAK_PROFILE_<ID>_KEY``), falling back to the default
    cloud key env. An ``onDevice`` (or unknown) profile falls back to the hub's configured default
    (the hub can't host another device's GGUF — honest n/a, never a crash).
    """
    from .engine import MeetingIntel

    if kind == "meshNode" and str(node or "").strip():
        from .mesh_relay import MeshRelayIntel

        return MeshRelayIntel(node=str(node).strip(), model_hint=str(model or ""))  # type: ignore[return-value]
    if kind == "openAICompatible" and str(base_url or "").strip():
        env = profile_key_env(profile_id)
        key_env = env if os.environ.get(env) else DEFAULT_INTEL_CLOUD_API_KEY_ENV
        return MeetingIntel(
            provider="cloud",
            cloud_model=(model or DEFAULT_INTEL_CLOUD_MODEL),
            cloud_base_url=str(base_url).strip(),
            cloud_api_key_env=key_env,
        )
    return build_configured_meeting_intel()


def intel_egress_posture(provider: str = DEFAULT_INTEL_PROVIDER) -> tuple[bool, str]:
    """Describe whether the configured provider can send transcripts off-machine.

    This is a *static* description of intent from config — it answers "can this
    setting transmit a transcript to the cloud?", not "is a model loaded right
    now?". It is the single source of truth for the egress posture surfaced in
    ``holdspeak doctor`` and the web runtime status (HS-25-01).

    Returns ``(can_transmit_offmachine, human_description)``.
    """
    normalized = _normalize_provider(provider)
    if normalized == "local":
        return False, "Local only — transcripts never leave this machine."
    if normalized == "cloud":
        return True, "Cloud — transcripts are sent to the configured cloud endpoint."
    # auto = local-first, but will fall back to the cloud when no local model is
    # available, so the configuration *can* transmit off-machine.
    return (
        True,
        "Auto — local first, but falls back to sending transcripts to the cloud "
        "when no local model is available.",
    )


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
