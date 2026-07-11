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
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse


TARGET_CONTRACT_VERSION = 1
PROFILE_ALIAS_VERSION = 1
THIS_MACHINE_ID = "this_machine"
PAIRED_DEVICE_ID = "paired_device"
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
    # Import lazily: provider imports this module on some boot paths.
    from .intel.providers import profile_key_env

    return bool(os.environ.get(profile_key_env(profile_id), "").strip())


def _recovery(reason: str, *, alternate: str = THIS_MACHINE_ID) -> dict[str, str]:
    return {
        "reason": reason,
        "action": "choose_alternate_target",
        "alternate_target_id": alternate,
    }


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
        """The immutable actual-placement part of an attempt receipt."""
        actual_boundary = self.boundary
        actual_fallback = fallback_reason
        if self.kind == "paired_device" and provider == "cloud":
            actual_boundary = "paired_device_then_external_service"
            actual_fallback = actual_fallback or "Paired device used its configured external engine"
        return {
            "target_id": self.id,
            "target_name": self.name,
            "target_kind": self.kind,
            "boundary": actual_boundary,
            "owner": self.owner,
            "transport": self.transport,
            "data_classes": ["instruction", "selected_context", "grounding", "generated_output"],
            "engine": provider or self.engine,
            "model": model or self.model,
            "fallback_reason": actual_fallback,
        }


def this_machine_target(*, name: str = "This device", model: str = "") -> InferenceTarget:
    return InferenceTarget(
        id=THIS_MACHINE_ID,
        name=name,
        kind="this_device",
        boundary="same_device",
        owner="you",
        transport="in_process",
        profile_id=None,
        engine="configured_local_engine",
        model=model,
        context_limit=16_384,
    )


def paired_device_target(*, name: str = "Paired device", model: str = "") -> InferenceTarget:
    """The current hub as seen by an authenticated paired-device caller."""
    return InferenceTarget(
        id=PAIRED_DEVICE_ID,
        name=name,
        kind="paired_device",
        boundary="paired_device",
        owner="you",
        transport="paired_https",
        profile_id=None,
        engine="configured_hub_engine",
        model=model,
        context_limit=16_384,
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

    if legacy_kind == "onDevice":
        kind, boundary, owner, transport, engine = (
            "this_device", "same_device", "you", "in_process", "local",
        )
        model = model or str(getattr(profile, "model_file", "") or "").strip()
    elif legacy_kind == "desktop":
        kind, boundary, owner, transport, engine = (
            "paired_device", "paired_device", "you", "paired_https", "paired_runtime",
        )
        if db is not None and model:
            manifests = [m for m in db.model_manifests.list() if m.node == "desktop"]
            if manifests and not any(m.name == model for m in manifests):
                state = "stale_manifest"
                reason = f"Paired device no longer advertises model '{model}'"
    elif legacy_kind == "meshNode":
        kind, boundary, owner, transport, engine = (
            "mesh_node", "private_mesh", "you", "mesh_relay", "node_runtime",
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
            state, reason = "unsupported", f"Destination '{name}' has no valid endpoint URL"
        elif requires_key and not key_present:
            from .intel.providers import profile_key_env

            state = "needs_key"
            reason = f"Destination '{name}' needs a key in ${profile_key_env(pid)}"
    else:
        kind, boundary, owner, transport, engine = (
            "unsupported", "unknown", "unknown", "none", "unknown",
        )
        state, reason = "unsupported", f"Destination '{name}' has unsupported kind '{legacy_kind or 'unknown'}'"

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
    )


def list_inference_targets(db: Any) -> list[InferenceTarget]:
    return [this_machine_target()] + [target_from_profile(p, db) for p in db.profiles.list()]


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


def target_refusal(target: InferenceTarget) -> dict[str, Any]:
    return {
        "error": target.readiness_reason or f"Destination '{target.name}' is unavailable",
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


def build_intel_for_target(target: InferenceTarget, db: Any) -> Any:
    """Construct the engine for one already-resolved target.

    ``this_device`` is deliberately local-only.  It never inherits the legacy
    ``auto`` provider, because doing so could turn a same-device choice into an
    invisible cross-boundary fallback.
    """
    from .config import Config
    from .intel.engine import MeetingIntel
    from .intel.providers import build_configured_meeting_intel, build_meeting_intel_for_profile

    if target.kind == "this_device":
        # Preserve the long-standing injectable constructor seam used by host
        # integrations, then pin real MeetingIntel instances to local. A mesh
        # default is never reused for a same-device choice.
        configured = build_configured_meeting_intel()
        from .intel.mesh_relay import MeshRelayIntel

        if not isinstance(configured, MeshRelayIntel):
            # MeetingIntel and injected host adapters share this constructor
            # seam. Pin any provider-bearing adapter locally before returning.
            if hasattr(configured, "provider"):
                configured.provider = "local"
            if hasattr(configured, "_active_provider"):
                configured._active_provider = None
            return configured
        meeting = Config.load().meeting
        kwargs: dict[str, Any] = {"provider": "local"}
        model_path = getattr(meeting, "intel_realtime_model", None)
        if model_path:
            kwargs["model_path"] = model_path
        return MeetingIntel(**kwargs)
    if target.kind == "paired_device" and target.profile_id is None:
        return build_configured_meeting_intel()
    if target.profile_id:
        profile = db.profiles.get(target.profile_id)
        if profile is not None:
            return build_meeting_intel_for_profile(
                kind=profile.kind,
                base_url=profile.base_url,
                model=profile.model,
                profile_id=profile.id,
                node=getattr(profile, "node", ""),
            )
    # Kept solely as a tolerant guard for an older caller; resolver users never
    # reach it with an unavailable target.
    return build_configured_meeting_intel()
