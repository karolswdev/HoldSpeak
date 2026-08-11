"""MeetingIntelPlan@1 — the frozen, content-free meeting intelligence plan (HS-131-08).

One meeting session freezes ONE plan at admission time. The plan names, per
capability, the ORDERED and immutable set of permitted deployment revisions
(Sol Amendment 1). Every admitted child repeats the exact entry it selected;
a capability absent from the plan is a named refusal, never a late
``resolve_placement`` call and never a silent retarget.

The plan carries hashes, ids, revisions, and capability names only — no
transcript, prompt, token, audio, or credential material ever enters it.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

PLAN_SCHEMA = 1

CAPABILITY_LIVE_ANALYSIS = "live-analysis"
CAPABILITY_BOOKMARK_LABEL = "bookmark-label"
CAPABILITY_AUTO_TITLE = "auto-title"
CAPABILITY_DEFERRED_ANALYSIS = "deferred-base-analysis"
PLUGIN_CAPABILITY_PREFIX = "plugin:"

# The work ``stop()`` displaces onto the deferred job, as STABLE SLUGS (never the
# owner-facing sentence). The job carries this list durably and the queue runs
# exactly it, so a normal deferred job (no handoff) keeps running base analysis +
# routed plugins and nothing else.
DISPLACED_FINAL_ANALYSIS = "final-analysis"
DISPLACED_BOOKMARK_LABELS = "bookmark-labels"
DISPLACED_AUTO_TITLE = "auto-title"
DISPLACED_ROUTED_INTELLIGENCE = "routed-intelligence"
DISPLACED_LABELS = {
    DISPLACED_FINAL_ANALYSIS: "final analysis",
    DISPLACED_BOOKMARK_LABELS: "bookmark labels",
    DISPLACED_AUTO_TITLE: "auto title",
    DISPLACED_ROUTED_INTELLIGENCE: "routed intelligence",
}

SESSION_CAPABILITIES = (
    CAPABILITY_LIVE_ANALYSIS,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_AUTO_TITLE,
)

# Named refusals. These are the only honest outcomes when the frozen plan does
# not authorize what a seam is about to do.
CAPABILITY_NOT_PLANNED = "meeting_intel_capability_not_planned"
REVISION_NOT_PLANNED = "meeting_intel_revision_not_planned"
SESSION_NOT_ADMITTED = "meeting_intel_session_not_admitted"
SESSION_NOT_LIVE = "meeting_intel_session_not_live"
# A closed live session is NEVER revived: deferred work admits its own parent.
SESSION_CLOSED = "meeting_session_closed"
PRINCIPAL_REQUIRED = "meeting_intel_principal_required"


class MeetingIntelRefused(RuntimeError):
    """A named, content-free meeting-intelligence refusal."""

    def __init__(self, reason: str, capability: str = "") -> None:
        super().__init__(reason if not capability else f"{reason}:{capability}")
        self.reason = reason
        self.capability = capability


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


@dataclass(frozen=True)
class MeetingIntelPlan:
    """One immutable meeting routing/deployment plan. See module docstring."""

    schema: int
    meeting_id: str
    provenance: str
    config_revision: str
    routing_hash: str
    plugin_registry_hash: str
    created_at: float
    deadline_at: float
    child_budget: int
    capabilities: Mapping[str, tuple[str, ...]]
    placements: Mapping[str, Mapping[str, Any]]
    sha256: str

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def revisions(self, capability: str) -> tuple[str, ...]:
        """The ordered permitted deployment revisions for one capability."""
        entry = self.capabilities.get(capability)
        if not entry:
            raise MeetingIntelRefused(CAPABILITY_NOT_PLANNED, capability)
        return tuple(entry)

    def primary(self, capability: str) -> str:
        return self.revisions(capability)[0]

    def assert_planned(self, capability: str, revision_id: str) -> str:
        """Refuse any revision that is not frozen in this capability's set."""
        if str(revision_id) not in self.revisions(capability):
            raise MeetingIntelRefused(REVISION_NOT_PLANNED, capability)
        return str(revision_id)

    def placement(self, capability: str) -> Mapping[str, Any]:
        return dict(self.placements.get(capability) or {})

    def summary(self) -> dict[str, Any]:
        """The content-free snapshot a parent ``input_snapshot`` may carry."""
        return {
            "plan_schema": self.schema,
            "meeting_id": self.meeting_id,
            "provenance": self.provenance,
            "plan_sha256": self.sha256,
            "config_revision": self.config_revision,
            "routing_hash": self.routing_hash,
            "plugin_registry_hash": self.plugin_registry_hash,
            "deadline_at": self.deadline_at,
            "child_budget": self.child_budget,
            "capabilities": {name: list(value) for name, value in sorted(self.capabilities.items())},
        }


