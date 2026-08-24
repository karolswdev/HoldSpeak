"""Read-only decoder for persisted ``MeetingIntelPlan@1`` history.

Meeting v1 plan construction and execution were retired at the Phase-F cutover.
This module intentionally retains only stable labels, refusal vocabulary, and a
content-free DTO decoder so old journals/projections can render their stored
bytes.  It does not resolve placement, inspect configuration, or provide a
resume/replay operation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

PLAN_SCHEMA = 1

# Stable v1 labels remain part of history and projection rendering, not authority.
CAPABILITY_LIVE_ANALYSIS = "live-analysis"
CAPABILITY_BOOKMARK_LABEL = "bookmark-label"
CAPABILITY_AUTO_TITLE = "auto-title"
CAPABILITY_DEFERRED_ANALYSIS = "deferred-base-analysis"
PLUGIN_CAPABILITY_PREFIX = "plugin:"

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
CAPABILITY_WHISPER_TRANSCRIBE = "whisper-transcribe"
CAPABILITY_WHISPER_PRELOAD = "whisper-preload"
TRANSCRIPTION_CAPABILITIES = (CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD)

CAPABILITY_NOT_PLANNED = "meeting_intel_capability_not_planned"
REVISION_NOT_PLANNED = "meeting_intel_revision_not_planned"
SESSION_NOT_ADMITTED = "meeting_intel_session_not_admitted"
SESSION_NOT_LIVE = "meeting_intel_session_not_live"
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
    """A decoded persisted v1 plan, intentionally incapable of execution."""

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

    @classmethod
    def from_persisted(cls, payload: bytes | str | Mapping[str, Any]) -> "MeetingIntelPlan":
        """Decode historical bytes without consulting any runtime authority."""
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        parsed = json.loads(payload) if isinstance(payload, str) else dict(payload)
        if int(parsed.get("schema") or 0) != PLAN_SCHEMA:
            raise ValueError("unsupported_meeting_intel_plan_schema")
        raw_capabilities = parsed.get("capabilities") or {}
        raw_placements = parsed.get("placements") or {}
        if not isinstance(raw_capabilities, Mapping) or not isinstance(raw_placements, Mapping):
            raise ValueError("invalid_meeting_intel_plan_history")
        canonical = {
            "schema": PLAN_SCHEMA,
            "meeting_id": str(parsed.get("meeting_id") or ""),
            "provenance": str(parsed.get("provenance") or ""),
            "config_revision": str(parsed.get("config_revision") or ""),
            "routing_hash": str(parsed.get("routing_hash") or ""),
            "plugin_registry_hash": str(parsed.get("plugin_registry_hash") or ""),
            "deadline_at": float(parsed.get("deadline_at") or 0.0),
            "child_budget": int(parsed.get("child_budget") or 0),
            "capabilities": {
                str(key): [str(value) for value in values]
                for key, values in raw_capabilities.items()
                if isinstance(values, (list, tuple))
            },
            "placements": {
                str(key): dict(value)
                for key, value in raw_placements.items()
                if isinstance(value, Mapping)
            },
        }
        return cls(
            schema=PLAN_SCHEMA,
            meeting_id=canonical["meeting_id"],
            provenance=canonical["provenance"],
            config_revision=canonical["config_revision"],
            routing_hash=canonical["routing_hash"],
            plugin_registry_hash=canonical["plugin_registry_hash"],
            created_at=float(parsed.get("created_at") or 0.0),
            deadline_at=canonical["deadline_at"],
            child_budget=canonical["child_budget"],
            capabilities={key: tuple(value) for key, value in canonical["capabilities"].items()},
            placements=canonical["placements"],
            sha256=str(parsed.get("sha256") or _sha(canonical)),
        )

    def summary(self) -> dict[str, Any]:
        """Return display-safe stored metadata; this is not an execution plan."""
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
            "placements": {name: dict(value) for name, value in sorted(self.placements.items())},
        }


def decode_meeting_intel_plan_v1(payload: bytes | str | Mapping[str, Any]) -> MeetingIntelPlan:
    """Public history/projection decoder; no route selection or replay exists."""
    return MeetingIntelPlan.from_persisted(payload)


__all__ = [
    "CAPABILITY_AUTO_TITLE",
    "CAPABILITY_BOOKMARK_LABEL",
    "CAPABILITY_DEFERRED_ANALYSIS",
    "CAPABILITY_LIVE_ANALYSIS",
    "CAPABILITY_NOT_PLANNED",
    "CAPABILITY_WHISPER_PRELOAD",
    "CAPABILITY_WHISPER_TRANSCRIBE",
    "DISPLACED_AUTO_TITLE",
    "DISPLACED_BOOKMARK_LABELS",
    "DISPLACED_FINAL_ANALYSIS",
    "DISPLACED_LABELS",
    "DISPLACED_ROUTED_INTELLIGENCE",
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
    "TRANSCRIPTION_CAPABILITIES",
    "decode_meeting_intel_plan_v1",
]