def _config_terms(meeting_config: Any) -> dict[str, Any]:
    """The content-free meeting-intel configuration terms the plan is frozen on."""
    return {
        "intel_enabled": bool(getattr(meeting_config, "intel_enabled", False)),
        "intel_provider": str(getattr(meeting_config, "intel_provider", "") or ""),
        "intel_profile_id": str(getattr(meeting_config, "intel_profile_id", "") or ""),
        "intel_deferred_enabled": bool(getattr(meeting_config, "intel_deferred_enabled", False)),
        "intel_realtime_model": str(getattr(meeting_config, "intel_realtime_model", "") or ""),
        "disabled_plugins": sorted(str(p) for p in (getattr(meeting_config, "disabled_plugins", None) or [])),
    }


def _placement_legs(db: Any, meeting_config: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Resolve the ordered permitted deployment legs for meeting intelligence.

    This enumerates what analysis ACTUALLY reaches (HS-130-05's
    ``resolve_meeting_placement`` composed with the Phase-130 placement
    authority):

    * an adopted ``intel_profile_id`` destination wins outright — ONE leg, no
      fallback; and
    * with no adopted destination the run lands on the configured local
      deployment (``this_machine``). The historical ``auto`` local→cloud fallback
      used to live INSIDE that one engine, so a receipt could name the local
      revision while the cloud endpoint ran. Sol Amendment 1: that fallback is
      frozen HERE as a real second entry — the hub-default cloud deployment —
      whenever the cloud leg is actually reachable. The intra-engine fallback is
      disabled either way (``build_intel_for_revision`` pins ``this_machine``
      local), so with an unreachable cloud leg the list honestly stays ONE entry
      and there is nothing left to retarget silently.

    The ordered-set shape is the contract: children SELECT an entry, never
    resolve one.
    """
    from ..inference_targets import hub_default_cloud_deployment, resolve_placement
    from ..intel.providers import (
        effective_intel_cloud,
        get_cloud_intel_runtime_status,
        resolve_meeting_placement,
    )

    placement = resolve_meeting_placement(meeting_config)
    pointer = str(placement.profile_id or "").strip() or None
    resolution = resolve_placement(db, invocation=pointer)
    target = resolution.target
    provider_intent = str(placement.provider or "")
    metadata = {
        "placement_source": str(placement.source or ""),
        "placement_reason": str(placement.reason or ""),
        "provider_intent": provider_intent,
        "boundary": str(target.boundary or ""),
        "target_id": str(target.id or ""),
        "target_kind": str(target.kind or ""),
        "target_ready": bool(target.ready),
        "target_readiness_reason": str(target.readiness_reason or ""),
        # No engine ever falls back internally any more: either the fallback is a
        # frozen second entry below, or it does not exist.
        "internal_provider_fallback": False,
        "auto_cloud_fallback": "",
        "auto_cloud_fallback_reason": "",
        "auto_cloud_fallback_boundary": "",
    }
    if pointer is not None or provider_intent != "auto":
        return (target,), metadata

    effective = effective_intel_cloud(meeting_config)
    reachable, reason = get_cloud_intel_runtime_status(
        cloud_model=effective.model,
        cloud_api_key_env=effective.api_key_env,
        cloud_base_url=effective.base_url,
    )
    if not reachable:
        metadata["auto_cloud_fallback"] = "unconfigured"
        metadata["auto_cloud_fallback_reason"] = str(reason or "")
        return (target,), metadata
    cloud = hub_default_cloud_deployment(effective)
    metadata["auto_cloud_fallback"] = "frozen"
    metadata["auto_cloud_fallback_boundary"] = str(cloud.boundary or "")
    return (target, cloud), metadata


def freeze_meeting_intel_plan(
    db: Any,
    *,
    meeting_id: str,
    capabilities: Sequence[str],
    deadline_at: float,
    child_budget: int,
    provenance: str = "desktop",
    meeting_config: Any = None,
    plugin_ids: Sequence[str] = (),
    created_at: Optional[float] = None,
) -> MeetingIntelPlan:
    """Resolve and freeze one MeetingIntelPlan@1 before any child is admitted."""
    from ..deployment_revisions import capture_deployment_revision

    if meeting_config is None:
        from ..config import Config

        meeting_config = Config.load().meeting

    legs, metadata = _placement_legs(db, meeting_config)
    revision_ids = tuple(capture_deployment_revision(db, leg).id for leg in legs)

    declared = list(dict.fromkeys(str(name) for name in capabilities if str(name).strip()))
    for plugin_id in dict.fromkeys(str(p) for p in plugin_ids if str(p).strip()):
        entry = f"{PLUGIN_CAPABILITY_PREFIX}{plugin_id}"
        if entry not in declared:
            declared.append(entry)

    # Resolution is PER CAPABILITY. Today every meeting-intelligence capability
    # resolves through the one meeting-intel placement authority, so the legs
    # coincide; the per-capability map is what lets a plugin capability name a
    # different revision without changing any child's contract.
    frozen = {name: revision_ids for name in sorted(declared)}
    placements = {name: dict(metadata) for name in sorted(declared)}

    terms = _config_terms(meeting_config)
    plugin_registry_hash = _sha({"plugins": sorted(dict.fromkeys(str(p) for p in plugin_ids)),
                                 "disabled": terms["disabled_plugins"]})
    routing_hash = _sha({"placement": metadata, "revisions": list(revision_ids)})
    config_revision = _sha(terms)
    now = time.time() if created_at is None else float(created_at)
    body = {
        "schema": PLAN_SCHEMA,
        "meeting_id": str(meeting_id),
        "provenance": str(provenance),
        "config_revision": config_revision,
        "routing_hash": routing_hash,
        "plugin_registry_hash": plugin_registry_hash,
        "deadline_at": float(deadline_at),
        "child_budget": int(child_budget),
        "capabilities": {name: list(value) for name, value in sorted(frozen.items())},
        "placements": {name: value for name, value in sorted(placements.items())},
    }
    return MeetingIntelPlan(
        schema=PLAN_SCHEMA,
        meeting_id=str(meeting_id),
        provenance=str(provenance),
        config_revision=config_revision,
        routing_hash=routing_hash,
        plugin_registry_hash=plugin_registry_hash,
        created_at=now,
        deadline_at=float(deadline_at),
        child_budget=int(child_budget),
        capabilities=frozen,
        placements=placements,
        sha256=_sha(body),
    )


__all__ = [
    "DISPLACED_AUTO_TITLE",
    "DISPLACED_BOOKMARK_LABELS",
    "DISPLACED_FINAL_ANALYSIS",
    "DISPLACED_LABELS",
    "DISPLACED_ROUTED_INTELLIGENCE",
    "CAPABILITY_AUTO_TITLE",
    "CAPABILITY_BOOKMARK_LABEL",
    "CAPABILITY_DEFERRED_ANALYSIS",
    "CAPABILITY_LIVE_ANALYSIS",
    "CAPABILITY_NOT_PLANNED",
    "MeetingIntelPlan",
    "MeetingIntelRefused",
    "PLAN_SCHEMA",
    "PLUGIN_CAPABILITY_PREFIX",
    "PRINCIPAL_REQUIRED",
    "REVISION_NOT_PLANNED",
    "SESSION_CAPABILITIES",
    "SESSION_CLOSED",
    "SESSION_NOT_ADMITTED",
    "SESSION_NOT_LIVE",
    "freeze_meeting_intel_plan",
]
